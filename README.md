# XVPN - Intelligent VPN with AI Agents

Полноценная VPN система с интеллектуальными агентами для автоматического управления транспортами, мониторинга и самовосстановления.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      XVPN System                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ TG Bot      │  │ Flask API      │  │ Main Agent      │  │
│  │ Agent       │◄─┤ (MCP Gateway)  │◄─┤ (State Machine) │  │
│  └─────────────┘  └────────────────┘  └─────────────────┘  │
│                           │                      │          │
│  ┌─────────────┐         │          ┌─────────────────┐    │
│  │ SQLite DB   │◄────────┘          │ Knowledge Base  │    │
│  │ (logs/data) │                    │ (protocols/RAG) │    │
│  └─────────────┘                    └─────────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    VPN Core (Xray/WG)                      │
└─────────────────────────────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │    Clients    │
                        │   (Local PC)  │
                        └───────────────┘
```

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
- `BOT_TOKEN` - токен Telegram бота
- `CHAT_ID` - ID чата администратора

### Обновление через GitHub

```bash
# На сервере
cd /opt/xvpn
git pull origin main
sudo systemctl restart xvpn-*

# Проверка обновлений
sudo systemctl status xvpn-*
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health
```

### Docker развертывание (альтернатива)

```bash
# Создание docker-compose.yml
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  xvpn-api:
    build: 
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8443:8443"
    volumes:
      - ./data:/opt/xvpn/agent/db
    environment:
      - FLASK_ENV=production
    restart: unless-stopped

  xvpn-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.agent
    volumes:
      - ./data:/opt/xvpn/agent/db
    depends_on:
      - xvpn-api
    restart: unless-stopped

  xvpn-bot:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - CHAT_ID=${CHAT_ID}
    depends_on:
      - xvpn-api
    restart: unless-stopped

  xvpn-core:
    image: teddysun/xray
    ports:
      - "443:443"
    volumes:
      - ./config/xray.json:/etc/xray/config.json
    restart: unless-stopped
COMPOSE_EOF

# Запуск через Docker
docker-compose up -d
```

## 🚀 Быстрый старт

### Сервер

1. **Запуск установки:**
```bash
sudo /opt/xvpn/install.sh
```

2. **Настройка Telegram бота:**
```bash
sudo nano /opt/xvpn/admin/.env
# Вставьте ваш BOT_TOKEN и CHAT_ID
```

3. **Запуск сервисов:**
```bash
sudo systemctl start xvpn-api xvpn-agent xvpn-bot
sudo systemctl enable xvpn-api xvpn-agent xvpn-bot
```

4. **Проверка статуса:**
```bash
sudo systemctl status xvpn-*
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health | jq .
```

### Клиент

1. **Установка клиента:**
```bash
~/chatvpn/install_client.sh
```

2. **Получение конфигурации:**
   - Используйте команду `/newclient` в Telegram боте
   - Сохраните полученный JSON в `~/chatvpn/client/clients/`

3. **Настройка переменных окружения:**
```bash
export XVPN_SERVER=https://your-server-ip:8443
```

4. **Запуск клиента:**
```bash
# Тестовый запуск
uv run ~/chatvpn/client/state_machine.py

# Автозапуск
systemctl --user enable xvpn-client
systemctl --user start xvpn-client
```

## 📋 Основные компоненты

### 1. Flask API Agent (`/opt/xvpn/api/app.py`)
**MCP Gateway** - центральный API для управления системой:
- 🔌 `/transports/manifest.json` - получение списка транспортов
- 👤 `/clients/<uuid>.json` - получение клиентских конфигураций
- 🏥 `/mcp/v1/vpn.health` - проверка здоровья системы
- 🔄 `/mcp/v1/agent.rotate/<uuid>` - ротация ключей клиента
- 📊 `/mcp/v1/agent.report/<uuid>` - получение отчетов
- 🆕 `/mcp/v1/admin.newclient` - создание нового клиента

### 2. Main Agent (`/opt/xvpn/agent/agent.py`)
**State Machine** - мозг системы:
- 🔍 **IDLE** → **DISCOVER** → **CONNECTING** → **ACTIVE** → **FALLBACK**
- 📡 Автоматическое переключение транспортов при сбоях
- 🏥 Мониторинг mask_score и health checks
- 📚 RAG-система для выполнения протоколов восстановления
- 📝 Логирование всех событий в SQLite

### 3. Telegram Bot Agent (`/opt/xvpn/admin/tg_bot.py`)
**Управляющий интерфейс**:
- 📱 `/start` - приветствие и список команд
- 📊 `/status` - статус системы и транспортов  
- 🆕 `/newclient` - создание нового клиента
- 🔄 `/rotate` - ротация ключей существующего клиента
- 📋 `/report` - детальный отчет по клиенту

### 4. Client State Machine (`~/chatvpn/client/state_machine.py`)
**Клиентская логика**:
- 🔍 Автоматическое обнаружение транспортов
- 📡 Подключение к оптимальному транспорту
- 🏥 Мониторинг здоровья соединения
- 🔄 Автоматический failover при проблемах

## 🗄️ База данных (SQLite)

Расположение: `/opt/xvpn/agent/db/agent.db`

### Таблицы:
- **logs** - события системы (timestamp, component, state, action, result)
- **protocols** - playbooks для автоматического восстановления  
- **fallback** - резервные ресурсы (IP, домены, DoH серверы)

### Утилиты:
```bash
# Просмотр логов
python3 /opt/xvpn/agent/db.py

