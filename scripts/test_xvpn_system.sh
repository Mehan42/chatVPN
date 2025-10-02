#!/bin/bash

# Комплексный тестовый скрипт для XVPN системы
# Проверка работы всех компонентов системы

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_DIR="/opt/xvpn"
LOG_FILE="$PROJECT_DIR/test_results.log"
TEST_RESULTS_DIR="$PROJECT_DIR/test_results"

# Функции вывода
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Инициализация логирования
init_logging() {
    print_header "Инициализация тестирования"
    
    # Создание директорий
    mkdir -p "$TEST_RESULTS_DIR"
    
    # Очистка старых логов
    > "$LOG_FILE"
    
    # Запись заголовка
    echo "XVPN System Test Results"
    echo "Timestamp: $(date)"
    echo "================================"
    echo ""
}

# Запись результата в лог
log_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    echo "Test: $test_name" >> "$LOG_FILE"
    echo "Result: $result" >> "$LOG_FILE"
    echo "Details: $details" >> "$LOG_FILE"
    echo "--------------------------------" >> "$LOG_FILE"
}

# Проверка системных требований
check_system_requirements() {
    print_header "Проверка системных требований"
    
    local all_passed=true
    
    # Проверка Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        print_success "Python: $python_version"
        log_result "Python Version" "PASS" "Version: $python_version"
    else
        print_error "Python не установлен"
        log_result "Python Version" "FAIL" "Python not found"
        all_passed=false
    fi
    
    # Проверка Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        print_success "Docker: $docker_version"
        log_result "Docker" "PASS" "Version: $docker_version"
    else
        print_error "Docker не установлен"
        log_result "Docker" "FAIL" "Docker not found"
        all_passed=false
    fi
    
    # Проверка Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
        print_success "Docker Compose: $compose_version"
        log_result "Docker Compose" "PASS" "Version: $compose_version"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        local compose_version=$(docker compose version | cut -d' ' -f3 | tr -d ',')
        print_success "Docker Compose: $compose_version"
        log_result "Docker Compose" "PASS" "Version: $compose_version"
    else
        print_error "Docker Compose не установлен"
        log_result "Docker Compose" "FAIL" "Docker Compose not found"
        all_passed=false
    fi
    
    # Проверка дискового пространства
    local available_space=$(df /opt/xvpn | awk 'NR==2 {print $4}')
    if [ "$available_space" -gt 1000000 ]; then  # > 1GB
        print_success "Дисковое пространство: $((available_space/1024/1024))GB свободно"
        log_result "Disk Space" "PASS" "$((available_space/1024/1024))GB available"
    else
        print_warning "Мало дискового пространства: $((available_space/1024/1024))GB"
        log_result "Disk Space" "WARNING" "$((available_space/1024/1024))GB available"
    fi
    
    # Проверка памяти
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -gt 512 ]; then  # > 512MB
        print_success "Оперативная память: ${available_memory}MB свободно"
        log_result "Memory" "PASS" "$available_memoryMB available"
    else
        print_warning "Мало памяти: ${available_memory}MB"
        log_result "Memory" "WARNING" "$available_memoryMB available"
    fi
    
    if $all_passed; then
        print_success "Все системные требования выполнены"
        return 0
    else
        print_error "Некоторые системные требования не выполнены"
        return 1
    fi
}

