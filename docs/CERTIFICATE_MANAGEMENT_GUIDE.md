# XVPN Certificate Management Guide

## Overview

This guide explains how to manage TLS certificates for XVPN, including monitoring, renewal, and deployment processes.

## Certificate Monitoring

### Purpose

The certificate monitoring system tracks expiration dates and sends alerts when certificates are approaching their expiration date.

### Monitoring Script

The monitoring script is located at:
```
/home/uss/chatvpn/scripts/monitor_certificates.py
```

### Configuration

The monitor configuration is stored in:
```
/opt/xvpn/data/cert_monitor_config.json
```

Default configuration:
```json
{
  "servers": [
    {"hostname": "77.110.123.27", "port": 8443, "name": "Production API"},
    {"hostname": "api.uss.hopto.org", "port": 443, "name": "Legacy API"}
  ],
  "alert_thresholds": {
    "critical": 7,
    "warning": 30,
    "info": 90
  },
  "notifications": {
    "email": {
      "enabled": false,
      "smtp_server": "localhost",
      "smtp_port": 587,
      "username": "",
      "password": "",
      "from_email": "xvpn@localhost",
      "to_emails": ["admin@localhost"]
    },
    "telegram": {
      "enabled": true,
      "bot_token": "",
      "chat_ids": []
    }
  },
  "renewal": {
    "auto_renew": true,
    "renew_days_before": 30,
    "script_path": "/home/uss/chatvpn/scripts/renew_certificates.sh"
  }
}
```

### Running the Monitor

```bash
# Run monitoring once
cd /home/uss/chatvpn
./scripts/monitor_certificates.py

# Run monitoring with custom config
./scripts/monitor_certificates.py --config /path/to/custom/config.json
```

### Monitoring Output

The monitor produces categorized output:
- **Critical**: Expired or expiring within 7 days
- **Warning**: Expiring within 30 days
- **Info**: Expiring within 90 days
- **Valid**: Valid for more than 90 days

## Certificate Renewal

### Purpose

The renewal system automatically renews certificates before they expire.

### Renewal Script

The renewal script is located at:
```
/home/uss/chatvpn/scripts/renew_certificates.py
```

### Configuration

The renewal configuration is stored in:
```
/opt/xvpn/data/cert_renewal_config.json
```

Default configuration:
```json
{
  "certificates": {
    "production": {
      "domains": ["77.110.123.27"],
      "cert_path": "/opt/xvpn/tls/cert.pem",
      "key_path": "/opt/xvpn/tls/key.pem",
      "provider": "self-signed",
      "renew_days_before": 30
    }
  },
  "providers": {
    "self-signed": {
      "script": "/home/uss/chatvpn/scripts/generate_tls_certs.sh",
      "days_valid": 365
    },
    "letsencrypt": {
      "script": "/usr/bin/certbot",
      "days_valid": 90
    }
  },
  "deployment": {
    "script": "/home/uss/chatvpn/scripts/deploy_certificates.sh",
    "reload_services": true,
    "services": ["xvpn-api"]
  },
  "notifications": {
    "enabled": true,
    "telegram": {
      "bot_token": "",
      "chat_ids": []
    }
  }
}
```

### Running Certificate Renewal

```bash
# Renew all certificates
cd /home/uss/chatvpn
./scripts/renew_certificates.py

# Renew specific certificate
./scripts/renew_certificates.py production

# Renew with custom config
./scripts/renew_certificates.py --config /path/to/custom/config.json
```

## Automated Monitoring with Cron

### Setting up Cron Jobs

Create a cron job to run monitoring daily:

```bash
# Edit crontab
crontab -e

# Add daily monitoring at 2 AM
0 2 * * * /home/uss/chatvpn/scripts/monitor_certificates.py >> /opt/xvpn/logs/cert_monitor.log 2>&1

# Add weekly renewal check on Sundays at 3 AM
0 3 * * 0 /home/uss/chatvpn/scripts/renew_certificates.py >> /opt/xvpn/logs/cert_renewal.log 2>&1
```

### Log Files

Monitor logs are stored in:
```
/opt/xvpn/logs/cert_monitor.log
/opt/xvpn/logs/cert_renewal.log
```

## Manual Certificate Management

### Generating New Certificates

```bash
# Generate self-signed certificates
cd /home/uss/chatvpn
./scripts/generate_tls_certs.sh

# Check generated certificates
ls -la /home/uss/chatvpn/security/tls/
```

### Deploying Certificates to Production

```bash
# Deploy certificates to production server
cd /home/uss/chatvpn
./scripts/deploy_certificates.sh

# Or manually copy certificates
scp /home/uss/chatvpn/security/tls/cert.pem root@77.110.123.27:/opt/xvpn/tls/
scp /home/uss/chatvpn/security/tls/key.pem root@77.110.123.27:/opt/xvpn/tls/

# Set proper permissions on production server
ssh root@77.110.123.27 "
  chown root:root /opt/xvpn/tls/cert.pem /opt/xvpn/tls/key.pem
  chmod 644 /opt/xvpn/tls/cert.pem
  chmod 600 /opt/xvpn/tls/key.pem
"
```

