#!/bin/bash

# Установщик XVPN для Linux
# Простая установка с проверкой зависимостей

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
APP_NAME="XVPN"
INSTALL_DIR="/opt/xvpn"
SERVICE_USER="xvpn"
VERSION="1.0.0"

# Функции вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root"
        echo "Попробуйте: sudo $0"
        exit 1
    fi
}

# Проверка системы
check_system() {
    print_info "Проверка системы..."
    
    # Проверка дистрибутива
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION_ID=$VERSION_ID
        print_info "Обнаружен дистрибутив: $OS $VERSION_ID"
    else
        print_error "Не удалось определить дистрибутив Linux"
        exit 1
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    if [[ "$ARCH" != "x86_64" ]]; then
        print_warning "Обнаружена архитектура $ARCH, рекомендуется x86_64"
    fi
}

# Установка зависимостей
install_dependencies() {
    print_info "Установка зависимостей..."
    
    # Определение менеджера пакетов
    if command -v apt-get &> /dev/null; then
        PACKAGE_MANAGER="apt-get"
        update_cmd="apt-get update"
        install_cmd="apt-get install -y"
        packages="python3 python3-pip python3-venv curl wget git"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
        update_cmd="yum check-update"
        install_cmd="yum install -y"
        packages="python3 python3-pip curl wget git"
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
        update_cmd="dnf check-update"
        install_cmd="dnf install -y"
        packages="python3 python3-pip curl wget git"
    else
        print_error "Не удалось определить менеджер пакетов"
        exit 1
    fi
    
    print_info "Используется менеджер пакетов: $PACKAGE_MANAGER"
    
    # Обновление системы
    $update_cmd
    
    # Установка зависимостей
    $install_cmd $packages
    
    # Установка Docker если возможно
    if ! command -v docker &> /dev/null; then
        print_info "Установка Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        usermod -aG docker $SUDO_USER
        print_success "Docker установлен"
    else
        print_success "Docker уже установлен"
    fi
}

# Создание пользователя
create_user() {
    print_info "Создание пользователя $SERVICE_USER..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" $SERVICE_USER
        print_success "Пользователь $SERVICE_USER создан"
    else
        print_success "Пользователь $SERVICE_USER уже существует"
    fi
}

# Установка приложения
install_app() {
    print_info "Установка приложения в $INSTALL_DIR..."
    
    # Создание директорий
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/client"
    mkdir -p "$INSTALL_DIR/server"
    mkdir -p "$INSTALL_DIR/docker"
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/data"
    
    # Копирование файлов
    cp -r client/* "$INSTALL_DIR/client/"
    cp -r server/* "$INSTALL_DIR/server/"
    cp -r docker/* "$INSTALL_DIR/docker/"
    cp docker-compose.yml "$INSTALL_DIR/"
    cp -r systemd/* "$INSTALL_DIR/systemd/"
    
    # Установка прав
    chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/client/chatvpn_backend.py"
    chmod +x "$INSTALL_DIR/server/install_server.sh"
    
    # Копирование systemd сервисов
    cp systemd/*.service /etc/systemd/system/
    
    print_success "Приложение установлено"
}

# Настройка системы
configure_system() {
    print_info "Настройка системы..."
    
    # Обновление systemd
    systemctl daemon-reload
    
    # Включение сервисов
    systemctl enable xvpn-docker.service
    systemctl enable xvpn-api.service
    systemctl enable xvpn-agent.service
    systemctl enable xvpn-bot.service
    systemctl enable xvpn-worker.service
    systemctl enable xvpn-client.service
    
    print_success "Система настроена"
}

# Запуск сервисов
start_services() {
    print_info "Запуск сервисов..."
    
    # Запуск Docker
    systemctl start docker
    
    # Запуск сервисов XVPN
    systemctl start xvpn-docker.service
    systemctl start xvpn-api.service
    systemctl start xvpn-agent.service
    systemctl start xvpn-bot.service
    systemctl start xvpn-worker.service
    systemctl start xvpn-client.service
    
    print_success "Сервисы запущены"
}

# Проверка установки
verify_installation() {
    print_info "Проверка установки..."
    
    # Проверка сервисов
    services=(
        "xvpn-docker"
        "xvpn-api"
        "xvpn-agent"
        "xvpn-bot"
        "xvpn-worker"
        "xvpn-client"
    )
    
    all_running=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service.service"; then
            print_success "Сервис $service.service работает"
        else
            print_error "Сервис $service.service не работает"
            all_running=false
        fi
    done
    
    if $all_running; then
        print_success "✅ Установка успешно завершена!"
        echo ""
        echo "Для управления сервисами используйте:"
        echo "  sudo systemctl start|stop|restart|status xvpn-*"
        echo "  sudo journalctl -u xvpn-* -f для просмотра логов"
        echo ""
        echo "Конфигурационные файлы находятся в: $INSTALL_DIR/config/"
        echo "Логи находятся в: $INSTALL_DIR/logs/"
    else
        print_error "❌ Некоторые сервисы не запустились"
        echo "Проверьте логи: sudo journalctl -u xvpn-*"
        exit 1
    fi
}

# Основная функция
main() {
    echo "================================"
    echo -e "${BLUE}🚀 Установка $APP_NAME $VERSION${NC}"
    echo "================================"
    
    check_root
    check_system
    install_dependencies
    create_user
    install_app
    configure_system
    start_services
    verify_installation
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
        echo "  sudo $0         # Стандартная установка"
        echo "  sudo $0 --help  # Показать справку"
        exit 0
        ;;
    "--version"|-v)
        echo "$APP_NAME $VERSION"
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