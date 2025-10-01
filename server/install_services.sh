#!/bin/bash

# Скрипт установки и настройки systemd сервисов для XVPN
# Автор: Roo
# Дата: 2025-01-01

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

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    log_error "Этот скрипт должен быть запущен от root пользователя"
    exit 1
fi

# Определение текущего пользователя
CURRENT_USER=$(logname 2>/dev/null || echo "${SUDO_USER:-$USER}")

log_info "Установка systemd сервисов для XVPN"
log_info "Текущий пользователь: $CURRENT_USER"

# Создание директории для сервисов
SERVICES_DIR="/etc/systemd/system"
XVPN_DIR="/home/$CURRENT_USER/.xvpn"

log_info "Создание необходимых директорий..."
mkdir -p "$XVPN_DIR"
mkdir -p "$SERVICES_DIR"

# Копирование файлов сервисов
log_info "Копирование файлов сервисов..."

# Копирование существующих сервисов с исправленными путями
cp server/server_bot.service "$SERVICES_DIR/xvpn-server-bot.service" || log_error "Не удалось скопировать server_bot.service"
cp server/xray.service "$SERVICES_DIR/xvpn-xray.service" || log_error "Не удалось скопировать xray.service"
cp server/agent.service "$SERVICES_DIR/xvpn-agent.service" || log_error "Не удалось скопировать agent.service"
cp server/api.service "$SERVICES_DIR/xvpn-api.service" || log_error "Не удалось скопировать api.service"
cp server/bot.service "$SERVICES_DIR/xvpn-bot.service" || log_error "Не удалось скопировать bot.service"
cp server/xvpn.service "$SERVICES_DIR/xvpn.service" || log_error "Не удалось скопировать xvpn.service"

# Установка правильных прав на директорию
chown -R "$CURRENT_USER:$CURRENT_USER" "$XVPN_DIR"
chmod -R 755 "$XVPN_DIR"

log_info "Перезагрузка systemd..."
systemctl daemon-reload

# Включение сервисов
log_info "Включение сервисов..."
systemctl enable xvpn.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-api.service
systemctl enable xvpn-xray.service
systemctl enable xvpn-bot.service

log_success "Сервисы успешно установлены!"
log_info "Для запуска сервисов выполните:"
log_info "  sudo systemctl start xvpn.service"
log_info ""
log_info "Для проверки статуса сервисов выполните:"
log_info "  sudo systemctl status xvpn.service"
log_info "  sudo systemctl status xvpn-*.service"
log_info ""
log_info "Для просмотра логов выполните:"
log_info "  sudo journalctl -u xvpn.service -f"
log_info "  sudo journalctl -u xvpn-*.service -f"

exit 0