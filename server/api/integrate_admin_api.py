#!/usr/bin/env python3
# Интеграция REST API с основной системой XVPN
# Абсолютный путь: ~/chatvpn/server/api/integrate_admin_api.py

import os
import sys
import json
import logging
from pathlib import Path

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_rest_api import create_admin_api

def setup_admin_api():
    """Настройка REST API для администрирования"""
    print("=== Настройка REST API для администрирования XVPN ===")
    
    # Конфигурация API
    config = {
        'secret_key': os.environ.get('XVPN_API_SECRET', 'xvpn-admin-secret-key-change-me'),
        'jwt_secret_key': os.environ.get('XVPN_JWT_SECRET', 'xvpn-jwt-secret-key-change-me'),
        'allowed_origins': [
            'http://localhost:3000',
            'https://admin.xvpn.com',
            'https://api.xvpn.com'
        ]
    }
    
    # Создание API экземпляра
    api = create_admin_api(config)
    
    # Создание директорий
    log_dir = Path.home() / 'chatvpn' / 'server' / 'api' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Настройка логирования
    log_file = log_dir / 'admin_api.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("REST API для администрирования XVPN настроен успешно")
    
    # Запуск API
    api.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )

def create_systemd_service():
    """Создание systemd сервиса для REST API"""
    print("\n=== Создание systemd сервиса для REST API ===")
    
    service_content = f"""[Unit]
Description=XVPN Admin REST API
After=network.target
Requires=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/home/xvpn/chatvpn
ExecStart=/usr/bin/python3 /home/xvpn/chatvpn/server/api/integrate_admin_api.py
Restart=always
RestartSec=10
Environment=XVPN_API_SECRET=xvpn-admin-secret-key-change-me
Environment=XVPN_JWT_SECRET=xvpn-jwt-secret-key-change-me
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    # Запись сервиса
    service_file = Path('/etc/systemd/system/xvpn-admin-api.service')
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✓ Сервис создан: {service_file}")
        
        # Активация сервиса
        print("Активация сервиса...")
        os.system('sudo systemctl daemon-reload')
        os.system('sudo systemctl enable xvpn-admin-api.service')
        os.system('sudo systemctl start xvpn-admin-api.service')
        
        # Проверка статуса
        result = os.system('sudo systemctl status xvpn-admin-api.service')
        if result == 0:
            print("✓ Сервис успешно запущен")
        else:
            print("✗ Ошибка запуска сервиса")
            
    except Exception as e:
        print(f"✗ Ошибка создания сервиса: {e}")

def setup_database():
    """Настройка базы данных для REST API"""
    print("\n=== Настройка базы данных для REST API ===")
    
    # Проверка существования базы данных
    db_path = Path.home() / 'chatvpn' / 'server' / 'api' / 'admin.db'
    
    if not db_path.exists():
        print("✓ База данных будет создана при первом запуске API")
    else:
        print(f"✓ База данных уже существует: {db_path}")
    
    # Создание пользователя для базы данных
    print("Настройка пользователя базы данных...")
    
    # SQLite не требует отдельного пользователя, но для PostgreSQL можно добавить
    
    print("✓ База данных настроена")

def create_admin_user():
    """Создание администратора"""
    print("\n=== Создание администратора ===")
    
    admin_data = {
        'username': 'admin',
        'email': 'admin@xvpn.com',
        'password': os.environ.get('XVPN_ADMIN_PASSWORD', 'XVPN Admin 2024!'),
        'role': 'admin'
    }
    
    print(f"Создание администратора: {admin_data['username']}")
    print(f"Email: {admin_data['email']}")
    print(f"Пароль: {admin_data['password']}")
    print("Важно: Измените пароль после первого входа!")
    
    # Создание пользователя будет выполнено при первом запуске API
    print("✓ Администратор будет создан при первом запуске API")

def setup_nginx_proxy():
    """Настройка Nginx прокси для REST API"""
    print("\n=== Настройка Nginx прокси ===")
    
    nginx_config = f"""server {{
    listen 80;
    server_name admin.xvpn.com;
    
    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name admin.xvpn.com;
    
    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/admin.xvpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.xvpn.com/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # Безопасность
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API прокси
    location /api/ {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Буферы
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }}
    
    # Статические файлы
    location / {{
        root /var/www/xvpn-admin;
        index index.html;
    }}
    
    # Логирование
    access_log /var/log/nginx/xvpn-admin-access.log;
    error_log /var/log/nginx/xvpn-admin-error.log;
}}
"""
    
    # Запись конфигурации
    nginx_file = Path('/etc/nginx/sites-available/xvpn-admin')
    
    try:
        with open(nginx_file, 'w') as f:
            f.write(nginx_config)
        
        print(f"✓ Nginx конфигурация создана: {nginx_file}")
        
        # Активация сайта
        os.system(f'sudo ln -sf {nginx_file} /etc/nginx/sites-enabled/')
        
        # Проверка конфигурации
        result = os.system('sudo nginx -t')
        if result == 0:
            print("✓ Nginx конфигурация валидна")
            
            # Перезапуск Nginx
            os.system('sudo systemctl restart nginx')
            print("✓ Nginx перезапущен")
        else:
            print("✗ Ошибка валидации Nginx конфигурации")
            
    except Exception as e:
        print(f"✗ Ошибка создания Nginx конфигурации: {e}")

def create_letsencrypt_cert():
    """Создание SSL сертификата Let's Encrypt"""
    print("\n=== Создание SSL сертификата ===")
    
    print("Проверка наличия сертификата...")
    
    cert_path = Path('/etc/letsencrypt/live/admin.xvpn.com')
    
    if cert_path.exists():
        print("✓ Сертификат уже существует")
    else:
        print("Создание нового сертификата...")
        
        # Проверка наличия certbot
        if os.system('which certbot > /dev/null') != 0:
            print("✗ Certbot не установлен")
            print("Установка certbot...")
            os.system('sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx')
        
        # Создание сертификата
        print("Создание сертификата для admin.xvpn.com...")
        result = os.system('sudo certbot certonly --nginx -d admin.xvpn.com --email admin@xvpn.com --agree-tos --no-eff-email')
        
        if result == 0:
            print("✓ Сертификат успешно создан")
        else:
            print("✗ Ошибка создания сертификата")
            print("Ручная настройка SSL может потребоваться")

