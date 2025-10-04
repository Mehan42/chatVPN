
# XVPN - Руководство по администрированию клиента

## 📋 Содержание

- [Архитектура клиента](#архитектура-клиента)
- [Установка клиента](#установка-клиента)
- [Конфигурация клиента](#конфигурация-клиента)
- [Системные службы](#системные-службы)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Управление подключениями](#управление-подключениями)
- [Безопасность](#безопасность)
- [Обновления и обслуживание](#обновления-и-обслуживание)
- [Решение проблем](#решение-проблем)

## 🏗️ Архитектура клиента

### Схема клиентской инфраструктуры

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           XVPN Клиентская Инфраструктура                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Client Application Layer                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  chatvpn_gui.py      state_machine.py      vpn_client.py             │    │
│  │  (GUI Interface)    (State Management)    (Core VPN Client)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Transport     │        │   Health        │        │   Proxy         │  │
│  │   Manager       │        │   Monitor       │        │   Helper        │  │
│  │   (Multi-Protocol)│      │   (Connection)  │        │   (Traffic)     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│             │                        │                        │            │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐  │
│  │   Configuration │        │   Logging       │        │   IPv6          │  │
│  │   Manager       │        │   System        │        │   Manager       │  │
│  │   (Settings)    │        │   (Files)       │        │   (Network)     │  │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Operating System Layer                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │   Windows        │  │      Linux/Ubuntu      │  │      macOS          │  │
│  │   Service        │  │      Systemd Service   │  │      Launchd Agent  │  │
│  │   (XVPNClient)   │  │      (xvpn-client)     │  │      (com.xvpn)     │  │
│  └─────────────────┘  └─────────────────────────┘  └─────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Составные части клиента

| Компонент | Описание | Путь | Порт | Зависимости |
|-----------|----------|------|------|-------------|
| **ChatVPN GUI** | Графический интерфейс | `~/chatvpn/client/gui/` | - | PyQt6, state_machine |
| **State Machine** | Управление состоянием | `~/chatvpn/client/state_machine.py` | - | transport_manager, health_monitor |
| **VPN Client** | Основной VPN клиент | `~/chatvpn/client/vpn_client.py` | - | Xray, system_proxy |
| **Transport Manager** | Управление транспортами | `~/chatvpn/client/transport_manager.py` | - | proxy_helper, ipv6_manager |
| **Health Monitor** | Мониторинг здоровья | `~/chatvpn/client/health.py` | - | state_machine, logging |
| **Proxy Helper** | Помощник с прокси | `~/chatvpn/client/proxy_helper.py` | - | system_proxy, network |
| **IPv6 Manager** | Управление IPv6 | `~/chatvpn/client/ipv6_manager.py` | - | network, system |

## 💻 Установка клиента

### Linux клиент

#### Системные требования

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv curl wget git jq htop
```

#### Установка клиента

```bash
# Создание пользователя и директорий
sudo useradd -r -s /bin/false -d /home/chatvpn chatvpn
sudo mkdir -p /home/chatvpn/chatvpn/client
sudo chown -R chatvpn:chatvpn /home/chatvpn

# Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git /home/chatvpn/chatvpn
cd /home/chatvpn/chatvpn

# Копирование файлов клиента
sudo cp -r client/* /home/chatvpn/chatvpn/client/
sudo chmod +x /home/chatvpn/chatvpn/client/*.py
sudo chmod +x /home/chatvpn/chatvpn/client/scripts/*.sh

# Установка Python зависимостей
cd /home/chatvpn/chatvpn/client
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install --upgrade -e .
```

#### Systemd служба клиента

```ini
# /etc/systemd/system/xvpn-client.service
[Unit]
Description=XVPN Client Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=chatvpn
Group=chatvpn
WorkingDirectory=/home/chatvpn/chatvpn/client
ExecStart=/home/chatvpn/chatvpn/client/venv/bin/python /home/chatvpn/chatvpn/client/state_machine.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=XVPN_CONFIG_FILE=/home/chatvpn/chatvpn/client/config.json
Environment=XVPN_SERVER=https://your-server:8443
Environment=XVPN_LOG_LEVEL=INFO
Environment=XVPN_LOG_FILE=/home/chatvpn/chatvpn/client/logs/client.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
MemoryMax=256M
CPUQuota=50%
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
```

#### Запуск клиента

```bash
# Обновление systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable xvpn-client.service

# Запуск сервиса
sudo systemctl start xvpn-client.service

# Проверка статуса
sudo systemctl status xvpn-client.service

# Просмотр логов
sudo journalctl -u xvpn-client -f
```

### Windows клиент

#### Системные требования

- Windows 10 или новее (64-bit)
- Python 3.8+ (в комплекте установщика)
- .NET Framework 4.8+
- Visual C++ Redistributable 2019+

#### Установка через инсталлятор

```powershell
# Запуск инсталлятора от имени администратора
.\installer\install_xvpn.bat

# Следуйте инструкциям инсталлятора
# 1. Выберите директорию установки (C:\xvpn)
# 2. Выберите компоненты для установки
# 3. Настройте параметры подключения
# 4. Завершите установку
```

#### Ручная установка

```powershell
# Создание директорий
mkdir C:\xvpn
mkdir C:\xvpn\client
mkdir C:\xvpn\logs
mkdir C:\xvpn\config

# Копирование файлов
xcopy client C:\xvpn\client\ /E /I /Y
xcopy installer C:\xvpn\installer\ /E /I /Y

# Установка Python
python-3.11.4-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Установка зависимостей
cd C:\xvpn\client
pip install --upgrade pip
pip install -r requirements.txt

# Создание службы Windows
sc create XVPNClient binPath= "C:\xvpn\client\state_machine.py" start= auto
sc description XVPNClient "XVPN Client Service for VPN connectivity"

# Запуск службы
sc start XVPNClient
```

#### Конфигурация Windows

```powershell
# Создание конфигурационного файла
$json = @"
{
  "uuid": "your_client_uuid",
  "version": "1.0.0",
  "server": "https://your-server:8443",
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
    "min_tls_version": "TLSv1.2"
  },
  "network": {
    "ipv6_enabled": true,
    "proxy_mode": "full"
  },
  "logging": {
    "level": "INFO",
    "file": "C:\\xvpn\\logs\\client.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
"@

$json | Out-File -FilePath "C:\xvpn\config\client.json" -Encoding UTF8
```

### macOS клиент

#### Системные требования

- macOS 10.15+ (Catalina)
- Python 3.8+ (через Homebrew)
- Xcode Command Line Tools

#### Установка зависимостей

```bash
# Установка Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python и зависимостей
brew install python@3.11
brew install curl wget jq htop

# Установка GUI зависимостей
brew install pyqt@6
```

#### Установка клиента

```bash
# Создание директорий
mkdir -p ~/Library/Application\ Support/XVPN
mkdir -p ~/Library/LaunchAgents
mkdir -p ~/Library/Logs/XVPN

# Клонирование репозитория
git clone https://github.com/xvpn/xvpn.git /tmp/xvpn
cd /tmp/xvpn

# Копирование файлов клиента
cp -r client/* ~/Library/Application\ Support/XVPN/
chmod +x ~/Library/Application\ Support/XVPN/*.py
chmod +x ~/Library/Application\ Support/XVPN/scripts/*.sh

# Установка Python зависимостей
cd ~/Library/Application\ Support/XVPN
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создание launchd сервиса
cat > ~/Library/LaunchAgents/com.xvpn.client.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xvpn.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/$USER/Library/Application Support/XVPN/venv/bin/python</string>
        <string>/Users/$USER/Library/Application Support/XVPN/state_machine.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/Library/Logs/XVPN/client.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/Library/Logs/XVPN/client.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>XVPN_CONFIG_FILE</key>
        <string>/Users