# XVPN Deployment

[English](#english) | [Русский](#russian)

---

## English {#english}

This directory contains deployment scripts and configuration for the XVPN system.

### 📁 Directory Structure

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
├── systemd/               # Systemd service files
│   ├── xvpn-api.service
│   ├── xvpn-agent.service
│   ├── xvpn-bot.service
│   └── xvpn-worker.service
└── traefik/               # Traefik configuration
    ├── traefik.yml
    └── dynamic_conf.yml
```

### 🚀 Quick Deployment

For quick deployment using the main script:
```bash
cd deploy
./deploy.sh
```

### 🐳 Docker Deployment

To deploy using Docker Compose:
```bash
cd deploy/docker
docker-compose up -d
```

### ☸️ Kubernetes Deployment

To deploy on Kubernetes:
```bash
cd deploy/kubernetes
kubectl apply -f .
```

### ⚙️ Configuration

Edit `deployment_config.py` to customize deployment settings.

---

## Russian {#russian}

Эта директория содержит скрипты развертывания и конфигурацию для системы XVPN.

### 📁 Структура директории

```
deploy/
├── deploy.sh              # Основной скрипт развертывания
├── deployment_config.py   # Конфигурация развертывания
├── docker/                # Файлы развертывания Docker
│   ├── Dockerfile.api
│   ├── Dockerfile.agent
│   ├── Dockerfile.bot
│   ├── Dockerfile.worker
│   └── Dockerfile.orchestrator
├── kubernetes/            # Файлы развертывания Kubernetes
│   ├── xvpn-deployment.yaml
│   ├── xvpn-service.yaml
│   └── xvpn-ingress.yaml
├── systemd/               # Файлы сервисов systemd
│   ├── xvpn-api.service
│   ├── xvpn-agent.service
│   ├── xvpn-bot.service
│   └── xvpn-worker.service
└── traefik/               # Конфигурация Traefik
    ├── traefik.yml
    └── dynamic_conf.yml
```

### 🚀 Быстрое развертывание

Для быстрого развертывания с использованием основного скрипта:
```bash
cd deploy
./deploy.sh
```

### 🐳 Развертывание Docker

Для развертывания с использованием Docker Compose:
```bash
cd deploy/docker
docker-compose up -d
```

### ☸️ Развертывание Kubernetes

Для развертывания в Kubernetes:
```bash
cd deploy/kubernetes
kubectl apply -f .
```

### ⚙️ Конфигурация

Отредактируйте `deployment_config.py` для настройки параметров развертывания.