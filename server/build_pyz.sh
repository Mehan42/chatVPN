#!/bin/bash
set -euo pipefail

SERVER="user@77.110.123.27"

echo "[1/3] Копирую файлы на сервер..."
scp ~/chatvpn/server/install_server.sh
~/chatvpn/server/server_bot.pyz
~/chatvpn/server/config_server.pyz
"$SERVER:/tmp/"

echo "[2/3] Делаю скрипт исполняемым..."
ssh "$SERVER" "chmod +x /tmp/install_server.sh"

echo "[3/3] Запускаю установку на сервере..."
ssh "$SERVER" "sudo /tmp/install_server.sh"

echo "=== Готово! Проверяйте статус: ssh $SERVER 'systemctl status server_bot xvpn-config --no-pager'"

