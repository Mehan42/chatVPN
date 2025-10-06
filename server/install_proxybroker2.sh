#!/bin/bash
# Install ProxyBroker2 for XVPN
# This script installs ProxyBroker2 and verifies the installation

set -e

echo "🚀 Installing ProxyBroker2 for XVPN"
echo "====================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "❌ Please do not run this script as root"
  exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
  echo "❌ pip is not installed. Please install python3-pip"
  exit 1
fi

# Install ProxyBroker2 from GitHub
echo "📥 Installing ProxyBroker2 from GitHub..."
pip install git+https://github.com/bluet/proxybroker2.git --upgrade

# Verify installation
echo "🔍 Verifying installation..."
if python3 -c "import proxybroker; print('✅ ProxyBroker2 installed successfully')" 2>/dev/null; then
  echo ""
  echo "🎉 ProxyBroker2 installation completed!"
  echo ""
  echo "📦 Installed components:"
  python3 -c "import proxybroker; print(f'   Version: {proxybroker.__version__}')"
  echo ""
  echo "🔧 Next steps:"
  echo "   1. Use ProxyBroker2 directly:"
  echo "      python3 -m proxybroker find --types HTTP HTTPS --limit 10"
  echo ""
  echo "   2. Use XVPN integration:"
  echo "      python3 examples/proxy_integration_example.py"
  echo ""
  echo "   3. Start proxy server:"
  echo "      python3 -m proxybroker serve --host 127.0.0.1 --port 8888 --types HTTP HTTPS"
  echo ""
else
  echo "❌ ProxyBroker2 installation failed"
  exit 1
fi