# Проверка файловой структуры
check_file_structure() {
    print_header "Проверка файловой структуры"
    
    local all_passed=true
    
    # Проверка основных директорий
    local required_dirs=(
        "$PROJECT_DIR/client"
        "$PROJECT_DIR/server"
        "$PROJECT_DIR/docker"
        "$PROJECT_DIR/config"
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/data"
        "$PROJECT_DIR/systemd"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Директория: $dir"
            log_result "Directory: $dir" "PASS" "Directory exists"
        else
            print_error "Директория не найдена: $dir"
            log_result "Directory: $dir" "FAIL" "Directory not found"
            all_passed=false
        fi
    done
    
    # Проверка основных файлов
    local required_files=(
        "$PROJECT_DIR/client/chatvpn_backend.py"
        "$PROJECT_DIR/server/api/app.py"
        "$PROJECT_DIR/docker-compose.yml"
        "$PROJECT_DIR/config/api.json"
        "$PROJECT_DIR/config/agent.json"
        "$PROJECT_DIR/config/client.json"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Файл: $file"
            log_result "File: $file" "PASS" "File exists"
        else
            print_error "Файл не найден: $file"
            log_result "File: $file" "FAIL" "File not found"
            all_passed=false
        fi
    done
    
    if $all_passed; then
        print_success "Файловая структура корректна"
        return 0
    else
        print_error "Проблемы с файловой структурой"
        return 1
    fi
}

# Проверка systemd сервисов
check_systemd_services() {
    print_header "Проверка systemd сервисов"
    
    local services=(
        "xvpn-docker"
        "xvpn-redis"
        "xvpn-traefik"
        "xvpn-api"
        "xvpn-agent"
        "xvpn-bot"
        "xvpn-worker"
        "xvpn-client"
    )
    
    local all_running=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service.service"; then
            print_success "Сервис: $service.service запущен"
            log_result "Service: $service" "PASS" "Service is running"
        else
            print_error "Сервис не запущен: $service.service"
            log_result "Service: $service" "FAIL" "Service is not running"
            all_running=false
        fi
    done
    
    if $all_running; then
        print_success "Все сервисы запущены"
        return 0
    else
        print_error "Некоторые сервисы не запущены"
        return 1
    fi
}

# Проверка Docker контейнеров
check_docker_containers() {
    print_header "Проверка Docker контейнеров"
    
    # Проверка, что Docker запущен
    if ! systemctl is-active --quiet docker.service; then
        print_error "Docker не запущен"
        log_result "Docker Service" "FAIL" "Docker is not running"
        return 1
    fi
    
    # Проверка контейнеров
    local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | tail -n +2)
    
    if [ -z "$containers" ]; then
        print_warning "Нет запущенных контейнеров"
        log_result "Docker Containers" "WARNING" "No containers running"
        return 0
    fi
    
    echo "$containers" | while read -r container status; do
        if echo "$status" | grep -q "Up"; then
            print_success "Контейнер: $container - $status"
            log_result "Container: $container" "PASS" "Status: $status"
        else
            print_error "Контейнер: $container - $status"
            log_result "Container: $container" "FAIL" "Status: $status"
        fi
    done
}

# Проверка API эндпоинтов
check_api_endpoints() {
    print_header "Проверка API эндпоинтов"
    
    local endpoints=(
        "https://api.uss.hopto.org/health"
        "https://api.uss.hopto.org/api/v1/status"
        "https://api.uss.hopto.org/agent/health"
    )
    
    local all_passed=true
    
    for endpoint in "${endpoints[@]}"; do
        if curl -k -s --max-time 10 "$endpoint" > /dev/null; then
            local response=$(curl -k -s --max-time 10 "$endpoint")
            print_success "API: $endpoint"
            log_result "API: $endpoint" "PASS" "Response: $response"
        else
            print_error "API недоступен: $endpoint"
            log_result "API: $endpoint" "FAIL" "Connection failed"
            all_passed=false
        fi
    done
    
    if $all_passed; then
        print_success "Все API эндпоинты доступны"
        return 0
    else
        print_error "Некоторые API эндпоинты недоступны"
        return 1
    fi
}

# Проверка безопасности
check_security() {
    print_header "Проверка безопасности"
    
    local all_passed=true
    
    # Проверка SSL сертификатов
    if openssl s_client -connect api.uss.hopto.org:443 -servername api.uss.hopto.org < /dev/null > /dev/null 2>&1; then
        print_success "SSL сертификат действителен"
        log_result "SSL Certificate" "PASS" "Certificate is valid"
    else
        print_error "SSL сертификат недействителен"
        log_result "SSL Certificate" "FAIL" "Certificate is invalid"
        all_passed=false
    fi
    
    # Проверка брандмауэра
    if command -v ufw &> /dev/null; then
        local ufw_status=$(sudo ufw status | grep -o "Status: [a-z]*")
        if echo "$ufw_status" | grep -q "active"; then
            print_success "Брандмауэр активен: $ufw_status"
            log_result "Firewall" "PASS" "UFW is active"
        else
            print_warning "Брандмауэр не активен: $ufw_status"
            log_result "Firewall" "WARNING" "UFW is not active"
        fi
    fi
    
    # Проверка прав доступа
    local sensitive_files=(
        "/opt/xvpn/config/api.json"
        "/opt/xvpn/config/agent.json"
        "/opt/xvpn/config/client.json"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local permissions=$(ls -la "$file" | awk '{print $1}')
            if echo "$permissions" | grep -q "rw-------"; then
                print_success "Права доступа корректны: $file"
                log_result "File Permissions: $file" "PASS" "Permissions: $permissions"
            else
                print_warning "Некорректные права доступа: $file"
                log_result "File Permissions: $file" "WARNING" "Permissions: $permissions"
            fi
        fi
    done
    
    if $all_passed; then
        print_success "Проверка безопасности пройдена"
        return 0
    else
        print_warning "Обнаружены проблемы безопасности"
        return 1
    fi
}

# Проверка производительности
check_performance() {
    print_header "Проверка производительности"
    
    # Проверка времени отклика API
    local start_time=$(date +%s%N)
    curl -k -s --max-time 10 "https://api.uss.hopto.org/health" > /dev/null
    local end_time=$(date +%s%N)
    local response_time=$((($end_time - $start_time) / 1000000))
    
    if [ "$response_time" -lt 1000 ]; then  # < 1 second
        print_success "Время отклика API: ${response_time}ms"
        log_result "API Response Time" "PASS" "${response_time}ms"
    else
        print_warning "Время отклика API: ${response_time}ms"
        log_result "API Response Time" "WARNING" "${response_time}ms"
    fi
    
    # Проверка использования памяти
    local memory_usage=$(ps aux --sort=-%mem | head -2 | tail -1 | awk '{print $4}')
    if [ "${memory_usage%\%}" -lt 80 ]; then
        print_success "Использование памяти: ${memory_usage}"
        log_result "Memory Usage" "PASS" "${memory_usage}"
    else
        print_warning "Высокое использование памяти: ${memory_usage}"
        log_result "Memory Usage" "WARNING" "${memory_usage}"
    fi
    
    # Проверка использования CPU
    local cpu_usage=$(ps aux --sort=-%cpu | head -2 | tail -1 | awk '{print $3}')
    if [ "${cpu_usage%\%}" -lt 80 ]; then
        print_success "Использование CPU: ${cpu_usage}"
        log_result "CPU Usage" "PASS" "${cpu_usage}"
    else
        print_warning "Высокое использование CPU: ${cpu_usage}"
        log_result "CPU Usage" "WARNING" "${cpu_usage}"
    fi
}

# Генерация отчета
generate_report() {
    print_header "Генерация отчета"
    
    local report_file="$TEST_RESULTS_DIR/system_report_$(date +%Y%m%d_%H%M%S).html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XVPN System Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        .log { background-color: #f9f9f9; padding: 10px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>XVPN System Test Report</h1>
        <p>Generated: $(date)</p>
        <p>System: $(uname -a)</p>
    </div>
    
    <div class="section">
        <h2>Test Results</h2>
        <pre class="log">$(cat "$LOG_FILE")</pre>
    </div>
</body>
</html>
EOF
    
    print_success "Отчет сгенерирован: $report_file"
    log_result "Report Generation" "PASS" "HTML report created"
}

# Основная функция
main() {
    print_header "Запуск комплексного тестирования XVPN системы"
    
    # Инициализация
    init_logging
    
    # Список тестов
    local tests=(
        "check_system_requirements"
        "check_file_structure"
        "check_systemd_services"
        "check_docker_containers"
        "check_api_endpoints"
        "check_security"
        "check_performance"
    )
    
    # Выполнение тестов
    local tests_passed=0
    local tests_total=${#tests[@]}
    
    for test in "${tests[@]}"; do
        print_info "Выполнение теста: $test"
        
        if $test; then
            ((tests_passed++))
        fi
        
        echo ""
    done
    
    # Генерация отчета
    generate_report
    
    # Итоговый результат
    print_header "Итоги тестирования"
    echo "Всего тестов: $tests_total"
    echo "Пройдено: $tests_passed"
    echo "Провалено: $((tests_total - tests_passed))"
    
    if [ "$tests_passed" -eq "$tests_total" ]; then
        print_success "✅ Все тесты пройдены успешно!"
        log_result "Overall Result" "PASS" "All $tests_total tests passed"
    else
        print_error "❌ Некоторые тесты провалены"
        log_result "Overall Result" "FAIL" "$((tests_total - tests_passed)) tests failed"
        exit 1
    fi
    
    echo ""
    print_info "Полный лог тестов: $LOG_FILE"
    print_info "HTML отчет: $TEST_RESULTS_DIR/system_report_*.html"
}

# Обработка аргументов
case "${1:-}" in
    "--help"|-h)
        echo "Использование: $0 [опции]"
        echo ""
        echo "Опции:"
        echo "  --help, -h     Показать эту справку"
        echo "  --version, -v  Показать версию"
        echo ""
        echo "Примеры:"
        echo "  sudo $0         # Запуск всех тестов"
        echo "  sudo $0 --help  # Показать справку"
        exit 0
        ;;
    "--version"|-v)
        echo "XVPN System Test Script v1.0.0"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Неизвестный аргумент: $1"
        echo "Используйте --help для справки"
        exit 1
        ;;
esac