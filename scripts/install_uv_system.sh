#!/bin/bash

# XVPN uv Installation Script
# Version: 1.0
# Author: XVPN Team
# Description: System-wide installation of uv and setup for XVPN

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
XVPN_USER="xvpn"
XVPN_DIR="/opt/xvpn"
LOG_FILE="/var/log/xvpn_uv_install.log"

# Logging function
log() {
    echo -e "$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Error handling
error_exit() {
    log "${RED}❌ Error: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error_exit "This script must be run as root. Use sudo."
fi

log "${BLUE}🚀 Starting XVPN uv installation...${NC}"

# Update package list
log "${BLUE}📦 Updating package list...${NC}"
apt-get update || error_exit "Failed to update package list"

# Install system dependencies
log "${BLUE}🔧 Installing system dependencies...${NC}"
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    || error_exit "Failed to install system dependencies"

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    log "${BLUE}🦀 Installing Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    export PATH="$HOME/.cargo/bin:$PATH"
else
    log "${GREEN}✅ Rust is already installed${NC}"
fi

# Install uv
log "${BLUE}📦 Installing uv package manager...${NC}"
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to system PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Verify uv installation
if ! command -v uv &> /dev/null; then
    error_exit "Failed to install uv"
fi

log "${GREEN}✅ uv installed successfully${NC}"

# Create system symlinks for uv and uvx
log "${BLUE}🔗 Creating system symlinks...${NC}"
ln -sf "$HOME/.cargo/bin/uv" "/usr/local/bin/uv"
ln -sf "$HOME/.cargo/bin/uvx" "/usr/local/bin/uvx"

# Verify system symlinks
if ! command -v uvx &> /dev/null; then
    error_exit "Failed to create uvx symlink"
fi

log "${GREEN}✅ System symlinks created successfully${NC}"

# Install pipx for additional package management
log "${BLUE}📦 Installing pipx...${NC}"
python3 -m pip install --upgrade pipx
pipx ensurepath

# Install uv completions
log "${BLUE}📝 Installing shell completions...${NC}"
uv --generate-shell-completion bash > /etc/bash_completion.d/uv
uv --generate-shell-completion zsh > /usr/share/zsh/vendor-completions/_uv
uvx --generate-shell-completion bash > /etc/bash_completion.d/uvx
uvx --generate-shell-completion zsh > /usr/share/zsh/vendor-completions/_uvx

# Create XVPN user if it doesn't exist
if ! id "$XVPN_USER" &>/dev/null; then
    log "${BLUE}👤 Creating XVPN user...${NC}"
    useradd -r -s /bin/false -d "$XVPN_DIR" "$XVPN_USER"
    log "${GREEN}✅ XVPN user created${NC}"
else
    log "${GREEN}✅ XVPN user already exists${NC}"
fi

# Create XVPN directory structure
log "${BLUE}📁 Creating XVPN directory structure...${NC}"
mkdir -p "$XVPN_DIR"
mkdir -p "$XVPN_DIR/logs"
mkdir -p "$XVPN_DIR/pids"
mkdir -p "$XVPN_DIR/config"
mkdir -p "$XVPN_DIR/data"
mkdir -p "$XVPN_DIR/backups"

# Set correct permissions
chown -R "$XVPN_USER:$XVPN_USER" "$XVPN_DIR"
chmod 755 "$XVPN_DIR"
chmod 644 "$XVPN_DIR"/*.py 2>/dev/null || true

# Install Python dependencies using uv
log "${BLUE}📦 Installing Python dependencies...${NC}"

# Switch to XVPN user for dependency installation
sudo -u "$XVPN_USER" bash << 'EOF'
cd "$XVPN_DIR"

# Install uv for the user
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Install basic Python dependencies
uv pip install --system \
    flask \
    requests \
    pydantic \
    python-dotenv \
    click \
    rich \
    psutil \
    aiohttp \
    uvloop \
    orjson || exit 1

# Install server dependencies
uv pip install --system \
    fastapi \
    uvicorn \
    gunicorn \
    sqlalchemy \
    alembic \
    redis \
    celery \
    flower || exit 1

# Install agent dependencies
uv pip install --system \
    openai \
    langchain \
    chromadb \
    tiktoken \
    sentence-transformers \
    faiss-cpu \
    numpy \
    pandas || exit 1

# Install bot dependencies
uv pip install --system \
    python-telegram-bot \
    aiogram \
    pydantic-settings || exit 1

# Install monitoring dependencies
uv pip install --system \
    prometheus-client \
    grafana-api \
    structlog \
    loguru \
    rich-argparse || exit 1

# Install development dependencies
uv pip install --system \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    black \
    isort \
    flake8 \
    mypy \
    pre-commit \
    bandit \
    safety || exit 1

EOF

if [ $? -ne 0 ]; then
    error_exit "Failed to install Python dependencies"
fi

log "${GREEN}✅ Python dependencies installed successfully${NC}"

# Create systemd services
log "${BLUE}🔧 Creating systemd services...${NC}"

# API service
cat > /etc/systemd/system/xvpn-api.service << EOF
[Unit]
Description=XVPN API Service with uv
After=network.target
Requires=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
ExecStart=/usr/local/bin/uvx run --app server.api.main:app
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=$XVPN_DIR/src:$XVPN_DIR/server
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=false
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Agent service
cat > /etc/systemd/system/xvpn-agent.service << EOF
[Unit]
Description=XVPN Agent Service with uv
After=network.target
Requires=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
ExecStart=/usr/local/bin/uvx run --app server.agent.main:agent
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=$XVPN_DIR/src:$XVPN_DIR/server/agent
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Bot service
cat > /etc/systemd/system/xvpn-bot.service << EOF
[Unit]
Description=XVPN Bot Service with uv
After=network.target
Requires=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
ExecStart=/usr/local/bin/uvx run --app server.admin.main:bot
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=$XVPN_DIR/src:$XVPN_DIR/server/admin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Worker service
cat > /etc/systemd/system/xvpn-worker.service << EOF
[Unit]
Description=XVPN Worker Service with uv
After=network.target
Requires=network.target

[Service]
Type=simple
User=$XVPN_USER
Group=$XVPN_USER
WorkingDirectory=$XVPN_DIR
ExecStart=/usr/local/bin/uvx run --app server.worker.main:worker
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=$XVPN_DIR/src:$XVPN_DIR/server
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable xvpn-api.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-bot.service
systemctl enable xvpn-worker.service

log "${GREEN}✅ Systemd services created and enabled${NC}"

# Create configuration files
log "${BLUE}📝 Creating configuration files...${NC}"

# Create .env file
cat > "$XVPN_DIR/.env" << EOF
# XVPN Configuration
FLASK_ENV=production
FLASK_DEBUG=false
PYTHONUNBUFFERED=1
DATABASE_URL=sqlite:///data/xvpn.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
XVPN_CONFIG_DIR=$XVPN_DIR/config
XVPN_DATA_DIR=$XVPN_DIR/data
XVPN_LOG_DIR=$XVPN_DIR/logs
EOF

# Set proper permissions
chown "$XVPN_USER:$XVPN_USER" "$XVPN_DIR/.env"
chmod 600 "$XVPN_DIR/.env"

log "${GREEN}✅ Configuration files created${NC}"

# Create installation verification script
cat > "$XVPN_DIR/verify_installation.sh" << 'EOF'
#!/bin/bash
# XVPN Installation Verification Script

echo "🔍 Verifying XVPN installation..."

# Check uv installation
if command -v uv &> /dev/null && command -v uvx &> /dev/null; then
    echo "✅ uv and uvx are installed"
    echo "   uv version: $(uv --version)"
else
    echo "❌ uv/uvx not found"
    exit 1
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
dependencies=("flask" "requests" "pydantic" "fastapi" "uvicorn" "prometheus-client")
for dep in "${dependencies[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo "✅ $dep"
    else
        echo "❌ $dep missing"
    fi
done

# Check systemd services
echo "🔧 Checking systemd services..."
services=("xvpn-api" "xvpn-agent" "xvpn-bot" "xvpn-worker")
for service in "${services[@]}"; do
    if systemctl is-enabled "$service" &>/dev/null; then
        echo "✅ $service is enabled"
    else
        echo "❌ $service is not enabled"
    fi
done

echo "✅ Verification completed"
EOF

chmod +x "$XVPN_DIR/verify_installation.sh"
chown "$XVPN_USER:$XVPN_USER" "$XVPN_DIR/verify_installation.sh"

# Create post-installation instructions
cat > "$XVPN_DIR/POST_INSTALL.md" << EOF
# XVPN Installation Complete

## Next Steps

1. **Verify Installation**
   \`\`\`bash
   sudo -u xvpn $XVPN_DIR/verify_installation.sh
   \`\`\`

2. **Copy Configuration Files**
   Copy configuration templates from \`config/\` to \`/opt/xvpn/config/\` and modify as needed.

3. **Start Services**
   \`\`\`bash
   sudo systemctl start xvpn-api
   sudo systemctl start xvpn-agent
   sudo systemctl start xvpn-bot
   sudo systemctl start xvpn-worker
   \`\`\`

4. **Check Service Status**
   \`\`\`bash
   sudo systemctl status xvpn-api
   sudo systemctl status xvpn-agent
   sudo systemctl status xvpn-bot
   sudo systemctl status xvpn-worker
   \`\`\`

5. **View Logs**
   \`\`\`bash
   journalctl -u xvpn-api -f
   journalctl -u xvpn-agent -f
   journalctl -u xvpn-bot -f
   journalctl -u xvpn-worker -f
   \`\`\`

## Management Commands

- **Start all services**: \`sudo systemctl start xvpn-*\`
- **Stop all services**: \`sudo systemctl stop xvpn-*\`
- **Restart all services**: \`sudo systemctl restart xvpn-*\`
- **Enable auto-start**: \`sudo systemctl enable xvpn-*\`

## Configuration

Edit files in \`/opt/xvpn/config/\` to customize your XVPN installation.

## Troubleshooting

Check the installation log: \`/var/log/xvpn_uv_install.log\`

## Support

For issues, check the GitHub repository or contact support.
EOF

chown "$XVPN_USER:$XVPN_USER" "$XVPN_DIR/POST_INSTALL.md"

log "${GREEN}✅ Post-installation instructions created${NC}"

# Final verification
log "${BLUE}🔍 Performing final verification...${NC}"

# Test uv command
if uv --version > /dev/null 2>&1; then
    log "${GREEN}✅ uv is working correctly${NC}"
else
    error_exit "Verification failed: uv is not working"
fi

# Test uvx command
if uvx --version > /dev/null 2>&1; then
    log "${GREEN}✅ uvx is working correctly${NC}"
else
    error_exit "Verification failed: uvx is not working"
fi

# Test Python imports
python3 -c "import flask; import requests; import pydantic" || error_exit "Verification failed: Python imports failed"

log "${GREEN}✅ Final verification completed successfully${NC}"

log "${GREEN}🎉 XVPN uv installation completed successfully!${NC}"
log "${BLUE}📋 Next steps:${NC}"
log "${BLUE}   1. Review: $XVPN_DIR/POST_INSTALL.md${NC}"
log "${BLUE}   2. Configure: Edit files in $XVPN_DIR/config/${NC}"
log "${BLUE}   3. Start services: systemctl start xvpn-*${NC}"
log "${BLUE}   4. Verify: sudo -u xvpn $XVPN_DIR/verify_installation.sh${NC}"

# Display summary
echo ""
echo "📊 Installation Summary:"
echo "   📁 XVPN Directory: $XVPN_DIR"
echo "   👤 User: $XVPN_USER"
echo "   🔧 Services: xvpn-api, xvpn-agent, xvpn-bot, xvpn-worker"
echo "   📋 Log File: $LOG_FILE"
echo "   📚 Documentation: $XVPN_DIR/POST_INSTALL.md"
echo ""