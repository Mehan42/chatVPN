#!/usr/bin/env python3
# Скрипт для отладки XVPN клиента с логированием

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Добавляем директорию скрипта в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

def setup_logging():
    """Настройка логирования в файл с текущей датой и временем"""
    log_filename = f"client_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = CLIENT_DIR / log_filename
    
    # Настройка основного логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filepath

def main():
    print("Запуск XVPN клиента в режиме отладки...")
    log_filepath = setup_logging()
    print(f"Логи будут сохраняться в файл: {log_filepath}")
    
    try:
        # Импорты после добавления пути
        from chatvpn_gui import App
        
        print("Инициализация GUI приложения...")
        app = App()
        
        print("Запуск главного цикла приложения...")
        print("GUI запущен. Используйте интерфейс для управления клиентом.")
        print("Для завершения работы закройте окно или нажмите Ctrl+C в этом терминале.")
        app.mainloop()
        
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Ошибка при работе приложения: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Работа приложения завершена.")
        print(f"Все логи сохранены в файл: {log_filepath}")

if __name__ == "__main__":
    main()