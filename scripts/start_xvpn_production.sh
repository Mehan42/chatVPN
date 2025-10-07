#!/usr/bin/env bash
"""
XVPN Production Startup Script
Starts all XVPN services in production environment
"""

set -e

echo "🚀 XVPN Production Startup Script"
echo "================================="

# Configuration
XVPN_HOME="/opt/xvpn"
XVPN_USER="xvpn"
XVPN_GROUP="xvpn"

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

# Check prerequisites
check_prerequisites() {
    print_warning "Checking prerequisites..."
    
    # Check if XVPN user exists
    if ! id "$XVPN_USER" &>/dev/null; then
        print_warning "Creating XVPN user..."
        useradd -r -s /bin/false -d "$XVPN_HOME" "$XVPN_USER"
    fi
    
    # Check if XVPN group exists
    if ! getent group "$XVPN_GROUP" &>/dev/null; then
        print_warning "Creating XVPN group..."
        groupadd -r "$XVPN_GROUP"
    fi
    
    # Add user to group
    usermod -a -G "$XVPN_GROUP" "$XVPN_USER"
    
    # Check if directories exist
    mkdir -p "$XVPN_HOME"/{api,agent,bot,data,logs,tls,config}
    
    # Set permissions
    chown -R "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME"
    chmod 750 "$XVPN_HOME"
    
    # Check if certificates exist
    if [ ! -f "$XVPN_HOME/tls/cert.pem" ] || [ ! -f "$XVPN_HOME/tls/key.pem" ]; then
        print_warning "Generating TLS certificates..."
        "$XVPN_HOME/scripts/generate_tls_certs.sh"
    fi
    
    # Check if API tokens exist
    if [ ! -f "$XVPN_HOME/data/api_tokens.json" ]; then
        print_warning "Generating API tokens..."
        "$XVPN_HOME/scripts/generate_api_tokens.py" generate-defaults
    fi
    
    print_status "Prerequisites checked and satisfied"
}

# Install systemd services
install_systemd_services() {
    print_warning "Installing systemd services..."
    
    # Copy service files
    cp "$XVPN_HOME/systemd/"*.service /etc/systemd/system/ 2>/dev/null || true
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable xvpn-api.service xvpn-agent.service xvpn-bot.service 2>/dev/null || true
    
    print_status "Systemd services installed"
}

# Start services
start_services() {
    print_warning "Starting XVPN services..."
    
    # Start services
    systemctl start xvpn-api.service
    systemctl start xvpn-agent.service
    systemctl start xvpn-bot.service
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    check_service_status
    
    print_status "XVPN services started"
}

# Check service status
check_service_status() {
    print_warning "Checking service status..."
    
    services=("xvpn-api" "xvpn-agent" "xvpn-bot")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service.service"; then
            print_status "$service is running"
        else
            print_error "$service is not running"
            systemctl status "$service.service" --no-pager || true
        fi
    done
}

# Test API connectivity
test_api_connectivity() {
    print_warning "Testing API connectivity..."
    
    # Test HTTPS endpoint
    if command -v curl &>/dev/null; then
        response=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/mcp/v1/vpn.health || echo "000")
        
        if [ "$response" = "200" ]; then
            print_status "API connectivity test PASSED"
        else
            print_error "API connectivity test FAILED (Status: $response)"
        fi
    else
        print_warning "curl not found, skipping API connectivity test"
    fi
}

# Test authentication
test_authentication() {
    print_warning "Testing API authentication..."
    
    # Get admin token
    if [ -f "$XVPN_HOME/data/api_tokens.json" ]; then
        admin_token=$(python3 -c "
import json
with open('$XVPN_HOME/data/api_tokens.json', 'r') as f:
    tokens = json.load(f)
    if 'admin' in tokens:
        print(tokens['admin']['token'])
" 2>/dev/null || echo "")
        
        if [ -n "$admin_token" ]; then
            print_status "Admin token found"
            
            # Test authenticated access
            if command -v curl &>/dev/null; then
                response=$(curl -k -s -H "Authorization: Bearer $admin_token" \
                    -o /dev/null -w "%{http_code}" \
                    https://localhost:8443/mcp/v1/admin.newclient || echo "000")
                
                if [ "$response" = "401" ] || [ "$response" = "403" ]; then
                    print_status "Authentication test PASSED (access denied as expected)"
                elif [ "$response" = "200" ]; then
                    print_warning "Authentication test result: Access granted (may be intentional)"
                else
                    print_error "Authentication test FAILED (Status: $response)"
                fi
            else
                print_warning "curl not found, skipping authentication test"
            fi
        else
            print_warning "No admin token found, skipping authentication test"
        fi
    else
        print_warning "API tokens file not found, skipping authentication test"
    fi
}

# Display service information
display_service_info() {
    print_warning "Displaying service information..."
    
    echo ""
    echo "🌐 XVPN Service Information:"
    echo "============================"
    echo "API Service:     https://localhost:8443/mcp/v1/vpn.health"
    echo "Transport Manifest: https://localhost:8443/transports/manifest.json"
    echo "Admin Endpoint:  https://localhost:8443/mcp/v1/admin.newclient"
    echo ""
    echo "📁 Important Directories:"
    echo "TLS Certificates: $XVPN_HOME/tls/"
    echo "API Tokens:       $XVPN_HOME/data/api_tokens.json"
    echo "Client Configs:   $XVPN_HOME/data/clients/"
    echo "Logs:             $XVPN_HOME/logs/"
    echo ""
    echo "🔧 Service Management:"
    echo "Start services:   sudo systemctl start xvpn-api xvpn-agent xvpn-bot"
    echo "Stop services:    sudo systemctl stop xvpn-api xvpn-agent xvpn-bot"
    echo "Check status:     sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
    echo "View logs:        sudo journalctl -u xvpn-api -f"
    echo ""
}

# Main function
main() {
    print_warning "Starting XVPN Production Setup..."
    
    # Check prerequisites
    check_prerequisites
    
    # Install systemd services
    install_systemd_services
    
    # Start services
    start_services
    
    # Test connectivity
    test_api_connectivity
    
    # Test authentication
    test_authentication
    
    # Display service information
    display_service_info
    
    print_status "XVPN Production Setup Completed Successfully!"
    echo ""
    echo "🎉 XVPN is now running in production mode!"
    echo "   Visit https://localhost:8443/mcp/v1/vpn.health to check status"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Configure firewall rules"
    echo "   2. Set up monitoring and alerting"
    echo "   3. Test with real clients"
    echo "   4. Document production procedures"
}

# Run main function
main "$@"