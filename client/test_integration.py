#!/usr/bin/env python3
# Тест интеграции state machine с GUI
# Абсолютный путь: ~/chatvpn/client/ (может быть переустановлен в другое место)test_integration.py

import sys
import os
import time
import threading
import tkinter as tk
from tkinter import messageboxfrom pathlib import Path

# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()


# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vpn_client import get_vpn_client
from state_machine import State, Event
from chatvpn_gui import App

def test_state_machine_integration():
    """Тест интеграции машины состояний"""
    print("=== Тест интеграции машины состояний ===")
    
    # Создание VPN клиента
    client = get_vpn_client()
    
    if not client.initialize():
        print("✗ Не удалось инициализировать VPN клиент")
        return False
    
    print("✓ VPN клиент инициализирован")
    
    # Тест получения статуса
    status = client.get_status()
    print(f"✓ Текущее состояние: {status.get('current_state', 'unknown')}")
    
    # Тест получения информации о сети
    network_info = client.get_network_info()
    print(f"✓ Информация о сети: {network_info.get('external_ips', {})}")
    
    # Тест получения оценки здоровья
    health_score = client.get_health_score()
    print(f"✓ Оценка здоровья: {health_score}/5")
    
    # Тест запуска/остановки VPN
    print("Тест запуска VPN...")
    if client.start_vpn():
        print("✓ VPN запущен")
        time.sleep(2)
        
        # Проверка состояния
        status = client.get_status()
        print(f"✓ Состояние после запуска: {status.get('current_state', 'unknown')}")
        
        # Тест остановки
        print("Тест остановки VPN...")
        if client.stop_vpn():
            print("✓ VPN остановлен")
            time.sleep(2)
            
            # Проверка состояния
            status = client.get_status()
            print(f"✓ Состояние после остановки: {status.get('current_state', 'unknown')}")
        else:
            print("✗ Не удалось остановить VPN")
            return False
    else:
        print("✗ Не удалось запустить VPN")
        return False
    
    print("✓ Все тесты пройдены успешно")
    return True

def test_gui_integration():
    """Тест интеграции с GUI"""
    print("\n=== Тест интеграции с GUI ===")
    
    # Создание основного окна
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно
    
    # Создание GUI приложения
    app = App()
    
    # Даем время на инициализацию
    time.sleep(2)
    
    # Проверка инициализации клиента
    if app.client:
        print("✓ VPN клиент в GUI инициализирован")
        
        # Тест получения статуса
        status = app.client.get_status()
        print(f"✓ Статус в GUI: {status.get('current_state', 'unknown')}")
        
        # Тест обновления состояния
        app.update_gui_state("test", None)
        print("✓ GUI состояние обновлено")
    else:
        print("✗ VPN клиент в GUI не инициализирован")
        return False
    
    # Закрытие GUI
    root.destroy()
    print("✓ Тест GUI завершен")
    return True

def main():
    """Главная функция тестирования"""
    print("Запуск тестов интеграции XVPN...")
    
    # Тест машины состояний
    sm_success = test_state_machine_integration()
    
    # Тест GUI
    gui_success = test_gui_integration()
    
    # Итог
    print("\n=== Итоги тестирования ===")
    if sm_success and gui_success:
        print("✓ Все тесты пройдены успешно!")
        print("✓ State machine интегрирована с GUI")
        return True
    else:
        print("✗ Некоторые тесты не пройдены")
        if not sm_success:
            print("✗ Проблемы с интеграцией state machine")
        if not gui_success:
            print("✗ Проблемы с интеграцией GUI")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)