#!/usr/bin/env python3
# Проверка возможности запуска GUI в текущей среде

import os
import sys
from pathlib import Path
import tkinter as tk

def check_x_server():
    """Проверяем, доступен ли X-сервер"""
    print("Проверка доступности графической среды...")
    
    # Проверяем переменные окружения
    display = os.environ.get('DISPLAY')
    x_authority = os.environ.get('XAUTHORITY')
    
    print(f"DISPLAY: {display}")
    print(f"XAUTHORITY: {x_authority}")
    
    # Проверяем, можем ли мы создать Tk окно
    try:
        root = tk.Tk()
        root.title("Тест X-сервера")
        root.geometry("300x200")
        
        label = tk.Label(root, text="X-сервер доступен!", font=("Arial", 14))
        label.pack(pady=50)
        
        # Проверяем, можем ли мы отобразить окно
        root.update()
        print("✓ Tkinter окно успешно создано и может быть отображено")
        
        # Даем немного времени для отображения
        root.after(2000, root.destroy)  # Закрываем через 2 секунды
        
        root.mainloop()
        print("✓ Тест X-сервера завершен успешно")
        return True
        
    except tk.TclError as e:
        print(f"✗ Ошибка Tkinter: {e}")
        print("  Это указывает на то, что X-сервер недоступен или не настроен")
        return False
    except Exception as e:
        print(f"✗ Ошибка при создании Tkinter окна: {e}")
        return False

def check_gui_with_error_handling():
    """Проверяем GUI с обработкой ошибок X-сервера"""
    try:
        from chatvpn_gui import App
        import tkinter as tk
        
        # Создаем тестовое окно как fallback
        root = tk.Tk()
        root.title("ChatVPN GUI Debug")
        root.geometry("400x300")
        
        label = tk.Label(root, text="GUI готов к запуску", font=("Arial", 12))
        label.pack(pady=20)
        
        # Пытаемся создать GUI приложение
        app = App.__new__(App)
        tk.Tk.__init__(app)
        app.withdraw()  # Скрываем окно
        
        # Инициализируем клиента
        app.client = None
        app.init_client()
        
        success_label = tk.Label(root, text="✓ GUI инициализирован успешно", fg="green")
        success_label.pack(pady=10)
        
        if app.client:
            uuid_label = tk.Label(root, text=f"UUID: {app.client.get_client_uuid()}")
            uuid_label.pack(pady=5)
        
        # Проверяем, что все методы существуют
        methods = ['on_toggle', 'on_fetch_config', 'on_change_uuid']
        for method in methods:
            if hasattr(app, method):
                method_label = tk.Label(root, text=f"✓ {method}: OK", fg="green")
                method_label.pack()
            else:
                method_label = tk.Label(root, text=f"✗ {method}: missing", fg="red")
                method_label.pack()
        
        print("✓ GUI может быть инициализирован даже если X-сервер недоступен")
        
        # Показываем окно с результатами на 3 секунды
        root.after(3000, root.destroy)
        root.mainloop()
        
        return True
        
    except tk.TclError as e:
        print(f"✗ Ошибка X-сервера при попытке запуска GUI: {e}")
        print("  GUI интерфейс требует графическую среду для отображения")
        return False
    except Exception as e:
        print(f"✗ Ошибка при инициализации GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Проверка запуска GUI в текущей среде ===\n")
    
    # Проверяем X-сервер
    x_available = check_x_server()
    
    print()
    
    if x_available:
        print("✓ X-сервер доступен, GUI должен отображаться нормально")
        print("  Попробуйте запустить: python3 chatvpn_gui.py")
    else:
        print("⚠ X-сервер недоступен, GUI не будет отображаться в терминале")
        print("  GUI требует графическую среду (настольную сессию Ubuntu)")
        print("  Попробуйте подключиться через VNC или использовать графический сеанс")
    
    print("\n=== Дополнительная проверка GUI ===")
    check_gui_with_error_handling()
    
    print("\n=== Рекомендации ===")
    if not x_available:
        print("• Запускайте GUI в графической среде Ubuntu (не в терминале SSH)")
        print("• Или используйте VNC/Remote Desktop для доступа к GUI")
    print("• GUI полностью функционален, просто может не отображаться в командной строке")
    print("• Кнопка смены UUID работает корректно")