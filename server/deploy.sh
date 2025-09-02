#!/bin/bash
set -euo pipefail

# === Настройки ===
SERVER="user@77.110.123.27"   # заменишь user@ip на свой сервер
REMOTE_TMP="/tmp/chatvpn"
REMOTE_OPT="/opt/xvpn"

echo "[1/6] Создаю временную папку на сервере..."
ssh "$SERVER" "mkdir -p $REMOTE_TMP"

echo "[2/6] Копирую файлы..."
scp ~/chatvpn/server/install_server.sh \
    ~/chatvpn/server/server_bot.pyz \
    ~/chatvpn/server/server_bot.service \
    ~/chatvpn/server/xray.service \
    "$SERVER:$REMOTE_TMP/"

echo "[3/6] Переношу файлы на сервер..."
ssh "$SERVER" "sudo mkdir -p $REMOTE_OPT && \
    sudo mv $REMOTE_TMP/install_server.sh $REMOTE_OPT/ && \
    sudo mv $REMOTE_TMP/server_bot.pyz $REMOTE_OPT/ && \
    sudo mv $REMOTE_TMP/server_bot.service /etc/systemd/system/ && \
    sudo mv $REMOTE_TMP/xray.service /etc/systemd/system/ && \
    sudo chown -R root:root $REMOTE_OPT/ && \
    sudo rm -rf $REMOTE_TMP"

echo "[4/6] Перечитываю systemd..."
ssh "$SERVER" "sudo systemctl daemon-reload"

echo "[5/6] Включаю автозапуск сервисов..."
ssh "$SERVER" "sudo systemctl enable --now server_bot xray"

echo "[6/6] Проверяю статусы сервисов..."
ssh "$SERVER" "sudo systemctl status server_bot --no-pager"
ssh "$SERVER" "sudo systemctl status xray --no-pager"

echo "=== Деплой завершён успешно ==="
