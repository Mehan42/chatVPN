#!/bin/bash

# Скрипт установки systemd сервисов для XVPN
# Абсолютный путь: ~/chatvpn/scripts/install_systemd_services.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Установка systemd сервисов XVPN ===${NC}"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен быть запущен с правами root${NC}"
   exit 1
fi

# Определение путей
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="$PROJECT_DIR/systemd"

# Создание пользователя и группы
echo -e "${YELLOW}1. Создание пользователя и группы xvpn...${NC}"
if ! id "xvpn" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/xvpn xvpn
    echo "Пользователь xvpn создан"
else
    echo "Пользователь xvpn уже существует"
fi

# Создание директорий
echo -e "${YELLOW}2. Создание директорий...${NC}"
mkdir -p /opt/xvpn
mkdir -p /opt/xvpn/client
mkdir -p /opt/xvpn/data
mkdir -p /opt/xvpn/logs
mkdir -p /opt/xvpn/config
mkdir -p /opt/xvpn/pids

# Копирование файлов
echo -e "${YELLOW}3. Копирование файлов...${NC}"
cp -r "$PROJECT_DIR/client" /opt/xvpn/
cp -r "$PROJECT_DIR/server" /opt/xvpn/
cp -r "$PROJECT_DIR/docker" /opt/xvpn/
cp "$PROJECT_DIR/docker-compose.yml" /opt/xvpn/
cp -r "$SYSTEMD_DIR"/* /etc/systemd/system/

# Установка прав
echo -e "${YELLOW}4. Установка прав...${NC}"
chown -R xvpn:xvpn /opt/xvpn
chmod +x /opt/xvpn/client/chatvpn_backend.py
chmod +x /opt/xvpn/server/install_server.sh
chmod +x /opt/xvpn/deploy/install_server.sh

# Установка зависимостей
echo -e "${YELLOW}5. Установка зависимостей...${NC}"
# Установка Python и pip, если не установлены
if ! command -v python3 &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Установка Docker и Docker Compose, если не установлены
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker xvpn
fi

# Установка uv, если не установлен
if ! command -v uv &> /dev/null; then
    echo "Установка uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    source ~/.bashrc
fi

# Установка requirements
if [ -f "/opt/xvpn/server/requirements.txt" ]; then
    cd /opt/xvpn/server
    uv pip install -r requirements.txt
fi

# Обновление systemd
echo -e "${YELLOW}6. Обновление systemd...${NC}"
systemctl daemon-reload

# Включение сервисов
echo -e "${YELLOW}7. Включение сервисов...${NC}"
systemctl enable xvpn-docker.service
systemctl enable xvpn-redis.service
systemctl enable xvpn-traefik.service
systemctl enable xvpn-api.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-bot.service
systemctl enable xvpn-worker.service
systemctl enable xvpn-client.service
systemctl enable xvpn-gui.service

# Запуск сервисов
echo -e "${YELLOW}8. Запуск сервисов...${NC}"
systemctl start xvpn-docker.service
systemctl start xvpn-redis.service
systemctl start xvpn-traefik.service
systemctl start xvpn-api.service
systemctl start xvpn-agent.service
systemctl start xvpn-bot.service
systemctl start xvpn-worker.service
systemctl start xvpn-client.service
systemctl start xvpn-gui.service

# Проверка статуса
echo -e "${YELLOW}9. Проверка статуса сервисов...${NC}"
sleep 5

services=(
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

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service.service"; then
        echo -e "${GREEN}✓ $service.service запущен${NC}"
    else
        echo -e "${RED}✗ $service.service не запущен${NC}"
        systemctl status "$service.service" --no-pager -l
    fi
done

echo -e "${GREEN}=== Установка завершена ===${NC}"
echo -e "${YELLOW}Проверьте статус сервисов командой: systemctl status xvpn-*${NC}"
echo -e "${YELLOW}Логи сервисов: journalctl -u xvpn-* -f${NC}"