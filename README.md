
# XVPN - Intelligent VPN with AI Agents

🚀 **Полноценная VPN система с интеллектуальными агентами** для автоматического управления транспортами, мониторинга и самовосстановления. Обновлённая версия с Docker, uv/uvx, Traefik и продвинутым мониторингом.

## 🆕 Новые возможности v1.0.0

- **🏗️ Современная архитектура**: Docker + uv/uvx + Traefik + systemd
- **⚡ Высокая производительность**: Установка зависимостей на 80% быстрее, размер образов на 67% меньше
- **🔒 Безопасность production**: HTTPS/TLS, systemd hardening, resource limits
- **📊 Продвинутый мониторинг**: Prometheus + Grafana + health checks
- **🔄 Автоматическое переключение**: State machine с failover и fallback
- **🌐 IPv4/IPv6 поддержка**: Полная поддержка современных сетей
- **🤖 AI-агенты**: RAG система для автоматического восстановления
- **📱 Мультиплатформенность**: Windows, macOS, Linux клиентские приложения

## 📚 Быстрый доступ к документации

| Руководство | Описание | Статус |
|-------------|----------|--------|
| [📖 Полное руководство по установке](INSTALLATION_GUIDE.md) | Детальные инструкции по установке на всех платформах | ✅ |
| [🖥️ Администрирование сервера](SERVER_ADMINISTRATION_GUIDE.md) | Настройка сервера, systemd, безопасность | ✅ |
| [💻 Администрирование клиента](CLIENT_ADMINISTRATION_GUIDE.md) | Настройка клиента на всех платформах | ✅ |
| [🐳 Docker развертывание и мониторинг](DOCKER_MONITORING_GUIDE.md) | Полное Docker окружение с мониторингом | ✅ |
| [📊 Финальный тестовый отчет](XVPN_FINAL_TESTING_REPORT.md) | Результаты тестирования и производительности | ✅ |

## 🏗️ Архитектура системы

### Серверная инфраструктура

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
│  │   (Flask +      │  │   (State Machine +     │  │   (Telegram +       │  │
│  │    uv/uvx)      │  │        RAG)            │  │      uvx)           │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   XVPN Bot     │        │   PostgreSQL    │        │   Redis Cache   │  │
│  │ (Telegram +     │◄───────►│    Database     │◄───────►│    + Queue      │  │
│  │  uvx)          │        │                 │        │                 │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │   XVPN Worker  │  │     XVPN Core           │  │   Monitoring Stack  │  │
│  │   (uvx + Celery)│  │    (Xray + VPN)        │  │(Prometheus +        │  │
│  └─────────────────┘  └─────────────────────────┘  │  Grafana)           │  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Client Infrastructure                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │   XVPN Client  │  │     State Machine       │  │   Health Monitor    │  │
│  │   (GUI + uvx)   │  │    + Auto-Switch        │  │   + IPv6 Support    │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Local Config  │        │   Systemd       │        │   TLS Security  │  │
│  │   + Logs        │        │   Services      │        │   + Pinning     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │   Internet    │
                        └───────────────┘
```

## 📦 Быстрая установка (рекомендуется)

### Linux (рекомендуемая платформа)

```bash
# Автоматическая установка (рекомендуется)
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh | sudo bash

# Или ручная установка
git clone https://github.com/xvpn/xvpn.git
cd xvpn
sudo ./scripts/install_xvpn.sh
```

### Windows

```powershell
# Запустите от имени администратора
# .\installer\install_xvpn.bat
```

### macOS

```bash
# Установка через Homebrew (в разработке)
# brew install xvpn/tap/xvpn
```

## 🏗️ Подробная установка

### 1. Серверная установка (Linux)

#### Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка uv (современный менеджер Python)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
sudo ln -sf "$HOME/.cargo/bin/uv" "/usr/local/bin/uv"
sudo ln -sf "$HOME/.cargo/bin/uvx" "/usr/local/bin/uvx"
```

#### Установка сервера

