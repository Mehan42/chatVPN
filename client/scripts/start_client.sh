#!/bin/bash
# Скрипт для запуска XVPN клиента

set -e

CLIENT_DIR="./client"
CONFIG_FILE="$CLIENT_DIR/config/client_config.json"
PROFILES_DIR="$CLIENT_DIR/profiles"

# Функция для проверки зависимости
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 не установлен"
        return 1
    fi
}

# Проверяем зависимости
echo "🔍 Проверка зависимостей..."
check_dependency jq || exit 1
check_dependency curl || exit 1
check_dependency xray || echo "⚠️  Xray не установлен (требуется для подключения)"

echo ""
echo "🚀 Запуск XVPN клиента"
echo "======================"

# Загружаем конфигурацию клиента
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Конфигурационный файл не найден: $CONFIG_FILE"
    echo "📋 Сначала настройте клиента: ./scripts/configure_client.sh"
    exit 1
fi

# Загружаем настройки
ACTIVE_SERVER_ID=$(jq -r '.active_server' "$CONFIG_FILE")
CONNECTION_TIMEOUT=$(jq -r '.connection_timeout' "$CONFIG_FILE")
LOG_LEVEL=$(jq -r '.log_level' "$CONFIG_FILE")

echo "📡 Активный сервер: $ACTIVE_SERVER_ID"
echo "⏱️ Таймаут подключения: ${CONNECTION_TIMEOUT}s"

# Проверяем, есть ли профили подключения
PROFILES=($(ls "$PROFILES_DIR"/*.json 2>/dev/null | head -10))
if [ ${#PROFILES[@]} -eq 0 ]; then
    echo "❌ Не найдено профилей подключения в $PROFILES_DIR"
    echo "📋 Получите профиль сначала: ./scripts/get_config.sh"
    exit 1
fi

echo "📋 Найдено профилей: ${#PROFILES[@]}"
for PROFILE in "${PROFILES[@]}"; do
    UUID=$(basename "$PROFILE" .json)
    echo "   - $UUID"
done

# Пока что просто выводим информацию, в реальном варианте
# здесь будет запуск Xray с конфигурацией из профиля
echo ""
echo "💡 Для запуска VPN-соединения:"
echo "   1. Выберите профиль из: $PROFILES_DIR"
echo "   2. Запустите Xray с конфигурацией: xray run -config $PROFILE"
echo ""
echo "📋 Пример команды: xray run -config $PROFILES_DIR/$(basename "${PROFILES[0]}")"

# Создаем временный конфигурационный файл для тестирования
if [ -f "${PROFILES[0]}" ]; then
    TEMP_CONFIG="/tmp/xray_temp_config.json"
    cp "${PROFILES[0]}" "$TEMP_CONFIG"
    echo "📋 Временный конфигурационный файл создан: $TEMP_CONFIG"
    echo "💡 Проверьте его содержимое перед подключением"
fi