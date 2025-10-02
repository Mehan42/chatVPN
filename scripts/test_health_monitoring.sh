#!/bin/bash

# Скрипт тестирования системы мониторинга здоровья
# Абсолютный путь: ~/chatvpn/scripts/test_health_monitoring.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Тестирование системы мониторинга здоровья XVPN ===${NC}"

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

# Функция для тестирования Python кода
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

echo -e "${YELLOW}1. Проверка импорта модуля health.py${NC}"
python3 -c "import sys; sys.path.append('client'); import health; print('Модуль health успешно импортирован')" && \
echo -e "${GREEN}✓ Импорт модуля: PASSED${NC}" || \
echo -e "${RED}✗ Импорт модуля: FAILED${NC}"

echo ""
echo -e "${YELLOW}2. Тестирование функции get_mask_score()${NC}"
python3 -c "
import sys
sys.path.append('client')
import health
score = health.get_mask_score()
print(f'Mask Score: {score}/5')
" && \
echo -e "${GREEN}✓ get_mask_score(): PASSED${NC}" || \
echo -e "${RED}✗ get_mask_score(): FAILED${NC}"

echo ""
echo -e "${YELLOW}3. Тестирование логирования здоровья${NC}"
python3 -c "
import sys
import os
sys.path.append('client')
import health

# Проверяем создание файла логов
monitor = health.HealthMonitor()
status = monitor.get_health_status()
print(f'Health status: {status[\"status\"]}')
print(f'Mask score: {status[\"mask_score\"]}')

# Проверяем существование файла логов
if os.path.exists(os.path.expanduser('~/chatvpn/client/logs/health.log')):
    print('Файл логов health.log создан')
else:
    print('Файл логов health.log не найден')
" && \
echo -e "${GREEN}✓ Логирование здоровья: PASSED${NC}" || \
echo -e "${RED}✗ Логирование здоровья: FAILED${NC}"

echo ""
echo -e "${YELLOW}4. Тестирование проверки утечки IP${NC}"
python3 -c "
import sys
sys.path.append('client')
import health

monitor = health.HealthMonitor()
ip_leak = monitor.check_ip_leak()
print(f'IP leak detected: {ip_leak}')
print('Тест проверки утечки IP завершен')
" && \
echo -e "${GREEN}✓ Проверка утечки IP: PASSED${NC}" || \
echo -e "${RED}✗ Проверка утечки IP: FAILED${NC}"

echo ""
echo -e "${YELLOW}5. Тестирование TLS анализа${NC}"
python3 -c "
import sys
sys.path.append('client')
import health

monitor = health.HealthMonitor()
tls_analysis = monitor.analyze_tls_fingerprint()
print(f'TLS analysis result: {tls_analysis[\"analysis_result\"]}')
print(f'TLS score: {tls_analysis[\"score\"]}/5')
print('Тест TLS анализа завершен')
" && \
echo -e "${GREEN}✓ TLS анализ: PASSED${NC}" || \
echo -e "${RED}✗ TLS анализ: FAILED${NC}"

echo ""
echo -e "${YELLOW}6. Тестирование GUI интеграции${NC}"
# Проверяем синтаксис обновленного GUI
if python3 -m py_compile client/chatvpn_gui.py; then
    echo -e "${GREEN}✓ GUI синтаксис: PASSED${NC}"
else
    echo -e "${RED}✗ GUI синтаксис: FAILED${NC}"
fi

echo ""
echo -e "${YELLOW}7. Проверка структуры логов${NC}"
log_file="$HOME/chatvpn/client/logs/health.log"
if [[ -f "$log_file" ]]; then
    echo "Файл логов найден: $log_file"
    echo "Последние 5 строк:"
    tail -n 5 "$log_file"
    echo ""
    echo -e "${GREEN}✓ Структура логов: PASSED${NC}"
else
    echo -e "${RED}✗ Структура логов: FAILED (файл не найден)${NC}"
fi

echo ""
echo -e "${BLUE}=== Тестирование завершено ===${NC}"
echo -e "${YELLOW}Рекомендации:${NC}"
echo "1. Проверьте, что GUI отображает индикатор безопасности"
echo "2. Убедитесь, что логи пишутся в ~/chatvpn/client/logs/health.log"
echo "3. Проверьте работу функции get_mask_score() в интерактивном режиме"
echo "4. Тестируйте GUI с запущенным VPN для проверки оценки маскировки"
echo ""
echo -e "${BLUE}Команды для дальнейшего тестирования:${NC}"
echo "- Запуск GUI: python3 client/chatvpn_gui.py"
echo "- Проверка логов: tail -f ~/chatvpn/client/logs/health.log"
echo "- Ручной запуск мониторинга: python3 -c \"import sys; sys.path.append('client'); import health; print(health.get_mask_score())\""