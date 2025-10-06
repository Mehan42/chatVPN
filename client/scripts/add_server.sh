#!/bin/bash
# Скрипт для добавления дополнительного сервера

set -e

CLIENT_DIR="./client"
CONFIG_FILE="$CLIENT_DIR/config/client_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Конфигурационный файл не найден: $CONFIG_FILE"
    exit 1
fi

echo "🌐 Добавление нового сервера"
echo "============================"

read -p "Введите IP-адрес нового сервера: " NEW_SERVER_IP
read -p "Введите DNS-сервер для нового сервера (по умолчанию 1.1.1.1): " NEW_DNS
NEW_DNS=${NEW_DNS:-"1.1.1.1"}
read -p "Введите ID сервера (по умолчанию secondary): " NEW_SERVER_ID
NEW_SERVER_ID=${NEW_SERVER_ID:-"secondary"}
read -p "Введите имя сервера (по умолчанию Secondary Server): " NEW_SERVER_NAME
NEW_SERVER_NAME=${NEW_SERVER_NAME:-"Secondary Server"}

# Читаем текущую конфигурацию
CURRENT_CONFIG=$(cat "$CONFIG_FILE")

# Извлекаем массив серверов
SERVERS_JSON=$(echo "$CURRENT_CONFIG" | jq '.servers')
NEW_SERVER_JSON=$(jq -n --arg id "$NEW_SERVER_ID" --arg api_url "https://$NEW_SERVER_IP:8443" --arg conn_url "vless://example-uuid@$NEW_SERVER_IP:443" --arg name "$NEW_SERVER_NAME" --arg ip "$NEW_SERVER_IP" --arg dns "$NEW_DNS" --argjson priority 2 '{
  id: $id,
  api_url: $api_url,
  connection_url: $conn_url,
  server_name: $name,
  ip: $ip,
  dns: $dns,
  priority: $priority
}')

# Добавляем новый сервер к массиву
NEW_SERVERS_JSON=$(echo "$SERVERS_JSON" | jq --argjson new_server "$NEW_SERVER_JSON" '. += [$new_server]')

# Обновляем конфигурацию с новым массивом серверов
UPDATED_CONFIG=$(echo "$CURRENT_CONFIG" | jq --argjson new_servers "$NEW_SERVERS_JSON" '.servers = $new_servers')

# Сохраняем обновленную конфигурацию
echo "$UPDATED_CONFIG" > "$CONFIG_FILE"

echo "✅ Новый сервер добавлен в конфигурацию"
echo "📋 Проверьте обновленную конфигурацию в $CONFIG_FILE"