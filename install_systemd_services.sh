#!/bin/bash

# XVPN Systemd Services Installer
# Установщик systemd сервисов XVPN

set -e  # Выход при любой ошибке

echo "🚀 Installing XVPN Systemd Services..."
echo "===================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# === Configuration ===
XVPN_USER="xvpn"
XVPN_DIR="/opt/xvpn"
SYSTEMD_DIR="/etc/systemd/system"
LOG_DIR="/var/log/xvpn"
BACKUP_DIR="/opt/xvpn/backups"

# === Functions ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_dependencies() {
    log "Checking dependencies..."
    
    # Проверка что все необходимые пакеты установлены
    packages=("systemd" "python3" "curl" "wget" "git" "docker.io" "docker-compose")
    
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package"; then
            log "Installing missing package: $package"
            apt install -y "$package"
        fi
    done
    
    log "All dependencies satisfied"
}

create_user() {
    log "Creating xvpn user..."
    
    # Создание пользователя xvpn если он не существует
    if ! id "$XVPN_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$XVPN_DIR" "$XVPN_USER"
        log "User $XVPN_USER created"
    else
        log "User $XVPN_USER already exists"
    fi
}

create_directories() {
    log "Creating directories..."
    
    # Создание необходимых директорий
    mkdir -p "$XVPN_DIR" "$LOG_DIR" "$BACKUP_DIR"
    mkdir -p "$XVPN_DIR"/{server,client,data,config,db,logs,transports,agents,bots,workers,orchestrators,cores,monitors,backups}
    mkdir -p "$LOG_DIR"/{api,agent,bot,worker,orchestrator,core,monitor,client,gui,state}
    
    # Установка прав доступа
    chown -R "$XVPN_USER":"$XVPN_USER" "$XVPN_DIR" "$LOG_DIR"
    chmod -R 750 "$XVPN_DIR" "$LOG_DIR"
    
    log "Directories created and permissions set"
}