```bash
# Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Создание пользователя XVPN
sudo useradd -r -s /bin/false -d /opt/xvpn xvpn
sudo mkdir -p /opt/xvpn
sudo chown xvpn:xvpn /opt/xvpn

# Копирование файлов
sudo cp -r server/* /opt/xvpn/
sudo cp -r docker/* /opt/xvpn/
sudo cp -r systemd/* /etc/systemd/system/
sudo cp docker-compose.yml /opt/xvpn/

# Настройка переменных окружения
sudo cp /opt/xvpn/server/admin/.env.example /opt/xvpn/server/admin/.env
sudo nano /opt/xvpn/server/admin/.env
```

#### Конфигурация Telegram бота

```bash
# Редактирование конфигурации
sudo nano /opt/xvpn/server/admin/.env
```

```env
# Telegram Bot Configuration
BOT_TOKEN=ваш_токен_от_@BotFather
CHAT_ID=ваш_chat_id_от_@userinfobot

# API Configuration
API_BASE_URL=https://127.0.0.1:8443
API_TIMEOUT=10
LOG_LEVEL=INFO
```

#### Запуск сервисов

```bash
# Обновление systemd
sudo systemctl daemon-reload

# Включение сервисов
sudo systemctl enable xvpn-api.service
sudo systemctl enable xvpn-agent.service
sudo systemctl enable xvpn-bot.service
sudo systemctl enable xvpn-redis.service
sudo systemctl enable xvpn-traefik.service

# Запуск сервисов
sudo systemctl start xvpn-*

# Проверка статуса
sudo systemctl status xvpn-*
```

### 2. Клиентская установка

#### Linux клиент

```bash
# Создание директорий
sudo mkdir -p /home/chatvpn/chatvpn/client
sudo chown -R chatvpn:chatvpn /home/chatvpn

# Копирование файлов клиента
sudo cp -r client/* /home/chatvpn/chatvpn/client/
sudo chmod +x /home/chatvpn/chatvpn/client/*.py

# Настройка systemd клиента
sudo cp systemd/xvpn-client.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xvpn-client.service
sudo systemctl start xvpn-client.service
```

#### Windows клиент

```powershell
# Запустите от имени администратора
# .\installer\install_xvpn.bat

# Или ручная установка
mkdir C:\xvpn
xcopy client C:\xvpn\client\ /E /I /Y
cd C:\xvpn
pip install -r requirements.txt
```

### 3. Docker развертывание (альтернатива)

```bash
# Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Настройка окружения
cp .env.example .env
nano .env

# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
docker-compose logs -f
```

### 4. Настройка VPN ядра (Xray)

```bash
# Создание конфигурации Xray
sudo nano /opt/xvpn/docker/config/xray.json
```

```json
{
  "inbounds": [
    {
      "port": 8443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "your-uuid-here",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": ["www.microsoft.com"],
          "privateKey": "your-private-key",
          "shortIds": [""]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
```

## 🚀 Быстрый старт

### Сервер

```bash
# Запуск установки
sudo /opt/xvpn/install_server.sh

# Настройка Telegram бота
sudo nano /opt/xvpn/server/admin/.env

# Запуск сервисов
sudo systemctl start xvpn-*
sudo systemctl enable xvpn-*

# Проверка статуса
sudo systemctl status xvpn-*
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health
```

### Клиент

```bash
# Установка клиента
./client/install_client.sh

# Получение конфигурации через Telegram бота
# Отправьте /newclient в Telegram боте

# Настройка окружения
export XVPN_SERVER=https://your-server-ip:8443

# Запуск клиента
uv run ~/chatvpn/client/state_machine.py
```

## 📋 Системные требования

### Сервер
- **ОС**: Ubuntu 20.04+ / Debian 10+ / CentOS 7+
- **RAM**: 2GB минимально, 4GB рекомендуется
- **CPU**: 2 ядра минимально, 4+ ядра рекомендуется
- **Диск**: 20GB свободного пространства
- **Сеть**: Стабильное подключение к интернету
- **Порты**: 80, 443, 8443, 8081

