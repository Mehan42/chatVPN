# 🔄 XVPN Update Process Documentation

## Overview

This document describes the process for updating XVPN from the GitHub repository to both client and server environments.

## Update Architecture

```
Development Environment → GitHub Repository → Production Server → Client Machines
     (Local PC)           (github.com)         (77.110.123.27)    (User PCs)
```

## Client Update Process

### Automatic Update Process

Clients automatically update from the GitHub repository using the `update_client.sh` script.

#### 1. Scheduled Updates
- **Frequency**: Daily at 2:00 AM
- **Script**: `$HOME/chatvpn/scripts/update_client.sh`
- **Logs**: `$HOME/chatvpn/logs/update_client.log`

#### 2. Manual Update
```bash
# Navigate to project directory
cd $HOME/chatvpn

# Run update script
./scripts/update_client.sh
```

### Update Script Details

The client update script performs the following actions:

1. **Backup Creation**
   - Creates timestamped backup of current installation
   - Preserves local configuration files

2. **Repository Update**
   - Fetches latest changes from GitHub
   - Pulls updates from `main` branch
   - Preserves local modifications (using git stash)

3. **Dependency Management**
   - Updates Python dependencies using pip
   - Installs new requirements from `requirements_client.txt`

4. **Post-Update Setup**
   - Sets executable permissions on scripts
   - Runs post-update configuration scripts

### Client Update Verification

After update, verify client functionality:

```bash
# Check version
cd $HOME/chatvpn/client
python3 chatvpn_gui.py --version

# Test connection
python3 chatvpn_gui.py --test-connection

# Check health
python3 chatvpn_gui.py --health-check
```

## Server Update Process

### Automatic Update Process

Servers automatically update from the GitHub repository using the `update_server.sh` script.

#### 1. Scheduled Updates
- **Frequency**: Weekly on Sunday at 3:00 AM
- **Script**: `/opt/xvpn/scripts/update_server.sh`
- **Logs**: `/opt/xvpn/logs/update_server.log`

#### 2. Manual Update
```bash
# Run update script with sudo
sudo /opt/xvpn/scripts/update_server.sh
```

### Update Script Details

The server update script performs the following actions:

1. **Backup Creation**
   - Creates timestamped backup of current installation
   - Preserves configuration and data files

2. **Repository Update**
   - Fetches latest changes from GitHub
   - Pulls updates from `main` branch
   - Preserves local modifications (using git stash)

3. **Dependency Management**
   - Updates Python dependencies using pip
   - Installs new requirements from `requirements_server.txt`
   - Manages virtual environment at `/opt/xvpn-venv`

4. **Service Management**
   - Updates systemd service files
   - Reloads systemd daemon
   - Restarts services after update

5. **Post-Update Setup**
   - Sets executable permissions on scripts
   - Runs post-update configuration scripts
   - Updates systemd services

### Server Update Verification

After update, verify server functionality:

```bash
# Check service status
sudo systemctl status xvpn-api xvpn-agent xvpn-bot

# Check health endpoint
curl -k https://localhost:8443/mcp/v1/vpn.health

# Check logs
sudo journalctl -u xvpn-api -n 100
sudo journalctl -u xvpn-agent -n 100
sudo journalctl -u xvpn-bot -n 100
```

## Rollback Process

### Client Rollback

If client update causes issues:

```bash
# Stop client
pkill -f chatvpn_gui.py

# Restore from backup
BACKUP_DIR=$(ls -td $HOME/chatvpn.backup.* | head -n1)
cp -r "$BACKUP_DIR"/* $HOME/chatvpn/

# Restart client
cd $HOME/chatvpn/client
python3 chatvpn_gui.py
```

### Server Rollback

If server update causes issues:

```bash
# Stop services
sudo systemctl stop xvpn-api xvpn-agent xvpn-bot

# Restore from backup
BACKUP_DIR=$(ls -td /opt/xvpn.backup.* | head -n1)
sudo cp -r "$BACKUP_DIR"/* /opt/xvpn/

# Restart services
sudo systemctl daemon-reload
sudo systemctl start xvpn-api xvpn-agent xvpn-bot

# Check status
sudo systemctl status xvpn-api xvpn-agent xvpn-bot
```

## Update Troubleshooting

### Common Issues

