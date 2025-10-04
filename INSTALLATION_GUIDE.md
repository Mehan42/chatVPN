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

```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Run the installation script
sudo ./installer/install_xvpn.sh
```

### Method 2: Manual Installation

1. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install dependencies**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv curl wget git docker.io docker-compose jq
   ```

3. **Install uv package manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
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

7. **Install Python dependencies**
   ```bash
   sudo -u xvpn bash -c "cd /opt/xvpn && pip3 install -r requirements.txt"
   ```

8. **Install AI components**
   ```bash
   sudo -u xvpn bash -c "cd /opt/xvpn && pip3 install chromadb sentence-transformers"
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

### Linux Client
```bash
# Clone repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Run client installation script
./install_client.sh
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
   - Reinstall dependencies: `pip3 install -r requirements.txt --force-reinstall`
   - Check Python version compatibility
   - Verify virtual environment setup

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