def setup_firewall():
    """Настройка файрвола"""
    print("\n=== Настройка файрвола ===")
    
    # Разрешение HTTPS порта
    os.system('sudo ufw allow 443/tcp')
    os.system('sudo ufw allow 80/tcp')  # Для Let's Encrypt
    
    print("✓ Файрвол настроен")

def main():
    """Основная функция"""
    print("Начало интеграции REST API с XVPN")
    
    try:
        # Настройка базы данных
        setup_database()
        
        # Создание администратора
        create_admin_user()
        
        # Настройка Nginx
        setup_nginx_proxy()
        
        # Создание SSL сертификата
        create_letsencrypt_cert()
        
        # Настройка файрвола
        setup_firewall()
        
        # Создание systemd сервиса
        create_systemd_service()
        
        print("\n=== Интеграция REST API завершена ===")
        print("\nДоступные эндпоинты:")
        print("  - Health check: http://admin.xvpn.com/api/health")
        print("  - API: https://admin.xvpn.com/api/")
        print("  - Документация: https://admin.xvpn.com/docs")
        
        print("\nДля доступа к панели администратора:")
        print("  - URL: https://admin.xvpn.com")
        print("  - Логин: admin")
        print("  - Пароль: XVPN Admin 2024!")
        
        print("\nДля просмотра логов:")
        print("  - sudo journalctl -u xvpn-admin-api -f")
        print("  - sudo tail -f /home/xvpn/chatvpn/server/api/logs/admin_api.log")
        
    except Exception as e:
        print(f"\n✗ Ошибка интеграции: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()