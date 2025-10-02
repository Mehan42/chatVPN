#!/usr/bin/env python3
# Скрипт запуска GUI XVPN
# Абсолютный путь: ~/chatvpn/scripts/run_gui.py

import sys
import os
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Настройка окружения"""
    # Добавление путей для импортов
    project_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'client'))
    
    # Создание директорий, если их нет
    dirs_to_create = [
        Path.home() / 'chatvpn' / 'client' / 'logs',
        Path.home() / 'chatvpn' / 'client' / 'config'
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Директория создана: {dir_path}")

def check_dependencies():
    """Проверка зависимостей"""
    required_modules = [
        'tkinter',
        'requests',
        'threading',
        'json',
        'time',
        'logging',
        'hashlib',
        'ssl'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Отсутствуют модули: {', '.join(missing_modules)}")
        return False
    
    return True

def check_gui_requirements():
    """Проверка требований GUI"""
    try:
        import tkinter as tk
        
        # Проверка темы
        try:
            style = ttk.Style()
            themes = style.theme_names()
            logger.info(f"Доступные темы: {themes}")
        except:
            logger.warning("Не удалось получить список тем")
        
        # Проверка поддержки шрифтов
        try:
            test_font = tk.font.Font(family="Arial", size=10)
            logger.info("Шрифты доступны")
        except:
            logger.warning("Проблемы с шрифтами")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки GUI: {e}")
        return False

def main():
    """Основная функция"""
    print("Запуск XVPN GUI")
    print("=" * 50)
    
    # Настройка окружения
    logger.info("Настройка окружения...")
    setup_environment()
    
    # Проверка зависимостей
    logger.info("Проверка зависимостей...")
    if not check_dependencies():
        logger.error("Проверка зависимостей не пройдена")
        return False
    
    # Проверка GUI требований
    logger.info("Проверка GUI требований...")
    if not check_gui_requirements():
        logger.warning("Проверка GUI требований не пройдена, но продолжаем")
    
    # Попытка импорта GUI
    try:
        from client.gui.vpn_gui import XVPNGUI
        logger.info("GUI импортирован успешно")
    except Exception as e:
        logger.error(f"Ошибка импорта GUI: {e}")
        return False
    
    # Запуск GUI
    try:
        import tkinter as tk
        
        logger.info("Создание главного окна...")
        root = tk.Tk()
        
        # Настройка окна
        root.title("XVPN Client")
        root.geometry("800x600")
        
        # Создание GUI
        logger.info("Создание экземпляра GUI...")
        app = XVPNGUI(root)
        
        # Обработка закрытия окна
        def on_closing():
            logger.info("Закрытие GUI...")
            try:
                if app.client:
                    logger.info("Остановка VPN...")
                    app.stop_vpn()
                logger.info("Завершение работы...")
            except Exception as e:
                logger.error(f"Ошибка при закрытии: {e}")
            finally:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        logger.info("Запуск главного цикла...")
        root.mainloop()
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка запуска GUI: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ GUI успешно завершен")
            sys.exit(0)
        else:
            print("\n❌ Ошибка запуска GUI")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Запуск отменен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        sys.exit(1)