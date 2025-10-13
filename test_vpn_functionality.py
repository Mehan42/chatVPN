#!/usr/bin/env python3
"""
Скрипт для тестирования функциональности VPN
"""

import subprocess
import time
import threading
import sys
from pathlib import Path

# Добавляем директорию скрипта в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

def test_vpn_functionality():
    """Тестирование функциональности VPN"""
    print("=== Тестирование функциональности VPN ===")
    
    try:
        # Импортируем компоненты VPN
        from vpn_client import VPNClient
        from chatvpn_backend import start_xray, stop_xray, get_status
        import logging
        
        # Включаем логирование
        logging.basicConfig(level=logging.INFO)
        
        print("Создание экземпляра VPN клиента...")
        client = VPNClient()
        
        print("Инициализация клиента...")
        if client.initialize():
            print("✓ Клиент успешно инициализирован")
        else:
            print("✗ Ошибка инициализации клиента")
            return False
            
        # Проверяем начальный статус
        initial_status = client.get_status()
        print(f"Начальный статус: {initial_status}")
        
        # Запускаем клиент
        print("Запуск VPN клиента...")
        if client.start():
            print("✓ VPN клиент запущен")
        else:
            print("✗ Ошибка запуска VPN клиента")
            return False
        
        # Проверяем статус после запуска
        status_after_start = client.get_status()
        print(f"Статус после запуска: {status_after_start}")
        
        # Проверяем, запущен ли клиент
        print(f"Клиент запущен: {client.is_running()}")
        
        # Проверяем информацию о транспортах
        transport_info = client.get_transport_info()
        print(f"Информация о транспортах: {transport_info}")
        
        # Пробуем запустить VPN
        print("\nПопытка запуска VPN...")
        if client.start_vpn():
            print("✓ Запрос запуска VPN отправлен")
            
            # Ждем некоторое время для соединения
            print("Ожидание соединения (10 секунд)...")
            for i in range(10):
                time.sleep(1)
                status = client.get_status()
                print(f"Статус после {i+1} сек: {status.get('current_state', 'unknown')}")
                
                # Проверяем, не произошла ли ошибка
                if status.get('last_error'):
                    print(f"Произошла ошибка: {status.get('last_error')}")
                    break
        else:
            print("✗ Ошибка запуска VPN")
        
        # Проверяем финальный статус
        final_status = client.get_status()
        print(f"\nФинальный статус: {final_status}")
        
        # Проверяем, запущен ли клиент
        print(f"Клиент запущен: {client.is_running()}")
        
        # Попробуем остановить VPN
        print("\nОстановка VPN...")
        if client.stop_vpn():
            print("✓ Запрос остановки VPN отправлен")
        else:
            print("✗ Ошибка остановки VPN")
            
        # Ожидание остановки
        time.sleep(3)
        
        # Финальная проверка
        final_status = client.get_status()
        print(f"Финальный статус после остановки: {final_status}")
        
        print("\n✓ Тестирование функциональности VPN завершено")
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"✗ Ошибка при тестировании функциональности VPN: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("Запуск тестирования функциональности VPN...")
    success = test_vpn_functionality()
    
    if success:
        print("\n✓ Все тесты функциональности VPN пройдены успешно")
    else:
        print("\n✗ Тестирование функциональности VPN завершилось с ошибками")

if __name__ == "__main__":
    main()