# Правильный процесс установки XVPN

## Подготовительные шаги

### 1. Проверка системы
```bash
# Проверка версии ОС
cat /etc/os-release

# Проверка свободного места
df -h

# Проверка оперативной памяти
free -h

# Проверка архитектуры
uname -m
```

### 2. Установка системных зависимостей
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-venv python3-dev curl wget git jq socat

# Установка Docker (опционально)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

## Этап 1: Подготовка окружения

### 1.1 Создание пользователя и директорий
```bash
# Создание пользователя xvpn
sudo useradd -r -s /bin/false -d /opt/xvpn xvpn 2>/dev/null || true

# Создание директорий
sudo mkdir -p /opt/xvpn/{data,logs,config,tls}
sudo chown -R xvpn:xvpn /opt/xvpn
sudo chmod -R 750 /opt/xvpn
```

### 1.2 Клонирование репозитория
```bash
cd /tmp
git clone https://github.com/Mehan42/chatVPN.git
sudo cp -r chatVPN/* /opt/xvpn/
sudo chown -R xvpn:xvpn /opt/xvpn
```

### 1.3 Проверка файлов
```bash
# Проверить наличие основных файлов
ls -la /opt/xvpn/server/api/app.py
ls -la /opt/xvpn/client/vpn_client.py
ls -la /opt/xvpn/requirements_server.txt
```

## Этап 2: Установка Python зависимостей

### 2.1 Создание виртуального окружения
```bash
# Создание виртуального окружения
sudo python3 -m venv /opt/xvpn/venv
sudo chown -R xvpn:xvpn /opt/xvpn/venv

# Установка зависимостей сервера
sudo -u xvpn /opt/xvpn/venv/bin/pip install --upgrade pip
sudo -u xvpn /opt/xvpn/venv/bin/pip install -r /opt/xvpn/requirements_server.txt

# Установка зависимостей клиента (если нужно)
sudo -u xvpn /opt/xvpn/venv/bin/pip install -r /opt/xvpn/requirements_client.txt
```

### 2.2 Проверка установки зависимостей
```bash
# Проверить, что зависимости установлены
sudo -u xvpn /opt/xvpn/venv/bin/python3 -c "import flask; print('Flask OK')"
sudo -u xvpn /opt/xvpn/venv/bin/python3 -c "import requests; print('Requests OK')"
sudo -u xvpn /opt/xvpn/venv/bin/python3 -c "import psutil; print('Psutil OK')"
```

## Этап 3: Установка XRay

### 3.1 Установка XRay
```bash
# Установка XRay
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Проверка установки
xray version
```

### 3.2 Настройка XRay конфигурации
```bash
# Создание директории конфигурации
sudo mkdir -p /usr/local/etc/xray

# Копирование примера конфигурации (замените на вашу конфигурацию)
# sudo cp /opt/xvpn/xray_config.json /usr/local/etc/xray/config.json
```

## Этап 4: Настройка SSL сертификатов

### 4.1 Установка Certbot
```bash
sudo apt install -y certbot

# Для получения сертификата понадобится домен, указывающий на этот сервер
# sudo certbot certonly --standalone -d yourdomain.com
```

### 4.2 Настройка путей к сертификатам
```bash
# Проверка наличия сертификатов (после получения)
# ls -la /etc/letsencrypt/live/yourdomain.com/

# Создание символических ссылок или копирование
# sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/xvpn/tls/cert.pem
# sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/xvpn/tls/key.pem
# sudo chown xvpn:xvpn /opt/xvpn/tls/*.pem
# sudo chmod 600 /opt/xvpn/tls/key.pem
```

## Этап 5: Настройка systemd сервисов

### 5.1 Создание сервисных файлов
```bash
# API сервис
sudo tee /etc/systemd/system/xvpn-api.service > /dev/null << EOF
[Unit]
Description=XVPN API Server
After=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn
Environment=PATH=/opt/xvpn/venv/bin
ExecStart=/opt/xvpn/venv/bin/python3 /opt/xvpn/server/api/app.py
Restart=always
RestartSec=5
Environment=FLASK_ENV=production
Environment=PYTHONPATH=/opt/xvpn

[Install]
WantedBy=multi-user.target
EOF

# Агент сервис
sudo tee /etc/systemd/system/xvpn-agent.service > /dev/null << EOF
[Unit]
Description=XVPN Agent
After=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn
Environment=PATH=/opt/xvpn/venv/bin
ExecStart=/opt/xvpn/venv/bin/python3 /opt/xvpn/server/agent/agent.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/xvpn

[Install]
WantedBy=multi-user.target
EOF

# Оркестратор сервис
sudo tee /etc/systemd/system/xvpn-orchestrator.service > /dev/null << EOF
[Unit]
Description=XVPN Orchestrator
After=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn
Environment=PATH=/opt/xvpn/venv/bin
ExecStart=/opt/xvpn/venv/bin/python3 /opt/xvpn/server/agent/orchestrator.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/xvpn

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 Загрузка и проверка сервисов
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Проверка синтаксиса сервисов
sudo systemctl status xvpn-api --no-pager
sudo systemctl status xvpn-agent --no-pager
sudo systemctl status xvpn-orchestrator --no-pager
```

