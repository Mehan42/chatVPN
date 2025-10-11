#!/usr/bin/env python3
"""
Скрипт диагностики клиента XVPN - проверяет все компоненты и зависимости
"""

import sys
import os
from pathlib import Path
import subprocess
import json

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    print(f"🔍 Версия Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Требуется Python 3.10 или выше")
        return False
    else:
        print("✅ Версия Python подходит")
        return True

def check_dependencies():
    """Проверка зависимостей клиента"""
    dependencies = [
        'tkinter',
        'requests',
        'PIL',
        'pystray',
        'psutil'
    ]
    
    print("\n🔍 Проверка зависимостей...")
    
    missing_deps = []
    for dep in dependencies:
        try:
            if dep == 'tkinter':
                import tkinter
            elif dep == 'requests':
                import requests
            elif dep == 'PIL':
                from PIL import Image
            elif dep == 'pystray':
                import pystray
            elif dep == 'psutil':
                import psutil
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Отсутствующие зависимости: {', '.join(missing_deps)}")
        print("Установите их командой:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    else:
        print("✅ Все зависимости установлены")
        return True

def check_client_files():
    """Проверка наличия файлов клиента"""
    client_dir = Path(__file__).parent.resolve()
    print(f"\n🔍 Проверка файлов клиента в {client_dir}")
    
    required_files = [
        'chatvpn_gui.py',
        'chatvpn_backend.py',
        'state_machine.py',
        'health.py',
        'discover.py',
        'transport_manager.py',
        'vpn_client.py',
        'proxy_helper.py',
        'proxy_modes.py',
        'ipv6_manager.py'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = client_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Отсутствующие файлы: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Все файлы клиента присутствуют")
        return True

def check_permissions():
    """Проверка прав доступа"""
    client_dir = Path(__file__).parent.resolve()
    print(f"\n🔍 Проверка прав доступа в {client_dir}")
    
    # Проверка прав на директорию
    if os.access(client_dir, os.R_OK):
        print("✅ Права на чтение директории")
    else:
        print("❌ Нет прав на чтение директории")
        return False
    
    # Проверка прав на запись в logs
    logs_dir = client_dir / 'logs'
    if logs_dir.exists():
        if os.access(logs_dir, os.W_OK):
            print("✅ Права на запись в logs/")
        else:
            print("❌ Нет прав на запись в logs/")
            return False
    else:
        try:
            logs_dir.mkdir(exist_ok=True)
            print("✅ Создана директория logs/")
        except Exception as e:
            print(f"❌ Ошибка создания logs/: {e}")
            return False
    
    return True

def check_network():
    """Проверка сетевых возможностей"""
    print("\n🔍 Проверка сетевых возможностей...")
    
    try:
        import requests
        response = requests.get('https://api.telegram.org', timeout=5)
        print(f"✅ Доступ к Telegram API (статус: {response.status_code})")
    except Exception as e:
        print(f"⚠️  Проблемы с доступом к Telegram API: {e}")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('google.com', 80))
        sock.close()
        
        if result == 0:
            print("✅ Интернет-соединение доступно")
        else:
            print("⚠️  Проблемы с интернет-соединением")
    except Exception as e:
        print(f"⚠️  Ошибка проверки интернета: {e}")

def check_environment():
    """Проверка переменных окружения"""
    print("\n🔍 Проверка переменных окружения...")
    
    env_vars = [
        'XVPN_CLIENT_BASE_DIR',
        'HOME',
        'PATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'Не установлена')
        if value != 'Не установлена':
            print(f"✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"⚠️  {var}: {value}")

def main():
    """Главная функция диагностики"""
    print("🔧 Диагностика клиента XVPN")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_dependencies,
        check_client_files,
        check_permissions,
        check_network,
        check_environment
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка при выполнении проверки {check.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Результаты диагностики:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено проверок: {passed}/{total}")
    
    if passed == total:
        print("🎉 Все проверки пройдены! Клиент готов к работе.")
        return 0
    elif passed >= total * 0.8:
        print("⚠️  Большинство проверок пройдены. Некоторые проблемы могут повлиять на работу.")
        return 1
    else:
        print("❌ Много проблем. Требуется исправление перед запуском клиента.")
        return 2

if __name__ == "__main__":
    sys.exit(main())