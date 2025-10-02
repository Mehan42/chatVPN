#!/bin/bash
# Обновление XVPN

set -e

echo "=== Обновление XVPN ==="
echo "Дата: $(date)"
echo ""

# Остановка сервисов
echo "Остановка сервисов..."
systemctl stop xvpn-api.service
systemctl stop xvpn-bot.service
systemctl stop xvpn-agent.service
systemctl stop xvpn-worker.service

# Остановка Docker
echo "Остановка Docker..."
cd /home/xvpn/chatvpn
docker-compose down

# Создание резервной копии
echo "Создание резервной копии..."
backup_dir="/home/xvpn/chatvpn_backup_$(date +%Y%m%d_%H%M%S)"
cp -r /home/xvpn/chatvpn "$backup_dir"

# Обновление файлов
echo "Обновление файлов..."
git pull origin main

# Обновление зависимостей
echo "Обновление зависимостей..."
pip3 install -r requirements.txt

# Обновление Docker образов
echo "Обновление Docker образов..."
docker-compose pull

# Запуск сервисов
echo "Запуск сервисов..."
docker-compose up -d

systemctl start xvpn-api.service
systemctl start xvpn-bot.service
systemctl start xvpn-agent.service
systemctl start xvpn-worker.service

# Проверка обновления
echo "Проверка обновления..."
sleep 10

if docker ps | grep -q xvpn-api; then
    echo "✓ Обновление успешно завершено"
else
    echo "✗ Ошибка обновления"
    echo "Восстановление из резервной копии..."
    cp -r "$backup_dir"/* /home/xvpn/chatvpn/
    docker-compose up -d
fi

echo ""
echo "=== Обновление XVPN завершено ==="
