# XVPN Deployment Configuration
# Конфигурация автоматического развертывания

# === Ansible Configuration ===
# ansible/inventory/hosts

[vpn_servers]
vpn1.xvpn.local ansible_host=192.168.1.10
vpn2.xvpn.local ansible_host=192.168.1.11
vpn3.xvpn.local ansible_host=192.168.1.12

[vpn_agents]
agent1.xvpn.local ansible_host=192.168.1.20
agent2.xvpn.local ansible_host=192.168.1.21
agent3.xvpn.local ansible_host=192.168.1.22

[vpn_bots]
bot1.xvpn.local ansible_host=192.168.1.30
bot2.xvpn.local ansible_host=192.168.1.31

[vpn_workers]
worker1.xvpn.local ansible_host=192.168.1.40
worker2.xvpn.local ansible_host=192.168.1.41
worker3.xvpn.local ansible_host=192.168.1.42

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/xvpn-deploy-key
ansible_python_interpreter=/usr/bin/python3

# === Ansible Playbook ===
# ansible/playbooks/deploy-xvpn.yml

---
- name: Deploy XVPN System
  hosts: all
  become: yes
  vars:
    xvpn_version: "1.0.0"
    xvpn_install_dir: "/opt/xvpn"
    xvpn_user: "xvpn"
    xvpn_group: "xvpn"
    docker_compose_file: "docker-compose.production.yml"
    
  tasks:
    # === System Preparation ===
    - name: Update system packages
      apt:
        update_cache: yes
        upgrade: dist
      when: ansible_os_family == "Debian"
      
    - name: Install system dependencies
      apt:
        name:
          - curl
          - wget
          - git
          - jq
          - net-tools
          - iproute2
          - ufw
          - fail2ban
        state: present
      when: ansible_os_family == "Debian"
      
    - name: Install Docker
      shell: |
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
      args:
        creates: /usr/bin/docker
        
    - name: Start and enable Docker
      systemd:
        name: docker
        state: started
        enabled: yes
        
    # === User and Group Creation ===
    - name: Create XVPN group
      group:
        name: "{{ xvpn_group }}"
        state: present
        
    - name: Create XVPN user
      user:
        name: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        home: "{{ xvpn_install_dir }}"
        shell: /bin/bash
        state: present
        system: yes
        
    # === Directory Structure ===
    - name: Create XVPN directories
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        mode: '0755'
      loop:
        - "{{ xvpn_install_dir }}"
        - "{{ xvpn_install_dir }}/data"
        - "{{ xvpn_install_dir }}/logs"
        - "{{ xvpn_install_dir }}/config"
        - "{{ xvpn_install_dir }}/certs"
        - "{{ xvpn_install_dir }}/backups"
        
    # === Certificate Management ===
    - name: Copy SSL certificates
      copy:
        src: "certs/{{ inventory_hostname }}/"
        dest: "{{ xvpn_install_dir }}/certs/"
        owner: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        mode: '0644'
      notify: Reload services
      
    # === Application Deployment ===
    - name: Clone XVPN repository
      git:
        repo: "https://github.com/Mehan42/chatVPN.git"
        dest: "{{ xvpn_install_dir }}/src"
        version: "v{{ xvpn_version }}"
        force: yes
        
    - name: Set ownership of source code
      file:
        path: "{{ xvpn_install_dir }}/src"
        owner: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        recurse: yes
        
    # === Docker Compose Deployment ===
    - name: Copy Docker Compose file
      template:
        src: "docker-compose.production.j2"
        dest: "{{ xvpn_install_dir }}/docker-compose.yml"
        owner: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        mode: '0644'
      notify: Restart services
      
    - name: Copy environment file
      template:
        src: "env.production.j2"
        dest: "{{ xvpn_install_dir }}/.env"
        owner: "{{ xvpn_user }}"
        group: "{{ xvpn_group }}"
        mode: '0600'
      notify: Restart services
      
    # === Service Management ===
    - name: Pull Docker images
      docker_compose:
        project_src: "{{ xvpn_install_dir }}"
        pull: yes
        
    - name: Start XVPN services
      docker_compose:
        project_src: "{{ xvpn_install_dir }}"
        state: present
        services:
          - xvpn-api
          - xvpn-agent
          - xvpn-bot
          - xvpn-worker
          - xvpn-core
          - redis
          - postgres
        
    # === Firewall Configuration ===
    - name: Configure UFW firewall
      ufw:
        rule: "{{ item.rule }}"
        port: "{{ item.port }}"
        proto: "{{ item.proto | default('tcp') }}"
        state: enabled
      loop:
        - { rule: "allow", port: "22" }      # SSH
        - { rule: "allow", port: "80" }      # HTTP
        - { rule: "allow", port: "443" }     # HTTPS
        - { rule: "allow", port: "8443" }    # XVPN API
        - { rule: "allow", port: "51820", proto: "udp" }  # WireGuard
        - { rule: "allow", port: "1080" }    # SOCKS Proxy
        - { rule: "allow", port: "3128" }    # HTTP Proxy
        
    # === Monitoring Setup ===
    - name: Install monitoring agents
      apt:
        name:
          - prometheus-node-exporter
          - collectd
        state: present
        
    - name: Start monitoring services
      systemd:
        name: "{{ item }}"
        state: started
        enabled: yes
      loop:
        - prometheus-node-exporter
        - collectd
        
    # === Health Checks ===
    - name: Wait for services to start
      uri:
        url: "https://{{ inventory_hostname }}:8443/mcp/v1/vpn.health"
        method: GET
        validate_certs: no
        timeout: 30
      register: health_check
      until: health_check.status == 200
      retries: 10
      delay: 5
      
    - name: Verify service health
      debug:
        msg: "Service is healthy: {{ health_check.json.status }}"

  handlers:
    - name: Reload services
      systemd:
        daemon_reload: yes
        
    - name: Restart services
      docker_compose:
        project_src: "{{ xvpn_install_dir }}"
        state: present
        restarted: yes

