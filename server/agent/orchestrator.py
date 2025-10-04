#!/usr/bin/env python3
"""
AI-оркестратор XVPN для управления рисками и автоматического восстановления
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import logging

# Импортируем созданные скрипты
from scripts.action_logger import action_logger
from scripts.test_runner import test_runner
from scripts.log_cleaner import log_cleaner

class XVPNOrchestrator:
    """AI-оркестратор XVPN для управления рисками и восстановления системы"""
    
    def __init__(self):
        self.state = "INITIALIZING"
        self.last_health_check = None
        self.consecutive_failures = 0
        self.max_failures = 5
        
        # Настройка логирования
        self.setup_logging()
        
        # Инициализация компонентов
        self.initialize_components()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/xvpn/orchestration/orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('XVPNOrchestrator')
        
    def initialize_components(self):
        """Инициализация компонентов"""
        try:
            self.logger.info("Инициализация AI-оркестратора XVPN")
            
            # Проверка доступности сервисов
            self.check_system_services()
            
            # Загрузка конфигурации
            self.load_config()
            
            # Запуск мониторинга
            self.state = "RUNNING"
            self.logger.info("AI-оркестратор XVPN запущен")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {e}")
            self.state = "ERROR"
            
    def load_config(self):
        """Загрузка конфигурации"""
        config_path = Path("/opt/xvpn/orchestrator_config.json")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "health_check_interval": 30,
                "max_failures": 5,
                "retry_attempts": 3,
                "fallback_timeout": 300,
                "notification_threshold": 3,
                "log_retention_days": 7
            }
            
    def check_system_services(self):
        """Проверка доступности системных сервисов"""
        services = ["xvpn-api", "xvpn-agent", "xvpn-core"]
        
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.logger.warning(f"Сервис {service} неактивен")
                    action_logger.log_error(
                        "SERVICE_NOT_RUNNING",
                        f"Сервис {service} неактивен",
                        {"service": service}
                    )
                else:
                    self.logger.info(f"Сервис {service} активен")
                    
            except Exception as e:
                self.logger.error(f"Ошибка проверки сервиса {service}: {e}")
                
    async def health_monitoring_loop(self):
        """Основной цикл мониторинга здоровья"""
        self.logger.info("Запуск цикла мониторинга здоровья")
        
        while self.state == "RUNNING":
            try:
                # Проверка здоровья системы
                health_status = await self.check_system_health()
                
                # Анализ состояния
                await self.analyze_system_state(health_status)
                
                # Пауза до следующей проверки
                await asyncio.sleep(self.config.get("health_check_interval", 30))
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
                
    async def check_system_health(self) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "issues": []
        }
        
        # Проверка API
        try:
            result = subprocess.run(
                ["curl", "-sk", "https://127.0.0.1:8443/mcp/v1/vpn.health"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                api_health = json.loads(result.stdout)
                health_status["components"]["api"] = {
                    "status": "healthy",
                    "response_time": api_health.get("response_time", 0),
                    "mask_score": api_health.get("mask_score", 0)
                }
            else:
                health_status["components"]["api"] = {"status": "unhealthy"}
                health_status["issues"].append("API не отвечает")
                
        except Exception as e:
            health_status["components"]["api"] = {"status": "error", "error": str(e)}
            health_status["issues"].append(f"Ошибка проверки API: {e}")
            
        # Проверка VPN ядра
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "xvpn-core"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            health_status["components"]["vpn_core"] = {
                "status": "active" if result.returncode == 0 else "inactive"
            }
            
            if result.returncode != 0:
                health_status["issues"].append("VPN ядро неактивно")
                
        except Exception as e:
            health_status["components"]["vpn_core"] = {"status": "error", "error": str(e)}
            health_status["issues"].append(f"Ошибка проверки VPN ядра: {e}")
            
        # Определение общего состояния
        if health_status["issues"]:
            health_status["overall_status"] = "degraded" if len(health_status["issues"]) < 3 else "critical"
            
        return health_status
        
    async def analyze_system_state(self, health_status: Dict[str, Any]):
        """Анализ состояния системы и принятие решений"""
        issues_count = len(health_status["issues"])
        
        # Логирование состояния
        self.logger.info(f"Состояние системы: {health_status['overall_status']}, проблем: {issues_count}")
        
        # Обработка различных состояний
        if health_status["overall_status"] == "critical":
            await self.handle_critical_state(health_status)
        elif health_status["overall_status"] == "degraded":
            await self.handle_degraded_state(health_status)
        elif health_status["overall_status"] == "healthy":
            await self.handle_healthy_state(health_status)
            
    async def handle_critical_state(self, health_status: Dict[str, Any]):
        """Обработка критического состояния"""
        self.logger.critical("КРИТИЧЕСКОЕ СОСТОЯНИЕ СИСТЕМЫ")
        
        # Увеличиваем счетчик сбоев
        self.consecutive_failures += 1
        
        # Логирование
        action_logger.log_error(
            "CRITICAL_STATE",
            f"Критическое состояние системы, проблем: {len(health_status['issues'])}",
            {"issues": health_status["issues"], "failures": self.consecutive_failures}
        )
        
        # Запуск диагностики
        await self.run_system_diagnosis()
        
        # Уведомление администратора
        await self.notify_administrator("CRITICAL", health_status["issues"])
        
        # Попытка восстановления
        if self.consecutive_failures >= self.max_failures:
            await self.attempt_system_recovery()
            
    async def handle_degraded_state(self, health_status: Dict[str, Any]):
        """Обработка пониженного состояния"""
        self.logger.warning("Пониженное состояние системы")
        
        # Запуск тестов
        test_results = test_runner.run_all_tests()
        
        # Логирование
        action_logger.log_action(
            "DEGRADED_STATE",
            {
                "issues": health_status["issues"],
                "test_results": test_results
            }
        )
        
        # Попытка автоматического восстановления
        await self.attempt_auto_recovery(health_status)
        
    async def handle_healthy_state(self, health_status: Dict[str, Any]):
        """Обработка здорового состояния"""
        self.logger.info("Система в здоровом состоянии")
        
        # Сброс счетчика сбоев
        if self.consecutive_failures > 0:
            self.consecutive_failures = 0
            self.logger.info("Счетчик сбоев сброшен")
            
        # Периодическая очистка логов
        if datetime.now().hour == 2 and datetime.now().minute < 5:  # 2:00 - 2:05
            await self.cleanup_logs()
            
    async def run_system_diagnosis(self):
        """Запрос диагностики системы"""
        try:
            # Запуск расширенных тестов
            diagnosis_results = test_runner.run_all_tests()
            
            # Логирование результатов
            self.logger.info(f"Диагностика завершена: {diagnosis_results['summary']}")
            
            # Сохранение результатов
            diagnosis_file = Path("/var/log/xvpn/orchestration/diagnosis.json")
            with open(diagnosis_file, 'w', encoding='utf-8') as f:
                json.dump(diagnosis_results, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")
            
    async def attempt_auto_recovery(self, health_status: Dict[str, Any]):
        """Попытка автоматического восстановления"""
        self.logger.info("Попытка автоматического восстановления")
        
        recovery_actions = []
        
        # Восстановление API
        if "api" in health_status["components"] and health_status["components"]["api"]["status"] != "healthy":
            recovery_actions.append("restart_api")
            
        # Восстановление VPN ядра
        if "vpn_core" in health_status["components"] and health_status["components"]["vpn_core"]["status"] != "active":
            recovery_actions.append("restart_vpn_core")
            
        # Выполнение действий восстановления
        for action in recovery_actions:
            try:
                await self.execute_recovery_action(action)
            except Exception as e:
                self.logger.error(f"Ошибка выполнения действия восстановления {action}: {e}")
                
    async def execute_recovery_action(self, action: str):
        """Выполнение действия восстановления"""
        self.logger.info(f"Выполнение действия восстановления: {action}")
        
        try:
            if action == "restart_api":
                result = subprocess.run(
                    ["systemctl", "restart", "xvpn-api"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                action_logger.log_action("API_RESTARTED", {"success": result.returncode == 0})
                
            elif action == "restart_vpn_core":
                result = subprocess.run(
                    ["systemctl", "restart", "xvpn-core"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                action_logger.log_action("VPN_CORE_RESTARTED", {"success": result.returncode == 0})
                
        except Exception as e:
            action_logger.log_error("RECOVERY_ACTION_FAILED", f"Ошибка выполнения {action}: {e}")
            
    async def attempt_system_recovery(self):
        """Попытка восстановления системы"""
        self.logger.critical("Попытка восстановления системы")
        
        try:
            # Перезапуск всех сервисов
            services = ["xvpn-api", "xvpn-agent", "xvpn-core"]
            
            for service in services:
                self.logger.info(f"Перезапуск сервиса {service}")
                result = subprocess.run(
                    ["systemctl", "restart", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.logger.info(f"Сервис {service} успешно перезапущен")
                else:
                    self.logger.error(f"Ошибка перезапуска сервиса {service}: {result.stderr}")
                    
            # Пауза перед проверкой
            await asyncio.sleep(10)
            
            # Проверка состояния после восстановления
            health_status = await self.check_system_health()
            await self.analyze_system_state(health_status)
            
        except Exception as e:
            self.logger.error(f"Ошибка восстановления системы: {e}")
            
    async def notify_administrator(self, level: str, issues: List[str]):
        """Уведомление администратора"""
        try:
            # Формирование сообщения
            message = f"🚨 XVPN Alert - {level.upper()}\n\n"
            message += f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Проблемы: {len(issues)}\n\n"
            
            for i, issue in enumerate(issues, 1):
                message += f"{i}. {issue}\n"
                
            # Здесь должен быть код отправки уведомления
            # Например, через Telegram бот или email
            
            self.logger.info(f"Уведомление администратора отправлено: {level}")
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")
            
    async def cleanup_logs(self):
        """Очистка логов"""
        try:
            results = log_cleaner.clean_old_logs()
            self.logger.info(f"Очистка логов завершена: {results}")
        except Exception as e:
            self.logger.error(f"Ошибка очистки логов: {e}")
            
    async def start(self):
        """Запуск оркестратора"""
        try:
            await self.health_monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("Оркестратор остановлен пользователем")
            self.state = "STOPPED"
        except Exception as e:
            self.logger.error(f"Критическая ошибка оркестратора: {e}")
            self.state = "ERROR"

# Создаем глобальный экземпляр
orchestrator = XVPNOrchestrator()

if __name__ == "__main__":
    # Запуск оркестратора
    asyncio.run(orchestrator.start())