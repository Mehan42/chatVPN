
# XVPN - Руководство по Docker развертыванию и мониторингу

## 📋 Содержание

- [Docker архитектура](#docker-архитектура)
- [Docker Compose конфигурация](#docker-compose-конфигурация)
- [Управление контейнерами](#управление-контейнерами)
- [Мониторинг с Prometheus и Grafana](#мониторинг-с-prometheus-и-grafana)
- [Логирование и трассировка](#логирование-и-трассировка)
- [Сетевая конфигурация](#сетевая-конфигурация)
- [Безопасность](#безопасность)
- [Масштабирование](#масштабирование)
- [Обновления и обслуживание](#обновления-и-обслуживание)
- [Решение проблем](#решение-проблем)

## 🐳 Docker архитектура

### Схема Docker инфраструктуры

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         XVPN Docker Infrastructure                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Docker Host Layer                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Docker Engine    Docker Compose    Docker Network    Docker Volume   │    │
│  │  (Orchestrator)  (Configuration)   (Networking)     (Storage)       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Load Balancer │        │   Monitoring    │        │   Storage       │  │
│  │   (Traefik)     │        │   (Prometheus)  │        │   (Volumes)     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Container Services Layer                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Application Services                             │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  xvpn-api    xvpn-agent    xvpn-bot    xvpn-worker    xvpn-core      │    │
│  │  (Flask)    (Python)      (Telegram)   (Background)   (Xray)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Cache Layer   │        │   Database      │        │   Monitoring    │  │
│  │   (Redis)       │        │   (PostgreSQL)  │        │   (Grafana)     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           External Services Layer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │   External      │  │   DNS & Load Balance    │  │   Certificate       │  │
│  │   Networks      │  │   (Cloudflare)         │  │   (Let's Encrypt)   │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Составные части Docker инфраструктуры

| Сервис | Описание | Образ | Порт | Volume | Зависимости |
|--------|----------|-------|------|--------|-------------|
| **xvpn-api** | Flask API шлюз | `xvpn/api:latest` | 8443 | `xvpn-config`, `xvpn-data` | redis, postgres |
| **xvpn-agent** | ИИ-агент | `xvpn/agent:latest` | 8443 | `xvpn-data`, `xvpn-knowledge` | xvpn-api |
| **xvpn-bot** | Telegram бот | `xvpn/bot:latest` | 8443 | `xvpn-config` | xvpn-api |
| **xvpn-worker** | Фоновые задачи | `xvpn/worker:latest` | - | `xvpn-data` | redis |
| **xvpn-core** | VPN ядро | `teddysun/xray:latest` | 443 | `xvpn-config`, `xvpn-data` | сеть |
| **redis** | Кэш и очередь | `redis:7-alpine` | 6379 | `xvpn-redis-data` | - |
| **postgres** | База данных | `postgres:15-alpine` | 5432 | `xvpn-postgres-data` | - |
| **traefik** | Reverse proxy | `traefik:v2.10` | 80/443 | `xvpn-traefik-config` | docker.sock |
| **prometheus** | Сбор метрик | `prom/prometheus:latest` | 9090 | `xvpn-prometheus-data` | - |
| **grafana** | Дашборды | `grafana/grafana:latest` | 3000 | `xvpn-grafana-data` | prometheus |

## 📦 Docker Compose конфигурация

### Основной docker-compose.yml

```yaml
# /opt/xvpn/docker-compose.yml
version: '3.8'

services:
  # === Traefik Load Balancer ===
  traefik:
    image: traefik:v2.10
    container_name: xvpn-traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.xvpn.address=:8443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=${SSL_EMAIL:-admin@uss.hopto.org}"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
      - "--providers.file.filename=/etc/traefik/tls.yml"
      - "--providers.file.watch=true"
    ports:
      - "80:80"
      - "443:443"
      - "8443:8443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-letsencrypt:/letsencrypt
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/tls.yml:/etc/traefik/tls.yml:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.uss.hopto.org`)"
      - "traefik.http.routers.traefik.entrypoints=web"
      - "traefik.http.services.traefik.loadbalancer.server.port=8080"

  # === XVPN API Service ===
  xvpn-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
      args:
        - UV_CACHE_DIR=/tmp/uv-cache
        - PYTHON_VERSION=3.11
    container_name: xvpn-api
    command: uvx run --app api.main:app
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=false
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=postgresql://xvpn:${POSTGRES_PASSWORD:-xvpn123}@postgres:5432/xvpn
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - XVPN_CONFIG_FILE=/config/api.json
    volumes:
      - xvpn-data:/data
      - ./config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.uss.hopto.org`) || PathPrefix(`/api`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=myresolver"
      - "traefik.http.services.api.loadbalancer.server.port=8443"
      - "traefik.http.middlewares.api-stripprefix.stripprefix.prefixes=/api"
      - "traefik.http.routers.api.middlewares=api-stripprefix"
      - "traefik.http.routers.api.priority=10"
      - "traefik.http.middlewares.api-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.middlewares.api-headers.headers.sslredirect=true"
      - "traefik.http.routers.api.middlewares=api-stripprefix,api-headers"

  # === XVPN Agent Service ===
  xvpn-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.agent
      args:
        - UV_CACHE_DIR=/tmp/uv-cache
        - PYTHON_VERSION=3.11
    container_name: xvpn-agent
    command: uvx run --app agent.main:agent
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://xvpn:${POSTGRES_PASSWORD:-xvpn123}@postgres:5432/xvpn
      - MANIFEST_URL=http://xvpn-api:8443/transports/manifest.json
      - HEALTH_URL=http://xvpn-api:8443/mcp/v1/vpn.health
      - AGENT_CONFIG_FILE=/config/agent.json
    volumes:
      - xvpn-data:/data
      - ./config:/config:ro
      - uv-cache:/tmp/uv-cache
      - ./server/agent/knowledge:/app/agent/knowledge:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - xvpn-api
      - postgres
      - redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.agent.rule=PathPrefix(`/agent`)"
      - "traefik.http.routers.agent.entrypoints=websecure"
      - "traefik.http.routers.agent.tls.certresolver=myresolver"
      - "traefik.http.services.agent.loadbalancer.server.port=8443"
      - "traefik.http.middlewares.agent-stripprefix.stripprefix.prefixes=/agent"
      - "traefik.http.routers.agent.middlewares=agent-stripprefix"
      - "traefik.http.routers.agent.priority=20"

  # === XVPN Bot Service ===
  xvpn-bot:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        - UV_CACHE_DIR=/tmp/uv-cache
        - PYTHON_VERSION=3.11
    container_name: xvpn-bot
    command: uvx run --app bot.main:bot
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - BOT_TOKEN=${BOT_TOKEN}
      - CHAT_ID=${CHAT_ID}
      - API_BASE_URL=https://api.uss.hopto.org
      - BOT_CONFIG_FILE=/config/bot.json
    volumes:
      - ./config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - xvpn-api
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bot.rule=Host(`bot.uss.hopto.org`)"
      - "traefik.http.routers.bot.entrypoints=websecure"
      - "traefik.http.routers.bot.tls.certresolver=myresolver"
      - "traefik.http.services.bot.loadbalancer.server.port=8443"
      - "traefik.http.routers.bot.priority=30"
      - "traefik.http.middlewares.bot-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.middlewares.bot-headers.headers.sslredirect=true"
      - "traefik.http.routers.bot.middlewares=bot-headers"

  # === XVPN Worker Service ===
  xvpn-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
      args:
        - UV_CACHE_DIR=/tmp/uv-cache
        - PYTHON_VERSION=3.11
    container_name: xvpn-worker
    command: uvx run --app worker.main:worker
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - WORKER_COUNT=2
      - DATABASE_URL=postgresql://xvpn:${POSTGRES_PASSWORD:-xvpn123}@postgres:5432/xvpn
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - xvpn-data:/data
      - ./config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  # === PostgreSQL Database ===
  postgres:
    image: postgres:15-alpine
    container_name: xvpn-postgres
    environment:
      - POSTGRES_DB=xvpn
      - POSTGRES_USER=xvpn
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-xvpn123}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=false"

  # === Redis Cache ===
  redis:
    image: redis:7-alpine
    container_name: xvpn-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
      - ./config/redis.conf:/etc/redis/redis.conf:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=false"

  # === XVPN Core VPN Service ===
  xvpn-core:
    image: teddysun/xray:latest
    container_name: xvpn-core
    command: xray run -c /config/xray.json
    volumes:
      - ./config/xray:/config:ro
      - xvpn-data:/data
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.vpn.rule=Host(`vpn.uss.hopto.org`)"
      - "traefik.http.routers.vpn.entrypoints=websecure"
      - "traefik.http.routers.vpn.tls.certresolver=myresolver"
      - "traefik.http.services.vpn.loadbalancer.server.port=443"
      - "traefik.http.routers.vpn.priority=5"
      - "traefik.http.middlewares.vpn-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.middlewares.vpn-headers.headers.sslredirect=true"
      - "traefik.http.routers.vpn.middlewares=vpn-headers"

  # === Prometheus Monitoring ===
  prometheus:
    image: prom/prometheus:latest
    container_name: xvpn-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=200h'
    volumes:
      - prometheus-data:/prometheus
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/rules:/etc/prometheus/rules:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=false"

  # === Grafana Dashboard ===
  grafana:
    image: grafana/grafana:latest
    container_name: xvpn-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    networks:
      - xvpn-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.uss.hopto.org`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=myresolver"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"
      - "traefik.http.middlewares.grafana-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.middlewares.grafana-headers.headers.sslredirect=true"
      - "traefik.http.routers.grafana.middlewares=grafana-headers"

# === Volumes ===
volumes:
  xvpn-data:
    driver: local
  postgres-data:
    driver: local
  redis-data:
    driver: local
  grafana-data:
    driver: local
  prometheus-data:
    driver: local
  traefik-letsencrypt:
    driver: local
  uv-cache:
    driver: local

# === Networks ===
networks:
  xvpn-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Traefik конфигурация

#### Traefik configuration

```yaml
# /opt/xvpn/traefik/traefik.yml
global:
  sendAnonymousUsage: false
  checkForUpdates: true

api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: myresolver
  xvpn:
    address: ":8443"

providers:
  docker:
    exposedByDefault: false
    network: xvpn-network
    endpoint: "unix:///var/run/docker.sock"
    watch: true
    pull: true
    swarmMode: false

certificatesResolvers:
  myresolver:
    acme:
      email: "${SSL_EMAIL:-admin@uss.hopto.org}"
      storage: "/etc/traefik/acme.json"
      tlsChallenge:
        {} # optional

log:
  level: INFO
  format: json
  filePath: "/var/log/traefik/traefik.log"

accessLog:
  filePath: "/var/log/traefik/access.log"
  format: json
  filters:
    statusCodes:
      - "200-400"
    retryAttempts: true
    minDuration: "10ms"

metrics:
  prometheus:
    buckets:
      - "0.1"
      - "0.3"
      - "1.2"
      - "5.0"
    entryPoint: "traefik"
```

#### TLS configuration

```yaml
# /opt/xvpn/traefik/tls.yml
tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
        - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
        - TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA
        - TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA
        - TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA
        - TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA
        - TLS_RSA_WITH_AES_