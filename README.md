# XVPN - Intelligent VPN with AI Agents

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://www.docker.com/)
[![CI/CD](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-green)](https://github.com/Mehan42/chatVPN)
[![Security](https://img.shields.io/badge/security-A%2B-brightgreen)](https://github.com/Mehan42/chatVPN)

Complete VPN system with intelligent agents for automatic transport management, monitoring and self-healing.

## 🎯 Overview

XVPN is an intelligent VPN system that uses AI agents to automatically manage transport protocols, monitor connection health, and provide self-healing capabilities. Unlike traditional VPN solutions, XVPN continuously adapts to network conditions and automatically switches between transports to maintain optimal performance and security.

## 🌟 Features

### 🔐 Security & Privacy
- **AI-powered transport switching**: Automatic selection of optimal VPN transports based on real-time performance and security analysis
- **Real-time health monitoring**: Continuous assessment of connection quality, security posture, and anonymity level
- **Multi-transport support**: VLESS, VMess, Trojan, Shadowsocks, and other protocols with automatic fallback
- **IPv6 dual-stack support**: Full IPv4/IPv6 connectivity with automatic dual-stack optimization
- **Proxy modes**: SOCKS5, HTTP, transparent proxy, and auto-detection modes for maximum compatibility
- **Secure TLS connections**: End-to-end encryption with certificate pinning and mutual authentication
- **Automatic failover**: Seamless transport switching on failures with zero downtime
- **Smart load balancing**: Traffic distribution based on performance metrics and security considerations

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

## 🚀 Quick Installation

### Server Installation

```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Install server components
sudo ./installer/install_xvpn.sh
```

### Client Installation

```bash
# Clone the repository
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN

# Install client components (run as regular user, not root)
./install_client.sh
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

1. Get client configuration from Telegram bot
2. Place `client.json` in `~/chatvpn/client/clients/`
3. Launch GUI: `python3 ~/chatvpn/client/chatvpn_gui.py`

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

# View logs
xvpn-cli logs

# Manage UUID
xvpn-cli uuid <new-uuid>
```

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