#!/bin/bash
# Скрипт для запуска XVPN API сервера в режиме разработки

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

# Функция для проверки зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не установлен"
        exit 1
    fi
    
    # Проверяем pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 не установлен"
        exit 1
    fi
    
    # Проверяем виртуальное окружение
    if [ ! -d "/home/uss/chatvpn/venv" ]; then
        log_warning "Виртуальное окружение не найдено, создаем..."
        python3 -m venv /home/uss/chatvpn/venv
    fi
    
    # Активируем виртуальное окружение
    source /home/uss/chatvpn/venv/bin/activate
    
    # Устанавливаем зависимости
    pip3 install flask flask-cors psutil requests
    
    log_success "Все зависимости установлены"
}

# Функция для запуска сервера
start_server() {
    local port="${1:-8443}"
    local debug="${2:-true}"
    
    log_info "Запуск XVPN API сервера на порту $port..."
    
    # Активируем виртуальное окружение
    source /home/uss/chatvpn/venv/bin/activate
    
    # Переходим в директорию сервера
    cd /home/uss/chatvpn/server/api
    
    # Устанавливаем переменные окружения
    export FLASK_ENV="development"
    export XVPN_API_PORT="$port"
    export DISABLE_AUTH="true"
    export DEBUG="$debug"
    
    # Запускаем сервер
    log_info "Запуск сервера с параметрами:"
    log_info "  FLASK_ENV: $FLASK_ENV"
    log_info "  XVPN_API_PORT: $XVPN_API_PORT"
    log_info "  DISABLE_AUTH: $DISABLE_AUTH"
    log_info "  DEBUG: $DEBUG"
    
    python3 app.py
}

# Функция для остановки сервера
stop_server() {
    log_info "Остановка XVPN API сервера..."
    
    # Находим и останавливаем процесс сервера
    local pids=$(pgrep -f "python3.*app\.py")
    
    if [ -n "$pids" ]; then
        log_info "Найдены процессы сервера: $pids"
        kill $pids
        log_success "Сервер остановлен"
    else
        log_warning "Процессы сервера не найдены"
    fi
}

# Функция для перезапуска сервера
restart_server() {
    local port="${1:-8443}"
    local debug="${2:-true}"
    
    log_info "Перезапуск XVPN API сервера..."
    
    # Останавливаем сервер
    stop_server
    
    # Ждем немного
    sleep 2
    
    # Запускаем сервер
    start_server "$port" "$debug"
}

# Функция для проверки состояния сервера
check_server_status() {
    log_info "Проверка состояния XVPN API сервера..."
    
    # Проверяем, запущен ли сервер
    local pids=$(pgrep -f "python3.*app\.py")
    
    if [ -n "$pids" ]; then
        log_success "Сервер запущен (PID: $pids)"
        
        # Проверяем доступность через HTTP
        if curl -k -s -f http://localhost:${1:-8443}/mcp/v1/vpn.health > /dev/null; then
            log_success "Сервер доступен по HTTP"
        else
            log_warning "Сервер запущен, но недоступен по HTTP"
        fi
    else
        log_warning "Сервер не запущен"
    fi
}

# Основная функция
main() {
    local command="${1:-start}"
    local port="${2:-8443}"
    local debug="${3:-true}"
    
    log_info "XVPN API Server Development Runner"
    log_info "=================================="
    
    case "$command" in
        start)
            # Проверяем зависимости
            check_dependencies
            
            # Запускаем сервер
            start_server "$port" "$debug"
            ;;
        stop)
            stop_server
            ;;
        restart)
            restart_server "$port" "$debug"
            ;;
        status)
            check_server_status "$port"
            ;;
        check-deps)
            check_dependencies
            ;;
        *)
            log_error "Неизвестная команда: $command"
            log_info "Использование: $0 [start|stop|restart|status|check-deps] [port] [debug]"
            log_info ""
            log_info "Примеры:"
            log_info "  $0 start          # Запустить сервер на порту 8443"
            log_info "  $0 start 8080     # Запустить сервер на порту 8080"
            log_info "  $0 stop           # Остановить сервер"
            log_info "  $0 restart        # Перезапустить сервер"
            log_info "  $0 status         # Проверить состояние сервера"
            log_info "  $0 check-deps     # Проверить зависимости"
            exit 1
            ;;
    esac
}

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi