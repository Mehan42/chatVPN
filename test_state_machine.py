#!/usr/bin/env python3
"""Тестирование машины состояний XVPN клиента"""

import time
import threading
from state_machine import create_state_machine, Event

def test_state_machine():
    print("=== Тестирование машины состояний XVPN ===")
    
    # Создание машины состояний
    sm = create_state_machine('test-uuid-123')
    
    def state_callback(state, context):
        print(f"Состояние изменено: {state.value}")
        print(f"  Health score: {context.health_score}")
        print(f"  Last error: {context.last_error}")
    
    # Добавляем callback
    sm.add_state_callback(None, state_callback)  # Callback для всех состояний
    
    # Запуск машины состояний в отдельном потоке
    sm_thread = threading.Thread(target=sm.start, daemon=True)
    sm_thread.start()
    
    # Ждем немного для инициализации
    time.sleep(2)
    
    # Проверяем начальное состояние
    print(f"Начальное состояние: {sm.get_current_state().value}")
    
    # Запрашиваем запуск
    print("Запрашиваем запуск...")
    sm.trigger_event(Event.START_REQUESTED)
    
    # Ждем немного
    time.sleep(5)
    
    # Проверяем текущее состояние
    current_state = sm.get_current_state().value
    print(f"Текущее состояние после запуска: {current_state}")
    
    # Получаем информацию о состоянии
    state_info = sm.get_state_info()
    print(f"Информация о состоянии: {state_info['current_state']}")
    
    # Останавливаем машину состояний
    print("Останавливаем машину состояний...")
    sm.stop()
    
    print("=== Тестирование завершено ===")

if __name__ == "__main__":
    test_state_machine()