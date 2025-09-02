#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["flask", "pydantic", "uuid"]
# ///

"""
XVPN Control API (MCP Gateway)
Главный API для управления VPN транспортами, клиентами и мониторингом
"""

from flask import Flask, jsonify, request, send_file
import os
import json
import time
import uuid
import sqlite3
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Пути
DB_PATH = "/opt/xvpn/agent/db/agent.db"
MANIFEST_PATH = "/opt/xvpn/core/manifest.json"
CLIENTS_DIR = "/opt/xvpn/core/clients"
LOGS_DIR = "/opt/xvpn/logs"

# Создаем директории если не существуют
os.makedirs(CLIENTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def log_api_event(endpoint, action, result, details=""):
    """Логирование API событий в БД"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs VALUES (?,?,?,?,?,?)",
            (int(time.time()), "api", endpoint, action, result, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log event: {e}")

def get_default_manifest():
    """Дефолтный манифест для транспортов"""
    return {
        "version": "1.0",
        "updated": int(time.time()),
        "transports": [
            {
                "id": "T0",
                "name": "Reality/WS+TLS",
                "type": "xray",
                "priority": 1,
                "config": {
                    "server": "example.com",
                    "port": 443,
                    "protocol": "vless"
                }
            },
            {
                "id": "T1", 
                "name": "WireGuard-over-TLS",
                "type": "wireguard",
                "priority": 2,
                "config": {
                    "server": "wg.example.com",
                    "port": 51820
                }
            }
        ]
    }

@app.route("/")
def index():
    return jsonify({
        "service": "XVPN Control API",
        "version": "1.0",
        "status": "running"
    })

@app.route("/transports/manifest.json")
def manifest():
    """Получение манифеста транспортов"""
    try:
        if os.path.exists(MANIFEST_PATH):
            with open(MANIFEST_PATH) as f:
                manifest_data = json.load(f)
        else:
            # Создаем дефолтный манифест
            manifest_data = get_default_manifest()
            with open(MANIFEST_PATH, 'w') as f:
                json.dump(manifest_data, f, indent=2)
        
        log_api_event("manifest", "fetch", "success")
        return jsonify(manifest_data)
    except Exception as e:
        log_api_event("manifest", "fetch", "error", str(e))
        return jsonify({"error": "manifest not found"}), 404

@app.route("/clients/<client_uuid>.json")
def client_config(client_uuid):
    """Получение конфигурации клиента по UUID"""
    try:
        client_path = os.path.join(CLIENTS_DIR, f"{client_uuid}.json")
        if os.path.exists(client_path):
            with open(client_path) as f:
                client_data = json.load(f)
            log_api_event("client", "fetch", "success", client_uuid)
            return jsonify(client_data)
        else:
            log_api_event("client", "fetch", "not_found", client_uuid)
            return jsonify({"error": "client not found"}), 404
    except Exception as e:
        log_api_event("client", "fetch", "error", f"{client_uuid}: {str(e)}")
        return jsonify({"error": "internal server error"}), 500

@app.route("/mcp/v1/vpn.health")
def vpn_health():
    """Health check VPN сервисов"""
    try:
        # Проверка состояния агента из БД
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT state, result FROM logs WHERE component='agent' ORDER BY ts DESC LIMIT 1"
        )
        last_state = cur.fetchone()
        conn.close()
        
        mask_score = 5  # Базовая оценка
        status = "OK"
        transports_status = {"T0": "active", "T1": "standby"}
        
        if last_state and last_state[1] != "OK":
            mask_score = 3
            status = "WARNING"
        
        result = {
            "mask_score": mask_score,
            "status": status,
            "transports_status": transports_status,
            "timestamp": int(time.time())
        }
        
        log_api_event("health", "check", "success")
        return jsonify(result)
    except Exception as e:
        log_api_event("health", "check", "error", str(e))
        return jsonify({"error": "health check failed"}), 500

@app.route("/mcp/v1/agent.rotate/<client_uuid>", methods=["POST"])
def rotate_client(client_uuid):
    """Ротация учетных данных клиента"""
    try:
        # Генерация новых учетных данных
        new_uuid = str(uuid.uuid4())
        
        client_data = {
            "uuid": new_uuid,
            "created": int(time.time()),
            "parent": client_uuid,
            "status": "active"
        }
        
        # Сохранение нового конфига
        new_client_path = os.path.join(CLIENTS_DIR, f"{new_uuid}.json")
        with open(new_client_path, 'w') as f:
            json.dump(client_data, f, indent=2)
        
        # Деактивация старого
        old_client_path = os.path.join(CLIENTS_DIR, f"{client_uuid}.json")
        if os.path.exists(old_client_path):
            with open(old_client_path) as f:
                old_data = json.load(f)
            old_data["status"] = "rotated"
            old_data["rotated_at"] = int(time.time())
            with open(old_client_path, 'w') as f:
                json.dump(old_data, f, indent=2)
        
        log_api_event("rotate", "success", f"{client_uuid} -> {new_uuid}")
        return jsonify({"new_uuid": new_uuid, "status": "rotated"})
    except Exception as e:
        log_api_event("rotate", "error", str(e), client_uuid)
        return jsonify({"error": "rotation failed"}), 500

@app.route("/mcp/v1/agent.report/<client_uuid>")
def client_report(client_uuid):
    """Получение отчета по клиенту"""
    try:
        since = request.args.get('since', str(int(time.time()) - 86400))  # последние 24ч
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM logs WHERE details LIKE ? AND ts >= ? ORDER BY ts DESC",
            (f"%{client_uuid}%", int(since))
        )
        logs = cur.fetchall()
        conn.close()
        
        report = {
            "client_uuid": client_uuid,
            "period_start": int(since),
            "period_end": int(time.time()),
            "logs_count": len(logs),
            "logs": [
                {
                    "timestamp": log[0],
                    "component": log[1],
                    "state": log[2],
                    "action": log[3],
                    "result": log[4],
                    "details": log[5]
                } for log in logs
            ]
        }
        
        log_api_event("report", "generated", "success", client_uuid)
        return jsonify(report)
    except Exception as e:
        log_api_event("report", "error", str(e), client_uuid)
        return jsonify({"error": "report generation failed"}), 500

@app.route("/mcp/v1/admin.newclient", methods=["POST"])
def new_client():
    """Создание нового клиента (для Telegram бота)"""
    try:
        client_uuid = str(uuid.uuid4())
        
        client_data = {
            "uuid": client_uuid,
            "created": int(time.time()),
            "status": "active",
            "type": "telegram_generated"
        }
        
        client_path = os.path.join(CLIENTS_DIR, f"{client_uuid}.json")
        with open(client_path, 'w') as f:
            json.dump(client_data, f, indent=2)
        
        log_api_event("newclient", "created", "success", client_uuid)
        return jsonify({
            "uuid": client_uuid,
            "status": "created",
            "download_url": f"/clients/{client_uuid}.json"
        })
    except Exception as e:
        log_api_event("newclient", "error", str(e))
        return jsonify({"error": "client creation failed"}), 500

if __name__ == "__main__":
    logger.info("🚀 Starting XVPN Control API")
    
    # Проверка наличия TLS сертификатов
    cert_file = "/opt/xvpn/api/tls/selfsigned.crt"
    key_file = "/opt/xvpn/api/tls/selfsigned.key"
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info("🔐 Starting with HTTPS")
        app.run(
            host="0.0.0.0",
            port=8443,
            ssl_context=(cert_file, key_file),
            debug=False
        )
    else:
        logger.warning("⚠️ Starting with HTTP (no TLS certificates)")
        app.run(host="0.0.0.0", port=8443, debug=False)
