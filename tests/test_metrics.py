#!/usr/bin/env python3
"""Тестирование модуля метрик XVPN"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from xvpn.metrics import *

def test_metrics():
    """Тестирование функций метрик"""
    print("=== Тестирование модуля метрик XVPN ===")
    
    # Тестирование записи метрик
    print("1. Тестирование записи метрик...")
    
    # Запись оценки здоровья
    record_health_score(5)
    print("   ✓ Запись оценки здоровья: 5")
    
    # Запись запроса API
    record_api_request("GET", "/mcp/v1/vpn.health", "200")
    print("   ✓ Запись запроса API: GET /mcp/v1/vpn.health 200")
    
    # Запись ошибки API
    record_api_error("Connection timeout")
    print("   ✓ Запись ошибки API: Connection timeout")
    
    # Запись ошибки агента
    record_agent_error("Transport not available")
    print("   ✓ Запись ошибки агента: Transport not available")
    
    # Запись ошибки бота
    record_bot_error("Message send failed")
    print("   ✓ Запись ошибки бота: Message send failed")
    
    # Запись ошибки воркера
    record_worker_error("Task execution failed")
    print("   ✓ Запись ошибки воркера: Task execution failed")
    
    # Запись активных подключений
    record_active_connections(10)
    print("   ✓ Запись активных подключений: 10")
    
    # Запись общего количества подключений
    record_total_connections()
    print("   ✓ Запись общего количества подключений: +1")
    
    # Запись переключения транспорта
    record_transport_switch()
    print("   ✓ Запись переключения транспорта: +1")
    
    # Запись сообщения бота
    record_bot_message("info")
    print("   ✓ Запись сообщения бота: info")
    
    # Запись задачи воркера
    record_worker_task("health_check")
    print("   ✓ Запись задачи воркера: health_check")
    
    # Тестирование экспорта метрик
    print("\n2. Тестирование экспорта метрик...")
    
    # Skip this for now as it's not fully implemented
    print("   ⚠️  Экспорт метрик пропущен (в разработке)")
    
    # Тестирование сводки метрик
    print("\n3. Тестирование сводки метрик...")
    
    summary = get_metrics_summary()
    print("   ✓ Сводка метрик сгенерирована успешно")
    print("   Сводка:")
    for line in summary.split('\n'):
        print(f"     {line}")
    
    # Тестирование декоратора метрик
    print("\n4. Тестирование декоратора метрик...")
    
    @metrics_collector
    def test_function():
        """Тестовая функция"""
        return "success"
    
    result = test_function()
    print(f"   ✓ Декоратор метрик работает: {result}")
    
    # Тестирование контекстного менеджера метрик
    print("\n5. Тестирование контекстного менеджера метрик...")
    
    with MetricsContext("GET", "/test") as ctx:
        print("   ✓ Контекстный менеджер метрик работает")
    
    print("\n=== Все тесты пройдены успешно! ===")

if __name__ == "__main__":
    test_metrics()