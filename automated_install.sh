#!/bin/bash
# Automated XVPN Installation with Checks
# Полностью автоматизированная установка с проверками и тестами

set -e  # Выходим при ошибке, но с отчетом

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Переменные
XVPN_USER="xvpn"
XVPN_DIR="/opt/xvpn"
LOG_DIR="/var/log/xvpn"
VENV_DIR="$XVPN_DIR/venv"

# Массив для отчета о проверках
checks=()
failed_checks=()

run_check() {
    local description="$1"
    local command="$2"
    local critical="$3"  # "critical" или "optional"
    
    log_info "Проверка: $description"
    
    if eval "$command"; then
        log_success "✓ $description"
        checks+=("✓ $description")
    else
        log_error "✗ $description"
        checks+=("✗ $description")
        if [ "$critical" = "critical" ]; then
            failed_checks+=("$description")
        else
            log_warning "Это не критическая ошибка"
        fi
    fi
}

perform_uninstall() {
    log_info "Деинсталляция предыдущей версии XVPN..."
    
    # Остановка сервисов
    sudo systemctl stop xvpn-api xvpn-agent xvpn-bot xvpn-orchestrator xvpn-worker xvpn-api-pex xvpn-agent-pex 2>/dev/null || true
    sudo systemctl disable xvpn-api xvpn-agent xvpn-bot xvpn-orchestrator xvpn-worker xvpn-api-pex xvpn-agent-pex 2>/dev/null || true
    
    # Удаление сервисов
    sudo rm -f /etc/systemd/system/xvpn-*.service
    sudo systemctl daemon-reload
    
    # Удаление директорий
    sudo rm -rf /opt/xvpn
    sudo rm -rf /var/log/xvpn
    
    # Удаление пользователя
    sudo userdel xvpn 2>/dev/null || true
    
    log_success "Деинсталляция завершена"
}