# === Terraform Configuration ===
# terraform/main.tf

# Провайдеры
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0"
}

# DigitalOcean провайдер
provider "digitalocean" {
  token = var.do_token
}

# Cloudflare провайдер
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# === Variables ===
# terraform/variables.tf

variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API Token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "fra1"  # Frankfurt
}

variable "vpn_server_count" {
  description = "Number of VPN servers to create"
  type        = number
  default     = 3
}

variable "agent_count" {
  description = "Number of agent instances to create"
  type        = number
  default     = 3
}

variable "bot_count" {
  description = "Number of bot instances to create"
  type        = number
  default     = 2
}

variable "worker_count" {
  description = "Number of worker instances to create"
  type        = number
  default     = 3
}

variable "domain" {
  description = "Domain name for XVPN"
  type        = string
  default     = "xvpn.local"
}

# === VPN Servers ===
# terraform/vpn-servers.tf

resource "digitalocean_droplet" "vpn_server" {
  count  = var.vpn_server_count
  name   = "xvpn-server-${count.index + 1}"
  region = var.region
  size   = "s-2vcpu-4gb"  # 2 CPUs, 4GB RAM
  image  = "ubuntu-22-04-x64"
  ssh_keys = [digitalocean_ssh_key.deploy.id]
  
  connection {
    host        = self.ipv4_address
    user        = "root"
    type        = "ssh"
    private_key = file(var.private_key_path)
    timeout     = "2m"
  }
  
  provisioner "remote-exec" {
    inline = [
      "export PATH=$PATH:/usr/bin",
      "sudo apt-get update",
      "sudo apt-get install -y python3 python3-pip",
      "pip3 install ansible"
    ]
  }
}

# === Load Balancer ===
# terraform/load-balancer.tf

