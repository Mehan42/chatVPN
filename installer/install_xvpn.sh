#!/bin/bash
# Установщик XVPN
# Автоматическая установка XVPN системы

set -e

echo "=== Установка XVPN ==="
echo "Дата: $(date)"
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   echo "Используйте: sudo ./install_xvpn.sh"
   exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Установка Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не найден. Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание пользователя XVPN
if ! id "xvpn" &>/dev/null; then
    echo "Создание пользователя xvpn..."
    useradd -m -s /bin/bash xvpn
    passwd -d xvpn  # Установка пустого пароля
else
    echo "Пользователь xvpn уже существует"
fi

# Создание директорий
echo "Создание директорий..."
mkdir -p /home/xvpn/chatvpn
mkdir -p /home/xvpn/chatvpn/client
mkdir -p /home/xvpn/chatvpn/server
mkdir -p /home/xvpn/chatvpn/server/security
mkdir -p /home/xvpn/chatvpn/server/api
mkdir -p /home/xvpn/chatvpn/server/agent
mkdir -p /home/xvpn/chatvpn/server/deploy
mkdir -p /home/xvpn/chatvpn/docker
mkdir -p /home/xvpn/chatvpn/scripts
mkdir -p /home/xvpn/chatvpn/docs
mkdir -p /home/xvpn/chatvpn/systemd
mkdir -p /var/log/xvpn
mkdir -p /etc/xvpn

# Копирование файлов
echo "Копирование файлов..."
cp -r client/* /home/xvpn/chatvpn/client/
cp -r server/* /home/xvpn/chatvpn/server/
cp -r docker/* /home/xvpn/chatvpn/docker/
cp -r scripts/* /home/xvpn/chatvpn/scripts/
cp -r systemd/* /etc/systemd/system/

# Установка прав
echo "Установка прав..."
chown -R xvpn:xvpn /home/xvpn/chatvpn
chmod +x /home/xvpn/chatvpn/client/*.py
chmod +x /home/xvpn/chatvpn/server/*.py
chmod +x /home/xvpn/chatvpn/scripts/*.sh
chmod +x /home/xvpn/chatvpn/scripts/*.py

# Установка зависимостей
echo "Установка зависимостей..."
cd /home/xvpn/chatvpn
pip3 install -r requirements.txt

# Копирование конфигурации
echo "Копирование конфигурации..."
if [ ! -f /etc/xvpn/config.json ]; then
    cp client/client.json.example /etc/xvpn/config.json
    chown xvpn:xvpn /etc/xvpn/config.json
fi

# Настройка systemd
echo "Настройка systemd..."
systemctl daemon-reload

# Включение сервисов
echo "Включение сервисов..."
systemctl enable xvpn-api.service
systemctl enable xvpn-bot.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-worker.service

# Запуск сервисов
echo "Запуск сервисов..."
systemctl start xvpn-api.service
systemctl start xvpn-bot.service
systemctl start xvpn-agent.service
systemctl start xvpn-worker.service

# Настройка Docker
echo "Настройка Docker..."
cd /home/xvpn/chatvpn
docker-compose up -d

# Проверка установки
echo "Проверка установки..."
sleep 10

# Проверка сервисов
if systemctl is-active --quiet xvpn-api.service; then
    echo "✓ API сервис запущен"
else
    echo "✗ API сервис не запущен"
fi

if systemctl is-active --quiet xvpn-bot.service; then
    echo "✓ Bot сервис запущен"
else
    echo "✗ Bot сервис не запущен"
fi

if docker ps | grep -q xvpn-api; then
    echo "✓ Docker контейнер API запущен"
else
    echo "✗ Docker контейнер API не запущен"
fi

# Завершение установки
echo ""
echo "=== Установка XVPN завершена ==="
echo "Логи:"
echo "  - Системные: journalctl -u xvpn-api.service"
echo "  - Docker: docker logs xvpn-api"
echo "  - Приложения: tail -f /var/log/xvpn/*.log"
echo ""
echo "Управление сервисами:"
echo "  - Запуск: sudo systemctl start xvpn-*.service"
echo "  - Остановка: sudo systemctl stop xvpn-*.service"
echo "  - Статус: sudo systemctl status xvpn-*.service"
echo ""
echo "Документация: /home/xvpn/chatvpn/docs/"
echo ""
echo "Для перезагрузки системы: sudo reboot"
