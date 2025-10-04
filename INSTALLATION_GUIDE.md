
# XVPN - Пошаговое руководство по установке

## 📋 Обзор

Это подробное руководство по установке XVPN системы на разных платформах. Проект разделён на серверную и клиентскую части, каждая из которых имеет свои требования и особенности установки.

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                     XVPN System                            │
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

## 🖥️ Поддерживаемые платформы

### Серверная часть
- **Linux**: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+
- **Минимальные требования**: 2 CPU, 4GB RAM, 20GB дискового пространства
- **Рекомендуемые требования**: 4 CPU, 8GB RAM, 50GB дискового пространства

### Клиентская часть
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 7+
- **Windows**: Windows 10/11 (64-bit)
- **macOS**: macOS 10.15+
- **Минимальные требования**: 1 CPU, 2GB RAM, 5GB дискового пространства

## 🚀 Быстрая установка

### Для Linux (рекомендуется)

```bash
# Автоматическая установка (рекомендуется)
curl -fsSL https://raw.githubusercontent.com/xvpn/xvpn/main/scripts/install_xvpn.sh | sudo bash

# Или ручная установка
sudo apt update && sudo apt upgrade -y
git clone https://github.com/xvpn/xvpn.git
cd xvpn
sudo ./scripts/install_xvpn.sh
```

### Для Windows

```powershell
# Скачайте установщик с GitHub Releases
# Запустите от имени администратора
.\install_xvpn.bat
```

### Для macOS

```bash
# Используйте Homebrew
brew install xvpn/tap/xvpn

# Или скачайте DMG файл и установите вручную
```

## 🔧 Подробная установка

### 1. Установка серверной части

#### 1.1 Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых зависимостей
sudo apt install -y curl wget git unzip jq

# Отключение swap (для Docker)
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# Настройка firewall
sudo ufw allow OpenSSH
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
sudo ufw allow 8081/tcp
sudo ufw allow 9090/tcp
sudo ufw --force enable
```

#### 1.2 Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

#### 1.3 Установка uv (Python package manager)

```bash
# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Добавление в PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 1.4 Создание пользователя и директорий

```bash
# Создание пользователя XVPN
sudo useradd -r -s /bin/false -d /opt/xvpn xvpn
sudo mkdir -p /opt/xvpn
sudo chown xvpn:xvpn /opt/xvpn

# Создание директорий
sudo mkdir -p /opt/xvpn/{api,agent,bot,config,data,logs,systemd}
sudo mkdir -p /var/log/xvpn
sudo mkdir -p /etc/xvpn
```

#### 1.5 Копирование файлов конфигурации

```bash
# Копирование systemd сервисов
sudo cp systemd/*.service /etc/systemd/system/

# Копирование конфигураций
sudo cp -r server/* /opt/xvpn/
sudo cp docker-compose.yml /opt/xvpn/
sudo cp traefik/* /opt/xvpn/traefik/

# Установка прав
sudo chown -R xvpn:xvpn /opt/xvpn
sudo chmod +x /opt/xvpn/*.py
sudo chmod +x /opt/xvpn/scripts/*.sh
```

#### 1.6 Настройка Traefik

```bash
# Создание конфигурации Traefik
sudo mkdir -p /opt/xvpn/traefik
sudo tee /opt/xvpn/traefik/traefik.yml > /dev/null <<EOF
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
  xvpn:
    address: ":8443"

providers:
  docker:
    exposedbydefault: false
    network: xvpn-network
  file:
    filename: /opt/xvpn/traefik/tls.yml

certificatesResolvers:
  myresolver:
    acme:
      email: admin@your-domain.com
      storage: /opt/xvpn/traefik/acme.json
      httpChallenge:
        entryPoint: web
EOF

# Создание TLS конфигурации
sudo tee /opt/xvpn/traefik/tls.yml > /dev/null <<EOF
tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
EOF
```

#### 1.7 Настройка systemd сервисов

