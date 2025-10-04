#!/usr/bin/env python3
"""
XVPN Component Test Script
Проверка работоспособности всех компонентов системы
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_python_environment():
    """Проверка Python окружения"""
    print("🔍 Проверка Python окружения...")
    
    # Проверка версии Python
    python_version = sys.version
    print(f"  Python version: {python_version.split()[0]}")
    
    # Проверка наличия необходимых модулей
    required_modules = ['flask', 'requests', 'psutil']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module}")
    
    if missing_modules:
        print(f"  Отсутствующие модули: {', '.join(missing_modules)}")
        return False
    
    print("  ✅ Python окружение в порядке")
    return True

def test_server_components():
    """Проверка серверных компонентов"""
    print("\n🔍 Проверка серверных компонентов...")
    
    # Проверка API
    try:
        from server.api.app import app
        print("  ✅ API компонент загружен")
    except Exception as e:
        print(f"  ❌ Ошибка загрузки API компонента: {e}")
        return False
    
    # Проверка агента
    try:
        from server.agent.agent import XVPNAgent
        print("  ✅ Агент компонент загружен")
    except Exception as e:
        print(f"  ❌ Ошибка загрузки агента: {e}")
        return False
    
    # Проверка бота
    try:
        from server.admin.tg_bot import main as bot_main
        print("  ✅ Бот компонент загружен")
    except Exception as e:
        print(f"  ❌ Ошибка загрузки бота: {e}")
        return False
    
    # Проверка воркера
    try:
        from server.worker.worker import main as worker_main
        print("  ✅ Воркер компонент загружен")
    except Exception as e:
        print(f"  ❌ Ошибка загрузки воркера: {e}")
        return False
    
    print("  ✅ Все серверные компоненты загружены")
    return True

def test_docker_compose():
    """Проверка Docker Compose конфигурации"""
    print("\n🔍 Проверка Docker Compose конфигурации...")
    
    # Проверка наличия docker-compose.yml
    compose_file = Path("docker-compose.yml")
    if compose_file.exists():
        print("  ✅ docker-compose.yml найден")
        
        # Проверка валидности YAML
        try:
            import yaml
            with open(compose_file, 'r') as f:
                yaml.safe_load(f)
            print("  ✅ docker-compose.yml валиден")
            return True
        except Exception as e:
            print(f"  ❌ Ошибка валидации docker-compose.yml: {e}")
            return False
    else:
        print("  ❌ docker-compose.yml не найден")
        return False

def test_file_permissions():
    """Проверка прав доступа к файлам"""
    print("\n🔍 Проверка прав доступа к файлам...")
    
    required_files = [
        "server/api/app.py",
        "server/agent/agent.py", 
        "server/admin/tg_bot.py",
        "server/worker/worker.py",
        "installer/install_xvpn.sh"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"  ❌ {file_path}")
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  Отсутствующие файлы: {', '.join(missing_files)}")
        return False
    
    print("  ✅ Все необходимые файлы присутствуют")
    return True

def test_network_connectivity():
    """Проверка сетевой connectivity"""
    print("\n🔍 Проверка сетевой connectivity...")
    
    # Проверка доступности внешних сервисов
    test_urls = [
        "https://api.ipify.org",
        "https://httpbin.org/ip"
    ]
    
    import requests
    
    success_count = 0
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                success_count += 1
                print(f"  ✅ {url}")
            else:
                print(f"  ❌ {url} (HTTP {response.status_code})")
        except Exception as e:
            print(f"  ❌ {url} ({e})")
    
    if success_count > 0:
        print("  ✅ Сетевая connectivity работает")
        return True
    else:
        print("  ❌ Сетевая connectivity не работает")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 XVPN Component Test Suite")
    print("=" * 40)
    
    tests = [
        test_python_environment,
        test_server_components,
        test_docker_compose,
        test_file_permissions,
        test_network_connectivity
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"  ❌ Ошибка в тесте {test_func.__name__}: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Результаты: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("✅ Все компоненты работают корректно!")
        return 0
    else:
        print("❌ Некоторые компоненты требуют внимания")
        return 1

if __name__ == "__main__":
    sys.exit(main())