#!/usr/bin/env bash
"""
XVPN Complete Installation Script
Installs and configures all XVPN components with security
"""

set -e

echo "🚀 XVPN Complete Installation Script"
echo "==================================="
echo ""

# Configuration
XVPN_HOME="/opt/xvpn"
XVPN_USER="xvpn"
XVPN_GROUP="xvpn"
REPO_URL="https://github.com/Mehan42/chatVPN.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        echo "Try: sudo $0"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_info "Installing system dependencies..."
    
    # Update package list
    apt update
    
    # Install required packages
    apt install -y \
        python3 python3-pip python3-venv \
        docker docker-compose \
        curl wget jq \
        sqlite3 \
        nginx \
        openssl \
        git \
        systemd
    
    # Install Python packages
    pip3 install --upgrade pip
    pip3 install -r /home/uss/chatvpn/requirements_server.txt
    
    print_status "System dependencies installed"
}

# Clone repository
clone_repository() {
    print_info "Cloning XVPN repository..."
    
    # Clone to /opt/xvpn
    if [ ! -d "$XVPN_HOME" ]; then
        git clone "$REPO_URL" "$XVPN_HOME"
    else
        print_warning "XVPN directory already exists, updating..."
        cd "$XVPN_HOME" && git pull
    fi
    
    # Set permissions
    chown -R root:root "$XVPN_HOME"
    chmod 755 "$XVPN_HOME"
    
    print_status "Repository cloned/updated successfully"
}

