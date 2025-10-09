#!/usr/bin/env python3
"""
Скрипт запуска XVPN клиента с правильной настройкой путей
"""

import sys
import os
from pathlib import Path

# Добавляем директорию клиента в путь поиска модулей
client_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(client_dir))

# Устанавливаем переменную окружения для клиента
os.environ["XVPN_CLIENT_BASE_DIR"] = str(client_dir)

# Импортируем и запускаем GUI
try:
    from chatvpn_gui import App
    app = App()
    app.mainloop()
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены:")
    print("  pip install -r requirements_client.txt")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка при запуске клиента: {e}")
    sys.exit(1)