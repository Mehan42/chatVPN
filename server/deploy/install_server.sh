#!/bin/bash
set -e

echo "🚀 XVPN Server Automatic Deployment"
echo "===================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo ./install_server.sh"
    exit 1
fi

# Определение операционной системы
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ Cannot determine OS version"
    exit 1
fi

echo "🐧 Detected OS: $OS $VER"

# 1. Обновление системы
echo "📦 Updating system packages..."
case $OS in
    ubuntu|debian)
        apt update && apt upgrade -y
        ;;
    centos|rhel|fedora)
        yum update -y || dnf update -y
        ;;
    *)
        echo "⚠️ Unsupported OS: $OS"
        exit 1
        ;;
esac

# 2. Установка зависимостей
echo "📥 Installing dependencies..."
case $OS in
    ubuntu|debian)
        apt install -y python3 python3-pip curl unzip sqlite3 jq git openssl
        
        # Установка uv
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        ln -sf $HOME/.cargo/bin/uv /usr/local/bin/uv
        ;;
    centos|rhel|fedora)
        yum install -y python3 python3-pip curl unzip sqlite jq git openssl || \
        dnf install -y python3 python3-pip curl unzip sqlite jq git openssl
        
        # Установка uv
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        ln -sf $HOME/.cargo/bin/uv /usr/local/bin/uv
        ;;
esac

# 3. Проверка и создание структуры директорий
echo "📁 Creating directory structure..."
if [ ! -d "/opt/xvpn" ]; then
    mkdir -p /opt/xvpn/{api,agent/{db,knowledge,logs},admin,core,tls,logs}
fi

mkdir -p /etc/xvpn/tls

# 4. Запуск основного установочного скрипта
if [ -f "/opt/xvpn/install.sh" ]; then
    echo "🔧 Running main installation script..."
    chmod +x /opt/xvpn/install.sh
    /opt/xvpn/install.sh
else
    echo "❌ Main installation script not found at /opt/xvpn/install.sh"
    echo "Please ensure you have cloned the repository to /opt/xvpn/"
    exit 1
fi

# 5. Проверка файлов конфигурации
echo "🔍 Checking configuration files..."

if [ ! -f "/opt/xvpn/admin/.env" ]; then
    echo "⚠️ Creating example .env file..."
    cat > /opt/xvpn/admin/.env << 'ENVEOF'
# XVPN Telegram Bot Configuration
# Get these values and replace:

# 1. Get BOT_TOKEN from @BotFather on Telegram
BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# 2. Get CHAT_ID from @userinfobot on Telegram
CHAT_ID=YOUR_CHAT_ID_HERE

# API Configuration
API_BASE_URL=https://127.0.0.1:8443
API_TIMEOUT=10

# Logging
LOG_LEVEL=INFO
ENVEOF

    echo "📝 IMPORTANT: Edit /opt/xvpn/admin/.env with your Telegram bot credentials!"
    echo "   - Get BOT_TOKEN from @BotFather"
    echo "   - Get CHAT_ID from @userinfobot"
fi

# 6. Создание манифеста по умолчанию
if [ ! -f "/opt/xvpn/core/manifest.json" ]; then
    echo "📋 Creating default manifest..."
    mkdir -p /opt/xvpn/core
    cat > /opt/xvpn/core/manifest.json << 'MANIFEST_EOF'
{
  "version": "1.0",
  "updated": 1640995200,
  "transports": [
    {
      "id": "T0",
      "name": "Reality/WS+TLS",
      "type": "xray",
      "priority": 1,
      "config": {
        "server": "your-server-ip",
        "port": 443,
        "protocol": "vless",
        "uuid": "your-uuid-here"
      }
    },
    {
      "id": "T1",
      "name": "WireGuard-over-TLS",
      "type": "wireguard", 
      "priority": 2,
      "config": {
        "server": "your-server-ip",
        "port": 51820
      }
    }
  ]
}
MANIFEST_EOF
fi

# 7. Проверка и включение служб
echo "🔄 Enabling and starting services..."

systemctl daemon-reload

# Проверяем какие сервисы можем запустить
services_to_start=""

