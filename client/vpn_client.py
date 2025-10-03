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
import traceback
from pathlib import Path
from typing import Dict, Optional, Any, Callable

# Импорт модулей
from state_machine import VPNStateMachine, State, Event
from chatvpn_backend import start_xray, stop_xray, get_status, load_config_from_server
from transport_manager import get_transport_manager
from health import get_mask_score, get_network_info

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / 'chatvpn' / 'client' / 'logs' / 'vpn_client.log')
    ]
)
logger = logging.getLogger(__name__)

class VPNClient:
    """Основной VPN клиент с интеграцией state machine"""
    
    def __init__(self, client_uuid: str = None):
        """Инициализация VPN клиента с улучшенным error handling"""
        # Определение UUID клиента
        self.client_uuid = client_uuid or self._get_or_create_uuid()
        
        # Пути
        self.config_path = Path.home() / 'chatvpn' / 'client' / 'client.json'
        self.state_dir = Path.home() / 'chatvpn' / 'client' / 'states'
        self.log_dir = Path.home() / 'chatvpn' / 'client' / 'logs'
        
        # Создание директорий
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise
        
        # Инициализация компонентов
        self.state_machine = None
        self.transport_manager = None
        self.running = False
        self.gui_callbacks = []
        self.error_handlers = []
        
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
        """Инициализация клиента с улучшенным error handling"""
        try:
            logger.info("Initializing VPN Client...")
            
            # Создание state machine
            try:
                self.state_machine = VPNStateMachine(self.client_uuid)
            except Exception as e:
                logger.error(f"Failed to create state machine: {e}")
                raise
            
            # Создание transport manager
            try:
                self.transport_manager = get_transport_manager(self.client_uuid)
            except Exception as e:
                logger.error(f"Failed to create transport manager: {e}")
                raise
            
            # Добавление callback для состояний
            try:
                self.state_machine.add_state_callback(State.RUNNING, self._on_state_running)
                self.state_machine.add_state_callback(State.ERROR, self._on_state_error)
                self.state_machine.add_state_callback(State.STOPPING, self._on_state_stopping)
            except Exception as e:
                logger.error(f"Failed to add state callbacks: {e}")
                raise
            
            # Загрузка конфигурации
            try:
                self._load_initial_config()
            except Exception as e:
                logger.error(f"Failed to load initial config: {e}")
                # Не критичная ошибка, продолжаем работу
            
            logger.info("VPN Client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize VPN Client: {e}")
            logger.error(traceback.format_exc())
            self._handle_error(e, "initialization")
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
        try:
            self._notify_gui(state, context)
            self._call_error_handlers("running", context)
        except Exception as e:
            logger.error(f"Error in RUNNING state callback: {e}")
            self._handle_error(e, "running_state")
    
    def _on_state_error(self, state, context):
        """Callback для состояния ERROR"""
        logger.error(f"VPN Client ERROR: {context.last_error}")
        try:
            self._notify_gui(state, context)
            self._call_error_handlers("error", context)
        except Exception as e:
            logger.error(f"Error in ERROR state callback: {e}")
            self._handle_error(e, "error_state")
    
    def _on_state_stopping(self, state, context):
        """Callback для состояния STOPPING"""
        logger.info("VPN Client is STOPPING")
        try:
            self._notify_gui(state, context)
            self._call_error_handlers("stopping", context)
        except Exception as e:
            logger.error(f"Error in STOPPING state callback: {e}")
            self._handle_error(e, "stopping_state")
    
    def _notify_gui(self, state, context):
        """Уведомление GUI о событии с улучшенным error handling"""
        for callback in self.gui_callbacks:
            try:
                callback(state, context)
            except Exception as e:
                logger.error(f"Error in GUI callback: {e}")
                logger.error(traceback.format_exc())
    
    def _handle_error(self, error: Exception, context: str):
        """Обработка ошибок с вызовом error handlers"""
        error_info = {
            "error": str(error),
            "type": type(error).__name__,
            "context": context,
            "timestamp": time.time(),
            "client_uuid": self.client_uuid
        }
        
        logger.error(f"Handling error in context {context}: {error}")
        
        # Вызов error handlers
        self._call_error_handlers("error", error_info)
        
        # Сохранение информации об ошибке
        self._save_error_log(error_info)
    
    def _call_error_handlers(self, event_type: str, data: Any):
        """Вызов всех зарегистрированных error handlers"""
        for handler in self.error_handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    def _save_error_log(self, error_info: Dict):
        """Сохранение информации об ошибке в лог файл"""
        error_log_file = self.log_dir / f"errors_{self.client_uuid}.log"
        try:
            with open(error_log_file, 'a') as f:
                json.dump(error_info, f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to save error log: {e}")
    
    def add_error_handler(self, handler: Callable):
        """Добавление error handler"""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable):
        """Удаление error handler"""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def add_gui_callback(self, callback):
        """Добавление callback для GUI"""
        self.gui_callbacks.append(callback)
    
    def start(self):
        """Запуск VPN клиента с улучшенным error handling"""
        try:
            if not self.state_machine:
                logger.info("State machine not initialized, initializing...")
                if not self.initialize():
                    self._handle_error(Exception("Failed to initialize client"), "start")
                    return False
            
            if self.running:
                logger.warning("VPN Client is already running")
                return True
            
            self.running = True
            
            # Запуск state machine в отдельном потоке
            try:
                self.state_thread = threading.Thread(target=self.state_machine.start, daemon=True)
                self.state_thread.start()
                logger.info("VPN Client started successfully")
                return True
            except Exception as e:
                self.running = False
                logger.error(f"Failed to start state machine: {e}")
                self._handle_error(e, "start")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in start: {e}")
            self._handle_error(e, "start")
            return False
    
    def stop(self):
        """Остановка VPN клиента с улучшенным error handling"""
        try:
            if not self.running:
                logger.warning("VPN Client is not running")
                return True
            
            self.running = False
            
            if self.state_machine:
                try:
                    self.state_machine.stop()
                except Exception as e:
                    logger.error(f"Error stopping state machine: {e}")
                    self._handle_error(e, "stop")
            
            logger.info("VPN Client stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in stop: {e}")
            self._handle_error(e, "stop")
            return False
    
    def start_vpn(self):
        """Запуск VPN с улучшенным error handling"""
        try:
            if not self.state_machine:
                logger.warning("State machine not initialized")
                return False
            
            if not self.running:
                logger.warning("VPN Client is not running")
                return False
            
            self.state_machine.trigger_event(Event.START_REQUESTED)
            logger.info("VPN start requested")
            return True
            
        except Exception as e:
            logger.error(f"Error starting VPN: {e}")
            self._handle_error(e, "start_vpn")
            return False
    
    def stop_vpn(self):
        """Остановка VPN с улучшенным error handling"""
        try:
            if not self.state_machine:
                logger.warning("State machine not initialized")
                return False
            
            if not self.running:
                logger.warning("VPN Client is not running")
                return False
            
            self.state_machine.trigger_event(Event.STOP_REQUESTED)
            logger.info("VPN stop requested")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping VPN: {e}")
            self._handle_error(e, "stop_vpn")
            return False
    
    def get_status(self) -> Dict:
        """Получение статуса клиента с улучшенным error handling"""
        try:
            if self.state_machine:
                status = self.state_machine.get_state_info()
                if status:
                    return status
                else:
                    return {"error": "State machine returned no status"}
            else:
                return {"error": "State machine not initialized"}
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self._handle_error(e, "get_status")
            return {"error": f"Failed to get status: {e}"}
    
    @property
    def context(self):
        """Доступ к контексту state machine"""
        if self.state_machine:
            return self.state_machine.context
        return None
    
    def get_network_info(self) -> Dict:
        """Получение информации о сети с поддержкой IPv6"""
        try:
            return get_network_info()
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            self._handle_error(e, "get_network_info")
            return {}
    
    def get_ipv6_info(self) -> Dict:
        """Получение информации о IPv6 сети"""
        try:
            from health import get_ipv6_info
            return get_ipv6_info()
        except Exception as e:
            logger.error(f"Failed to get IPv6 info: {e}")
            self._handle_error(e, "get_ipv6_info")
            return {}
    
    def support_ipv6(self) -> bool:
        """Проверка поддержки IPv6"""
        try:
            ipv6_info = self.get_ipv6_info()
            return bool(ipv6_info.get("local_ipv6") or ipv6_info.get("external_ipv6"))
        except Exception as e:
            logger.error(f"Failed to check IPv6 support: {e}")
            self._handle_error(e, "support_ipv6")
            return False
    
    def get_health_score(self) -> int:
        """Получение оценки здоровья"""
        try:
            return get_mask_score()
        except Exception as e:
            logger.error(f"Failed to get health score: {e}")
            self._handle_error(e, "get_health_score")
            return 0
    
    def get_transport_info(self) -> Dict:
        """Получение информации о транспорте"""
        try:
            if self.transport_manager:
                current = self.transport_manager.get_current_transport()
                available = self.transport_manager.get_available_transports()
                return {
                    "current": current,
                    "available_count": len(available),
                    "available_transports": available
                }
            return {"error": "Transport manager not initialized"}
        except Exception as e:
            logger.error(f"Failed to get transport info: {e}")
            self._handle_error(e, "get_transport_info")
            return {"error": f"Failed to get transport info: {e}"}
    
    def force_transport_switch(self, transport_id: str) -> bool:
        """Принудительное переключение транспорта"""
        try:
            if not self.transport_manager:
                logger.warning("Transport manager not initialized")
                return False
            
            if not self.running:
                logger.warning("VPN Client is not running")
                return False
            
            success = self.transport_manager.force_transport_switch(transport_id)
            if success:
                logger.info(f"Forced transport switch to {transport_id}")
            else:
                logger.warning(f"Failed to force transport switch to {transport_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error forcing transport switch: {e}")
            self._handle_error(e, "force_transport_switch")
            return False
    
    def reload_config(self) -> bool:
        """Перезагрузка конфигурации"""
        try:
            if not self.state_machine:
                logger.warning("State machine not initialized")
                return False
            
            if not self.running:
                logger.warning("VPN Client is not running")
                return False
            
            self.state_machine.trigger_event(Event.START_REQUESTED)
            logger.info("Config reload requested")
            return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            self._handle_error(e, "reload_config")
            return False
    
    def get_client_uuid(self) -> str:
        """Получение UUID клиента"""
        return self.client_uuid
    
    def is_running(self) -> bool:
        """Проверка, запущен ли клиент"""
        try:
            if self.state_machine:
                return self.state_machine.get_current_state() == State.RUNNING
            return False
        except Exception as e:
            logger.error(f"Error checking if client is running: {e}")
            self._handle_error(e, "is_running")
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