#!/bin/bash
# Скрипт для запуска всех тестов интеграции XVPN клиента

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для запуска теста
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    log_info "Запуск теста: $test_name"
    
    # Запускаем тест
    if eval "$test_cmd"; then
        log_success "Тест $test_name пройден"
        return 0
    else
        log_error "Тест $test_name не пройден"
        return 1
    fi
}

# Основная функция
main() {
    log_info "Начало тестирования интеграции XVPN клиента"
    
    # Получаем путь к проекту
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    
    log_info "Каталог проекта: $PROJECT_DIR"
    
    # Переходим в каталог проекта
    cd "$PROJECT_DIR"
    
    # Запускаем все тесты
    local test_count=0
    local passed_count=0
    local failed_count=0
    
    # Тест 1: Базовое тестирование
    test_count=$((test_count + 1))
    if run_test "Базовое тестирование" "go run cmd/test/main.go"; then
        passed_count=$((passed_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
    
    # Тест 2: Расширенное тестирование
    test_count=$((test_count + 1))
    if run_test "Расширенное тестирование" "go run cmd/extended_test/main.go"; then
        passed_count=$((passed_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
    
    # Тест 3: Тестирование компонентов
    test_count=$((test_count + 1))
    if run_test "Тестирование компонентов" "go run cmd/component_test/main.go"; then
        passed_count=$((passed_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
    
    # Тест 4: API интеграционное тестирование
    test_count=$((test_count + 1))
    if run_test "API интеграционное тестирование" "go run cmd/api_integration_test/main.go"; then
        passed_count=$((passed_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
    
    # Выводим сводку
    echo
    log_info "Сводка тестирования:"
    log_info "  Всего тестов: $test_count"
    log_success "  Пройдено: $passed_count"
    log_error "  Не пройдено: $failed_count"
    
    if [ $failed_count -eq 0 ]; then
        log_success "Все тесты пройдены успешно!"
        exit 0
    else
        log_error "Некоторые тесты не пройдены"
        exit 1
    fi
}

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi