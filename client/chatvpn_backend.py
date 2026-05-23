#!/usr/bin/env python3
# ChatVPN backend
# Абсолютный путь: ~/chatvpn/client/chatvpn_backend.py

import os
import subprocess
import requests
import time

CONFIG_PATH = os.path.expanduser("~/chatvpn/client/client.json")
CONF_UUID_PATH = os.path.expanduser("~/chatvpn/client/client.conf")

XRAY_BIN = "/usr/bin/xray"   # путь к бинарю xray
XRAY_PROC = None


# =============================
# UUID клиента
# =============================

def get_client_uuid():
    if os.path.exists(CONF_UUID_PATH):
        with open(CONF_UUID_PATH, "r") as f:
            return f.read().strip()
    return None

def save_client_uuid(uuid):
    with open(CONF_UUID_PATH, "w") as f:
        f.write(uuid.strip())


# =============================
# Запрос client.json у сервера
# =============================

def fetch_config_from_server(save_path=CONFIG_PATH):
    # если сервер умеет отдавать напрямую
    return False, "Прямой серверный конфиг не реализован"


# =============================
# Запрос client.json у бота
# =============================

def fetch_config_from_bot(save_path=CONFIG_PATH):
    client_uuid = get_client_uuid()
    if not client_uuid:
        return False, "UUID не задан"

    try:
        cmd = f"/get_config {client_uuid}"

        # сначала получаем последний update_id (чтобы отбрасывать старые события)
        updates = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", timeout=5
        ).json()
        last_update_id = 0
        for u in updates.get("result", []):
            last_update_id = max(last_update_id, u["update_id"])

        # отправляем команду в бот
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": cmd}, timeout=5
        )

        # ждём до 20 секунд
        for _ in range(20):
            updates = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": last_update_id + 1}, timeout=5
            ).json()

            for u in updates.get("result", []):
                msg = u.get("message", {})
                doc = msg.get("document")
                if doc and doc["file_name"] == "client.json":
                    file_id = doc["file_id"]

                    f = requests.get(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                        params={"file_id": file_id}, timeout=5
                    ).json()

                    file_path = f["result"]["file_path"]
                    dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    r = requests.get(dl_url, timeout=5)

                    with open(save_path, "wb") as f_out:
                        f_out.write(r.content)

                    return True, "Конфиг получен через бота"

            time.sleep(1)

        return False, "Бот не прислал client.json за 20 секунд"
    except Exception as e:
        return False, f"Ошибка у бота: {e}"


# =============================
# Управление конфигом
# =============================

def load_config():
    ok, msg = fetch_config_from_server()
    if ok:
        return ok, msg
    return fetch_config_from_bot()


# =============================
# Управление Xray
# =============================

def start_vpn():
    global XRAY_PROC
    if not os.path.exists(CONFIG_PATH):
        return False, "Нет client.json, запросите конфиг"

    try:
        XRAY_PROC = subprocess.Popen([XRAY_BIN, "-c", CONFIG_PATH])
        return True, "VPN запущен"
    except Exception as e:
        return False, f"Ошибка запуска: {e}"

def stop_vpn():
    global XRAY_PROC
    if XRAY_PROC:
        XRAY_PROC.terminate()
        XRAY_PROC = None
        return True, "VPN остановлен"
    return False, "VPN не запущен"

def is_running():
    return XRAY_PROC is not None and XRAY_PROC.poll() is None


# =============================
# Статус: IP и скорость
# =============================

def get_ip():
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        return r.text.strip()
    except:
        return "?"

def get_speed():
    # ⚠️ заглушка: сюда можно прикрутить ifstat/psutil
    return 0, 0
