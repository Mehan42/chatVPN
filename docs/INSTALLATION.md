# XVPN - Installation Guide

## Overview

XVPN is a secure VPN client with AI integration, built with Python and Docker. This guide covers installation procedures for different platforms.

## Requirements

- Python 3.8+
- Docker 20.0+
- Docker Compose 1.29+
- Systemd (Linux)
- 512MB RAM minimum
- 1GB disk space

## Installation Methods

### 1. Quick Install (Recommended)

For Linux systems, use the automated installer:

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh | sudo bash

# Or download first and run
wget https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh
sudo chmod +x install_xvpn.sh
sudo ./install_xvpn.sh
```

### 2. Manual Installation

#### Linux

```bash
# Clone the repository
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl wget git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install XVPN
sudo ./scripts/install_xvpn.sh
```

#### Windows

1. Download the Windows installer from the [releases page](https://github.com/xvpn/xvpn/releases)
2. Run the installer as Administrator
3. Follow the installation wizard

#### macOS

1. Download the macOS installer from the [releases page](https://github.com/xvpn/xvpn/releases)
2. Open the DMG file
3. Drag XVPN to your Applications folder
4. Run the application

### 3. Docker Installation

```bash
# Clone the repository
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Start the services
docker-compose up -d

# Check status
docker-compose ps
```

## Post-Installation

### 1. Verify Installation

```bash
# Check service status
sudo systemctl status xvpn-*

# View logs
sudo journalctl -u xvpn-* -f

# Test connectivity
curl https://api.xvpn.local/health
```

### 2. Configuration

The configuration files are located in `/opt/xvpn/config/` (Linux) or the application directory.

Main configuration files:
- `api.json` - API server configuration
- `agent.json` - Agent configuration
- `client.json` - Client configuration

### 3. First Run

```bash
# Start the client
sudo systemctl start xvpn-client.service

# Check client status
sudo systemctl status xvpn-client.service

# Load initial configuration
sudo /opt/xvpn/client/chatvpn_backend.py config
```

## Service Management

### Linux Systemd

```bash
# Start services
sudo systemctl start xvpn-*

# Stop services
sudo systemctl stop xvpn-*

# Restart services
sudo systemctl restart xvpn-*

# Enable auto-start on boot
sudo systemctl enable xvpn-*

# Disable auto-start
sudo systemctl disable xvpn-*

# View logs
sudo journalctl -u xvpn-* -f
```

### Docker

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```

2. **Port conflicts**
   ```bash
   # Check port usage
   sudo netstat -tulpn | grep :80
   sudo netstat -tulpn | grep :443
   ```

3. **Permission issues**
   ```bash
   sudo chown -R xvpn:xvpn /opt/xvpn
   sudo chmod +x /opt/xvpn/client/chatvpn_backend.py
   ```

4. **Service not starting**
   ```bash
   # Check service status
   sudo systemctl status xvpn-*
   
   # View logs
   sudo journalctl -u xvpn-* --no-pager -n 100
   ```

### Logs Location

- Linux: `/opt/xvpn/logs/`
- Docker: `docker-compose logs`
- Systemd: `journalctl -u xvpn-*`

### Support

If you encounter issues:

1. Check the logs
2. Review the troubleshooting section
3. Open an issue on [GitHub](https://github.com/xvpn/xvpn/issues)
4. Join our [community](https://discord.gg/xvpn)

## Uninstallation

### Linux

```bash
# Stop and disable services
sudo systemctl stop xvpn-*
sudo systemctl disable xvpn-*

# Remove systemd services
sudo rm /etc/systemd/system/xvpn-*.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/xvpn

# Remove user (optional)
sudo userdel xvpn
```

### Windows

1. Go to Control Panel > Programs and Features
2. Uninstall XVPN
3. Remove the installation directory

### macOS

1. Drag XVPN to the Trash
2. Remove configuration files from `~/Library/Application Support/XVPN/`

### Docker

```bash
# Stop and remove containers
docker-compose down

# Remove images (optional)
docker-compose down -v
docker rmi xvpn-*