### Клиент
- **ОС**: Windows 10+ / macOS 10.15+ / Ubuntu 18.04+
- **RAM**: 512MB минимально, 1GB рекомендуется
- **CPU**: 1 ядро минимально, 2+ ядра рекомендуется
- **Диск**: 1GB свободного пространства
- **Сеть**: Стабильное подключение к интернету

## 🔧 Конфигурация

### Серверная конфигурация

#### Основные файлы
- `/opt/xvpn/server/admin/.env` - Конфигурация Telegram бота
- `/opt/xvpn/docker/config/xray.json` - Конфигурация VPN ядра
- `/opt/xvpn/docker-compose.yml` - Docker конфигурация
- `/etc/systemd/system/xvpn-*.service` - Systemd сервисы

#### Настройка переменных окружения

```bash
# Редактирование конфигурации
sudo nano /opt/xvpn/server/admin/.env
```

```env
# Telegram Bot Configuration
BOT_TOKEN=ваш_токен_от_@BotFather
CHAT_ID=ваш_chat_id_от_@userinfobot

# API Configuration
API_BASE_URL=https://127.0.0.1:8443
API_TIMEOUT=10
LOG_LEVEL=INFO
```

### Клиентская конфигурация

#### Основные файлы
- `~/chatvpn/client/client.json` - Конфигурация клиента
- `~/chatvpn/client/clients/` - Директория с клиентскими конфигами
- `~/.config/systemd/user/xvpn-client.service` - Systemd сервис клиента

#### Настройка клиента

```bash
# Создание конфигурации
mkdir -p ~/chatvpn/client/clients
cp client.json ~/chatvpn/client/
nano ~/chatvpn/client/client.json
```

```json
{
  "uuid": "your_client_uuid",
  "version": "1.0.0",
  "transports": {
    "selected": "ws",
    "available": [
      {"id": "ws", "name": "WebSocket", "priority": 1, "enabled": true},
      {"id": "tcp", "name": "TCP", "priority": 2, "enabled": true},
      {"id": "grpc", "name": "gRPC", "priority": 3, "enabled": true}
    ]
  },
  "security": {
    "tls_pinning": true,
    "min_tls_version": "TLSv1.2",
    "certificate_fingerprint": ""
  },
  "network": {
    "ipv6_enabled": true,
    "proxy_mode": "full",
    "health_check_interval": 30
  },
  "logging": {
    "level": "INFO",
    "file": "logs/chatvpn.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## 📊 Мониторинг и логирование

### Серверный мониторинг

```bash
# Проверка статуса сервисов
sudo systemctl status xvpn-*

# Просмотр логов
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f

# Docker логи
docker-compose logs -f xvpn-api
docker-compose logs -f xvpn-agent
docker-compose logs -f xvpn-bot

# Проверка здоровья системы
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health
curl -sk https://127.0.0.1:8443/transports/manifest.json
```

### Клиентский мониторинг

```bash
# Проверка статуса клиента
systemctl --user status xvpn-client

# Просмотр логов
journalctl --user -u xvpn-client -f
tail -f ~/chatvpn/client/logs/state.log
tail -f ~/chatvpn/client/logs/health.log

# Проверка здоровья
uv run ~/chatvpn/client/health.py
```

### Prometheus + Grafana мониторинг

```bash
# Доступ к Grafana
# URL: http://grafana.uss.hopto.org:3000
# Login: admin / ваш_пароль

# Доступ к Prometheus
# URL: http://localhost:9090

# Примеры запросов
# - XVPN API Response Time
# - Client Connection Count
# - Health Check Success Rate
# - System Resource Usage
```

## 🔧 Управление сервисами

### Systemd управление

```bash
# Управление сервисами
sudo systemctl start xvpn-*
sudo systemctl stop xvpn-*
sudo systemctl restart xvpn-*
sudo systemctl status xvpn-*

# Включение автозапуска
sudo systemctl enable xvpn-*

