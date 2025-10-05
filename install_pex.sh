#!/bin/bash
# XVPN PEX Installation Script

set -e  # Выход при ошибке

echo "🚀 Установка XVPN с использованием PEX (автономные исполняемые файлы)"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Проверка наличия pex
if ! command -v python3 -m pex &> /dev/null; then
    echo "📦 Установка pex..."
    pip3 install pex
fi

# Создание директории установки
INSTALL_DIR="/opt/xvpn"
sudo mkdir -p "$INSTALL_DIR/pex"
sudo mkdir -p "$INSTALL_DIR/data"
sudo mkdir -p "$INSTALL_DIR/logs"

# Определяем архитектуру
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH="x86_64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    ARCH="aarch64"
else
    echo "⚠️ Архитектура $ARCH может не поддерживаться, продолжаем..."
fi

# Проверяем, есть ли уже собранные PEX-файлы
if [ -f "dist/pex/xvpn-api.pex" ] && [ -f "dist/pex/xvpn-agent.pex" ]; then
    echo "✅ Найдены предварительно собранные PEX-файлы, копируем..."
    
    sudo cp dist/pex/xvpn-*.pex "$INSTALL_DIR/pex/"
    sudo chown -R xvpn:xvpn "$INSTALL_DIR/pex"
    sudo chmod +x "$INSTALL_DIR/pex/xvpn-*.pex"
else
    echo "⚠️ PEX-файлы не найдены, собираем..."
    
    # Сборка PEX-файлов
    chmod +x build_pex.sh
    ./build_pex.sh server
    
    # Копирование собранных файлов
    sudo cp dist/pex/xvpn-*.pex "$INSTALL_DIR/pex/"
    sudo chown -R xvpn:xvpn "$INSTALL_DIR/pex"
    sudo chmod +x "$INSTALL_DIR/pex/xvpn-*.pex"
fi

# Установка XRay (если требуется)
echo "🌐 Проверка установки XRay..."
if ! command -v xray &> /dev/null; then
    echo "XRay не найден, установка..."
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
fi

# Установка systemd сервисов для PEX-версий (если на Linux)
if command -v systemctl &> /dev/null; then
    echo "⚙️ Установка systemd сервисов для PEX-компонентов..."
    
    # Создание сервиса для API с PEX
    sudo tee /etc/systemd/system/xvpn-api-pex.service > /dev/null << EOF
[Unit]
Description=XVPN API Server (PEX)
After=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn
ExecStart=/opt/xvpn/pex/xvpn-api.pex
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/xvpn

[Install]
WantedBy=multi-user.target
EOF

    # Создание сервиса для агента с PEX
    sudo tee /etc/systemd/system/xvpn-agent-pex.service > /dev/null << EOF
[Unit]
Description=XVPN Agent (PEX)
After=network.target

[Service]
Type=simple
User=xvpn
Group=xvpn
WorkingDirectory=/opt/xvpn
ExecStart=/opt/xvpn/pex/xvpn-agent.pex
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/xvpn

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    
    echo "ℹ️  PEX-сервисы установлены. Для запуска используйте:"
    echo "   sudo systemctl start xvpn-api-pex"
    echo "   sudo systemctl start xvpn-agent-pex"
fi

echo "✅ Установка XVPN с использованием PEX завершена!"
echo ""
echo "📋 Для запуска PEX-компонентов используйте:"
echo "   sudo -u xvpn /opt/xvpn/pex/xvpn-api.pex"
echo "   sudo -u xvpn /opt/xvpn/pex/xvpn-agent.pex"
echo "   sudo -u xvpn /opt/xvpn/pex/xvpn-client.pex"
echo ""
echo " systemd сервисы: sudo systemctl start xvpn-api-pex"