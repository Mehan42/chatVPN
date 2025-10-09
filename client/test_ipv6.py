#!/usr/bin/env python3
# Тест IPv6 поддержки для XVPN
# Абсолютный путь: ~/chatvpn/client/ (может быть переустановлен в другое место)test_ipv6.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))from pathlib import Path

# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()


from ipv6_manager import get_ipv6_manager
from health import get_network_info
import json

def test_ipv6_support():
    """Тестирование IPv6 поддержки"""
    print("=== Тест IPv6 поддержки XVPN ===")
    
    # Получение IPv6 менеджера
    manager = get_ipv6_manager()
    
    # Проверка поддержки IPv6
    ipv6_supported = manager.is_ipv6_supported()
    print(f"✓ Поддержка IPv6: {'Да' if ipv6_supported else 'Нет'}")
    
    # Получение статуса IPv6
    status = manager.get_ipv6_connectivity_status()
    print(f"✓ IPv6 включен: {'Да' if status['ipv6_enabled'] else 'Нет'}")
    print(f"✓ Dual-stack включен: {'Да' if status['dual_stack_enabled'] else 'Нет'}")
    
    # Внешний IPv6
    if status['external_ipv6']:
        print(f"✓ Внешний IPv6: {status['external_ipv6']}")
    else:
        print("✓ Внешний IPv6: Не определен")
    
    # Локальные IPv6 адреса
    if status['local_ipv6_addresses']:
        print(f"✓ Локальные IPv6 адреса:")
        for ip in status['local_ipv6_addresses']:
            print(f"  - {ip}")
    else:
        print("✓ Локальные IPv6 адреса: Не найдены")
    
    # Статус подключения
    print(f"✓ IPv6 подключение: {'Да' if status['ipv6_connectivity'] else 'Нет'}")
    print(f"✓ Dual-stack подключение: {'Да' if status['dual_stack_connectivity'] else 'Нет'}")
    
    return ipv6_supported

def test_ipv6_connectivity():
    """Тестирование IPv6 подключения"""
    print("\n=== Тест IPv6 подключения ===")
    
    manager = get_ipv6_manager()
    
    # Тест подключения
    connectivity = manager.test_ipv6_connectivity()
    
    print(f"✓ IPv6 DNS разрешение: {'Да' if connectivity['ipv6_dns_resolution'] else 'Нет'}")
    print(f"✓ IPv6 TCP подключение: {'Да' if connectivity['ipv6_tcp_connectivity'] else 'Нет'}")
    print(f"✓ IPv6 HTTP подключение: {'Да' if connectivity['ipv6_http_connectivity'] else 'Нет'}")
    print(f"✓ Dual-stack поддержка: {'Да' if connectivity['dual_stack_support'] else 'Нет'}")
    
    connectivity_score = sum([
        connectivity['ipv6_dns_resolution'],
        connectivity['ipv6_tcp_connectivity'],
        connectivity['ipv6_http_connectivity'],
        connectivity['dual_stack_support']
    ])
    
    print(f"✓ Общий результат: {connectivity_score}/4")
    
    return connectivity_score >= 2

def test_network_info_ipv6():
    """Тестирование IPv6 в информации о сети"""
    print("\n=== Тест IPv6 в информации о сети ===")
    
    try:
        network_info = get_network_info()
        
        print(f"✓ Двойная стековая поддержка: {'Да' if network_info.get('dual_stack') else 'Нет'}")
        print(f"✓ VPN активен (IPv4): {'Да' if network_info.get('vpn_ipv4_active') else 'Нет'}")
        print(f"✓ VPN активен (IPv6): {'Да' if network_info.get('vpn_ipv6_active') else 'Нет'}")
        
        external_ips = network_info.get('external_ips', {})
        print(f"✓ Внешний IPv4: {external_ips.get('ipv4', 'Не определен')}")
        print(f"✓ Внешний IPv6: {external_ips.get('ipv6', 'Не определен')}")
        
        # Проверка утечек
        ip_leak = network_info.get('ip_leak', {})
        if isinstance(ip_leak, dict):
            print(f"✓ IPv4 утечка: {'Да' if ip_leak.get('ipv4_leak') else 'Нет'}")
            print(f"✓ IPv6 утечка: {'Да' if ip_leak.get('ipv6_leak') else 'Нет'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка получения информации о сети: {e}")
        return False

def test_ipv6_configuration():
    """Тестирование конфигурации IPv6"""
    print("\n=== Тест конфигурации IPv6 ===")
    
    try:
        manager = get_ipv6_manager()
        
        # Загрузка конфигурации
        config = manager.config
        print(f"✓ IPv6 включен в конфигурации: {'Да' if config.get('ipv6_enabled') else 'Нет'}")
        print(f"✓ Dual-stack включен в конфигурации: {'Да' if config.get('dual_stack_enabled') else 'Нет'}")
        
        # Предпочтительные сервисы
        preferred_services = config.get('preferred_v6_services', [])
        print(f"✓ Предпочтительные IPv6 сервисы ({len(preferred_services)}):")
        for service in preferred_services[:3]:  # Показываем первые 3
            print(f"  - {service}")
        
        # DNS серверы
        dns_servers = config.get('ipv6_dns_servers', [])
        print(f"✓ IPv6 DNS серверы ({len(dns_servers)}):")
        for dns in dns_servers:
            print(f"  - {dns}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка конфигурации IPv6: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("Запуск тестирования IPv6 поддержки XVPN...")
    
    # Тестирование поддержки
    ipv6_supported = test_ipv6_support()
    
    # Тестирование подключения
    connectivity_ok = test_ipv6_connectivity()
    
    # Тестирование информации о сети
    network_info_ok = test_network_info_ipv6()
    
    # Тестирование конфигурации
    config_ok = test_ipv6_configuration()
    
    # Итоги
    print("\n=== Итоги тестирования IPv6 ===")
    
    total_tests = 4
    passed_tests = sum([
        ipv6_supported,
        connectivity_ok,
        network_info_ok,
        config_ok
    ])
    
    print(f"✓ Пройдено тестов: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("✓ Все тесты IPv6 пройдены успешно!")
        print("✓ XVPN полностью готов к работе с IPv6")
        return True
    else:
        print("✗ Некоторые тесты IPv6 не пройдены")
        
        if not ipv6_supported:
            print("✗ Система не поддерживает IPv6")
        if not connectivity_ok:
            print("✗ Проблемы с IPv6 подключением")
        if not network_info_ok:
            print("✗ Проблемы с информацией о сети")
        if not config_ok:
            print("✗ Проблемы с конфигурацией IPv6")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)