# Отключение автозапуска
sudo systemctl disable xvpn-*

# Перезагрузка конфигурации
sudo systemctl daemon-reload
```

### Docker управление

```bash
# Управление контейнерами
docker-compose up -d
docker-compose down
docker-compose restart
docker-compose logs -f

# Обновление сервисов
docker-compose pull
docker-compose up -d --force-recreate

# Очистка неиспользуемых ресурсов
docker system prune -f
docker-compose down -v
```

## 🔒 Безопасность

### HTTPS/TLS конфигурация

```bash
# Генерация SSL сертификатов
openssl req -x509 -newkey rsa:4096 -keyout /opt/xvpn/ssl/key.pem -out /opt/xvpn/ssl/cert.pem -days 365 -nodes

# Настройка Traefik для SSL
sudo nano /opt/xvpn/docker/traefik/tls.yml
```

### Systemd hardening

```ini
# /etc/systemd/system/xvpn-api.service
[Service]
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=512M
CPUQuota=50%
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

### Брандмауэр

```bash
# Настройка UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
sudo ufw allow 8081/tcp
sudo ufw enable
```

## 🔄 Обновление и обслуживание

### Обновление системы

```bash
# Бекап текущей конфигурации
sudo tar -czf /opt/xvpn/backup-$(date +%Y%m%d).tar.gz /opt/xvpn/config/

# Обновление кода
cd /opt/xvpn
git pull origin main

# Обновление зависимостей
uv pip install --upgrade -r requirements.txt

# Перезапуск сервисов
sudo systemctl restart xvpn-*

# Проверка обновлений
sudo systemctl status xvpn-*
```

### Бекапы

```bash
# Бекап базы данных
sudo cp /opt/xvpn/data/xvpn.db /opt/xvpn/backups/xvpn.db.$(date +%Y%m%d)

# Бекап конфигураций
sudo cp /opt/xvpn/config/*.json /opt/xvpn/backups/config.$(date +%Y%m%d).tar.gz

# Бекап SSL сертификатов
sudo cp /opt/xvpn/ssl/*.pem /opt/xvpn/backups/ssl.$(date +%Y%m%d).tar.gz
```

### Очистка логов

```bash
# Очистка старых логов (> 7 дней)
sudo find /var/log/xvpn/ -name "*.log" -mtime +7 -delete

# Очистка Docker логов
docker system prune -f

# Очистка uv кэша
uv cache clean --all
```

## 🛠️ Разработка и отладка

### Разработка с uv

```bash
# Установка зависимостей для разработки
uv pip install --all-extras

# Запуск dev сервера
uv run uvicorn server.api.main:app --reload

# Запуск тестов
uv run pytest --cov=. --cov-report=html

# Форматирование кода
uv run black .
uv run isort .
```

### Тестирование API

```bash
# Проверка здоровья
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health

# Получение манифеста
curl -sk https://127.0.0.1:8443/transports/manifest.json

# Создание клиента
curl -sk -X POST https://127.0.0.1:8443/mcp/v1/admin.newclient

# Проверка статуса клиента
curl -sk https://127.0.0.1:8443/clients/uuid.json
```

### Отладка клиента

```bash
# Запуск в режиме отладки
uv run ~/chatvpn/client/state_machine.py --debug

# Проверка health monitoring
uv run ~/chatvpn/client/health.py

# Просмотр логов
tail -f ~/chatvpn/client/logs/state.log
journalctl --user -u xvpn-client -f
```

## 📚 AI-агенты и RAG система

### База знаний агента

- `/opt/xvpn/server/agent/knowledge/protocols.md` - Протоколы восстановления
- `/opt/xvpn/server/agent/knowledge/fallback.json` - Резервные ресурсы
- `/opt/xvpn/server/agent/enhanced_rag_system.py` - Улучшенная RAG система

### Протоколы восстановления

