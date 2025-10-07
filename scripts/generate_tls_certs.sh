#!/bin/bash

# Script to generate self-signed TLS certificates for XVPN
set -e

echo "🔧 Generating TLS certificates for XVPN..."

# Create certificate directory in project if it doesn't exist
CERT_DIR="/home/uss/chatvpn/security/tls"
mkdir -p "$CERT_DIR"

# Check if certificates already exist
if [ -f "$CERT_DIR/cert.pem" ] && [ -f "$CERT_DIR/key.pem" ]; then
    echo "⚠️  Certificates already exist. Skipping generation."
    echo "   If you want to regenerate, delete the existing files first:"
    echo "   rm $CERT_DIR/cert.pem $CERT_DIR/key.pem"
    exit 0
fi

# Generate private key and certificate
openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 365 \
    -nodes \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=XVPN/PU=IT/CN=localhost/emailAddress=admin@xvpn.local" \
    -addext "subjectAltName=DNS:localhost,DNS:*.xvpn.local,IP:127.0.0.1"

# Set proper permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "✅ TLS certificates generated successfully!"
echo "   Certificate: $CERT_DIR/cert.pem"
echo "   Private Key: $CERT_DIR/key.pem"
echo ""
echo "💡 Note: These are self-signed certificates for development only."
echo "   For production, please replace with certificates from a CA."