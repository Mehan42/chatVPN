
# XVPN - Руководство по администрированию сервера

## 📋 Содержание

- [Архитектура сервера](#архитектура-сервера)
- [Systemd сервисы](#systemd-сервисы)
- [Настройка сети](#настройка-сети)
- [Docker управление](#docker-управление)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Безопасность](#безопасность)
- [Обновления и бекапы](#обновления-и-бекапы)
- [Решение проблем](#решение-проблем)

## 🏗️ Архитектура сервера

### Схема серверной инфраструктуры

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           XVPN Серверная Инфраструктура                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Systemd Services Layer                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  xvpn-api.service    xvpn-agent.service    xvpn-bot.service         │    │
│  │  xvpn-redis.service  xvpn-traefik.service  xvpn-core.service        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Docker Layer  │        │   Configuration │        │   Monitoring    │  │
│  │                 │        │     Files       │        │     Layer       │  │
│  │  docker-compose │        │  /opt/xvpn/     │        │  /opt/xvpn/     │  │
│  │    .yml         │        │   config/       │        │   monitoring/   │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Application Layer                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │     XVPN API    │  │      XVPN Agent        │  │     XVPN Bot        │  │
│  │   (Flask + uvx) │  │   (State Machine)      │  │   (Telegram + uvx)  │  │
│  │     Port: 8443  │  │     Port: 8443        │  │     Port: 8443      │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │     Redis       │        │   PostgreSQL    │        │    Xray Core    │  │
│  │     Port: 6379  │        │   Port: 5432    │        │   Port: 443     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Infrastructure Layer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │     Traefik     │  │    Prometheus          │  │      Grafana        │  │
│  │   Load Balancer │  │    Monitoring          │  │      Dashboard      │  │
│  │    Port: 80/443 │  │    Port: 9090         │  │     Port: 3000      │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Составные части сервера

| Компонент | Описание | Путь | Порт | Зависимости |
|-----------|----------|------|------|-------------|
| **XVPN API** | Центральный API шлюз | `/opt/xvpn/api/` | 8443 | PostgreSQL, Redis |
| **XVPN Agent** | ИИ-агент с state machine | `/opt/xvpn/agent/` | 8443 | XVPN API, База знаний |
| **XVPN Bot** | Telegram бот | `/opt/xvpn/bot/` | 8443 | XVPN API, Telegram API |
| **XVPN Core** | VPN ядро (Xray) | `/opt/xvpn/core/` | 443 | Сетевые интерфейсы |
| **Redis** | Кэш и очередь сообщений | `/opt/xvpn/redis/` | 6379 | XVPN API, XVPN Agent |
| **PostgreSQL** | Основная база данных | `/opt/xvpn/postgres/` | 5432 | XVPN API, XVPN Agent |
| **Traefik** | Reverse proxy | `/opt/xvpn/traefik/` | 80/443 | Все сервисы |
| **Prometheus** | Сбор метрик | `/opt/xvpn/monitoring/` | 9090 | Traefik, Сервисы |
| **Grafana** | Дашборды | `/opt/xvpn/monitoring/` | 3000 | Prometheus |

## 🔧 Systemd сервисы

### Systemd unit файлы

#### XVPN API Service

```ini
# /etc/systemd/system/xvpn-api.service
[Unit]
Description=XVPN Control API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xvpn/api
ExecStart=/usr/bin/uvx run --app api.main:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=FLASK_ENV=production
Environment=DATABASE_URL=sqlite:////opt/xvpn/data/xvpn.db
Environment=REDIS_URL=redis://localhost:6379/0
Environment=LOG_LEVEL=INFO

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=512M
CPUQuota=50%
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
```

#### XVPN Agent Service

```ini
# /etc/systemd/system/xvpn-agent.service
[Unit]
Description=XVPN Agent Service
After=network.target docker.service xvpn-api.service
Requires=docker.service xvpn-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xvpn/agent
ExecStart=/usr/bin/uvx run --app agent.main:agent
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=LOG_LEVEL=INFO
Environment=MANIFEST_URL=http://localhost:8443/transports/manifest.json
Environment=HEALTH_URL=http://localhost:8443/mcp/v1/vpn.health

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=256M
CPUQuota=30%

[Install]
WantedBy=multi-user.target
```

#### XVPN Bot Service

```ini
# /etc/systemd/system/xvpn-bot.service
[Unit]
Description=XVPN Telegram Bot Service
After=network.target docker.service xvpn-api.service
Requires=docker.service xvpn-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xvpn/bot
ExecStart=/usr/bin/uvx run --app bot.main:bot
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=LOG_LEVEL=INFO
Environment=BOT_TOKEN=your_bot_token
Environment=CHAT_ID=your_chat_id

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=128M
CPUQuota=20%

[Install]
WantedBy=multi-user.target
```

#### XVPN Redis Service

```ini
# /etc/systemd/system/xvpn-redis.service
[Unit]
Description=XVPN Redis Cache
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xvpn/redis
ExecStart=/usr/bin/docker run --rm -v xvpn-redis-data:/data -p 6379:6379 redis:7-alpine redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

#### XVPN Traefik Service

```ini
# /etc/systemd/system/xvpn-traefik.service
[Unit]
Description=XVPN Traefik Load Balancer
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xvpn/traefik
ExecStart=/usr/bin/docker run --rm -v /var/run/docker.sock:/var/run/docker.sock:ro -v xvpn-traefik-config:/etc/traefik -p 80:80 -p 443:443 -p 8080:8080 traefik:v2.10
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=256M
CPUQuota=40%

[Install]
WantedBy=multi-user.target
```

### Управление сервисами

#### Основные команды

```bash
# Проверка статуса всех сервисов
sudo systemctl status xvpn-*

# Запуск всех сервисов
sudo systemctl start xvpn-*

# Остановка всех сервисов
sudo systemctl stop xvpn-*

# Перезапуск всех сервисов
sudo systemctl restart xvpn-*

# Включение автозапуска
sudo systemctl enable xvpn-*

# Отключение автозапуска
sudo systemctl disable xvpn-*

# Перезагрузка конфигурации
sudo systemctl daemon-reload
```

#### Управление отдельными сервисами

```bash
# Управление API сервисом
sudo systemctl start xvpn-api.service
sudo systemctl stop xvpn-api.service
sudo systemctl restart xvpn-api.service
sudo systemctl status xvpn-api.service

# Управление агентом
sudo systemctl start xvpn-agent.service
sudo systemctl stop xvpn-agent.service
sudo systemctl restart xvpn-agent.service
sudo systemctl status xvpn-agent.service

# Управление ботом
sudo systemctl start xvpn-bot.service
sudo systemctl stop xvpn-bot.service
sudo systemctl restart xvpn-bot.service
sudo systemctl status xvpn-bot.service
```

#### Просмотр логов

```bash
# Просмотр логов всех сервисов
sudo journalctl -u xvpn-* -f

# Просмотр логов конкретного сервиса
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f

# Просмотр логов с временным фильтром
sudo journalctl -u xvpn-api --since "2024-01-01" --until "2024-01-02"

# Просмотр последних N логов
sudo journalctl -u xvpn-api -n 100

# Экспорт логов в файл
sudo journalctl -u xvpn-* > xvpn-logs-$(date +%Y%m%d).log
```

#### Анализ ошибок

```bash
# Поиск ошибок в логах
sudo journalctl -u xvpn-* | grep -i error

# Поиск сбоев в логах
sudo journalctl -u xvpn-* | grep -i fail

# Поиск предупреждений
sudo journalctl -u xvpn-* | grep -i warning

# Анализ производительности
sudo journalctl -u xvpn-api | grep -i "slow\|timeout\|performance"
```

## 🌐 Настройка сети

### Базовая сетевая конфигурация

#### Файл `/etc/network/interfaces` (Debian/Ubuntu)

```bash
# Основная сетевая конфигурация
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4
```

#### Файл `/etc/sysconfig/network-scripts/ifcfg-eth0` (CentOS/RHEL)

```bash
TYPE=Ethernet
BOOTPROTO=static
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=8.8.4.4
ONBOOT=yes
```

### Настройка IP forwarding

```bash
# Включение IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.conf

# Применение изменений
sudo sysctl -p

# Проверка
sysctl net.ipv4.ip_forward
sysctl net.ipv6.conf.all.forwarding
```

### Настройка NAT и iptables

```bash
# Очистка существующих правил
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -X

# Политика по умолчанию
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

# Разрешение локального трафика
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# Разрешение установленных соединений
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Разрешение портов XVPN
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT

# Разрешение SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Запись правил для сохранения
sudo iptables-save > /etc/iptables/rules.v4
sudo ip6tables-save > /etc/iptables/rules.v6

# Автоматическая загрузка при старте
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

### Настройка UFW (Uncomplicated Firewall)

```bash
# Установка UFW
sudo apt install -y ufw

# Политика по умолчанию
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение портов
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8443/tcp  # XVPN API
sudo ufw allow 8081/tcp  # Monitoring

# Включение брандмауэра
sudo ufw enable

# Проверка статуса
sudo ufw status

# Логирование
sudo ufw logging on
```

### Настройка DNS и времени

#### Конфигурация DNS

```bash
# Установка DNS серверов
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf

# Или через systemd-resolved
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

#### Синхронизация времени

```bash
# Установка NTP
sudo apt install -y ntp

# Или через systemd-timesyncd
sudo systemctl enable systemd-timesyncd
sudo systemctl start systemd-timesyncd

# Проверка времени
timedatectl status
ntpq -p
```

## 🐳 Docker управление

### Docker Compose конфигурация

#### Файл `docker-compose.yml`

```yaml
version: '3.8'

services:
  xvpn-api:
    build:
      context: /opt/xvpn
      dockerfile: docker/Dockerfile.api
    container_name: xvpn-api
    command: uvx run --app api.main:app
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:////opt/xvpn/data/xvpn.db
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - xvpn-data:/opt/xvpn/data
      - xvpn-config:/opt/xvpn/config
    ports:
      - "8443:8443"
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - redis

  xvpn-agent:
    build:
      context: /opt/xvpn
      dockerfile: docker/Dockerfile.agent
    container_name: xvpn-agent
    command: uvx run --app agent.main:agent
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - MANIFEST_URL=http://xvpn-api:8443/transports/manifest.json
      - HEALTH_URL=http://xvpn-api:8443/mcp/v1/vpn.health
    volumes:
      - xvpn-data:/opt/xvpn/data
      - xvpn-config:/opt/xvpn/config
      - xvpn-knowledge:/opt/xvpn/agent/knowledge
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - xvpn-api
      - redis

  xvpn-bot:
    build:
      context: /opt/xvpn
      dockerfile: docker/Dockerfile.bot
    container_name: xvpn-bot
    command: uvx run --app bot.main:bot
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - BOT_TOKEN=${BOT_TOKEN}
      - CHAT_ID=${CHAT_ID}
      - API_BASE_URL=http://xvpn-api:8443
    volumes:
      - xvpn-config:/opt/xvpn/config
    networks:
      - xvpn-network
    restart: unless-stopped
    depends_on:
      - xvpn-api

  redis:
    image: redis:7-alpine
    container_name: xvpn-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - xvpn-redis-data:/data
    networks:
      - xvpn-network
    restart: unless-stopped

  traefik:
    image: traefik:v2.10
    container_name: xvpn-traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.xvpn.address=:8443"
    ports:
      - "80:80"
      - "443:443"
      - "8443:8443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - xvpn-traefik-config:/etc/traefik
    networks:
      - xvpn-network
    restart: unless-stopped

volumes:
  xvpn-data:
    driver: local
  xvpn-config:
    driver: local
  xvpn-redis-data:
    driver: local
  xvpn-knowledge:
    driver: local
  xvpn-traefik-config:
    driver: local

networks:
  xvpn-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Управление Docker контейнерами

#### Базовые команды

```bash
# Запуск всех сервисов
sudo docker-compose up -d

# Остановка всех сервисов
sudo docker-compose down

# Перезапуск всех сервисов
sudo docker-compose restart

# Перезапуск конкретного сервиса
sudo docker-compose restart xvpn-api

# Просмотр статуса
sudo docker-compose ps

# Просмотр логов
sudo docker-compose logs -f

# Просмотр логов конкретного сервиса
sudo docker-compose logs -f xvpn-api
```

#### Обновление сервисов

```bash
# Обновление образов
sudo docker-compose pull

# Обновление и перезапуск
sudo docker-compose up -d --force-recreate

# Обновление без перезапуска
sudo docker-compose pull
sudo docker-compose up -d

# Обновление с очисткой
sudo docker-compose pull
sudo docker-compose up -d --force-recreate --remove-orphans
```

#### Управление volumes

```bash
# Просмотр volumes
sudo docker volume ls
sudo docker volume inspect xvpn-data

# Бэкап volume
sudo docker run --rm -v xvpn-data:/data -v $(pwd):/backup alpine tar czf /backup/xvpn-data-backup.tar.gz -C /data .

# Восстановление volume
sudo docker run --rm -v xvpn-data:/data -v $(pwd):/backup alpine tar xzf /backup/xvpn-data-backup.tar.gz -C /data

# Очистка неиспользуемых volumes
sudo docker volume prune
```

#### Мониторинг ресурсов

```bash
# Просмотр использования ресурсов
sudo docker stats

# Просмотр статистики контейнера
sudo docker stats xvpn-api

# Просмотр использования диска
sudo docker system df

# Очистка неиспользуемых ресурсов
sudo docker system prune -f
sudo docker image prune -f
sudo docker container prune -f
sudo docker volume prune -f
```

## 📊 Мониторинг и логирование

### Prometheus конфигурация

#### Файл `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'xvpn-api'
    static_configs:
      - targets: ['localhost:8443']
    metrics_path: '/metrics'

  - job_name: 'xvpn-agent'
    static_configs:
      - targets: ['localhost:8443']
    metrics_path: '/metrics'

  - job_name: 'traefik'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

### Grafana дашборды

#### Основные дашборды

1. **System Overview**
   - CPU Usage
   - Memory Usage
   - Disk Usage
   - Network Traffic

2. **XVPN Services**
   - API Response Time
   - Agent Health Status
   - Connection Count
   - Error Rate

3. **Network Metrics**
   - Bandwidth Usage
   - Connection Latency
   - Packet Loss
   - Connection Errors

#### Пример дашборда конфигурации

```json
{
  "dashboard": {
    "title": "XVPN System Overview",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "Memory Usage"
          }
        ]
      },
      {
        "title": "XVPN API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Логирование конфигурация

#### Filebeat конфигурация

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/xvpn/*.log
  fields:
    service: xvpn
    environment: production
  fields_under_root: true

output.logstash:
  hosts: ["logstash:5044"]

setup.template.enabled: true
setup.template.name: "xvpn"
setup.template.pattern: "xvpn-*"
setup.template.settings:
  index.number_of_shards: 1
```

### Health checks

#### API Health Check

```bash
#!/bin/bash
# /opt/xvpn/scripts/health_check.sh

API_URL="https://localhost:8443/mcp/v1/vpn.health"
API_USER="admin"
API_PASS="password"

# Проверка доступности API
response=$(curl -k -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $response -eq 200 ]; then
    echo "API is healthy"
    exit 0
else
    echo "API is unhealthy (HTTP $response)"
    exit 1
fi
```

#### Системный Health Check

```bash
#!/bin/bash
# /opt/xvpn/scripts/system_health_check.sh

# Проверка CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "WARNING: CPU usage is ${CPU_USAGE}%"
fi

# Проверка памяти
MEMORY_USAGE=$(free | grep Mem | awk '{print ($3/$2)*100}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "WARNING: Memory usage is ${MEMORY_USAGE}%"
fi

# Проверка диска
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# Проверка сервисов
SERVICES=("xvpn-api" "xvpn-agent" "xvpn-bot")
for service in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet $service; then
        echo "ERROR: Service $service is not running"
    fi
done

# Проверка Docker контейнеров
if ! docker-compose ps | grep -q "Up"; then
    echo "ERROR: Docker containers are not running"
fi

echo "Health check completed"
```

## 🔒 Безопасность

### Systemd hardening

#### Усиление безопасности сервисов

```bash
# Создание отдельного пользователя для XVPN
sudo useradd -r -s /bin/false -d /opt/xvpn xvpn
sudo chown -R xvpn:xvpn /opt/xvpn

# Обновление unit файлов с hardening
for service in xvpn-api xvpn-agent xvpn-bot; do
    sudo sed -i 's/NoNewPrivileges=false/NoNewPrivileges=true/' /etc/systemd/system/$service.service
    sudo sed -i 's/PrivateTmp=false/PrivateTmp=true/' /etc/systemd/system/$service.service
    sudo sed -i 's/ProtectSystem=false/ProtectSystem=strict/' /etc/systemd/system/$service.service
    sudo sed -i 's/ProtectHome=false/ProtectHome=true/' /etc/systemd/system/$service.service
done

# Перезагрузка systemd
sudo systemctl daemon-reload
```

### SSL/TLS конфигурация

#### Генерация SSL сертификатов

```bash
# Создание директории для SSL
sudo mkdir -p /opt/xvpn/ssl
cd /opt/xvpn/ssl

# Генерация приватного ключа
openssl genpkey -algorithm RSA -out key.pem -pkeyopt rsa_keygen_bits:4096

# Создание CSR
openssl req -new -key key.pem -out csr.pem -subj "/C=RU/ST=State/L=City/O=XVPN/OU=IT/CN=$(hostname)"

# Подпись сертификата (самоподписанный)
openssl x509 -req -days 365 -in csr.pem -signkey key.pem -out cert.pem

# Установка прав
sudo chmod 600 key.pem cert.pem
```

#### Настройка Let's Encrypt

```bash
# Установка Certbot
sudo apt install -y certbot

# Получение сертификата
sudo certbot certonly --standalone -d api.yourdomain.com -d bot.yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Конфигурация брандмауэра

#### iptables advanced rules

```bash
#!/bin/bash
# /opt/xvpn/scripts/firewall_setup.sh

# Очистка правил
iptables -F
iptables -t nat -F
iptables -X

# Политика по умолчанию
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Разрешение локального трафика
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Разрешение установленных соединений
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Разрешение SSH
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT

# Разрешение XVPN портов
iptables -A INPUT -p tcp --dport 80 -m state --state NEW -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m state --state NEW -j ACCEPT
iptables -A INPUT -p tcp --dport 8443 -m state --state NEW -j ACCEPT
iptables -A INPUT -p tcp --dport 8081 -m state --state NEW -j ACCEPT

# Разрешение исходящих соединений
iptables -A OUTPUT -p tcp --dport 80 -m state --state NEW -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -m state --state NEW -j ACCEPT

# Запись правил
iptables-save > /etc/iptables/rules.v4

echo "Firewall configured successfully"
```

### Аудит безопасности

#### Скрипт аудита

```bash
#!/bin/bash
# /opt/xvpn/scripts/security_audit.sh

echo "Starting security audit..."

# Проверка обновлений системы
echo "Checking system updates..."
sudo apt update -qq
sudo apt list --upgradable

# Проверка открытых портов
echo "Checking open ports..."
sudo netstat -tulpn
sudo ss -tulpn

# Проверка пользователей
echo "Checking users..."
cut -d: -f1 /etc/passwd
sudo last

# Проверка прав доступа
echo "Checking file permissions..."
sudo find /opt/xvpn -type f -exec ls -la {} \;

# Проверка логов
echo "Checking recent security logs..."
sudo journalctl -u ssh --since "1 hour ago" | grep -i "failed\|error"
sudo journalctl -u xvpn-* --since "1 hour ago" | grep -i "error\|failed"

# Проверка SSL сертификатов
echo "Checking SSL certificates..."
if [ -f "/opt/xvpn/ssl/cert.pem" ]; then
    openssl x509 -in /opt/xvpn/ssl/cert.pem -text -noout
fi

echo "Security audit completed"
```

## 🔄 Обновления и бекапы

### Система обновлений

#### Автоматическое обновление

```bash
#!/bin/bash
# /opt/xvpn/scripts/auto_update.sh

LOG_FILE="/var/log/xvpn/update.log"
BACKUP_DIR="/opt/xvpn/backups"

# Создание бекапа
echo "$(date): Creating backup..." >> $LOG_FILE
sudo tar -czf $BACKUP_DIR/backup-$(date +%Y%m%d-%H%M).tar.gz \
    /opt/xvpn/config/ \
    /opt/xvpn/data/ \
    /etc/systemd/system/xvpn-*.service

# Обновление системы
echo "$(date): Updating system..." >> $LOG_FILE
sudo apt update && sudo apt upgrade -y

# Обновление XVPN
echo "$(date): Updating XVPN..." >> $LOG_FILE
cd /opt/xvpn
sudo git pull origin main

# Обновление зависимостей
echo "$(date): Updating dependencies..." >> $LOG_FILE
sudo uv pip install --upgrade -r requirements.txt

# Обновление Docker образов
echo "$(date): Updating Docker images..." >> $LOG_FILE
sudo docker-compose pull

# Перезапуск сервисов
echo "$(date): Restarting services..." >> $LOG_FILE
sudo systemctl restart xvpn-*

# Проверка статуса
echo "$(date): Checking service status..." >> $LOG_FILE
sudo systemctl status xvpn-* >> $LOG_FILE

# Очистка старых бекапов
echo "$(date): Cleaning old backups..." >> $LOG_FILE
find $BACKUP_DIR -name "backup-*.tar.gz" -mtime +7 -delete

echo "$(date): Update completed successfully" >> $LOG_FILE
```

### Расписание обновлений

```bash
# Добавление в crontab
sudo crontab -e

# Ежедневное обновление в 3:00 ночи
0 3 * * * /opt/xvpn/scripts/auto_update.sh

# Еженедельный полный бекап
0 4 * * 0 /opt/xvpn/scripts/full_backup.sh

# Ежемесячный аудит безопасности
0 5 1 * * /opt/xvpn/scripts/security_audit.sh
```

### Полный бекап

```bash
#!/bin/bash
# /opt/xvpn/scripts/full_backup.sh

BACKUP_DIR="/opt/xvpn/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/full-backup-$TIMESTAMP.tar.gz"

echo "Starting full backup..."

# Создание бекапа
sudo tar -czf $BACKUP_FILE \
    --exclude=$BACKUP_DIR \
    --exclude=/opt/xvpn/logs \
    --exclude=/opt/xvpn/temp \
    /opt/xvpn/ \
    /etc/systemd/system/xvpn-*.service \
    /etc/iptables/rules.v4 \
    /etc/crontab

# Проверка целостности бекапа
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_FILE"
    echo "Backup size: $(du -h $BACKUP_FILE)"
else
    echo "ERROR: Backup failed"
    exit 1
fi

# Очистка старых бекапов
find $BACKUP_DIR -name "full-backup-*.tar.gz" -mtime +30 -delete

echo "Full backup completed"
```

### Восстановление из бекапа

```bash
#!/bin/bash
# /opt/xvpn/scripts/restore_backup.sh

BACKUP_FILE=$1
BACKUP_DIR="/opt/xvpn/backups"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting restore from backup: $BACKUP_FILE"

# Остановка сервисов
echo "Stopping services..."
sudo systemctl stop xvpn-*

# Распаковка бекапа
echo "Extracting backup..."
sudo tar -xzf $BACKUP_FILE -C /

# Восстановление прав доступа
echo "Restoring permissions..."
sudo chown -R xvpn:xvpn /opt/xvpn
sudo chmod +x /opt/xvpn/scripts/*.sh

# Перезагрузка systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Запуск сервисов
echo "Starting services..."
sudo systemctl start xvpn-*

# Проверка статуса
echo "Checking service status..."
sudo systemctl status xvpn-*

echo "Restore completed successfully"
```

## 🛠️ Решение проблем

### Диагностический скрипт

```bash
#!/bin/bash
# /opt/xvpn/scripts/diagnose_system.sh

echo "XVPN System Diagnostics"
echo "========================"

# Информация о системе
echo "System Information:"
echo "OS: $(lsb_release -a 2>/dev/null || echo 'Unknown')"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime -p)"
echo ""

# Проверка сервисов
echo "Service Status:"
SERVICES=("xvpn-api" "xvpn-agent" "xvpn-bot" "xvpn-redis" "xvpn-traefik")
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: STOPPED"
    fi
done
echo ""

# Проверка Docker
echo "Docker Status:"
if systemctl is-active --quiet docker; then
    echo "✓ Docker: RUNNING"
    echo "  Containers:"
    docker-compose ps 2>/dev/null || echo "    No containers found"
else
    echo "✗ Docker: STOPPED"
fi
echo ""

# Проверка портов
echo "Port Status:"
PORTS=("80" "443" "8443" "8081")
for port in "${PORTS[@]}"; do
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✓ Port $port: OPEN"
    else
        echo "✗ Port $port: CLOSED"
    fi
done
echo ""

# Проверка ресурсов
echo "Resource Usage:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%"
echo "Memory: $(free | grep Mem | awk '{print ($3/$2)*100}')%"
echo "Disk: $(df / | tail -1 | awk '{print $5}' | sed 's/%//')%"
echo ""

# Проверка логов на ошибки
echo "Recent Errors:"
if journalctl -u xvpn-* --since "1 hour ago" | grep -qi "error\|failed"; then
    journalctl -u xvpn-* --since "1 hour ago" | grep -i "error\|failed" | tail -5
else
    echo "No recent errors found"
fi

echo "Diagnostics completed"
```

### Автоматическое восстановление

```bash
#!/bin/bash
# /opt/xvpn/scripts/auto_recovery.sh

LOG_FILE="/var/log/xvpn/recovery.log"
SERVICES=("xvpn-api" "xvpn-agent" "xvpn-bot")

echo "$(date): Starting auto-recovery..." >> $LOG_FILE

# Проверка и перезапacht неработающих сервисов
for service in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet $service; then
        echo "$(date): Service $service is not running, attempting to restart..." >> $LOG_FILE
        systemctl start $service
        
        if systemctl is-active --quiet $service; then
            echo "$(date): Service $service restarted successfully" >> $LOG_FILE
        else
            echo "$(date): ERROR: Failed to restart service $service" >> $LOG_FILE
        fi
    fi
done

# Проверка Docker контейнеров
if ! docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo "$(date): Docker containers are not running, attempting to restart..." >> $LOG_FILE
    docker-compose restart
    
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo "$(date): Docker containers restarted successfully" >> $LOG_FILE
    else
        echo "$(date): ERROR: Failed to restart Docker containers" >> $LOG_FILE
    fi
fi

# Проверка доступности API
if ! curl -k -s -f https://localhost:8443/mcp/v1/vpn.health > /dev/null; then
    echo "$(date): API is not responding, attempting to restart..." >> $LOG_FILE
    systemctl restart xvpn-api
    
    if curl -k -s -f https://localhost:8443/mcp/v1/vpn.health > /dev/null; then
        echo "$(date): API restarted successfully" >> $LOG_FILE
    else
        echo "$(date): ERROR: API still not responding after restart" >> $LOG_FILE
    fi
fi

echo "$(date): Auto-recovery completed" >> $LOG_FILE
```

---

**XVPN v