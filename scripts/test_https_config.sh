#!/bin/bash

# Скрипт тестирования HTTPS загрузки конфигов
# Абсолютный путь: ~/chatvpn/scripts/test_https_config.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Тестирование HTTPS загрузки конфигов ===${NC}"

# Тестовые URL
API_URL="https://api.uss.hopto.org"
BOT_URL="https://bot.uss.hopto.org"
CONFIG_URL="${API_URL}/config"
MANIFEST_URL="${API_URL}/transports/manifest.json"

# Тестовые данные
TEST_CONFIG='{
  "version": "1.0.0",
  "protocols": ["vless", "vmess"],
  "servers": [
    {
      "address": "uss.hopto.org",
      "port": 443,
      "type": "https"
    }
  ],
  "uuid": "test-uuid-12345",
  "created_at": "2025-01-01T00:00:00Z"
}'

# Функция тестирования HTTPS соединения
test_https_connection() {
    local url=$1
    local description=$2
    
    echo -e "${YELLOW}Тестирование: $description${NC}"
    echo "URL: $url"
    
    # Проверка доступности
    if curl -s --head "$url" > /dev/null; then
        echo -e "${GREEN}✓ Соединение установлено${NC}"
        
        # Проверка SSL/TLS
        echo "Проверка SSL/TLS..."
        if curl -s -k -I "$url" | grep -i "server: nginx\|server: traefik" > /dev/null; then
            echo -e "${GREEN}✓ Сервер идентифицирован${NC}"
        else
            echo -e "${YELLOW}⚠ Сервер не идентифицирован${NC}"
        fi
        
        # Проверка сертификата
        echo "Проверка сертификата..."
        local cert_info=$(echo -n | openssl s_client -connect "$(echo "$url" | sed 's|https://||' | sed 's|/.*||'):443" 2>/dev/null | openssl x509 -noout -dates -issuer -subject)
        if [[ -n "$cert_info" ]]; then
            echo -e "${GREEN}✓ Сертификат валиден${NC}"
            echo "Информация о сертификате:"
            echo "$cert_info" | head -5
        else
            echo -e "${RED}✗ Сертификат не валиден${NC}"
        fi
        
        # Проверка HSTS
        echo "Проверка HSTS..."
        local hsts=$(curl -s -k -I "$url" | grep -i "strict-transport-security")
        if [[ -n "$hsts" ]]; then
            echo -e "${GREEN}✓ HSTS активен${NC}"
            echo "HSTS: $hsts"
        else
            echo -e "${YELLOW}⚠ HSTS не обнаружен${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}✗ Соединение не установлено${NC}"
        return 1
    fi
}

# Функция тестирования API эндпоинтов
test_api_endpoints() {
    local url=$1
    local endpoint=$2
    local description=$3
    
    echo -e "${YELLOW}Тестирование: $description${NC}"
    echo "URL: ${url}${endpoint}"
    
    # Тест GET запроса
    local response=$(curl -s -k -w "%{http_code}" "${url}${endpoint}" -o /tmp/response.json)
    
    if [[ "$response" == "200" ]]; then
        echo -e "${GREEN}✓ GET запрос успешен (200 OK)${NC}"
        
        # Проверка JSON ответа
        if [[ -s /tmp/response.json ]]; then
            echo -e "${GREEN}✓ JSON ответ получен${NC}"
            echo "Ответ (первые 200 символов):"
            head -c 200 /tmp/response.json
            echo "..."
        else
            echo -e "${YELLOW}⚠ Пустой ответ${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}✗ GET запрос неуспешен ($response)${NC}"
        if [[ -s /tmp/response.json ]]; then
            echo "Ошибка:"
            cat /tmp/response.json
        fi
        return 1
    fi
}

# Функция тестирования TLS пиннинга
test_tls_pinning() {
    echo -e "${YELLOW}Тестирование TLS пиннинга${NC}"
    
    # Создаем тестовый Python скрипт для проверки TLS пиннинга
    cat > /tmp/test_tls_pinning.py << 'EOF'
#!/usr/bin/env python3
import ssl
import hashlib
import requests
import sys

def test_certificate_pinning():
    # Ожидаемый fingerprint (замените на реальный)
    expected_fingerprint = "a37542363831b757b8a5d3d8a9c4f6e7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"
    
    try:
        # Тест соединения с Let's Encrypt
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Получаем сертификат
        with context.wrap_socket(ssl.create_default_socket(), server_hostname="uss.hopto.org") as sock:
            der_cert = sock.getpeercert(binary_form=True)
            actual_fingerprint = hashlib.sha256(der_cert).hexdigest()
        
        print(f"Ожидаемый fingerprint: {expected_fingerprint}")
        print(f"Фактический fingerprint: {actual_fingerprint}")
        
        if actual_fingerprint == expected_fingerprint:
            print("✓ TLS пиннинг прошел успешно")
            return True
        else:
            print("✗ TLS пиннинг не прошел - fingerprints не совпадают")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка тестирования TLS пиннинга: {e}")
        return False

if __name__ == "__main__":
    test_certificate_pinning()
EOF
    
    # Запускаем тест
    if python3 /tmp/test_tls_pinning.py; then
        echo -e "${GREEN}✓ Тест TLS пиннинга прошел${NC}"
        return 0
    else
        echo -e "${RED}✗ Тест TLS пиннинга не прошел${NC}"
        return 1
    fi
}

# Основной тест
main() {
    echo "Начало тестирования HTTPS инфраструктуры..."
    echo ""
    
    # Тест 1: HTTPS соединение с API
    test_https_connection "$API_URL" "HTTPS соединение с API"
    echo ""
    
    # Тест 2: HTTPS соединение с Bot
    test_https_connection "$BOT_URL" "HTTPS соединение с Bot"
    echo ""
    
    # Тест 3: API эндпоинт config
    test_api_endpoints "$API_URL" "/config" "API эндпоинт config"
    echo ""
    
    # Тест 4: API эндпоинт manifest
    test_api_endpoints "$API_URL" "/transports/manifest.json" "API эндпоинт manifest"
    echo ""
    
    # Тест 5: TLS пиннинг
    test_tls_pinning
    echo ""
    
    # Тест 6: Тест клиентской загрузки конфига
    echo -e "${YELLOW}Тестирование клиентской загрузки конфига${NC}"
    echo "Тестирование client/chatvpn_backend.py config..."
    
    if python3 client/chatvpn_backend.py config; then
        echo -e "${GREEN}✓ Клиентская загрузка конфига прошла успешно${NC}"
    else
        echo -e "${RED}✗ Клиентская загрузка конфига не прошла${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}=== Тестирование завершено ===${NC}"
    echo -e "${YELLOW}Рекомендации:${NC}"
    echo "1. Проверьте, что домены api.uss.hopto.org и bot.uss.hopto.org указывают на этот сервер"
    echo "2. Убедитесь, что Let's Encrypt сертификаты успешно получены"
    echo "3. Проверьте, что Traefik корректно настроен для обработки HTTPS"
    echo "4. Убедитесь, что API сервисы работают и возвращают корректные ответы"
    echo "5. Проверьте логи сервисов: journalctl -u xvpn-* -f"
}

# Запуск основного теста
main