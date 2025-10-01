cat > ~/chatvpn/client/install_client.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "=== ChatVPN Client Installer ==="

# Проверяем, что запускается не от root
if [ "$EUID" -eq 0 ]; then
   echo "❌ Не запускайте от root. Выполните как обычный
пользователь."
   exit 1
fi

echo "[1/6] Обновление системы..."
sudo apt update -y

echo "[2/6] Установка зависимостей..."
sudo apt install -y python3 python3-pip curl jq python3-tk

echo "[3/6] Установка uv (Python package installer)..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "[4/6] Создание директорий..."
mkdir -p ~/chatvpn/client/{clients,transports,logs,gui}

echo "[5/6] Установка Python зависимостей..."
pip3 install requests flask pydantic

echo "[6/6] Настройка автозапуска..."
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/xvpn-client.service << 'INNEREOF'
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
INNEREOF

echo "=== Установка завершена ==="
echo "📁 Директория клиента: ~/chatvpn/client"
echo "🔧 GUI запуск: python3 ~/chatvpn/client/chatvpn_gui.py"
echo "🔄 Для автозапуска: systemctl --user enable xvpn-client"

echo ""
echo "💡 Использование:"
echo "1. Получите client.json от администратора"
echo "2. Положите client.json в ~/chatvpn/client/clients/"
echo "3. Запустите GUI: python3 ~/chatvpn/client/chatvpn_gui.py"
echo "4. Или запустите автоматически: systemctl --user start
xvpn-client"
EOF

