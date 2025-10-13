#!/usr/bin/env python3
"""
Скрипт для проверки изменения внешнего IP при подключении к VPN
"""

import requests
import time
import subprocess
import json
from datetime import datetime

def get_external_ip():
    """Получение внешнего IP-адреса"""
    services = [
        'https://api.ipify.org',
        'https://icanhazip.com',
        'https://ident.me',
        'https://ipecho.net/plain',
        'https://ifconfig.co/ip'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                # Проверяем, что полученный ответ является корректным IP-адресом
                if '.' in ip and len(ip.split('.')) == 4:
                    print(f"  IP получен с {service}: {ip}")
                    return ip
        except Exception as e:
            print(f"  Ошибка получения IP с {service}: {str(e)}")
            continue
    
    return None

def check_ip_change():
    """Проверка изменения IP перед и после подключения к VPN"""
    print("Проверка изменения внешнего IP...")
    
    # Получаем IP до подключения к VPN
    print("Получение внешнего IP до подключения к VPN...")
    ip_before = get_external_ip()
    if not ip_before:
        print("Ошибка: Не удалось получить IP до подключения к VPN")
        return False
    
    print(f"IP до подключения: {ip_before}")
    
    # Подключаемся к VPN
    print("\nПодключение к VPN...")
    print("Для этой проверки вам нужно вручную подключить VPN, затем нажмите Enter")
    input("Нажмите Enter после подключения к VPN...")
    
    # Ждем немного для стабилизации соединения
    print("Ожидание стабилизации соединения...")
    time.sleep(5)
    
    # Получаем IP после подключения к VPN
    print("\nПолучение внешнего IP после подключения к VPN...")
    ip_after = get_external_ip()
    if not ip_after:
        print("Ошибка: Не удалось получить IP после подключения к VPN")
        return False
    
    print(f"IP после подключения: {ip_after}")
    
    # Сравниваем IP-адреса
    if ip_before != ip_after:
        print(f"\n✅ IP изменился! Подключение к VPN работает корректно.")
        print(f"  До: {ip_before}")
        print(f"  После: {ip_after}")
        return True
    else:
        print(f"\n❌ IP не изменился. Подключение к VPN может не работать.")
        print(f"  До: {ip_before}")
        print(f"  После: {ip_after}")
        return False

def main():
    """Основная функция"""
    print("=== Тестирование изменения внешнего IP при подключении к VPN ===")
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        success = check_ip_change()
        
        print(f"\n=== Результат ===")
        if success:
            print("Тест пройден: IP-адрес изменился при подключении к VPN")
        else:
            print("Тест не пройден: IP-адрес не изменился при подключении к VPN")
            
    except Exception as e:
        print(f"Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()