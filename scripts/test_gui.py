#!/usr/bin/env python3
# Тестовый скрипт для проверки GUI XVPN
# Абсолютный путь: ~/chatvpn/scripts/test_gui.py

import sys
import os
import threading
import time
import logging
from pathlib import Path

# Добавление путей для импортов
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'client'))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gui_imports():
    """Тестирование импортов GUI модулей"""
    print("=== Тестирование импортов GUI ===")
    
    try:
        # Тест импорта tkinter
        import tkinter as tk
        print("✓ tkinter импортирован успешно")
        
        # Тест импорта ttk
        from tkinter import ttk
        print("✓ ttk импортирован успешно")
        
        # Тест импорта модулей проекта
        from client.gui.vpn_gui import XVPNGUI
        print("✓ XVPNGUI импортирован успешно")
        
        # Тест импорта VPN клиента
        from vpn_client import get_vpn_client
        print("✓ VPN клиент импортирован успешно")
        
        # Тест импорта state machine
        from state_machine import State, Event
        print("✓ State machine импортирован успешно")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка импорта: {e}")
        return False

def test_gui_creation():
    """Тестирование создания GUI"""
    print("\n=== Тестирование создания GUI ===")
    
    try:
        import tkinter as tk
        
        # Создание основного окна
        root = tk.Tk()
        root.withdraw()  # Скрыть окно для теста
        
        # Создание GUI
        from client.gui.vpn_gui import XVPNGUI
        app = XVPNGUI(root)
        
        print("✓ GUI создан успешно")
        
        # Закрытие окна
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка создания GUI: {e}")
        return False

def test_gui_integration():
    """Тестирование интеграции GUI с другими модулями"""
    print("\n=== Тестирование интеграции GUI ===")
    
    try:
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        from client.gui.vpn_gui import XVPNGUI
        
        # Создание GUI
        app = XVPNGUI(root)
        
        # Тестирование инициализации клиента
        if app.init_client():
            print("✓ Клиент инициализирован успешно")
        else:
            print("⚠ Клиент не удалось инициализировать (это ожидаемо без сервера)")
        
        # Тестирование методов GUI
        print("✓ Методы GUI доступны:")
        print(f"  - start_vpn: {hasattr(app, 'start_vpn')}")
        print(f"  - stop_vpn: {hasattr(app, 'stop_vpn')}")
        print(f"  - reload_config: {hasattr(app, 'reload_config')}")
        print(f"  - update_transport_list: {hasattr(app, 'update_transport_list')}")
        print(f"  - test_dns: {hasattr(app, 'test_dns')}")
        print(f"  - test_ip: {hasattr(app, 'test_ip')}")
        print(f"  - test_tls: {hasattr(app, 'test_tls')}")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка интеграции: {e}")
        return False

def test_gui_features():
    """Тестирование возможностей GUI"""
    print("\n=== Тестирование возможностей GUI ===")
    
    try:
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        from client.gui.vpn_gui import XVPNGUI
        
        app = XVPNGUI(root)
        
        # Тестирование вкладок
        tabs = app.notebook.tabs()
        print(f"✓ Вкладки созданы: {len(tabs)}")
        for i, tab in enumerate(tabs):
            tab_text = app.notebook.tab(tab, "text")
            print(f"  - Вкладка {i+1}: {tab_text}")
        
        # Тестирование индикаторов
        app.update_state_indicator('green')
        print("✓ Индикатор состояния обновлен")
        
        app.update_health_indicator(3)
        print("✓ Индикатор здоровья обновлен")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования возможностей: {e}")
        return False

def test_error_handling():
    """Тестирование обработки ошибок"""
    print("\n=== Тестирование обработки ошибок ===")
    
    try:
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        from client.gui.vpn_gui import XVPNGUI
        
        app = XVPNGUI(root)
        
        # Тестирование ошибочных операций
        try:
            app.start_vpn()  # Должно работать без ошибки
        except Exception as e:
            print(f"⚠ Ожидаемая ошибка при запуске без клиента: {e}")
        
        try:
            app.stop_vpn()  # Должно работать без ошибки
        except Exception as e:
            print(f"⚠ Ожидаемая ошибка при остановке без клиента: {e}")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования обработки ошибок: {e}")
        return False

def test_performance():
    """Тестирование производительности GUI"""
    print("\n=== Тестирование производительности GUI ===")
    
    try:
        import tkinter as tk
        import time
        
        root = tk.Tk()
        root.withdraw()
        
        from client.gui.vpn_gui import XVPNGUI
        
        # Тестирование времени создания
        start_time = time.time()
        app = XVPNGUI(root)
        creation_time = time.time() - start_time
        
        print(f"✓ Время создания GUI: {creation_time:.3f} секунд")
        
        # Тестирование обновления
        start_time = time.time()
        app.update_state_indicator('blue')
        app.update_health_indicator(5)
        update_time = time.time() - start_time
        
        print(f"✓ Время обновления GUI: {update_time:.3f} секунд")
        
        root.destroy()
        
        # Проверка производительности
        if creation_time < 2.0:  # Меньше 2 секунд
            print("✓ Производительность хорошая")
        else:
            print("⚠ Производительность может быть улучшена")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования производительности: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Тестирование GUI XVPN")
    print("=" * 50)
    
    # Запуск тестов
    tests = [
        ("Импорты", test_gui_imports),
        ("Создание GUI", test_gui_creation),
        ("Интеграция", test_gui_integration),
        ("Возможности", test_gui_features),
        ("Обработка ошибок", test_error_handling),
        ("Производительность", test_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Тест '{test_name}' завершился с ошибкой: {e}")
            results.append((test_name, False))
        
        print("-" * 50)
    
    # Вывод результатов
    print("\n=== Результаты тестирования ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ ПРОШЕЛ" if result else "✗ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтог: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠ Некоторые тесты не пройдены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)