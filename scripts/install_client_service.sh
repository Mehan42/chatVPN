#!/bin/bash

# Установка клиентского systemd-сервиса XVPN
# Абсолютный путь: ~/chatvpn/scripts/install_client_service.sh

set -e

echo "=== Установка клиентского systemd-сервиса XVPN ==="

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   exit 1
fi

# Директория установки
INSTALL_DIR="/home/chatvpn/client"
SERVICE_FILE="/etc/systemd/system/xvpn-client.service"
LOG_DIR="/var/log/chatvpn"

# Проверка существования директории
if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "Ошибка: Директория $INSTALL_DIR не существует"
    exit 1
fi

# Создание пользователя и группы (если не существуют)
if ! id "chatvpn" &>/dev/null; then
    echo "Создание пользователя chatvpn..."
    useradd -r -s /bin/false -d "$INSTALL_DIR" chatvpn
fi

# Создание директории логов
mkdir -p "$LOG_DIR"
chown chatvpn:chatvpn "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Копирование файла сервиса
echo "Установка файла сервиса..."
cp systemd/xvpn-client.service "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

# Установка прав на директорию клиента
chown -R chatvpn:chatvpn "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"

# Включение и запуск сервиса
echo "Включение сервиса..."
systemctl daemon-reload
systemctl enable xvpn-client.service

echo "=== Установка завершена ==="
echo ""
echo "Для управления сервисом используйте:"
echo "  sudo systemctl start xvpn-client.service"
echo "  sudo systemctl stop xvpn-client.service"
echo "  sudo systemctl restart xvpn-client.service"
echo "  sudo systemctl status xvpn-client.service"
echo ""
echo "Для просмотра логов:"
echo "  sudo journalctl -u xvpn-client.service -f"
echo ""
echo "Проверка статуса:"
systemctl is-enabled xvpn-client.service