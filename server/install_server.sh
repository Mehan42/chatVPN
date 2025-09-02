#!/bin/bash
set -euo pipefail

# ================================
# ChatVPN Server Installer
# Порты: Xray=8443, BotAPI=8081, Health=9090
# ================================

echo "[1/6] Обновление системы..."
sudo apt update -y
sudo apt upgrade -y

echo "[2/6] Установка зависимостей..."
sudo apt install -y python3 python3-venv unzip curl wget jq

echo "[3/6] Создание директорий..."
sudo mkdir -p /opt/xvpn
sudo mkdir -p /opt/xvpn/data
sudo mkdir -p /opt/xvpn/xray
sudo mkdir -p /var/log/xvpn
sudo chown -R $USER:$USER /opt/xvpn

echo "[4/6] Установка Xray на порт 8443..."
XRAY_VERSION="25.6.8"
wget -qO /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip
unzip -o /tmp/xray.zip -d /opt/xvpn/xray
rm -f /tmp/xray.zip

# Базовый конфиг XRAY (8443)
cat > /opt/xvpn/data/config.json <<EOF
{
  "inbounds": [
    {
      "port": 8443,
      "protocol": "vless",
      "settings": {
        "clients": []
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality"
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
EOF

echo "[5/6] Установка systemd сервисов..."

# === XRAY ===
cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray core (ChatVPN)
After=network.target

[Service]
ExecStart=/opt/xvpn/xray/xray run -c /opt/xvpn/data/config.json
Restart=always
User=nobody
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

# === ChatVPN Bot ===
cat > /etc/systemd/system/server_bot.service <<EOF
[Unit]
Description=ChatVPN Server Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/xvpn/server_bot.pyz --server-ip $(hostname -I | awk '{print $1}') --port 8081
WorkingDirectory=/opt/xvpn
Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Перезапуск systemd..."
sudo systemctl daemon-reload
sudo systemctl enable xray
sudo systemctl enable server_bot

echo "=== Установка завершена ==="
echo "Проверьте сервисы:"
echo "  sudo systemctl status xray --no-pager"
echo "  sudo systemctl status server_bot --no-pager"
echo
echo "Xray порт: 8443"
echo "Bot API порт: 8081"
echo "Healthcheck порт: 9090 (зарезервирован)"