resource "digitalocean_loadbalancer" "vpn_lb" {
  name   = "xvpn-load-balancer"
  region = var.region

  forwarding_rule {
    entry_port     = 443
    entry_protocol = "https"
    
    target_port     = 8443
    target_protocol = "https"
    
    certificate_name = digitalocean_certificate.vpn.name
  }

  healthcheck {
    port     = 8443
    protocol = "https"
    path     = "/mcp/v1/vpn.health"
    check_interval_seconds = 10
    response_timeout_seconds = 5
    healthy_threshold = 3
    unhealthy_threshold = 3
  }

  droplet_ids = digitalocean_droplet.vpn_server[*].id
}

# === DNS Records ===
# terraform/dns.tf

resource "cloudflare_record" "vpn_api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  value   = digitalocean_loadbalancer.vpn_lb.ip
  type    = "A"
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "vpn_dashboard" {
  zone_id = var.cloudflare_zone_id
  name    = "dashboard"
  value   = digitalocean_loadbalancer.vpn_lb.ip
  type    = "A"
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "vpn_docs" {
  zone_id = var.cloudflare_zone_id
  name    = "docs"
  value   = digitalocean_loadbalancer.vpn_lb.ip
  type    = "A"
  ttl     = 1
  proxied = true
}

# === Kubernetes Configuration ===
# kubernetes/xvpn-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: xvpn-api
  labels:
    app: xvpn-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xvpn-api
  template:
    metadata:
      labels:
        app: xvpn-api
    spec:
      containers:
      - name: xvpn-api
        image: ghcr.io/mehan42/xvpn-api:latest
        ports:
        - containerPort: 8443
        envFrom:
        - configMapRef:
            name: xvpn-config
        - secretRef:
            name: xvpn-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /mcp/v1/vpn.health
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /mcp/v1/vpn.health
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: xvpn-api-service
spec:
  selector:
    app: xvpn-api
  ports:
    - protocol: TCP
      port: 8443
      targetPort: 8443
  type: LoadBalancer

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xvpn-agent
  labels:
    app: xvpn-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xvpn-agent
  template:
    metadata:
      labels:
        app: xvpn-agent
    spec:
      containers:
      - name: xvpn-agent
        image: ghcr.io/mehan42/xvpn-agent:latest
        envFrom:
        - configMapRef:
            name: xvpn-config
        - secretRef:
            name: xvpn-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xvpn-bot
  labels:
    app: xvpn-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: xvpn-bot
  template:
    metadata:
      labels:
        app: xvpn-bot
    spec:
      containers:
      - name: xvpn-bot
        image: ghcr.io/mehan42/xvpn-bot:latest
        envFrom:
        - configMapRef:
            name: xvpn-config
        - secretRef:
            name: xvpn-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xvpn-worker
  labels:
    app: xvpn-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xvpn-worker
  template:
    metadata:
      labels:
        app: xvpn-worker
    spec:
      containers:
      - name: xvpn-worker
        image: ghcr.io/mehan42/xvpn-worker:latest
        envFrom:
        - configMapRef:
            name: xvpn-config
        - secretRef:
            name: xvpn-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"

# === Helm Chart Configuration ===
# helm/xvpn/Chart.yaml

apiVersion: v2
name: xvpn
description: Intelligent VPN with AI Agents
type: application
version: 1.0.0
appVersion: "1.0.0"

# === Helm Values ===
# helm/xvpn/values.yaml

# XVPN application configuration
xvpn:
  # API configuration
  api:
    replicaCount: 3
    image:
      repository: ghcr.io/mehan42/xvpn-api
      tag: "latest"
      pullPolicy: IfNotPresent
    service:
      type: LoadBalancer
      port: 8443
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
      requests:
        cpu: 250m
        memory: 256Mi
  
  # Agent configuration
  agent:
    replicaCount: 3
    image:
      repository: ghcr.io/mehan42/xvpn-agent
      tag: "latest"
      pullPolicy: IfNotPresent
    resources:
      limits:
        cpu: 250m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi
  
  # Bot configuration
  bot:
    replicaCount: 2
    image:
      repository: ghcr.io/mehan42/xvpn-bot
      tag: "latest"
      pullPolicy: IfNotPresent
    resources:
      limits:
        cpu: 250m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi
  
  # Worker configuration
  worker:
    replicaCount: 3
    image:
      repository: ghcr.io/mehan42/xvpn-worker
      tag: "latest"
      pullPolicy: IfNotPresent
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
      requests:
        cpu: 200m
        memory: 256Mi

# === Ingress Configuration ===
# helm/xvpn/templates/ingress.yaml

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: xvpn-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  tls:
  - hosts:
    - api.xvpn.local
    - dashboard.xvpn.local
    - docs.xvpn.local
    secretName: xvpn-tls
  rules:
  - host: api.xvpn.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: xvpn-api-service
            port:
              number: 8443
  - host: dashboard.xvpn.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: xvpn-dashboard-service
            port:
              number: 80
  - host: docs.xvpn.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: xvpn-docs-service
            port:
              number: 80

# === GitHub Actions Deployment ===
# .github/workflows/deploy.yml

name: Deploy XVPN

on:
  # Запуск при пуше в основную ветку
  push:
    branches:
      - main
      - release/**
    paths:
      - "server/**"
      - "src/**"
      - "docker/**"
      - "kubernetes/**"
      - "helm/**"
      - "ansible/**"
      - "terraform/**"
      
  # Запуск по расписанию (ежедневно в 3:00)
  schedule:
    - cron: "0 3 * * *"
    
  # Запуск вручную
  workflow_dispatch:
    inputs:
      environment:
        description: "Environment to deploy to"
        required: true
        default: "staging"
        type: choice
        options:
          - staging
          - production
      version:
        description: "Version to deploy"
        required: false
        default: "latest"

jobs:
  # === Build Docker Images ===
  build-images:
    name: Build Docker Images
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api, agent, bot, worker, orchestrator]
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка QEMU для multi-arch сборки
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
        
      # Установка Docker Buildx
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      # Вход в Docker Registry
      - name: Log in to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
          
      # Вход в GitHub Container Registry
      - name: Log in to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      # Извлечение метаданных Docker
      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            name=ghcr.io/${{ github.repository }}-${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
            
      # Сборка и пуш Docker образа
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.${{ matrix.service }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          
      # Экспорт образа для тестирования
      - name: Export Docker image
        if: github.event_name == 'pull_request'
        run: |
          docker save ghcr.io/${{ github.repository }}-${{ matrix.service }}:${{ github.sha }} > /tmp/${{ matrix.service }}-${{ github.sha }}.tar
          
      # Загрузка образа для тестирования
      - name: Upload Docker image artifact
        if: github.event_name == 'pull_request'
        uses: actions/upload-artifact@v3
        with:
          name: docker-image-${{ matrix.service }}
          path: /tmp/${{ matrix.service }}-${{ github.sha }}.tar
          
  # === Test Deployment ===
  test-deployment:
    name: Test Deployment
    runs-on: ubuntu-latest
    needs: build-images
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Загрузка Docker образов для тестирования
      - name: Download Docker images
        uses: actions/download-artifact@v3
        with:
          path: /tmp/docker-images
          
      # Загрузка образов в Docker
      - name: Load Docker images
        run: |
          for image in /tmp/docker-images/docker-image-*/docker-image-*.tar; do
            if [ -f "$image" ]; then
              docker load -i "$image"
            fi
          done
          
      # Запуск тестов развертывания
      - name: Run Deployment Tests
        run: |
          echo "Running deployment tests..."
          # TODO: Add deployment testing logic
          
      # Уведомление о результатах тестов
      - name: Deployment Test Results Notification
        if: always()
        run: |
          echo "Deployment tests completed"
          # TODO: Add notification logic
          
  # === Staging Deployment ===
  staging-deployment:
    name: Staging Deployment
    runs-on: ubuntu-latest
    needs: test-deployment
    environment:
      name: staging
      url: https://staging.xvpn.local
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Развертывание в staging окружение
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          # TODO: Add actual deployment commands
          
      # Проверка развертывания
      - name: Verify Staging Deployment
        run: |
          echo "Verifying staging deployment..."
          # TODO: Add verification logic
          
      # Уведомление о развертывании в staging
      - name: Staging Deployment Notification
        if: always()
        run: |
          echo "Staging deployment completed"
          # TODO: Add notification logic
          
  # === Production Deployment ===
  production-deployment:
    name: Production Deployment
    runs-on: ubuntu-latest
    needs: staging-deployment
    if: github.ref == 'refs/heads/main' && github.event.inputs.environment == 'production'
    environment:
      name: production
      url: https://xvpn.local
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Развертывание в production окружение
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment..."
          # TODO: Add actual deployment commands
          
      # Проверка развертывания
      - name: Verify Production Deployment
        run: |
          echo "Verifying production deployment..."
          # TODO: Add verification logic
          
      # Уведомление о развертывании в production
      - name: Production Deployment Notification
        if: always()
        run: |
          echo "Production deployment completed"
          # TODO: Add notification logic
          
  # === Rollback Handler ===
  rollback-handler:
    name: Rollback Handler
    runs-on: ubuntu-latest
    needs: [staging-deployment, production-deployment]
    if: failure()
    steps:
      # Откат изменений
      - name: Rollback Changes
        run: |
          echo "Rolling back changes due to deployment failure..."
          # TODO: Add rollback logic
          
      # Уведомление об откате
      - name: Rollback Notification
        if: always()
        run: |
          echo "Rollback completed"
          # TODO: Add notification logic

# === Deployment Scripts ===
# scripts/deploy.sh

#!/bin/bash

# Скрипт для развертывания XVPN системы

set -e  # Выход при любой ошибке

echo "🚀 Deploying XVPN System..."
echo "==========================="

# === Параметры ===
DEPLOY_ENVIRONMENT=${1:-staging}
DEPLOY_VERSION=${2:-latest}
DRY_RUN=${3:-false}

# === Переменные окружения ===
export DEBIAN_FRONTEND=noninteractive
export TZ=UTC

# === Функции вспомогательные ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        error_exit "Git is not installed"
    fi
    
    log "All prerequisites satisfied"
}

