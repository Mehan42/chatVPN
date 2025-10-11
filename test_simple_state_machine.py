#!/usr/bin/env python3
"""Простое тестирование машины состояний XVPN клиента"""

import time
import threading
from state_machine import create_state_machine, Event, State

def test_state_machine_simple():
    print("=== Простое тестирование машины состояний XVPN ===")
    
    # Создание машины состояний
    sm = create_state_machine('test-uuid-123')
    
    print(f"Начальное состояние: {sm.get_current_state().value}")
    
    # Добавим немного задержки для инициализации
    time.sleep(1)
    
    # Проверим состояние еще раз
    print(f"Состояние после инициализации: {sm.get_current_state().value}")
    
    # Попробуем вызвать события вручную для проверки переходов
    print("Вызываем START_REQUESTED...")
    sm.trigger_event(Event.START_REQUESTED)
    
    time.sleep(2)  # Дадим время для обработки события
    
    print(f"Состояние после START_REQUESTED: {sm.get_current_state().value}")
    
    # Если машина находится в CONFIG_FETCHING, попробуем имитировать успешную загрузку
    if sm.get_current_state() == State.CONFIG_FETCHING:
        print("Вызываем CONFIG_FETCHED...")
        sm.trigger_event(Event.CONFIG_FETCHED)
        time.sleep(2)
        print(f"Состояние после CONFIG_FETCHED: {sm.get_current_state().value}")
    
    # Если машина в CONFIG_VALIDATING, вызовем CONFIG_VALIDATED
    if sm.get_current_state() == State.CONFIG_VALIDATING:
        print("Вызываем CONFIG_VALIDATED...")
        sm.trigger_event(Event.CONFIG_VALIDATED)
        time.sleep(2)
        print(f"Состояние после CONFIG_VALIDATED: {sm.get_current_state().value}")
    
    # Если машина в IDLE, вызовем START_REQUESTED
    if sm.get_current_state() == State.IDLE:
        print("Вызываем START_REQUESTED из IDLE...")
        sm.trigger_event(Event.START_REQUESTED)
        time.sleep(2)
        print(f"Состояние после START_REQUESTED из IDLE: {sm.get_current_state().value}")
    
    print("=== Тестирование завершено ===")

if __name__ == "__main__":
    test_state_machine_simple()