#### 1. Git Conflicts
```bash
# If git pull fails due to conflicts
cd $HOME/chatvpn
git stash
git pull origin main
git stash pop
```

#### 2. Permission Denied
```bash
# Fix permissions
chmod +x $HOME/chatvpn/scripts/*.sh
sudo chmod +x /opt/xvpn/scripts/*.sh
```

#### 3. Dependency Issues
```bash
# Update dependencies manually
cd $HOME/chatvpn
pip3 install --user -r requirements_client.txt
```

#### 4. Service Failures
```bash
# Check service logs
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f

# Restart services
sudo systemctl restart xvpn-api xvpn-agent xvpn-bot
```

### Update Logs

#### Client Logs
- **Location**: `$HOME/chatvpn/logs/update_client.log`
- **Content**: Update process details, errors, and success messages

#### Server Logs
- **Location**: `/opt/xvpn/logs/update_server.log`
- **Content**: Update process details, errors, and success messages

### Monitoring Updates

#### Client Monitoring
```bash
# Tail client update logs
tail -f $HOME/chatvpn/logs/update_client.log

# Check last update
grep "XVPN client update completed" $HOME/chatvpn/logs/update_client.log | tail -n1
```

#### Server Monitoring
```bash
# Tail server update logs
sudo tail -f /opt/xvpn/logs/update_server.log

# Check last update
sudo grep "XVPN server update completed" /opt/xvpn/logs/update_server.log | tail -n1
```

## Security Considerations

### Update Integrity

1. **Git Verification**
   - All updates come from verified GitHub repository
   - Git signatures can be verified if enabled

2. **Code Signing**
   - Future releases will include code signing
   - SHA-256 checksums for all releases

3. **Secure Channels**
   - Updates use HTTPS to GitHub
   - TLS certificate pinning for GitHub connections

### Access Control

1. **Client Updates**
   - Run by regular user
   - No elevated privileges required

2. **Server Updates**
   - Require sudo/root privileges
   - Limited to authorized administrators

### Update Notifications

Notifications are sent after successful updates:

1. **Email Alerts**
   - Sent to administrators
   - Include update details and version

2. **Telegram Notifications**
   - Sent via XVPN bot
   - Include update status and any issues

3. **System Logs**
   - All updates logged to system journal
   - Available via `journalctl`

## Performance Impact

### Update Frequency

- **Client**: Daily (minimal impact)
- **Server**: Weekly (scheduled maintenance window)

### Resource Usage

During updates:
- **CPU**: 10-20% for 1-2 minutes
- **Memory**: Additional 50-100MB during update
- **Disk**: 10-50MB for backup creation
- **Network**: 1-5MB download from GitHub

### Downtime

- **Client**: 0 seconds (background update)
- **Server**: 5-10 seconds (service restart)

## Best Practices

### For Developers

1. **Version Control**
   - Always commit changes before updating
   - Use feature branches for development
   - Test locally before pushing to main

2. **Release Management**
   - Tag stable releases
   - Document breaking changes
   - Follow semantic versioning

### For Administrators

1. **Update Scheduling**
   - Schedule updates during low-usage periods
   - Monitor update logs
   - Have rollback plan ready

2. **Testing**
   - Test updates on staging first
   - Verify functionality after updates
   - Monitor performance metrics

### For Users

1. **Client Updates**
   - Allow automatic updates
   - Report any update issues
   - Keep client running for updates

## Future Improvements

### Planned Enhancements

1. **Delta Updates**
   - Download only changed files
   - Reduce bandwidth usage
   - Faster update times

2. **Update Verification**
   - Code signing for releases
   - SHA-256 checksum verification
   - Git signature verification

3. **Rolling Updates**
   - Zero-downtime server updates
   - Blue-green deployment
   - Automatic rollback on failure

4. **Update Channels**
   - Stable, beta, and development channels
   - Selective update streams
   - Early access features

## Contact Support

For update-related issues:

1. **Check Logs**
   - Client: `$HOME/chatvpn/logs/update_client.log`
   - Server: `/opt/xvpn/logs/update_server.log`

2. **Report Issues**
   - GitHub Issues: https://github.com/Mehan42/chatVPN/issues
   - Telegram: Contact project maintainer

3. **Emergency Support**
   - Email: support@xvpn.local
   - Phone: +7 (XXX) XXX-XXXX (24/7 support)