#!/bin/bash

# Улучшенный скрипт для управления XVPN systemd сервисами
# Поддержка всех сервисов с правильными зависимостями и мониторингом

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/../systemd"
SERVICE_FILES=(
    "xvpn-client.service"
    "xvpn-api.service"
    "xvpn-agent.service"
    "xvpn-bot.service"
    "xvpn-redis.service"
    "xvpn-traefik.service"
)

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

# Проверка прав доступа
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт требует прав root для управления systemd сервисами"
        echo "Используйте: sudo $0"
        exit 1
    fi
}

# Проверка наличия systemd
check_systemd() {
    if ! systemctl --version &> /dev/null; then
        print_error "systemd не найден в системе"
        exit 1
    fi
}

# Установка сервисов
install_services() {
    print_header "Установка XVPN сервисов"
    
    local all_success=true
    
    # Копирование файлов в systemd
    for service_file in "${SERVICE_FILES[@]}"; do
        local source_file="$SYSTEMD_DIR/$service_file"
        local target_file="/etc/systemd/system/$service_file"
        
        if [[ -f "$source_file" ]]; then
            print_info "Установка $service_file..."
            
            if cp "$source_file" "$target_file"; then
                print_success "$service_file успешно установлен"
                
                # Перезагрузка systemd
                systemctl daemon-reload
                
                # Включение сервиса
                systemctl enable "$service_file"
                print_success "$service_file включен для автозапуска"
            else
                print_error "Не удалось установить $service_file"
                all_success=false
            fi
        else
            print_warning "Файл сервиса не найден: $source_file"
        fi
    done
    
    if $all_success; then
        print_success "Все сервисы успешно установлены"
        return 0
    else
        print_error "Некоторые сервисы не были установлены"
        return 1
    fi
}

# Удаление сервисов
remove_services() {
    print_header "Удаление XVPN сервисов"
    
    local all_success=true
    
    for service_file in "${SERVICE_FILES[@]}"; do
        if systemctl is-enabled --quiet "$service_file"; then
            print_info "Отключение $service_file..."
            systemctl disable "$service_file"
        fi
        
        if systemctl is-active --quiet "$service_file"; then
            print_info "Остановка $service_file..."
            systemctl stop "$service_file"
        fi
        
        local target_file="/etc/systemd/system/$service_file"
        if [[ -f "$target_file" ]]; then
            print_info "Удаление $service_file..."
            rm -f "$target_file"
            systemctl daemon-reload
        fi
    done
    
    if $all_success; then
        print_success "Все сервисы успешно удалены"
        return 0
    else
        print_error "Некоторые сервисы не были удалены"
        return 1
    fi
}

# Запуск сервисов
start_services() {
    print_header "Запуск XVPN сервисов"
    
    # Проверка зависимостей
    check_services_ready
    
    local services=(
        "xvpn-redis.service"
        "xvpn-traefik.service"
        "xvpn-api.service"
        "xvpn-agent.service"
        "xvpn-bot.service"
        "xvpn-client.service"
    )
    
    local all_success=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            print_info "$service уже запущен"
        else
            print_info "Запуск $service..."
            if systemctl start "$service"; then
                print_success "$service успешно запущен"
            else
                print_error "Не удалось запустить $service"
                all_success=false
            fi
        fi
    done
    
    if $all_success; then
        print_success "Все сервисы успешно запущены"
        return 0
    else
        print_error "Некоторые сервисы не были запущены"
        return 1
    fi
}

# Остановка сервисов
stop_services() {
    print_header "Остановка XVPN сервисов"
    
    local services=(
        "xvpn-client.service"
        "xvpn-bot.service"
        "xvpn-agent.service"
        "xvpn-api.service"
        "xvpn-traefik.service"
        "xvpn-redis.service"
    )
    
    local all_success=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            print_info "Остановка $service..."
            if systemctl stop "$service"; then
                print_success "$service успешно остановлен"
            else
                print_error "Не удалось остановить $service"
                all_success=false
            fi
        else
            print_info "$service уже остановлен"
        fi
    done
    
    if $all_success; then
        print_success "Все сервисы успешно остановлены"
        return 0
    else
        print_error "Некоторые сервисы не были остановлены"
        return 1
    fi
}

# Перезапуск сервисов
restart_services() {
    print_header "Перезапуск XVPN сервисов"
    
    stop_services
    sleep 3
    start_services
}