```bash
# Обновление systemd
sudo systemctl daemon-reload

# Включение сервисов
sudo systemctl enable xvpn-api.service
sudo systemctl enable xvpn-agent.service
sudo systemctl enable xvpn-bot.service
sudo systemctl enable xvpn-worker.service
sudo systemctl enable xvpn-traefik.service

# Запуск сервисов
sudo systemctl start xvpn-api.service
sudo systemctl start xvpn-agent.service
sudo systemctl start xvpn-bot.service
sudo systemctl start xvpn-worker.service
sudo systemctl start xvpn-traefik.service
```

#### 1.8 Проверка установки

```bash
# Проверка статуса сервисов
sudo systemctl status xvpn-*

# Проверка логов
sudo journalctl -u xvpn-api -f
sudo journalctl -u xvpn-agent -f
sudo journalctl -u xvpn-bot -f

# Проверка доступности API
curl -k https://localhost:8443/mcp/v1/vpn.health
curl -k https://localhost:8443/transports/manifest.json
```

### 2. Установка клиентской части

#### 2.1 Для Linux

```bash
# Создание директорий
mkdir -p ~/chatvpn/{client,clients,transports,logs,gui}

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-tk

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Установка Python пакетов
pip3 install requests flask pydantic click

# Копирование файлов клиента
cp -r client/* ~/chatvpn/client/

# Создание systemd сервиса пользователя
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/xvpn-client.service << EOF
[Unit]
Description=XVPN Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/chatvpn/client/state_machine.py
Restart=always
RestartSec=10
WorkingDirectory=%h/chatvpn/client
Environment=PYTHONPATH=%h/chatvpn/client
StandardOutput=append:%h/chatvpn/client/logs/client_stdout.log
StandardError=append:%h/chatvpn/client/logs/client_stderr.log

[Install]
WantedBy=default.target
EOF

# Включение сервиса
systemctl --user daemon-reload
systemctl --user enable xvpn-client
```

#### 2.2 Для Windows

```powershell
# Создание директорий
New-Item -ItemType Directory -Path "C:\chatvpn\client" -Force
New-Item -ItemType Directory -Path "C:\chatvpn\clients" -Force
New-Item -ItemType Directory -Path "C:\chatvpn\transports" -Force
New-Item -ItemType Directory -Path "C:\chatvpn\logs" -Force

# Установка Python (если не установлен)
winget install Python.Python.3.11

# Установка зависимостей
pip install requests flask pydantic click

# Копирование файлов клиента
Copy-Item -Path "client\*" -Destination "C:\chatvpn\client\" -Recurse

# Создание службы Windows
New-Service -Name "XVPN Client" -BinaryPathName "C:\Python39\python.exe C:\chatvpn\client\state_machine.py" -DisplayName "XVPN Client Service" -StartupType Automatic -Description "XVPN Client Service"
```

#### 2.3 Для macOS

```bash
# Создание директорий
mkdir -p ~/chatvpn/{client,clients,transports,logs,gui}

# Установка зависимостей
brew install python-tk

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Установка Python пакетов
pip3 install requests flask pydantic click

# Копирование файлов клиента
cp -r client/* ~/chatvpn/client/

# Настройка автозапуска
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.xvpn.client.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xvpn.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>~/chatvpn/client/state_machine.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>~/chatvpn/client</string>
    <key>StandardOutPath</key>
    <string>~/chatvpn/client/logs/client_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>~/chatvpn/client/logs/client_stderr.log</string>
</dict>
</plist>
EOF

# Включение автозапуска
launchctl load ~/Library/LaunchAgents/com.xvpn.client.plist
```

### 3. Настройка взаимодействия клиент-сервер

#### 3.1 Получение конфигурации от сервера

```bash
# Через Telegram бот
# Отправьте сообщение /newclient боту
# Сохраните полученный файл в ~/chatvpn/client/clients/

# Или через API
curl -k -X POST https://your-server:8443/mcp/v1/admin.newclient -o ~/chatvpn/client/clients/$(uuidgen).json
```

#### 3.2 Настройка переменных окружения

```bash
# Для Linux/macOS
echo 'export XVPN_SERVER=https://your-server:8443' >> ~/.bashrc
echo 'export XVPN_CONFIG=~/chatvpn/client/clients/' >> ~/.bashrc
source ~/.bashrc

# Для Windows (PowerShell)
[Environment]::SetEnvironmentVariable("XVPN_SERVER", "https://your-server:8443", "User")
[Environment]::SetEnvironmentVariable("XVPN_CONFIG", "C:\chatvpn\clients\", "User")
```

