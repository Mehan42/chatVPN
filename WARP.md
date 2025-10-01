# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

XVPN is an intelligent VPN system with AI agents for automated transport management, monitoring, and self-recovery. It consists of server-side components (Flask API, Main Agent, Telegram Bot) and client-side components (GUI, State Machine, Health Monitor).

## Development Commands

### Server Development

**Setup and Installation:**
```bash
# Install server (requires root)
sudo ./server/install_server.sh

# Manual installation of dependencies
sudo apt update && sudo apt install -y python3 python3-venv curl jq

# Start all services
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot
```

**Development Testing:**
```bash
# Test API endpoints
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health | jq .
curl -sk https://127.0.0.1:8443/transports/manifest.json | jq .
curl -sk -X POST https://127.0.0.1:8443/mcp/v1/admin.newclient

# Check service status
sudo systemctl status xvpn-*

# View logs
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f  
sudo journalctl -u xvpn-bot -f
```

**Database Operations:**
```bash
# View recent logs
python3 /opt/xvpn/agent/db.py

# Database statistics
sqlite3 /opt/xvpn/agent/db/agent.db "SELECT COUNT(*) FROM logs;"

# View recent agent events  
sqlite3 /opt/xvpn/agent/db/agent.db "SELECT datetime(ts, 'unixepoch'), state, action, result FROM logs WHERE component='agent' ORDER BY ts DESC LIMIT 10;"
```

### Client Development

**Setup and Testing:**
```bash
# Install client dependencies (user, not root)
./install_client.sh

# Set server URL
export XVPN_SERVER=https://your-server-ip:8443

# Test client components
uv run ~/chatvpn/client/health.py
uv run ~/chatvpn/client/state_machine.py

# Start client GUI
python3 ~/chatvpn/client/chatvpn_gui.py

# Check client logs
tail -f ~/chatvpn/client/logs/state.log
tail -f ~/chatvpn/client/logs/health.log
```

**Client Service Management:**
```bash
# Enable user service
systemctl --user enable xvpn-client
systemctl --user start xvpn-client

# Check status
systemctl --user status xvpn-client
journalctl --user -u xvpn-client -f
```

### Testing and Validation

**Run CI/CD pipeline locally:**
```bash
# Lint Python files
find . -name "*.py" -exec flake8 {} \; || true
find . -name "*.py" -exec black --check {} \; || true

# Test agent modules
cd server && python agent/health.py
python agent/db.py

# Validate JSON configuration files
find . -name "*.json" -exec python -m json.tool {} \; > /dev/null
```

**Integration Testing:**
```bash
# Test complete flow
pytest tests/ -v  # (if tests exist)

# Manual integration test
python3 -c "import sys; sys.path.append('server'); from api.app import app; print('✅ API imports successfully')"
```

## Architecture Overview

### Core Components

**Server Side (runs on `/opt/xvpn/`):**

1. **Flask API Agent** (`server/api/app.py`) - MCP Gateway
   - Endpoints: `/transports/manifest.json`, `/clients/<uuid>.json`, `/mcp/v1/*`
   - Handles client configurations, health checks, and admin operations
   - Logs all events to SQLite database

2. **Main Agent** (`server/agent/agent.py`) - State Machine & RAG
   - States: IDLE → DISCOVER → CONNECTING → ACTIVE → FALLBACK
   - Manages transport switching based on mask_score and health checks
   - Uses knowledge base for automated recovery protocols

3. **Telegram Bot Agent** (`server/admin/tg_bot.py`) - Management Interface
   - Commands: `/status`, `/newclient`, `/rotate`, `/report`
   - Admin interface for client management and monitoring
   - Integrates with Flask API for operations

**Client Side (runs in `~/chatvpn/client/`):**

1. **GUI Application** (`client/chatvpn_gui.py`) - User Interface
   - Status display, VPN on/off controls, mask score visualization
   - Fetches configurations from server or Telegram bot

2. **Backend Logic** (`client/chatvpn_backend.py`) - Core Functions
   - Configuration fetching, Xray process management
   - IP checking, VPN status monitoring

3. **State Machine** (`client/state_machine.py`) - Connection Management
   - Automatic transport discovery and switching
   - Client-side failover logic

4. **Health Monitor** (`client/health.py`) - Connection Quality Assessment
   - Mask score calculation (1-5 scale)
   - IP leak detection, TLS profile validation

### Data Flow

1. **Configuration Distribution**: Flask API serves client configs and transport manifests
2. **Health Monitoring**: Both client and server continuously assess connection quality
3. **Automatic Recovery**: RAG system executes protocols from knowledge base when issues occur
4. **Admin Management**: Telegram bot provides real-time monitoring and control

### Key Directories

**Server:**
- `/opt/xvpn/agent/db/` - SQLite database with logs, protocols, fallback resources
- `/opt/xvpn/agent/knowledge/` - RAG knowledge base (protocols.md, fallback.json)
- `/opt/xvpn/core/clients/` - Client configuration files
- `/opt/xvpn/logs/` - Service logs

**Client:**
- `~/chatvpn/client/clients/` - Local client configurations
- `~/chatvpn/client/transports/` - Cached transport manifests
- `~/chatvpn/client/logs/` - Client operation logs

### State Management

**Agent States:**
- `IDLE` - Initial state, waiting for instructions
- `DISCOVER` - Finding and testing available transports  
- `CONNECTING` - Establishing connection to selected transport
- `ACTIVE` - Successfully connected and monitoring
- `FALLBACK` - Using backup resources due to primary failure

**Transport Switching Logic:**
- Mask score < 3 triggers automatic transport switch
- Failed connections after 3 attempts move to next transport
- Periodic health checks maintain connection quality
- RAG protocols handle specific failure scenarios

## Environment Configuration

**Required Environment Variables:**

Server:
```bash
BOT_TOKEN=<telegram_bot_token>
CHAT_ID=<admin_telegram_chat_id>
API_BASE_URL=https://127.0.0.1:8443
```

Client:
```bash  
XVPN_SERVER=https://your-server-ip:8443
```

## Troubleshooting

**Common Server Issues:**
```bash
# Check if services are running
sudo systemctl status xvpn-*

# Verify API accessibility
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health

# Check database integrity
python3 /opt/xvpn/agent/db.py

# Review agent logs for errors
sudo journalctl -u xvpn-agent -n 50
```

**Common Client Issues:**
```bash
# Verify client configuration exists
ls -la ~/chatvpn/client/clients/

# Test server connectivity
curl -sk $XVPN_SERVER/transports/manifest.json

# Check health monitoring
python3 ~/chatvpn/client/health.py

# Review client logs
tail -f ~/chatvpn/client/logs/state.log
```

## CI/CD Integration

The project uses GitHub Actions for automated testing and deployment:

- **Testing**: Linting, module imports, configuration validation
- **Security**: Secret scanning, hardcoded credential detection  
- **Build**: Artifact creation for server and client components
- **Deploy**: Staging and production deployment with rollback
- **Monitoring**: Telegram notifications for deployment status

Deploy environments are configured through GitHub secrets: `STAGING_*` and `PROD_*` variables for SSH access and Telegram notifications.

## Development Notes

- All server paths use `/opt/xvpn/` prefix for consistency
- All client paths use `~/chatvpn/client/` prefix for user-space operation
- Database operations are logged for full audit trail
- Health monitoring runs continuously with configurable thresholds
- Transport selection uses priority-based algorithm with failure tracking
- RAG knowledge base enables automated incident response

The system is designed for autonomous operation with minimal manual intervention, using AI agents for intelligent transport management and self-healing capabilities.