# === Функции развертывания ===
prepare_environment() {
    log "Preparing deployment environment: $DEPLOY_ENVIRONMENT"
    
    # Создание директорий
    mkdir -p /opt/xvpn/{data,logs,config,certs,backups}
    
    # Установка прав доступа
    chown -R 1000:1000 /opt/xvpn || true
    
    # Создание пользователя XVPN (если нужно)
    if ! id -u xvpn &>/dev/null; then
        useradd -r -s /bin/false -d /opt/xvpn xvpn || true
        usermod -aG docker xvpn || true
    fi
    
    # Установка прав доступа для пользователя
    chown -R xvpn:xvpn /opt/xvpn || true
}

clone_repository() {
    log "Cloning repository..."
    
    # Клонирование репозитория
    if [ -d "/opt/xvpn/src" ]; then
        log "Repository already exists, pulling latest changes..."
        cd /opt/xvpn/src
        git pull origin main
    else
        log "Cloning fresh repository..."
        git clone https://github.com/Mehan42/chatVPN.git /opt/xvpn/src
    fi
    
    # Проверка версии
    if [ "$DEPLOY_VERSION" != "latest" ]; then
        log "Checking out version: $DEPLOY_VERSION"
        cd /opt/xvpn/src
        git checkout "v$DEPLOY_VERSION" || git checkout "$DEPLOY_VERSION"
    fi
    
    # Установка прав доступа
    chown -R xvpn:xvpn /opt/xvpn/src
}

