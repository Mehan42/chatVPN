#!/usr/bin/env python3
"""
XVPN API Gateway
MCP (Management Control Plane) API для XVPN системы
"""

import os
import sys
import json
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Добавляем путь к серверным компонентам
sys.path.append(str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)  # В продакшене настроить более строго

# Заглушка для базы данных
class DatabaseStub:
    def __init__(self):
        self.logs = []
    
    def log_event(self, component, state, action, result):
        log_entry = {
            "timestamp": time.time(),
            "component": component,
            "state": state,
            "action": action,
            "result": result
        }
        self.logs.append(log_entry)

# Глобальный экземпляр базы данных
db = DatabaseStub()

@app.route("/mcp/v1/vpn.health", methods=["GET"])
def health_check():
    """Проверка здоровья VPN"""
    return jsonify({
        "status": "healthy",
        "mask_score": 5,
        "timestamp": time.time(),
        "version": "1.0.0"
    })

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
    
    client_uuid = str(uuid.uuid4())
    
    # Создание заглушечного конфига клиента
    client_config = {
        "uuid": client_uuid,
        "transports": [
            {
                "id": "vless-reality",
                "name": "VLESS + Reality",
                "type": "vless-reality",
                "priority": 1,
                "ipv6": True,
                "need_udp": False,
                "config": {
                    "server": os.getenv("SERVER_IP", "localhost"),
                    "port": 443,
                    "protocol": "tcp"
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
    
    return jsonify({
        "success": True,
        "uuid": client_uuid,
        "config_url": f"/clients/{client_uuid}.json"
    })

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
    app.run(
        host="0.0.0.0",
        port=8443,
        debug=False,
        ssl_context=(
            "/opt/xvpn/tls/cert.pem",  # Путь к SSL сертификату
            "/opt/xvpn/tls/key.pem"    # Путь к приватному ключу
        ) if os.path.exists("/opt/xvpn/tls/cert.pem") else None
    ) if os.getenv("FLASK_ENV") != "development" else app.run(
        host="0.0.0.0",
        port=8443,
        debug=True
    )

if __name__ == "__main__":
    main()