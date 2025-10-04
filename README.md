
# XVPN - Интеллектуальная VPN с AI-агентами и современными технологиями

Полноценная VPN система с искусственным интеллектом для автоматического управления транспортами, мониторинга, самовосстановления и продвинутой безопасности. Проект использует современные технологии: Docker, uv, Traefik, systemd, IPv6, proxy modes и enhanced RAG.

---

## 🚀 Быстрый старт

### Автоматическая установка (рекомендуется)

```bash
# Linux сервер
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/installer/install_xvpn.sh | sudo bash

# Linux клиент
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/client/install_client.sh | bash

# Windows
.\installer\install_xvpn.bat
```

### Docker развертывание

```bash
# Клонирование и запуск
git clone https://github.com/xvpn/xvpn.git
cd xvpn
cp .env.example .env
nano .env  # Настройте переменные
docker-compose up -d
```

---

## 🏗️ Современная архитектура

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           XVPN INTELLIGENT SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Telegram Bot  │  │   Traefik Proxy  │  │   XVPN API      │  │   Agent    │ │
│  │   (Management)  │◄─┤   (Load Balancer)│◄─┤   (Flask+uv)    │◄─┤   (RAG)    │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                    │                    │                    │         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Client GUI    │  │   XVPN Core      │  │   PostgreSQL    │  │   Redis     │ │
│  │   (Tkinter)     │  │   (Xray/WireGuard)│  │   (Optional)    │  │   (Cache)   │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                  │
                         ┌────────▼────────┐
                         │   Systemd      │
                         │   Services     │
                         └─────────────────┘
```

### Ключевые технологии

- **🐳 Docker Compose** - Контейнеризация всех сервисов
- **🚀 uv/uvx** - Менеджер пакетов Python (в 10-50x быстрее pip)
- **🔄 Traefik** - Reverse proxy с автоматической SSL
- **⚡ Systemd** - Автоматический запуск и мониторинг
- **🌐 IPv6** - Полная поддержка dual-stack
- **🔒 Enhanced Security** - TLS pinning, rate limiting, IP blacklisting
- **🧠 Enhanced RAG с AI-оркестратором** - Интеллектуальная база знаний для автоматического управления
- **📊 Monitoring** - Prometheus, Grafana, health checks

---

## 🧠 Enhanced RAG с AI-оркестратором

### Критическая важность ChromaDB для XVPN

**ChromaDB является обязательным компонентом** для работы RAG системы и AI-оркестратора в XVPN. Проект спроектирован с использованием векторных баз данных как основного механизма работы.

#### Обязательные зависимости для RAG системы:
```bash
# Основные зависимости для работы AI-оркестратора
pip install chromadb sentence-transformers

# Или через uv (рекомендуется)
uv add chromadb sentence-transformers
```

#### Как устроена RAG система в XVPN:

#### 1. **Основной режим (с ChromaDB)**
- **ChromaDB** - основное векторное хранилище для семантического поиска
- **Sentence-transformers** - генерация эмбеддингов для контекстуального поиска
- **SQLite** - хранение метаданных и истории запросов
- **Обязателен** для работы AI-оркестратора и протоколов восстановления

#### 2. **Fallback режим (ограниченный)**
- Только если ChromaDB недоступна во время работы
- **Не поддерживает** семантический поиск
- Работает только по ключевым словам через SQLite
- **AI-оркестратор не функционирует** в полном объеме

### AI-оркестратор - работа с ChromaDB

База знаний на базе ChromaDB является "мозгом" AI-оркестратора:

#### Протоколы для ИИ (хранятся в ChromaDB):
```json
{
  "T0_failed_3x": "Автоматически переключиться на T1 транспорт",
  "API_manifest_unreachable": "Использовать fallback ресурсы",
  "All_transports_down": "Собрать диагностику и уведомить админа",
  "Mask_score_degradation": "Реагировать на ухудшение маскировки",
  "Connection_loss": "Переключиться на резервный протокол"
}
```

#### Как работает AI-оркестратор:
1. **Векторный поиск** в ChromaDB для релевантных протоколов
2. **Контекстуальное понимание** на эмбеддингах sentence-transformers
3. **Приоритизация** решений на основе метаданных и истории
4. **Автоматическое выполнение** найденных протоколов

#### Обязательные компоненты:
- **ChromaDB** - векторное хранилище для семантического поиска
- **Sentence-transformers** - контекстуальное понимание запросов
- **SQLite** - метаданные и история запросов

### Управление базой знаний

#### Структура знаний:
```
/opt/xvpn/agent/knowledge/
├── protocols.md          # Протоколы восстановления
├── fallback.json        # Резервные ресурсы
├── rag_metadata_*.db     # База данных метаданных
└── chroma_*/            # Векторная база (если ChromaDB)
```

#### Мониторинг RAG системы:
```bash
# Проверка статуса ChromaDB
python3 /opt/xvpn/agent/enhanced_rag_system.py --stats

