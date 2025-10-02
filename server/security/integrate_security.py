#!/usr/bin/env python3
# Интеграция системы безопасности с XVPN
# Абсолютный путь: ~/chatvpn/server/security/integrate_security.py

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_manager import create_security_manager

def setup_security_integration():
    """Настройка интеграции системы безопасности"""
    print("=== Интеграция системы безопасности XVPN ===")
    
    # Конфигурация безопасности
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
    
    # Создание systemd сервиса
    create_security_systemd_service()
    
    # Интеграция с API
    integrate_with_api(security_manager)
    
    # Интеграция с базой данных
    integrate_with_database(security_manager)
    
    # Настройка мониторинга
    setup_monitoring(security_manager)
    
    print("=== Интеграция безопасности завершена ===")
    
    return security_manager

def create_security_systemd_service():
    """Создание systemd сервиса для системы безопасности"""
    print("\n=== Создание systemd сервиса для безопасности ===")
    
    service_content = f"""[Unit]
Description=XVPN Security Manager
After=network.target
Requires=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/home/xvpn/chatvpn
ExecStart=/usr/bin/python3 /home/xvpn/chatvpn/server/security/integrate_security.py
Restart=always
RestartSec=10
Environment=XVPN_SECURITY_CONFIG=/home/xvpn/chatvpn/server/security/config.json
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    # Запись сервиса
    service_file = Path('/etc/systemd/system/xvpn-security.service')
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✓ Сервис создан: {service_file}")
        
        # Активация сервиса
        print("Активация сервиса...")
        os.system('sudo systemctl daemon-reload')
        os.system('sudo systemctl enable xvpn-security.service')
        os.system('sudo systemctl start xvpn-security.service')
        
        # Проверка статуса
        result = os.system('sudo systemctl status xvpn-security.service')
        if result == 0:
            print("✓ Сервис безопасности успешно запущен")
        else:
            print("✗ Ошибка запуска сервиса")
            
    except Exception as e:
        print(f"✗ Ошибка создания сервиса: {e}")

def integrate_with_api(security_manager):
    """Интеграция с REST API"""
    print("\n=== Интеграция с REST API ===")
    
    try:
        # Создание эндпоинтов безопасности
        api_endpoints = {
            '/api/security/status': {
                'method': 'GET',
                'description': 'Получение статуса безопасности',
                'response': security_manager.get_security_report()
            },
            '/api/security/events': {
                'method': 'GET',
                'description': 'Получение событий безопасности',
                'response': [str(event) for event in security_manager.events]
            },
            '/api/security/block-ip': {
                'method': 'POST',
                'description': 'Блокировка IP адреса',
                'parameters': {'ip': 'string', 'duration': 'int'}
            },
            '/api/security/unblock-ip': {
                'method': 'POST',
                'description': 'Разблокировка IP адреса',
                'parameters': {'ip': 'string'}
            },
            '/api/security/recommendations': {
                'method': 'GET',
                'description': 'Получение рекомендаций по безопасности',
                'response': security_manager.get_security_recommendations()
            }
        }
        
        # Создание конфигурации для API
        api_config = {
            'security_endpoints': api_endpoints,
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60,
                'burst_limit': 10
            },
            'authentication': {
                'enabled': True,
                'required_roles': ['admin', 'security']
            }
        }
        
        # Сохранение конфигурации
        config_path = Path.home() / 'chatvpn' / 'server' / 'api' / 'security_config.json'
        with open(config_path, 'w') as f:
            json.dump(api_config, f, indent=2)
        
        print(f"✓ Конфигурация API безопасности сохранена: {config_path}")
        
        # Интеграция с существующим API
        integrate_with_existing_api(security_manager)
        
    except Exception as e:
        print(f"✗ Ошибка интеграции с API: {e}")

def integrate_with_existing_api(security_manager):
    """Интеграция с существующим REST API"""
    try:
        # Обновление существующего API
        api_update_script = """
# Добавление безопасности в существующее API
from flask import Flask, request, jsonify
import logging
from security_manager import create_security_manager

app = Flask(__name__)

# Инициализация безопасности
security_manager = create_security_manager()

