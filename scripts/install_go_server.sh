#!/bin/bash

# XVPN Go Server Installation Script
# This script installs and configures the XVPN Go server with systemd and Docker support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/xvpn/go-server"
DATA_DIR="/opt/xvpn/data"
LOG_DIR="/opt/xvpn/logs"
CONFIG_DIR="/opt/xvpn/config"
TLS_DIR="/opt/xvpn/tls"
USER_NAME="xvpn"
GROUP_NAME="xvpn"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

create_user() {
    log_info "Creating system user and group..."

    if ! id -u "$USER_NAME" >/dev/null 2>&1; then
        useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$USER_NAME"
        log_success "User $USER_NAME created"
    else
        log_warning "User $USER_NAME already exists"
    fi
}

create_directories() {
    log_info "Creating directories..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$TLS_DIR"

    chown -R "$USER_NAME:$GROUP_NAME" "$INSTALL_DIR"
    chown -R "$USER_NAME:$GROUP_NAME" "$DATA_DIR"
    chown -R "$USER_NAME:$GROUP_NAME" "$LOG_DIR"
    chown -R "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR"
    chown -R "$USER_NAME:$GROUP_NAME" "$TLS_DIR"

    chmod 755 "$INSTALL_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 700 "$TLS_DIR"

    log_success "Directories created and permissions set"
}

install_binary() {
    log_info "Installing XVPN Go server binary..."

    # Copy binary (assuming it's built and available)
    if [[ -f "./xvpn-server-go" ]]; then
        cp "./xvpn-server-go" "$INSTALL_DIR/"
        chown "$USER_NAME:$GROUP_NAME" "$INSTALL_DIR/xvpn-server-go"
        chmod 755 "$INSTALL_DIR/xvpn-server-go"
        log_success "Binary installed"
    else
        log_error "Binary ./xvpn-server-go not found. Please build it first."
        exit 1
    fi
}

generate_tls_certificates() {
    log_info "Generating TLS certificates..."

    if [[ ! -f "$TLS_DIR/server.crt" ]] || [[ ! -f "$TLS_DIR/server.key" ]]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$TLS_DIR/server.key" -out "$TLS_DIR/server.crt" -days 365 -nodes -subj "/CN=localhost"
        chown "$USER_NAME:$GROUP_NAME" "$TLS_DIR/server.crt" "$TLS_DIR/server.key"
        chmod 600 "$TLS_DIR/server.key"
        chmod 644 "$TLS_DIR/server.crt"
        log_success "TLS certificates generated"
    else
        log_warning "TLS certificates already exist"
    fi
}

create_config() {
    log_info "Creating configuration file..."

    cat > "$CONFIG_DIR/server.json" << EOF
{
  "server": {
    "port": 8443
  },
  "api": {
    "port": 8443,
    "base_path": "/api/v1"
  },
  "gateway": {
    "port": 8443,
    "base_path": "/gateway"
  },
  "database": {
    "path": "$DATA_DIR/xvpn.db"
  },
  "telegram": {
    "token": "${TELEGRAM_BOT_TOKEN:-your_bot_token_here}",
    "chat_id": "${TELEGRAM_CHAT_ID:-your_chat_id_here}"
  },
  "tls": {
    "cert_file": "$TLS_DIR/server.crt",
    "key_file": "$TLS_DIR/server.key"
  }
}
EOF

    chown "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR/server.json"
    chmod 644 "$CONFIG_DIR/server.json"

    log_success "Configuration file created"
}

install_systemd_service() {
    log_info "Installing systemd service..."

    cat > "/etc/systemd/system/xvpn-go-server.service" << EOF
[Unit]
Description=XVPN Go Server (API + Gateway + Bot)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/xvpn-server-go
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
Environment=XVPN_CONFIG_FILE=$CONFIG_DIR/server.json
Environment=XVPN_DATABASE_PATH=$DATA_DIR/xvpn.db
Environment=TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN}
Environment=TELEGRAM_CHAT_ID=\${TELEGRAM_CHAT_ID}
Environment=XVPN_TLS_CERT=$TLS_DIR/server.crt
Environment=XVPN_TLS_KEY=$TLS_DIR/server.key

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$DATA_DIR $LOG_DIR $CONFIG_DIR
ProtectHome=yes
PrivateDevices=yes

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xvpn-go-server

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable xvpn-go-server.service

    log_success "Systemd service installed and enabled"
}

setup_firewall() {
    log_info "Setting up firewall rules..."

    if command -v ufw >/dev/null 2>&1; then
        ufw allow 8443/tcp
        log_success "UFW firewall rule added"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --permanent --add-port=8443/tcp
        firewall-cmd --reload
        log_success "Firewalld rule added"
    else
        log_warning "No supported firewall detected. Please manually open port 8443/tcp"
    fi
}

create_env_file() {
    log_info "Creating environment file template..."

    cat > "$CONFIG_DIR/xvpn.env" << EOF
# XVPN Go Server Environment Variables
# Copy this file and set your actual values

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Server Configuration
XVPN_SERVER_PORT=8443
XVPN_DATABASE_PATH=$DATA_DIR/xvpn.db

# TLS Configuration
XVPN_TLS_CERT=$TLS_DIR/server.crt
XVPN_TLS_KEY=$TLS_DIR/server.key

# Optional: Custom config file
XVPN_CONFIG_FILE=$CONFIG_DIR/server.json
EOF

    chown "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR/xvpn.env"
    chmod 600 "$CONFIG_DIR/xvpn.env"

    log_success "Environment file template created"
}

print_completion_message() {
    log_success "XVPN Go Server installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit $CONFIG_DIR/xvpn.env with your actual values"
    echo "2. Source the environment: source $CONFIG_DIR/xvpn.env"
    echo "3. Start the service: sudo systemctl start xvpn-go-server"
    echo "4. Check status: sudo systemctl status xvpn-go-server"
    echo "5. View logs: sudo journalctl -u xvpn-go-server -f"
    echo
    echo "API will be available at: https://localhost:8443"
    echo "Health check: https://localhost:8443/health"
}

# Main installation process
main() {
    log_info "Starting XVPN Go Server installation..."

    check_root
    create_user
    create_directories
    install_binary
    generate_tls_certificates
    create_config
    install_systemd_service
    setup_firewall
    create_env_file

    print_completion_message
}

# Run main function
main "$@"