# Тестирование векторного поиска
python3 /opt/xvpn/agent/enhanced_rag_system.py --test-query "как восстановить транспорт"

# Проверка доступности ChromaDB
curl -s http://localhost:8000/api/v1/health || echo "ChromaDB недоступен"

# Просмотр истории запросов
sqlite3 /opt/xvpn/agent/knowledge/rag_metadata_*.db "SELECT * FROM query_contexts ORDER BY timestamp DESC LIMIT 10;"

# Очистка старых данных
python3 /opt/xvpn/agent/enhanced_rag_system.py --cleanup
```

#### Если ChromaDB не установлена:
```bash
# Ошибка при запуске AI-оркестратора
python3 /opt/xvpn/agent/agent.py
# Output: "ChromaDB not available. AI-orchestrator disabled"

# Система будет работать без:
# - Семантического поиска
# - Контекстуального понимания
# - Автоматического восстановления
# - AI-управления рисками

#### Интеграция с AI-оркестратором:
База знаний автоматически обновляется на основе:
- **Логов системы** - анализ ошибок и сбоев
- **Health checks** - мониторинг состояния транспорта
- **User feedback** - отзывы и улучшения
- **Security events** - инциденты безопасности

---

## 📦 Развертывание на разных платформах

### 1. Серверная установка (Linux Ubuntu/Debian)

#### Автоматическая установка

```bash
# 1. Установка обязательных зависимостей (включая ChromaDB для AI-оркестратора)
sudo apt update && sudo apt install -y python3-pip python3-venv
pip3 install chromadb sentence-transformers

# 2. Загрузка и запуск установщика
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/installer/install_xvpn.sh | sudo bash

# 3. Настройка окружения
sudo cp /opt/xvpn/admin/.env.example /opt/xvpn/admin/.env
sudo nano /opt/xvpn/admin/.env

# 3. Запуск сервисов
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot xvpn-core
sudo systemctl start xvpn-*
```

#### Переменные окружения (`.env`)

```env
# Telegram Bot
BOT_TOKEN=123456789:ABCDEF1234567890abcdef1234567890ABC
CHAT_ID=987654321

# API Configuration
API_BASE_URL=https://api.yourdomain.com:8443
API_TIMEOUT=10
LOG_LEVEL=INFO

# Database (опционально)
DATABASE_URL=postgresql://user:password@localhost/xvpn
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost
```

#### Ручная установка

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv curl wget git docker.io docker-compose

# 2. Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# 3. Клонирование проекта
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# 4. Установка зависимостей
uv sync --all-extras