copy_service_files() {
    log "Copying service files..."
    
    # Копирование файлов сервисов
    if [ -d "/home/uss/chatvpn/systemd" ]; then
        cp /home/uss/chatvpn/systemd/*.service "$SYSTEMD_DIR/"
        log "Service files copied"
    else
        log "Warning: systemd directory not found"
    fi
}

setup_docker() {
    log "Setting up Docker..."
    
    # Добавление пользователя в группу docker
    usermod -aG docker "$XVPN_USER" || true
    
    # Включение и запуск Docker
    systemctl enable docker
    systemctl start docker
    
    log "Docker setup completed"
}

setup_firewall() {
    log "Setting up firewall..."
    
    # Установка UFW если не установлен
    if ! command -v ufw &> /dev/null; then
        apt install -y ufw
    fi
    
    # Включение UFW
    ufw --force enable
    
    # Разрешение необходимых портов
    ufw allow ssh
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 8443/tcp  # XVPN API
    ufw allow 51820/udp # WireGuard
    
    log "Firewall configured"
}

reload_systemd() {
    log "Reloading systemd..."
    
    # Перезагрузка конфигурации systemd
    systemctl daemon-reload
    
    log "Systemd reloaded"
}

enable_services() {
    log "Enabling services..."
    
    # Включение сервисов
    services=("xvpn-api" "xvpn-agent" "xvpn-bot" "xvpn-worker" "xvpn-orchestrator" "xvpn-core" "xvpn-monitor" "xvpn-backup")
    
    for service in "${services[@]}"; do
        if [ -f "$SYSTEMD_DIR/$service.service" ]; then
            systemctl enable "$service.service"
            log "Service $service enabled"
        else
            log "Warning: Service $service not found"
        fi
    done
    
    # Включение таймера бэкапа
    if [ -f "$SYSTEMD_DIR/xvpn-backup.timer" ]; then
        systemctl enable xvpn-backup.timer
        log "Backup timer enabled"
    fi
}

create_config_files() {
    log "Creating configuration files..."
    
    # Создание директории для конфигурации
    mkdir -p "$XVPN_DIR/config"
    
    # Создание базового конфигурационного файла
    cat > "$XVPN_DIR/config/xvpn.conf" << EOF
{
  "server_ip": "$(curl -s ifconfig.co)",
  "api_port": 8443,
  "bot_token": "",
  "chat_id": "",
  "log_level": "INFO",
  "data_dir": "/opt/xvpn/data",
  "logs_dir": "/var/log/xvpn"
}
EOF
    
    # Создание файла .env
    cat > "$XVPN_DIR/.env" << EOF
XVPN_USER=$XVPN_USER
XVPN_DIR=$XVPN_DIR
LOG_DIR=$LOG_DIR
BOT_TOKEN=
CHAT_ID=
API_BASE_URL=https://$(curl -s ifconfig.co):8443
DATABASE_URL=sqlite:////opt/xvpn/db/agent.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF
    
    # Установка прав доступа
    chown -R "$XVPN_USER":"$XVPN_USER" "$XVPN_DIR/config" "$XVPN_DIR/.env"
    chmod 600 "$XVPN_DIR/.env"
    
    log "Configuration files created"
}

setup_logging() {
    log "Setting up logging..."
    
    # Создание директорий для логов
    mkdir -p "$LOG_DIR"/{api,agent,bot,worker,orchestrator,core,monitor,client,gui,state}
    
    # Установка прав доступа
    chown -R "$XVPN_USER":"$XVPN_USER" "$LOG_DIR"
    chmod -R 750 "$LOG_DIR"
    
    log "Logging configured"
}

setup_backup() {
    log "Setting up backup..."
    
    # Создание директории для бэкапов
    mkdir -p "$BACKUP_DIR"
    
    # Установка прав доступа
    chown -R "$XVPN_USER":"$XVPN_USER" "$BACKUP_DIR"
    chmod -R 750 "$BACKUP_DIR"
    
    log "Backup configured"
}

final_check() {
    log "Performing final check..."
    
    # Проверка что все сервисы скопированы
    services=("xvpn-api" "xvpn-agent" "xvpn-bot" "xvpn-worker" "xvpn-orchestrator" "xvpn-core" "xvpn-monitor" "xvpn-backup")
    
    for service in "${services[@]}"; do
        if [ -f "$SYSTEMD_DIR/$service.service" ]; then
            log "✅ $service.service found"
        else
            log "❌ $service.service not found"
        fi
    done
    
    log "Final check completed"
}

# === Main Installation Process ===
main() {
    log "Starting XVPN Systemd Services Installation"
    
    # Проверка зависимостей
    check_dependencies
    
    # Создание пользователя
    create_user
    
    # Создание директорий
    create_directories
    
    # Копирование файлов сервисов
    copy_service_files
    
    # Настройка Docker
    setup_docker
    
    # Настройка firewall
    setup_firewall
    
    # Перезагрузка systemd
    reload_systemd
    
    # Включение сервисов
    enable_services
    
    # Создание конфигурационных файлов
    create_config_files
    
    # Настройка логирования
    setup_logging
    
    # Настройка бэкапа
    setup_backup
    
    # Финальная проверка
    final_check
    
    log "XVPN Systemd Services Installation Completed!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Set your Telegram bot token in $XVPN_DIR/.env"
    echo "2. Start services: sudo systemctl start xvpn-api xvpn-agent xvpn-bot"
    echo "3. Check status: sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
    echo "4. Enable auto-start: sudo systemctl enable xvpn-api xvpn-agent xvpn-bot"
    echo ""
    echo "💡 Tips:"
    echo "- View logs: sudo journalctl -u xvpn-* -f"
    echo "- Restart services: sudo systemctl restart xvpn-*"
    echo "- Stop services: sudo systemctl stop xvpn-*"
}

# === Run Installation ===
main "$@"
exit 0