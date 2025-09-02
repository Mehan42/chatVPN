#!/usr/bin/env bash
# Абсолютный путь: ~/chatvpn/client/install_client.sh
# Установка Xray + Python GUI (tkinter+pystray) и ярлыка ChatVPN

set -euo pipefail

if [ "$EUID" -eq 0 ]; then
  OWNER="${SUDO_USER:-root}"
  OWNER_HOME="$(getent passwd "$OWNER" | cut -d: -f6)"
else
  OWNER="$(id -un)"
  OWNER_HOME="$HOME"
fi

INSTALL_DIR="/opt/chatvpn"
BIN_DIR="$INSTALL_DIR/bin"
CFG_DIR="$INSTALL_DIR/config"
RUN_DIR="$INSTALL_DIR/run"
APP_DESKTOP="$OWNER_HOME/.local/share/applications/ChatVPN.desktop"

echo "[1/6] deps..."
sudo apt update
sudo apt install -y curl unzip python3 python3-tk python3-pil python3-pil.imagetk python3-venv

echo "[2/6] python deps..."
# ставим pystray для текущего пользователя
pip3 install --user --upgrade pip
pip3 install --user pystray

echo "[3/6] dirs..."
sudo mkdir -p "$BIN_DIR" "$CFG_DIR" "$RUN_DIR"
sudo touch /var/log/chatvpn_client.log
sudo chown -R "$OWNER":"$OWNER" "$INSTALL_DIR" /var/log/chatvpn_client.log
mkdir -p "$OWNER_HOME/.local/share/applications"

echo "[4/6] Xray..."
curl -L -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
sudo unzip -o /tmp/xray.zip -d "$BIN_DIR"
sudo chown -R "$OWNER":"$OWNER" "$BIN_DIR"
chmod +x "$BIN_DIR/xray"

echo "[5/6] backend+gui..."
sudo cp -f "$OWNER_HOME/chatvpn/client/chatvpn_backend.py" "$INSTALL_DIR/chatvpn_backend.py"
sudo cp -f "$OWNER_HOME/chatvpn/client/chatvpn_gui.py"     "$INSTALL_DIR/chatvpn_gui.py"
sudo chown "$OWNER":"$OWNER" "$INSTALL_DIR/chatvpn_backend.py" "$INSTALL_DIR/chatvpn_gui.py"

echo "[6/6] desktop shortcut..."
cat > "$APP_DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=ChatVPN
Comment=Мини-клиент для Xray (VLESS+Reality)
Exec=python3 /opt/chatvpn/chatvpn_gui.py
Terminal=false
Categories=Network;
EOF
chmod +x "$APP_DESKTOP"

echo "Готово ✅"
echo "Запуск из меню приложений: ChatVPN"
echo "Логи клиента: /var/log/chatvpn_client.log"
