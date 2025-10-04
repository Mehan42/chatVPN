#!/bin/bash

# XVPN Deployment Script
# Скрипт для развертывания XVPN системы

set -e  # Выход при любой ошибке

echo "🚀 Deploying XVPN System..."
echo "=========================="

# === Параметры ===
DEPLOY_ENVIRONMENT=${1:-staging}
DEPLOY_VERSION=${2:-latest}
DRY_RUN=${3:-false}

# === Переменные окружения ===
export DEBIAN_FRONTEND=noninteractive
export TZ=UTC

# === Функции вспомогательные ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        error_exit "Git is not installed"
    fi
    
    log "All prerequisites satisfied"
}

# === Функции развертывания ===
prepare_environment() {
    log "Preparing deployment environment: $DEPLOY_ENVIRONMENT"
    
    # Создание директорий
    mkdir -p /opt/xvpn/{data,logs,config,certs,backups}
    
    # Установка прав доступа
    chown -R 1000:1000 /opt/xvpn || true
    
    # Создание пользователя XVPN (если нужно)
    if ! id -u xvpn &>/dev/null; then
        useradd -r -s /bin/false -d /opt/xvpn xvpn || true
        usermod -aG docker xvpn || true
    fi
    
    # Установка прав доступа для пользователя
    chown -R xvpn:xvpn /opt/xvpn || true
}

clone_repository() {
    log "Cloning repository..."
    
    # Клонирование репозитория
    if [ -d "/opt/xvpn/src" ]; then
        log "Repository already exists, pulling latest changes..."
        cd /opt/xvpn/src
        git pull origin main
    else
        log "Cloning fresh repository..."
        git clone https://github.com/Mehan42/chatVPN.git /opt/xvpn/src
    fi
    
    # Проверка версии
    if [ "$DEPLOY_VERSION" != "latest" ]; then
        log "Checking out version: $DEPLOY_VERSION"
        cd /opt/xvpn/src
        git checkout "v$DEPLOY_VERSION" || git checkout "$DEPLOY_VERSION"
    fi
    
    # Установка прав доступа
    chown -R xvpn:xvpn /opt/xvpn/src
}

configure_docker_compose() {
    log "Configuring Docker Compose for $DEPLOY_ENVIRONMENT..."
    
    # Копирование файла конфигурации
    if [ "$DEPLOY_ENVIRONMENT" = "production" ]; then
        cp /opt/xvpn/src/docker-compose.production.yml /opt/xvpn/docker-compose.yml
    else
        cp /opt/xvpn/src/docker-compose.staging.yml /opt/xvpn/docker-compose.yml
    fi
    
    # Установка прав доступа
    chown xvpn:xvpn /opt/xvpn/docker-compose.yml
    
    # Настройка переменных окружения
    if [ ! -f "/opt/xvpn/.env" ]; then
        cp /opt/xvpn/src/.env.$DEPLOY_ENVIRONMENT /opt/xvpn/.env
        chown xvpn:xvpn /opt/xvpn/.env
        chmod 600 /opt/xvpn/.env
    fi
}

pull_images() {
    log "Pulling Docker images..."
    
    # Вход в реестр (если нужно)
    if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    fi
    
    # Загрузка образов
    cd /opt/xvpn
    docker-compose pull
    
    # Проверка загрузки
    if [ $? -ne 0 ]; then
        error_exit "Failed to pull Docker images"
    fi
}

start_services() {
    log "Starting XVPN services..."
    
    # Остановка существующих служб (если есть)
    cd /opt/xvpn
    docker-compose down --remove-orphans || true
    
    # Запуск новых служб
    if [ "$DRY_RUN" = "true" ]; then
        docker-compose up --no-start
    else
        docker-compose up -d
    fi
    
    # Проверка запуска
    if [ $? -ne 0 ]; then
        error_exit "Failed to start services"
    fi
}

verify_deployment() {
    log "Verifying deployment..."
    
    # Ожидание запуска служб
    log "Waiting for services to start..."
    sleep 30
    
    # Проверка состояния служб
    cd /opt/xvpn
    docker-compose ps
    
    # Проверка здоровья API
    log "Checking API health..."
    for i in {1..10}; do
        if curl -k -f https://localhost:8443/mcp/v1/vpn.health > /dev/null 2>&1; then
            log "✅ API is healthy"
            return 0
        fi
        log "⏳ Waiting for API to become healthy ($i/10)"
        sleep 10
    done
    
    error_exit "API failed to become healthy"
}

# === Основной поток выполнения ===
main() {
    log "Starting XVPN deployment to $DEPLOY_ENVIRONMENT environment"
    
    # Проверка предварительных условий
    check_prerequisites
    
    # Подготовка окружения
    prepare_environment
    
    # Клонирование репозитория
    clone_repository
    
    # Настройка Docker Compose
    configure_docker_compose
    
    # Загрузка образов
    pull_images
    
    # Запуск служб
    start_services
    
    # Проверка развертывания
    verify_deployment
    
    # Уведомление об успешном развертывании
    log "✅ XVPN deployment completed successfully!"
    log "Environment: $DEPLOY_ENVIRONMENT"
    log "Version: $DEPLOY_VERSION"
    log "Services started. Check status with: docker-compose ps"
}

# === Обработка сигналов ===
trap 'error_exit "Deployment interrupted"' INT TERM

# === Запуск ===
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <environment> [version] [dry-run]"
    echo "  environment: staging|production"
    echo "  version: version tag (optional, default: latest)"
    echo "  dry-run: true|false (optional, default: false)"
    exit 1
fi

main "$@"
exit 0