perform_installation() {
    log_info "Начало установки XVPN..."

    # Этап 1: Подготовка системы
    log_info "=== Этап 1: Подготовка системы ==="
    
    # Проверки перед установкой
    run_check "Наличие curl" "command -v curl" "critical"
    run_check "Наличие git" "command -v git" "critical"
    run_check "Наличие python3" "command -v python3" "critical"
    run_check "Наличие systemctl" "command -v systemctl" "critical"
    
    if [ ${#failed_checks[@]} -gt 0 ]; then
        log_error "Критические проверки не пройдены, установка прервана"
        return 1
    fi

    # Установка системных зависимостей
    log_info "Установка системных зависимостей..."
    
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3 python3-venv python3-dev curl wget jq socat
    else
        log_error "Неизвестная система, установка зависимостей не поддерживается"
        return 1
    fi

    # Этап 2: Подготовка окружения
    log_info "=== Этап 2: Подготовка окружения ==="
    
    # Создание пользователя
    run_check "Создание пользователя $XVPN_USER" "sudo useradd -r -s /bin/false -d $XVPN_DIR $XVPN_USER 2>/dev/null || true" "critical"
    
    # Создание директорий
    sudo mkdir -p "$XVPN_DIR"/{data,logs,config,tls}
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R "$XVPN_USER":"$XVPN_USER" "$XVPN_DIR"
    sudo chmod -R 750 "$XVPN_DIR"
    
    run_check "Создание директорий" "[ -d $XVPN_DIR ] && [ -d $LOG_DIR ]" "critical"
    
    # Клонирование репозитория
    log_info "Клонирование репозитория..."
    temp_dir=$(mktemp -d)
    cd "$temp_dir"
    git clone https://github.com/Mehan42/chatVPN.git
    sudo cp -r chatVPN/* "$XVPN_DIR/"
    sudo chown -R "$XVPN_USER":"$XVPN_USER" "$XVPN_DIR"
    cd - > /dev/null
    
    run_check "Клонирование репозитория" "[ -f $XVPN_DIR/server/api/app.py ]" "critical"
    
    # Этап 3: Установка Python зависимостей
    log_info "=== Этап 3: Установка Python зависимостей ==="
    
    # Создание виртуального окружения
    sudo python3 -m venv "$VENV_DIR"
    sudo chown -R "$XVPN_USER":"$XVPN_USER" "$VENV_DIR"
    
    # Установка зависимостей
    sudo -u "$XVPN_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$XVPN_USER" "$VENV_DIR/bin/pip" install -r "$XVPN_DIR/requirements_server.txt"
    
    run_check "Установка серверных зависимостей" "$VENV_DIR/bin/python3 -c 'import flask'" "critical"
    
    # Этап 4: Установка XRay
    log_info "=== Этап 4: Установка XRay ==="
    
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
    
    run_check "Установка XRay" "command -v xray" "critical"
    
    # Этап 5: Настройка systemd сервисов
    log_info "=== Этап 5: Настройка systemd сервисов ==="
    
    # Создание сервисных файлов
    sudo tee /etc/systemd/system/xvpn-api.service > /dev/null << EOF
[Unit]
Description=XVPN API Server
After=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python3 $XVPN_DIR/server/api/app.py
Restart=always
RestartSec=5
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$XVPN_DIR

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/xvpn-agent.service > /dev/null << EOF
[Unit]
Description=XVPN Agent
After=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python3 $XVPN_DIR/server/agent/agent.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=$XVPN_DIR

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/xvpn-orchestrator.service > /dev/null << EOF
[Unit]
Description=XVPN Orchestrator
After=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python3 $XVPN_DIR/server/agent/orchestrator.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=$XVPN_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Загрузка сервисов
    sudo systemctl daemon-reload
    
    run_check "Создание сервисных файлов" "[ -f /etc/systemd/system/xvpn-api.service ]" "critical"
    
    # Этап 6: Тестирование
    log_info "=== Этап 6: Тестирование ==="
    
    # Запуск вспомогательных сервисов (без SSL)
    sudo systemctl start xvpn-agent
    sudo systemctl start xvpn-orchestrator
    
    sleep 3
    
    run_check "Агент запущен" "sudo systemctl is-active --quiet xvpn-agent" "optional"
    run_check "Оркестратор запущен" "sudo systemctl is-active --quiet xvpn-orchestrator" "optional"
    
    # Проверка процессов
    run_check "Процесс агента запущен" "pgrep -f 'server.agent.agent' > /dev/null" "optional"
    run_check "Процесс оркестратора запущен" "pgrep -f 'server.agent.orchestrator' > /dev/null" "optional"
    
    # Проверка зависимостей
    run_check "Flask установлен" "$VENV_DIR/bin/python3 -c 'import flask'" "critical"
    run_check "Requests установлен" "$VENV_DIR/bin/python3 -c 'import requests'" "critical"
    run_check "Psutil установлен" "$VENV_DIR/bin/python3 -c 'import psutil'" "critical"
    run_check "SQLAlchemy установлен" "$VENV_DIR/bin/python3 -c 'import sqlalchemy'" "critical"
    
    log_success "Установка завершена"
}

generate_report() {
    log_info "=== Отчет об установке ==="
    
    echo ""
    echo "Проверки:"
    for check in "${checks[@]}"; do
        echo "  $check"
    done
    
    echo ""
    if [ ${#failed_checks[@]} -gt 0 ]; then
        echo -e "${RED}Критические ошибки:${NC}"
        for error in "${failed_checks[@]}"; do
            echo -e "  ❌ $error"
        done
    else
        echo -e "${GREEN}Все критические проверки пройдены!${NC}"
    fi
    
    echo ""
    log_success "Установка завершена!"
    echo ""
    echo "Для запуска API сервера (требуется SSL):"
    echo "  sudo systemctl start xvpn-api"
    echo ""
    echo "Для запуска других сервисов:"
    echo "  sudo systemctl start xvpn-agent"
    echo "  sudo systemctl start xvpn-orchestrator"
    echo ""
    echo "Для проверки статуса:"
    echo "  sudo systemctl status xvpn-api"
    echo "  sudo systemctl status xvpn-agent"
    echo "  sudo systemctl status xvpn-orchestrator"
    echo ""
    echo "Логи:"
    echo "  sudo journalctl -u xvpn-api -f"
    echo "  sudo journalctl -u xvpn-agent -f"
    echo "  sudo journalctl -u xvpn-orchestrator -f"
}

# Основная логика скрипта
case "${1:-install}" in
    "install")
        perform_uninstall
        perform_installation
        generate_report
        ;;
    "uninstall")
        perform_uninstall
        log_success "Деинсталляция завершена"
        ;;
    "test")
        if [ $# -lt 2 ]; then
            log_error "Использование: $0 test <service-name>"
            exit 1
        fi
        
        service_name="$2"
        sudo systemctl status "$service_name" --no-pager
        ;;
    *)
        echo "Использование: $0 [install|uninstall|test]"
        echo "  install  - выполнить полную установку (по умолчанию)"
        echo "  uninstall - выполнить деинсталляцию"
        echo "  test <service-name> - проверить статус сервиса"
        exit 1
        ;;
esac