configure_docker_compose() {
    log "Configuring Docker Compose for $DEPLOY_ENVIRONMENT..."
    
    # Копирование файла конфигурации
    if [ "$DEPLOY_ENVIRONMENT" = "production" ]; then
        cp /opt/xvpn/src/docker-compose.production.yml /opt/xvpn/docker-compose.yml
    else
        cp /opt/xvpn/src/docker-compose.staging.yml /opt/xvpn/docker-compose.yml
    fi
    
    # Установка прав доступа
    chown xvpn:xvpn /opt/xvpn/docker-compose.yml
    
    # Настройка переменных окружения
    if [ ! -f "/opt/xvpn/.env" ]; then
        cp /opt/xvpn/src/.env.$DEPLOY_ENVIRONMENT /opt/xvpn/.env
        chown xvpn:xvpn /opt/xvpn/.env
        chmod 600 /opt/xvpn/.env
    fi
}

pull_images() {
    log "Pulling Docker images..."
    
    # Вход в реестр (если нужно)
    if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    fi
    
    # Загрузка образов
    cd /opt/xvpn
    docker-compose pull
    
    # Проверка загрузки
    if [ $? -ne 0 ]; then
        error_exit "Failed to pull Docker images"
    fi
}

start_services() {
    log "Starting XVPN services..."
    
    # Остановка существующих служб (если есть)
    cd /opt/xvpn
    docker-compose down --remove-orphans || true
    
    # Запуск новых служб
    if [ "$DRY_RUN" = "true" ]; then
        docker-compose up --no-start
    else
        docker-compose up -d
    fi
    
    # Проверка запуска
    if [ $? -ne 0 ]; then
        error_exit "Failed to start services"
    fi
}

