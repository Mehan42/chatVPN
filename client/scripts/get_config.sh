#!/bin/bash
# Скрипт для получения конфигурации от API сервера

set -e

CLIENT_DIR="./client"
CONFIG_FILE="$CLIENT_DIR/config/client_config.json"
PROFILES_DIR="$CLIENT_DIR/profiles"

# Загружаем конфигурацию клиента
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Конфигурационный файл не найден: $CONFIG_FILE"
    echo "📋 Сначала настройте клиента: ./scripts/configure_client.sh"
    exit 1
fi

# Читаем активный сервер из конфига
ACTIVE_SERVER_ID=$(jq -r '.active_server' "$CONFIG_FILE")
SERVERS_JSON=$(jq -c ".servers[] | select(.id==\"$ACTIVE_SERVER_ID\")" "$CONFIG_FILE")

if [ -z "$SERVERS_JSON" ] || [ "$SERVERS_JSON" = "" ]; then
    echo "❌ Активный сервер не найден: $ACTIVE_SERVER_ID"
    exit 1
fi

API_URL=$(echo "$SERVERS_JSON" | jq -r '.api_url')
SERVER_IP=$(echo "$SERVERS_JSON" | jq -r '.ip')

echo "🔗 Подключение к API серверу: $API_URL"
echo "🌐 IP сервера: $SERVER_IP"

# Проверяем доступность API сервера
if ! curl -k -s --max-time 10 "$API_URL/mcp/v1/vpn.health" > /dev/null; then
    echo "❌ Не удается подключиться к API серверу: $API_URL"
    exit 1
else
    echo "✅ API сервер доступен"
fi

# Запрашиваем UUID у пользователя
read -p "Введите UUID клиента для получения конфигурации: " CLIENT_UUID

# Проверяем UUID на валидность
if [[ ! "$CLIENT_UUID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo "❌ Неверный формат UUID. Пример: 123e4567-e89b-12d3-a456-426614174000"
    exit 1
fi

# Получаем конфигурацию от API сервера
CONFIG_URL="$API_URL/clients/$CLIENT_UUID.json"
echo "📥 Получение конфигурации клиента $CLIENT_UUID..."

CONFIG_RESPONSE=$(curl -k -s --max-time 15 "$CONFIG_URL")

if [ "$CONFIG_RESPONSE" = "" ] || [ "$CONFIG_RESPONSE" = "{}" ]; then
    echo "❌ Не удалось получить конфигурацию для UUID $CLIENT_UUID"
    exit 1
fi

# Проверяем, есть ли ошибки в ответе
if echo "$CONFIG_RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
    ERROR_MSG=$(echo "$CONFIG_RESPONSE" | jq -r '.error')
    echo "❌ Ошибка от API сервера: $ERROR_MSG"
    exit 1
fi

# Создаем директорию профилей, если не существует
mkdir -p "$PROFILES_DIR"

# Сохраняем полученную конфигурацию
PROFILE_FILE="$PROFILES_DIR/$CLIENT_UUID.json"
echo "$CONFIG_RESPONSE" > "$PROFILE_FILE"

echo "✅ Конфигурация сохранена в: $PROFILE_FILE"
echo ""
echo "📋 Конфигурация клиента:"
echo "$CONFIG_RESPONSE" | jq '.'

echo ""
echo "💡 Для использования конфигурации подключите VPN-клиент к файлу: $PROFILE_FILE"