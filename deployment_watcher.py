#!/usr/bin/env python3
"""
Скрипт для отслеживания изменений в репозитории и автоматического обновления 
серверов и клиентов в зависимости от содержания коммитов.
"""

import os
import sys
import time
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set
import argparse
import logging
from datetime import datetime

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

class DeploymentWatcher:
    def __init__(self, repo_path: str = ".", target_type: str = "auto"):
        self.repo_path = Path(repo_path).resolve()
        self.target_type = target_type  # "server", "client", "auto", "both"
        self.last_commit_hash = self.get_current_commit()
        logger.info(f"Инициализация watcher для репо: {self.repo_path}, цель: {self.target_type}")
        
        # Определение типов файлов для разных целей
        self.server_files = {
            'server/', 'api/', 'bot/', 'agent/', 'admin/', 
            'requirements_server.txt', 'docker/', 'traefik/',
            'install_server.sh', 'post_install_setup.sh'
        }
        
        self.client_files = {
            'client/', 'requirements_client.txt', 'install_client.sh'
        }
    
    def get_current_commit(self) -> str:
        """Получает хэш текущего коммита"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Не удалось получить хэш коммита: {e}")
            return ""
    
    def get_commit_info(self, commit_hash: str) -> Dict:
        """Получает информацию о коммите"""
        try:
            # Получаем сообщение коммита
            msg_result = subprocess.run(
                ["git", "show", "-s", "--format=%s", "--quiet", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_message = msg_result.stdout.strip()
            
            # Получаем список измененных файлов
            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            changed_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
            
            return {
                'hash': commit_hash,
                'message': commit_message,
                'files': changed_files
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Не удалось получить информацию о коммите {commit_hash}: {e}")
            return {'hash': commit_hash, 'message': '', 'files': []}
    
    def determine_target(self, commit_info: Dict) -> Set[str]:
        """Определяет, для каких целей предназначен коммит"""
        targets = set()
        commit_msg = commit_info['message'].lower()
        changed_files = [f.lower() for f in commit_info['files']]
        
        # Проверяем сообщение коммита
        if 'server' in commit_msg or '[server]' in commit_msg:
            targets.add('server')
        
        if 'client' in commit_msg or '[client]' in commit_msg:
            targets.add('client')
        
        # Проверяем изменившиеся файлы
        for file_path in changed_files:
            # Проверяем server файлы
            for server_prefix in self.server_files:
                if file_path.startswith(server_prefix):
                    targets.add('server')
                    break
            
            # Проверяем client файлы
            for client_prefix in self.client_files:
                if file_path.startswith(client_prefix):
                    targets.add('client')
                    break
        
        # Если не определено явно, определяем автоматически
        if not targets:
            # Если есть файлы и для сервера, и для клиента - обновляем оба
            server_related = any(any(file_path.startswith(prefix) for prefix in self.server_files) 
                               for file_path in changed_files)
            client_related = any(any(file_path.startswith(prefix) for prefix in self.client_files) 
                               for file_path in changed_files)
            
            if server_related and client_related:
                targets = {'server', 'client'}
            elif server_related:
                targets = {'server'}
            elif client_related:
                targets = {'client'}
            else:
                # Если неясно, обновляем и сервер, и клиент
                targets = {'server', 'client'}
        
        return targets
    
    def update_server(self) -> bool:
        """Обновляет серверную часть"""
        logger.info("Начинаем обновление сервера...")
        try:
            # Pull latest changes
            subprocess.run(["git", "pull"], cwd=self.repo_path, check=True)
            
            # Обновляем зависимости сервера
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_server.txt"], 
                         cwd=self.repo_path, check=True)
            
            # Перезапускаем systemd сервисы
            subprocess.run(["sudo", "systemctl", "restart", "xvpn-api"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "xvpn-agent"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "xvpn-bot"], check=True)
            
            logger.info("Сервер успешно обновлен")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при обновлении сервера: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении сервера: {e}")
            return False
    
    def update_client(self) -> bool:
        """Обновляет клиентскую часть"""
        logger.info("Начинаем обновление клиента...")
        try:
            # Pull latest changes
            subprocess.run(["git", "pull"], cwd=self.repo_path, check=True)
            
            # Обновляем зависимости клиента
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_client.txt"], 
                         cwd=self.repo_path, check=True)
            
            # Если есть systemd сервис клиента, перезапускаем его
            try:
                subprocess.run(["systemctl", "--user", "restart", "xvpn-client"], check=True)
                logger.info("Сервис клиента перезапущен")
            except subprocess.CalledProcessError:
                logger.info("Сервис клиента не найден или не требуется перезапуск")
            
            logger.info("Клиент успешно обновлен")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при обновлении клиента: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении клиента: {e}")
            return False
    
    def process_new_commit(self, commit_info: Dict):
        """Обрабатывает новый коммит"""
        logger.info(f"Обнаружен новый коммит: {commit_info['hash'][:8]} - {commit_info['message']}")
        
        targets = self.determine_target(commit_info)
        logger.info(f"Определены цели обновления: {targets}")
        
        # Применяем фильтр по типу цели, если задан
        if self.target_type == "server":
            targets = targets.intersection({'server'})
        elif self.target_type == "client":
            targets = targets.intersection({'client'})
        elif self.target_type == "auto":
            # Оставляем только определенные цели
            pass
        elif self.target_type == "both":
            # Обновляем все
            targets = {'server', 'client'}
        
        if 'server' in targets:
            logger.info("Выполняем обновление сервера...")
            self.update_server()
        
        if 'client' in targets:
            logger.info("Выполняем обновление клиента...")
            self.update_client()
        
        # Сохраняем хэш обработанного коммита
        self.last_commit_hash = commit_info['hash']
    
    def check_for_updates(self) -> bool:
        """Проверяет наличие новых коммитов"""
        current_commit = self.get_current_commit()
        
        if current_commit != self.last_commit_hash:
            commit_info = self.get_commit_info(current_commit)
            self.process_new_commit(commit_info)
            return True
        
        return False
    
    def run(self, interval: int = 30):
        """Запускает бесконечный цикл проверки обновлений"""
        logger.info(f"Запуск watcher с интервалом {interval} секунд")
        
        try:
            while True:
                self.check_for_updates()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Работа watcher остановлена пользователем")
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")

def main():
    parser = argparse.ArgumentParser(description="Скрипт для отслеживания изменений в репозитории и автоматического обновления")
    parser.add_argument('--repo-path', default='.', help='Путь к репозиторию (по умолчанию: текущая директория)')
    parser.add_argument('--target', choices=['server', 'client', 'auto', 'both'], default='auto',
                       help='Целевая система для обновления (по умолчанию: auto)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Интервал проверки в секундах (по умолчанию: 30)')
    parser.add_argument('--once', action='store_true',
                       help='Выполнить одну проверку и выйти (не запускать цикл)')
    
    args = parser.parse_args()
    
    watcher = DeploymentWatcher(repo_path=args.repo_path, target_type=args.target)
    
    if args.once:
        watcher.check_for_updates()
    else:
        watcher.run(interval=args.interval)

if __name__ == "__main__":
    main()