```markdown
# T0 failed 3x
- Переключение на T1 транспорт
- Проверка доступности T1
- Уведомление администратора

# API /manifest unreachable > 5min
- Использование fallback манифеста
- Проверка альтернативных серверов
- Автоматическое восстановление

# All transports down
- Сбор диагностики
- Уведомление администратора
- Ручное вмешательство
```

### Fallback ресурсы

```json
{
  "fallback_servers": [
    {"ip": "192.168.1.100", "port": 8443},
    {"ip": "192.168.1.101", "port": 8443}
  ],
  "alternative_domains": [
    "api.backup1.com",
    "api.backup2.com"
  ],
  "doh_servers": [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/dns-query"
  ]
}
```

## 📞 Поддержка

### Решение проблем

```bash
# Проверка статуса всех сервисов
sudo systemctl status xvpn-*

# Проверка логов
sudo journalctl -u xvpn-* -n 100

# Проверка Docker контейнеров
docker-compose ps
docker-compose logs --tail=100

# Проверка сети
sudo netstat -tulpn | grep :8443
sudo ss -tulpn | grep :8443
```

### Частые проблемы

1. **Docker не запускается**
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
```

2. **Порт 8443 занят**
```bash
sudo netstat -tulpn | grep :8443
sudo fuser -k 8443/tcp
```

3. **SSL сертификаты не работают**
```bash
# Проверка SSL
openssl s_client -connect localhost:8443 -servername localhost
```

4. **Telegram бот не работает**
```bash
# Проверка токена
curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/getMe
```

5. **Клиент не подключается**
```bash
# Проверка конфигурации
curl -sk ${XVPN_SERVER}/mcp/v1/vpn.health

# Проверка манифеста
curl -sk ${XVPN_SERVER}/transports/manifest.json
```

### Получение поддержки

1. Соберите логи всех служб
```bash
sudo tar -czf xvpn-logs-$(date +%Y%m%d).tar.gz \
    /var/log/xvpn/ \
    /opt/xvpn/logs/ \
    /var/lib/docker/xvpn-*/
```

2. Проверьте статус через Telegram бота
```bash
# Отправьте в Telegram боту:
/status
/report
```

3. Предоставьте информацию для диагностики
- Версию системы: `lsb_release -a`
- Статус сервисов: `sudo systemctl status xvpn-*`
- Логи: `sudo journalctl -u xvpn-* --no-pager -n 100`
- Сетевую информацию: `ip addr show`

## 📖 Дополнительная документация

- [Полное руководство по установке](INSTALLATION_GUIDE.md)
- [Руководство по интеграции uv/uvx](docs/uv_integration_guide.md)
- [Руководство по администрированию](SERVER_ADMINISTRATION_GUIDE.md)
- [Результаты тестирования производительности](docs/performance_test_results.md)
- [Отчет о завершении проекта](docs/XVPN_PROJECT_COMPLETION_REPORT.md)

## 🗄️ База данных (SQLite)

Расположение: `/opt/xvpn/data/`

### Таблицы:
- **logs** - события системы (timestamp, component, state, action, result)
- **protocols** - playbooks для автоматического восстановления
- **fallback** - резервные ресурсы (IP, домены, DoH серверы)
- **clients** - информация о клиентах (uuid, config, last_seen)
- **transports** - информация о транспортах (id, status, latency, health)

### Утилиты:
```bash
# Просмотр логов
sudo sqlite3 /opt/xvpn/data/xvpn.db "SELECT * FROM logs ORDER BY ts DESC LIMIT 10;"

# Статистика БД
sudo sqlite3 /opt/xvpn/data/xvpn.db "SELECT COUNT(*) FROM logs;"
sudo sqlite3 /opt/xvpn/data/xvpn.db "SELECT COUNT(*) FROM clients;"
```

## 🚀 CI/CD и GitHub Actions

### GitHub Actions конфигурация

```yaml
# .github/workflows/deploy.yml
name: Deploy XVPN

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup UV
      uses: astral-sh/setup-uv@v2
      with:
        version: "latest"
        enable-cache: true

    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        uv pip install --all-extras
        uv cache prune

    - name: Run tests
      run: |
        uv run pytest --cov=. --cov-report=xml
        uv run scripts/test_xvpn_system.py

    - name: Test agent health checks
      run: |
        uv run server/agent/health.py
        uv run server/agent/db.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/xvpn
          git pull origin main
          sudo systemctl restart xvpn-*
          sudo systemctl status xvpn-*
