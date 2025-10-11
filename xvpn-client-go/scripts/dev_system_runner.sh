#!/bin/bash
# Скрипт для запуска всей системы XVPN (клиент + сервер) в режиме разработки

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

# Глобальные переменные
CLIENT_DIR="/home/uss/chatvpn/xvpn-client-go"
SERVER_DIR="/home/uss/chatvpn/server"
MOCK_SERVER_PID=""
CLIENT_PID=""

# Функция для запуска mock-сервера
start_mock_server() {
    log_info "Запуск mock-сервера..."
    
    # Переходим в директорию клиента
    cd "$CLIENT_DIR"
    
    # Запускаем mock-сервер в фоновом режиме
    go run cmd/mock_api_server/main.go > /tmp/xvpn_mock_server.log 2>&1 &
    MOCK_SERVER_PID=$!
    
    # Ждем немного, чтобы сервер успел запуститься
    sleep 3
    
    # Проверяем, запущен ли сервер
    if kill -0 "$MOCK_SERVER_PID" 2>/dev/null; then
        echo "$MOCK_SERVER_PID" > /tmp/xvpn_mock_server.pid
        log_success "Mock-сервер запущен (PID: $MOCK_SERVER_PID)"
        return 0
    else
        log_error "Ошибка запуска mock-сервера"
        return 1
    fi
}

# Функция для остановки mock-сервера
stop_mock_server() {
    log_info "Остановка mock-сервера..."
    
    # Проверяем PID файл
    if [ -f /tmp/xvpn_mock_server.pid ]; then
        MOCK_SERVER_PID=$(cat /tmp/xvpn_mock_server.pid)
    fi
    
    # Останавливаем сервер
    if [ -n "$MOCK_SERVER_PID" ] && kill -0 "$MOCK_SERVER_PID" 2>/dev/null; then
        kill "$MOCK_SERVER_PID"
        log_success "Mock-сервер остановлен (PID: $MOCK_SERVER_PID)"
    else
        log_warning "Mock-сервер не запущен или уже остановлен"
    fi
    
    # Удаляем PID файл
    rm -f /tmp/xvpn_mock_server.pid
    
    # Убиваем все процессы mock-сервера
    pkill -f "mock_api_server" 2>/dev/null || true
}

# Функция для запуска клиента
start_client() {
    log_info "Запуск XVPN клиента..."
    
    # Переходим в директорию клиента
    cd "$CLIENT_DIR"
    
    # Запускаем клиента в фоновом режиме
    go run cmd/xvpn-client/main.go > /tmp/xvpn_client.log 2>&1 &
    CLIENT_PID=$!
    
    # Ждем немного, чтобы клиент успел запуститься
    sleep 3
    
    # Проверяем, запущен ли клиент
    if kill -0 "$CLIENT_PID" 2>/dev/null; then
        echo "$CLIENT_PID" > /tmp/xvpn_client.pid
        log_success "Клиент запущен (PID: $CLIENT_PID)"
        return 0
    else
        log_error "Ошибка запуска клиента"
        return 1
    fi
}

# Функция для остановки клиента
stop_client() {
    log_info "Остановка XVPN клиента..."
    
    # Проверяем PID файл
    if [ -f /tmp/xvpn_client.pid ]; then
        CLIENT_PID=$(cat /tmp/xvpn_client.pid)
    fi
    
    # Останавливаем клиента
    if [ -n "$CLIENT_PID" ] && kill -0 "$CLIENT_PID" 2>/dev/null; then
        kill "$CLIENT_PID"
        log_success "Клиент остановлен (PID: $CLIENT_PID)"
    else
        log_warning "Клиент не запущен или уже остановлен"
    fi
    
    # Удаляем PID файл
    rm -f /tmp/xvpn_client.pid
    
    # Убиваем все процессы клиента
    pkill -f "xvpn-client" 2>/dev/null || true
}

