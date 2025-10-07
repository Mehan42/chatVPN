#!/bin/bash

# XVPN Certificate Deployment Script
# Deploys TLS certificates to production server

set -e

# Configuration
PROD_SERVER="77.110.123.27"
PROD_USER="root"
LOCAL_CERT_DIR="/home/uss/chatvpn/security/tls"
REMOTE_CERT_DIR="/opt/xvpn/tls"

echo "🚀 XVPN Certificate Deployment to Production Server"
echo "==================================================="

# Check if certificates exist locally
if [ ! -f "$LOCAL_CERT_DIR/cert.pem" ] || [ ! -f "$LOCAL_CERT_DIR/key.pem" ]; then
    echo "❌ Error: Certificates not found in $LOCAL_CERT_DIR"
    echo "   Please generate certificates first:"
    echo "   cd /home/uss/chatvpn && ./scripts/generate_tls_certs.sh"
    exit 1
fi

echo "✅ Found local certificates"

# Test SSH connection
echo "🔍 Testing SSH connection to $PROD_SERVER..."
if ! ssh -o ConnectTimeout=10 "$PROD_USER@$PROD_SERVER" "echo 'SSH connection successful'"; then
    echo "❌ Error: Cannot connect to production server via SSH"
    echo "   Please ensure you have SSH access to $PROD_SERVER"
    exit 1
fi

echo "✅ SSH connection successful"

# Create remote directory
echo "📂 Creating remote certificate directory..."
ssh "$PROD_USER@$PROD_SERVER" "mkdir -p $REMOTE_CERT_DIR"

# Transfer certificates
echo "📤 Transferring certificates to production server..."
scp "$LOCAL_CERT_DIR/cert.pem" "$PROD_USER@$PROD_SERVER:$REMOTE_CERT_DIR/"
scp "$LOCAL_CERT_DIR/key.pem" "$PROD_USER@$PROD_SERVER:$REMOTE_CERT_DIR/"

# Set proper permissions
echo "🔐 Setting proper permissions on production server..."
ssh "$PROD_USER@$PROD_SERVER" "
    chown root:root $REMOTE_CERT_DIR/cert.pem $REMOTE_CERT_DIR/key.pem
    chmod 644 $REMOTE_CERT_DIR/cert.pem
    chmod 600 $REMOTE_CERT_DIR/key.pem
"

# Verify installation
echo "✅ Verifying certificate installation..."
ssh "$PROD_USER@$PROD_SERVER" "
    ls -la $REMOTE_CERT_DIR/
    echo 'Certificate installation verified'
"

echo ""
echo "🎉 Certificate deployment completed successfully!"
echo "   Certificates deployed to: $PROD_SERVER:$REMOTE_CERT_DIR/"
echo ""
echo "下一步 (Next steps):"
echo "1. Restart XVPN services on production server:"
echo "   ssh $PROD_USER@$PROD_SERVER 'systemctl restart xvpn-api'"
echo "2. Test HTTPS connectivity:"
echo "   curl -k https://$PROD_SERVER:8443/mcp/v1/vpn.health"