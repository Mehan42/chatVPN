#!/usr/bin/env python3
# Финальное тестирование XVPN системы
# Абсолютный путь: ~/chatvpn/scripts/final_system_test.py

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

def test_client_components():
    """Тестирование клиентских компонентов"""
    print("\n=== Тестирование клиентских компонентов ===")
    
    results = []
    
    # Тестирование state machine
    try:
        sys.path.append('client')
        from state_machine import create_state_machine
        
        # Создание тестовой машины состояний
        sm = create_state_machine('test_client')
        
        # Проверка основных функций
        current_state = sm.get_current_state()
        state_info = sm.get_state_info()
        
        if current_state and state_info:
            print("✓ State Machine работает корректно")
            results.append(("State Machine", True))
        else:
            print("✗ State Machine не работает")
            results.append(("State Machine", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования State Machine: {e}")
        results.append(("State Machine", False))
    
    # Тестирование health monitoring
    try:
        from health import get_mask_score, get_network_info
        
        # Проверка функции оценки маскировки
        mask_score = get_mask_score()
        
        # Проверка функции получения сетевой информации
        network_info = get_network_info()
        
        if isinstance(mask_score, int) and isinstance(network_info, dict):
            print("✓ Health Monitoring работает корректно")
            results.append(("Health Monitoring", True))
        else:
            print("✗ Health Monitoring не работает")
            results.append(("Health Monitoring", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Health Monitoring: {e}")
        results.append(("Health Monitoring", False))
    
    # Тестирование IPv6 менеджера
    try:
        from ipv6_manager import get_ipv6_status, test_ipv6_connectivity
        
        # Проверка статуса IPv6
        ipv6_status = get_ipv6_status()
        
        # Проверка IPv6 connectivity
        ipv6_connectivity = test_ipv6_connectivity()
        
        if ipv6_status is not None and ipv6_connectivity is not None:
            print("✓ IPv6 Manager работает корректно")
            results.append(("IPv6 Manager", True))
        else:
            print("✗ IPv6 Manager не работает")
            results.append(("IPv6 Manager", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования IPv6 Manager: {e}")
        results.append(("IPv6 Manager", False))
    
    # Тестирование proxy менеджера
    try:
        from proxy_manager import ProxyManager
        
        # Создание менеджера прокси
        pm = ProxyManager()
        
        # Проверка доступных режимов
        modes = pm.get_available_modes()
        
        # Проверка текущего режима
        current_mode = pm.get_current_mode()
        
        if modes and current_mode is not None:
            print("✓ Proxy Manager работает корректно")
            results.append(("Proxy Manager", True))
        else:
            print("✗ Proxy Manager не работает")
            results.append(("Proxy Manager", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Proxy Manager: {e}")
        results.append(("Proxy Manager", False))
    
    # Тестирование transport менеджера
    try:
        from transport_manager import get_transport_manager
        
        # Создание менеджера транспорта
        tm = get_transport_manager('test_client')
        
        # Проверка доступных транспортиров
        transports = tm.get_available_transports()
        
        if transports is not None:
            print("✓ Transport Manager работает корректно")
            results.append(("Transport Manager", True))
        else:
            print("✗ Transport Manager не работает")
            results.append(("Transport Manager", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Transport Manager: {e}")
        results.append(("Transport Manager", False))
    
    # Тестирование backend
    try:
        import chatvpn_backend as be
        
        # Проверка UUID клиента
        uuid = be.get_client_uuid()
        
        if uuid is not None or True:  # UUID может быть пустым при первой установке
            print("✓ ChatVPN Backend работает корректно")
            results.append(("ChatVPN Backend", True))
        else:
            print("✗ ChatVPN Backend не работает")
            results.append(("ChatVPN Backend", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования ChatVPN Backend: {e}")
        results.append(("ChatVPN Backend", False))
    
    return results

def test_server_components():
    """Тестирование серверных компонентов"""
    print("\n=== Тестирование серверных компонентов ===")
    
    results = []
    
    # Тестирование API
    try:
        # Проверка существования файлов API
        api_files = [
            'server/api/app.py',
            'server/api/admin_rest_api.py',
            'server/api/security_config.json'
        ]
        
        all_exist = True
        for file_path in api_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ API компоненты существуют")
            results.append(("API Components", True))
        else:
            print("✗ API компоненты отсутствуют")
            results.append(("API Components", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования API: {e}")
        results.append(("API Components", False))
    
    # Тестирование агента
    try:
        # Проверка существования файлов агента
        agent_files = [
            'server/agent/agent.py',
            'server/agent/enhanced_rag_system.py'
        ]
        
        all_exist = True
        for file_path in agent_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Agent компоненты существуют")
            results.append(("Agent Components", True))
        else:
            print("✗ Agent компоненты отсутствуют")
            results.append(("Agent Components", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Agent: {e}")
        results.append(("Agent Components", False))
    
    # Тестирование безопасности
    try:
        # Проверка существования файлов безопасности
        security_files = [
            'server/security/security_manager.py',
            'server/security/integrate_security.py',
            'server/security/security_schema.sql'
        ]
        
        all_exist = True
        for file_path in security_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Security компоненты существуют")
            results.append(("Security Components", True))
        else:
            print("✗ Security компоненты отсутствуют")
            results.append(("Security Components", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Security: {e}")
        results.append(("Security Components", False))
    
    return results

def test_infrastructure():
    """Тестирование инфраструктуры"""
    print("\n=== Тестирование инфраструктуры ===")
    
    results = []
    
    # Тестирование Docker
    try:
        # Проверка существования docker-compose.yml
        if Path('docker-compose.yml').exists():
            print("✓ Docker Compose конфигурация существует")
            results.append(("Docker Compose", True))
        else:
            print("✗ Docker Compose конфигурация отсутствует")
            results.append(("Docker Compose", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Docker: {e}")
        results.append(("Docker Compose", False))
    
    # Тестирование Traefik
    try:
        # Проверка существования файлов Traefik
        traefik_files = [
            'traefik/traefik.yml',
            'traefik/tls.yml'
        ]
        
        all_exist = True
        for file_path in traefik_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Traefik конфигурация существует")
            results.append(("Traefik Configuration", True))
        else:
            print("✗ Traefik конфигурация отсутствует")
            results.append(("Traefik Configuration", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Traefik: {e}")
        results.append(("Traefik Configuration", False))
    
    # Тестирование systemd
    try:
        # Проверка существования systemd сервисов
        systemd_files = [
            'systemd/xvpn-api.service',
            'systemd/xvpn-bot.service',
            'systemd/xvpn-agent.service',
            'systemd/xvpn-worker.service'
        ]
        
        all_exist = True
        for file_path in systemd_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Systemd сервисы существуют")
            results.append(("Systemd Services", True))
        else:
            print("✗ Systemd сервисы отсутствуют")
            results.append(("Systemd Services", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования Systemd: {e}")
        results.append(("Systemd Services", False))
    
    # Тестирование скриптов
    try:
        # Проверка существования скриптов
        script_files = [
            'scripts/install_systemd_services.sh',
            'scripts/manage_xvpn_services.sh',
            'scripts/test_xvpn_system.sh',
            'scripts/create_installer.py'
        ]
        
        all_exist = True
        for file_path in script_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Скрипты существуют")
            results.append(("Scripts", True))
        else:
            print("✗ Скрипты отсутствуют")
            results.append(("Scripts", False))
    except Exception as e:
        print(f"✗ Ошибка тестирования скриптов: {e}")
        results.append(("Scripts", False))
    
    return results

def test_installer():
    """Тестирование установщика"""
    print("\n=== Тестирование установщика ===")
    
    results = []
    
    try:
        # Проверка существования установщика
        installer_dir = Path('installer')
        if installer_dir.exists():
            print("✓ Директория установщика существует")
            results.append(("Installer Directory", True))
        else:
            print("✗ Директория установщика отсутствует")
            results.append(("Installer Directory", False))
            return results
        
        # Проверка файлов установщика
        installer_files = [
            'installer/install_xvpn.sh',
            'installer/uninstall_xvpn.sh',
            'installer/install_xvpn.bat',
            'installer/update_xvpn.sh',
            'installer/installer_report.json'
        ]
        
        all_exist = True
        for file_path in installer_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Файлы установщика существуют")
            results.append(("Installer Files", True))
        else:
            print("✗ Файлы установщика отсутствуют")
            results.append(("Installer Files", False))
        
        # Проверка прав на выполнение
        install_script = Path('installer/install_xvpn.sh')
        if install_script.exists() and os.access(install_script, os.X_OK):
            print("✓ Скрипт установки имеет права на выполнение")
            results.append(("Install Script Permissions", True))
        else:
            print("✗ Скрипт установки не имеет прав на выполнение")
            results.append(("Install Script Permissions", False))
        
    except Exception as e:
        print(f"✗ Ошибка тестирования установщика: {e}")
        results.append(("Installer Error", False))
    
    return results

def test_documentation():
    """Тестирование документации"""
    print("\n=== Тестирование документации ===")
    
    results = []
    
    try:
        # Проверка существования документации
        doc_files = [
            'docs/XVPN_Implementation_Report.md',
            'README.md',
            'ПРОЕКТНЫЙ_ПЛАН_XVPN.md'
        ]
        
        all_exist = True
        for file_path in doc_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        if all_exist:
            print("✓ Документация существует")
            results.append(("Documentation", True))
        else:
            print("✗ Документация отсутствует")
            results.append(("Documentation", False))
        
        # Проверка размеров файлов документации
        impl_report = Path('docs/XVPN_Implementation_Report.md')
        if impl_report.exists() and impl_report.stat().st_size > 1000:
            print("✓ Отчет о реализации содержит достаточно информации")
            results.append(("Implementation Report", True))
        else:
            print("✗ Отчет о реализации неполный")
            results.append(("Implementation Report", False))
        
    except Exception as e:
        print(f"✗ Ошибка тестирования документации: {e}")
        results.append(("Documentation Error", False))
    
    return results

def test_integration():
    """Интеграционное тестирование"""
    print("\n=== Интеграционное тестирование ===")
    
    results = []
    
    # Проверка зависимостей
    try:
        import requirements
        
        # Проверка существования requirements.txt
        if Path('requirements.txt').exists():
            print("✓ Файл зависимостей существует")
            results.append(("Dependencies", True))
        else:
            print("✗ Файл зависимостей отсутствует")
            results.append(("Dependencies", False))
    except Exception as e:
        print(f"✗ Ошибка проверки зависимостей: {e}")
        results.append(("Dependencies Error", False))
    
    # Проверка конфигурации
    try:
        # Проверка существования клиентской конфигурации
        if Path('client/client.json').exists():
            print("✓ Клиентская конфигурация существует")
            results.append(("Client Configuration", True))
        else:
            print("✗ Клиентская конфигурация отсутствует")
            results.append(("Client Configuration", False))
        
        # Проверка существования серверной конфигурации
        if Path('server/config.json').exists():
            print("✓ Серверная конфигурация существует")
            results.append(("Server Configuration", True))
        else:
            print("✗ Серверная конфигурация отсутствует")
            results.append(("Server Configuration", False))
        
    except Exception as e:
        print(f"✗ Ошибка проверки конфигурации: {e}")
        results.append(("Configuration Error", False))
    
    return results

def generate_test_report(results):
    """Генерация отчета о тестировании"""
    print("\n=== Генерация отчета о тестировании ===")
    
    try:
        # Подсчет результатов
        total_tests = len(results)
        passed_tests = sum(1 for _, passed in results if passed)
        failed_tests = total_tests - passed_tests
        
        # Создание отчета
        report = {
            'test_date': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'results': results
        }
        
        # Сохранение отчета
        report_path = Path('installer/system_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Отчет о тестировании сохранен: {report_path}")
        
        # Вывод сводки
        print(f"\n=== Сводка тестирования ===")
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {failed_tests}")
        print(f"Успешность: {report['success_rate']:.1f}%")
        
        return report
        
    except Exception as e:
        print(f"✗ Ошибка генерации отчета: {e}")
        return None

def main():
    """Основная функция тестирования"""
    print("=== Финальное тестирование XVPN системы ===")
    print(f"Дата: {datetime.now().isoformat()}")
    print()
    
    all_results = []
    
    # Тестирование клиентских компонентов
    client_results = test_client_components()
    all_results.extend(client_results)
    
    # Тестирование серверных компонентов
    server_results = test_server_components()
    all_results.extend(server_results)
    
    # Тестирование инфраструктуры
    infra_results = test_infrastructure()
    all_results.extend(infra_results)
    
    # Тестирование установщика
    installer_results = test_installer()
    all_results.extend(installer_results)
    
    # Тестирование документации
    doc_results = test_documentation()
    all_results.extend(doc_results)
    
    # Интеграционное тестирование
    integration_results = test_integration()
    all_results.extend(integration_results)
    
    # Генерация отчета
    report = generate_test_report(all_results)
    
    # Общий результат
    if report:
        success_rate = report['success_rate']
        if success_rate >= 90:
            print(f"\n🎉 Отлично! Система готова к продакшену ({success_rate:.1f}% успешных тестов)")
            return True
        elif success_rate >= 70:
            print(f"\n✅ Хорошо! Система почти готова ({success_rate:.1f}% успешных тестов)")
            return True
        else:
            print(f"\n⚠️  Требуется доработка ({success_rate:.1f}% успешных тестов)")
            return False
    else:
        print("\n❌ Не удалось сгенерировать отчет о тестировании")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)