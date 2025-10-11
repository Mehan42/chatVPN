#!/usr/bin/env python3
"""
Скрипт запуска XVPN клиента с правильной настройкой путей и окружения
"""

import sys
import os
from pathlib import Path

# Добавляем директорию клиента в путь поиска модулей
client_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(client_dir))

# Устанавливаем переменную окружения для клиента
os.environ["XVPN_CLIENT_BASE_DIR"] = str(client_dir)

def main():
    """Главная функция запуска клиента"""
    try:
        print(f"🚀 Запуск XVPN клиента из {client_dir}")
        
        # Проверяем наличие необходимых файлов
        required_files = [
            'chatvpn_gui.py',
            'chatvpn_backend.py', 
            'state_machine.py',
            'health.py',
            'discover.py',
            'transport_manager.py',
            'vpn_client.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not (client_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Ошибка: Отсутствуют необходимые файлы: {missing_files}")
            return 1
        
        print("✅ Все необходимые файлы найдены")
        
        # Импортируем и запускаем GUI
        from chatvpn_gui import App
        app = App()
        app.mainloop()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены:")
        print("  pip install -r requirements_client.txt")
        return 1
    except Exception as e:
        print(f"❌ Ошибка при запуске клиента: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())