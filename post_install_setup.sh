#!/bin/bash
# XVPN Post-Installation Setup Script
# Скрипт автоматической настройки после установки XVPN

set -e

echo "🔧 XVPN Post-Installation Setup"

# Проверка, что мы находимся в правильной директории
if [ ! -f "README.md" ]; then
    echo "❌ Пожалуйста, запустите скрипт из корневой директории репозитория"
    exit 1
fi

# Обновление репозитория
echo "📥 Обновление репозитория..."
git pull

# Настройка фаервола
echo "🛡️ Настройка фаервола..."
if command -v ufw &> /dev/null; then
    echo "  Открытие портов в фаерволе..."
    # Порт 443 для XRay (VPN трафик)
    sudo ufw allow 443/tcp || echo "⚠️ Не удалось открыть порт 443"
    # Порт 8443 для MCP/API (управление) - уже должен быть открыт
    sudo ufw allow 8443/tcp || echo "⚠️ Не удалось открыть порт 8443"
    echo "  ✅ Порты 443 и 8443 настроены в фаерволе"
else
    echo "  ℹ️ UFW не найден, пропускаем настройку фаервола"
fi

# Обновление конфигурации API сервера
echo "📋 Обновление конфигурации API сервера..."
sudo mkdir -p /opt/xvpn/server/api

# Создание резервной копии существующей конфигурации
if [ -f "/opt/xvpn/server/api/config.json" ]; then
    sudo cp /opt/xvpn/server/api/config.json /opt/xvpn/server/api/config.json.backup.$(date +%Y%m%d_%H%M%S)
    echo "  💾 Создана резервная копия конфигурации API"
fi

# Копирование обновленной конфигурации
sudo cp server/api/config.json /opt/xvpn/server/api/config.json
sudo chown xvpn:xvpn /opt/xvpn/server/api/config.json
sudo chmod 644 /opt/xvpn/server/api/config.json
echo "  ✅ Конфигурация API сервера обновлена"

# Обновление systemd сервисов
echo "⚙️ Обновление systemd сервисов..."
if [ -f "server/api.service" ]; then
    sudo cp server/api.service /etc/systemd/system/xvpn-api.service
    sudo cp server/agent.service /etc/systemd/system/xvpn-agent.service
    sudo cp server/orchestrator.service /etc/systemd/system/xvpn-orchestrator.service
    sudo systemctl daemon-reload
    echo "  ✅ Systemd сервисы обновлены"
fi

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."
sudo systemctl restart xvpn-api xvpn-agent xvpn-orchestrator 2>/dev/null || echo "⚠️ Некоторые сервисы не перезапущены"

# Включение автозапуска
echo "🔁 Включение автозапуска сервисов..."
sudo systemctl enable xvpn-api xvpn-agent xvpn-orchestrator 2>/dev/null || echo "⚠️ Не удалось включить автозапуск некоторых сервисов"

# Проверка статуса
echo "🔍 Проверка статуса сервисов..."
echo "  API Server:"
sudo systemctl is-active xvpn-api --quiet && echo "    ✅ xvpn-api: active" || echo "    ❌ xvpn-api: inactive"
echo "  Agent:"
sudo systemctl is-active xvpn-agent --quiet && echo "    ✅ xvpn-agent: active" || echo "    ❌ xvpn-agent: inactive"
echo "  Orchestrator:"
sudo systemctl is-active xvpn-orchestrator --quiet && echo "    ✅ xvpn-orchestrator: active" || echo "    ❌ xvpn-orchestrator: inactive"

echo ""
echo "✅ Автоматическая настройка XVPN завершена!"
echo ""
echo "ℹ️  Информация о портах:"
echo "   Порт 443: XRay VPN трафик"
echo "   Порт 8443: MCP/API интерфейс управления"
echo ""
echo "🌐 Для проверки работы API используйте:"
echo "   curl -k https://localhost:8443/mcp/v1/vpn.health"
echo ""
echo "📝 Дополнительная информация:"
echo "   Логи API сервера: sudo journalctl -u xvpn-api -f"
echo "   Логи агента: sudo journalctl -u xvpn-agent -f"
echo "   Логи оркестратора: sudo journalctl -u xvpn-orchestrator -f"