# XVPN - Intelligent VPN with AI Agents and Proxy Integration

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://www.docker.com/)
[![CI/CD](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-green)](https://github.com/Mehan42/chatVPN)
[![Security](https://img.shields.io/badge/security-A%2B-brightgreen)](https://github.com/Mehan42/chatVPN)

Complete VPN system with intelligent agents for automatic transport management, monitoring and self-healing, plus ProxyBroker2 integration for enhanced proxy discovery.

## 🎯 Overview

XVPN is an intelligent VPN system that uses AI agents to automatically manage transport protocols, monitor connection health, and provide self-healing capabilities. Unlike traditional VPN solutions, XVPN continuously adapts to network conditions and automatically switches between transports to maintain optimal performance and security.

XVPN now includes integration with ProxyBroker2 for enhanced proxy discovery and management capabilities, providing robust solutions for bypassing network restrictions.

## 🌟 Features

### 🔐 Security & Privacy
- **AI-powered transport switching**: Automatic selection of optimal VPN transports based on real-time performance and security analysis
- **Real-time health monitoring**: Continuous assessment of connection quality, security posture, and anonymity level
- **Multi-transport support**: VLESS, VMess, Trojan, Shadowsocks, WireGuard, and other protocols with automatic fallback
- **IPv6 dual-stack support**: Full IPv4/IPv6 connectivity with automatic dual-stack optimization
- **Proxy modes**: SOCKS5, HTTP, transparent proxy, and auto-detection modes for maximum compatibility
- **Secure TLS connections**: End-to-end encryption with certificate pinning and mutual authentication
- **Automatic failover**: Seamless transport switching on failures with zero downtime
- **Smart load balancing**: Traffic distribution based on performance metrics and security considerations
- **ProxyBroker2 Integration**: Automatic discovery and validation of proxies from 50+ sources for enhanced bypass capabilities

### 🤖 Intelligence & Automation
- **AI Orchestration**: Advanced AI agents powered by ChromaDB RAG system for intelligent decision-making
- **Self-healing capabilities**: Automatic recovery from network issues, transport failures, and system errors
- **Predictive transport selection**: Machine learning algorithms predict optimal transports based on historical data
- **Dynamic configuration updates**: Real-time configuration adjustments without service interruption
- **Intelligent error handling**: Automatic error detection, classification, and resolution
- **Automated proxy management**: Continuous discovery and validation of working proxies for bypass scenarios

### 🛠️ Management & Monitoring
- **Telegram Bot Interface**: Full-featured management via Telegram with real-time notifications
- **Comprehensive CLI**: Powerful command-line interface for advanced users and automation
- **Web Dashboard**: Modern web interface for monitoring and configuration (coming soon)
- **Extensive logging**: Structured JSON logging with Prometheus metrics integration
- **Centralized monitoring**: Unified view of all system components with alerting capabilities
- **Performance analytics**: Detailed performance metrics and historical data analysis
- **Proxy pool management**: Centralized proxy discovery, validation, and distribution

### 🚀 Deployment & Scalability
- **Containerized deployment**: Docker and Docker Compose support for easy deployment
- **Kubernetes ready**: Helm charts and Kubernetes manifests for scalable deployments
- **Microservices architecture**: Modular design with clear separation of concerns
- **Zero-downtime updates**: Rolling updates and blue-green deployment strategies
- **Multi-region support**: Distributed deployment across multiple geographic regions
- **Fault tolerance**: Built-in redundancy and disaster recovery mechanisms
- **Proxy distribution network**: Scalable proxy server architecture for serving proxies to multiple clients

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git
- Docker (optional, for containerized deployment)
\n## 🚀 Flexible Deployment

XVPN now supports flexible deployment in arbitrary directories with automatic update capabilities:

### Client Installation in Custom Directory
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client
```

### Server Installation
```bash
sudo ./install_server_flexible.sh
```

### Automatic Updates
The system includes advanced deployment watcher that monitors repository changes and automatically updates clients and servers:

```bash
python3 advanced_deployment_watcher.py --config deployment_config.json
```

See [FLEXIBLE_DEPLOYMENT_GUIDE.md](FLEXIBLE_DEPLOYMENT_GUIDE.md) for detailed documentation.


### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Mehan42/chatVPN.git
   cd chatVPN
   ```

2. **Install dependencies**:
   ```bash
   # Install main dependencies
   pip install -r requirements.txt
   
   # Install server dependencies
   pip install -r requirements_server.txt
   
   # Install client dependencies (optional)
   pip install -r requirements_client.txt
   
   # Install ProxyBroker2 integration (optional but recommended)
   pip install git+https://github.com/bluet/proxybroker2.git
   # Or use the XVPN installation script
   ./server/install_proxybroker2.sh
   ```

3. **Configure environment**:
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

4. **Run installation scripts**:
   ```bash
   # Install server components
   ./install_server.sh
   
   # Install systemd services (optional)
   ./install_systemd_services.sh
   
   # Run post-installation setup
   ./post_install_setup.sh
   ```

### Usage

#### Find and Check Proxies
```bash
# Find 10 working HTTP(S) proxies
python -m proxybroker find --types HTTP HTTPS --limit 10

# Find proxies from specific countries
python -m proxybroker find --types HTTP HTTPS --countries US GB DE --limit 20
```

#### Grab Proxies (Without Checking)
```bash
# Quickly grab proxies without validation
python -m proxybroker grab --countries US --limit 50 --outfile proxies.txt
```

#### Run Local Proxy Server
```bash
# Run a local proxy server that distributes requests
python -m proxybroker serve --host 127.0.0.1 --port 8888 --types HTTP HTTPS
```

### Client Usage

#### Basic Client Setup
```bash
# Clone client repository (if separate)
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN/client

# Install client dependencies
pip install -r requirements_client.txt

# Configure client
cp client/example_client_config.json client/config.json
nano client/config.json
```

#### Run Client
```bash
# Start client with configuration
python client/chatvpn_gui.py
```

## 📋 Requirements

### Core Requirements
- Python 3.10+
- aiohttp >= 3.8.0
- aiodns >= 3.0.0
- maxminddb >= 2.0.0
- attrs >= 21.0.0
- cachetools >= 5.0.0
- click >= 8.0.0

### Optional Requirements
- Docker (for containerized deployment)
- Docker Compose (for multi-container setups)
- Kubernetes (for orchestrated deployments)
- ProxyBroker2 (for enhanced proxy discovery)

### System Requirements
- **Minimum**: 1 CPU core, 2GB RAM, 20GB disk space
- **Recommended**: 2+ CPU cores, 4GB+ RAM, 50GB+ disk space

## 🔧 Configuration

### Environment Variables
```bash
# Server configuration
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8443
export SERVER_SSL_CERT=/path/to/cert.pem
export SERVER_SSL_KEY=/path/to/key.pem

# Telegram bot configuration
export BOT_TOKEN=your_telegram_bot_token
export CHAT_ID=your_chat_id

# ProxyBroker2 configuration (optional)
export PROXY_TIMEOUT=8
export PROXY_MAX_CONN=200
export PROXY_MAX_TRIES=3
export PROXY_VERIFY_SSL=false
```

### Configuration Files
- `.env` - Environment variables
- `server/config.json` - Server configuration
- `client/config.json` - Client configuration
- `proxybroker/config.json` - ProxyBroker2 configuration

## 📊 Monitoring

### Health Checks
```bash
# Check server health
curl -k https://localhost:8443/mcp/v1/vpn.health

# Check server status
curl -k https://localhost:8443/mcp/v1/vpn.status
```

### Logs
```bash
# View server logs
journalctl -u xvpn-api -f

# View client logs
tail -f /var/log/xvpn/client.log
```

### Metrics
XVPN exposes Prometheus metrics for monitoring:
- Connection health metrics
- Transport performance metrics
- Proxy discovery metrics
- System resource metrics

## 🔌 ProxyBroker2 Integration

XVPN integrates with ProxyBroker2 to provide enhanced proxy discovery and management capabilities:

### Features
- **Automatic proxy discovery**: Find proxies from 50+ sources automatically
- **Proxy validation**: Real-time testing of proxy connectivity and anonymity
- **Load balancing**: Distribute requests across multiple working proxies
- **Failover mechanism**: Automatic switching when proxies become unavailable
- **Geographic filtering**: Select proxies based on country and region
- **Protocol support**: HTTP, HTTPS, SOCKS4, SOCKS5, and CONNECT methods
- **Anonymity levels**: Transparent, Anonymous, and High anonymity detection

### Architecture
- **Server-side**: Continuous proxy discovery and validation
- **Client-side**: Receive validated proxies from server
- **Local proxy server**: Distribute requests through external proxies
- **API integration**: Seamless communication between components

For detailed integration documentation, see [server/PROXY_INTEGRATION.md](server/PROXY_INTEGRATION.md)

## 🚀 Quick Start with Proxy Integration

1. **Install ProxyBroker2**:
   ```bash
   pip install git+https://github.com/bluet/proxybroker2.git
   ```

2. **Discover proxies**:
   ```python
   from server.proxy_integration import XVPNProxyManager
   
   # Initialize proxy manager
   manager = await XVPNProxyManager.create({
       'proxy_timeout': 8,
       'proxy_max_tries': 3
   })
   
   # Find HTTP/HTTPS proxies
   proxies = await manager.find_proxies(['HTTP', 'HTTPS'], limit=50)
   print(f"Found {len(proxies)} working proxies")
   ```

3. **Start proxy server**:
   ```bash
   # Run local proxy server that distributes requests
   python -m proxybroker serve --host 127.0.0.1 --port 8888 --types HTTP HTTPS SOCKS5
   ```

## 📋 Requirements

- Python 3.10+
- Docker (optional, for containerized deployment)
- Git (for cloning and updates)
- ProxyBroker2 (for proxy discovery features)

## 🛠️ Installation

### 1. Clone the repository:
```bash
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN
```

## 📚 Documentation

### User Guides
- [Installation Guide](INSTALLATION_GUIDE.md) - Complete installation instructions
- [User Guide](USER_GUIDE.md) - Complete usage instructions
- [Client Administration Guide](CLIENT_ADMINISTRATION_GUIDE.md) - Client management
- [Server Administration Guide](SERVER_ADMINISTRATION_GUIDE.md) - Server management

### Developer Guides
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Development Setup](DEVELOPMENT_SETUP.md) - Development environment setup
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Architecture Guide](ARCHITECTURE_GUIDE.md) - System architecture documentation

### Admin Guides
- [Security Guide](SECURITY.md) - Security best practices
- [Monitoring Guide](MONITORING_GUIDE.md) - Monitoring and alerting
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues and solutions
- [Performance Guide](PERFORMANCE_GUIDE.md) - Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please:
1. Check the [Documentation](#documentation)
2. Search existing [Issues](https://github.com/Mehan42/chatVPN/issues)
3. Create a new issue with detailed information about the problem
4. Join our [Community](COMMUNITY.md) for support

---

*Made with ❤️ for secure communications*

## 🎯 Overview

XVPN is an intelligent VPN system that uses AI agents to automatically manage transport protocols, monitor connection health, and provide self-healing capabilities. Unlike traditional VPN solutions, XVPN continuously adapts to network conditions and automatically switches between transports to maintain optimal performance and security.

## 🌟 Features

### 🔐 Security & Privacy
- **AI-powered transport switching**: Automatic selection of optimal VPN transports based on real-time performance and security analysis
- **Real-time health monitoring**: Continuous assessment of connection quality, security posture, and anonymity level
- **Multi-transport support**: VLESS, VMess, Trojan, Shadowsocks, WireGuard, and other protocols with automatic fallback
- **IPv6 dual-stack support**: Full IPv4/IPv6 connectivity with automatic dual-stack optimization
- **Proxy modes**: SOCKS5, HTTP, transparent proxy, and auto-detection modes for maximum compatibility
- **Secure TLS connections**: End-to-end encryption with certificate pinning and mutual authentication
- **Automatic failover**: Seamless transport switching on failures with zero downtime
- **Smart load balancing**: Traffic distribution based on performance metrics and security considerations
- **ProxyBroker2 Integration**: Automatic discovery and validation of proxies from 50+ sources for enhanced bypass capabilities

### 🤖 Intelligence & Automation
- **AI Orchestration**: Advanced AI agents powered by ChromaDB RAG system for intelligent decision-making
- **Self-healing capabilities**: Automatic recovery from network issues, transport failures, and system errors
- **Predictive transport selection**: Machine learning algorithms predict optimal transports based on historical data
- **Dynamic configuration updates**: Real-time configuration adjustments without service interruption
- **Intelligent error handling**: Automatic error detection, classification, and resolution
- **Automated proxy management**: Continuous discovery and validation of working proxies for bypass scenarios

### 🛠️ Management & Monitoring
- **Telegram Bot Interface**: Full-featured management via Telegram with real-time notifications
- **Comprehensive CLI**: Powerful command-line interface for advanced users and automation
- **Web Dashboard**: Modern web interface for monitoring and configuration (coming soon)
- **Extensive logging**: Structured JSON logging with Prometheus metrics integration
- **Centralized monitoring**: Unified view of all system components with alerting capabilities
- **Performance analytics**: Detailed performance metrics and historical data analysis
- **Proxy pool management**: Centralized proxy discovery, validation, and distribution

### 🚀 Deployment & Scalability
- **Containerized deployment**: Docker and Docker Compose support for easy deployment
- **Kubernetes ready**: Helm charts and Kubernetes manifests for scalable deployments
- **Microservices architecture**: Modular design with clear separation of concerns
- **Zero-downtime updates**: Rolling updates and blue-green deployment strategies
- **Multi-region support**: Distributed deployment across multiple geographic regions
- **Fault tolerance**: Built-in redundancy and disaster recovery mechanisms
- **Proxy distribution network**: Scalable proxy server architecture for serving proxies to multiple clients

## 🔌 ProxyBroker2 Integration

XVPN integrates with ProxyBroker2 to provide enhanced proxy discovery and management capabilities:

### Features
- **Automatic proxy discovery**: Find proxies from 50+ sources automatically
- **Proxy validation**: Real-time testing of proxy connectivity and anonymity
- **Load balancing**: Distribute requests across multiple working proxies
- **Failover mechanism**: Automatic switching when proxies become unavailable
- **Geographic filtering**: Select proxies based on country and region
- **Protocol support**: HTTP, HTTPS, SOCKS4, SOCKS5, and CONNECT methods
- **Anonymity levels**: Transparent, Anonymous, and High anonymity detection

### Architecture
- **Server-side**: Continuous proxy discovery and validation
- **Client-side**: Receive validated proxies from server
- **Local proxy server**: Distribute requests through external proxies
- **API integration**: Seamless communication between components

For detailed integration documentation, see [server/PROXY_INTEGRATION.md](server/PROXY_INTEGRATION.md)

## 🚀 Quick Start with Proxy Integration

1. **Install ProxyBroker2**:
   ```bash
   pip install git+https://github.com/bluet/proxybroker2.git
   ```

2. **Discover proxies**:
   ```python
   from server.proxy_integration import XVPNProxyManager
   
   # Initialize proxy manager
   manager = await XVPNProxyManager.create({
       'proxy_timeout': 8,
       'proxy_max_tries': 3
   })
   
   # Find HTTP/HTTPS proxies
   proxies = await manager.find_proxies(['HTTP', 'HTTPS'], limit=50)
   print(f"Found {len(proxies)} working proxies")
   ```

3. **Start proxy server**:
   ```bash
   # Run local proxy server that distributes requests
   python -m proxybroker serve --host 127.0.0.1 --port 8888 --types HTTP HTTPS SOCKS5
   ```

## 📋 Requirements

- Python 3.10+
- Docker (optional, for containerized deployment)
- Git (for cloning and updates)
- ProxyBroker2 (for proxy discovery features)

## 🛠️ Installation

### 1. Clone the repository:
```bash
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN
```

### 🤖 Intelligence & Automation
- **AI Orchestration**: Advanced AI agents powered by ChromaDB RAG system for intelligent decision-making
- **Self-healing capabilities**: Automatic recovery from network issues, transport failures, and system errors
- **Predictive transport selection**: Machine learning algorithms predict optimal transports based on historical data
- **Dynamic configuration updates**: Real-time configuration adjustments without service interruption
- **Intelligent error handling**: Automatic error detection, classification, and resolution

### 🛠️ Management & Monitoring
- **Telegram Bot Interface**: Full-featured management via Telegram with real-time notifications
- **Comprehensive CLI**: Powerful command-line interface for advanced users and automation
- **Web Dashboard**: Modern web interface for monitoring and configuration (coming soon)
- **Extensive logging**: Structured JSON logging with Prometheus metrics integration
- **Centralized monitoring**: Unified view of all system components with alerting capabilities
- **Performance analytics**: Detailed performance metrics and historical data analysis

### 🚀 Deployment & Scalability
- **Containerized deployment**: Docker and Docker Compose support for easy deployment
- **Kubernetes ready**: Helm charts and Kubernetes manifests for scalable deployments
- **Microservices architecture**: Modular design with clear separation of concerns
- **Zero-downtime updates**: Rolling updates and blue-green deployment strategies
- **Multi-region support**: Distributed deployment across multiple geographic regions
- **Fault tolerance**: Built-in redundancy and disaster recovery mechanisms

## 🏗️ Architecture

XVPN uses a hybrid architecture with separate components for VPN traffic and management:

### Port Configuration:
- **Port 443**: XRay VPN traffic (primary VPN endpoint)
- **Port 8443**: MCP/API management interface (internal use)
- **Optional Nginx**: Reverse proxy for external access routing

### Component Architecture:
1. **XRay Core** - Handles VPN tunneling on port 443
2. **MCP/API Server** - Management interface on port 8443
3. **Agent Service** - Local system management
4. **Orchestrator** - Coordination between components
5. **Nginx Proxy** - External traffic routing (optional)

Traffic flows:
- External VPN clients → Port 443 (XRay)
- Internal management → Port 8443 (MCP/API)
- External web access → Nginx routes to appropriate service

See [ARCHITECTURE_INFO.md](ARCHITECTURE_INFO.md) for detailed architecture information.

## 🚀 Quick Installation

### Server Installation

```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Install server components
sudo ./install_server.sh

# Run post-installation setup
sudo ./post_install_setup.sh
```

### Client Installation

```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Install client components (run as regular user, not root)
./install_client.sh
```

## 🏗️ Architecture Overview

XVPN uses a hybrid architecture with separate components for VPN traffic and management:

### Port Configuration:
- **Port 443**: XRay VPN traffic (primary VPN endpoint)
- **Port 8443**: MCP/API management interface (internal use)
- **Optional Nginx**: Reverse proxy for external access routing

### Component Architecture:
1. **XRay Core** - Handles VPN tunneling on port 443
2. **MCP/API Server** - Management interface on port 8443
3. **Agent Service** - Local system management
4. **Orchestrator** - Coordination between components
5. **Nginx Proxy** - External traffic routing (optional)

Traffic flows:
- External VPN clients → Port 443 (XRay)
- Internal management → Port 8443 (MCP/API)
- External web access → Nginx routes to appropriate service

### Alternative Installation (Universal)

If you need to install all dependencies at once:

Using uv (recommended - faster and more reliable):
```bash
# For server components only
uv pip install -r requirements_server.txt

# For client components only
uv pip install -r requirements_client.txt

# For development (both server and client)
uv pip install -r requirements_server.txt -r requirements_client.txt
```

Using pip (fallback option):
```bash
# For server components only
pip install -r requirements_server.txt

# For client components only  
pip install -r requirements_client.txt

# For development (both server and client)
pip install -r requirements_server.txt -r requirements_client.txt
```

Using PEX (autonomous executables - no virtual environment needed):
```bash
# Install pex
pip install pex

# Build server executables
./build_pex.sh server

# Build client executables  
./build_pex.sh client

# Build all executables
./build_pex.sh all

# Run built executables
chmod +x dist/pex/xvpn-*.pex
./dist/pex/xvpn-api.pex
```

## 🔧 Server Configuration

1. Set up Telegram bot token in `/opt/xvpn/.env`:
```bash
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_chat_id_here
```

2. Start services:
```bash
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot
```

3. Check status:
```bash
sudo systemctl status xvpn-api xvpn-agent xvpn-bot
```

## 🖥️ Client Configuration

### Standard Client Setup

1. Get client configuration from Telegram bot
2. Place `client.json` in `~/chatvpn/client/clients/`
3. Launch GUI: `python3 ~/chatvpn/client/chatvpn_gui.py`

### New Client Architecture (Recommended)

For the new client architecture with multi-server support, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Mehan42/chatVPN.git
   cd chatVPN/client
   ```

2. Install dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install curl jq

   # Install Xray for actual connection
   bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
   ```

3. Configure client:
   ```bash
   ./scripts/configure_client.sh
   ```

4. Get UUID from Telegram bot and fetch configuration:
   ```bash
   ./scripts/get_config.sh
   ```

5. Start client:
   ```bash
   ./scripts/start_client.sh
   ```

Then use generated profile with Xray:
```bash
xray run -config profiles/[your-uuid].json
```

## 🐳 Docker Deployment

For production environments, use Docker Compose:

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Advanced Features

### State Machine Architecture

XVPN uses a sophisticated state machine with the following states:
- **INITIALIZING**: System startup and initialization
- **IDLE**: Ready state, waiting for commands
- **CONFIG_FETCHING**: Retrieving configuration from server
- **CONFIG_VALIDATING**: Validating configuration integrity
- **STARTING**: Starting VPN connection
- **RUNNING**: VPN is active and functioning
- **HEALTH_CHECKING**: Performing health assessments
- **SWITCHING_TRANSPORT**: Switching to alternative transport
- **STOPPING**: Stopping VPN connection
- **ERROR**: Error state with automatic recovery
- **RECOVERING**: Recovery from errors
- **UPDATING**: Updating configuration or software

### AI Orchestration

The AI orchestrator uses:
- **ChromaDB**: Vector database for knowledge storage
- **RAG System**: Retrieval-Augmented Generation for context-aware decisions
- **LLM Aliases**: Configurable language model interfaces
- **Deterministic Rules**: Pre-defined fallback behaviors

### Transport Management

XVPN supports multiple transport protocols:
1. **VLESS + Reality**: High-performance, censorship-resistant
2. **VMess + WebSocket**: Compatible with most firewalls
3. **Trojan + TCP**: Classic trojan protocol
4. **Shadowsocks + AEAD**: Lightweight encryption
5. **Fallback protocols**: HTTP, SOCKS5, direct connections

### Monitoring & Metrics

XVPN provides comprehensive monitoring:
- **Health Score**: 0-5 rating of connection quality
- **Transport Metrics**: Performance and reliability data
- **Network Analysis**: Connectivity and latency measurements
- **Security Assessment**: TLS fingerprint and IP leak checks
- **Resource Usage**: CPU, memory, and network utilization

## 📈 Monitoring

### Health Endpoints
- `/mcp/v1/vpn.health`: Overall system health
- `/transports/manifest.json`: Available transports
- `/clients/{uuid}.json`: Client-specific configuration

### Prometheus Metrics
All services expose Prometheus-compatible metrics:
- API requests and response times
- Agent health scores
- Bot message counts
- Worker task processing
- Connection statistics

### Grafana Dashboards
Pre-built dashboards for:
- System overview
- Transport performance
- Health monitoring
- Security metrics

## 🚨 Emergency Procedures

In case of issues:

1. Check service status: `sudo systemctl status xvpn-*`
2. Review logs: `sudo journalctl -u xvpn-* -f`
3. Restart services: `sudo systemctl restart xvpn-*`
4. Check firewall: `sudo ufw status`

## 🔧 CLI Commands

XVPN provides a powerful CLI interface:

```bash
# Start VPN
xvpn-cli start

# Stop VPN
xvpn-cli stop

# Check status
xvpn-cli status

# Request configuration
xvpn-cli config

# Check health
xvpn-cli health

# List transports
xvpn-cli transport list

# Switch transport
xvpn-cli transport switch <transport-id>

# Test connectivity
xvpn-cli test

# Test protocol availability (for bypassing blocks)
xvpn-cli protocols

# Detect network blocks (for bypassing blocks)
xvpn-cli blocks

# View logs
xvpn-cli logs

# Manage UUID
xvpn-cli uuid <new-uuid>
```

### Block Bypass Commands

XVPN includes special commands for detecting and bypassing network blocks:

- `xvpn-cli protocols` - Test all available protocols to find working ones
- `xvpn-cli blocks` - Detect which ports and services are blocked by your ISP
- `xvpn-cli transport list` - List all available transport protocols
- `xvpn-cli transport switch <transport-id>` - Switch to a working transport protocol

## 🛡️ Security Features

### TLS Security
- **Certificate Pinning**: Protection against MITM attacks
- **Mutual Authentication**: Two-way verification
- **TLS 1.3**: Latest encryption standards
- **Perfect Forward Secrecy**: Key isolation

### Transport Security
- **Obfuscation**: Traffic masking techniques
- **Protocol Diversity**: Multiple fallback options
- **Dynamic Port Selection**: Adaptive port usage
- **Censorship Resistance**: Anti-blocking mechanisms

### Data Protection
- **Encrypted Storage**: Configuration file encryption
- **Zero-Knowledge Architecture**: No plaintext storage
- **Secure Erasure**: Automatic cleanup of sensitive data
- **Access Controls**: Role-based permissions

## 🏗️ Architecture

### Server Components

- **API Service**: RESTful interface for client communication
- **Agent Service**: Core intelligence and decision-making
- **Bot Service**: Telegram management interface
- **Worker Service**: Background task processing
- **Orchestrator**: AI-powered coordination
- **XRay Core**: VPN transport engine

### Client Components

- **GUI Application**: User interface with status indicators
- **State Machine**: Connection lifecycle management
- **Health Monitor**: Real-time connection assessment
- **Transport Manager**: Protocol selection and switching
- **Proxy Helper**: Proxy mode configuration
- **IPv6 Manager**: IPv6 connectivity management

### Infrastructure

- **Traefik**: Reverse proxy and load balancer
- **Redis**: Caching and message queuing
- **PostgreSQL**: Relational data storage
- **ChromaDB**: Vector database for AI knowledge
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and monitoring
- **Loki**: Log aggregation

## 📦 Dependencies

### Runtime Dependencies
- Python 3.10+
- Docker 20.10+
- Docker Compose 1.29+
- Git 2.30+
- Curl, Wget
- Systemd

### Python Packages
- Flask 2.3+
- Requests 2.31+
- Pydantic 2.0+
- SQLAlchemy 2.0+
- Redis-py 5.0+
- Celery 5.3+
- ChromaDB 0.4+
- Sentence Transformers 2.2+
- Telegram Bot API 20.0+
- Psutil 5.9+
- Uvicorn 0.23+
- Gunicorn 21.0+

## 🧪 Testing

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test module
pytest tests/unit/test_state_machine.py -v
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v

# Run API tests
pytest tests/integration/test_api.py -v
```

### Performance Tests
```bash
# Run performance tests
pytest tests/performance/ -v

# Run load tests
locust -f tests/performance/locustfile.py
```

### Security Tests
```bash
# Run security scans
bandit -r src/ server/ client/
safety check
trivy fs .
```

## 📚 Documentation

### User Guides
- [Installation Guide](INSTALLATION_GUIDE.md)
- [User Guide](USER_GUIDE.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)

### Developer Guides
- [Architecture Guide](ARCHITECTURE_GUIDE.md)
- [API Reference](API_REFERENCE.md)
- [Development Setup](DEVELOPMENT_SETUP.md)
- [Contributing Guide](CONTRIBUTING.md)

### Admin Guides
- [Server Administration](SERVER_ADMINISTRATION_GUIDE.md)
- [Client Administration](CLIENT_ADMINISTRATION_GUIDE.md)
- [Monitoring Guide](MONITORING_GUIDE.md)
- [Security Guide](SECURITY_GUIDE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Made with ❤️ for secure communications*