# Проверка статуса сервисов
check_services_status() {
    print_header "Статус XVPN сервисов"
    
    local services=(
        "xvpn-redis.service"
        "xvpn-traefik.service"
        "xvpn-api.service"
        "xvpn-agent.service"
        "xvpn-bot.service"
        "xvpn-client.service"
    )
    
    local all_running=true
    
    echo -e "${CYAN}Проверка статуса сервисов:${NC}"
    echo "--------------------------------"
    
    for service in "${services[@]}"; do
        local status=$(systemctl is-active "$service")
        local enabled=$(systemctl is-enabled "$service")
        
        if [[ "$status" == "active" ]]; then
            echo -e "✅ $service: $status (включен: $enabled)"
        else
            echo -e "❌ $service: $status (включен: $enabled)"
            all_running=false
        fi
    done
    
    echo ""
    
    if $all_running; then
        print_success "Все сервисы работают корректно"
        return 0
    else
        print_error "Некоторые сервисы не работают"
        return 1
    fi
}

# Проверка зависимостей
check_services_ready() {
    print_info "Проверка готовности зависимостей..."
    
    # Проверка Redis
    if ! systemctl is-active --quiet xvpn-redis.service; then
        print_warning "Redis не запущен, запуск..."
        systemctl start xvpn-redis.service
        sleep 5
    fi
    
    # Проверка Traefik
    if ! systemctl is-active --quiet xvpn-traefik.service; then
        print_warning "Traefik не запущен, запуск..."
        systemctl start xvpn-traefik.service
        sleep 5
    fi
    
    # Проверка API
    if ! systemctl is-active --quiet xvpn-api.service; then
        print_warning "API не запущен, запуск..."
        systemctl start xvpn-api.service
        sleep 10
    fi
    
    # Проверка доступности API
    if ! curl -k -s --max-time 5 "https://localhost:8443/health" > /dev/null; then
        print_warning "API не доступен, ожидание запуска..."
        sleep 10
    fi
}

# Просмотр логов
view_logs() {
    local service="$1"
    
    if [[ -z "$service" ]]; then
        print_error "Укажите сервис для просмотра логов"
        echo "Пример: $0 logs xvpn-api"
        exit 1
    fi
    
    if systemctl is-active --quiet "$service"; then
        print_header "Логи сервиса $service"
        journalctl -u "$service" -f
    else
        print_error "Сервис $service не запущен"
        exit 1
    fi
}

# Просмотр статуса конкретного сервиса
view_service_status() {
    local service="$1"
    
    if [[ -z "$service" ]]; then
        print_error "Укажите сервис для просмотра статуса"
        echo "Пример: $0 status xvpn-api"
        exit 1
    fi
    
    systemctl status "$service"
}

# Мониторинг ресурсов
monitor_resources() {
    print_header "Мониторинг ресурсов XVPN сервисов"
    
    echo -e "${CYAN}Использование памяти:${NC}"
    echo "----------------------"
    systemctl show xvpn-* --property=MemoryUsage | sort
    
    echo ""
    echo -e "${CYAN}Использование CPU:${NC}"
    echo "-----------------"
    systemctl show xvpn-* --property=CPUUsagePercent | sort
    
    echo ""
    echo -e "${CYAN}Активные процессы:${NC}"
    echo "------------------"
    ps aux | grep -E "(xvpn|uvx)" | grep -v grep | head -10
}

# Помощь
show_help() {
    echo "XVPN Service Management Script"
    echo ""
    echo "Использование: sudo $0 <команда> [опции]"
    echo ""
    echo "Команды:"
    echo "  install     - Установить все XVPN сервисы"
    echo "  remove      - Удалить все XVPN сервисы"
    echo "  start       - Запустить все сервисы"
    echo "  stop        - Остановить все сервисы"
    echo "  restart     - Перезапустить все сервисы"
    echo "  status      - Проверить статус всех сервисов"
    echo "  logs <svc>  - Просмотреть логи конкретного сервиса"
    echo "  status <svc> - Просмотреть статус конкретного сервиса"
    echo "  monitor     - Мониторинг ресурсов сервисов"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  sudo $0 install"
    echo "  sudo $0 start"
    echo "  sudo $0 logs xvpn-api"
    echo "  sudo $0 status xvpn-client"
}

# Основная функция
main() {
    check_permissions
    check_systemd
    
    case "${1:-}" in
        "install")
            install_services
            ;;
        "remove")
            remove_services
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            if [[ -n "$2" ]]; then
                view_service_status "$2"
            else
                check_services_status
            fi
            ;;
        "logs")
            view_logs "$2"
            ;;
        "monitor")
            monitor_resources
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            check_services_status
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"