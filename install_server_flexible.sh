#!/bin/bash
# Скрипт установки XVPN сервера с поддержкой автоматического обновления

set -e  # Выход при ошибке

# Параметры по умолчанию
INSTALL_DIR="/opt/xvpn"
REPO_URL="https://github.com/Mehan42/chatVPN.git"
BRANCH="main"

# Функция вывода справки
usage() {
    echo "Использование: $0 [опции]"
    echo "Опции:"
    echo "  -d DIR     Директория установки (по умолчанию: /opt/xvpn)"
    echo "  -r URL     URL репозитория (по умолчанию: $REPO_URL)"
    echo "  -b BRANCH  Ветка репозитория (по умолчанию: $BRANCH)"
    echo "  -h         Показать эту справку"
    exit 1
}

# Парсинг аргументов
while getopts "d:r:b:h" opt; do
    case $opt in
        d) INSTALL_DIR="$OPTARG" ;;
        r) REPO_URL="$OPTARG" ;;
        b) BRANCH="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Проверка, что запущено от root
if [ "$EUID" -ne 0 ]; then
    echo "Ошибка: Этот скрипт должен быть запущен от root"
    exit 1
fi

echo "=== Установка XVPN сервера ==="
echo "Директория установки: $INSTALL_DIR"
echo "Репозиторий: $REPO_URL"
echo "Ветка: $BRANCH"
echo ""

# Проверка зависимостей
echo "Проверка зависимостей..."
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: python3 не найден"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Ошибка: git не найден"
    apt update
    apt install -y git
fi

echo "Python3: $(python3 --version)"
echo "Git: $(git --version)"
echo ""

# Создание директории установки и пользователя
echo "Создание пользователя xvpn и директории установки..."
if ! id "xvpn" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" xvpn
fi

mkdir -p "$INSTALL_DIR"
chown xvpn:xvpn "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Клонирование репозитория если нужно
if [ ! -d ".git" ]; then
    echo "Клонирование репозитория..."
    sudo -u xvpn git clone --branch "$BRANCH" "$REPO_URL" ./
else
    echo "Репозиторий уже существует, обновляем..."
    sudo -u xvpn git fetch origin
    sudo -u xvpn git reset --hard "origin/$BRANCH"
fi

echo ""

# Установка Python зависимостей
echo "Установка Python зависимостей..."
if [ -f "requirements_server.txt" ]; then
    python3 -m pip install --user -r requirements_server.txt
else
    echo "Файл requirements_server.txt не найден, устанавливаем основные зависимости..."
    python3 -m pip install requests flask pydantic
fi

echo ""

# Создание необходимых подкаталогов
echo "Создание подкаталогов..."
mkdir -p "$INSTALL_DIR"/{api,agent,admin,core,tls,db,logs,transports,clients}
chown -R xvpn:xvpn "$INSTALL_DIR"

echo ""

# Копирование конфигурации watcher'а
if [ -f "/home/uss/chatvpn/deployment_config.json" ]; then
    echo "Копирование конфигурации watcher'а..."
    cp "/home/uss/chatvpn/deployment_config.json" "$INSTALL_DIR/"
    cp "/home/uss/chatvpn/advanced_deployment_watcher.py" "$INSTALL_DIR/"
    chown xvpn:xvpn "$INSTALL_DIR/deployment_config.json" "$INSTALL_DIR/advanced_deployment_watcher.py"
    echo "Watcher установлен. Для запуска: su - xvpn -c 'cd $INSTALL_DIR && python3 advanced_deployment_watcher.py --config deployment_config.json'"
fi

echo ""

# Создание systemd сервисов
echo "Создание systemd сервисов..."

cat > "/etc/systemd/system/xvpn-api.service" << EOF
[Unit]
Description=XVPN API Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=$INSTALL_DIR/server/api
ExecStart=/usr/bin/python3 $INSTALL_DIR/server/api/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
RemoveIPC=true

[Install]
WantedBy=multi-user.target
EOF

cat > "/etc/systemd/system/xvpn-agent.service" << EOF
[Unit]
Description=XVPN Agent Service
After=network.target xvpn-api.service
Wants=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=$INSTALL_DIR/server/agent
ExecStart=/usr/bin/python3 $INSTALL_DIR/server/agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > "/etc/systemd/system/xvpn-bot.service" << EOF
[Unit]
Description=XVPN Telegram Bot Service
After=network.target xvpn-api.service
Wants=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=$INSTALL_DIR/server/admin
ExecStart=/usr/bin/python3 $INSTALL_DIR/server/admin/tg_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Сервисы systemd созданы"
echo ""

# Запуск systemd daemon-reload
systemctl daemon-reload

echo "=== Установка завершена ==="
echo "Сервер установлен в: $INSTALL_DIR"
echo ""
echo "Для настройки .env файлов:"
echo "  sudo -u xvpn tee $INSTALL_DIR/server/admin/.env << EOF"
echo "  BOT_TOKEN=your_bot_token"
echo "  CHAT_ID=your_chat_id"
echo "  EOF"
echo ""
echo "Для запуска сервисов:"
echo "  systemctl enable xvpn-api xvpn-agent xvpn-bot"
echo "  systemctl start xvpn-api xvpn-agent xvpn-bot"
echo "  systemctl status xvpn-api xvpn-agent xvpn-bot"
echo ""
echo "Для запуска watcher'а (если скопирован):"
echo "  sudo -u xvpn bash -c 'cd $INSTALL_DIR && python3 advanced_deployment_watcher.py --config deployment_config.json'"