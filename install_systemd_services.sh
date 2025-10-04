#!/bin/bash

# XVPN Systemd Services Installer
# Установщик systemd служб XVPN

set -e  # Выход при любой ошибке

echo "🚀 Installing XVPN Systemd Services..."
echo "====================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Создание пользователя xvpn если его нет
echo "👤 Creating xvpn user..."
if ! id "xvpn" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/xvpn xvpn
    echo "✅ Created xvpn user"
else
    echo "✅ xvpn user already exists"
fi

# Создание необходимых директорий
echo "📁 Creating directories..."
mkdir -p /opt/xvpn/{data,logs,config,db,clients,transports}
mkdir -p /var/log/xvpn
chown -R xvpn:xvpn /opt/xvpn /var/log/xvpn

# Копирование systemd unit файлов
echo "📋 Copying systemd unit files..."
cp systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# Установка прав на unit файлы
chmod 644 /etc/systemd/system/xvpn-*.service

# Включение служб
echo "⚙️ Enabling services..."
systemctl enable xvpn-api.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-bot.service
systemctl enable xvpn-worker.service
systemctl enable xvpn-orchestrator.service
systemctl enable xvpn-client.service

# Запуск служб
echo "🚀 Starting services..."
systemctl start xvpn-api.service
systemctl start xvpn-agent.service
systemctl start xvpn-bot.service
systemctl start xvpn-worker.service
systemctl start xvpn-orchestrator.service
systemctl start xvpn-client.service

# Проверка статуса служб
echo "🔍 Checking service status..."
systemctl status xvpn-api.service --no-pager || true
systemctl status xvpn-agent.service --no-pager || true
systemctl status xvpn-bot.service --no-pager || true
systemctl status xvpn-worker.service --no-pager || true
systemctl status xvpn-orchestrator.service --no-pager || true
systemctl status xvpn-client.service --no-pager || true

echo "✅ XVPN Systemd Services installed successfully!"
echo ""
echo "📋 To check service status:"
echo "   systemctl status xvpn-*"
echo ""
echo "📋 To view logs:"
echo "   journalctl -u xvpn-api -f"
echo "   journalctl -u xvpn-agent -f"
echo "   journalctl -u xvpn-bot -f"
echo "   journalctl -u xvpn-worker -f"
echo "   journalctl -u xvpn-orchestrator -f"
echo "   journalctl -u xvpn-client -f"
echo ""
echo "📋 To stop services:"
echo "   systemctl stop xvpn-*"
echo ""
echo "📋 To restart services:"
echo "   systemctl restart xvpn-*"