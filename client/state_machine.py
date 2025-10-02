#!/usr/bin/env python3
# XVPN State Machine
# Полная машина состояний клиента
# Абсолютный путь: ~/chatvpn/client/state_machine.py

import json
import time
import logging
import threading
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from transport_manager import get_transport_manager
from health import get_mask_score, get_network_info
from chatvpn_backend import start_xray, stop_xray, get_status, load_config_from_server

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class State(Enum):
    """Состояния VPN клиента"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    CONFIG_FETCHING = "config_fetching"
    CONFIG_VALIDATING = "config_validating"
    STARTING = "starting"
    RUNNING = "running"
    HEALTH_CHECKING = "health_checking"
    SWITCHING_TRANSPORT = "switching_transport"
    STOPPING = "stopping"
    ERROR = "error"
    RECOVERING = "recovering"
    UPDATING = "updating"

class Event(Enum):
    """События для машины состояний"""
    START_REQUESTED = "start_requested"
    STOP_REQUESTED = "stop_requested"
    CONFIG_FETCHED = "config_fetched"
    CONFIG_VALIDATED = "config_validated"
    START_SUCCESS = "start_success"
    START_FAILED = "start_failed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    HEALTH_CHECK_PASSED = "health_check_passed"
    TRANSPORT_SWITCH_FAILED = "transport_switch_failed"
    TRANSPORT_SWITCH_SUCCESS = "transport_switch_success"
    ERROR_OCCURRED = "error_occurred"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"
    UPDATE_AVAILABLE = "update_available"
    UPDATE_COMPLETED = "update_completed"

@dataclass
class Context:
    """Контекст машины состояний"""
    client_uuid: str
    current_state: State = State.INITIALIZING
    previous_state: Optional[State] = None
    state_entered_at: float = 0
    last_error: Optional[str] = None
    error_count: int = 0
    transport_manager = None
    config_data: Optional[Dict] = None
    current_transport: Optional[Dict] = None
    health_score: int = 0
    network_info: Optional[Dict] = None
    retry_count: int = 0
    max_retries: int = 3
    last_health_check: float = 0
    health_check_interval: int = 30
    
    def __post_init__(self):
        if self.transport_manager is None:
            self.transport_manager = get_transport_manager(self.client_uuid)

@dataclass
class Transition:
    """Правило перехода состояний"""
    from_state: State
    event: Event
    to_state: State
    action: Optional[Callable] = None
    condition: Optional[Callable] = None
    timeout: Optional[int] = None

class VPNStateMachine:
    """Полная машина состояний VPN клиента"""
    
    def __init__(self, client_uuid: str):
        self.client_uuid = client_uuid
        self.context = Context(client_uuid=client_uuid)
        self.running = False
        self.state_history = []
        self.event_queue = []
        self.lock = threading.Lock()
        self.state_callbacks = {}
        
        # Инициализация путей
        self.state_dir = Path.home() / 'chatvpn' / 'client' / 'states'
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Определение правил переходов
        self.transitions = self._define_transitions()
        
        # Настройка логирования
        self._setup_logging()
        
        logger.info(f"State Machine initialized for client {client_uuid}")
    
    def _setup_logging(self):
        """Настройка логирования машины состояний"""
        log_file = self.state_dir / f'state_machine_{self.client_uuid}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - STATE - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _define_transitions(self) -> List[Transition]:
        """Определение правил переходов состояний"""
        transitions = [
            # Инициализация
            Transition(State.INITIALIZING, Event.START_REQUESTED, State.CONFIG_FETCHING),
            
            # Ожидание конфигурации
            Transition(State.CONFIG_FETCHING, Event.CONFIG_FETCHED, State.CONFIG_VALIDATING),
            Transition(State.CONFIG_FETCHING, Event.ERROR_OCCURRED, State.ERROR),
            
            # Валидация конфигурации
            Transition(State.CONFIG_VALIDATING, Event.CONFIG_VALIDATED, State.IDLE),
            Transition(State.CONFIG_VALIDATING, Event.ERROR_OCCURRED, State.ERROR),
            
            # Запуск VPN
            Transition(State.IDLE, Event.START_REQUESTED, State.STARTING),
            Transition(State.STARTING, Event.START_SUCCESS, State.RUNNING),
            Transition(State.STARTING, Event.START_FAILED, State.ERROR),
            Transition(State.STARTING, Event.ERROR_OCCURRED, State.ERROR),
            
            # Работа VPN
            Transition(State.RUNNING, Event.HEALTH_CHECK_FAILED, State.HEALTH_CHECKING),
            Transition(State.RUNNING, Event.TRANSPORT_SWITCH_FAILED, State.SWITCHING_TRANSPORT),
            Transition(State.RUNNING, Event.STOP_REQUESTED, State.STOPPING),
            Transition(State.RUNNING, Event.UPDATE_AVAILABLE, State.UPDATING),
            
            # Проверка здоровья
            Transition(State.HEALTH_CHECKING, Event.HEALTH_CHECK_PASSED, State.RUNNING),
            Transition(State.HEALTH_CHECKING, Event.HEALTH_CHECK_FAILED, State.SWITCHING_TRANSPORT),
            Transition(State.HEALTH_CHECKING, Event.ERROR_OCCURRED, State.ERROR),
            
            # Переключение транспорта
            Transition(State.SWITCHING_TRANSPORT, Event.TRANSPORT_SWITCH_SUCCESS, State.RUNNING),
            Transition(State.SWITCHING_TRANSPORT, Event.TRANSPORT_SWITCH_FAILED, State.RECOVERING),
            Transition(State.SWITCHING_TRANSPORT, Event.ERROR_OCCURRED, State.ERROR),
            
            # Остановка VPN
            Transition(State.STOPPING, Event.STOP_REQUESTED, State.IDLE),
            Transition(State.STOPPING, Event.ERROR_OCCURRED, State.ERROR),
            
            # Восстановление
            Transition(State.RECOVERING, Event.RECOVERY_SUCCESS, State.RUNNING),
            Transition(State.RECOVERING, Event.RECOVERY_FAILED, State.ERROR),
            Transition(State.ERROR, Event.START_REQUESTED, State.RECOVERING),
            
            # Обновление
            Transition(State.UPDATING, Event.UPDATE_COMPLETED, State.RUNNING),
            Transition(State.UPDATING, Event.ERROR_OCCURRED, State.ERROR),
        ]
        return transitions
    
    def add_state_callback(self, state: State, callback: Callable):
        """Добавление callback для состояния"""
        if state not in self.state_callbacks:
            self.state_callbacks[state] = []
        self.state_callbacks[state].append(callback)
    
    def trigger_event(self, event: Event, data: Optional[Dict] = None):
        """Триггер события"""
        with self.lock:
            self.event_queue.append((event, data or {}))
            logger.info(f"Event queued: {event.value}")
    
    def process_events(self):
        """Обработка событий"""
        while self.event_queue:
            with self.lock:
                event, data = self.event_queue.pop(0)
            
            self._handle_event(event, data)
    
    def _handle_event(self, event: Event, data: Dict):
        """Обработка单个 события"""
        transition = self._find_transition(self.context.current_state, event)
        
        if transition:
            self._execute_transition(transition, data)
        else:
            logger.warning(f"No transition found for {self.context.current_state.value} -> {event.value}")
    
    def _find_transition(self, from_state: State, event: Event) -> Optional[Transition]:
        """Поиск правила перехода"""
        for transition in self.transitions:
            if transition.from_state == from_state and transition.event == event:
                if transition.condition and not transition.condition(self.context, data):
                    continue
                return transition
        return None
    
    def _execute_transition(self, transition: Transition, data: Dict):
        """Выполнение перехода состояний"""
        old_state = self.context.current_state
        new_state = transition.to_state
        
        logger.info(f"State transition: {old_state.value} -> {new_state.value}")
        
        # Выполнение действия перехода
        if transition.action:
            try:
                transition.action(self.context, data)
            except Exception as e:
                logger.error(f"Error in transition action: {e}")
                self.trigger_event(Event.ERROR_OCCURRED)
                return
        
        # Обновление контекста
        self.context.previous_state = old_state
        self.context.current_state = new_state
        self.context.state_entered_at = time.time()
        
        # Выполнение callback для нового состояния
        self._execute_state_callbacks(new_state)
        
        # Сохранение истории состояний
        self._save_state_history(old_state, new_state)
    
    def _execute_state_actions(self, state: State):
        """Выполнение действий для состояния"""
        actions = {
            State.INITIALIZING: self._action_initializing,
            State.CONFIG_FETCHING: self._action_config_fetching,
            State.CONFIG_VALIDATING: self._action_config_validating,
            State.IDLE: self._action_idle,
            State.STARTING: self._action_starting,
            State.RUNNING: self._action_running,
            State.HEALTH_CHECKING: self._action_health_checking,
            State.SWITCHING_TRANSPORT: self._action_switching_transport,
            State.STOPPING: self._action_stopping,
            State.ERROR: self._action_error,
            State.RECOVERING: self._action_recovering,
            State.UPDATING: self._action_updating,
        }
        
        action = actions.get(state)
        if action:
            try:
                action(self.context)
            except Exception as e:
                logger.error(f"Error in state action {state.value}: {e}")
                self.trigger_event(Event.ERROR_OCCURRED)
    
    def _action_initializing(self, context: Context):
        """Действия для состояния инициализации"""
        logger.info("Initializing VPN client...")
        
        # Загрузка конфигурации
        config_path = Path.home() / 'chatvpn' / 'client' / 'client.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                context.config_data = json.load(f)
        
        # Получение сетевой информации
        context.network_info = get_network_info()
        
        # Установка начального состояния
        self.trigger_event(Event.START_REQUESTED)
    
    def _action_config_fetching(self, context: Context):
        """Действия для состояния загрузки конфигурации"""
        logger.info("Fetching configuration from server...")
        
        try:
            success = load_config_from_server()
            if success:
                self.trigger_event(Event.CONFIG_FETCHED)
            else:
                raise Exception("Failed to fetch configuration")
        except Exception as e:
            logger.error(f"Config fetch failed: {e}")
            context.last_error = str(e)
            self.trigger_event(Event.ERROR_OCCURRED)
    
    def _action_config_validating(self, context: Context):
        """Действия для состояния валидации конфигурации"""
        logger.info("Validating configuration...")
        
        if not context.config_data:
            raise Exception("No configuration data")
        
        # Проверка структуры конфигурации
        required_fields = ['uuid', 'transports']
        for field in required_fields:
            if field not in context.config_data:
                raise Exception(f"Missing required field: {field}")
        
        # Выбор транспорта
        transport_manager = context.transport_manager
        if transport_manager:
            context.current_transport = transport_manager.get_current_transport()
        
        if context.current_transport:
            self.trigger_event(Event.CONFIG_VALIDATED)
        else:
            raise Exception("No available transport")
    
    def _action_idle(self, context: Context):
        """Действия для состояния ожидания"""
        logger.info("VPN client idle")
        
        # Периодическая проверка конфигурации
        if time.time() - context.last_health_check > 300:  # 5 минут
            self.trigger_event(Event.START_REQUESTED)
    
    def _action_starting(self, context: Context):
        """Действия для состояния запуска"""
        logger.info("Starting VPN...")
        
        try:
            if start_xray():
                self.trigger_event(Event.START_SUCCESS)
            else:
                raise Exception("Failed to start Xray")
        except Exception as e:
            logger.error(f"Start failed: {e}")
            context.last_error = str(e)
            self.trigger_event(Event.START_FAILED)
    
    def _action_running(self, context: Context):
        """Действия для состояния работы"""
        logger.info("VPN running")
        
        # Запуск мониторинга здоровья
        self._start_health_monitoring()
        
        # Обновление информации о сети
        context.network_info = get_network_info()
        context.health_score = get_mask_score()
    
    def _action_health_checking(self, context: Context):
        """Действия для проверки здоровья"""
        logger.info("Performing health check...")
        
        try:
            health_score = get_mask_score()
            if health_score >= 3:
                self.trigger_event(Event.HEALTH_CHECK_PASSED)
            else:
                self.trigger_event(Event.HEALTH_CHECK_FAILED)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.trigger_event(Event.ERROR_OCCURRED)
    
    def _action_switching_transport(self, context: Context):
        """Действия для переключения транспорта"""
        logger.info("Switching transport...")
        
        try:
            if context.transport_manager and context.fallback_transports:
                success = context.transport_manager.force_transport_switch(
                    context.fallback_transports[0]['id']
                )
                if success:
                    self.trigger_event(Event.TRANSPORT_SWITCH_SUCCESS)
                else:
                    self.trigger_event(Event.TRANSPORT_SWITCH_FAILED)
            else:
                raise Exception("No fallback transport available")
        except Exception as e:
            logger.error(f"Transport switch failed: {e}")
            self.trigger_event(Event.ERROR_OCCURRED)
    
    def _action_stopping(self, context: Context):
        """Действия для остановки"""
        logger.info("Stopping VPN...")
        
        try:
            stop_xray()
            self.trigger_event(Event.STOP_REQUESTED)
        except Exception as e:
            logger.error(f"Stop failed: {e}")
            self.trigger_event(Event.ERROR_OCCURRED)
    
    def _action_error(self, context: Context):
        """Действия для состояния ошибки"""
        logger.error(f"VPN client in error state: {context.last_error}")
        
        # Попытка восстановления
        if context.error_count < context.max_retries:
            context.error_count += 1
            self.trigger_event(Event.START_REQUESTED)
        else:
            logger.error("Max retries reached, giving up")
    
    def _action_recovering(self, context: Context):
        """Действия для восстановления"""
        logger.info("Attempting recovery...")
        
        try:
            # Перезапуск VPN
            stop_xray()
            time.sleep(2)
            
            if start_xray():
                self.trigger_event(Event.RECOVERY_SUCCESS)
            else:
                raise Exception("Failed to recover")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.trigger_event(Event.RECOVERY_FAILED)
    
    def _action_updating(self, context: Context):
        """Действия для обновления"""
        logger.info("Updating VPN configuration...")
        
        try:
            # Загрузка новой конфигурации
            success = load_config_from_server()
            if success:
                self.trigger_event(Event.UPDATE_COMPLETED)
            else:
                raise Exception("Update failed")
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.trigger_event(Event.ERROR_OCCURRED)
    
    def _start_health_monitoring(self):
        """Запуск мониторинга здоровья"""
        def health_check_loop():
            while self.context.current_state == State.RUNNING:
                try:
                    time.sleep(self.context.health_check_interval)
                    self.trigger_event(Event.HEALTH_CHECK_FAILED)
                except Exception as e:
                    logger.error(f"Health check loop error: {e}")
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
    
    def _execute_state_callbacks(self, state: State):
        """Выполнение callback для состояния"""
        callbacks = self.state_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback(state, self.context)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def _save_state_history(self, from_state: State, to_state: State):
        """Сохранение истории состояний"""
        history_entry = {
            'timestamp': time.time(),
            'from_state': from_state.value,
            'to_state': to_state.value,
            'client_uuid': self.client_uuid
        }
        
        self.state_history.append(history_entry)
        
        # Сохранение в файл
        history_file = self.state_dir / f'state_history_{self.client_uuid}.json'
        try:
            with open(history_file, 'w') as f:
                json.dump(self.state_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state history: {e}")
    
    def get_current_state(self) -> State:
        """Получение текущего состояния"""
        return self.context.current_state
    
    def get_state_info(self) -> Dict:
        """Получение информации о текущем состоянии"""
        return {
            'current_state': self.context.current_state.value,
            'previous_state': self.context.previous_state.value if self.context.previous_state else None,
            'state_entered_at': self.context.state_entered_at,
            'last_error': self.context.last_error,
            'error_count': self.context.error_count,
            'health_score': self.context.health_score,
            'network_info': self.context.network_info,
            'retry_count': self.context.retry_count
        }
    
    def start(self):
        """Запуск машины состояний"""
        self.running = True
        logger.info("State Machine started")
        
        # Запуск основного цикла
        while self.running:
            try:
                # Обработка событий
                self.process_events()
                
                # Выполнение действий для текущего состояния
                self._execute_state_actions(self.context.current_state)
                
                # Пауза
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("State Machine interrupted")
                break
            except Exception as e:
                logger.error(f"State Machine error: {e}")
                self.trigger_event(Event.ERROR_OCCURRED)
        
        # Очистка
        self.stop()
    
    def stop(self):
        """Остановка машины состояний"""
        self.running = False
        logger.info("State Machine stopped")

def create_state_machine(client_uuid: str) -> VPNStateMachine:
    """Фабричная функция для создания машины состояний"""
    return VPNStateMachine(client_uuid)

if __name__ == "__main__":
    # Тестирование машины состояний
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 state_machine.py <client_uuid>")
        sys.exit(1)
    
    client_uuid = sys.argv[1]
    state_machine = create_state_machine(client_uuid)
    
    print(f"Starting State Machine for UUID: {client_uuid}")
    print("Commands: start, stop, status, quit")
    
    def print_status():
        print(f"Current state: {state_machine.get_current_state().value}")
        info = state_machine.get_state_info()
        print(f"State info: {info}")
    
    def start_callback(state, context):
        print(f"VPN is now {state.value}")
    
    def error_callback(state, context):
        print(f"VPN error: {context.last_error}")
    
    # Добавление callback
    state_machine.add_state_callback(State.RUNNING, start_callback)
    state_machine.add_state_callback(State.ERROR, error_callback)
    
    # Запуск в отдельном потоке
    import threading
    sm_thread = threading.Thread(target=state_machine.start, daemon=True)
    sm_thread.start()
    
    # Интерактивная консоль
    while True:
        try:
            cmd = input("Enter command: ").strip().lower()
            
            if cmd == "start":
                state_machine.trigger_event(Event.START_REQUESTED)
            elif cmd == "stop":
                state_machine.trigger_event(Event.STOP_REQUESTED)
            elif cmd == "status":
                print_status()
            elif cmd == "quit":
                break
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            break
    
    state_machine.stop()
    print("State Machine stopped")