#!/bin/bash
# Деинсталлятор XVPN

set -e

echo "=== Деинсталляция XVPN ==="
echo "Дата: $(date)"
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   echo "Используйте: sudo ./uninstall_xvpn.sh"
   exit 1
fi

# Остановка сервисов
echo "Остановка сервисов..."
systemctl stop xvpn-api.service
systemctl stop xvpn-bot.service
systemctl stop xvpn-agent.service
systemctl stop xvpn-worker.service

# Отключение сервисов
echo "Отключение сервисов..."
systemctl disable xvpn-api.service
systemctl disable xvpn-bot.service
systemctl disable xvpn-agent.service
systemctl disable xvpn-worker.service

# Удаление контейнеров Docker
echo "Удаление контейнеров Docker..."
cd /home/xvpn/chatvpn
docker-compose down -v

# Удаление systemd сервисов
echo "Удаление systemd сервисов..."
rm -f /etc/systemd/system/xvpn-*.service
systemctl daemon-reload

# Удаление директорий
echo "Удаление директорий..."
rm -rf /home/xvpn/chatvpn
rm -rf /etc/xvpn
rm -rf /var/log/xvpn

# Удаление пользователя
if id "xvpn" &>/dev/null; then
    echo "Удаление пользователя xvpn..."
    userdel -r xvpn
fi

# Удаление Docker (опционально)
read -p "Удалить Docker? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Удаление Docker..."
    apt-get purge -y docker-ce docker-ce-cli containerd.io docker-compose
    rm -rf /var/lib/docker
fi

# Очистка
echo "Очистка..."
apt-get autoremove -y
apt-get clean

echo ""
echo "=== Деинсталляция XVPN завершена ==="
