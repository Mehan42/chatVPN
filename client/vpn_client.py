#!/usr/bin/env python3
# XVPN Client - Основной клиент с интеграцией state machine
# Абсолютный путь: ~/chatvpn/client/vpn_client.py

import os
import sys
import json
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Any

# Импорт модулей
from state_machine import VPNStateMachine, State, Event
from chatvpn_backend import start_xray, stop_xray, get_status, load_config_from_server
from transport_manager import get_transport_manager
from health import get_mask_score, get_network_info

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VPNClient:
    """Основной VPN клиент с интеграцией state machine"""
    
    def __init__(self, client_uuid: str = None):
        # Определение UUID клиента
        self.client_uuid = client_uuid or self._get_or_create_uuid()
        
        # Пути
        self.config_path = Path.home() / 'chatvpn' / 'client' / 'client.json'
        self.state_dir = Path.home() / 'chatvpn' / 'client' / 'states'
        self.log_dir = Path.home() / 'chatvpn' / 'client' / 'logs'
        
        # Создание директорий
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализация компонентов
        self.state_machine = None
        self.transport_manager = None
        self.running = False
        self.gui_callbacks = []
        
        # Настройка логирования
        self._setup_logging()
        
        logger.info(f"VPN Client initialized for UUID: {self.client_uuid}")
    
    def _get_or_create_uuid(self) -> str:
        """Получение или создание UUID клиента"""
        uuid_file = Path.home() / 'chatvpn' / 'client' / 'client.conf'
        
        if uuid_file.exists():
            with open(uuid_file, 'r') as f:
                return f.read().strip()
        
        # Генерация нового UUID
        new_uuid = str(uuid.uuid4())
        with open(uuid_file, 'w') as f:
            f.write(new_uuid)
        
        return new_uuid
    
    def _setup_logging(self):
        """Настройка логирования"""
        log_file = self.log_dir / f'vpn_client_{self.client_uuid}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - CLIENT - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def initialize(self):
        """Инициализация клиента"""
        try:
            logger.info("Initializing VPN Client...")
            
            # Создание state machine
            self.state_machine = VPNStateMachine(self.client_uuid)
            
            # Создание transport manager
            self.transport_manager = get_transport_manager(self.client_uuid)
            
            # Добавление callback для состояний
            self.state_machine.add_state_callback(State.RUNNING, self._on_state_running)
            self.state_machine.add_state_callback(State.ERROR, self._on_state_error)
            self.state_machine.add_state_callback(State.STOPPING, self._on_state_stopping)
            
            # Загрузка конфигурации
            self._load_initial_config()
            
            logger.info("VPN Client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize VPN Client: {e}")
            return False
    
    def _load_initial_config(self):
        """Загрузка начальной конфигурации"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded existing config for {config.get('uuid', 'unknown')}")
            else:
                logger.info("No existing config, will fetch from server")
                self.state_machine.trigger_event(Event.START_REQUESTED)
        except Exception as e:
            logger.error(f"Failed to load initial config: {e}")
            self.state_machine.trigger_event(Event.START_REQUESTED)
    
    def _on_state_running(self, state, context):
        """Callback для состояния RUNNING"""
        logger.info("VPN Client is RUNNING")
        self._notify_gui("running", context)
    
    def _on_state_error(self, state, context):
        """Callback для состояния ERROR"""
        logger.error(f"VPN Client ERROR: {context.last_error}")
        self._notify_gui("error", context)
    
    def _on_state_stopping(self, state, context):
        """Callback для состояния STOPPING"""
        logger.info("VPN Client is STOPPING")
        self._notify_gui("stopping", context)
    
    def _notify_gui(self, event_type: str, context):
        """Уведомление GUI о событии"""
        for callback in self.gui_callbacks:
            try:
                callback(event_type, context)
            except Exception as e:
                logger.error(f"Error in GUI callback: {e}")
    
    def add_gui_callback(self, callback):
        """Добавление callback для GUI"""
        self.gui_callbacks.append(callback)
    
    def start(self):
        """Запуск VPN клиента"""
        if not self.state_machine:
            if not self.initialize():
                return False
        
        self.running = True
        
        # Запуск state machine в отдельном потоке
        self.state_thread = threading.Thread(target=self.state_machine.start, daemon=True)
        self.state_thread.start()
        
        logger.info("VPN Client started")
        return True
    
    def stop(self):
        """Остановка VPN клиента"""
        self.running = False
        
        if self.state_machine:
            self.state_machine.stop()
        
        logger.info("VPN Client stopped")
    
    def start_vpn(self):
        """Запуск VPN"""
        if self.state_machine:
            self.state_machine.trigger_event(Event.START_REQUESTED)
            return True
        return False
    
    def stop_vpn(self):
        """Остановка VPN"""
        if self.state_machine:
            self.state_machine.trigger_event(Event.STOP_REQUESTED)
            return True
        return False
    
    def get_status(self) -> Dict:
        """Получение статуса клиента"""
        if self.state_machine:
            return self.state_machine.get_state_info()
        return {"error": "State machine not initialized"}
    
    def get_network_info(self) -> Dict:
        """Получение информации о сети с поддержкой IPv6"""
        try:
            return get_network_info()
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {}
    
    def get_ipv6_info(self) -> Dict:
        """Получение информации о IPv6 сети"""
        try:
            from health import get_ipv6_info
            return get_ipv6_info()
        except Exception as e:
            logger.error(f"Failed to get IPv6 info: {e}")
            return {}
    
    def support_ipv6(self) -> bool:
        """Проверка поддержки IPv6"""
        try:
            ipv6_info = self.get_ipv6_info()
            return bool(ipv6_info.get("local_ipv6") or ipv6_info.get("external_ipv6"))
        except Exception as e:
            logger.error(f"Failed to check IPv6 support: {e}")
            return False
    
    def get_health_score(self) -> int:
        """Получение оценки здоровья"""
        try:
            return get_mask_score()
        except Exception as e:
            logger.error(f"Failed to get health score: {e}")
            return 0
    
    def get_transport_info(self) -> Dict:
        """Получение информации о транспорте"""
        if self.transport_manager:
            current = self.transport_manager.get_current_transport()
            available = self.transport_manager.get_available_transports()
            return {
                "current": current,
                "available_count": len(available),
                "available_transports": available
            }
        return {}
    
    def force_transport_switch(self, transport_id: str) -> bool:
        """Принудительное переключение транспорта"""
        if self.transport_manager:
            return self.transport_manager.force_transport_switch(transport_id)
        return False
    
    def reload_config(self) -> bool:
        """Перезагрузка конфигурации"""
        if self.state_machine:
            self.state_machine.trigger_event(Event.START_REQUESTED)
            return True
        return False
    
    def get_client_uuid(self) -> str:
        """Получение UUID клиента"""
        return self.client_uuid
    
    def is_running(self) -> bool:
        """Проверка, запущен ли клиент"""
        if self.state_machine:
            return self.state_machine.get_current_state() == State.RUNNING
        return False

# Глобальный экземпляр клиента
_vpn_client = None

def get_vpn_client(client_uuid: str = None) -> VPNClient:
    """Получение глобального экземпляра VPN клиента"""
    global _vpn_client
    if _vpn_client is None or (_vpn_client.client_uuid != client_uuid and client_uuid):
        _vpn_client = VPNClient(client_uuid)
    return _vpn_client

# Командная строка интерфейс
def main():
    """Основная функция для командной строки"""
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN Client")
    parser.add_argument("command", choices=["start", "stop", "status", "config", "uuid"], help="Команда")
    parser.add_argument("--uuid", help="Client UUID")
    
    args = parser.parse_args()
    
    # Получение клиента
    client = get_vpn_client(args.uuid)
    
    # Инициализация
    if not client.initialize():
        print("Failed to initialize VPN Client")
        sys.exit(1)
    
    # Выполнение команды
    if args.command == "start":
        if client.start_vpn():
            print("VPN start requested")
        else:
            print("Failed to start VPN")
    
    elif args.command == "stop":
        if client.stop_vpn():
            print("VPN stop requested")
        else:
            print("Failed to stop VPN")
    
    elif args.command == "status":
        status = client.get_status()
        print(f"Current state: {status.get('current_state', 'unknown')}")
        print(f"Health score: {client.get_health_score()}")
        print(f"Network info: {client.get_network_info()}")
        transport_info = client.get_transport_info()
        if transport_info.get('current'):
            print(f"Current transport: {transport_info['current']['id']}")
        print(f"Available transports: {transport_info.get('available_count', 0)}")
    
    elif args.command == "config":
        if client.reload_config():
            print("Config reload requested")
        else:
            print("Failed to reload config")
    
    elif args.command == "uuid":
        print(f"Client UUID: {client.get_client_uuid()}")

if __name__ == "__main__":
    main()