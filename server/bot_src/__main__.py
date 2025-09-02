#!/usr/bin/env python3
# Абсолютный путь источника: ~/chatvpn/server/bot_src/__main__.py
# Самодостаточный Telegram-бот без внешних зависимостей (urllib).
# Команды: /ping, /status, /register_client, /get_config
# Конфиг: читает TOKEN/CHAT_ID и пути из /opt/xvpn/data/server.env (или переменных окружения).
# Данные: /opt/xvpn/data/ (profiles.json, server.env), сервер IP передаётся параметром --server-ip.

import os, sys, json, time, uuid, argparse, urllib.request, urllib.parse, ssl, subprocess

POLL_TIMEOUT = 25  # seconds
API = "https://api.telegram.org/bot{token}/{method}"

def load_env(env_path):
    env = {}
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    k,v = line.split("=",1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    # override by real env if present
    for k in ["TOKEN","CHAT_ID"]:
        if os.getenv(k): env[k]=os.getenv(k)
    return env

def api_call(token, method, data=None):
    url = API.format(token=token, method=method)
    ctx = ssl.create_default_context()
    if data is None:
        with urllib.request.urlopen(url, context=ctx, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    else:
        payload = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))

def send_message(token, chat_id, text):
    return api_call(token, "sendMessage", {"chat_id": chat_id, "text": text})

def send_document(token, chat_id, filename, content_bytes):
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    data = []
    def part(name, value, filename=None, content_type=None):
        data.append(f"--{boundary}\r\n".encode())
        hdr = f'Content-Disposition: form-data; name="{name}"'
        if filename:
            hdr += f'; filename="{filename}"'
        hdr += "\r\n"
        if content_type:
            hdr += f"Content-Type: {content_type}\r\n"
        hdr += "\r\n"
        data.append(hdr.encode())
        if isinstance(value, bytes):
            data.append(value)
        else:
            data.append(str(value).encode())
        data.append(b"\r\n")
    part("chat_id", chat_id)
    part("document", content_bytes, filename=filename, content_type="application/json")
    data.append(f"--{boundary}--\r\n".encode())
    body = b"".join(data)

    url = API.format(token=token, method="sendDocument")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        return json.loads(r.read().decode())

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def gen_uuid():
    return str(uuid.uuid4())

def run_cmd(args):
    try:
        out = subprocess.check_output(args, stderr=subprocess.STDOUT, timeout=8)
        return out.decode().strip()
    except Exception as e:
        return f"error: {e}"

def build_client_config(server_ip, uuid_str, pub_key, short_id, sni_host, flow="xtls-rprx-vision", port=443):
    # Xray VLESS + Reality client config (Linux)
    return {
        "log": {"loglevel":"warning"},
        "inbounds": [{
            "tag": "socks-in",
            "listen": "127.0.0.1",
            "port": 10808,
            "protocol": "socks",
            "settings": {"udp": True, "auth": "noauth"}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": server_ip,
                    "port": port,
                    "users": [{
                        "id": uuid_str,
                        "encryption": "none",
                        "flow": flow
                    }]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": sni_host,
                    "publicKey": pub_key,
                    "shortId": short_id,
                    "fingerprint": "chrome"
                }
            },
            "tag": "proxy"
        }]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="/opt/xvpn/data")
    parser.add_argument("--server-ip", required=True, help="Публичный IP сервера (например 77.110.123.27)")
    parser.add_argument("--sni-host", default="www.cloudflare.com", help="SNI для Reality")
    args = parser.parse_args()

    data_dir = args.data_dir
    ensure_dirs(data_dir)

    env = load_env(os.path.join(data_dir, "server.env"))
    token = env.get("TOKEN", "")
    default_chat = env.get("CHAT_ID", "")
    if not token or not default_chat:
        print("ERROR: TOKEN/CHAT_ID не заданы в /opt/xvpn/data/server.env или окружении", file=sys.stderr)
        sys.exit(1)

    profiles_path = os.path.join(data_dir, "profiles.json")
    meta_path = os.path.join(data_dir, "meta.json")
    profiles = read_json(profiles_path, {})
    meta = read_json(meta_path, {})

    # Загрузим серверные Reality-параметры, которые создал install_server.sh
    server_params_path = os.path.join(data_dir, "reality.json")
    reality = read_json(server_params_path, {})
    pub_key = reality.get("publicKey", "")
    short_id = reality.get("shortId", "")
    if not pub_key or not short_id:
        print("WARNING: reality.json пуст — /get_config не сможет собрать клиентский конфиг", file=sys.stderr)

    offset = 0
    # Инициализация getUpdates: получим last update_id
    try:
        updates = api_call(token, f"getUpdates?timeout=0")
        if updates.get("ok"):
            if updates["result"]:
                offset = updates["result"][-1]["update_id"] + 1
    except Exception as e:
        print(f"init polling failed: {e}", file=sys.stderr)

    send_message(token, default_chat, "Server bot: online ✅")

    while True:
        try:
            updates = api_call(token, f"getUpdates?timeout={POLL_TIMEOUT}&offset={offset}")
            if not updates.get("ok"):
                time.sleep(2); continue
            for upd in updates["result"]:
                offset = max(offset, upd["update_id"] + 1)
                msg = upd.get("message") or {}
                text = (msg.get("text") or "").strip()
                chat_id = str(msg.get("chat",{}).get("id", default_chat))
                if not text: continue

                if text.startswith("/ping"):
                    send_message(token, chat_id, "pong")

                elif text.startswith("/status"):
                    # Простая проверка состояния Xray через systemctl
                    xray = run_cmd(["/bin/systemctl","is-active","xray.service"])
                    send_message(token, chat_id, f"status: bot=ok, xray={xray}")

                elif text.startswith("/register_client"):
                    # создаём профиль
                    cid = gen_uuid()
                    profiles[cid] = {"uuid": cid, "created": int(time.time())}
                    write_json(profiles_path, profiles)
                    send_message(token, chat_id, f"client registered: {cid}")

                elif text.startswith("/get_config"):
                    parts = text.split()
                    if len(parts) == 2:
                        cid = parts[1].strip()
                    else:
                        # берём любой (первый) профиль
                        cid = next(iter(profiles.keys()), None)
                    if not cid or cid not in profiles:
                        send_message(token, chat_id, "нет зарегистрированных клиентов. Используйте /register_client")
                        continue
                    if not pub_key or not short_id:
                        send_message(token, chat_id, "reality параметры не готовы. Проверьте /opt/xvpn/data/reality.json")
                        continue
                    cfg = build_client_config(args.server_ip, profiles[cid]["uuid"], pub_key, short_id, args.sni_host)
                    payload = json.dumps(cfg, ensure_ascii=False, indent=2).encode()
                    send_document(token, chat_id, f"client_{cid}.json", payload)
                else:
                    send_message(token, chat_id, "Команды: /ping, /status, /register_client, /get_config [client_uuid]")

        except Exception as e:
            # не падаем на ошибках сети
            print(f"loop error: {e}", file=sys.stderr)
            time.sleep(2)

if __name__ == "__main__":
    main()