## Этап 6: Тестирование установки

### 6.1 Проверка сервисов
```bash
# Проверка, что сервисы доступны
systemctl list-unit-files | grep xvpn
```

### 6.2 Запуск и проверка работы
```bash
# Запуск агента и оркестратора (они не требуют SSL сразу)
sudo systemctl start xvpn-agent
sudo systemctl start xvpn-orchestrator

# Проверка статуса
sudo systemctl status xvpn-agent --no-pager
sudo systemctl status xvpn-orchestrator --no-pager
```

### 6.3 Тестирование API (после получения SSL сертификатов)
```bash
# После настройки SSL и запуска API:
# sudo systemctl start xvpn-api
# 
# curl -k https://localhost:8443/mcp/v1/vpn.health
```

## Этап 7: Проверка готовности системы

### 7.1 Проверка процессов
```bash
# Проверить запущенные процессы
ps aux | grep -E "(xray|python)" | grep -v grep
```

### 7.2 Проверка портов
```bash
# Проверить открытые порты
sudo netstat -tlnp | grep -E "(443|8443)"
```

### 7.3 Проверка логов
```bash
# Проверить логи (если есть активность)
sudo tail -f /var/log/xray/access.log 2>/dev/null || echo "XRay logs not found"
sudo ls -la /opt/xvpn/logs/ 2>/dev/null || echo "XVPN logs not found"
```

## Автоматизированный тест установки

Создайте скрипт для автоматической проверки:

```bash
cat << 'EOF' > /tmp/test_installation.sh
#!/bin/bash

echo "=== Тестирование установки XVPN ==="
SUCCESS=0
TOTAL=0

test_step() {
    local step="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    echo -n "Тест $TOTAL: $step ... "
    
    if eval "$cmd"; then
        echo "✅"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "❌"
    fi
}

# Тестирование основных компонентов
test_step "Python 3 доступен" "command -v python3"
test_step "Git доступен" "command -v git"
test_step "XRay установлен" "command -v xray"
test_step "Пользователь xvpn существует" "id xvpn"
test_step "Директории созданы" "[ -d /opt/xvpn ] && [ -d /opt/xvpn/venv ]"
test_step "Зависимости установлены" "/opt/xvpn/venv/bin/python3 -c 'import flask'"

# Тестирование сервисов
test_step "API сервис создан" "[ -f /etc/systemd/system/xvpn-api.service ]"
test_step "Агент сервис создан" "[ -f /etc/systemd/system/xvpn-agent.service ]"
test_step "Оркестратор сервис создан" "[ -f /etc/systemd/system/xvpn-orchestrator.service ]"

echo "=== Результаты: $SUCCESS/$TOTAL тестов пройдено ==="

if [ $SUCCESS -eq $TOTAL ]; then
    echo "🎉 Установка прошла успешно!"
    exit 0
else
    echo "⚠️  Требуется ручная проверка недостающих компонентов"
    exit 1
fi
EOF

chmod +x /tmp/test_installation.sh
sudo /opt/xvpn/venv/bin/python3 /tmp/test_installation.sh
```

## Резервное копирование конфигурации

Создайте скрипт резервного копирования:

```bash
cat << 'EOF' > /tmp/backup_config.sh
#!/bin/bash

BACKUP_DIR="/opt/xvpn/backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Резервное копирование конфигураций
cp -r /opt/xvpn/config "$BACKUP_DIR/" 2>/dev/null || echo "Нет пользовательских конфигов"
cp /opt/xvpn/requirements*.txt "$BACKUP_DIR/" 2>/dev/null || echo "Нет файлов зависимостей"
cp /etc/systemd/system/xvpn-*.service "$BACKUP_DIR/" 2>/dev/null || echo "Нет systemd файлов"

echo "Резервная копия создана в: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
EOF

chmod +x /tmp/backup_config.sh
```

После прохождения всех тестов система XVPN будет полностью готова к работе.