#### 3.3 Запуск клиента

```bash
# Для Linux/macOS
systemctl --user start xvpn-client

# Для Windows
net start "XVPN Client"

# Проверка статуса
systemctl --user status xvpn-client
```

### 4. Настройка мониторинга и логирования

#### 4.1 Настройка Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'xvpn-api'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'xvpn-agent'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'xvpn-bot'
    static_configs:
      - targets: ['localhost:9092']
    scrape_interval: 5s
    metrics_path: /metrics
```

#### 4.2 Настройка Grafana

```bash
# Установка Grafana
sudo apt install -y grafana

# Запуск Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Настройка дашбордов
# URL: http://localhost:3000
# Login: admin/admin
# Изменить пароль при первом входе
```

#### 4.3 Настройка логирования

```bash
# Создание logrotate конфигурации
sudo tee /etc/logrotate.d/xvpn > /dev/null <<EOF
/var/log/xvpn/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 xvpn xvpn
    postrotate
        systemctl reload xvpn-api.service
        systemctl reload xvpn-agent.service
        systemctl reload xvpn-bot.service
    endscript
}
EOF
```

### 5. Продвинутая настройка

#### 5.1 Настройка HTTPS с Let's Encrypt

```bash
# Установка Certbot
sudo apt install -
#### 5.1 Настройка HTTPS с Let's Encrypt

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot certonly --nginx -d your-domain.com

# Настройка автоматического обновления
sudo crontab -e
# Добавить строку: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 5.2 Настройка бэкапов

```bash
# Создание скрипта бэкапа
sudo tee /opt/xvpn/scripts/backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/opt/xvpn/backups"
DATE=\$(date +%Y%m%d_%H%M%S)

# Создание бэкапов
mkdir -p \$BACKUP_DIR

# Бэкап БД
sqlite3 /opt/xvpn/agent/db/agent.db ".backup \$BACKUP_DIR/agent_\$DATE.db"

# Бэкап конфигов
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz -C /opt/xvpn .

# Бэкап клиентских конфигов
tar -czf \$BACKUP_DIR/clients_\$DATE.tar.gz -C /opt/xvpn/clients .

# Удаление старых бэкапов (более 7 дней)
find \$BACKUP_DIR -name "*.db" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Бэкап создан: \$BACKUP_DIR/config_\$DATE.tar.gz"
EOF

sudo chmod +x /opt/xvpn/scripts/backup.sh

# Настройка ежедневного бэкапа
sudo crontab -e
# Добавить строку: 0 2 * * * /opt/xvpn/scripts/backup.sh
```

#### 5.3 Настройка безопасности

```bash
# Отключение root входа
sudo passwd -l root

# Настройка SSH
sudo tee /etc/ssh/sshd_config > /dev/null <<EOF
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
EOF

sudo systemctl restart sshd

# Настройка fail2ban
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h

[xvpn-api]
enabled = true
port = 8443
filter = http-auth
logpath = /var/log/xvpn/api.log
maxretry = 5
bantime = 1h
EOF

sudo systemctl restart fail2ban
```

### 6. Устранение неполадок

#### 6.1 Проблемы с установкой

**Проблема: Docker не запускается**
```bash
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

**Проблема: Порт уже занят**
```bash
# Проверка использования порта
sudo netstat -tulpn | grep :8443

# Остановка процесса
sudo kill -9 <PID>
```

**Проблема: Нет доступа к интернету**
```bash
# Проверка сети
ping 8.8.8.8
curl https://google.com

# Настройка прокси (если нужно)
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

#### 6.2 Проблемы с сервисами

**Сервис не запускается**
```bash
# Проверка статуса
sudo systemctl status xvpn-api.service

# Просмотр логов
sudo journalctl -u xvpn-api.service -n 50

# Перезапуск
sudo systemctl restart xvpn-api.service
```