verify_deployment() {
    log "Verifying deployment..."
    
    # Ожидание запуска служб
    log "Waiting for services to start..."
    sleep 30
    
    # Проверка состояния служб
    cd /opt/xvpn
    docker-compose ps
    
    # Проверка здоровья API
    log "Checking API health..."
    for i in {1..10}; do
        if curl -k -f https://localhost:8443/mcp/v1/vpn.health > /dev/null 2>&1; then
            log "✅ API is healthy"
            return 0
        fi
        log "⏳ Waiting for API to become healthy ($i/10)"
        sleep 10
    done
    
    error_exit "API failed to become healthy"
}

# === Основной поток выполнения ===
main() {
    log "Starting XVPN deployment to $DEPLOY_ENVIRONMENT environment"
    
    # Проверка предварительных условий
    check_prerequisites
    
    # Подготовка окружения
    prepare_environment
    
    # Клонирование репозитория
    clone_repository
    
    # Настройка Docker Compose
    configure_docker_compose
    
    # Загрузка образов
    pull_images
    
    # Запуск служб
    start_services
    
    # Проверка развертывания
    verify_deployment
    
    # Уведомление об успешном развертывании
    log "✅ XVPN deployment completed successfully!"
    log "Environment: $DEPLOY_ENVIRONMENT"
    log "Version: $DEPLOY_VERSION"
    log "Services started. Check status with: docker-compose ps"
}

# === Обработка сигналов ===
trap 'error_exit "Deployment interrupted"' INT TERM

# === Запуск ===
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <environment> [version] [dry-run]"
    echo "  environment: staging|production"
    echo "  version: version tag (optional, default: latest)"
    echo "  dry-run: true|false (optional, default: false)"
    exit 1
fi

main "$@"
exit 0

# === Конец скрипта ===

# === Health Check Script ===
# scripts/health-check.sh

#!/bin/bash

# Скрипт для проверки здоровья XVPN системы

set -e

echo "🏥 Checking XVPN System Health..."
echo "================================="

# === Переменные ===
API_BASE_URL="https://localhost:8443"
HEALTH_ENDPOINT="/mcp/v1/vpn.health"
MANIFEST_ENDPOINT="/transports/manifest.json"
TIMEOUT=30

