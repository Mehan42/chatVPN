## Архитектура сервисов XVPN

### Порты и сервисы:
- **Порт 443**: XRay VPN трафик (основной VPN endpoint)
- **Порт 8443**: MCP/API интерфейс управления (внутреннее использование)
- **Nginx (опционально)**: Маршрутизация внешнего трафика

### Конфигурация API сервера
```bash
# Создание конфигурационного файла API сервера
sudo tee /opt/xvpn/server/api/config.json > /dev/null << EOF
{
  "host": "127.0.0.1",
  "port": 8443,
  "ssl_enabled": true,
  "ssl_cert_path": "/opt/xvpn/tls/cert.pem",
  "ssl_key_path": "/opt/xvpn/tls/key.pem",
  "log_level": "INFO",
  "database_url": "sqlite:////opt/xvpn/data/xvpn.db"
}
EOF

sudo chown xvpn:xvpn /opt/xvpn/server/api/config.json
sudo chmod 644 /opt/xvpn/server/api/config.json
```

### Настройка Nginx для маршрутизации (опционально)
```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации Nginx
sudo tee /etc/nginx/sites-available/xvpn > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /opt/xvpn/tls/cert.pem;
    ssl_certificate_key /opt/xvpn/tls/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Все пути кроме внутренних API перенаправляем на XRay (VPN)
    location / {
        proxy_pass http://127.0.0.1:443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Внутренние API пути перенаправляем на MCP (порт 8443)
    location ~ ^/(mcp|api|admin) {
        proxy_pass https://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_verify off;
    }
}
EOF

# Включение сайта
sudo ln -sf /etc/nginx/sites-available/xvpn /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

После прохождения всех тестов система XVPN будет полностью готова к работе.