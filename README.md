# XVPN - Intelligent VPN with AI Agents

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://www.docker.com/)

Complete VPN system with intelligent agents for automatic transport management, monitoring and self-healing.

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

## 📊 Features

- **AI-powered transport switching**: Automatic selection of optimal VPN transports
- **Real-time health monitoring**: Continuous assessment of connection quality
- **Multi-transport support**: VLESS, VMess, Trojan, and other protocols
- **IPv6 dual-stack support**: Full IPv4/IPv6 connectivity
- **Proxy modes**: SOCKS5, HTTP, transparent proxy support
- **Secure TLS connections**: End-to-end encryption with certificate pinning
- **Automatic failover**: Seamless transport switching on failures
- **Smart load balancing**: Traffic distribution based on performance metrics

## 🔐 Security Features

- **Certificate pinning**: Protection against MITM attacks
- **Secure communication**: All API calls use HTTPS
- **Access controls**: Role-based permissions
- **Encrypted storage**: Configuration files encryption
- **Network isolation**: Service separation and firewalls

## 🛠️ Architecture

The system consists of:

- **Server components**:
  - API Gateway (Flask-based)
  - Main Agent (state machine + RAG)
  - Telegram Bot (management interface)
  - XRay Core (VPN engine)
  - AI Orchestrator (intelligent automation)

- **Client components**:
  - GUI Application
  - State Machine (connection management)
  - Health Monitor (quality assessment)
  - Transport Manager (automatic switching)

## 📈 Monitoring

- **Health endpoints**: `/mcp/v1/vpn.health`
- **Transport manifest**: `/transports/manifest.json`
- **Client configurations**: `/clients/{uuid}.json`
- **Performance metrics**: Available via Prometheus/Grafana

## 🚨 Emergency Procedures

In case of issues:

1. Check service status: `sudo systemctl status xvpn-*`
2. Review logs: `sudo journalctl -u xvpn-* -f`
3. Restart services: `sudo systemctl restart xvpn-*`
4. Check firewall: `sudo ufw status`

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