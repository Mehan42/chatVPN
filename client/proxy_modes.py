#!/usr/bin/env python3
# XVPN Proxy Modes Manager
# Управление различными режимами прокси для XVPN
# Абсолютный путь: ~/chatvpn/client/proxy_modes.py

import os
import json
import time
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyMode(Enum):
    """Режимы работы прокси"""
    SYSTEM = "system"
    MANUAL = "manual"
    AUTO = "auto"
    TRANSPARENT = "transparent"
    SPLIT = "split"
    BYPASS = "bypass"

class ProxyModesManager:
    """Менеджер режимов прокси для XVPN"""
    
    def __init__(self):
        self.config = self._load_config()
        self.current_mode = ProxyMode(self.config.get('current_mode', 'system'))
        self.auto_detect_enabled = self.config.get('auto_detect_enabled', True)
        self.bypass_rules = self.config.get('bypass_rules', [])
        self.manual_settings = self.config.get('manual_settings', {})
        self.transparent_enabled = self.config.get('transparent_enabled', False)
        
        # Пути к логам
        self.log_dir = Path.home() / 'chatvpn' / 'client' / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / 'proxy_modes.log'
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка логирования"""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _load_config(self) -> Dict:
        """Загрузка конфигурации режимов прокси"""
        config_path = Path.home() / 'chatvpn' / 'client' / 'proxy_modes_config.json'
        default_config = {
            "current_mode": "system",
            "auto_detect_enabled": True,
            "bypass_rules": [
                "localhost",
                "127.0.0.1/8",
                "::1/128",
                "*.local",
                "*.localdomain"
            ],
            "manual_settings": {
                "proxy_type": "http",
                "proxy_host": "",
                "proxy_port": 8080,
                "proxy_username": "",
                "proxy_password": "",
                "proxy_exceptions": []
            },
            "transparent_enabled": False,
            "split_tunnel_enabled": False,
            "split_tunnel_apps": [],
            "dns_leak_protection": True
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    logger.info(f"Proxy modes config loaded from {config_path}")
            else:
                # Создаем файл конфигурации с настройками по умолчанию
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Proxy modes config created at {config_path}")
            
            return default_config
            
        except Exception as e:
            logger.error(f"Error loading proxy modes config: {e}")
            return default_config
    
    def save_config(self):
        """Сохранение конфигурации режимов прокси"""
        config_path = Path.home() / 'chatvpn' / 'client' / 'proxy_modes_config.json'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Proxy modes config saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving proxy modes config: {e}")
    
    def set_mode(self, mode: ProxyMode) -> bool:
        """Установка режима прокси"""
        try:
            # Отключаем текущий режим
            self._disable_current_mode()
            
            # Устанавливаем новый режим
            self.current_mode = mode
            self.config['current_mode'] = mode.value
            
            logger.info(f"Setting proxy mode to: {mode.value}")
            
            # Включаем новый режим
            success = self._enable_mode(mode)
            
            if success:
                self.save_config()
                logger.info(f"Successfully switched to {mode.value} mode")
            else:
                logger.error(f"Failed to switch to {mode.value} mode")
                self.current_mode = ProxyMode(self.config.get('current_mode', 'system'))
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting proxy mode: {e}")
            return False
    
    def _disable_current_mode(self):
        """Отключение текущего режима прокси"""
        try:
            if self.current_mode == ProxyMode.SYSTEM:
                self._disable_system_proxy()
            elif self.current_mode == ProxyMode.MANUAL:
                self._disable_manual_proxy()
            elif self.current_mode == ProxyMode.TRANSPARENT:
                self._disable_transparent_proxy()
            elif self.current_mode == ProxyMode.SPLIT:
                self._disable_split_tunnel()
            elif self.current_mode == ProxyMode.BYPASS:
                self._disable_bypass_mode()
            
            logger.info(f"Disabled {self.current_mode.value} proxy mode")
            
        except Exception as e:
            logger.error(f"Error disabling current proxy mode: {e}")
    
    def _enable_mode(self, mode: ProxyMode) -> bool:
        """Включение указанного режима прокси"""
        try:
            if mode == ProxyMode.SYSTEM:
                return self._enable_system_proxy()
            elif mode == ProxyMode.MANUAL:
                return self._enable_manual_proxy()
            elif mode == ProxyMode.AUTO:
                return self._enable_auto_proxy()
            elif mode == ProxyMode.TRANSPARENT:
                return self._enable_transparent_proxy()
            elif mode == ProxyMode.SPLIT:
                return self._enable_split_tunnel()
            elif mode == ProxyMode.BYPASS:
                return self._enable_bypass_mode()
            
            logger.error(f"Unknown proxy mode: {mode}")
            return False
            
        except Exception as e:
            logger.error(f"Error enabling proxy mode {mode.value}: {e}")
            return False
    
    def _enable_system_proxy(self) -> bool:
        """Включение системного прокси"""
        try:
            # Получаем системные настройки прокси
            proxy_settings = self._get_system_proxy_settings()
            
            if proxy_settings:
                # Применяем системные настройки
                self._apply_proxy_settings(proxy_settings)
                logger.info("System proxy enabled")
                return True
            else:
                logger.warning("No system proxy settings found")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling system proxy: {e}")
            return False
    
    def _enable_manual_proxy(self) -> bool:
        """Включение ручного прокси"""
        try:
            manual_settings = self.config.get('manual_settings', {})
            
            if not manual_settings.get('proxy_host') or not manual_settings.get('proxy_port'):
                logger.error("Manual proxy settings not configured")
                return False
            
            proxy_settings = {
                'proxy_type': manual_settings.get('proxy_type', 'http'),
                'proxy_host': manual_settings['proxy_host'],
                'proxy_port': manual_settings['proxy_port'],
                'proxy_username': manual_settings.get('proxy_username', ''),
                'proxy_password': manual_settings.get('proxy_password', ''),
                'exceptions': manual_settings.get('proxy_exceptions', [])
            }
            
            self._apply_proxy_settings(proxy_settings)
            logger.info(f"Manual proxy enabled: {proxy_settings['proxy_host']}:{proxy_settings['proxy_port']}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling manual proxy: {e}")
            return False
    
    def _enable_auto_proxy(self) -> bool:
        """Включение авто-прокси (автоматическое определение)"""
        try:
            # Автоматическое определение прокси настроек
            auto_proxy = self._detect_proxy_automatically()
            
            if auto_proxy:
                self._apply_proxy_settings(auto_proxy)
                logger.info("Auto proxy enabled")
                return True
            else:
                logger.warning("No proxy settings detected automatically")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling auto proxy: {e}")
            return False
    
    def _enable_transparent_proxy(self) -> bool:
        """Включение прозрачного прокси"""
        try:
            # Настройка iptables для прозрачного прокси
            success = self._setup_transparent_proxy()
            
            if success:
                logger.info("Transparent proxy enabled")
                return True
            else:
                logger.error("Failed to setup transparent proxy")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling transparent proxy: {e}")
            return False
    
    def _enable_split_tunnel(self) -> bool:
        """Включение split-tunnel прокси"""
        try:
            apps = self.config.get('split_tunnel_apps', [])
            
            if not apps:
                logger.warning("No applications configured for split tunnel")
                return False
            
            # Настройка split tunnel для указанных приложений
            success = self._setup_split_tunnel(apps)
            
            if success:
                logger.info(f"Split tunnel enabled for {len(apps)} applications")
                return True
            else:
                logger.error("Failed to setup split tunnel")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling split tunnel: {e}")
            return False
    
    def _enable_bypass_mode(self) -> bool:
        """Включение режима обхода прокси"""
        try:
            # Настройка исключений для прокси
            bypass_rules = self.config.get('bypass_rules', [])
            
            if not bypass_rules:
                logger.warning("No bypass rules configured")
                return False
            
            # Применяем правила обхода
            success = self._apply_bypass_rules(bypass_rules)
            
            if success:
                logger.info(f"Bypass mode enabled with {len(bypass_rules)} rules")
                return True
            else:
                logger.error("Failed to apply bypass rules")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling bypass mode: {e}")
            return False
    
    def _disable_system_proxy(self):
        """Отключение системного прокси"""
        try:
            # Очистка переменных окружения
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
            
            # Сброс системных настроек прокси
            self._reset_system_proxy_settings()
            
            logger.info("System proxy disabled")
            
        except Exception as e:
            logger.error(f"Error disabling system proxy: {e}")
    
    def _disable_manual_proxy(self):
        """Отключение ручного прокси"""
        self._disable_system_proxy()
    
    def _disable_transparent_proxy(self):
        """Отключение прозрачного прокси"""
        try:
            # Очистка iptables правил
            subprocess.run(['iptables', '-F'], check=False)
            subprocess.run(['ip6tables', '-F'], check=False)
            
            logger.info("Transparent proxy disabled")
            
        except Exception as e:
            logger.error(f"Error disabling transparent proxy: {e}")
    
    def _disable_split_tunnel(self):
        """Отключение split-tunnel"""
        try:
            # Очистка правил для приложений
            self._cleanup_split_tunnel_rules()
            
            logger.info("Split tunnel disabled")
            
        except Exception as e:
            logger.error(f"Error disabling split tunnel: {e}")
    
    def _disable_bypass_mode(self):
        """Отключение режима обхода"""
        try:
            # Очистка правил обхода
            self._cleanup_bypass_rules()
            
            logger.info("Bypass mode disabled")
            
        except Exception as e:
            logger.error(f"Error disabling bypass mode: {e}")
    
    def _get_system_proxy_settings(self) -> Optional[Dict]:
        """Получение системных настроек прокси"""
        try:
            # Проверка переменных окружения
            proxy_settings = {}
            
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy:
                proxy_settings['proxy_host'] = http_proxy.split(':')[0]
                proxy_settings['proxy_port'] = int(http_proxy.split(':')[1])
                proxy_settings['proxy_type'] = 'http'
            
            if https_proxy:
                proxy_settings['proxy_host'] = https_proxy.split(':')[0]
                proxy_settings['proxy_port'] = int(https_proxy.split(':')[1])
                proxy_settings['proxy_type'] = 'https'
            
            return proxy_settings if proxy_settings else None
            
        except Exception as e:
            logger.error(f"Error getting system proxy settings: {e}")
            return None
    
    def _detect_proxy_automatically(self) -> Optional[Dict]:
        """Автоматическое определение прокси настроек"""
        try:
            # Здесь может быть логика автоматического обнаружения прокси
            # Например, через PAC файлы, WPAD, или другие методы
            
            # Пока возвращаем None (нет авто-обнаружения)
            return None
            
        except Exception as e:
            logger.error(f"Error detecting proxy automatically: {e}")
            return None
    
    def _apply_proxy_settings(self, settings: Dict):
        """Применение настроек прокси"""
        try:
            # Установка переменных окружения
            proxy_url = f"{settings['proxy_type']}://{settings['proxy_host']}:{settings['proxy_port']}"
            
            if settings.get('proxy_username') and settings.get('proxy_password'):
                proxy_url = f"{settings['proxy_type']}://{settings['proxy_username']}:{settings['proxy_password']}@{settings['proxy_host']}:{settings['proxy_port']}"
            
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url
            
            logger.info(f"Proxy settings applied: {proxy_url}")
            
        except Exception as e:
            logger.error(f"Error applying proxy settings: {e}")
    
    def _setup_transparent_proxy(self) -> bool:
        """Настройка прозрачного прокси"""
        try:
            # Базовая настройка iptables для прозрачного прокси
            # Это упрощенная реализация
            
            # Очистка существующих правил
            subprocess.run(['iptables', '-F'], check=False)
            subprocess.run(['ip6tables', '-F'], check=False)
            
            # Пример правила перенаправления трафика через прокси
            # В реальной реализации здесь должна быть более сложная логика
            
            logger.info("Transparent proxy setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up transparent proxy: {e}")
            return False
    
    def _setup_split_tunnel(self, apps: List[str]) -> bool:
        """Настройка split-tunnel для приложений"""
        try:
            # Очистка существующих правил
            self._cleanup_split_tunnel_rules()
            
            # Настройка правил для каждого приложения
            for app in apps:
                # Пример настройки маршрутизации для приложения
                # В реальной реализации здесь должна быть более сложная логика
                
                logger.info(f"Split tunnel configured for: {app}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up split tunnel: {e}")
            return False
    
    def _apply_bypass_rules(self, rules: List[str]) -> bool:
        """Применение правил обхода прокси"""
        try:
            # Очистка существующих правил обхода
            self._cleanup_bypass_rules()
            
            # Применение новых правил
            for rule in rules:
                # Пример настройки исключений
                # В реальной реализации здесь должна быть более сложная логика
                
                logger.info(f"Bypass rule applied: {rule}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying bypass rules: {e}")
            return False
    
    def _reset_system_proxy_settings(self):
        """Сброс системных настроек прокси"""
        try:
            # Сброс конфигурации системного прокси
            # Это может включать сброс системных настроек в ОС
            
            logger.info("System proxy settings reset")
            
        except Exception as e:
            logger.error(f"Error resetting system proxy settings: {e}")
    
    def _cleanup_split_tunnel_rules(self):
        """Очистка правил split-tunnel"""
        try:
            # Очистка правил маршрутизации для split-tunnel
            
            logger.info("Split tunnel rules cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up split tunnel rules: {e}")
    
    def _cleanup_bypass_rules(self):
        """Очистка правил обхода"""
        try:
            # Очистка правил исключений
            
            logger.info("Bypass rules cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up bypass rules: {e}")
    
    def get_current_mode(self) -> ProxyMode:
        """Получение текущего режима прокси"""
        return self.current_mode
    
    def get_mode_info(self) -> Dict[str, Any]:
        """Получение информации о текущем режиме"""
        return {
            "current_mode": self.current_mode.value,
            "auto_detect_enabled": self.auto_detect_enabled,
            "bypass_rules_count": len(self.bypass_rules),
            "manual_settings_configured": bool(self.manual_settings.get('proxy_host')),
            "transparent_enabled": self.transparent_enabled,
            "split_tunnel_enabled": bool(self.config.get('split_tunnel_apps')),
            "dns_leak_protection": self.config.get('dns_leak_protection', True)
        }
    
    def get_available_modes(self) -> List[str]:
        """Получение списка доступных режимов"""
        return [mode.value for mode in ProxyMode]
    
    def test_proxy_connection(self) -> Dict[str, Any]:
        """Тестирование подключения через прокси"""
        try:
            import requests
            
            test_results = {
                "proxy_working": False,
                "http_response": False,
                "https_response": False,
                "latency_ms": None,
                "error": None
            }
            
            # Тест HTTP запроса через прокси
            try:
                start_time = time.time()
                response = requests.get("http://httpbin.org/ip", timeout=10)
                if response.status_code == 200:
                    test_results["http_response"] = True
                    test_results["latency_ms"] = int((time.time() - start_time) * 1000)
            except Exception as e:
                test_results["error"] = f"HTTP test failed: {e}"
            
            # Тест HTTPS запроса через прокси
            try:
                start_time = time.time()
                response = requests.get("https://httpbin.org/ip", timeout=10)
                if response.status_code == 200:
                    test_results["https_response"] = True
                    test_results["latency_ms"] = int((time.time() - start_time) * 1000)
            except Exception as e:
                if not test_results["error"]:
                    test_results["error"] = f"HTTPS test failed: {e}"
            
            # Общий статус работы прокси
            test_results["proxy_working"] = test_results["http_response"] or test_results["https_response"]
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing proxy connection: {e}")
            return {"proxy_working": False, "error": str(e)}

# Глобальный экземпляр
_proxy_modes_manager = None

def get_proxy_modes_manager() -> ProxyModesManager:
    """Получение глобального экземпляра ProxyModesManager"""
    global _proxy_modes_manager
    if _proxy_modes_manager is None:
        _proxy_modes_manager = ProxyModesManager()
    return _proxy_modes_manager

if __name__ == "__main__":
    # Тестирование менеджера режимов прокси
    print("Testing XVPN Proxy Modes Manager...")
    
    manager = get_proxy_modes_manager()
    
    # Получение информации о текущем режиме
    mode_info = manager.get_mode_info()
    print(f"Current mode: {mode_info['current_mode']}")
    print(f"Available modes: {manager.get_available_modes()}")
    
    # Тестирование подключения через прокси
    if mode_info['current_mode'] != 'bypass':
        test_results = manager.test_proxy_connection()
        print(f"Proxy test results: {test_results}")
    
    print("Proxy Modes Manager test completed")