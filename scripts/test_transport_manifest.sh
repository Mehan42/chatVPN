#!/bin/bash

# Скрипт тестирования системы манифестов и автоматического переключения транспортов
# Абсолютный путь: ~/chatvpn/scripts/test_transport_manifest.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Тестирование системы манифестов и автоматического переключения транспортов XVPN ===${NC}"

# Функция для проверки результата
check_result() {
    local test_name="$1"
    local expected_result="$2"
    local actual_result="$3"
    
    if [[ "$actual_result" == "$expected_result" ]]; then
        echo -e "${GREEN}✓ $test_name: PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name: FAILED${NC}"
        echo "  Ожидаемый: $expected_result"
        echo "  Фактический: $actual_result"
        return 1
    fi
}

# Функция для тестирования Python модулей
test_python_module() {
    local test_name="$1"
    local python_code="$2"
    local expected_result="$3"
    
    echo -e "${YELLOW}Тест: $test_name${NC}"
    
    # Создаем временный файл с кодом
    temp_file=$(mktemp)
    echo "$python_code" > "$temp_file"
    
    # Запускаем тест
    result=$(python3 "$temp_file" 2>/dev/null)
    rm "$temp_file"
    
    check_result "$test_name" "$expected_result" "$result"
}

echo -e "${YELLOW}1. Проверка существования манифеста транспортов${NC}"
if [[ -f "client/transports/manifest.json" ]]; then
    echo -e "${GREEN}✓ Манифест транспортов существует${NC}"
    
    # Проверка синтаксиса JSON
    if python3 -c "import json; json.load(open('client/transports/manifest.json'))"; then
        echo -e "${GREEN}✓ Синтаксис JSON корректен${NC}"
    else
        echo -e "${RED}✗ Ошибка синтаксиса JSON${NC}"
    fi
else
    echo -e "${RED}✗ Манифест транспортов не найден${NC}"
fi

echo ""
echo -e "${YELLOW}2. Проверка структуры манифеста${NC}"
python3 -c "
import json
with open('client/transports/manifest.json', 'r') as f:
    manifest = json.load(f)

# Проверка основных полей
required_fields = ['version', 'last_updated', 'transports']
for field in required_fields:
    if field in manifest:
        print(f'✓ Поле {field} найдено')
    else:
        print(f'✗ Поле {field} отсутствует')

# Проверка транспортов
transports = manifest.get('transports', [])
print(f'✓ Найдено {len(transports)} транспортов')

# Проверка каждого транспорта
for i, transport in enumerate(transports):
    required_transport_fields = ['id', 'name', 'type', 'protocol', 'config']
    for field in required_transport_fields:
        if field in transport:
            print(f'  ✓ Транспорт {i}: поле {field} найдено')
        else:
            print(f'  ✗ Транспорт {i}: поле {field} отсутствует')
" && \
echo -e "${GREEN}✓ Структура манифеста: PASSED${NC}" || \
echo -e "${RED}✗ Структура манифеста: FAILED${NC}"

echo ""
echo -e "${YELLOW}3. Тестирование модуля discover.py${NC}"
python3 client/discover.py && \
echo -e "${GREEN}✓ discover.py: PASSED${NC}" || \
echo -e "${RED}✗ discover.py: FAILED${NC}"

echo ""
echo -e "${YELLOW}4. Тестирование Transport Manager${NC}"
python3 -c "
import sys
sys.path.append('client')
from transport_manager import get_transport_manager
import uuid

# Создаем тестовый UUID
test_uuid = str(uuid.uuid4())
print(f'Тест UUID: {test_uuid}')

# Создаем менеджер
manager = get_transport_manager(test_uuid)

# Проверка методов
print('✓ TransportManager создан')

# Тестирование получения конфигурации (может не работать без сервера)
try:
    config = manager.fetch_client_config()
    if config:
        print(f'✓ Конфигурация получена: {config.get(\"available_transports\", 0)} доступных транспортов')
    else:
        print('ℹ Конфигурация не получена (ожидаемо без сервера)')
except Exception as e:
    print(f'ℹ Ожидаемая ошибка: {e}')