# === Функции проверки ===
check_api_health() {
    echo "🔍 Checking API health..."
    
    # Проверка состояния здоровья
    if curl -k --max-time $TIMEOUT -f "$API_BASE_URL$HEALTH_ENDPOINT" > /tmp/health-response.json 2>/dev/null; then
        STATUS=$(jq -r '.status' /tmp/health-response.json)
        MASK_SCORE=$(jq -r '.mask_score' /tmp/health-response.json)
        VERSION=$(jq -r '.version' /tmp/health-response.json)
        
        echo "✅ API is $STATUS (mask score: $MASK_SCORE, version: $VERSION)"
        return 0
    else
        echo "❌ API health check failed"
        return 1
    fi
}

check_transport_manifest() {
    echo "🔍 Checking transport manifest..."
    
    # Проверка манифеста транспортов
    if curl -k --max-time $TIMEOUT -f "$API_BASE_URL$MANIFEST_ENDPOINT" > /tmp/manifest-response.json 2>/dev/null; then
        TRANSPORTS_COUNT=$(jq -r '.transports | length' /tmp/manifest-response.json)
        MANIFEST_VERSION=$(jq -r '.version' /tmp/manifest-response.json)
        
        echo "✅ Transport manifest available ($TRANSPORTS_COUNT transports, version: $MANIFEST_VERSION)"
        return 0
    else
        echo "❌ Transport manifest check failed"
        return 1
    fi
}

check_docker_containers() {
    echo "🔍 Checking Docker containers..."
    
    # Проверка контейнеров
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" > /tmp/containers.txt 2>/dev/null; then
        echo "✅ Docker containers:"
        cat /tmp/containers.txt
        return 0
    else
        echo "❌ Docker container check failed"
        return 1
    fi
}

check_system_resources() {
    echo "🔍 Checking system resources..."
    
    # Проверка использования CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -f1 -d"%")
    
    # Проверка использования памяти
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    # Проверка использования диска
    DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | cut -f1 -d"%")
    
    echo "📊 System Resources:"
    echo "   CPU Usage: ${CPU_USAGE}%"
    echo "   Memory Usage: ${MEMORY_USAGE}%"
    echo "   Disk Usage: ${DISK_USAGE}%"
    
    # Проверка критических уровней
    if [ "$MEMORY_USAGE" -gt 90 ] || [ "$DISK_USAGE" -gt 90 ]; then
        echo "⚠️  High resource usage detected!"
        return 1
    fi
    
    return 0
}

check_network_connectivity() {
    echo "🔍 Checking network connectivity..."
    
    # Проверка внешнего подключения
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo "✅ External network connectivity is OK"
    else
        echo "❌ External network connectivity is DOWN"
        return 1
    fi
    
    # Проверка DNS
    if nslookup google.com > /dev/null 2>&1; then
        echo "✅ DNS resolution is OK"
    else
        echo "❌ DNS resolution is DOWN"
        return 1
    fi
    
    return 0
}

# === Основная проверка здоровья ===
check_health() {
    echo "🏥 Running comprehensive health check..."
    
    # Проверка API
    check_api_health || return 1
    
    # Проверка манифеста транспортов
    check_transport_manifest || return 1
    
    # Проверка контейнеров Docker
    check_docker_containers || return 1
    
    # Проверка системных ресурсов
    check_system_resources || return 1
    
    # Проверка сетевого подключения
    check_network_connectivity || return 1
    
    echo "✅ All health checks passed!"
    return 0
}

# === Уведомление о результатах ===
send_notification() {
    if [ "$1" = "success" ]; then
        echo "🟢 XVPN Health Check: SUCCESS"
        # TODO: Add notification logic (Slack, Telegram, Email)
    else
        echo "🔴 XVPN Health Check: FAILURE"
        # TODO: Add notification logic (Slack, Telegram, Email)
    fi
}

# === Основной поток выполнения ===
main() {
    # Запуск проверки здоровья
    if check_health; then
        send_notification "success"
        exit 0
    else
        send_notification "failure"
        exit 1
    fi
}

# === Запуск ===
main "$@"
exit 0

# === Конец скрипта ===