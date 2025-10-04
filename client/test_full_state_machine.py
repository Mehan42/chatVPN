#!/usr/bin/env python3
"""Тестирование машины состояний XVPN клиента с полным запуском"""

import time
import threading
from state_machine import create_state_machine, Event, State

def test_state_machine_full():
    print("=== Тестирование машины состояний XVPN (полный запуск) ===")
    
    # Создание машины состояний
    sm = create_state_machine('test-uuid-123')
    
    # Запуск машины состояний в отдельном потоке
    sm_thread = threading.Thread(target=sm.start, daemon=True)
    sm_thread.start()
    
    print(f"Начальное состояние: {sm.get_current_state().value}")
    
    # Подождем немного для инициализации
    time.sleep(3)
    
    print(f"Состояние после инициализации: {sm.get_current_state().value}")
    print(f"Информация о состоянии: {sm.get_state_info()}")
    
    # Попробуем вызвать события
    print("\nВызываем START_REQUESTED...")
    sm.trigger_event(Event.START_REQUESTED)
    
    time.sleep(3)  # Дадим время для обработки события
    
    print(f"Состояние после START_REQUESTED: {sm.get_current_state().value}")
    print(f"Информация о состоянии: {sm.get_state_info()}")
    
    # Попробуем вручную вызвать CONFIG_FETCHED если машина в CONFIG_FETCHING
    if sm.get_current_state() == State.CONFIG_FETCHING:
        print("\nВызываем CONFIG_FETCHED...")
        sm.trigger_event(Event.CONFIG_FETCHED)
        time.sleep(2)
        print(f"Состояние после CONFIG_FETCHED: {sm.get_current_state().value}")
    
    # Если машина в CONFIG_VALIDATING, вызовем CONFIG_VALIDATED
    if sm.get_current_state() == State.CONFIG_VALIDATING:
        print("\nВызываем CONFIG_VALIDATED...")
        sm.trigger_event(Event.CONFIG_VALIDATED)
        time.sleep(2)
        print(f"Состояние после CONFIG_VALIDATED: {sm.get_current_state().value}")
    
    # Если машина в IDLE, вызовем START_REQUESTED
    if sm.get_current_state() == State.IDLE:
        print("\nВызываем START_REQUESTED из IDLE...")
        sm.trigger_event(Event.START_REQUESTED)
        time.sleep(3)
        print(f"Состояние после START_REQUESTED из IDLE: {sm.get_current_state().value}")
    
    # Останавливаем машину состояний
    print("\nОстанавливаем машину состояний...")
    sm.stop()
    
    print("=== Тестирование завершено ===")

if __name__ == "__main__":
    test_state_machine_full()