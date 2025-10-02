# XVPN - Administration Guide

## Overview

This guide provides comprehensive administration procedures for XVPN, including system setup, monitoring, maintenance, and troubleshooting.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Monitoring](#monitoring)
5. [Maintenance](#maintenance)
6. [Security](#security)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tuning](#performance-tuning)
10. [Scaling](#scaling)

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     XVPN System Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Client    │    │    Agent    │    │     Bot     │     │
│  │   (GUI)     │    │   (AI)      │    │   (Telegram)│     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │         │
│         └───────────────────┼───────────────────┘         │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                       API                        │     │
│  │           (REST/GraphQL)                         │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                    Database                       │     │
│  │              (SQLite/PostgreSQL)                  │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                   XRay Core                       │     │
│  │                   (VPN Protocol)                   │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                   Traefik                         │     │
│  │                 (Load Balancer)                   │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                   Docker                          │     │
│  │                (Container Orchestration)           │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                   Systemd                         │     │
│  │                 (Service Management)               │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                             │                              │
│  ┌─────────────────────────┼─────────────────────────┐     │
│  │                   Network                         │     │
│  │              (HTTPS/TLS/IPv6)                     │     │
│  └─────────────────────────┼─────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Client** - GUI application for end users
2. **Agent** - AI-powered backend with RAG system
3. **Bot** - Telegram integration for notifications
4. **API** - REST/GraphQL server for system integration
5. **Database** - SQLite/PostgreSQL for data storage
6. **XRay Core** - VPN protocol implementation
7. **Traefik** - Load balancer and reverse proxy
8. **Docker** - Container orchestration
9. **Systemd** - Service management

## Installation

### Prerequisites

- Linux Ubuntu 20.04+ or CentOS 8+
- 2GB RAM minimum (4GB recommended)
- 20GB disk space minimum
- HTTPS domain with valid SSL certificate
- Static IP address

### Automated Installation

```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh | sudo bash

# Or download and run manually
wget https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh
sudo chmod +x install_xvpn.sh
sudo ./install_xvpn.sh
```

### Manual Installation

```bash
# System update
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv curl wget git docker.io docker-compose

# Install Docker
sudo curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone repository
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Install XVPN
sudo ./scripts/install_xvpn.sh
```

## Configuration

### Main Configuration Files

```bash
# Configuration directory
/opt/xvpn/config/

# Main configuration files
/opt/xvpn/config/api.json      # API server configuration
/opt/xvpn/config/agent.json    # Agent configuration
/opt/xvpn/config/client.json    # Client configuration
/opt/xvpn/config/docker-compose.yml  # Docker configuration
```

### API Configuration

```json
{
  "host": "0.0.0.0",
  "port": 8443,
  "ssl": true,
  "ssl_cert": "/opt/xvpn/ssl/cert.pem",
  "ssl_key": "/opt/xvpn/ssl/key.pem",
  "database": {
    "url": "sqlite:///data/xvpn.db",
    "pool_size": 10,
    "max_overflow": 20
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0
  }
}
```

### Agent Configuration

```json
{
  "name": "XVPN-Agent",
  "version": "1.0.0",
  "database": {
    "url": "sqlite:///data/agent.db"
  },
  "api": {
    "url": "https://api.xvpn.local"
  },
  "health_check": {
    "interval": 30,
    "timeout": 10
  },
  "rag_system": {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Client Configuration

```json
{
  "server": "api.xvpn.local",
  "port": 443,
  "protocol": "https",
  "auto_connect": false,
  "dns_leak_protection": true,
  "kill_switch": true,
  "preferred_protocol": "udp",
  "allowed_protocols": ["udp", "tcp"],
  "security_level": "high"
}
```

## Monitoring

### System Monitoring

```bash
# System overview
htop
free -h
df -h
uptime

# Network monitoring
iftop
nethogs
netstat -tulpn

# Process monitoring
ps aux | grep xvpn
systemctl status xvpn-*
```

### Application Monitoring

```bash
# API logs
journalctl -u xvpn-api -f

# Agent logs
journalctl -u xvpn-agent -f

# Client logs
journalctl -u xvpn-client -f

# Docker logs
docker-compose logs -f
```

### Health Checks

```bash
# API health check
curl -k https://api.xvpn.local/health

# Agent health check
curl -k https://api.xvpn.local/agent/health

# System health check
curl -k https://api.xvpn.local/system/health
```

### Monitoring Dashboard

```bash
# Install Prometheus
sudo apt install prometheus

# Configure Prometheus
sudo nano /etc/prometheus/prometheus.yml

# Install Grafana
sudo apt install grafana

# Access Grafana
http://your-server:3000
admin/admin
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Daily tasks
sudo systemctl status xvpn-*
sudo journalctl -u xvpn-* --since today

# Weekly tasks
sudo docker system prune -f
sudo apt update && sudo apt upgrade -y

# Monthly tasks
sudo backup_xvpn.sh
sudo logrotate -f /etc/logrotate.d/xvpn
```

### Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/xvpn

# Configuration content
/opt/xvpn/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 xvpn xvpn
}
```

### Service Updates

```bash
# Update XVPN
cd /opt/xvpn
git pull
sudo ./scripts/install_xvpn.sh

# Restart services
sudo systemctl restart xvpn-*
```

## Security

### Firewall Configuration

```bash
# UFW Configuration
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
sudo ufw deny 8080/tcp

# iptables Configuration
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### SSL/TLS Configuration

```bash
# Let's Encrypt SSL Certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.xvpn.local -d bot.xvpn.local

# SSL Configuration
sudo nano /opt/xvpn/traefik/tls.yml

# Test SSL
openssl s_client -connect api.xvpn.local:443
```

### User Access Control

```bash
# Create admin user
sudo useradd -m -s /bin/bash xvpn-admin
sudo usermod -aG sudo xvpn-admin

# SSH Key Authentication
ssh-keygen -t rsa -b 4096
ssh-copy-id xvpn-admin@your-server
```

## Backup and Recovery

### Backup Script

```bash
#!/bin/bash
# backup_xvpn.sh

BACKUP_DIR="/backup/xvpn"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="xvpn_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration and data
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude="logs" \
    --exclude="*.log" \
    /opt/xvpn/ \
    /etc/systemd/system/xvpn-*.service

# Backup database
sqlite3 /opt/xvpn/data/xvpn.db ".backup $BACKUP_DIR/xvpn.db_$DATE"

# Cleanup old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.db_*" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"
```

### Recovery Procedure

```bash
# Stop services
sudo systemctl stop xvpn-*

# Extract backup
cd /opt/xvpn
sudo tar -xzf /backup/xvpn/xvpn_backup_20231201_120000.tar.gz

# Restore database
sudo sqlite3 /opt/xvpn/data/xvpn.db < /backup/xvpn/xvpn.db_20231201_120000

# Start services
sudo systemctl start xvpn-*

# Verify recovery
sudo systemctl status xvpn-*
```

## Troubleshooting

### Common Issues

#### 1. Service Not Starting

```bash
# Check service status
sudo systemctl status xvpn-*

# View logs
sudo journalctl -u xvpn-* --no-pager -n 100

# Check dependencies
sudo systemctl status docker
sudo systemctl status nginx
```

#### 2. Port Conflicts

```bash
# Check port usage
sudo netstat -tulpn | grep :443
sudo ss -tulpn | grep :8443

# Kill conflicting process
sudo kill -9 <PID>
```

#### 3. Database Issues

```bash
# Check database
sudo sqlite3 /opt/xvpn/data/xvpn.db ".tables"
sudo sqlite3 /opt/xvpn/data/xvpn.db "SELECT COUNT(*) FROM users;"

# Repair database
sudo sqlite3 /opt/xvpn/data/xvpn.db "VACUUM;"
```

#### 4. SSL Certificate Issues

```bash
# Check certificate
sudo openssl x509 -in /opt/xvpn/ssl/cert.pem -text -noout

# Renew certificate
sudo certbot renew

# Test SSL
curl -k https://api.xvpn.local/health
```

### Debug Mode

```bash
# Enable debug mode
sudo systemctl set-property xvpn-api.service --property=Environment="DEBUG=True"
sudo systemctl restart xvpn-api

# View debug logs
sudo journalctl -u xvpn-api -f | grep DEBUG
```

### Performance Issues

```bash
# Check system resources
htop
free -h
df -h

# Check network
ping api.xvpn.local
traceroute api.xvpn.local

# Check database performance
sudo sqlite3 /opt/xvpn/data/xvpn.db "PRAGMA cache_size = -10000;"
```

## Performance Tuning

### System Tuning

```bash
# Increase file descriptors
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# TCP tuning
echo "net.core.somaxconn = 65536" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Database Tuning

```bash
# SQLite tuning
sudo sqlite3 /opt/xvpn/data/xvpn.db "PRAGMA journal_mode = WAL;"
sudo sqlite3 /opt/xvpn/data/xvpn.db "PRAGMA synchronous = NORMAL;"
sudo sqlite3 /opt/xvpn/data/xvpn.db "PRAGMA cache_size = -10000;"
```

### Application Tuning

```bash
# API server tuning
sudo nano /opt/xvpn/config/api.json

{
  "workers": 4,
  "threads": 2,
  "timeout": 30,
  "keepalive": 2
}
```

## Scaling

### Horizontal Scaling

```bash
# Load balancer configuration
sudo nano /opt/xvpn/traefik/traefik.yml

# Add multiple API servers
"api.xvpn.local": {
  "services": [
    "api-1",
    "api-2",
    "api-3"
  ]
}
```

### Database Scaling

```bash
# PostgreSQL setup
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb xvpn
sudo -u postgres createuser xvpn_user
sudo -u postgres psql -c "ALTER USER xvpn_user WITH PASSWORD 'password';"

# Configure API for PostgreSQL
{
  "database": {
    "url": "postgresql://xvpn_user:password@localhost/xvpn"
  }
}
```

### Container Scaling

```bash
# Docker Compose scaling
sudo docker-compose up -d --scale api=3
sudo docker-compose up -d --scale agent=2
```

## Conclusion

This administration guide provides comprehensive procedures for managing XVPN systems. Follow these guidelines to ensure optimal performance, security, and reliability.

For additional help, refer to:
- [XVPN Documentation](https://docs.xvpn.local)
- [GitHub Issues](https://github.com/xvpn/xvpn/issues)
- [Community Forum](https://forum.xvpn.local)
- [Support Team](mailto:support@xvpn.local)