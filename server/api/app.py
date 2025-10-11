#!/usr/bin/env python3
"""
XVPN API Gateway
MCP (Management Control Plane) API для XVPN системы
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Добавляем путь к серверным компонентам
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

# Import authentication module
try:
    # Пробуем относительный импорт
    from .auth import auth_manager, require_auth
except ImportError:
    try:
        # Пробуем абсолютный импорт
        sys.path.append(str(server_root))
        from server.api.auth import auth_manager, require_auth
    except ImportError:
        # Если не удается импортировать, создаем заглушки
        class AuthManager:
            def __init__(self):
                pass
        
        def require_auth(required_permissions=None):
            def decorator(f):
                return f
            return decorator
        
        auth_manager = AuthManager()
        require_auth = require_auth

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # В продакшене настроить более строго

# Глобальный флаг для отключения аутентификации в разработке
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"

# Реализация базы данных XVPN
class XVPNDatabase:
    def __init__(self, db_path=None):
        import sqlite3
        self.db_path = db_path or "/home/uss/chatvpn/server/data/xvpn.db"
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        import sqlite3
        import os
        
        # Создаем директорию если не существует
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицы если не существуют
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                component TEXT,
                state TEXT,
                action TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                uuid TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME,
                config TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transports (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                priority INTEGER,
                config TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_event(self, component, state, action, result):
        """Логирование события в базу данных"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO events (timestamp, component, state, action, result) VALUES (?, ?, ?, ?, ?)",
            (time.time(), component, state, action, result)
        )
        
        conn.commit()
        conn.close()
    
    def add_client(self, client_uuid, config=None):
        """Добавление клиента в базу данных"""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_json = json.dumps(config) if config else None
        cursor.execute(
            "INSERT OR REPLACE INTO clients (uuid, config, last_seen) VALUES (?, ?, ?)",
            (client_uuid, config_json, time.time())
        )
        
        conn.commit()
        conn.close()
    
    def get_client(self, client_uuid):
        """Получение информации о клиенте"""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config, last_seen FROM clients WHERE uuid = ?", (client_uuid,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            config, last_seen = result
            return {
                "config": json.loads(config) if config else None,
                "last_seen": last_seen
            }
        return None
    
    def get_recent_events(self, limit=100):
        """Получение последних событий"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp, component, state, action, result FROM events ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()
        
        conn.close()
        
        events = []
        for row in results:
            events.append({
                "timestamp": row[0],
                "component": row[1],
                "state": row[2],
                "action": row[3],
                "result": row[4]
            })
        
        return events

# Глобальный экземпляр базы данных
db = XVPNDatabase()

@app.route("/mcp/v1/vpn.health", methods=["GET"])
@require_auth(required_permissions=["read"]) if not DISABLE_AUTH else lambda f: f
def health_check():
    """Проверка здоровья VPN"""
    # Логируем событие
    db.log_event("api", "health_check", "get_health_status", "success")
    
    # В реальной системе здесь будет проверка состояния VPN сервисов
    import psutil
    import os
    
    try:
        # Проверяем статус основных сервисов
        services_status = {}
        for service in ["xray", "traefik", "redis"]:
            try:
                result = subprocess.run(["systemctl", "is-active", service], 
                                       capture_output=True, text=True)
                services_status[service] = result.stdout.strip() == "active"
            except:
                services_status[service] = False
        
        # Проверяем системные метрики
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }
        
        # Рассчитываем общий статус
        overall_status = "healthy"
        if not all(services_status.values()) or system_metrics["cpu_percent"] > 90:
            overall_status = "degraded"
        
        response_data = {
            "status": overall_status,
            "mask_score": 5,  # в реальной системе это будет динамическое значение
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": services_status,
            "system_metrics": system_metrics
        }
        
        return jsonify(response_data)
    except Exception as e:
        # Логируем ошибку
        db.log_event("api", "health_check", "get_health_status", f"error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time(),
            "version": "1.0.0"
        }), 500

@app.route("/transports/manifest.json", methods=["GET"])
@require_auth(required_permissions=["read"]) if not DISABLE_AUTH else lambda f: f
def get_transport_manifest():
    """Получение манифеста транспортов"""
    # Возвращаем полный список доступных транспортов
    manifest = {
        "version": 1,
        "transports": [
            {
                "id": "vless-reality",
                "name": "VLESS + Reality",
                "type": "vless-reality",
                "priority": 1,
                "ipv6": True,
                "need_udp": False,
                "ru_traffic": True,  # Поддерживает российский трафик
                "non_ru_traffic": True,  # Поддерживает международный трафик
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 443,
                    "protocol": "tcp"
                }
            },
            {
                "id": "v2ray-websocket",
                "name": "V2Ray WebSocket",
                "type": "v2ray-websocket",
                "priority": 2,
                "ipv6": True,
                "need_udp": False,
                "ru_traffic": False,  # Поддерживает только международный трафик
                "non_ru_traffic": True,
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 443,
                    "protocol": "ws",
                    "path": "/v2ray"
                }
            },
            {
                "id": "wireguard-tls",
                "name": "WireGuard-over-TLS",
                "type": "wireguard-tls",
                "priority": 3,
                "ipv6": True,
                "need_udp": True,
                "ru_traffic": False,
                "non_ru_traffic": True,
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 51820,
                    "protocol": "udp"
                }
            },
            {
                "id": "trojan-tcp",
                "name": "Trojan TCP",
                "type": "trojan-tcp",
                "priority": 4,
                "ipv6": True,
                "need_udp": False,
                "ru_traffic": True,
                "non_ru_traffic": True,
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 443,
                    "protocol": "tcp"
                }
            },
            {
                "id": "shadowsocks-aead",
                "name": "ShadowSocks AEAD",
                "type": "shadowsocks-aead",
                "priority": 5,
                "ipv6": True,
                "need_udp": True,
                "ru_traffic": False,
                "non_ru_traffic": True,
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 8484,
                    "protocol": "udp"
                }
            },
            {
                "id": "hysteria2",
                "name": "Hysteria 2",
                "type": "hysteria2",
                "priority": 6,
                "ipv6": True,
                "need_udp": True,
                "ru_traffic": False,
                "non_ru_traffic": True,
                "config": {
                    "server": os.getenv("SERVER_IP", "77.110.123.27"),
                    "port": 2096,
                    "protocol": "udp"
                }
            }
        ]
    }
    return jsonify(manifest)

@app.route("/mcp/v1/admin.newclient", methods=["POST"])
@require_auth(required_permissions=["admin", "write"])
def create_new_client():
    """Создание нового клиента (для администраторов)"""
    import uuid
    
    try:
        client_uuid = str(uuid.uuid4())
        
        # Создание конфига клиента с полной системой транспортов и маршрутизацией
        client_config = {
            "uuid": client_uuid,
            "created_at": time.time(),
            "routing": {
                # Правила маршрутизации трафика
                "rules": {
                    # Трафик внутри России направляем через транспорты с ru_traffic: True
                    "ru_traffic_transport": ["vless-reality", "trojan-tcp"],
                    # Международный трафик направляем через все доступные транспорты
                    "non_ru_traffic_transport": ["v2ray-websocket", "hysteria2", "wireguard-tls"],
                    # Резервные транспорты при проблемах с основным
                    "fallback_transports": ["trojan-tcp", "hysteria2", "shadowsocks-aead"]
                }
            },
            "transports": [
                {
                    "id": "vless-reality",
                    "name": "VLESS + Reality",
                    "type": "vless-reality",
                    "priority": 1,
                    "ipv6": True,
                    "need_udp": False,
                    "ru_traffic": True,  # Поддерживает российский трафик
                    "non_ru_traffic": True,  # Поддерживает международный трафик
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 443,
                        "protocol": "tcp",
                        "uuid": client_uuid  # Используем UUID клиента для идентификации
                    }
                },
                {
                    "id": "v2ray-websocket",
                    "name": "V2Ray WebSocket",
                    "type": "v2ray-websocket",
                    "priority": 2,
                    "ipv6": True,
                    "need_udp": False,
                    "ru_traffic": False,  # Для международного трафика
                    "non_ru_traffic": True,
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 443,
                        "protocol": "ws",
                        "path": f"/v2ray/{client_uuid}",
                        "uuid": client_uuid
                    }
                },
                {
                    "id": "wireguard-tls",
                    "name": "WireGuard-over-TLS",
                    "type": "wireguard-tls",
                    "priority": 3,
                    "ipv6": True,
                    "need_udp": True,
                    "ru_traffic": False,
                    "non_ru_traffic": True,
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 51820,
                        "protocol": "udp",
                        "public_key": "PLACEHOLDER_PUBLIC_KEY",  # В реальной системе будет сгенерирован
                        "uuid": client_uuid
                    }
                },
                {
                    "id": "trojan-tcp",
                    "name": "Trojan TCP",
                    "type": "trojan-tcp",
                    "priority": 4,
                    "ipv6": True,
                    "need_udp": False,
                    "ru_traffic": True,
                    "non_ru_traffic": True,
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 443,
                        "protocol": "tcp",
                        "password": client_uuid,  # Используем UUID как пароль
                        "sni": os.getenv("SERVER_NAME", "77.110.123.27")
                    }
                },
                {
                    "id": "shadowsocks-aead",
                    "name": "ShadowSocks AEAD",
                    "type": "shadowsocks-aead",
                    "priority": 5,
                    "ipv6": True,
                    "need_udp": True,
                    "ru_traffic": False,
                    "non_ru_traffic": True,
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 8484,
                        "protocol": "udp",
                        "method": "2022-blake3-aes-256-gcm",
                        "password": client_uuid  # Используем UUID как пароль
                    }
                },
                {
                    "id": "hysteria2",
                    "name": "Hysteria 2",
                    "type": "hysteria2",
                    "priority": 6,
                    "ipv6": True,
                    "need_udp": True,
                    "ru_traffic": False,
                    "non_ru_traffic": True,
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 2096,
                        "protocol": "udp",
                        "password": client_uuid,  # Используем UUID как пароль
                        "sni": os.getenv("SERVER_NAME", "77.110.123.27")
                    }
                }
            ]
        }
        
        # Сохранение конфига
        clients_dir = Path("/opt/xvpn/data/clients") / client_uuid
        clients_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = clients_dir / "client.json"
        with open(config_file, "w") as f:
            json.dump(client_config, f, indent=2)
        
        # Добавляем клиента в базу данных
        db.add_client(client_uuid, client_config)
        
        # Логируем создание клиента
        db.log_event("api", "admin", "create_client", f"success - uuid: {client_uuid}")
        
        return jsonify({
            "success": True,
            "uuid": client_uuid,
            "config_url": f"/clients/{client_uuid}.json",
            "created_at": client_config["created_at"]
        })
    except Exception as e:
        # Логируем ошибку
        db.log_event("api", "admin", "create_client", f"error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/clients/<uuid>.json", methods=["GET"])
@require_auth(required_permissions=["read"]) if not DISABLE_AUTH else lambda f: f
def get_client_config(uuid):
    """Получение конфигурации клиента"""
    config_file = Path("/opt/xvpn/data/clients") / uuid / "client.json"
    
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
        return jsonify(config)
    else:
        return jsonify({"error": "Client not found"}), 404

def main():
    """Основная функция запуска API сервера"""
    # Используем порт 8443 для HTTPS в разработке, 443 для продакшена
    port = int(os.getenv("XVPN_API_PORT", 443 if os.getenv("FLASK_ENV") == "production" else 8443))
    
    # Определяем пути к TLS сертификатам
    cert_paths = [
        "/opt/xvpn/tls/cert.pem",           # Продакшен путь
        "/home/uss/chatvpn/security/tls/cert.pem",  # Разработка путь
        "./security/tls/cert.pem"           # Локальный путь
    ]
    
    ssl_context = None
    for cert_path in cert_paths:
        key_path = cert_path.replace("cert.pem", "key.pem")
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = (cert_path, key_path)
            print(f"🔒 Using TLS certificates from: {cert_path}")
            break
    
    # Запуск сервера с HTTPS если есть сертификаты, иначе HTTP
    if ssl_context and os.getenv("FLASK_ENV") != "development":
        print(f"🚀 Starting HTTPS server on port {port}")
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            ssl_context=ssl_context
        )
    else:
        print(f"🚀 Starting HTTP server on port {port} (development mode)")
        app.run(
            host="0.0.0.0",
            port=port,
            debug=True
        )

if __name__ == "__main__":
    main()