# 5. Настройка сервисов
sudo cp systemd/* /etc/systemd/system/
sudo systemctl daemon-reload

# 6. Запуск
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot
```

### 2. Клиентская установка (Linux)

#### Автоматическая установка

```bash
# Загрузка установщика клиента
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/client/install_client.sh | bash

# Настройка клиента
cd ~/chatvpn
export XVPN_SERVER=https://api.yourdomain.com:8443
cp client/client.json.example client/client.json
nano client/client.json
```

#### Ручная установка

```bash
# 1. Клонирование проекта
git clone https://github.com/xvpn/xvpn.git
cd chatvpn

# 2. Установка зависимостей
uv sync

# 3. Настройка systemd
cp systemd/xvpn-client.service ~/.config/systemd/user/
systemctl --user daemon-reload

# 4. Запуск
systemctl --user enable xvpn-client
systemctl --user start xvpn-client

# 5. Запуск GUI
python3 client/chatvpn_gui.py
```

### 3. Установка на Windows

#### Автоматическая установка

```cmd
# 1. Установка обязательных зависимостей (включая ChromaDB для AI-оркестратора)
pip install chromadb sentence-transformers

# 2. Запуск установщика
.\installer\install_xvpn.bat

# 3. Ручная настройка
set XVPN_SERVER=https://api.yourdomain.com:8443
python client\chatvpn_gui.py
```

#### Ручная установка

```cmd
# 1. Установка Python 3.8+
# 2. Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git
cd chatvpn

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Настройка клиента
copy client\client.json.example client\client.json
notepad client\client.json

# 5. Запуск GUI
python client\chatvpn_gui.py
```

### 4. Установка на macOS

#### Через Homebrew

```bash
# 1. Установка обязательных зависимостей (включая ChromaDB для AI-оркестратора)
brew install python3 docker-compose chroma
pip3 install chromadb sentence-transformers

# 2. Клонирование проекта
git clone https://github.com/xvpn/xvpn.git
cd chatvpn

# 3. Установка через pip
pip3 install -r requirements.txt

# 4. Запуск GUI
python3 client/chatvpn_gui.py
```

---

## 🐳 Docker Compose развертывание

### Полная конфигурация

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Traefik Load Balancer
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.xvpn.address=:8443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@yourdomain.com"
    ports:
      - "80:80"
      - "443:443"
      - "8443:8443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./traefik/letsencrypt:/letsencrypt"
      - "./traefik/traefik.yml:/etc/traefik/traefik.yml:ro"
    networks:
      - xvpn-network

  # XVPN API Service
  xvpn-api:
    build: 
      context: .
      dockerfile: docker/Dockerfile.api
    command: uvx run --app api.main:app
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:////data/xvpn.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - xvpn-data:/data
      - ./config:/config:ro
    networks:
      - xvpn-network
    depends_on:
      - redis

  # XVPN Agent Service
  xvpn-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.agent
    command: uvx run --app agent.main:agent
    environment:
      - DATABASE_URL=sqlite:////data/agent.db
      - MANIFEST_URL=http://xvpn-api:8443/transports/manifest.json
    volumes:
      - xvpn-data:/data
      - ./server/agent/knowledge:/app/agent/knowledge:ro
    networks:
      - xvpn-network
    depends_on:
      - xvpn-api
      - redis

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - xvpn-network

  # XVPN Core VPN
  xvpn-core:
    image: teddysun/xray:latest
    volumes:
      - ./config/xray:/config:ro
    networks:
      - xvpn-network

volumes:
  xvpn-data:
  redis-data:

networks:
  xvpn-network:
    driver: bridge
```

### Запуск Docker

```bash
# Клонирование проекта
git clone https://github.com/xvpn/xvpn.git
cd xvpn

# Настройка окружения
cp .env.example .env
nano .env

# Запуск всех сервисов
docker-compose up -d

# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f xvpn-api

# Остановка
docker-compose down
```

---

## 🔧 Конфигурация компонентов

### 1. Серверная конфигурация

#### API сервер (`/opt/xvpn/api/config.json`)

```json
{
  "host": "0.0.0.0",
  "port": 8443,
  "ssl": true,
  "ssl_cert": "/etc/ssl/certs/xvpn.crt",
  "ssl_key": "/etc/ssl/certs/xvpn.key",
  "database": {
    "url": "sqlite:////opt/xvpn/agent/db/agent.db",
    "echo": false
  },
  "security": {
    "rate_limit": "100/hour",
    "ip_blacklist": [],
    "cors_origins": ["*"]
  }
}
```

#### Агент (`/opt/xvpn/agent/config.json`)

```json
{
  "agent_uuid": "xvpn-agent-001",
  "health_check_interval": 30,
  "transport_switch_timeout": 15,
  "max_retries": 3,
  "rag_system": {
    "enabled": true,
    "vector_db": "chromadb",
    "embedding_model": "all-MiniLM-L6-v2"
  }
}
```

### 2. Клиентская конфигурация

#### Основной клиент (`~/chatvpn/client/client.json`)

```json
{
  "client_uuid": "xvpn-client-001",
  "server_url": "https://api.yourdomain.com:8443",
  "auto_connect": true,
  "proxy_mode": "full",
  "ipv6_support": true,
  "health_check": {
    "enabled": true,
    "interval": 30,
    "mask_score_threshold": 3
  },
  "transports": {
    "websocket": {
      "enabled": true,
      "priority": 1
    },
    "tcp": {
      "enabled": true,

### AI модель для оркестратора

Для XVPN оркестратора выбрана **TinyLlama 1.1B** - оптимальная open-source модель:

**Характеристики:**
- Параметры: 1.1B
- Размер: ~2.2GB (GGUF)
- RAM при запуске: 4-6GB
- Оптимизирована для CPU
- Легко интегрируется через Ollama

**Альтернативы:**
- **OpenRouter + Claude Haiku**: более мощная, но требует API ключа
- **Phi-2 2.7B**: больше параметров, но требует больше ресурсов
- **Mistral 7B Q4**: хорошая производительность, но больше размера

**Установка через Docker:**
```bash
# Сборка образа оркестратора
docker build -f docker/Dockerfile.orchestrator -t xvpn-orchestrator .

# Запуск с Ollama и TinyLlama
docker run -d \
  --name xvpn-orchestrator \
  -p 11434:11434 \
  -p 8080:8080 \
  -v /var/log/xvpn:/var/log/xvpn \
  xvpn-orchestrator
```


## 🤖 AI-Оркестратор XVPN

### Обзор
AI-оркестратор XVPN - это система управления рисками и автоматического восстановления, которая обеспечивает мониторинг, диагностику и автоматическое восстановление системы при сбоях.

### Компоненты оркестратора:
- **Мониторинг здоровья** - автоматическая проверка состояния всех сервисов
- **Анализ рисков** - оценка серьезности проблем и принятие решений
- **Автовосстановление** - автоматический перезапуск сервисов при сбоях
- **Логирование действий** - детальное логирование всех операций
- **Уведомления администратора** - уведомления о критических проблемах

### Архитектура оркестратора:
```
┌─────────────────────────────────────────────────────────────┐
│                   AI Orchestrator                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Health      │  │ Action      │  │ Recovery        │   │
│  │ Monitor     │◄─│ Logger      │◄─│ Engine         │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                    │                      │                  │
│  ┌─────────────┐  │  ┌─────────────┐    │  ┌─────────────┐  │
│  │ Test Runner │  │  │ Log Cleaner │    │  │ Systemd      │  │
│  └─────────────┘  └───────────────┘    │  │ Controller  │  │
│                                            └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Установка и настройка оркестратора

#### 1. Интеграция компонентов
```bash
# Копирование файлов оркестратора на сервер
sudo cp -r server/agent/orchestrator.py /opt/xvpn/agent/
sudo cp -r server/agent/scripts /opt/xvpn/agent/
sudo cp server/agent/orchestrator_config.json /opt/xvpn/agent/

# Установка systemd-сервиса
sudo cp systemd/xvpn-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload

# Автоматическая интеграция
cd /opt/xvpn/agent/scripts
sudo python3 integrate_orchestrator.py
```

#### 2. Настройка конфигурации
```bash
# Редактирование конфигурации оркестратора
sudo nano /opt/xvpn/agent/orchestrator_config.json
```

Основные параметры конфигурации:
- `health_check.interval`: интервал проверки здоровья (секунды)
- `max_failures`: максимальное количество сбоев
- `recovery.actions`: действия восстановления
- `notifications.enabled`: включение уведомлений

#### 3. Запуск оркестратора
```bash
# Включение автозапуска
sudo systemctl enable xvpn-orchestrator

# Запуск сервиса
sudo systemctl start xvpn-orchestrator

# Проверка статуса
sudo systemctl status xvpn-orchestrator

# Просмотр логов
sudo journalctl -u xvpn-orchestrator -f
```

### Управление оркестратором

#### Команды управления:
```bash
# Перезапуск оркестратора
sudo systemctl restart xvpn-orchestrator

# Остановка оркестратора
sudo systemctl stop xvpn-orchestrator

# Перезагрузка конфигурации
sudo systemctl reload xvpn-orchestrator
```

#### Мониторинг состояния:
```bash
# Проверка здоровья системы
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health

# Просмотр логов оркестратора
tail -f /var/log/xvpn/orchestration/orchestrator.log

# Запуск диагностики
sudo python3 /opt/xvpn/agent/scripts/test_runner.py
```

### Сценарии восстановления

#### 1. Автоматическое восстановление при сбоях API:
```
1. Мониторинг обнаруживает недоступность API
2. Оркестратор запускает диагностику
3. При подтверждении проблемы - перезапускает сервис xvpn-api
4. Проверяет результат восстановления
5. При успехе - продолжает мониторинг
6. При неудаче - уведомляет администратора
```

#### 2. Восстановление VPN ядра:
```
1. Обнаружена неактивность VPN ядра
2. Оркестратор проверяет зависимости
3. Перезапускает сервис xvpn-core
4. Мониторит восстановление соединения
5. При необходимости - запускает альтернативные протоколы
```

#### 3. Критическое состояние системы:
```
1. Критическое количество сбоев (> 5)
2. Запуск полной диагностики
3. Перезапуск всех сервисов
4. Уведомление администратора
5. Ручное вмешательство при необходимости
```

### Логирование и мониторинг

#### Структура логов:
```
/var/log/xvpn/orchestration/    # Логи оркестратора
/var/log/xvpn/agent/           # Логи агента
/var/log/xvpn/api/             # Логи API
/var/log/xvpn/core/            # Логи VPN ядра
```

#### Автоматическая очистка логов:
```bash
# Запуск очистки вручную
sudo python3 /opt/xvpn/agent/scripts/log_cleaner.py

# Автоматическая очистка (каждый день в 2:00)
sudo systemctl status xvpn-orchestrator
```

### Тестирование оркестратора

#### Запуск тестов:
```bash
# Полный набор тестов
sudo python3 /opt/xvpn/agent/scripts/test_runner.py

# Тесты сетевой активности
sudo python3 /opt/xvpn/agent/scripts/test_runner.py run_network_tests

# Тесты VPN
sudo python3 /opt/xvpn/agent/scripts/test_runner.py run_vpn_tests

# Тесты системы
sudo python3 /opt/xvpn/agent/scripts/test_runner.py run_system_tests
```

#### Симуляция сбоев:
```bash
# Остановка API для тестирования
sudo systemctl stop xvpn-api

# Мониторинг реакции оркестратора
sudo journalctl -u xvpn-orchestrator -f

# Проверка автоматического восстановления
sudo systemctl status xvpn-api
```

### Конфигурация уведомлений

#### Telegram уведомления:
```bash
# Установка переменных окружения
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Перезагрузка конфигурации
sudo systemctl restart xvpn-orchestrator
```

#### Email уведомления:
```bash
# Настройка email
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT=587
export SMTP_USERNAME="your_email@gmail.com"
export SMTP_PASSWORD="your_password"
export FROM_EMAIL="your_email@gmail.com"
export TO_EMAIL="admin@yourdomain.com"
```

### Производительность и оптимизация

#### Ресурсные ограничения:
- **Память**: до 512MB
- **CPU**: до 50%
- **Диск**: автоматическая очистка логов старше 7 дней

#### Оптимизация производительности:
```bash
# Просмотр статистики логов
sudo python3 /opt/xvpn/agent/scripts/log_cleaner.py get_log_stats

# Очистка кэша
sudo systemctl restart xvpn-orchestrator
```

### Решение проблем

#### Проблемы с оркестратором:
```bash
# Проверка статуса
sudo systemctl status xvpn-orchestrator

# Просмотр логов
sudo journalctl -u xvpn-orchestrator -n 100

# Перезапуск
sudo systemctl restart xvpn-orchestrator
```

#### Проблемы с восстановлением:
```bash
# Запруч диагностики
sudo python3 /opt/xvpn/agent/scripts/test_runner.py

# Проверка зависимостей
sudo systemctl list-dependencies xvpn-orchestrator
```

### Обновление оркестратора

```bash
# Остановка сервисов
sudo systemctl stop xvpn-orchestrator

# Обновление кода
cd /opt/xvpn/agent
git pull origin main

# Запуск сервисов
sudo systemctl start xvpn-orchestrator

# Проверка обновлений
sudo systemctl status xvpn-orchestrator
```

      "priority": 2
    },
    "grpc": {
      "enabled": true,
      "priority": 3
    }
  }
}
```

---

## 📊 Мониторинг и логирование

### 1. Systemd мониторинг

```bash
# Просмотр статуса всех сервисов
sudo systemctl status xvpn-*

# Просмотр логов
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f

# Перезапуск сервисов
sudo systemctl restart x
