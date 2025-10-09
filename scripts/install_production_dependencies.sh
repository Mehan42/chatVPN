#!/usr/bin/env bash
"""
XVPN Production Server Dependencies Installer
Installs all required dependencies for XVPN on production server
"""

set -e

echo "📦 XVPN Production Server Dependencies Installer"
echo "================================================"

# Configuration
XVPN_HOME="/opt/xvpn"
XVPN_USER="xvpn"
XVPN_GROUP="xvpn"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    echo "Try: sudo $0"
    exit 1
fi

# Update package list
print_warning "Updating package list..."
apt update

# Install system dependencies
print_warning "Installing system dependencies..."
apt install -y \
    python3 python3-pip python3-venv \
    curl wget jq \
    docker docker-compose \
    nginx \
    openssl \
    sqlite3 \
    systemd \
    git

# Create XVPN user and group
print_warning "Creating XVPN user and group..."
if ! id "$XVPN_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$XVPN_HOME" "$XVPN_USER"
fi

if ! getent group "$XVPN_GROUP" &>/dev/null; then
    groupadd -r "$XVPN_GROUP"
fi

# Add user to group
usermod -a -G "$XVPN_GROUP" "$XVPN_USER"

# Create directories
print_warning "Creating XVPN directories..."
mkdir -p "$XVPN_HOME"/{api,agent,bot,data,logs,tls,config,clients}
mkdir -p "$XVPN_HOME"/data/{clients,transports,users}
mkdir -p "$XVPN_HOME"/logs/{api,agent,bot,client}
mkdir -p "$XVPN_HOME"/tls/{certs,keys}
mkdir -p "$XVPN_HOME"/config/{api,agent,bot,client}

# Set permissions
print_warning "Setting directory permissions..."
chown -R "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME"
chmod 750 "$XVPN_HOME"
chmod 640 "$XVPN_HOME"/config/*
chmod 600 "$XVPN_HOME"/tls/*

# Create virtual environment
print_warning "Creating Python virtual environment..."
python3 -m venv "$XVPN_HOME/venv"
chown -R "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME/venv"

# Activate virtual environment
source "$XVPN_HOME/venv/bin/activate"

# Install Python dependencies
print_warning "Installing Python dependencies..."
pip install --upgrade pip
pip install flask flask-cors flask-limiter requests psutil pyyaml
pip install cryptography pyopenssl
pip install sqlite3
pip install aiohttp asyncio
pip install numpy pandas scikit-learn
pip install langchain langchain-community langchain-core
pip install prometheus-client elasticsearch
pip install kubernetes docker paramiko
pip install torch transformers accelerate bitsandbytes

# Create systemd service files
print_warning "Creating systemd service files..."
cat > /etc/systemd/system/xvpn-api.service << 'EOF'
[Unit]
Description=XVPN API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn/api
ExecStart=/opt/xvpn/venv/bin/python /opt/xvpn/api/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
RemoveIPC=true

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/xvpn-agent.service << 'EOF'
[Unit]
Description=XVPN Agent Service
After=network.target xvpn-api.service
Requires=xvpn-api.service

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn/agent
ExecStart=/opt/xvpn/venv/bin/python /opt/xvpn/agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
RemoveIPC=true

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/xvpn-bot.service << 'EOF'
[Unit]
Description=XVPN Telegram Bot Service
After=network.target xvpn-api.service
Requires=xvpn-api.service

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn/bot
EnvironmentFile=/opt/xvpn/config/bot/.env
ExecStart=/opt/xvpn/venv/bin/python /opt/xvpn/bot/__main__.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
RemoveIPC=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
print_warning "Reloading systemd..."
systemctl daemon-reload

# Enable services
print_warning "Enabling systemd services..."
systemctl enable xvpn-api.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-bot.service

# Generate TLS certificates
print_warning "Generating TLS certificates..."
mkdir -p "$XVPN_HOME/tls"
openssl req -x509 -newkey rsa:4096 -keyout "$XVPN_HOME/tls/key.pem" -out "$XVPN_HOME/tls/cert.pem" -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=XVPN/OU=IT/CN=localhost/emailAddress=admin@xvpn.local"

# Set certificate permissions
chown root:root "$XVPN_HOME/tls/cert.pem" "$XVPN_HOME/tls/key.pem"
chmod 644 "$XVPN_HOME/tls/cert.pem"
chmod 600 "$XVPN_HOME/tls/key.pem"

# Generate API tokens
print_warning "Generating API tokens..."
"$XVPN_HOME/venv/bin/python" -c "
import os
import json
import secrets
import time
from pathlib import Path

# Generate secure tokens
admin_token = secrets.token_urlsafe(32)
client_token = secrets.token_urlsafe(32)

# Create tokens data
tokens = {
    'admin': {
        'token': admin_token,
        'permissions': ['admin', 'read', 'write'],
        'created_at': time.time(),
        'expires_at': None,
        'description': 'Default admin token'
    },
    'client': {
        'token': client_token,
        'permissions': ['read'],
        'created_at': time.time(),
        'expires_at': None,
        'description': 'Default client token'
    }
}

# Save tokens
tokens_file = Path('/opt/xvpn/data/api_tokens.json')
tokens_file.parent.mkdir(parents=True, exist_ok=True)

with open(tokens_file, 'w') as f:
    json.dump(tokens, f, indent=2)

print(f'Admin token: {admin_token}')
print(f'Client token: {client_token}')
print(f'Tokens saved to: {tokens_file}')
"

# Final checks
print_warning "Performing final checks..."
if systemctl is-active --quiet xvpn-api.service; then
    print_status "XVPN API service is active"
else
    print_warning "XVPN API service is not active (will start on next boot)"
fi

if systemctl is-active --quiet xvpn-agent.service; then
    print_status "XVPN Agent service is active"
else
    print_warning "XVPN Agent service is not active (will start on next boot)"
fi

if systemctl is-active --quiet xvpn-bot.service; then
    print_status "XVPN Bot service is active"
else
    print_warning "XVPN Bot service is not not active (will start on next boot)"
fi

# Summary
echo ""
echo "================================================"
echo "📊 XVPN Production Server Dependencies Summary"
echo "================================================"
echo ""
print_status "System dependencies installed"
print_status "Python dependencies installed"
print_status "XVPN user and group created"
print_status "Directories created with proper permissions"
print_status "Systemd services configured and enabled"
print_status "TLS certificates generated"
print_status "API tokens generated"
echo ""
echo "💡 Next steps:"
echo "   1. Start services: sudo systemctl start xvpn-api xvpn-agent xvpn-bot"
echo "   2. Check status: sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
echo "   3. Test HTTPS: curl -k https://localhost:8443/mcp/v1/vpn.health"
echo "   4. Configure firewall: sudo ufw allow 443/tcp"
echo ""
echo "📁 Important directories:"
echo "   XVPN home: $XVPN_HOME"
echo "   TLS certificates: $XVPN_HOME/tls/"
echo "   API tokens: $XVPN_HOME/data/api_tokens.json"
echo "   Logs: $XVPN_HOME/logs/"
echo ""
print_status "XVPN production server dependencies installed successfully!"
echo "🚀 XVPN is ready for production deployment!"