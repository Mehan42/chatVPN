#!/usr/bin/env bash
# update_server.sh
# Script to update XVPN server from GitHub repository

set -e

echo "🔄 XVPN Server Update Script"
echo "==========================="

# Configuration
REPO_URL="https://github.com/Mehan42/chatVPN.git"
LOCAL_DIR="/opt/xvpn"
BACKUP_DIR="/opt/xvpn.backup.$(date +%Y%m%d_%H%M%S)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    echo "Try: sudo $0"
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Check if directory exists
if [ ! -d "$LOCAL_DIR" ]; then
    print_warning "Server directory not found. Cloning repository..."
    git clone "$REPO_URL" "$LOCAL_DIR"
    cd "$LOCAL_DIR"
    print_status "Repository cloned successfully"
else
    # Create backup
    print_warning "Creating backup of current installation..."
    cp -r "$LOCAL_DIR" "$BACKUP_DIR"
    print_status "Backup created: $BACKUP_DIR"
    
    # Update from repository
    cd "$LOCAL_DIR"
    print_warning "Updating from GitHub repository..."
    
    # Fetch latest changes
    git fetch origin
    
    # Check if there are changes
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        print_status "Server is already up to date"
        exit 0
    fi
    
    # Stash local changes if any
    if ! git diff-index --quiet HEAD --; then
        print_warning "Stashing local changes..."
        git stash
    fi
    
    # Pull latest changes
    git pull origin main
    
    # Pop stashed changes if any
    if git stash list | grep -q "stash@"; then
        print_warning "Restoring stashed changes..."
        git stash pop
    fi
    
    print_status "Server updated successfully"
fi

# Install/update dependencies
print_warning "Installing/updating dependencies..."
if command -v pip3 &> /dev/null; then
    # Create virtual environment if it doesn't exist
    if [ ! -d "/opt/xvpn-venv" ]; then
        print_warning "Creating virtual environment..."
        python3 -m venv /opt/xvpn-venv
    fi
    
    # Activate virtual environment
    source /opt/xvpn-venv/bin/activate
    
    # Install server dependencies
    pip install --upgrade pip
    pip install -r "$LOCAL_DIR/requirements_server.txt" || print_warning "Failed to install server requirements"
    pip install -r "$LOCAL_DIR/requirements.txt" || print_warning "Failed to install common requirements"
else
    print_warning "pip3 not found, skipping dependency installation"
fi

# Make scripts executable
print_warning "Setting executable permissions..."
find "$LOCAL_DIR/scripts" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find "$LOCAL_DIR/server" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

# Run post-update setup
if [ -f "$LOCAL_DIR/scripts/post_update_server.sh" ]; then
    print_warning "Running post-update setup..."
    "$LOCAL_DIR/scripts/post_update_server.sh" || print_warning "Post-update setup failed"
fi

# Update systemd services
print_warning "Updating systemd services..."
if [ -d "$LOCAL_DIR/systemd" ]; then
    cp "$LOCAL_DIR/systemd/"*.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
    print_status "Systemd services updated"
fi

print_status "XVPN server update completed successfully!"
echo ""
echo "💡 Next steps:"
echo "1. Restart XVPN services:"
echo "   sudo systemctl restart xvpn-api xvpn-agent xvpn-bot"
echo "2. Check service status:"
echo "   sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
echo "3. Review logs for any issues:"
echo "   sudo journalctl -u xvpn-api -f"
echo ""
echo "📋 To restart all services:"
echo "   sudo systemctl restart xvpn-api xvpn-agent xvpn-bot xvpn-client"