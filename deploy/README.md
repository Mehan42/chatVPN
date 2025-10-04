# XVPN Deployment

This directory contains deployment scripts and configuration for the XVPN system.

## 📁 Directory Structure

```
deploy/
├── deploy.sh              # Main deployment script
├── deployment_config.py   # Deployment configuration
├── docker/                # Docker deployment files
│   ├── Dockerfile.api
│   ├── Dockerfile.agent
│   ├── Dockerfile.bot
│   ├── Dockerfile.worker
│   └── Dockerfile.orchestrator
├── kubernetes/            # Kubernetes deployment files
│   ├── xvpn-deployment.yaml
│   ├── xvpn-service.yaml
│   └── xvpn-ingress.yaml
├── ansible/               # Ansible deployment files
│   ├── inventory/
│   ├── playbooks/
│   └── roles/
├── terraform/             # Terraform infrastructure files
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── helm/                  # Helm charts
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
```

## 🚀 Deployment

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10+

### Quick Deployment

```bash
# Deploy to staging environment
./deploy.sh staging

# Deploy to production environment
./deploy.sh production

# Deploy specific version
./deploy.sh production 1.0.0

# Dry run (without actually starting services)
./deploy.sh staging latest true
```

### Docker Deployment

```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/

# Check deployment status
kubectl get deployments

# Check service status
kubectl get services

# View logs
kubectl logs -f deployment/xvpn-api
```

### Ansible Deployment

```bash
# Run Ansible playbook
ansible-playbook -i ansible/inventory/hosts ansible/playbooks/deploy-xvpn.yml

# Check service status
ansible -i ansible/inventory/hosts all -m shell -a "systemctl status xvpn-*"
```

### Terraform Deployment

```bash
# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure changes
terraform apply

# Destroy infrastructure
terraform destroy
```

### Helm Deployment

```bash
# Install Helm chart
helm install xvpn helm/

# Upgrade Helm chart
helm upgrade xvpn helm/

# Check release status
helm status xvpn

# Uninstall Helm chart
helm uninstall xvpn
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id

# Server Configuration
SERVER_IP=your_server_ip
API_BASE_URL=https://your_domain:8443

# Database Configuration
DATABASE_URL=sqlite:///data/xvpn.db
REDIS_URL=redis://redis:6379/0

# Security Configuration
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/xvpn/api.log

# Feature Flags
FEATURE_AI_ORCHESTRATOR=true
FEATURE_IPV6_SUPPORT=true
FEATURE_PROXY_MODES=true
FEATURE_HEALTH_MONITORING=true
```

### Docker Compose Configuration

Customize `docker-compose.yml` for your environment:

```yaml
version: '3.8'

services:
  xvpn-api:
    image: ghcr.io/mehan42/xvpn-api:latest
    ports:
      - "8443:8443"
    volumes:
      - ./data:/data
      - ./config:/config:ro
      - ./logs:/var/log/xvpn
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - CHAT_ID=${CHAT_ID}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - LOG_LEVEL=${LOG_LEVEL}
    restart: unless-stopped
```

## 🧪 Testing

### Health Check

```bash
# Check API health
curl -k https://localhost:8443/mcp/v1/vpn.health

# Check transport manifest
curl -k https://localhost:8443/transports/manifest.json

# Check client configuration
curl -k https://localhost:8443/clients/test-uuid-123.json
```

### Automated Tests

```bash
# Run deployment tests
pytest tests/deployment/ -v

# Run integration tests
pytest tests/integration/ -v

# Run end-to-end tests
pytest tests/e2e/ -v
```

## 📊 Monitoring

### Prometheus Metrics

The XVPN system exposes Prometheus metrics at `/metrics` endpoint:

```bash
# Scrape metrics
curl -k https://localhost:8443/metrics
```

### Grafana Dashboards

Import the provided dashboards:

- XVPN Overview Dashboard
- XVPN Transport Performance
- XVPN Health Monitoring
- XVPN Security Metrics

### Health Checks

The system performs periodic health checks:

- API Health (`/mcp/v1/vpn.health`)
- Transport Availability (`/transports/manifest.json`)
- Client Connectivity (`/clients/{uuid}.json`)

## 🛡️ Security

### TLS Configuration

The XVPN system uses TLS for all communications:

- Certificate pinning for API endpoints
- Mutual TLS authentication for inter-service communication
- Automatic certificate renewal with Let's Encrypt

### Firewall Rules

Recommended firewall rules:

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow XVPN API
ufw allow 8443/tcp

# Allow VPN traffic
ufw allow 51820/udp  # WireGuard
ufw allow 1080/tcp   # SOCKS proxy
ufw allow 3128/tcp   # HTTP proxy
```

### Access Control

The system implements role-based access control:

- Admin users (full access)
- Operator users (limited access)
- Client users (VPN access only)

## 🆘 Troubleshooting

### Common Issues

1. **Service won't start**
   - Check logs: `docker-compose logs -f`
   - Verify configuration files
   - Check port availability

2. **Docker containers not starting**
   - Check Docker logs: `docker logs xvpn-api`
   - Verify Docker installation
   - Check resource limits

3. **Network connectivity issues**
   - Check firewall rules: `ufw status`
   - Verify port availability
   - Check DNS resolution

4. **Python dependency issues**
   - Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
   - Check Python version compatibility
   - Verify virtual environment setup

### Logs Location

- API logs: `/var/log/xvpn/api.log`
- Agent logs: `/var/log/xvpn/agent.log`
- Bot logs: `/var/log/xvpn/bot.log`
- Docker logs: `docker-compose logs`

## 🔄 Updates

### Update Process

```bash
# Pull latest changes
git pull origin main

# Update Docker images
docker-compose pull

# Restart services
docker-compose up -d --force-recreate
```

### Rolling Updates

For production environments, use rolling updates:

```bash
# Update one service at a time
docker-compose up -d --no-deps --scale xvpn-api=2 xvpn-api
docker-compose up -d --no-deps xvpn-api
```

## 🗑️ Cleanup

### Remove Services

```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Remove Data

```bash
# Remove data directory
rm -rf /opt/xvpn/data

# Remove logs
rm -rf /opt/xvpn/logs

# Remove configuration
rm -rf /opt/xvpn/config
```

## 📞 Support

For support, please:

1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team via Telegram

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.