# Функция для проверки состояния системы
check_status() {
    log_info "Проверка состояния системы..."
    
    # Проверяем mock-сервер
    if [ -f /tmp/xvpn_mock_server.pid ]; then
        MOCK_SERVER_PID=$(cat /tmp/xvpn_mock_server.pid)
        if kill -0 "$MOCK_SERVER_PID" 2>/dev/null; then
            log_success "Mock-сервер запущен (PID: $MOCK_SERVER_PID)"
        else
            log_warning "Mock-сервер не запущен (PID: $MOCK_SERVER_PID)"
        fi
    else
        log_warning "PID файла mock-сервера не найдено"
    fi
    
    # Проверяем клиента
    if [ -f /tmp/xvpn_client.pid ]; then
        CLIENT_PID=$(cat /tmp/xvpn_client.pid)
        if kill -0 "$CLIENT_PID" 2>/dev/null; then
            log_success "Клиент запущен (PID: $CLIENT_PID)"
        else
            log_warning "Клиент не запущен (PID: $CLIENT_PID)"
        fi
    else
        log_warning "PID файла клиента не найдено"
    fi
    
    # Проверяем доступность API
    if curl -k -s -f http://localhost:8443/mcp/v1/vpn.health > /dev/null 2>&1; then
        log_success "API сервера доступен"
    else
        log_warning "API сервера недоступен"
    fi
}

# Функция для перезапуска всей системы
restart_system() {
    log_info "Перезапуск всей системы..."
    
    # Останавливаем текущую систему
    stop_system
    
    # Ждем немного
    sleep 3
    
    # Запускаем систему заново
    start_system
}

# Функция для запуска всей системы
start_system() {
    log_info "Запуск всей системы..."
    
    # Запускаем mock-сервер
    if start_mock_server; then
        log_success "Mock-сервер запущен успешно"
    else
        log_error "Ошибка запуска mock-сервера"
        return 1
    fi
    
    # Ждем немного
    sleep 3
    
    # Запускаем клиента
    if start_client; then
        log_success "Клиент запущен успешно"
    else
        log_error "Ошибка запуска клиента"
        stop_mock_server
        return 1
    fi
    
    log_success "Вся система запущена"
}

# Функция для остановки всей системы
stop_system() {
    log_info "Остановка всей системы..."
    
    # Останавливаем клиента
    stop_client
    
    # Останавливаем mock-сервер
    stop_mock_server
    
    log_success "Вся система остановлена"
}

# Функция для просмотра логов
view_logs() {
    local component="${1:-all}"
    
    case "$component" in
        server|mock-server)
            log_info "Просмотр логов mock-сервера..."
            if [ -f /tmp/xvpn_mock_server.log ]; then
                tail -f /tmp/xvpn_mock_server.log
            else
                log_warning "Логи mock-сервера не найдены"
            fi
            ;;
        client)
            log_info "Просмотр логов клиента..."
            if [ -f /tmp/xvpn_client.log ]; then
                tail -f /tmp/xvpn_client.log
            else
                log_warning "Логи клиента не найдены"
            fi
            ;;
        all)
            log_info "Просмотр всех логов..."
            echo "=== Логи mock-сервера ==="
            if [ -f /tmp/xvpn_mock_server.log ]; then
                tail -n 20 /tmp/xvpn_mock_server.log
            else
                echo "Логи не найдены"
            fi
            echo ""
            echo "=== Логи клиента ==="
            if [ -f /tmp/xvpn_client.log ]; then
                tail -n 20 /tmp/xvpn_client.log
            else
                echo "Логи не найдены"
            fi
            ;;
        *)
            log_error "Неизвестный компонент: $component"
            log_info "Использование: $0 logs [server|client|all]"
            ;;
    esac
}

# Основная функция
main() {
    local command="${1:-start}"
    
    log_info "XVPN System Development Runner"
    log_info "=============================="
    
    case "$command" in
        start)
            start_system
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "${2:-all}"
            ;;
        *)
            log_error "Неизвестная команда: $command"
            log_info "Использование: $0 [start|stop|restart|status|logs] [component]"
            log_info ""
            log_info "Примеры:"
            log_info "  $0 start          # Запустить всю систему"
            log_info "  $0 stop           # Остановить всю систему"
            log_info "  $0 restart        # Перезапустить всю систему"
            log_info "  $0 status         # Проверить состояние системы"
            log_info "  $0 logs           # Просмотр всех логов"
            log_info "  $0 logs server    # Просмотр логов сервера"
            log_info "  $0 logs client    # Просмотр логов клиента"
            exit 1
            ;;
    esac
}

# Обработчик сигналов для корректного завершения
trap 'stop_system; exit 0' INT TERM

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi