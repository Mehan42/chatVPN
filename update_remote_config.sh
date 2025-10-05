#!/bin/bash
# XVPN Remote Server Update Script
# Скрипт для обновления конфигурации на удаленном сервере

set -e

echo "🔄 XVPN Remote Server Update"

# Проверка, что мы находимся в правильной директории
if [ ! -f "README.md" ]; then
    echo "❌ Пожалуйста, запустите скрипт из корневой директории репозитория"
    exit 1
fi

# Обновление репозитория
echo "📥 Обновление репозитория..."
git pull

# Копирование обновленных файлов конфигурации
echo "📋 Копирование обновленных файлов конфигурации..."

# Создание резервных копий существующих конфигов (если есть)
if [ -f "/opt/xvpn/server/api/config.json" ]; then
    sudo cp /opt/xvpn/server/api/config.json /opt/xvpn/server/api/config.json.backup.$(date +%Y%m%d_%H%M%S)
    echo "💾 Создана резервная копия конфигурации API"
fi

# Обновление конфигурации API сервера
sudo mkdir -p /opt/xvpn/server/api
sudo cp server/api/config.json /opt/xvpn/server/api/config.json
sudo chown xvpn:xvpn /opt/xvpn/server/api/config.json
sudo chmod 644 /opt/xvpn/server/api/config.json
echo "✅ Конфигурация API сервера обновлена"

# Обновление systemd сервисов
if [ -f "server/api.service" ]; then
    sudo cp server/api.service /etc/systemd/system/xvpn-api.service
    sudo cp server/agent.service /etc/systemd/system/xvpn-agent.service
    sudo cp server/orchestrator.service /etc/systemd/system/xvpn-orchestrator.service
    sudo systemctl daemon-reload
    echo "✅ Systemd сервисы обновлены"
fi

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."
sudo systemctl restart xvpn-api xvpn-agent xvpn-orchestrator

# Проверка статуса
echo "🔍 Проверка статуса сервисов..."
sudo systemctl status xvpn-api --no-pager || echo "⚠️  xvpn-api не запущен"
sudo systemctl status xvpn-agent --no-pager || echo "⚠️  xvpn-agent не запущен"
sudo systemctl status xvpn-orchestrator --no-pager || echo "⚠️  xvpn-orchestrator не запущен"

echo "✅ Обновление конфигурации завершено!"

# Информация о портах
echo ""
echo "ℹ️  Информация о портах:"
echo "   Порт 443: XRay VPN трафик"
echo "   Порт 8443: MCP/API интерфейс управления"
echo ""
echo "🌐 Для проверки работы API используйте:"
echo "   curl -k https://localhost:8443/mcp/v1/vpn.health"