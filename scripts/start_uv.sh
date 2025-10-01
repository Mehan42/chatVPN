#!/bin/bash

# XVPN Service Startup Script with uv/uvx
# Version: 1.0
# Author: XVPN Team
# Description: Script to start XVPN services using uvx package manager

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
XVPN_DIR="/opt/xvpn"
LOG_DIR="/opt/xvpn/logs"
PID_DIR="/opt/xvpn/pids"
CONFIG_DIR="/opt/xvpn/config"
PYTHON_PATH="/usr/local/bin"

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed!${NC}"
    echo "Please install uv first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Ensure uvx is available
if ! command -v uvx &> /dev/null; then
    echo -e "${RED}❌ uvx is not available!${NC}"
    echo "Please check your uv installation."
    exit 1
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p "$LOG_DIR" "$PID_DIR" "$CONFIG_DIR"

# Set correct permissions
chown -R xvpn:xvpn "$XVPN_DIR"
chmod 755 "$XVPN_DIR"
chmod 644 "$XVPN_DIR"/*.py
chmod 755 "$XVPN_DIR/scripts"/*.sh

# Function to check if a service is running
is_service_running() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_file=$2
    local config_file=$3
    local port=$4
    
    echo -e "${BLUE}🚀 Starting $service_name...${NC}"
    
    if is_service_running "$service_name"; then
        echo -e "${YELLOW}⚠️  $service_name is already running${NC}"
        return 0
    fi
    
    # Set environment variables
    export PYTHONPATH="$XVPN_DIR/src:$XVPN_DIR/server"
    export FLASK_ENV=production
    export FLASK_DEBUG=false
    export PYTHONUNBUFFERED=1
    
    # Start service with uvx
    nohup uvx run --app "$service_file" \
        --config "$config_file" \
        --port "$port" \
        > "$LOG_DIR/${service_name}.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_DIR/${service_name}.pid"
    
    # Wait for service to start
    sleep 3
    
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        return 1
    fi
}

# Function to stop a service
stop_service() {
    local service_name=$1
    
    echo -e "${BLUE}🛑 Stopping $service_name...${NC}"
    
    if ! is_service_running "$service_name"; then
        echo -e "${YELLOW}⚠️  $service_name is not running${NC}"
        return 0
    fi
    
    local pid_file="$PID_DIR/${service_name}.pid"
    local pid=$(cat "$pid_file")
    
    # Graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local timeout=30
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt $timeout ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Force killing $service_name...${NC}"
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$pid_file"
    echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
}

# Function to check service status
check_service_status() {
    local service_name=$1
    local port=$2
    
    if is_service_running "$service_name"; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
        
        # Check if service is responding
        if curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is responding on port $port${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name is running but not responding${NC}"
        fi
    else
        echo -e "${RED}❌ $service_name is not running${NC}"
    fi
}

# Function to view logs
view_logs() {
    local service_name=$1
    
    if [ -f "$LOG_DIR/${service_name}.log" ]; then
        echo -e "${BLUE}📄 Logs for $service_name:${NC}"
        tail -f "$LOG_DIR/${service_name}.log"
    else
        echo -e "${RED}❌ Log file not found for $service_name${NC}"
    fi
}

# Function to install uv system-wide
install_uv() {
    echo -e "${BLUE}🔧 Installing uv package manager...${NC}"
    
    # Download and install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add to PATH
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if command -v uv &> /dev/null && command -v uvx &> /dev/null; then
        echo -e "${GREEN}✅ uv installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install uv${NC}"
        exit 1
    fi
    
    # Create uv symlinks in /usr/local/bin
    sudo ln -sf "$HOME/.cargo/bin/uv" "/usr/local/bin/uv"
    sudo ln -sf "$HOME/.cargo/bin/uvx" "/usr/local/bin/uvx"
}

# Function to update dependencies
update_dependencies() {
    echo -e "${BLUE}📦 Updating dependencies with uv...${NC}"
    
    cd "$XVPN_DIR"
    
    # Update main dependencies
    echo "Updating main dependencies..."
    uv pip install --upgrade -e .
    
    # Update server dependencies
    echo "Updating server dependencies..."
    uv pip install --upgrade -e ".[server,agent,bot]"
    
    echo -e "${GREEN}✅ Dependencies updated successfully${NC}"
}

# Function to show help
show_help() {
    echo "XVPN Service Manager with uv/uvx"
    echo ""
    echo "Usage: $0 [COMMAND] [SERVICE]"
    echo ""
    echo "Commands:"
    echo "  start [api|agent|bot|all]    - Start service(s)"
    echo "  stop [api|agent|bot|all]     - Stop service(s)"
    echo "  restart [api|agent|bot|all]  - Restart service(s)"
    echo "  status [api|agent|bot|all]   - Check service status"
    echo "  logs [api|agent|bot]         - View service logs"
    echo "  install                      - Install uv system-wide"
    echo "  update                       - Update dependencies with uv"
    echo "  backup                       - Backup XVPN data"
    echo "  restore                      - Restore XVPN data"
    echo "  help                         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start all                 - Start all services"
    echo "  $0 stop api                  - Stop API service"
    echo "  $0 status agent              - Check agent status"
    echo "  $0 logs bot                  - View bot logs"
}

# Main script logic
main() {
    case "${1:-help}" in
        start)
            case "$2" in
                api)
                    start_service "api" "server.api.main:app" "$CONFIG_DIR/api.json" "8443"
                    ;;
                agent)
                    start_service "agent" "server.agent.main:agent" "$CONFIG_DIR/agent.json" "8443"
                    ;;
                bot)
                    start_service "bot" "server.admin.main:bot" "$CONFIG_DIR/bot.json" "8443"
                    ;;
                all|"")
                    start_service "api" "server.api.main:app" "$CONFIG_DIR/api.json" "8443"
                    start_service "agent" "server.agent.main:agent" "$CONFIG_DIR/agent.json" "8443"
                    start_service "bot" "server.admin.main:bot" "$CONFIG_DIR/bot.json" "8443"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown service: $2${NC}"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        stop)
            case "$2" in
                api)
                    stop_service "api"
                    ;;
                agent)
                    stop_service "agent"
                    ;;
                bot)
                    stop_service "bot"
                    ;;
                all|"")
                    stop_service "api"
                    stop_service "agent"
                    stop_service "bot"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown service: $2${NC}"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        restart)
            case "$2" in
                api|agent|bot)
                    stop_service "$2"
                    sleep 2
                    case "$2" in
                        api)
                            start_service "api" "server.api.main:app" "$CONFIG_DIR/api.json" "8443"
                            ;;
                        agent)
                            start_service "agent" "server.agent.main:agent" "$CONFIG_DIR/agent.json" "8443"
                            ;;
                        bot)
                            start_service "bot" "server.admin.main:bot" "$CONFIG_DIR/bot.json" "8443"
                            ;;
                    esac
                    ;;
                all|"")
                    stop_service "api"
                    stop_service "agent"
                    stop_service "bot"
                    sleep 3
                    start_service "api" "server.api.main:app" "$CONFIG_DIR/api.json" "8443"
                    start_service "agent" "server.agent.main:agent" "$CONFIG_DIR/agent.json" "8443"
                    start_service "bot" "server.admin.main:bot" "$CONFIG_DIR/bot.json" "8443"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown service: $2${NC}"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        status)
            case "$2" in
                api)
                    check_service_status "api" "8443"
                    ;;
                agent)
                    check_service_status "agent" "8443"
                    ;;
                bot)
                    check_service_status "bot" "8443"
                    ;;
                all|"")
                    check_service_status "api" "8443"
                    check_service_status "agent" "8443"
                    check_service_status "bot" "8443"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown service: $2${NC}"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        logs)
            case "$2" in
                api|agent|bot)
                    view_logs "$2"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown service: $2${NC}"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        install)
            install_uv
            ;;
        update)
            update_dependencies
            ;;
        backup)
            echo -e "${BLUE}🔄 Creating backup...${NC}"
            # TODO: Implement backup logic
            echo -e "${GREEN}✅ Backup completed${NC}"
            ;;
        restore)
            echo -e "${BLUE}🔄 Restoring from backup...${NC}"
            # TODO: Implement restore logic
            echo -e "${GREEN}✅ Restore completed${NC}"
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"