#!/usr/bin/env python3
# XVPN Transport Manager
# Автоматическое переключение транспортов на основе доступности и производительности
# Абсолютный путь: ~/chatvpn/client/transport_manager.py

import os
import json
import time
import threading
import logging
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from discover import discover_transports

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransportManager:
    """Менеджер транспортов для автоматического переключения"""
    
    def __init__(self, client_uuid: str):
        self.client_uuid = client_uuid
        self.manifest_path = Path.home() / 'chatvpn' / 'client' / 'transports' / 'manifest.json'
        self.current_transport = None
        self.fallback_transports = []
        self.health_check_interval = 30
        self.max_failures = 3
        self.failure_count = 0
        self.last_health_check = 0
        self.health_check_thread = None
        self.running = False
        
        # Пути к логам
        self.log_dir = Path.home() / 'chatvpn' / 'client' / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / 'transport_manager.log'
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка логирования"""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    def load_manifest(self) -> Optional[Dict]:
        """Загрузка манифеста транспортов"""
        try:
            if not self.manifest_path.exists():
                logger.error(f"Manifest file not found: {self.manifest_path}")
                return None
                
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return None
    
    def fetch_client_config(self) -> Optional[Dict]:
        """Получение конфигурации клиента с сервера"""
        try:
            url = f"https://api.uss.hopto.org/clients/{self.client_uuid}.json"
            response = requests.get(url, timeout=10, verify=True)
            
            if response.status_code == 200:
                config = response.json()
                logger.info(f"Client config fetched successfully. Available transports: {config.get('available_transports', 0)}")
                return config
            else:
                logger.error(f"Failed to fetch client config: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching client config: {e}")
            return None
    
    def start_health_monitoring(self):
        """Запуск мониторинга здоровья транспортов"""
        if self.running:
            logger.warning("Health monitoring is already running")
            return
            
        self.running = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("Health monitoring started")
    
    def stop_health_monitoring(self):
        """Остановка мониторинга здоровья"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def _health_check_loop(self):
        """Цикл проверки здоровья транспортов"""
        while self.running:
            try:
                self._check_transports_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(5)
    
    def _check_transports_health(self):
        """Проверка здоровья всех транспортов"""
        try:
            # Получаем текущую конфигурацию
            config = self.fetch_client_config()
            if not config:
                logger.warning("Failed to fetch client config, skipping health check")
                return
            
            # Обновляем список транспортов
            self.current_transport = config.get('selected_transport')
            self.fallback_transports = config.get('fallback_transports', [])
            
            # Проверяем доступность текущего транспорта
            if self.current_transport:
                is_healthy = self._check_transport_health(self.current_transport)
                
                if not is_healthy:
                    self.failure_count += 1
                    logger.warning(f"Current transport {self.current_transport['id']} failed (count: {self.failure_count})")
                    
                    # Если достигли лимита сбоев, переключаемся на запасной
                    if self.failure_count >= self.max_failures and self.fallback_transports:
                        self._switch_to_fallback()
                    else:
                        logger.info("Waiting for transport recovery...")
                else:
                    self.failure_count = 0
                    logger.debug(f"Transport {self.current_transport['id']} is healthy")
            
        except Exception as e:
            logger.error(f"Error checking transports health: {e}")
    
    def _check_transport_health(self, transport: Dict) -> bool:
        """Проверка здоровья конкретного транспорта"""
        try:
            config = transport.get('config', {})
            host = config.get('server')
            port = config.get('port')
            
            if not host or not port:
                return False
            
            # Базовая проверка доступности
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                return False
            
            # Для TLS проверяем через HTTPS
            if config.get('tls', {}).get('enabled', False):
                try:
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    with socket.create_connection((host, port), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=host) as ssock:
                            return True
                except:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Transport health check failed: {e}")
            return False
    
    def _switch_to_fallback(self):
        """Переключение на запасной транспорт"""
        if not self.fallback_transports:
            logger.warning("No fallback transports available")
            return
        
        # Выбираем первый доступный запасной транспорт
        for fallback in self.fallback_transports:
            if self._check_transport_health(fallback):
                old_transport = self.current_transport
                self.current_transport = fallback
                self.failure_count = 0
                
                logger.info(f"Switched from {old_transport['id']} to {fallback['id']}")
                
                # Здесь можно добавить логику перезапуска VPN с новым транспортом
                self._restart_vpn_with_transport(fallback)
                break
        else:
            logger.error("No fallback transport is available")
    
    def _restart_vpn_with_transport(self, transport: Dict):
        """Перезапуск VPN с указанным транспортом"""
        try:
            # Здесь должна быть логика перезапуска VPN с новым транспортом
            # Пока просто записываем в лог
            logger.info(f"VPN restart requested with transport: {transport['id']}")
            
            # Пример: сохраняем конфигурацию и перезапускаем
            config = transport.get('config', {})
            vpn_config = {
                'server': config.get('server'),
                'port': config.get('port'),
                'protocol': config.get('protocol', 'tcp'),
                'type': transport.get('type'),
                'uuid': self.client_uuid
            }
            
            # Сохраняем конфигурацию
            config_path = Path.home() / 'chatvpn' / 'client' / 'current_transport.json'
            with open(config_path, 'w') as f:
                json.dump(vpn_config, f, indent=2)
            
            logger.info(f"Transport config saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Error restarting VPN with transport {transport['id']}: {e}")
    
    def get_current_transport(self) -> Optional[Dict]:
        """Получение текущего активного транспорта"""
        return self.current_transport
    
    def get_available_transports(self) -> List[Dict]:
        """Получение списка доступных транспортов"""
        try:
            config = self.fetch_client_config()
            if config:
                return config.get('fallback_transports', []) + [config.get('selected_transport')]
            return []
        except:
            return []
    
    def force_transport_switch(self, transport_id: str) -> bool:
        """Принудительное переключение на указанный транспорт"""
        try:
            available_transports = self.get_available_transports()
            
            for transport in available_transports:
                if transport.get('id') == transport_id:
                    if self._check_transport_health(transport):
                        old_transport = self.current_transport
                        self.current_transport = transport
                        self.failure_count = 0
                        
                        logger.info(f"Force switched from {old_transport['id'] if old_transport else 'None'} to {transport_id}")
                        self._restart_vpn_with_transport(transport)
                        return True
                    else:
                        logger.warning(f"Transport {transport_id} is not healthy")
                        return False
            
            logger.error(f"Transport {transport_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error forcing transport switch: {e}")
            return False