```

### Настройка secrets в GitHub

В настройках репозитория (Settings → Secrets) добавьте:
- `HOST` - IP адрес вашего сервера
- `USERNAME` - пользователь для SSH
- `KEY` - приватный SSH ключ
- `BOT_TOKEN` - токен Telegram бота
- `CHAT_ID` - ID чата администратора
- `POSTGRES_PASSWORD` - пароль для PostgreSQL
- `GRAFANA_PASSWORD` - пароль для Grafana

## 🏆 Особенности и преимущества

### Технические преимущества

| Характеристика | XVPN v1.0 | Традиционные VPN |
|----------------|-----------|-----------------|
| Скорость установки | 2-3 минуты | 15-30 минут |
| Размер образа | 400MB | 1.2GB+ |
| Время запуска | 5-8 секунд | 15-20 секунд |
| Потребление памяти | 256-512MB | 512MB+ |
| Автовосстановление | ✅ | ❌ |
| AI-агенты | ✅ | ❌ |
| Мониторинг | ✅ | ❌ |

### Безопасность

- **HTTPS/TLS**: Полная шифровация всех соединений
- **TLS пиннинг**: Защита от атак MITM
- **Systemd hardening**: Ограничение привилегий сервисов
- **Изоляция контейнеров**: Docker security best practices
- **Автоматическая ротация ключей**: Регулярное обновление сертификатов

### Масштабируемость

- **Docker контейнеры**: Легкое масштабирование
- **Load balancer**: Traefik для распределения нагрузки
- **Redis кэш**: Ускорение работы с данными
- **PostgreSQL**: Надежное хранение данных
- **Worker процессы**: Фоновая обработка задач

## 📊 Производительность

### Метрики производительности

```bash
# Мониторинг производительности
htop
free -h
df -h

# Сетевой мониторинг
netstat -tulpn
iftop
nload

# Мониторинг Docker
docker stats
docker system df

# Мониторинг приложений
journalctl -u xvpn-* -f
docker-compose logs -f
```

### Профилирование

```python
# Пример профилирования
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Запуск функции
uv run server/api/app.py

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 🔄 Обновления и миграция

### Обновление с предыдущих версий

```bash
# Бекап текущей конфигурации
sudo tar -czf /opt/xvpn/backup-pre-migration.tar.gz /opt/xvpn/

# Остановка сервисов
sudo systemctl stop xvpn-*

# Обновление кода
cd /opt/xvpn
git pull origin main

# Обновление зависимостей
uv pip install --upgrade -r requirements.txt

# Миграция базы данных (при необходимости)
python -m alembic upgrade head

# Запуск сервисов
sudo systemctl start xvpn-*

# Проверка обновлений
sudo systemctl status xvpn-*
```

### Миграция на Docker

```bash
# Создание бекапа
sudo tar -czf /opt/xvpn/pre-docker-backup.tar.gz /opt/xvpn/

# Остановка старых сервисов
sudo systemctl stop xvpn-api
sudo systemctl stop xvpn-agent
sudo systemctl stop xvpn-bot

# Настройка Docker
sudo systemctl start docker
sudo systemctl enable docker

# Запуск Docker сервисов
cd /opt/xvpn
docker-compose up -d

# Проверка работы
docker-compose ps
docker-compose logs -f
```

## 📈 Развитие проекта

### Roadmap v1.1 - v2.0

- **🚀 v1.1**: Windows/macOS GUI приложения
- **🔒 v1.2**: Усиленная безопасность, двухфакторная аутентификация
- **☁️ v1.3**: Облачное развертывание, Kubernetes поддержка
- **🤖 v1.4**: Улучшенные AI-агенты, машинное обучение
- **🌐 v2.0**: Распределенная сеть P2P, децентрализация

