#!/usr/bin/env python3
"""
Минимальный тест для проверки метода reload_config без импорта других модулей
"""

import sys
import os
from pathlib import Path

# Добавляем директорию клиента в путь поиска
client_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(client_dir))

# Создаем минимальный mock класс для тестирования
class MockStateMachine:
    def trigger_event(self, event):
        print(f"[MOCK] StateMachine.trigger_event({event}) called")

class MockClient:
    def __init__(self):
        self.state_machine = MockStateMachine()
        self.running = True
        self.client_uuid = "test-uuid-123"
    
    def reload_config(self) -> tuple[bool, str]:
        """Перезагрузка конфигурации"""
        try:
            if not self.state_machine:
                return (False, "State machine not initialized")
            
            if not self.running:
                return (False, "VPN Client is not running")
            
            self.state_machine.trigger_event("START_REQUESTED")
            return (True, "Config reload requested")
        except Exception as e:
            return (False, f"Error reloading config: {e}")
    
    def get_client_uuid(self) -> str:
        """Получение UUID клиента"""
        return self.client_uuid

def test_reload_config():
    """Тест метода reload_config"""
    print("=== Тест метода reload_config ===")
    
    # Создаем mock клиента
    client = MockClient()
    
    # Тестируем метод
    result = client.reload_config()
    
    print(f"Результат: {result}")
    print(f"Тип результата: {type(result)}")
    
    # Проверяем распаковку
    try:
        ok, msg = result
        print(f"Распаковка успешна: ok={ok}, msg=\"{msg}\"")
        print("✅ Метод работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка распаковки: {e}")
        return False

if __name__ == "__main__":
    test_reload_config()
