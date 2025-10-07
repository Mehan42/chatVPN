#!/usr/bin/env bash
# update_client.sh
# Script to update XVPN client from GitHub repository

set -e

echo "🔄 XVPN Client Update Script"
echo "==========================="

# Configuration
REPO_URL="https://github.com/Mehan42/chatVPN.git"
LOCAL_DIR="$HOME/chatvpn"
BACKUP_DIR="$HOME/chatvpn.backup.$(date +%Y%m%d_%H%M%S)"

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

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Check if directory exists
if [ ! -d "$LOCAL_DIR" ]; then
    print_warning "Local directory not found. Cloning repository..."
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
        print_status "Client is already up to date"
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
    
    print_status "Client updated successfully"
fi

# Install/update dependencies
print_warning "Installing/updating dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --user -r "$LOCAL_DIR/requirements_client.txt" || print_warning "Failed to install client requirements"
else
    print_warning "pip3 not found, skipping dependency installation"
fi

# Make scripts executable
print_warning "Setting executable permissions..."
find "$LOCAL_DIR/scripts" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find "$LOCAL_DIR/client" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

# Run post-update setup
if [ -f "$LOCAL_DIR/scripts/post_update_client.sh" ]; then
    print_warning "Running post-update setup..."
    "$LOCAL_DIR/scripts/post_update_client.sh" || print_warning "Post-update setup failed"
fi

print_status "XVPN client update completed successfully!"
echo ""
echo "💡 Next steps:"
echo "1. Restart the client application"
echo "2. Check the changelog for breaking changes"
echo "3. Test the updated functionality"
echo ""
echo "📋 To restart the client:"
echo "   cd $LOCAL_DIR/client && python3 chatvpn_gui.py"