#!/usr/bin/env python3
# Отладка запуска GUI с выводом всех ошибок

import sys
import os
from pathlib import Path
import traceback

# Добавляем директорию скрипта в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

def debug_full_gui():
    try:
        print("Попытка запустить GUI интерфейс...")
        print(f"Текущая директория: {os.getcwd()}")
        print(f"Python путь: {sys.path[:3]}...")  # Показываем начало пути
        
        # Импортируем и запускаем GUI
        import tkinter as tk
        
        # Проверяем, доступна ли X-среда
        try:
            import tkinter
            root = tkinter.Tk()
            root.withdraw()  # Скрываем окно
            print("✓ Tkinter работает корректно")
            root.destroy()
        except Exception as e:
            print(f"⚠ Tkinter ошибка: {e}")
            return False
        
        # Теперь попробуем запустить основной GUI
        print("Запуск основного GUI...")
        
        # Импортируем chatvpn_gui но не запускаем mainloop
        from chatvpn_gui import App
        
        # Создаем экземпляр приложения
        app = App()
        print("✓ GUI приложение успешно создано")
        
        # Проверяем, есть ли все элементы интерфейса
        elements = [
            'status_lbl', 'ip_lbl', 'toggle_btn', 'cfg_btn', 'uuid_btn',
            'speed_lbl', 'tray_icon'
        ]
        
        for elem in elements:
            if hasattr(app, elem):
                print(f"✓ Элемент {elem} создан")
            else:
                print(f"⚠ Элемент {elem} не найден")
        
        # Проверяем клиента
        if app.client:
            print("✓ VPN клиент инициализирован")
            print(f"  UUID клиента: {app.client.get_client_uuid()}")
        else:
            print("⚠ VPN клиент не инициализирован")
        
        # Останавливаем приложение
        app.destroy()
        
        print("✓ GUI тестирование успешно завершено без запуска mainloop")
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Ошибка при запуске GUI: {e}")
        traceback.print_exc()
        return False

# Пробуем импортировать все зависимости GUI
def check_dependencies():
    print("Проверка зависимостей GUI...")
    
    deps = [
        ('tkinter', 'tkinter'),
        ('PIL', 'PIL'),
        ('pystray', 'pystray'),
        ('PIL.Image', 'PIL.Image'),
    ]
    
    for import_name, module_name in deps:
        try:
            __import__(import_name)
            print(f"✓ {module_name} - доступен")
        except ImportError as e:
            print(f"✗ {module_name} - недоступен: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("=== Отладка GUI интерфейса ===")
    
    success_deps = check_dependencies()
    if success_deps:
        print("\n=== Запуск GUI теста ===")
        success_gui = debug_full_gui()
        
        if success_deps and success_gui:
            print("\n🎉 Все тесты GUI прошли успешно!")
            print("✓ Зависимости установлены")
            print("✓ GUI интерфейс работает")
            print("✓ GUI может быть запущен с python3 chatvpn_gui.py")
        else:
            print("\n❌ Один или несколько тестов GUI не прошли")
    else:
        print("\n❌ Не все зависимости GUI установлены")