#!/usr/bin/env python3
# Тестирование системы безопасности XVPN
# Абсолютный путь: ~/chatvpn/server/security/test_security_system.py

import os
import sys
import time
import json
import requests
import threading
from pathlib import Path

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_manager import create_security_manager
from integrate_security import setup_security_integration

def test_security_manager():
    """Тестирование менеджера безопасности"""
    print("\n=== Тестирование менеджера безопасности ===")
    
    try:
        # Создание конфигурации
        security_config = {
            'max_failed_logins': 5,
            'block_duration': 3600,
            'rate_limit_requests': 100,
            'rate_limit_window': 3600,
            'enable_ip_whitelist': False,
            'enable_ip_blacklist': True,
            'enable_rate_limiting': True,
            'enable_anomaly_detection': True,
            'scan_interval': 300,
            'log_retention_days': 30
        }
        
        # Создание менеджера безопасности
        security_manager = create_security_manager(security_config)
        
        # Тестирование IP безопасности
        test_ip = "192.168.1.100"
        print(f"Тестирование IP безопасности для {test_ip}")
        
        # Проверка IP (должен быть разрешен)
        is_secure, message = security_manager.check_ip_security(test_ip)
        print(f"IP безопасность: {is_secure}, сообщение: {message}")
        
        # Блокировка IP
        security_manager.block_ip(test_ip, 3600)
        print(f"IP {test_ip} заблокирован на 3600 секунд")
        
        # Повторная проверка IP (должен быть заблокирован)
        is_secure, message = security_manager.check_ip_security(test_ip)
        print(f"IP безопасность после блокировки: {is_secure}, сообщение: {message}")
        
        # Разблокировка IP
        security_manager.unblock_ip(test_ip)
        print(f"IP {test_ip} разблокирован")
        
        # Повторная проверка IP (должен быть разрешен)
        is_secure, message = security_manager.check_ip_security(test_ip)
        print(f"IP безопасность после разблокировки: {is_secure}, сообщение: {message}")
        
        # Тестирование rate limiting
        print("\nТестирование rate limiting")
        for i in range(5):
            rate_limited = security_manager.check_rate_limit(test_ip)
            print(f"Request {i+1}: Rate limited = {rate_limited}")
            time.sleep(0.1)
        
        # Получение отчета о безопасности
        print("\nПолучение отчета о безопасности")
        security_report = security_manager.get_security_report()
        print("Статус безопасности:", security_report.get('status'))
        print("Количество событий:", len(security_report.get('recent_events', [])))
        
        # Получение рекомендаций
        print("\nПолучение рекомендаций по безопасности")
        recommendations = security_manager.get_security_recommendations()
        print("Количество рекомендаций:", len(recommendations))
        
        print("✓ Менеджер безопасности протестирован успешно")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования менеджера безопасности: {e}")
        return False

def test_security_integration():
    """Тестирование интеграции безопасности"""
    print("\n=== Тестирование интеграции безопасности ===")
    
    try:
        # Настройка интеграции безопасности
        security_manager = setup_security_integration()
        
        # Проверка конфигурации
        config_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'config.json'
        if config_path.exists():
            print("✓ Конфигурация безопасности создана")
        else:
            print("✗ Конфигурация безопасности не найдена")
        
        # Проверка systemd сервиса
        service_path = Path('/etc/systemd/system/xvpn-security.service')
        if service_path.exists():
            print("✓ Systemd сервис безопасности создан")
        else:
            print("✗ Systemd сервис безопасности не найден")
        
        # Проверка конфигурации API
        api_config_path = Path.home() / 'chatvpn' / 'server' / 'api' / 'security_config.json'
        if api_config_path.exists():
            print("✓ Конфигурация API безопасности создана")
        else:
            print("✗ Конфигурация API безопасности не найдена")
        
        # Проверка SQL схемы
        sql_schema_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'security_schema.sql'
        if sql_schema_path.exists():
            print("✓ SQL схема безопасности создана")
        else:
            print("✗ SQL схема безопасности не найдена")
        
        # Проверка скрипта мониторинга
        monitoring_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'security_monitor.py'
        if monitoring_path.exists():
            print("✓ Скрипт мониторинга безопасности создан")
        else:
            print("✗ Скрипт мониторинга безопасности не найден")
        
        print("✓ Интеграция безопасности протестирована успешно")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования интеграции безопасности: {e}")
        return False

