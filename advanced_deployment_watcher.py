#!/usr/bin/env python3
"""
Расширенный скрипт для отслеживания изменений в репозиториях и автоматического обновления 
серверов и клиентов в зависимости от содержания коммитов и конфигурации.
"""

import os
import sys
import time
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import argparse
import logging
from datetime import datetime
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeploymentAction:
    """Класс для выполнения различных действий по обновлению"""
    
    @staticmethod
    def pip_install(requirements_file: str, cwd: Path) -> bool:
        """Устанавливает зависимости из requirements файла"""
        try:
            logger.info(f"Установка зависимостей из {requirements_file}")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], cwd=cwd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при установке зависимостей: {e}")
            return False
    
    @staticmethod
    def systemctl_restart(services: List[str], sudo: bool = False, user: bool = False) -> bool:
        """Перезапускает systemd сервисы"""
        try:
            for service in services:
                cmd = ["systemctl"]
                if sudo:
                    cmd = ["sudo"] + cmd
                if user:
                    cmd.append("--user")
                cmd.extend(["restart", service])
                
                logger.info(f"Перезапуск сервиса: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при перезапуске сервиса: {e}")
            return False

class DeploymentWatcher:
    def __init__(self, config_path: str = "deployment_config.json"):
        self.config = self.load_config(config_path)
        self.watchers = []
        
        # Инициализация watcher'ов для каждого репозитория
        for repo_config in self.config['repositories']:
            watcher = RepoWatcher(
                name=repo_config['name'],
                path=repo_config['path'],
                branches=repo_config['branches'],
                targets=repo_config['targets'],
                config=self.config
            )
            self.watchers.append(watcher)
    
    def load_config(self, config_path: str) -> Dict:
        """Загружает конфигурацию из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Конфигурационный файл {config_path} не найден")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге конфигурационного файла: {e}")
            sys.exit(1)
    
    def run(self):
        """Запускает все watcher'ы"""
        logger.info(f"Запуск watcher'ов для {len(self.watchers)} репозиториев")
        
        try:
            while True:
                for watcher in self.watchers:
                    watcher.check_for_updates()
                
                time.sleep(self.config['check_interval'])
        except KeyboardInterrupt:
            logger.info("Работа всех watcher'ов остановлена пользователем")
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")

