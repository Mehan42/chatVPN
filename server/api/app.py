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
from flask import Flask, jsonify, request
from flask_cors import CORS

# Добавляем путь к серверным компонентам
sys.path.append(str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)  # В продакшене настроить более строго

# Реализация базы данных XVPN
class XVPNDatabase:
    def __init__(self, db_path=None):
        import sqlite3
        self.db_path = db_path or "/opt/xvpn/data/xvpn.db"
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
def get_transport_manifest():
    """Получение манифеста транспортов"""
    # Для тестирования возвращаем заглушку
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
                "config": {
                    "server": "localhost",
                    "port": 443,
                    "protocol": "tcp"
                }
            }
        ]
    }
    return jsonify(manifest)

@app.route("/mcp/v1/admin.newclient", methods=["POST"])
def create_new_client():
    """Создание нового клиента (для администраторов)"""
    import uuid
    
    try:
        client_uuid = str(uuid.uuid4())
        
        # Создание конфига клиента с поддержкой различных транспортов
        client_config = {
            "uuid": client_uuid,
            "created_at": time.time(),
            "transports": [
                {
                    "id": "vless-reality",
                    "name": "VLESS + Reality",
                    "type": "vless-reality",
                    "priority": 1,
                    "ipv6": True,
                    "need_udp": False,
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
                    "config": {
                        "server": os.getenv("SERVER_IP", "77.110.123.27"),
                        "port": 443,
                        "protocol": "ws",
                        "path": f"/v2ray/{client_uuid}",
                        "uuid": client_uuid
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
    # Используем порт 443 для продакшена, если доступен, иначе 8443
    port = int(os.getenv("XVPN_API_PORT", 443 if os.getenv("FLASK_ENV") != "development" else 8443))
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        ssl_context=(
            "/opt/xvpn/tls/cert.pem",  # Путь к SSL сертификату
            "/opt/xvpn/tls/key.pem"    # Путь к приватному ключу
        ) if os.path.exists("/opt/xvpn/tls/cert.pem") else None
    ) if os.getenv("FLASK_ENV") != "development" else app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

if __name__ == "__main__":
    main()