if systemctl list-unit-files | grep -q xvpn-api; then
    services_to_start="$services_to_start xvpn-api"
fi

if systemctl list-unit-files | grep -q xvpn-agent; then
    services_to_start="$services_to_start xvpn-agent"
fi

# Запускаем Telegram бота только если есть конфигурация
if [ -f "/opt/xvpn/admin/.env" ] && grep -q "YOUR_BOT_TOKEN" /opt/xvpn/admin/.env; then
    echo "⏭️ Skipping Telegram bot start (configuration needed)"
elif systemctl list-unit-files | grep -q xvpn-bot; then
    services_to_start="$services_to_start xvpn-bot"
fi

if [ -n "$services_to_start" ]; then
    echo "🚀 Starting services: $services_to_start"
    systemctl enable $services_to_start
    systemctl start $services_to_start
    
    echo "📊 Service status:"
    systemctl status $services_to_start --no-pager
fi

# 8. Проверка установки
echo "🔍 Running installation verification..."

# Проверка API
if systemctl is-active --quiet xvpn-api; then
    sleep 2
    if curl -sk https://127.0.0.1:8443/ >/dev/null 2>&1; then
        echo "✅ API is responding"
    else
        echo "⚠️ API is running but not responding"
    fi
else
    echo "⚠️ API service is not running"
fi

# Проверка базы данных
if [ -f "/opt/xvpn/agent/db/agent.db" ]; then
    echo "✅ Database created"
else
    echo "⚠️ Database not found"
fi

# Проверка файлов агентов
agents_check=0
for agent in api/app.py agent/agent.py admin/tg_bot.py; do
    if [ -f "/opt/xvpn/$agent" ]; then
        agents_check=$((agents_check + 1))
    fi
done

if [ $agents_check -eq 3 ]; then
    echo "✅ All agent files are present"
else
    echo "⚠️ Some agent files are missing ($agents_check/3)"
fi

echo ""
echo "🎉 XVPN Server Installation Complete!"
echo "====================================="
echo ""
echo "📋 Next Steps:"
echo "1. Configure Telegram Bot:"
echo "   sudo nano /opt/xvpn/admin/.env"
echo ""
echo "2. Configure VPN Core (Xray):"
echo "   sudo nano /etc/xvpn/xray.json"
echo ""
echo "3. Update server manifest:"
echo "   sudo nano /opt/xvpn/core/manifest.json"
echo ""
echo "4. Restart services after configuration:"
echo "   sudo systemctl restart xvpn-*"
echo ""
echo "5. Check status:"
echo "   sudo systemctl status xvpn-*"
echo "   curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health"
echo ""
echo "📖 Full documentation: /opt/xvpn/README.md"
echo ""
if systemctl is-active --quiet xvpn-api; then
    echo "🔗 API Health Check: https://$(curl -s ifconfig.me):8443/mcp/v1/vpn.health"
fi

# 9. Создание cron задачи для health monitoring
echo "⏰ Setting up health monitoring cron job..."
cat > /etc/cron.d/xvpn-health << 'CRON_EOF'
# XVPN Health Monitoring
*/5 * * * * root curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health >> /opt/xvpn/logs/cron_health.log 2>&1
CRON_EOF

echo "✅ Health monitoring cron job created"

# 10. Установка logrotate конфигурации
echo "🔄 Setting up log rotation..."
cat > /etc/logrotate.d/xvpn << 'LOGROTATE_EOF'
/opt/xvpn/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 root root
}

/opt/xvpn/agent/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 root root
}
LOGROTATE_EOF

echo "✅ Log rotation configured"

echo ""
echo "🔧 Installation Summary:"
echo "========================"
echo "• Directory: /opt/xvpn/"
echo "• Database: /opt/xvpn/agent/db/agent.db"
echo "• Logs: /opt/xvpn/logs/ and /opt/xvpn/agent/logs/"
echo "• Services: xvpn-api, xvpn-agent, xvpn-bot"
echo "• Health monitoring: /etc/cron.d/xvpn-health"
echo "• Log rotation: /etc/logrotate.d/xvpn"
echo ""
echo "🎯 Ready to configure and use XVPN!"