### Restarting Services

After deploying new certificates, restart services:

```bash
# On production server
systemctl restart xvpn-api

# Check service status
systemctl status xvpn-api

# View logs if needed
journalctl -u xvpn-api -f
```

## Certificate Providers

### Self-Signed Certificates

Self-signed certificates are used for development and internal deployments.

Generation script:
```
/home/uss/chatvpn/scripts/generate_tls_certs.sh
```

### Let's Encrypt Certificates

For public deployments, Let's Encrypt certificates provide trusted SSL/TLS encryption.

Requirements:
- Public domain name pointing to server
- Port 80 accessible for ACME challenge
- Certbot installed

Installation:
```bash
# Install certbot
apt-get update
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d yourdomain.com

# Copy to XVPN directory
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/xvpn/tls/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/xvpn/tls/key.pem
```

## Security Best Practices

### Certificate Storage

1. Store private keys with restricted permissions (600)
2. Store certificates with read permissions (644)
3. Backup certificates regularly
4. Use encrypted backups for sensitive environments

### Certificate Rotation

1. Implement automated monitoring and renewal
2. Test renewal process regularly
3. Have rollback procedures for failed renewals
4. Monitor certificate expiration dates

### Access Control

1. Limit access to certificate files
2. Use dedicated service accounts
3. Audit certificate access regularly
4. Rotate certificates before expiration

## Troubleshooting

### Common Issues

#### Certificate Generation Fails

```bash
# Check OpenSSL installation
openssl version

# Check permissions
ls -la /home/uss/chatvpn/security/tls/

# Run generation with verbose output
bash -x /home/uss/chatvpn/scripts/generate_tls_certs.sh
```

#### Certificate Deployment Fails

```bash
# Check SSH connectivity
ssh root@77.110.123.27 "echo 'Connected'"

# Check destination directory
ssh root@77.110.123.27 "ls -la /opt/xvpn/tls/"

# Check disk space
ssh root@77.110.123.27 "df -h /opt/xvpn/"
```

#### Service Won't Start After Certificate Update

```bash
# Check service logs
journalctl -u xvpn-api -f

# Check certificate validity
openssl x509 -in /opt/xvpn/tls/cert.pem -text -noout

# Check key validity
openssl rsa -in /opt/xvpn/tls/key.pem -check -noout
```

#### Certificate Verification Errors

```bash
# Test HTTPS connectivity
curl -vk https://77.110.123.27:8443/mcp/v1/vpn.health

# Check certificate chain
openssl s_client -connect 77.110.123.27:8443 -servername 77.110.123.27
```

### Log Analysis

Monitor logs for certificate-related issues:
```bash
# Check certificate monitoring logs
tail -f /opt/xvpn/logs/cert_monitor.log

# Check renewal logs
tail -f /opt/xvpn/logs/cert_renewal.log

# Check API service logs
journalctl -u xvpn-api -f
```

## Backup and Recovery

### Certificate Backups

Regular backups of certificates are stored in:
```
/opt/xvpn/tls/backup/
```

Backup naming convention:
```
cert_YYYYMMDD_HHMMSS.pem
key_YYYYMMDD_HHMMSS.pem
```

### Restoring Certificates

```bash
# List available backups
ls -la /opt/xvpn/tls/backup/

# Restore specific backup
cp /opt/xvpn/tls/backup/cert_20251007_131122.pem /opt/xvpn/tls/cert.pem
cp /opt/xvpn/tls/backup/key_20251007_131122.pem /opt/xvpn/tls/key.pem

# Set proper permissions
chown root:root /opt/xvpn/tls/cert.pem /opt/xvpn/tls/key.pem
chmod 644 /opt/xvpn/tls/cert.pem
chmod 600 /opt/xvpn/tls/key.pem

# Restart services
systemctl restart xvpn-api
```

## Monitoring and Alerts

### Alert Thresholds

- **Critical**: 7 days before expiration (or already expired)
- **Warning**: 30 days before expiration
- **Info**: 90 days before expiration

### Notification Methods

1. **Telegram**: Real-time alerts via Telegram bot
2. **Email**: Email notifications for critical alerts
3. **System Logs**: All events logged to system journal

### Alert Content

Alerts include:
- Server name and address
- Days until expiration (or days expired)
- Certificate subject and issuer
- Recommended actions

## Production Considerations

### High Availability

For production environments:

1. Use redundant certificate monitoring
2. Implement failover procedures
3. Test renewal processes regularly
4. Monitor multiple geographic locations

### Compliance

Ensure certificates meet regulatory requirements:

1. Use appropriate certificate authorities
2. Maintain audit trails
3. Follow industry best practices
4. Document certificate lifecycle

### Disaster Recovery

Have plans for:

1. Rapid certificate replacement
2. Service restoration procedures
3. Communication protocols
4. Post-incident analysis

## Next Steps

1. Configure monitoring thresholds for your environment
2. Set up notification channels (Telegram, email)
3. Schedule regular monitoring with cron
4. Test renewal procedures
5. Implement backup and recovery procedures
6. Monitor logs for certificate-related issues
7. Document your certificate management processes