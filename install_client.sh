#!/bin/bash
# XVPN Client Installation Script
# Установка XVPN клиента на локальную машину

set -e  # Выход при любой ошибке

echo "🚀 Установка XVPN клиента..."

# Проверка прав (клиент не требует root)
if [ "$EUID" -eq 0 ]; then
    echo "❌ Не запускайте клиент от root. Запустите как обычный пользователь."
    exit 1
fi

# Инициализация переменных
CHATVPN_DIR="$HOME/chatvpn"
CLIENT_DIR="$CHATVPN_DIR/client"
LOGS_DIR="$CLIENT_DIR/logs"
TRANSPORTS_DIR="$CLIENT_DIR/transports"
CLIENTS_DIR="$CLIENT_DIR/clients"

echo "🔧 Подготовка директорий..."
mkdir -p "$CLIENT_DIR" "$LOGS_DIR" "$TRANSPORTS_DIR" "$CLIENTS_DIR"
mkdir -p "$CLIENT_DIR/gui" "$CLIENT_DIR/states"

echo "📦 Установка системных зависимостей..."
sudo apt update
sudo apt install -y python3 python3-pip python3-tk curl wget jq

# Установка uv
echo "📦 Установка uv (современный Python пакетный менеджер)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
source "$HOME/.cargo/env"

# Клонирование репозитория (используем ваш репозиторий)
echo "📥 Клонирование репозитория..."
if [ -d "$CHATVPN_DIR" ]; then
    echo "⚠️  Директория $CHATVPN_DIR уже существует, обновляем..."
    cd "$CHATVPN_DIR"
    git pull
else
    cd /tmp
    git clone https://github.com/Mehan42/chatVPN.git chatvpn-install
    cp -r chatvpn-install/client/* "$CLIENT_DIR/"
    rm -rf chatvpn-install
fi

# Установка Python зависимостей
echo "🐍 Установка Python зависимостей..."
pip3 install --user -r "$CLIENT_DIR/requirements.txt"

# Установка дополнительных зависимостей для клиента
pip3 install --user requests flask pydantic click pillow pystray

echo "⚙️ Настройка автозапуска через systemd (пользовательский сервис)..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/xvpn-client.service" << EOF
[Unit]
Description=XVPN Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/chatvpn/client/chatvpn_backend.py start
Restart=always
RestartSec=10
WorkingDirectory=%h/chatvpn/client
Environment=PYTHONPATH=%h/chatvpn/client
StandardOutput=append:%h/chatvpn/client/logs/client_stdout.log
StandardError=append:%h/chatvpn/client/logs/client_stderr.log

[Install]
WantedBy=default.target
EOF

# Настройка путей в скриптах
echo "🔧 Обновление абсолютных путей в скриптах..."
sed -i "s|~/chatvpn/client|$CLIENT_DIR|g" "$CLIENT_DIR/chatvpn_backend.py"
sed -i "s|~/chatvpn/client|$CLIENT_DIR|g" "$CLIENT_DIR/chatvpn_gui.py"

echo "🎯 Установка завершена!"
echo ""
echo "📋 Дальнейшие шаги:"
echo "1. Получите client.json от администратора и положите в $CLIENTS_DIR"
echo "2. Запустите GUI: python3 $CLIENT_DIR/chatvpn_gui.py"
echo "3. Или запустите автоматически: systemctl --user start xvpn-client"
echo "4. Для автозапуска: systemctl --user enable xvpn-client"
echo ""
echo "💡 Подсказки:"
echo "- Кнопка 'Запросить конфиг' в GUI будет работать, если сервер настроен"
echo "- Индикатор безопасности покажет уровень маскировки"
echo "- Для IPv6 подключения убедитесь, что IPv6 включен в системе"

# Проверка минимальной установки
if [ -f "$CLIENT_DIR/chatvpn_gui.py" ] && [ -f "$CLIENT_DIR/chatvpn_backend.py" ]; then
    echo "✅ Клиент установлен корректно"
else
    echo "❌ Ошибка установки клиента"
    exit 1
fi

exit 0