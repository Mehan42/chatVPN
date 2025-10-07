#!/bin/bash

# Script to install TLS certificates to system directory
set -e

echo "🔐 Installing TLS certificates to system directory..."

# Source directory (where we generated certificates)
SOURCE_DIR="/home/uss/chatvpn/security/tls"
TARGET_DIR="/opt/xvpn/tls"

# Check if source certificates exist
if [ ! -f "$SOURCE_DIR/cert.pem" ] || [ ! -f "$SOURCE_DIR/key.pem" ]; then
    echo "❌ Source certificates not found in $SOURCE_DIR"
    echo "   Please generate certificates first by running:"
    echo "   /home/uss/chatvpn/scripts/generate_tls_certs.sh"
    exit 1
fi

# Create target directory if it doesn't exist
sudo mkdir -p "$TARGET_DIR"

# Copy certificates to system directory
sudo cp "$SOURCE_DIR/cert.pem" "$TARGET_DIR/"
sudo cp "$SOURCE_DIR/key.pem" "$TARGET_DIR/"

# Set proper ownership and permissions
sudo chown root:root "$TARGET_DIR/cert.pem" "$TARGET_DIR/key.pem"
sudo chmod 644 "$TARGET_DIR/cert.pem"
sudo chmod 600 "$TARGET_DIR/key.pem"

echo "✅ TLS certificates installed successfully!"
echo "   Certificate: $TARGET_DIR/cert.pem"
echo "   Private Key: $TARGET_DIR/key.pem"
echo ""
echo "💡 Note: These are self-signed certificates for development only."
echo "   For production, please replace with certificates from a CA."