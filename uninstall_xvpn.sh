#!/bin/bash
# XVPN Uninstall Script

echo "🔄 XVPN Uninstallation"

# Остановка сервисов
echo "🛑 Остановка сервисов..."
sudo systemctl stop xvpn-api xvpn-agent xvpn-bot xvpn-orchestrator xvpn-worker xvpn-api-pex xvpn-agent-pex 2>/dev/null || true
sudo systemctl disable xvpn-api xvpn-agent xvpn-bot xvpn-orchestrator xvpn-worker xvpn-api-pex xvpn-agent-pex 2>/dev/null || true

# Удаление сервисов
echo "🗑️ Удаление systemd сервисов..."
sudo rm -f /etc/systemd/system/xvpn-*.service
sudo systemctl daemon-reload
sudo systemctl reset-failed

# Удаление директорий
echo "📁 Удаление директорий..."
sudo rm -rf /opt/xvpn
sudo rm -rf /var/log/xvpn
sudo rm -rf /usr/local/etc/xray 2>/dev/null || true

# Удаление пользователя xvpn
echo "👥 Удаление пользователя xvpn..."
sudo userdel xvpn 2>/dev/null || true

# Удаление XRay (опционально)
# echo "🗑️ Удаление XRay..."
# bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove

# Очистка pip cache (опционально)
# pip cache purge 2>/dev/null || true

echo "✅ XVPN успешно удалён"