@app.before_request
def security_check():
    # Проверка IP безопасности
    client_ip = request.remote_addr
    is_secure, message = security_manager.check_ip_security(client_ip)
    
    if not is_secure:
        return jsonify({'error': message}), 403
    
    # Rate limiting
    if security_manager.check_rate_limit(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    return None

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
"""
        
        # Сохранение скрипта
        script_path = Path.home() / 'chatvpn' / 'server' / 'api' / 'security_middleware.py'
        with open(script_path, 'w') as f:
            f.write(api_update_script)
        
        print(f"✓ Middleware для безопасности создан: {script_path}")
        
    except Exception as e:
        print(f"✗ Ошибка интеграции с существующим API: {e}")

def integrate_with_database(security_manager):
    """Интеграция с базой данных"""
    print("\n=== Интеграция с базой данных ===")
    
    try:
        # Создание таблиц для безопасности
        security_tables = {
            'security_events': {
                'columns': [
                    'id TEXT PRIMARY KEY',
                    'timestamp DATETIME',
                    'event_type TEXT',
                    'severity TEXT',
                    'source_ip TEXT',
                    'details TEXT',
                    'resolved BOOLEAN',
                    'resolved_at DATETIME'
                ]
            },
            'blocked_ips': {
                'columns': [
                    'ip TEXT PRIMARY KEY',
                    'blocked_at DATETIME',
                    'expires_at DATETIME',
                    'reason TEXT'
                ]
            },
            'security_rules': {
                'columns': [
                    'id TEXT PRIMARY KEY',
                    'name TEXT',
                    'type TEXT',
                    'enabled BOOLEAN',
                    'parameters TEXT',
                    'created_at DATETIME',
                    'updated_at DATETIME'
                ]
            }
        }
        
        # Создание SQL скрипта
        sql_script = "-- SQL скрипт для безопасности XVPN\n"
        sql_script += "-- Создание таблиц\n"
        
        for table_name, table_def in security_tables.items():
            sql_script += f"\n-- Таблица: {table_name}\n"
            sql_script += f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            sql_script += ",\n".join(f"    {col}" for col in table_def['columns'])
            sql_script += "\n);\n"
        
        # Сохранение SQL скрипта
        sql_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'security_schema.sql'
        with open(sql_path, 'w') as f:
            f.write(sql_script)
        
        print(f"✓ SQL скрипт для безопасности создан: {sql_path}")
        
    except Exception as e:
        print(f"✗ Ошибка интеграции с базой данных: {e}")

def setup_monitoring(security_manager):
    """Настройка мониторинга безопасности"""
    print("\n=== Настройка мониторинга безопасности ===")
    
    try:
        # Создание скрипта мониторинга
        monitoring_script = """
#!/usr/bin/env python3
# Скрипт мониторинга безопасности XVPN
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.append('/home/xvpn/chatvpn')
from security_manager import create_security_manager

def security_monitor():
    """Мониторинг безопасности"""
    security_manager = create_security_manager()
    
    while True:
        try:
            # Получение отчета о безопасности
            report = security_manager.get_security_report()
            
            # Проверка критических событий
            critical_events = [event for event in report.get('recent_events', []) 
                             if event.get('severity') == 'critical']
            
            if critical_events:
                # Отправка уведомления
                send_security_alert(critical_events)
            
            # Сохранение отчета
            save_security_report(report)
            
            # Пауза перед следующей проверкой
            time.sleep(300)  # 5 минут
            
        except Exception as e:
            print(f"Ошибка мониторинга: {e}")
            time.sleep(60)

def send_security_alert(events):
    """Отправка уведомления о безопасности"""
    # Здесь можно добавить отправку email, Telegram и т.д.
    for event in events:
        print(f"КРИТИЧЕСКОЕ СОБЫТИЕ: {event}")

def save_security_report(report):
    """Сохранение отчета о безопасности"""
    report_path = Path('/home/xvpn/chatvpn/server/security/reports')
    report_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_path / f'security_report_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == '__main__':
    security_monitor()
"""
        
        # Сохранение скрипта мониторинга
        monitoring_path = Path.home() / 'chatvpn' / 'server' / 'security' / 'security_monitor.py'
        with open(monitoring_path, 'w') as f:
            f.write(monitoring_script)
        
        print(f"✓ Скрипт мониторинга создан: {monitoring_path}")
        
        # Создание cron задания
        cron_job = f"* * * * * /usr/bin/python3 {monitoring_path} >> /var/log/xvpn-security-monitor.log 2>&1"
        
        # Добавление в cron
        try:
            with open('/tmp/xvpn-security-cron', 'w') as f:
                f.write(cron_job + '\n')
            
            os.system('crontab /tmp/xvpn-security-cron')
            os.system('rm /tmp/xvpn-security-cron')
            
            print("✓ Cron задание для мониторинга безопасности добавлено")
            
        except Exception as e:
            print(f"✗ Ошибка добавления cron задания: {e}")
        
    except Exception as e:
        print(f"✗ Ошибка настройки мониторинга: {e}")

if __name__ == "__main__":
    # Запуск интеграции безопасности
    security_manager = setup_security_integration()
    
    # Запуск мониторинга
    print("\n=== Запуск мониторинга безопасности ===")
    try:
        monitoring_thread = threading.Thread(target=security_manager.security_scanner_loop, daemon=True)
        monitoring_thread.start()
        print("✓ Мониторинг безопасности запущен")
    except Exception as e:
        print(f"✗ Ошибка запуска мониторинга: {e}")
    
    # Ожидание завершения
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nПрекращение работы системы безопасности")