class RepoWatcher:
    def __init__(self, name: str, path: str, branches: List[str], targets: Dict, config: Dict):
        self.name = name
        self.path = Path(path).resolve()
        self.branches = branches
        self.targets = targets
        self.config = config
        self.last_commit_hashes = {branch: self.get_current_commit(branch) for branch in branches}
        
        # Настройка логирования для этого репо
        self.logger = logging.getLogger(f"RepoWatcher-{name}")
        
        self.logger.info(f"Инициализация watcher для репо: {self.path}, ветки: {branches}")
    
    def get_current_commit(self, branch: str = "main") -> str:
        """Получает хэш текущего коммита в ветке"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{branch}"], 
                cwd=self.path, 
                capture_output=True, 
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Не удалось получить хэш коммита для ветки {branch}: {e}")
            # Попробуем локальный коммит
            try:
                result = subprocess.run(
                    ["git", "rev-parse", branch], 
                    cwd=self.path, 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e2:
                self.logger.error(f"Не удалось получить локальный хэш коммита: {e2}")
                return ""
    
    def get_commit_info(self, commit_hash: str) -> Dict:
        """Получает информацию о коммите"""
        try:
            # Получаем сообщение коммита
            msg_result = subprocess.run(
                ["git", "show", "-s", "--format=%s", "--quiet", commit_hash],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_message = msg_result.stdout.strip()
            
            # Получаем автора коммита
            author_result = subprocess.run(
                ["git", "show", "-s", "--format=%an", "--quiet", commit_hash],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_author = author_result.stdout.strip()
            
            # Получаем список измененных файлов
            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            changed_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
            
            # Получаем дату коммита
            date_result = subprocess.run(
                ["git", "show", "-s", "--format=%ci", "--quiet", commit_hash],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_date = date_result.stdout.strip()
            
            return {
                'hash': commit_hash,
                'message': commit_message,
                'author': commit_author,
                'date': commit_date,
                'files': changed_files
            }
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Не удалось получить информацию о коммите {commit_hash}: {e}")
            return {'hash': commit_hash, 'message': '', 'author': '', 'date': '', 'files': []}
    
    def determine_targets(self, commit_info: Dict) -> Set[str]:
        """Определяет, для каких целей предназначен коммит"""
        targets = set()
        commit_msg = commit_info['message'].lower()
        changed_files = [f.lower() for f in commit_info['files']]
        
        # Проверяем сообщение коммита
        if any(tag in commit_msg for tag in ['server', '[server]', '(server)', 'backend']):
            targets.add('server')
        
        if any(tag in commit_msg for tag in ['client', '[client]', '(client)', 'frontend']):
            targets.add('client')
        
        # Проверяем изменившиеся файлы для каждой цели
        for target_name, target_config in self.targets.items():
            for file_path in changed_files:
                for file_prefix in target_config['files']:
                    if file_path.startswith(file_prefix.lower()):
                        targets.add(target_name)
                        break
        
        # Если не определено явно, определяем на основе файлов
        if not targets:
            for target_name, target_config in self.targets.items():
                if any(any(file_path.startswith(fp.lower()) for fp in target_config['files']) 
                      for file_path in changed_files):
                    targets.add(target_name)
        
        # Если так и не определено, обновляем все
        if not targets:
            targets = set(self.targets.keys())
        
        return targets
    
    def execute_actions(self, target_name: str) -> bool:
        """Выполняет действия для указанной цели"""
        self.logger.info(f"Выполнение действий для цели: {target_name}")
        
        target_config = self.targets[target_name]
        all_success = True
        
        for action in target_config['actions']:
            action_type = action['type']
            
            if action_type == 'pip_install':
                req_file = action['requirements']
                success = DeploymentAction.pip_install(req_file, self.path)
            
            elif action_type == 'systemctl':
                services = action['services']
                sudo = action.get('sudo', False)
                user = action.get('user', False)
                success = DeploymentAction.systemctl_restart(services, sudo, user)
            
            else:
                self.logger.warning(f"Неизвестный тип действия: {action_type}")
                success = False
            
            if not success:
                all_success = False
                self.logger.error(f"Действие {action_type} для цели {target_name} завершилось с ошибкой")
        
        return all_success
    
    def notify_update(self, commit_info: Dict, affected_targets: Set[str]):
        """Отправляет уведомление об обновлении"""
        if not self.config['notification']['enabled']:
            return
        
        notification_config = self.config['notification']
        
        if 'telegram' in notification_config:
            telegram_config = notification_config['telegram']
            if telegram_config['bot_token'] and telegram_config['chat_id']:
                message = (f"🔄 Обновление в репозитории {self.name}\n\n"
                          f"Коммит: {commit_info['hash'][:8]}\n"
                          f"Сообщение: {commit_info['message']}\n"
                          f"Автор: {commit_info['author']}\n"
                          f"Цели обновления: {', '.join(affected_targets)}")
                
                try:
                    url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
                    payload = {
                        'chat_id': telegram_config['chat_id'],
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(url, json=payload)
                    if response.status_code != 200:
                        self.logger.error(f"Ошибка при отправке уведомления в Telegram: {response.text}")
                except Exception as e:
                    self.logger.error(f"Ошибка при отправке уведомления в Telegram: {e}")
    
    def process_new_commit(self, commit_info: Dict, branch: str):
        """Обрабатывает новый коммит"""
        self.logger.info(f"Обнаружен новый коммит в ветке {branch}: {commit_info['hash'][:8]} - {commit_info['message']}")
        
        targets = self.determine_targets(commit_info)
        self.logger.info(f"Определены цели обновления: {targets}")
        
        # Выполняем git pull для получения изменений
        try:
            subprocess.run(["git", "pull"], cwd=self.path, check=True)
            self.logger.info("Выполнен git pull для получения изменений")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при выполнении git pull: {e}")
            return  # Не продолжаем, если не удалось получить изменения
        
        # Выполняем действия для каждой цели
        successful_targets = []
        for target in targets:
            if self.execute_actions(target):
                successful_targets.append(target)
            else:
                self.logger.error(f"Не удалось обновить цель: {target}")
        
        # Отправляем уведомление
        self.notify_update(commit_info, set(successful_targets))
    
    def check_for_updates(self):
        """Проверяет наличие новых коммитов в отслеживаемых ветках"""
        for branch in self.branches:
            current_commit = self.get_current_commit(branch)
            
            if current_commit and current_commit != self.last_commit_hashes[branch]:
                commit_info = self.get_commit_info(current_commit)
                self.process_new_commit(commit_info, branch)
                self.last_commit_hashes[branch] = current_commit

def main():
    parser = argparse.ArgumentParser(description="Скрипт для отслеживания изменений в репозиториях и автоматического обновления")
    parser.add_argument('--config', default='deployment_config.json', help='Путь к конфигурационному файлу')
    parser.add_argument('--interval', type=int, default=None,
                       help='Интервал проверки в секундах (переопределяет значение в конфиге)')
    parser.add_argument('--once', action='store_true',
                       help='Выполнить одну проверку и выйти (не запускать цикл)')
    
    args = parser.parse_args()
    
    # Загружаем watcher
    watcher = DeploymentWatcher(config_path=args.config)
    
    # Переопределяем интервал если указан
    if args.interval is not None:
        watcher.config['check_interval'] = args.interval
    
    if args.once:
        for repo_watcher in watcher.watchers:
            repo_watcher.check_for_updates()
    else:
        watcher.run()

if __name__ == "__main__":
    main()