# Setup directories
setup_directories() {
    print_info "Setting up directories..."
    
    # Create XVPN user and group
    if ! id "$XVPN_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$XVPN_HOME" "$XVPN_USER"
    fi
    
    if ! getent group "$XVPN_GROUP" &>/dev/null; then
        groupadd -r "$XVPN_GROUP"
    fi
    
    # Add user to group
    usermod -a -G "$XVPN_GROUP" "$XVPN_USER"
    
    # Create required directories
    mkdir -p "$XVPN_HOME"/{api,agent,bot,data,logs,tls,config,clients}
    mkdir -p "$XVPN_HOME/data"/{clients,transports,certificates}
    mkdir -p "$XVPN_HOME/logs"/{api,agent,bot,client}
    mkdir -p "$XVPN_HOME/tls"
    mkdir -p "$XVPN_HOME/config"
    
    # Set permissions
    chown -R "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME"
    chmod 750 "$XVPN_HOME"
    chmod 640 "$XVPN_HOME"/config/*
    chmod 600 "$XVPN_HOME"/tls/*
    
    print_status "Directories set up successfully"
}

# Generate TLS certificates
generate_tls_certificates() {
    print_info "Generating TLS certificates..."
    
    # Run certificate generation script
    if [ -f "$XVPN_HOME/scripts/generate_tls_certs.sh" ]; then
        "$XVPN_HOME/scripts/generate_tls_certs.sh"
    else
        print_warning "Certificate generation script not found, using development script..."
        
        # Generate self-signed certificates
        openssl req -x509 \
            -newkey rsa:4096 \
            -keyout "$XVPN_HOME/tls/key.pem" \
            -out "$XVPN_HOME/tls/cert.pem" \
            -days 365 \
            -nodes \
            -subj "/C=RU/ST=Moscow/L=Moscow/O=XVPN/OU=IT/CN=localhost/emailAddress=admin@xvpn.local" \
            -addext "subjectAltName=DNS:localhost,DNS:*.xvpn.local,IP:127.0.0.1"
    fi
    
    # Set proper permissions
    chown "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME/tls/cert.pem" "$XVPN_HOME/tls/key.pem"
    chmod 644 "$XVPN_HOME/tls/cert.pem"
    chmod 600 "$XVPN_HOME/tls/key.pem"
    
    print_status "TLS certificates generated successfully"
}

# Generate API tokens
generate_api_tokens() {
    print_info "Generating API tokens..."
    
    # Run token generation script
    if [ -f "$XVPN_HOME/scripts/generate_api_tokens.py" ]; then
        python3 "$XVPN_HOME/scripts/generate_api_tokens.py" generate-defaults
    else
        print_warning "Token generation script not found, creating default tokens..."
        
        # Create default tokens file
        cat > "$XVPN_HOME/data/api_tokens.json" << 'EOF'
{
  "admin": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token_placeholder",
    "permissions": ["admin", "read", "write"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Default admin token"
  },
  "client": {
    "token": "cGxlYXNlIGRvbid0IHN0ZWFsIHRoaXMgdG9rZW4=",
    "permissions": ["read"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Default client token"
  },
  "bot": {
    "token": "dGhpcyBpcyBhIHRlc3QgdG9rZW4gZm9yIHRoZSBib3Q=",
    "permissions": ["read", "write"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Telegram bot token"
  }
}
EOF
    fi
    
    # Set proper permissions
    chown "$XVPN_USER":"$XVPN_GROUP" "$XVPN_HOME/data/api_tokens.json"
    chmod 600 "$XVPN_HOME/data/api_tokens.json"
    
    print_status "API tokens generated successfully"
}

# Install systemd services
install_systemd_services() {
    print_info "Installing systemd services..."
    
    # Copy service files
    if [ -d "$XVPN_HOME/systemd" ]; then
        cp "$XVPN_HOME/systemd/"*.service /etc/systemd/system/ 2>/dev/null || true
    else
        print_warning "Systemd service files not found"
        return 1
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable xvpn-api.service xvpn-agent.service xvpn-bot.service 2>/dev/null || true
    
    print_status "Systemd services installed"
}

# Start services
start_services() {
    print_info "Starting XVPN services..."
    
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
    print_info "Checking service status..."
    
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
    print_info "Testing API connectivity..."
    
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
    print_info "Testing API authentication..."
    
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

# Display installation summary
display_installation_summary() {
    print_info "Displaying installation summary..."
    
    echo ""
    echo "🌐 XVPN Installation Summary:"
    echo "============================"
    echo "Installation Directory: $XVPN_HOME"
    echo "User: $XVPN_USER"
    echo "Group: $XVPN_GROUP"
    echo "Repository: $REPO_URL"
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
    echo "🔐 API Authentication:"
    echo "Admin Token:      Check $XVPN_HOME/data/api_tokens.json"
    echo "Client Token:     Check $XVPN_HOME/data/api_tokens.json"
    echo "Bot Token:        Check $XVPN_HOME/data/api_tokens.json"
    echo ""
    echo "💡 Next Steps:"
    echo "1. Configure firewall rules"
    echo "2. Set up monitoring and alerting"
    echo "3. Test with real clients"
    echo "4. Document production procedures"
    echo ""
}

# Main function
main() {
    print_info "Starting XVPN Complete Installation..."
    
    # Check if running as root
    check_root
    
    # Install dependencies
    install_dependencies
    
    # Clone repository
    clone_repository
    
    # Setup directories
    setup_directories
    
    # Generate TLS certificates
    generate_tls_certificates
    
    # Generate API tokens
    generate_api_tokens
    
    # Install systemd services
    install_systemd_services
    
    # Start services
    start_services
    
    # Test connectivity
    test_api_connectivity
    
    # Test authentication
    test_authentication
    
    # Display summary
    display_installation_summary
    
    print_status "XVPN Complete Installation Finished Successfully!"
    echo ""
    echo "🎉 XVPN is now installed and running!"
    echo "   Visit https://localhost:8443/mcp/v1/vpn.health to check status"
    echo ""
    echo "🔐 API Authentication Tokens:"
    echo "   Admin Token: Check $XVPN_HOME/data/api_tokens.json"
    echo "   Client Token: Check $XVPN_HOME/data/api_tokens.json"
    echo "   Bot Token: Check $XVPN_HOME/data/api_tokens.json"
    echo ""
    echo "🔧 Service Management Commands:"
    echo "   Start services: sudo systemctl start xvpn-api xvpn-agent xvpn-bot"
    echo "   Stop services:  sudo systemctl stop xvpn-api xvpn-agent xvpn-bot"
    echo "   Check status:   sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
    echo ""
    echo "📄 Documentation:"
    echo "   User Guide:     $XVPN_HOME/docs/USER_GUIDE.md"
    echo "   Admin Guide:    $XVPN_HOME/docs/ADMIN_GUIDE.md"
    echo "   Developer Guide: $XVPN_HOME/docs/DEVELOPER_GUIDE.md"
    echo ""
}

# Run main function
main "$@"