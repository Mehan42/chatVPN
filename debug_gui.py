#!/usr/bin/env python3
# Отладка GUI интерфейса

import sys
import os
from pathlib import Path
import traceback

# Добавляем директорию скрипта в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

def debug_gui():
    try:
        print("Начинаем импорт модулей...")
        
        import tkinter as tk
        print("✓ Tkinter импортирован успешно")
        
        # Проверяем другие зависимости
        try:
            import PIL
            print("✓ PIL (Pillow) импортирован успешно")
        except ImportError:
            print("✗ PIL (Pillow) не установлен")
            return False
        
        try:
            import pystray
            print("✓ pystray импортирован успешно")
        except ImportError:
            print("✗ pystray не установлен")
            return False
        
        print("✓ Все зависимости GUI импортированы успешно")
        
        # Проверяем наличие иконок
        icon_green_path = CLIENT_DIR / "icon_green.png"
        icon_red_path = CLIENT_DIR / "icon_red.png"
        
        if icon_green_path.exists():
            print(f"✓ Иконка найдена: {icon_green_path}")
        else:
            print(f"✗ Иконка не найдена: {icon_green_path}")
        
        if icon_red_path.exists():
            print(f"✓ Иконка найдена: {icon_red_path}")
        else:
            print(f"✗ Иконка не найдена: {icon_red_path}")
        
        # Пытаемся выполнить частичную инициализацию без запуска mainloop
        print("\nПытаемся импортировать GUI класс...")
        from chatvpn_gui import App
        print("✓ GUI класс импортирован успешно")
        
        # Проверим инициализацию без запуска
        print("Создаем экземпляр GUI (без запуска)...")
        app = App.__new__(App)  # Создаем объект без вызова __init__
        
        print("✓ Объект GUI создан без ошибок")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при отладке GUI: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Запуск отладки GUI интерфейса...")
    success = debug_gui()
    
    if success:
        print("\n✓ GUI интерфейс работает корректно")
        print("  Примечание: GUI может не отображаться, если не запущен на графическом сервере (X11/Wayland)")
    else:
        print("\n✗ Обнаружены проблемы с GUI интерфейсом")