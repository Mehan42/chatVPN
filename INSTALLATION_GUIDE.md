# XVPN Installation Guide

## Prerequisites

- Ubuntu 20.04 LTS or newer (recommended)
- At least 2GB RAM
- At least 20GB disk space
- Root or sudo access

## System Requirements

### Minimum Requirements
- CPU: 1 core
- RAM: 2GB
- Disk: 20GB
- Network: 100Mbps

### Recommended Requirements
- CPU: 2+ cores
- RAM: 4GB+
- Disk: 50GB+
- Network: 1Gbps+

## Installation Methods

### Method 1: Automated Installation (Recommended)

For Server:
```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Run the server installation script (as root/sudo)
sudo ./install_server.sh
```

For Client:
```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Run the client installation script (as regular user)
./install_client.sh
```

### Method 2: Manual Installation with uv (Recommended)

Modern installations should use `uv` for faster and more reliable dependency management:

1. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install dependencies**
   ```bash
   sudo apt install -y python3 python3-venv curl wget git docker.io docker-compose jq
   ```

3. **Install uv package manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or use pip: pip install uv
   ```

4. **Create xvpn user**
   ```bash
   sudo useradd -r -s /bin/false -d /opt/xvpn xvpn
   ```

5. **Create directories**
   ```bash
   sudo mkdir -p /opt/xvpn /var/log/xvpn
   sudo chown -R xvpn:xvpn /opt/xvpn /var/log/xvpn
   ```

6. **Copy project files**
   ```bash
   sudo cp -r ./* /opt/xvpn/
   sudo chown -R xvpn:xvpn /opt/xvpn
   ```

7. **Install Python dependencies (with automatic uv installation if needed)**

   First, ensure uv is installed system-wide (recommended):
   ```bash
   # Install uv to default location ($HOME/.local/bin) and add to PATH
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Add uv to PATH for current session
   export PATH="$HOME/.local/bin:$PATH"
   # Make it persistent in shell profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

   For Server (with fallback to pip if uv fails):
   ```bash
   # Install uv if not already present
   if ! command -v uv &> /dev/null; then
       curl -LsSf https://astral.sh/uv/install.sh | sh
       export PATH="$HOME/.local/bin:$PATH"
   fi
   
   # Try uv first (if uv is available)
   if command -v uv &> /dev/null; then
       # Run with uv from user's path (using sudo -i to ensure proper environment)
       sudo -i -u xvpn bash -c "cd /opt/xvpn && ~/.local/bin/uv pip install -r requirements_server.txt"
   else
       # Fallback to pip
       sudo -u xvpn bash -c "cd /opt/xvpn && pip3 install -r requirements_server.txt"
   fi
   ```

   For Client (with fallback to pip if uv fails):
   ```bash
   # Install uv if not already present
   if ! command -v uv &> /dev/null; then
       curl -LsSf https://astral.sh/uv/install.sh | sh
       export PATH="$HOME/.local/bin:$PATH"
   fi
   
   # Try uv first (if uv is available)
   if command -v uv &> /dev/null; then
       # Run with uv from user's path
       sudo -i -u xvpn bash -c "cd /opt/xvpn && ~/.local/bin/uv pip install -r requirements_client.txt"
   else
       # Fallback to pip
       sudo -u xvpn bash -c "cd /opt/xvpn && pip3 install -r requirements_client.txt"
   fi
   ```
   
   Alternative method - Create a system-wide symlink:
   ```bash
   # Install uv normally
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Create a system-wide symlink (requires root)
   sudo ln -sf $HOME/.local/bin/uv /usr/local/bin/uv
   # Now it's available to all users
   sudo -u xvpn bash -c "cd /opt/xvpn && uv pip install -r requirements_server.txt"
   ```

9. **Copy systemd services**
   ```bash
   sudo cp /opt/xvpn/systemd/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

10. **Configure firewall**
    ```bash
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 443/tcp
    sudo ufw allow 8443/tcp
    ```

## Configuration

### 1. Set up Telegram Bot

1. Create a Telegram bot using [@BotFather](https://t.me/BotFather)
2. Get your bot token and chat ID
3. Configure `/opt/xvpn/.env`:
   ```bash
   BOT_TOKEN=your_telegram_bot_token_here
   CHAT_ID=your_chat_id_here
   ```

### 2. SSL Certificate Setup

For production use, obtain SSL certificates:

```bash
# Using Let's Encrypt (requires domain name)
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### 3. Environment Variables

Edit `/opt/xvpn/.env`:
```bash
XVPN_USER=xvpn
XVPN_DIR=/opt/xvpn
LOG_DIR=/var/log/xvpn
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id
API_BASE_URL=https://yourdomain.com:8443
DATABASE_URL=sqlite:////opt/xvpn/db/agent.db
LOG_LEVEL=INFO
```

## Starting Services

### Start all services
```bash
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot
```

### Check service status
```bash
sudo systemctl status xvpn-api xvpn-agent xvpn-bot
```

### View logs
```bash
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f
```

## Docker Installation

### Build Docker Images
```bash
cd /opt/xvpn
docker-compose build
```

### Start Services
```bash
docker-compose up -d
```

### View Container Logs
```bash
docker-compose logs -f
```

## Client Installation

### Linux Client (Recommended Method)

Using the automated script:
```bash
# Clone repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Run client installation script
./install_client.sh
```

### Linux Client (Manual Installation with uv)

For more control over the installation:

1. **Install uv package manager**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install client dependencies**:
   ```bash
   uv pip install -r requirements_client.txt
   # Or alternatively: pip3 install -r requirements_client.txt
   ```

3. **Install XRay** (required for VPN functionality):
   ```bash
   bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
   ```

4. **Prepare client directories**:
   ```bash
   mkdir -p ~/chatvpn/client
   mkdir -p ~/chatvpn/client/logs
   mkdir -p ~/chatvpn/client/states
   mkdir -p ~/chatvpn/client/transports
   ```

5. **Run the client**:
   ```bash
   python3 client/vpn_client.py start
   ```

### Windows Client
Download the Windows installer from releases page and run as administrator.

### macOS Client
```bash
# Install using Homebrew
brew tap xvpn/xvpn
brew install xvpn-client
```

## Verification

### Check API Health
```bash
curl -k https://localhost:8443/mcp/v1/vpn.health
```

### Check Transport Manifest
```bash
curl -k https://localhost:8443/transports/manifest.json
```

### Check Service Status
```bash
sudo systemctl status xvpn-*
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   - Check logs: `sudo journalctl -u xvpn-api -n 50`
   - Verify configuration files
   - Check file permissions

2. **Docker containers not starting**
   - Check Docker logs: `docker-compose logs`
   - Verify Docker installation
   - Check resource limits

3. **Network connectivity issues**
   - Check firewall rules: `sudo ufw status`
   - Verify port availability
   - Check DNS resolution

4. **Python dependency issues**

   Using uv (recommended):
   ```bash
   # Clear uv cache and reinstall
   uv cache clean
   uv pip install -r requirements_server.txt  # or requirements_client.txt
   ```

   Using pip:
   ```bash
   # Reinstall dependencies: 
   pip3 install -r requirements_server.txt --force-reinstall  # or requirements_client.txt
   # Check Python version compatibility
   # Verify virtual environment setup
   ```

5. **uv-specific issues**
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Check uv version: `uv --version`
   - Use uv pip: `uv pip install package_name`

### Logs Location

- API logs: `/var/log/xvpn/api.log`
- Agent logs: `/var/log/xvpn/agent.log`
- Bot logs: `/var/log/xvpn/bot.log`
- Docker logs: `docker-compose logs`

## Updates

### Update Server Components
```bash
cd /opt/xvpn
git pull

# Update dependencies with fallback
# Ensure uv is available
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Try uv first (if uv is available)
if command -v uv &> /dev/null; then
    # Run with uv from user's path
    sudo -i -u xvpn bash -c "cd /opt/xvpn && ~/.local/bin/uv pip install -r requirements_server.txt --upgrade"  # or requirements_client.txt
else
    # Fallback to pip
    sudo -u xvpn bash -c "cd /opt/xvpn && pip3 install -r requirements_server.txt --upgrade"  # or requirements_client.txt
fi

sudo systemctl restart xvpn-*
```

### Update Docker Containers
```bash
cd /opt/xvpn
docker-compose pull
docker-compose up -d --force-recreate
```

## Backup and Restore

### Backup Configuration
```bash
sudo tar -czf xvpn-backup-$(date +%Y%m%d).tar.gz /opt/xvpn/config /opt/xvpn/data
```

### Restore Configuration
```bash
sudo tar -xzf xvpn-backup-YYYYMMDD.tar.gz -C /
```

## Uninstallation

### Remove Services
```bash
sudo systemctl stop xvpn-*
sudo systemctl disable xvpn-*
sudo rm /etc/systemd/system/xvpn-*.service
sudo systemctl daemon-reload
```

### Remove Files
```bash
sudo rm -rf /opt/xvpn
sudo rm -rf /var/log/xvpn
sudo userdel xvpn
```

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team via Telegram