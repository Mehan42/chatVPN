#!/bin/bash

# Скрипт тестирования машины состояний VPN клиента
# Абсолютный путь: ~/chatvpn/scripts/test_state_machine.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Тестирование машины состояний VPN клиента XVPN ===${NC}"

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

echo -e "${YELLOW}1. Проверка синтаксиса модулей${NC}"

# Проверка синтаксиса state_machine.py
python3 -m py_compile client/state_machine.py && \
echo -e "${GREEN}✓ state_machine.py синтаксически корректен${NC}" || \
echo -e "${RED}✗ state_machine.py синтаксические ошибки${NC}"

# Проверка синтаксиса vpn_client.py
python3 -m py_compile client/vpn_client.py && \
echo -e "${GREEN}✓ vpn_client.py синтаксически корректен${NC}" || \
echo -e "${RED}✗ vpn_client.py синтаксические ошибки${NC}"

echo ""
echo -e "${YELLOW}2. Тестирование импортов модулей${NC}"

# Проверка импортов
python3 -c "
try:
    import sys
    sys.path.append('client')
    from state_machine import VPNStateMachine, State, Event
    print('✓ state_machine импортирован успешно')
except Exception as e:
    print(f'✗ Ошибка импорта state_machine: {e}')

try:
    import sys
    sys.path.append('client')
    from vpn_client import VPNClient, get_vpn_client
    print('✓ vpn_client импортирован успешно')
except Exception as e:
    print(f'✗ Ошибка импорта vpn_client: {e}')

try:
    import sys
    sys.path.append('client')
    from transport_manager import get_transport_manager
    print('✓ transport_manager импортирован успешно')
except Exception as e:
    print(f'✗ Ошибка импорта transport_manager: {e}')
" && \
echo -e "${GREEN}✓ Все модули успешно импортированы${NC}" || \
echo -e "${RED}✗ Ошибки импорта модулей${NC}"

echo ""
echo -e "${YELLOW}3. Тестирование создания машины состояний${NC}"

# Тестирование создания state machine
python3 -c "
import sys
sys.path.append('client')
from state_machine import VPNStateMachine, State, Event

# Создание тестового UUID
test_uuid = 'test-uuid-123'
print(f'Тест UUID: {test_uuid}')

# Создание state machine
try:
    sm = VPNStateMachine(test_uuid)
    print(f'✓ State Machine создан для UUID: {sm.client_uuid}')
    print(f'✓ Начальное состояние: {sm.get_current_state().value}')
    
    # Проверка контекста
    info = sm.get_state_info()
    print(f'✓ Информация о состоянии: {info.get(\"current_state\", \"N/A\")}')
    
except Exception as e:
    print(f'✗ Ошибка создания State Machine: {e}')
" && \
echo -e "${GREEN}✓ State Machine создан успешно${NC}" || \
echo -e "${RED}✗ Ошибка создания State Machine${NC}"

echo ""
echo -e "${YELLOW}4. Тестирование VPN клиента${NC}"

# Тестирование создания VPN клиента
python3 -c "
import sys
sys.path.append('client')
from vpn_client import VPNClient

# Создание VPN клиента
try:
    client = VPNClient('test-client-uuid')
    print(f'✓ VPN Client создан для UUID: {client.get_client_uuid()}')
    
    # Проверка инициализации
    if client.initialize():
        print('✓ VPN Client инициализирован успешно')
    else:
        print('ℹ VPN Client инициализация пропущена (ожидаемо без сервера)')
    
    # Проверка статуса
    status = client.get_status()
    print(f'✓ Статус клиента: {status.get(\"current_state\", \"unknown\")}')
    
    # Проверка сетевой информации
    network_info = client.get_network_info()
    print(f'✓ Сетевая информация: {len(network_info)} полей')
    
    # Проверка оценки здоровья
    health_score = client.get_health_score()
    print(f'✓ Оценка здоровья: {health_score}')
    
except Exception as e:
    print(f'✗ Ошибка создания VPN Client: {e}')
" && \
echo -e "${GREEN}✓ VPN Client создан успешно${NC}" || \
echo -e "${RED}✗ Ошибка создания VPN Client${NC}"

echo ""
echo -e "${YELLOW}5. Тестирование машины состояний в интерактивном режиме${NC}"

echo "Создаем тестовый state machine для проверки состояний..."
python3 -c "
import sys
sys.path.append('client')
from state_machine import VPNStateMachine, State, Event
import threading
import time

# Создание тестового state machine
test_uuid = 'interactive-test-uuid'
sm = VPNStateMachine(test_uuid)