**Проблемы с БД**
```bash
# Проверка целостности БД
sqlite3 /opt/xvpn/agent/db/agent.db "PRAGMA integrity_check;"

# Восстановление БД
sqlite3 /opt/xvpn/agent/db/agent.db ".backup /tmp/backup.db"
sqlite3 /opt/xvpn/agent/db/agent.db ".restore /tmp/backup.db"
```

#### 6.3 Проблемы с клиентом

**Клиент не подключается**
```bash
# Проверка конфигурации
ls -la ~/chatvpn/client/clients/

# Проверка статуса клиента
systemctl --user status xvpn-client

# Просмотр логов
tail -f ~/chatvpn/client/logs/state.log
tail -f ~/chatvpn/client/logs/health.log
```

**Нет доступа к серверу**
```bash
# Проверка доступности сервера
curl -k https://your-server:8443/mcp/v1/vpn.health

# Проверка firewall
sudo ufw status
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
```

### 7. Обновление системы

#### 7.1 Обновление сервера

```bash
# Остановка сервисов
sudo systemctl stop xvpn-api.service
sudo systemctl stop xvpn-agent.service
sudo systemctl stop xvpn-bot.service
sudo systemctl stop xvpn-worker.service

# Обновление кода
cd /opt/xvpn
git pull origin main

# Обновление зависимостей
uv sync

# Запуск сервисов
sudo systemctl start xvpn-api.service
sudo systemctl start xvpn-agent.service
sudo systemctl start xvpn-bot.service
sudo systemctl start xvpn-worker.service

# Проверка обновлений
sudo systemctl status xvpn-*
```

#### 7.2 Обновление клиента

```bash
# Остановка клиента
systemctl --user stop xvpn-client

# Обновление кода
cd ~/chatvpn
git pull origin main

# Обновление зависимостей
uv sync

# Запуск клиента
systemctl --user start xvpn-client

# Проверка обновлений
systemctl --user status xvpn-client
```

### 8. Рекомендации по производительности

#### 8.1 Оптимизация сервера

```bash
# Настройка sysctl
sudo tee /etc/sysctl.conf > /dev/null <<EOF
# Оптимизация сети
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 0
net.ipv4.tcp_max_syn_backlog = 4096
net.core.netdev_max_backlog = 10000

# Оптимизация файловой системы
fs.file-max = 100000
vm.swappiness = 10
EOF

sudo sysctl -p
```

#### 8.2 Оптимизация Docker

```bash
# Настройка Docker daemon
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "exec-opts": ["native.cgroupdriver=systemd"],
  "live-restore": true,
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5
}
EOF

sudo systemctl restart docker
```

### 9. Безопасность

#### 9.1 Настройка SSL/TLS

```bash
# Генерация SSL сертификата
openssl req -x509 -newkey rsa:4096 -keyout /opt/xvpn/ssl/key.pem -out /opt/xvpn/ssl/cert.pem -days 365 -nodes

# Настройка Traefik для SSL
sudo tee /opt/xvpn/traefik/tls.yml > /dev/null <<EOF
tls:
  certificates:
    - certFile: /opt/xvpn/ssl/cert.pem
      keyFile: /opt/xvpn/ssl/key.pem
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
EOF
```

#### 9.2 Настройка безопасности контейнеров

```bash
# Создание отдельной сети Docker
docker network create --driver bridge xvpn-network

# Настройка безопасности
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "userns-remap": "default",
  "live-restore": true,
  "no-new-privileges": true,
  "icc": false
}
EOF

sudo systemctl restart docker
```

### 10. Заключение

Это руководство охватывает все аспекты установки и настройки XVPN системы. Если у вас возникнут вопросы или проблемы, пожалуйста, обратитесь к документации или обратитесь в поддержку.

#### Быстрые ссылки:
- [Настройка сервера](#1-установка-серверной-части)
- [Настройка клиента](#2-установка-клиентской-части)
- [Мониторинг](#4-настройка-мониторинга-и-логирования)
- [Устранение неполадок](#6-устранение-неполадок)
- [Обновление](#7-обновление-системы)

---

**XVPN Installation Guide v1.0.0**  
*Последнее обновление: $(date)*