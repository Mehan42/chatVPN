#!/bin/bash
set -e

echo "🚀 XVPN Server Installation Script"
echo "=================================="

# 1. Зависимости
echo "📦 Installing dependencies..."
apt update
apt install -y python3 python3-pip curl unzip sqlite3 uv jq

# 2. Создание директорий
echo "📁 Creating directory structure..."
mkdir -p /opt/xvpn/{api,agent/{db,knowledge,logs},admin,core,tls,logs}
mkdir -p /etc/xvpn/tls

# 3. Заготовка БД
echo "🗃️ Creating SQLite database..."
sqlite3 /opt/xvpn/agent/db/agent.db <<'DBEOF'
CREATE TABLE IF NOT EXISTS protocols (
  id INTEGER PRIMARY KEY,
  name TEXT,
  situation TEXT,
  steps TEXT,
  updated_at INTEGER
);
CREATE TABLE IF NOT EXISTS fallback (
  id INTEGER PRIMARY KEY,
  type TEXT,
  value TEXT,
  priority INTEGER DEFAULT 100,
  notes TEXT
);
CREATE TABLE IF NOT EXISTS logs (
  ts INTEGER,
  component TEXT,
  state TEXT,
  action TEXT,
  result TEXT,
  details TEXT
);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);
DBEOF

# 4. systemd юниты
echo "⚙️ Creating systemd units..."

cat >/etc/systemd/system/xvpn-core.service <<'UNITEOF'
[Unit]
Description=XVPN Core (Xray)
After=network.target

[Service]
ExecStart=/usr/bin/xray -config /etc/xvpn/xray.json
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

cat >/etc/systemd/system/xvpn-api.service <<'UNITEOF'
[Unit]
Description=XVPN Control API
After=network.target

[Service]
WorkingDirectory=/opt/xvpn/api
ExecStart=/usr/bin/uv run /opt/xvpn/api/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNITEOF

cat >/etc/systemd/system/xvpn-agent.service <<'UNITEOF'
[Unit]
Description=XVPN Agent
After=network.target

[Service]
WorkingDirectory=/opt/xvpn/agent
ExecStart=/usr/bin/uv run /opt/xvpn/agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNITEOF

cat >/etc/systemd/system/xvpn-bot.service <<'UNITEOF'
[Unit]
Description=XVPN Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/xvpn/admin
EnvironmentFile=/opt/xvpn/admin/.env
ExecStart=/usr/bin/uv run /opt/xvpn/admin/tg_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNITEOF

# 5. Создание самоподписанного сертификата для разработки
echo "🔐 Creating self-signed certificate..."
if [ ! -f /opt/xvpn/api/tls/selfsigned.crt ]; then
    mkdir -p /opt/xvpn/api/tls
    openssl req -x509 -newkey rsa:4096 -keyout /opt/xvpn/api/tls/selfsigned.key -out /opt/xvpn/api/tls/selfsigned.crt -days 365 -nodes -subj "/CN=localhost"
fi

# 6. Права доступа
echo "🔒 Setting permissions..."
chown -R root:root /opt/xvpn
chmod -R 755 /opt/xvpn
chmod 600 /opt/xvpn/agent/db/agent.db
chmod 600 /opt/xvpn/api/tls/selfsigned.key

# 7. Enable services (но не запускаем пока не созданы файлы)
systemctl daemon-reload

echo "✅ Install complete!"
echo ""
echo "Next steps:"
echo "1. Configure Xray: /etc/xvpn/xray.json"
echo "2. Configure Telegram Bot: /opt/xvpn/admin/.env"
echo "3. Start services: systemctl start xvpn-api xvpn-agent xvpn-bot"
echo "4. Check status: systemctl status xvpn-*"
