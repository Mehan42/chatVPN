#!/usr/bin/env python3
# Тестовый скрипт проверки systemd сервисов XVPN
# Абсолютный путь: ~/chatvpn/scripts/test_systemd_services.py

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

def test_service_file_syntax(service_file):
    """Проверка синтаксиса файла сервиса"""
    print(f"=== Проверка синтаксиса {service_file} ===")
    
    try:
        # Проверка синтаксиса systemd
        result = subprocess.run(
            ["systemd-analyze", "verify", service_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {service_file} синтаксически корректен")
            return True
        else:
            print(f"✗ {service_file} имеет синтаксические ошибки:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print(f"⚠ systemd-analyze не найден, пропускаем проверку")
        return True
    except Exception as e:
        print(f"✗ Ошибка проверки синтаксиса: {e}")
        return False

def test_service_file_content(service_file):
    """Проверка содержимого файла сервиса"""
    print(f"=== Проверка содержимого {service_file} ===")
    
    try:
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Проверка обязательных секций
        required_sections = ['[Unit]', '[Service]', '[Install]']
        missing_sections = []
        
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"✗ Отсутствуют обязательные секции: {', '.join(missing_sections)}")
            return False
        
        # Проверка обязательных полей
        required_fields = [
            'Description',
            'ExecStart',
            'Restart',
            'User',
            'Group'
        ]
        
        missing_fields = []
        for field in required_fields:
            if f'{field}=' not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"✗ Отсутствуют обязательные поля: {', '.join(missing_fields)}")
            return False
        
        print(f"✓ {service_file} содержит все необходимые секции и поля")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка чтения файла: {e}")
        return False

def test_dependency_order():
    """Проверка порядка зависимостей"""
    print("=== Проверка порядка зависимостей ===")
    
    # Проверка зависимостей GUI сервиса
    gui_service = "systemd/xvpn-gui.service"
    
    try:
        with open(gui_service, 'r') as f:
            content = f.read()
        
        # Проверка наличия зависимостей
        dependencies = [
            'After=network.target',
            'Requires=xvpn-client.service'
        ]
        
        missing_deps = []
        for dep in dependencies:
            if dep not in content:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"✗ Отсутствуют зависимости: {', '.join(missing_deps)}")
            return False
        
        print("✗ Порядок зависимостей корректен")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка проверки зависимостей: {e}")
        return False

def test_service_permissions():
    """Проверка прав доступа к файлам сервисов"""
    print("=== Проверка прав доступа ===")
    
    systemd_dir = Path("systemd")
    if not systemd_dir.exists():
        print("✗ Директория systemd не найдена")
        return False
    
    services = [
        "xvpn-docker.service",
        "xvpn-redis.service",
        "xvpn-traefik.service",
        "xvpn-api.service",
        "xvpn-agent.service",
        "xvpn-bot.service",
        "xvpn-worker.service",
        "xvpn-client.service",
        "xvpn-gui.service"
    ]
    
    all_good = True
    for service in services:
        service_file = systemd_dir / service
        if not service_file.exists():
            print(f"✗ Файл сервиса не найден: {service}")
            all_good = False
            continue
        
        # Проверка прав
        if os.path.isfile(service_file):
            print(f"✓ {service} существует и является файлом")
        else:
            print(f"✗ {service} не является файлом")
            all_good = False
        
        # Проверка чтения
        try:
            with open(service_file, 'r') as f:
                f.read()
            print(f"✓ {service} доступен для чтения")
        except:
            print(f"✗ {service} недоступен для чтения")
            all_good = False
    
    return all_good

def test_install_script():
    """Проверка скрипта установки"""
    print("=== Проверка скрипта установки ===")
    
    install_script = "scripts/install_systemd_services.sh"
    
    if not Path(install_script).exists():
        print("✗ Скрипт установки не найден")
        return False
    
    # Проверка прав
    if not os.access(install_script, os.X_OK):
        print("✗ Скрипт установки не исполняемый")
        return False
    
    print("✓ Скрипт установки существует и исполняемый")
    
    # Проверка наличия GUI в установке
    try:
        with open(install_script, 'r') as f:
            content = f.read()
        
        if 'xvpn-gui.service' not in content:
            print("✗ GUI сервис не добавлен в скрипт установки")
            return False
        
        print("✓ GUI сервис добавлен в скрипт установки")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка проверки скрипта установки: {e}")
        return False

def test_management_script():
    """Проверка скрипта управления"""
    print("=== Проверка скрипта управления ===")
    
    mgmt_script = "scripts/manage_xvpn_services.sh"
    
    if not Path(mgmt_script).exists():
        print("✗ Скрипт управления не найден")
        return False
    
    # Проверка прав
    if not os.access(mgmt_script, os.X_OK):
        print("✗ Скрипт управления не исполняемый")
        return False
    
    print("✓ Скрипт управления существует и исполняемый")
    
    # Проверка наличия GUI в управлении
    try:
        with open(mgmt_script, 'r') as f:
            content = f.read()
        
        if 'xvpn-gui' not in content:
            print("✗ GUI сервис не добавлен в скрипт управления")
            return False
        
        print("✓ GUI сервис добавлен в скрипт управления")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка проверки скрипта управления: {e}")
        return False

def test_gui_service_specific():
    """Специфичные проверки для GUI сервиса"""
    print("=== Специфичные проверки GUI сервиса ===")
    
    gui_service = "systemd/xvpn-gui.service"
    
    try:
        with open(gui_service, 'r') as f:
            content = f.read()
        
        # Проверка GUI специфичных настроек
        gui_settings = [
            'DISPLAY=:0',
            'XDG_RUNTIME_DIR=/run/user/1000',
            'WorkingDirectory=/opt/xvpn/client',
            'ExecStart=/usr/bin/python3 /opt/xvpn/scripts/run_gui.py'
        ]
        
        missing_settings = []
        for setting in gui_settings:
            if setting not in content:
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"✗ Отсутствуют GUI настройки: {', '.join(missing_settings)}")
            return False
        
        # Проверка безопасности
        security_settings = [
            'NoNewPrivileges=true',
            'PrivateTmp=true',
            'ProtectSystem=strict'
        ]
        
        missing_security = []
        for setting in security_settings:
            if setting not in content:
                missing_security.append(setting)
        
        if missing_security:
            print(f"⚠ Отсутствуют настройки безопасности: {', '.join(missing_security)}")
        
        print("✓ GUI сервис имеет все необходимые настройки")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка проверки GUI сервиса: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Тестирование systemd сервисов XVPN")
    print("=" * 50)
    
    # Запуск тестов
    tests = [
        ("Права доступа", test_service_permissions),
        ("Синтаксис сервисов", lambda: test_service_file_syntax("systemd/xvpn-gui.service")),
        ("Содержимое сервисов", lambda: test_service_file_content("systemd/xvpn-gui.service")),
        ("Порядок зависимостей", test_dependency_order),
        ("GUI специфичные настройки", test_gui_service_specific),
        ("Скрипт установки", test_install_script),
        ("Скрипт управления", test_management_script),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Тест '{test_name}' завершился с ошибкой: {e}")
            results.append((test_name, False))
        
        print("-" * 50)
    
    # Вывод результатов
    print("\n=== Результаты тестирования ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ ПРОШЕЛ" if result else "✗ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтог: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты systemd сервисов пройдены успешно!")
        return True
    else:
        print("⚠ Некоторые тесты не пройдены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)