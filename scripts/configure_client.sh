#!/bin/bash
# Интерактивная настройка XVPN клиента

set -e

CLIENT_DIR="."
CONFIG_FILE="./config/client_config.json"

echo "🚀 Настройка XVPN клиента"
echo "==========================="

read -p "Введите IP-адрес сервера XVPN: " SERVER_IP

# Проверяем, является ли введенный IP валидным
if ! [[ $SERVER_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]] && ! [[ $SERVER_IP =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
    echo "⚠️  Введен неверный формат IP-адреса или доменного имени"
    exit 1
fi

read -p "Введите DNS-сервер (по умолчанию 1.1.1.1): " DNS_SERVER
DNS_SERVER=${DNS_SERVER:-"1.1.1.1"}

read -p "Введите ID сервера (по умолчанию primary): " SERVER_ID
SERVER_ID=${SERVER_ID:-"primary"}

read -p "Введите имя сервера (по умолчанию Primary Server): " SERVER_NAME
SERVER_NAME=${SERVER_NAME:-"Primary Server"}

# Создаем директорию конфигурации, если не существует
mkdir -p ./config

# Обновляем конфигурационный файл
cat > "$CONFIG_FILE" << EOF
{
  "servers": [
    {
      "id": "$SERVER_ID",
      "api_url": "https://$SERVER_IP:8443",
      "connection_url": "vless://example-uuid@$SERVER_IP:443",
      "server_name": "$SERVER_NAME",
      "ip": "$SERVER_IP",
      "dns": "$DNS_SERVER",
      "priority": 1
    }
  ],
  "active_server": "$SERVER_ID",
  "default_profile": "default",
  "connection_timeout": 10,
  "reconnect_attempts": 3,
  "log_level": "INFO",
  "profiles_dir": "./profiles",
  "logs_dir": "./logs",
  "auto_switch": true,
  "switch_threshold": 1000
}
EOF

echo "✅ Конфигурация клиента обновлена"
echo "📋 Проверьте конфигурацию в $CONFIG_FILE"