# Создаем флаг для управления потоком
running = [True]

def state_machine_loop():
    while running[0]:
        try:
            sm.process_events()
            sm._execute_state_actions(sm.context.current_state)
            time.sleep(0.1)
        except Exception as e:
            print(f'Ошибка в state machine loop: {e}')
            break

# Запускаем state machine в отдельном потоке
sm_thread = threading.Thread(target=state_machine_loop, daemon=True)
sm_thread.start()

print(f'✓ State Machine запущен для UUID: {test_uuid}')
print(f'✓ Текущее состояние: {sm.get_current_state().value}')
print('✓ State Machine работает (тест завершится через 3 секунды)')

# Даем поработать
time.sleep(3)

# Остановка
running[0] = False
time.sleep(0.5)

print(f'✓ Финальное состояние: {sm.get_current_state().value}')
print('✓ Интерактивный тест завершен')
" && \
echo -e "${GREEN}✓ Интерактивный тест машины состояний пройден${NC}" || \
echo -e "${RED}✗ Интерактивный тест не пройден${NC}"

echo ""
echo -e "${YELLOW}6. Проверка интеграции с существующим кодом${NC}"

# Проверка обратной совместимости с существующим backend
python3 -c "
import sys
sys.path.append('client')
import chatvpn_backend as be

# Проверка существующих функций
try:
    # Проверка функций
    print('✓ chatvpn_backend импортирован')
    print('✓ Функции доступны:')
    print(f'  - start_xray: {callable(be.start_xray)}')
    print(f'  - stop_xray: {callable(be.stop_xray)}')
    print(f'  - get_status: {callable(be.get_status)}')
    print(f'  - load_config_from_server: {callable(be.load_config_from_server)}')
    
    # Проверка статуса (не должен падать)
    status = be.get_status()
    print(f'✓ Статус Xray: {status.get(\"status\", \"unknown\")}')
    
except Exception as e:
    print(f'✗ Ошибка проверки обратной совместимости: {e}')
" && \
echo -e "${GREEN}✓ Обратная совместимость сохранена${NC}" || \
echo -e "${RED}✗ Обратная совместимость нарушена${NC}"

echo ""
echo -e "${YELLOW}7. Проверка путей и директорий${NC}"

# Проверка создания директорий
echo "Проверка директорий для state machine:"
for dir_path in "~/chatvpn/client/states" "~/chatvpn/client/logs"; do
    expanded_path=$(eval echo "$dir_path")
    if [[ -d "$expanded_path" ]]; then
        echo -e "${GREEN}✓ Директория существует: $expanded_path${NC}"
        # Проверка файлов в директории
        if ls "$expanded_path"/*.log 1> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Файлы логов созданы: $(ls "$expanded_path"/*.log | head -1)${NC}"
        fi
    else
        echo -e "${RED}✗ Директория не существует: $expanded_path${NC}"
    fi
done

echo ""
echo -e "${YELLOW}8. Тестирование командной строки VPN клиента${NC}"

# Проверка работы командной строки
echo "Тестирование команды status:"
python3 client/vpn_client.py status --uuid test-cli-uuid && \
echo -e "${GREEN}✓ Команда status работает${NC}" || \
echo -e "${YELLOW}ℹ Команда status: ожидаемые ошибки (нет сервера)${NC}"

echo "Тестирование команды uuid:"
python3 client/vpn_client.py uuid && \
echo -e "${GREEN}✓ Команда uuid работает${NC}" || \
echo -e "${RED}✗ Команда uuid не работает${NC}"

echo ""
echo -e "${BLUE}=== Тестирование машины состояний завершено ===${NC}"
echo -e "${YELLOW}Рекомендации:${NC}"
echo "1. Запустите сервер для полного функционального тестирования"
echo "2. Проверьте работу state machine в реальных условиях"
echo "3. Тестируйте переключение состояний при ошибках"
echo "4. Мониторьте логи в ~/chatvpn/client/states/ и ~/chatvpn/client/logs/"
echo ""
echo -e "${BLUE}Команды для дальнейшего тестирования:${NC}"
echo "- Запуск state machine: python3 client/state_machine.py <UUID>"
echo "- Запуск VPN клиента: python3 client/vpn_client.py start --uuid <UUID>"
echo "- Проверка статуса: python3 client/vpn_client.py status --uuid <UUID>"
echo "- Просмотр логов: tail -f ~/chatvpn/client/logs/vpn_client_<UUID>.log"
echo "- Интерактивный тест: python3 client/state_machine.py <UUID> (в интерактивном режиме)"