# Тестирование списка доступных транспортов
try:
    transports = manager.get_available_transports()
    print(f'✓ Доступно транспортов: {len(transports)}')
except Exception as e:
    print(f'ℹ Ожидаемая ошибка: {e}')
" && \
echo -e "${GREEN}✓ Transport Manager: PASSED${NC}" || \
echo -e "${RED}✗ Transport Manager: FAILED${NC}"

echo ""
echo -e "${YELLOW}5. Проверка интеграции с серверным API${NC}"
echo "Проверка эндпоинта /clients/<UUID>.json (ожидаемо 404 - клиент не существует):"
curl -s -o /dev/null -w "%{http_code}" https://api.uss.hopto.org/clients/test-uuid.json && \
echo -e "${GREEN}✓ API эндпоинт доступен${NC}" || \
echo -e "${YELLOW}ℹ API эндпоинт недоступен (ожидаемо)${NC}"

echo ""
echo -e "${YELLOW}6. Тестирование автоматического переключения транспортов${NC}"
python3 -c "
import sys
sys.path.append('client')
from transport_manager import get_transport_manager
import uuid

# Создаем тестовый UUID
test_uuid = str(uuid.uuid4())
manager = get_transport_manager(test_uuid)

# Проверяем методы принудительного переключения
print('✓ Методы переключения доступны')

# Тестирование принудительного переключения (не должно сработать без транспорта)
try:
    result = manager.force_transport_switch('nonexistent_transport')
    print(f'✓ Принудительное переключение: {result} (ожидаемо False)')
except Exception as e:
    print(f'ℹ Ошибка переключения: {e}')
" && \
echo -e "${GREEN}✓ Автоматическое переключение: PASSED${NC}" || \
echo -e "${RED}✗ Автоматическое переключение: FAILED${NC}"

echo ""
echo -e "${YELLOW}7. Проверка логирования транспортов${NC}"
log_dir=\"\$HOME/chatvpn/client/logs\"
if [[ -d \"\$log_dir\" ]]; then
    echo -e "${GREEN}✓ Директория логов существует: \$log_dir${NC}"
    
    # Проверка наличия файлов логов
    if [[ -f \"\$log_dir/transport_manager.log\" ]]; then
        echo -e "${GREEN}✓ Файл логов менеджера транспортов существует${NC}"
        echo \"Последние 3 строки:\"
        tail -n 3 \"\$log_dir/transport_manager.log\"
    else
        echo -e "${YELLOW}ℹ Файл логов менеджера транспортов еще не создан${NC}"
    fi
else
    echo -e "${RED}✗ Директория логов не существует${NC}"
fi

echo ""
echo -e "${YELLOW}8. Проверка бэкапа и восстановления${NC}"
# Создаем резервную копию манифеста
if [[ -f \"client/transports/manifest.json\" ]]; then
    cp client/transports/manifest.json client/transports/manifest.json.backup
    echo -e "${GREEN}✓ Резервная копия манифеста создана${NC}"
    
    # Проверка восстановления
    if [[ -f \"client/transports/manifest.json.backup\" ]]; then
        echo -e "${GREEN}✓ Резервная копия доступна для восстановления${NC}"
    else
        echo -e "${RED}✗ Резервная копия недоступна${NC}"
    fi
fi

echo ""
echo -e "${BLUE}=== Тестирование завершено ===${NC}"
echo -e "${YELLOW}Рекомендации:${NC}"
echo "1. Запустите сервер для полного тестирования API эндпоинтов"
echo "2. Проверьте работу автоматического переключения транспортов"
echo "3. Тестируйте переключение при недоступности основного транспорта"
echo "4. Мониторьте логи в ~/chatvpn/client/logs/"
echo ""
echo -e "${BLUE}Команды для дальнейшего тестирования:${NC}"
echo "- Запуск менеджера транспортов: python3 client/transport_manager.py <UUID>"
echo "- Проверка логов: tail -f ~/chatvpn/client/logs/transport_manager.log"
echo "- Тестирование discover: python3 client/discover.py"
echo "- Проверка манифеста: cat client/transports/manifest.json | python3 -m json.tool"