# Глобальный экземпляр для использования в других модулях
_transport_manager = None

def get_transport_manager(client_uuid: str) -> TransportManager:
    """Получение глобального экземпляра TransportManager"""
    global _transport_manager
    if _transport_manager is None or _transport_manager.client_uuid != client_uuid:
        _transport_manager = TransportManager(client_uuid)
    return _transport_manager

if __name__ == "__main__":
    # Тестирование менеджера транспортов
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 transport_manager.py <client_uuid>")
        sys.exit(1)
    
    client_uuid = sys.argv[1]
    manager = get_transport_manager(client_uuid)
    
    print(f"Testing Transport Manager for UUID: {client_uuid}")
    
    # Тестирование загрузки конфигурации
    config = manager.fetch_client_config()
    if config:
        print(f"✓ Client config fetched successfully")
        print(f"  Available transports: {config.get('available_transports', 0)}")
        print(f"  Selected transport: {config.get('selected_transport', {}).get('id', 'None')}")
    else:
        print("✗ Failed to fetch client config")
    
    # Тестирование списка доступных транспортов
    transports = manager.get_available_transports()
    print(f"\nAvailable transports: {len(transports)}")
    for i, transport in enumerate(transports, 1):
        print(f"  {i}. {transport.get('id')} - {transport.get('name')} (Priority: {transport.get('priority', 999)})")
    
    # Запуск мониторинга (на 30 секунд для теста)
    print("\nStarting health monitoring for 30 seconds...")
    manager.start_health_monitoring()
    time.sleep(30)
    manager.stop_health_monitoring()
    print("Health monitoring stopped")