# Статистика БД
sqlite3 /opt/xvpn/agent/db/agent.db "SELECT COUNT(*) FROM logs;"
```

## 📚 База знаний (RAG)

### Протоколы (`/opt/xvpn/agent/knowledge/protocols.md`):
- **T0 failed 3x** - переключение на T1
- **API /manifest unreachable > 5min** - использование fallback
- **All transports down** - сбор диагностики и уведомление админа
- **Mask score degradation** - реакция на ухудшение маскировки

### Fallback ресурсы (`/opt/xvpn/agent/knowledge/fallback.json`):
- IP адреса резервных серверов
- Альтернативные домены
- DoH серверы (Cloudflare, Google, Quad9)
- Статические манифесты

## 🔧 Системные службы

### Сервер:
```bash
# Статус всех служб
sudo systemctl status xvpn-*

# Логи
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f  
sudo journalctl -u xvpn-bot -f
```

### Клиент:
```bash
# Пользовательский сервис
systemctl --user status xvpn-client
journalctl --user -u xvpn-client -f

# Логи клиента
tail -f ~/chatvpn/client/logs/state.log
tail -f ~/chatvpn/client/logs/health.log
```

## 🛠️ Разработка и отладка

### Тестирование API:
```bash
# Проверка здоровья
curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health

# Получение манифеста
curl -sk https://127.0.0.1:8443/transports/manifest.json

# Создание клиента
curl -sk -X POST https://127.0.0.1:8443/mcp/v1/admin.newclient
```

### Мониторинг агента:
```bash
# Последние события агента
sqlite3 /opt/xvpn/agent/db/agent.db "SELECT datetime(ts, 'unixepoch'), state, action, result FROM logs WHERE component='agent' ORDER BY ts DESC LIMIT 10;"
```

### Тестирование клиента:
```bash
# Проверка health monitor
uv run ~/chatvpn/client/health.py

# Запуск state machine в отладочном режиме
uv run ~/chatvpn/client/state_machine.py
```

## 🔒 Безопасность

- 🔐 **TLS** - все API запросы только через HTTPS
- 🔑 **Авторизация** - Telegram бот проверяет chat_id
- 📁 **Права доступа** - БД и конфиги только для root
- 🔄 **Ротация ключей** - автоматическая ротация клиентских ключей
- 📝 **Логирование** - все действия записываются в БД

## 📊 Мониторинг

### Ключевые метрики:
- **Mask Score** (1-5) - оценка качества маскировки
- **Transport Status** - состояние каждого транспорта
- **Health Trend** - тренд изменения здоровья системы
- **Connection Latency** - задержка соединения

### Алерты:
- Mask score < 3 → автоматическое переключение транспорта
- Все транспорты недоступны → уведомление в Telegram
- API недоступен > 5min → использование fallback ресурсов

## 🔄 Обновления и обслуживание

### Обновление системы:
```bash
# Остановка служб
sudo systemctl stop xvpn-*

# Обновление кода (git pull, etc)
cd /opt/xvpn
git pull origin main

# Перезапуск
sudo systemctl start xvpn-*
```

### Бэкапы:
```bash
# Бэкап БД
cp /opt/xvpn/agent/db/agent.db /opt/xvpn/agent/db/backups/agent.db.$(date +%Y%m%d)

# Бэкап конфигураций
tar -czf /opt/xvpn/backup-$(date +%Y%m%d).tar.gz /opt/xvpn/agent/knowledge/ /opt/xvpn/admin/.env
```

### Очистка логов:
```bash
# Очистка старых логов (> 7 дней)
python3 /opt/xvpn/agent/db.py
```

## 🆘 Решение проблем

### Проблемы с подключением:
1. Проверить статус агента: `sudo systemctl status xvpn-agent`
2. Проверить логи: `sudo journalctl -u xvpn-agent -n 50`
3. Проверить health: `curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health`

### Проблемы с Telegram ботом:
1. Проверить TOKEN и CHAT_ID в `/opt/xvpn/admin/.env`
2. Проверить статус бота: `sudo systemctl status xvpn-bot`
3. Тестировать бота: отправить `/start` в Telegram

### Проблемы клиента:
1. Проверить наличие client.json в `~/chatvpn/client/clients/`
2. Проверить переменную XVPN_SERVER
3. Проверить логи: `journalctl --user -u xvpn-client -n 50`

## 📞 Поддержка

Для получения поддержки:
1. Соберите логи всех служб
2. Проверьте статус через `/status` в Telegram боте
3. Предоставьте mask_score и последние события из БД

---

**Created by AI Agent Mode for ChatVPN Project**  
*Полная автономная VPN система с интеллектуальным управлением*
