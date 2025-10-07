#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from datetime import datetime

def run_test(test_name, test_func):
    """Запуск теста с обработкой ошибок"""
    print(f"\n=== {test_name} ===")
    try:
        result = test_func()
        if result:
            print(f"✓ {test_name}: УСПЕШНО")
            return True
        else:
            print(f"✗ {test_name}: НЕУДАЧНО")
            return False
    except Exception as e:
        print(f"✗ {test_name}: ОШИБКА - {e}")
        return False

def check_python():
    """Проверка Python окружения"""
    try:
        version = subprocess.check_output(["python3", "--version"], stderr=subprocess.STDOUT).decode().strip()
        print(f"Python версия: {version}")
        
        # Проверка установленных пакетов
        result = subprocess.run([sys.executable, "-c", "import sys; print('Python OK')"], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка проверки Python: {e}")
        return False

def check_client_files():
    """Проверка файлов клиентской части"""
    client_dir = "client"
    required_files = [
        "chatvpn_backend.py",
        "chatvpn_gui.py", 
        "vpn_client.py",
        "state_machine.py",
        "health.py",
        "tls_checker.py",
        "transport_manager.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(client_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    return len(missing_files) == 0

def check_server_files():
    """Проверка файлов серверной части"""
    server_dir = "server"
    required_files = [
        "api/app.py",
        "agent/agent.py",
        "bot_src/__main__.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(server_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    return len(missing_files) == 0

def test_imports():
    """Проверка импортов в клиентских модулях"""
    import_tests = [
        ("client.health", "get_mask_score"),
        ("client.tls_checker", "get_tls_score"),
        ("client.state_machine", "StateMachine"),
        ("client.transport_manager", "TransportManager")
    ]
    
    passed = 0
    for module_name, function_name in import_tests:
        try:
            module = __import__(module_name, fromlist=[function_name])
            if hasattr(module, function_name):
                print(f"✓ {module_name}.{function_name}")
                passed += 1
            else:
                print(f"✗ {module_name}.{function_name} - функция не найдена")
        except Exception as e:
            print(f"✗ {module_name} - ошибка импорта: {e}")
    
    return passed == len(import_tests)

def test_basic_functionality():
    """Тест базовой функциональности"""
    try:
        # Тест health модуля
        from client import health
        score = health.get_mask_score()
        print(f"✓ Health score: {score}")
        
        # Т TLS модуля
        from client import tls_checker
        tls_score = tls_checker.get_tls_score()
        print(f"✓ TLS score: {tls_score}")
        
        return True
    except Exception as e:
        print(f"Ошибка тестирования базовой функциональности: {e}")
        return False

def check_systemd_services():
    """Проверка systemd сервисов"""
    service_files = [
        "systemd/xvpn-client.service",
        "systemd/xvpn-api.service", 
        "systemd/xvpn-agent.service",
        "systemd/xvpn-bot.service"
    ]
    
    missing_files = []
    for service_file in service_files:
        if not os.path.exists(service_file):
            missing_files.append(service_file)
        else:
            print(f"✓ {service_file}")
    
    return len(missing_files) == 0

def check_docker_files():
    """Проверка Docker файлов"""
    docker_files = [
        "docker-compose.yml",
        "docker/Dockerfile.api",
        "docker/Dockerfile.agent",
        "docker/Dockerfile.bot"
    ]
    
    missing_files = []
    for docker_file in docker_files:
        if not os.path.exists(docker_file):
            missing_files.append(docker_file)
        else:
            print(f"✓ {docker_file}")
    
    return len(missing_files) == 0

def main():
    """Главная функция тестирования"""
    print("XVPN Комплексное тестирование")
    print("=" * 50)
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Проверка Python окружения", check_python),
        ("Проверка клиентских файлов", check_client_files),
        ("Проверка серверных файлов", check_server_files),
        ("Проверка импортов", test_imports),
        ("Тест базовой функциональности", test_basic_functionality),
        ("Проверка systemd сервисов", check_systemd_services),
        ("Проверка Docker файлов", check_docker_files),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed_tests += 1
        time.sleep(1)  # Небольшая задержка между тестами
    
    print("\n" + "=" * 50)
    print(f"Итоги тестирования:")
    print(f"Всего тестов: {total_tests}")
    print(f"Пройдено: {passed_tests}")
    print(f"Провалено: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОЙДЕНЫ НЕУСПЕШНО")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)