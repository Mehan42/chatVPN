# XVPN TLS Certificate Deployment Guide

## Overview

This guide describes how to deploy TLS certificates for XVPN on the production server at IP 77.110.123.27.

## Prerequisites

- SSH access to the production server (77.110.123.27)
- Root or sudo privileges
- OpenSSL installed on the server

## Deployment Steps

### 1. Generate TLS Certificates Locally

First, generate the self-signed certificates in your local development environment:

```bash
# Navigate to your project directory
cd /home/uss/chatvpn

# Generate certificates using the provided script
./scripts/generate_tls_certs.sh
```

This will create certificates in `/home/uss/chatvpn/security/tls/`:
- `cert.pem` - Certificate file
- `key.pem` - Private key file

### 2. Transfer Certificates to Production Server

Transfer the certificates to the production server using SCP:

```bash
# From your local machine, transfer certificates to production server
scp /home/uss/chatvpn/security/tls/cert.pem root@77.110.123.27:/tmp/
scp /home/uss/chatvpn/security/tls/key.pem root@77.110.123.27:/tmp/
```

### 3. Install Certificates on Production Server

SSH into the production server and install the certificates:

```bash
# SSH into production server
ssh root@77.110.123.27

# Create TLS directory if it doesn't exist
mkdir -p /opt/xvpn/tls

# Move certificates to the proper location
mv /tmp/cert.pem /opt/xvpn/tls/
mv /tmp/key.pem /opt/xvpn/tls/

# Set proper permissions
chown root:root /opt/xvpn/tls/cert.pem /opt/xvpn/tls/key.pem
chmod 644 /opt/xvpn/tls/cert.pem
chmod 600 /opt/xvpn/tls/key.pem
```

### 4. Verify Certificate Installation

Check that certificates are properly installed:

```bash
# Verify certificate files exist with correct permissions
ls -la /opt/xvpn/tls/

# Expected output:
# -rw-r--r-- 1 root root 2122 Oct 7 13:11 cert.pem
# -rw------- 1 root root 3272 Oct 7 13:11 key.pem
```

### 5. Restart XVPN Services

Restart the XVPN API service to use the new certificates:

```bash
# Restart the API service
systemctl restart xvpn-api

# Check service status
systemctl status xvpn-api

# View service logs if needed
journalctl -u xvpn-api -f
```

## Testing HTTPS Connectivity

Test that HTTPS is working correctly:

```bash
# Test HTTPS endpoint
curl -k https://77.110.123.27:8443/mcp/v1/vpn.health

# Expected response:
# {
#   "status": "healthy",
#   "mask_score": 5,
#   "timestamp": 1234567890.123,
#   "version": "1.0.0",
#   ...
# }
```

## Certificate Renewal

For certificate renewal, follow the same steps:

1. Generate new certificates locally
2. Transfer to production server
3. Replace existing certificate files
4. Restart services

## Production Considerations

For production environments, replace self-signed certificates with certificates from a trusted Certificate Authority (CA) such as Let's Encrypt.

### Let's Encrypt Integration

To use Let's Encrypt certificates:

1. Install Certbot:
   ```bash
   apt-get update
   apt-get install certbot
   ```

2. Obtain certificates:
   ```bash
   certbot certonly --standalone -d yourdomain.com
   ```

3. Copy certificates to XVPN directory:
   ```bash
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/xvpn/tls/cert.pem
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/xvpn/tls/key.pem
   ```

4. Set proper permissions and restart services

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Ensure certificate files have correct permissions (644 for cert, 600 for key)
   - Ensure owned by root user

2. **Service Won't Start**
   - Check service logs: `journalctl -u xvpn-api -f`
   - Verify certificate paths in service configuration

3. **HTTPS Connection Refused**
   - Verify firewall allows connections on port 443
   - Check service is listening: `netstat -tlnp | grep :443`

### Log Locations

- XVPN API logs: `/opt/xvpn/logs/api.log`
- Systemd service logs: `journalctl -u xvpn-api`
- Certificate directory: `/opt/xvpn/tls/`

## Security Recommendations

1. **Certificate Storage**
   - Store private keys with restricted permissions (600)
   - Regularly audit certificate access

2. **Certificate Rotation**
   - Implement automated certificate renewal
   - Monitor certificate expiration dates

3. **Network Security**
   - Restrict access to certificate files
   - Use firewalls to limit service exposure

## Next Steps

After deploying TLS certificates, proceed with:
1. Implementing client-side certificate pinning
2. Securing API endpoints with authentication
3. Setting up automated certificate renewal