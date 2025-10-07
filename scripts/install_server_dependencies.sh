#!/usr/bin/env bash
"""
XVPN Server Dependencies Installer
Installs all required Python packages for XVPN server
"""

set -e

echo "📦 Installing XVPN Server Dependencies"
echo "====================================="

# Update package list
echo "🔄 Updating package list..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv curl wget jq

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv /opt/xvpn-venv
source /opt/xvpn-venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install flask flask-cors flask-limiter requests psutil pyyaml

# Install security dependencies
echo "🔐 Installing security dependencies..."
pip install cryptography pyopenssl

# Install database dependencies
echo "🗄️  Installing database dependencies..."
pip install sqlite3

# Install testing dependencies
echo "🧪 Installing testing dependencies..."
pip install pytest pytest-cov pytest-html

# Install development dependencies
echo "🛠️  Installing development dependencies..."
pip install black flake8 pylint

# Install AI dependencies
echo "🤖 Installing AI dependencies..."
pip install torch transformers accelerate bitsandbytes
pip install langchain langchain-community langchain-core
pip install prometheus-client elasticsearch
pip install kubernetes docker paramiko
pip install numpy pandas scikit-learn

# Create requirements file
echo "📝 Creating requirements file..."
pip freeze > /opt/xvpn-venv/requirements.txt

echo ""
echo "✅ XVPN server dependencies installed successfully!"
echo "   Virtual environment: /opt/xvpn-venv"
echo "   Requirements file: /opt/xvpn-venv/requirements.txt"
echo ""
echo "💡 To activate virtual environment:"
echo "   source /opt/xvpn-venv/bin/activate"
echo ""
echo "💡 To run XVPN server:"
echo "   cd /home/uss/chatvpn/server/api && python3 app.py"