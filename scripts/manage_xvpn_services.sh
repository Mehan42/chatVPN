#!/bin/bash

# Скрипт управления сервисами XVPN
# Абсолютный путь: ~/chatvpn/scripts/manage_xvpn_services.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Список сервисов
SERVICES=(
    "xvpn-docker"
    "xvpn-redis"
    "xvpn-traefik"
    "xvpn-api"
    "xvpn-agent"
    "xvpn-bot"
    "xvpn-worker"
    "xvpn-client"
    "xvpn-gui"
)

# Цвета для статуса
COLOR_RUNNING="${GREEN}"
COLOR_STOPPED="${RED}"
COLOR_INACTIVE="${YELLOW}"

show_help() {
    echo "Скрипт управления сервисами XVPN"
    echo ""
    echo "Использование: $0 [опции] [сервисы...]"
    echo ""
    echo "Опции:"
    echo "  start     Запустить сервисы"
    echo "  stop      Остановить сервисы"
    echo "  restart   Перезапустить сервисы"
    echo "  status    Показать статус сервисов"
    echo "  logs      Показать логи сервисов"
    echo "  enable    Включить автозапуск сервисов"
    echo "  disable   Отключить автозапуск сервисов"
    echo "  logs-f    Показать логи в реальном времени"
    echo "  help      Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start xvpn-api xvpn-client     # Запустить API и клиент"
    echo "  $0 stop                           # Остановить все сервисы"
    echo "  $0 status                         # Показать статус всех сервисов"
    echo "  $0 logs xvpn-api                  # Показать логи API"
    echo ""
    echo "Если не указаны сервисы, действие применяется ко всем."
}

get_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service.service"; then
        echo -e "${COLOR_RUNNING}● Запущен${NC}"
    elif systemctl is-enabled --quiet "$service.service"; then
        echo -e "${COLOR_STOPPED}● Остановлен (включен)${NC}"
    else
        echo -e "${COLOR_INACTIVE}● Отключен${NC}"
    fi
}

start_services() {
    local services=$1
    echo -e "${BLUE}=== Запуск сервисов ===${NC}"
    for service in $services; do
        if systemctl is-active --quiet "$service.service"; then
            echo -e "${GREEN}✓ $service уже запущен${NC}"
        else
            echo -e "${YELLOW}Запуск $service...${NC}"
            systemctl start "$service.service"
            if systemctl is-active --quiet "$service.service"; then
                echo -e "${GREEN}✓ $service запущен${NC}"
            else
                echo -e "${RED}✗ $service не удалось запустить${NC}"
            fi
        fi
    done
}

stop_services() {
    local services=$1
    echo -e "${BLUE}=== Остановка сервисов ===${NC}"
    # Останавливаем в обратном порядке
    local reverse_services=$(echo "$services" | tac -s' ')
    for service in $reverse_services; do
        if systemctl is-active --quiet "$service.service"; then
            echo -e "${YELLOW}Остановка $service...${NC}"
            systemctl stop "$service.service"
            if systemctl is-active --quiet "$service.service"; then
                echo -e "${RED}✗ $service не удалось остановить${NC}"
            else
                echo -e "${GREEN}✓ $service остановлен${NC}"
            fi
        else
            echo -e "${GREEN}✓ $service уже остановлен${NC}"
        fi
    done
}

restart_services() {
    local services=$1
    echo -e "${BLUE}=== Перезапуск сервисов ===${NC}"
    for service in $services; do
        echo -e "${YELLOW}Перезапуск $service...${NC}"
        systemctl restart "$service.service"
        if systemctl is-active --quiet "$service.service"; then
            echo -e "${GREEN}✓ $service перезапущен${NC}"
        else
            echo -e "${RED}✗ $service не удалось перезапустить${NC}"
        fi
    done
}

show_status() {
    local services=$1
    echo -e "${BLUE}=== Статус сервисов ===${NC}"
    printf "%-20s %s\n" "Сервис" "Статус"
    printf "%-20s %s\n" "-------------------" "-------------------"
    for service in $services; do
        printf "%-20s %s\n" "$service" "$(get_service_status "$service")"
    done
}

show_logs() {
    local services=$1
    echo -e "${BLUE}=== Логи сервисов ===${NC}"
    for service in $services; do
        echo -e "${YELLOW}=== Логи $service ===${NC}"
        journalctl -u "$service.service" --no-pager -n 50
        echo ""
    done
}

follow_logs() {
    local services=$1
    echo -e "${BLUE}=== Логи сервисов в реальном времени ===${NC}"
    journalctl -u "$service.service" -f
}

enable_services() {
    local services=$1
    echo -e "${BLUE}=== Включение автозапуска сервисов ===${NC}"
    for service in $services; do
        echo -e "${YELLOW}Включение $service...${NC}"
        systemctl enable "$service.service"
        echo -e "${GREEN}✓ $service включен${NC}"
    done
}

disable_services() {
    local services=$1
    echo -e "${BLUE}=== Отключение автозапуска сервисов ===${NC}"
    for service in $services; do
        echo -e "${YELLOW}Отключение $service...${NC}"
        systemctl disable "$service.service"
        echo -e "${GREEN}✓ $service отключен${NC}"
    done
}

# Проверка аргументов
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

# Определение действия
ACTION=$1
shift

# Определение сервисов
if [[ $# -eq 0 ]]; then
    SERVICES_SELECTED="${SERVICES[*]}"
else
    SERVICES_SELECTED="$@"
fi

# Выполнение действия
case "$ACTION" in
    "start")
        start_services "$SERVICES_SELECTED"
        ;;
    "stop")
        stop_services "$SERVICES_SELECTED"
        ;;
    "restart")
        restart_services "$SERVICES_SELECTED"
        ;;
    "status")
        show_status "$SERVICES_SELECTED"
        ;;
    "logs")
        show_logs "$SERVICES_SELECTED"
        ;;
    "logs-f")
        follow_logs "$SERVICES_SELECTED"
        ;;
    "enable")
        enable_services "$SERVICES_SELECTED"
        ;;
    "disable")
        disable_services "$SERVICES_SELECTED"
        ;;
    "help")
        show_help
        ;;
    *)
        echo -e "${RED}Ошибка: Неизвестное действие '$ACTION'${NC}"
        show_help
        exit 1
        ;;
esac