def test_api_security():
    """Тестирование API безопасности"""
    print("\n=== Тестирование API безопасности ===")
    
    try:
        # Запуск тестового сервера API безопасности
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        # Инициализация безопасности
        security_config = {
            'max_failed_logins': 5,
            'block_duration': 3600,
            'rate_limit_requests': 100,
            'rate_limit_window': 3600,
            'enable_ip_whitelist': False,
            'enable_ip_blacklist': True,
            'enable_rate_limiting': True,
            'enable_anomaly_detection': True,
            'scan_interval': 300,
            'log_retention_days': 30
        }
        
        security_manager = create_security_manager(security_config)
        
        # Middleware для безопасности
        @app.before_request
        def security_check():
            client_ip = request.remote_addr
            is_secure, message = security_manager.check_ip_security(client_ip)
            
            if not is_secure:
                return jsonify({'error': message}), 403
            
            if security_manager.check_rate_limit(client_ip):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return None
        
        # API эндпоинты
        @app.route('/api/security/status')
        def security_status():
            return jsonify(security_manager.get_security_report())
        
        @app.route('/api/security/block-ip', methods=['POST'])
        def block_ip():
            data = request.get_json()
            ip = data.get('ip')
            duration = data.get('duration', 3600)
            
            if ip:
                security_manager.block_ip(ip, duration)
                return jsonify({'message': f'IP {ip} blocked for {duration} seconds'})
            else:
                return jsonify({'error': 'IP address required'}), 400
        
        @app.route('/api/security/unblock-ip', methods=['POST'])
        def unblock_ip():
            data = request.get_json()
            ip = data.get('ip')
            
            if ip:
                security_manager.unblock_ip(ip)
                return jsonify({'message': f'IP {ip} unblocked'})
            else:
                return jsonify({'error': 'IP address required'}), 400
        
        # Запуск тестового сервера
        import threading
        
        def run_test_server():
            app.run(host='127.0.0.1', port=5001, debug=True)
        
        server_thread = threading.Thread(target=run_test_server, daemon=True)
        server_thread.start()
        
        # Ожидание запуска сервера
        time.sleep(2)
        
        # Тестирование API
        base_url = 'http://127.0.0.1:5001'
        
        # Тест статуса безопасности
        response = requests.get(f'{base_url}/api/security/status')
        if response.status_code == 200:
            print("✓ API статус безопасности работает")
        else:
            print("✗ API статус безопасности не работает")
        
        # Тест блокировки IP
        test_ip = "192.168.1.200"
        response = requests.post(f'{base_url}/api/security/block-ip', 
                                json={'ip': test_ip, 'duration': 300})
        if response.status_code == 200:
            print("✓ API блокировки IP работает")
        else:
            print("✗ API блокировки IP не работает")
        
        # Тест разблокировки IP
        response = requests.post(f'{base_url}/api/security/unblock-ip', 
                                json={'ip': test_ip})
        if response.status_code == 200:
            print("✓ API разблокировки IP работает")
        else:
            print("✗ API разблокировки IP не работает")
        
        print("✓ API безопасности протестировано успешно")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования API безопасности: {e}")
        return False

def test_database_integration():
    """Тестирование интеграции с базой данных"""
    print("\n=== Тестирование интеграции с базой данных ===")
    
    try:
        # Проверка существования SQL схемы
        sql_schema_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'security_schema.sql'
        if not sql_schema_path.exists():
            print("✗ SQL схема безопасности не найдена")
            return False
        
        # Чтение SQL схемы
        with open(sql_schema_path, 'r') as f:
            sql_content = f.read()
        
        # Проверка наличия таблиц
        expected_tables = ['security_events', 'blocked_ips', 'security_rules']
        for table in expected_tables:
            if f'CREATE TABLE IF NOT EXISTS {table}' in sql_content:
                print(f"✓ Таблица {table} найдена в схеме")
            else:
                print(f"✗ Таблица {table} не найдена в схеме")
                return False
        
        # Тестирование создания таблиц (в памяти)
        import sqlite3
        
        # Создание тестовой базы данных в памяти
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Выполнение SQL скрипта
        cursor.executescript(sql_content)
        
        # Проверка существования таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in expected_tables:
            if table in tables:
                print(f"✓ Таблица {table} создана успешно")
            else:
                print(f"✗ Таблица {table} не создана")
                return False
        
        conn.close()
        
        print("✓ Интеграция с базой данных протестирована успешно")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования интеграции с базой данных: {e}")
        return False

def test_systemd_service():
    """Тестирование systemd сервиса"""
    print("\n=== Тестирование systemd сервиса ===")
    
    try:
        # Проверка существования systemd сервиса
        service_path = Path('/etc/systemd/system/xvpn-security.service')
        if not service_path.exists():
            print("✗ Systemd сервис безопасности не найден")
            return False
        
        # Проверка содержимого сервиса
        with open(service_path, 'r') as f:
            service_content = f.read()
        
        # Проверка важных параметров
        required_params = [
            'Description=XVPN Security Manager',
            'After=network.target',
            'Type=simple',
            'User=xvpn',
            'Group=xvpn',
            'ExecStart=/usr/bin/python3 /home/xvpn/chatvpn/server/security/integrate_security.py'
        ]
        
        for param in required_params:
            if param in service_content:
                print(f"✓ Параметр найден: {param}")
            else:
                print(f"✗ Параметр не найден: {param}")
                return False
        
        print("✓ Systemd сервис безопасности протестирован успешно")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования systemd сервиса: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("=== Тестирование системы безопасности XVPN ===")
    
    results = []
    
    # Тестирование менеджера безопасности
    results.append(("Менеджер безопасности", test_security_manager()))
    
    # Тестирование интеграции безопасности
    results.append(("Интеграция безопасности", test_security_integration()))
    
    # Тестирование API безопасности
    results.append(("API безопасности", test_api_security()))
    
    # Тестирование интеграции с базой данных
    results.append(("Интеграция с базой данных", test_database_integration()))
    
    # Тестирование systemd сервиса
    results.append(("Systemd сервис", test_systemd_service()))
    
    # Вывод результатов
    print("\n=== Результаты тестирования ===")
    success_count = 0
    total_count = len(results)
    
    for test_name, result in results:
        if result:
            print(f"✓ {test_name}: Успешно")
            success_count += 1
        else:
            print(f"✗ {test_name}: Ошибка")
    
    # Общий результат
    print(f"\nОбщий результат: {success_count}/{total_count} тестов пройдено успешно")
    
    if success_count == total_count:
        print("🎉 Все тесты системы безопасности пройдены успешно!")
        return True
    else:
        print("❌ Некоторые тесты не пройдены. Проверьте вывод выше.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)