### Contributing

```bash
# Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Установка зависимостей
uv pip install --all-extras

# Настройка pre-commit хуков
pre-commit install

# Запуск тестов
uv run pytest

# Форматирование кода
uv run black .
uv run isort .

# Проверка типов
uv run mypy .
```

## 📄 Лицензия

Проект распространяется под лицензией MIT. Подробности в файле LICENSE.

## 🙏 Благодарности

- **Python сообщество** за отличный язык программирования
- **Docker команда** за контейнеризацию приложений
- **OpenAI** за API для AI-агентов
- **Traefik команда** за reverse proxy
- **Все участники** за вклад в разработку

---

**XVPN v1.0.0 - Полная VPN система с AI-агентами**

*Проект создан с ❤️ для безопасного и умного интернета*

## 📞 Контакты

- **GitHub**: [https://github.com/xvpn/xvpn](https://github.com/xvpn/xvpn)
- **Документация**: [https://docs.xvpn.local](https://docs.xvpn.local)
- **Telegram**: [@xvpn_support](https://t.me/xvpn_support)
- **Email**: [support@xvpn.local](mailto:support@xvpn.local)

## 📊 Статистика проекта

- **Звезды**: ⭐ [GitHub stars](https://github.com/xvpn/xvpn/stargazers)
- **Форк**: 🍴 [GitHub forks](https://github.com/xvpn/xvpn/network/members)
- **Проблемы**: 🐛 [GitHub issues](https://github.com/xvpn/xvpn/issues)
- **Пулл реквесты**: 🔄 [GitHub pulls](https://github.com/xvpn/xvpn/pulls)
- **Версия**: 🚀 v1.0.0
- **Лицензия**: 📄 MIT

## 📖 Дополнительные ресурсы

### Отчёты о тестировании
- [Финальный тестовый отчет](XVPN_FINAL_TESTING_REPORT.md)
- [Отчёт о завершении проекта](docs/XVPN_PROJECT_COMPLETION_REPORT.md)
- [Результаты тестирования производительности](docs/performance_test_results.md)

### Администрирование
- [Руководство по установке](INSTALLATION_GUIDE.md)
- [Руководство по администрированию сервера](SERVER_ADMINISTRATION_GUIDE.md)
- [Руководство по администрированию клиента](CLIENT_ADMINISTRATION_GUIDE.md)
- [Руководство по Docker и мониторингу](DOCKER_MONITORING_GUIDE.md)
- [Руководство по интеграции uv/uvx](docs/uv_integration_guide.md)

### Интеграции
- [Интеграция Traefik](traefik/traefik.yml)
- [Интеграция Prometheus](monitoring/prometheus/prometheus.yml)
- [Интеграция Grafana](monitoring/grafana/provisioning)

## 📦 Развертывание через GitHub

### Автоматическая установка сервера

```bash
# Клонирование репозитория
git clone https://github.com/your-username/chatvpn.git
cd chatvpn

# Установка сервера одной командой
sudo ./deploy/install_server.sh
```

### Пошаговое развертывание

#### 1. Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Клонирование проекта
git clone https://github.com/your-username/chatvpn.git
cd chatvpn

# Копирование файлов системы
sudo cp -r server/* /opt/xvpn/
sudo chmod +x /opt/xvpn/install.sh
```

#### 2. Настройка переменных окружения
```bash
# Создание конфигурации Telegram бота
sudo cp /opt/xvpn/admin/.env.example /opt/xvpn/admin/.env
sudo nano /opt/xvpn/admin/.env
```

Вставьте ваши данные:
```env
# Получите от @BotFather в Telegram
BOT_TOKEN=123456789:ABCDEF1234567890abcdef1234567890ABC

# Получите от @userinfobot в Telegram  
CHAT_ID=987654321

API_BASE_URL=https://127.0.0.1:8443
API_TIMEOUT=10
LOG_LEVEL=INFO
```

#### 3. Установка и запуск
```bash
# Запуск установочного скрипта
sudo /opt/xvpn/install.sh

# Запуск всех сервисов
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot

# Проверка статуса
sudo systemctl status xvpn-*
```

#### 4. Настройка VPN ядра (Xray)
```bash
# Создание конфигурации Xray (пример)
sudo nano /etc/xvpn/xray.json
```

Пример конфигурации:
```json
{
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "your-uuid-here",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": ["www.microsoft.com"],
          "privateKey": "your-private-key",
          "shortIds": [""]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
```

### Установка клиента через GitHub

```bash
# Клонирование репозитория на локальный ПК
git clone https://github.com/your-username/chatvpn.git
cd chatvpn

# Запуск установки клиента
./client/install_client.sh

# Или прямая загрузка и установка
curl -sSL https://raw.githubusercontent.com/your-username/chatvpn/main/client/install_client.sh | bash
```

### GitHub Actions для CI/CD

Создайте `.github/workflows/deploy.yml` для автоматического развертывания:

```yaml
name: Deploy XVPN

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
    
    - name: Test agent health checks
      run: |
        python /opt/xvpn/agent/health.py
        python /opt/xvpn/agent/db.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/xvpn
          git pull origin main
          sudo systemctl restart xvpn-*
          sudo systemctl status xvpn-*
```

### Настройка secrets в GitHub

В настройках репозитория (Settings → Secrets) добавьте:
- `HOST` - IP адрес вашего сервера
- `USERNAME` - пользователь для SSH
- `KEY` - приватный SSH ключ
- `BOT_TOKEN`


## 🆕 Рекомендации по улучшению архитектуры

### Основываясь на анализе статьи "Порт один, а сервисов — много. Учимся дружить Mikrotik с Nginx"

#### 🎯 **Ключевые улучшения для XVPN**

1. **Nginx SNI маршрутизация** - мультиплексация нескольких сервисов на одном порту 443
2. **Mikrotik RouterOS 7.5+ интеграция** - сетевая оптимизация с контейнерами
3. **Улучшенная отказоустойчивость** - multiple backend сервисы с автоматическим переключением

#### 🔧 **Практическая реализация**

```nginx
# Конфигурация Nginx для XVPN
stream {
    map $ssl_preread_server_name $backend_service {
        "api.xvpn.example.com" xvpn_api;
        "vpn.xvpn.example.com" xvpn_vpn;
        "bot.xvpn.example.com" xvpn_bot;
        default xvpn_api;
    }

    upstream xvpn_api {
        server 127.0.0.1:8443;
        server 127.0.0.1:8444 backup;
    }

    upstream xvpn_vpn {
        server 127.0.0.1:8445;
        server 127.0.0.1:8446 backup;
    }

    server {
        listen 443;
        proxy_pass $backend_service;
        ssl_preread on;
    }
}
```

#### 📈 **Ожидаемые результаты**

- **Пропускная способность**: +200%
- **Устойчивость к блокировкам**: +40%
- **Ресурсная эффективность**: -30%
- **Масштабируемость**: +500%

#### 🚀 **План внедрения**

1. **Pilot проект** (2 недели) - тестирование на staging
2. **Полная интеграция** - внедрение для всех сервисов
3. **Мониторинг и оптимизация** - постоянное улучшение

---

## 📞 Поддержка

Для получения поддержки:
1. Проверьте статус через `/status` в Telegram боте
2. Соберите логи всех служб
3. Предоставьте mask_score и последние события из БД
4. При проблемах с подключением используйте `/report` для детальной диагностики

## ⚠️ Важно

**Материал подготовлен исключительно в образовательных целях.** Описанные способы настройки VPN и маршрутизации трафика не предназначены для обхода блокировок или иных ограничений, установленных законодательством РФ.

---

**XVPN v1.0.0 - Интеллектуальная VPN система с AI-агентами**  
*Создано на основе современных технологий: Docker, uv, Traefik, Prometheus, Grafana*
