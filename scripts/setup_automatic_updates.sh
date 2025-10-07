#!/usr/bin/env bash
# setup_automatic_updates.sh
# Script to set up automatic updates for XVPN client and server

set -e

echo "🔄 Setting up automatic XVPN updates..."
echo "======================================"

# Configuration
CLIENT_UPDATE_SCRIPT="$HOME/chatvpn/scripts/update_client.sh"
SERVER_UPDATE_SCRIPT="/opt/xvpn/scripts/update_server.sh"

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

# Setup client automatic updates
setup_client_updates() {
    if [ -f "$CLIENT_UPDATE_SCRIPT" ]; then
        print_warning "Setting up client automatic updates..."
        
        # Make sure script is executable
        chmod +x "$CLIENT_UPDATE_SCRIPT"
        
        # Create cron job for client updates (daily at 2 AM)
        (crontab -l 2>/dev/null; echo "0 2 * * * $CLIENT_UPDATE_SCRIPT >> $HOME/chatvpn/logs/update_client.log 2>&1") | crontab -
        
        print_status "Client automatic updates set up successfully"
    else
        print_warning "Client update script not found, skipping client updates setup"
    fi
}

# Setup server automatic updates
setup_server_updates() {
    if [ -f "$SERVER_UPDATE_SCRIPT" ]; then
        print_warning "Setting up server automatic updates..."
        
        # Make sure script is executable
        chmod +x "$SERVER_UPDATE_SCRIPT"
        
        # Create cron job for server updates (weekly on Sunday at 3 AM)
        (crontab -l 2>/dev/null; echo "0 3 * * 0 $SERVER_UPDATE_SCRIPT >> /opt/xvpn/logs/update_server.log 2>&1") | crontab -
        
        print_status "Server automatic updates set up successfully"
    else
        print_warning "Server update script not found, skipping server updates setup"
    fi
}

# Setup update notifications
setup_notifications() {
    print_warning "Setting up update notifications..."
    
    # Create notification script
    NOTIFICATION_SCRIPT="$HOME/chatvpn/scripts/notify_updates.sh"
    
    cat > "$NOTIFICATION_SCRIPT" << 'EOF'
#!/usr/bin/env bash
# notify_updates.sh
# Script to send update notifications

# Check if there were updates in the last run
LOG_FILE="$HOME/chatvpn/logs/update_client.log"
LAST_RUN=$(tail -n 20 "$LOG_FILE" 2>/dev/null | grep -c "XVPN client update completed successfully!")

if [ "$LAST_RUN" -gt 0 ]; then
    # Send notification (this is a placeholder - implement your preferred notification method)
    echo "XVPN client was updated successfully at $(date)" | mail -s "XVPN Client Update" admin@example.com 2>/dev/null || true
fi
EOF
    
    chmod +x "$NOTIFICATION_SCRIPT"
    
    # Add notification cron job (runs 10 minutes after update)
    (crontab -l 2>/dev/null; echo "10 2 * * * $NOTIFICATION_SCRIPT") | crontab -
    
    print_status "Update notifications set up successfully"
}

# Main execution
main() {
    # Setup client updates
    setup_client_updates
    
    # Setup server updates (requires root)
    if [ "$EUID" -eq 0 ]; then
        setup_server_updates
    else
        print_warning "Not running as root, skipping server updates setup"
        print_warning "Run with sudo to set up server updates: sudo $0"
    fi
    
    # Setup notifications
    setup_notifications
    
    print_status "Automatic updates setup completed!"
    echo ""
    echo "📅 Update Schedule:"
    echo "   Client: Daily at 2:00 AM"
    echo "   Server: Weekly on Sunday at 3:00 AM"
    echo ""
    echo "📋 To view/update cron jobs:"
    echo "   crontab -l"
    echo ""
    echo "💾 Logs Location:"
    echo "   Client: $HOME/chatvpn/logs/update_client.log"
    echo "   Server: /opt/xvpn/logs/update_server.log"
}

# Run main function
main