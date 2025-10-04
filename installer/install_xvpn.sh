#!/bin/bash

# XVPN Installation Script
# Установка XVPN системы с нуля на Ubuntu/Debian сервер

set -e  # Выход при любой ошибке

echo "🚀 Установка XVPN системы..."

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Инициализация переменных
XVPN_USER="xvpn"
XVPN_DIR="/opt/xvpn"
SYSTEMD_DIR="/etc/systemd/system"
LOG_DIR="/var/log/xvpn"
BACKUP_DIR="/opt/xvpn/backups"

echo "🔧 Обновление системы..."
apt update && apt upgrade -y

echo "📦 Установка системных зависимостей..."
apt install -y python3 python3-pip python3-venv curl wget git docker.io docker-compose jq

# Установка uv
echo "📦 Установка uv (современный Python пакетный менеджер)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
source "$HOME/.cargo/env"

# Создание пользователя XVPN
echo "👤 Создание пользователя xvpn..."
if ! id "$XVPN_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$XVPN_DIR" "$XVPN_USER"
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p "$XVPN_DIR" "$LOG_DIR" "$BACKUP_DIR"
chown -R "$XVPN_USER:$XVPN_USER" "$XVPN_DIR" "$LOG_DIR"

# Копирование файлов проекта (предполагаем, что мы уже в корневой директории проекта)
echo "📥 Копирование файлов проекта..."
cp -r ./* "$XVPN_DIR/"
chown -R "$XVPN_USER:$XVPN_USER" "$XVPN_DIR"

# Создание виртуального окружения для серверных компонентов
echo "🐍 Создание виртуального окружения для сервера..."
SERVER_ENV="$XVPN_DIR/server/venv"
python3 -m venv "$SERVER_ENV"
chown -R "$XVPN_USER:$XVPN_USER" "$SERVER_ENV"

# Установка зависимостей в виртуальное окружение
echo "📦 Установка Python зависимостей..."
sudo -u "$XVPN_USER" bash -c "source $SERVER_ENV/bin/activate && pip install --upgrade pip"
sudo -u "$XVPN_USER" bash -c "source $SERVER_ENV/bin/activate && pip install -r $XVPN_DIR/requirements.txt"

# Установка ChromaDB и других AI зависимостей
echo "🤖 Установка AI компонентов..."
sudo -u "$XVPN_USER" bash -c "source $SERVER_ENV/bin/activate && pip install chromadb sentence-transformers"

# Копирование systemd сервисов
echo "⚙️ Копирование systemd сервисов..."
cp "$XVPN_DIR/systemd/"*.service "$SYSTEMD_DIR/"
systemctl daemon-reload

# Создание конфигурационного файла
echo "📝 Создание конфигурационных файлов..."
mkdir -p "$XVPN_DIR/config"
cat > "$XVPN_DIR/config/xvpn.conf" << EOF
{
  "server_ip": "$(curl -s ifconfig.co)",
  "api_port": 8443,
  "bot_token": "",
  "chat_id": "",
  "log_level": "INFO",
  "data_dir": "/opt/xvpn/data",
  "logs_dir": "/var/log/xvpn"
}
EOF

# Создание директорий для данных
mkdir -p "$XVPN_DIR/data/clients" "$XVPN_DIR/data/transports" "$XVPN_DIR/db"

# Настройка прав доступа
chown -R "$XVPN_USER:$XVPN_USER" "$XVPN_DIR/data" "$XVPN_DIR/db"
chmod -R 750 "$XVPN_DIR/data" "$XVPN_DIR/db"

# Создание файла .env для сервисов
cat > "$XVPN_DIR/.env" << EOF
XVPN_USER=$XVPN_USER
XVPN_DIR=$XVPN_DIR
LOG_DIR=$LOG_DIR
BOT_TOKEN=
CHAT_ID=
API_BASE_URL=https://$(curl -s ifconfig.co):8443
DATABASE_URL=sqlite:////opt/xvpn/db/agent.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF

# Включение и запуск Docker
systemctl enable docker
systemctl start docker

# Настройка firewall (только необходимые порты)
echo "🛡️ Настройка firewall..."
apt install -y ufw
ufw --force enable
ufw allow ssh
ufw allow 443/tcp
ufw allow 8443/tcp
ufw allow 8080/tcp  # Traefik dashboard (только для администратора, в продакшене отключить)

# Предупреждение о безопасности
echo "⚠️  ВАЖНО: После установки установите токен Telegram бота в $XVPN_DIR/.env"

echo "✅ Установка завершена!"
echo ""
echo "📋 Дальнейшие шаги:"
echo "1. Установите токен Telegram бота в $XVPN_DIR/.env"
echo "2. Запустите сервисы: sudo systemctl start xvpn-api xvpn-agent xvpn-bot"
echo "3. Проверьте статус: sudo systemctl status xvpn-api xvpn-agent xvpn-bot"
echo "4. Документация: $XVPN_DIR/INSTALLATION_GUIDE.md"

# Проверка установки
if systemctl list-unit-files | grep -q xvpn-api.service; then
    echo "✅ Сервисы установлены корректно"
else
    echo "❌ Ошибка установки сервисов"
    exit 1
fi

exit 0