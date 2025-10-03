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
import ssl
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Пути - используем относительные пути и домашнюю директорию
import tempfile
from pathlib import Path

# Определяем базовую директорию в домашней папке пользователя или в temp
BASE_DIR = Path.home() / ".xvpn"
if not BASE_DIR.exists():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "agent.db"
MANIFEST_PATH = BASE_DIR / "manifest.json"
CLIENTS_DIR = BASE_DIR / "clients"
LOGS_DIR = BASE_DIR / "logs"

# Создаем директории если не существуют с правильными правами
os.makedirs(CLIENTS_DIR, exist_ok=True, mode=0o755)
os.makedirs(LOGS_DIR, exist_ok=True, mode=0o755)

# Устанавливаем правильные права для файлов
def setup_file_permissions(file_path):
    """Установка правильных прав для файла"""
    if file_path.exists():
        os.chmod(file_path, 0o644)

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

# Создаем базовые файлы, если они не существуют
if not DB_PATH.exists():
    setup_file_permissions(DB_PATH)
if not MANIFEST_PATH.exists():
    manifest_data = get_default_manifest()
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    setup_file_permissions(MANIFEST_PATH)

# Устанавливаем права для директорий
os.chmod(CLIENTS_DIR, 0o755)
os.chmod(LOGS_DIR, 0o755)

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


@app.route("/")
def index():
    return jsonify({
        "service": "XVPN Control API",
        "version": "1.0",
        "status": "running"
    })

@app.route("/api/v1/status")
def api_status():
    """Статус API сервиса"""
    try:
        # Проверка состояния БД
        db_status = "ok"
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.close()
        except:
            db_status = "error"
        
        # Проверка манифеста
        manifest_status = "ok"
        try:
            if not MANIFEST_PATH.exists():
                manifest_status = "missing"
            else:
                with open(MANIFEST_PATH) as f:
                    json.load(f)
        except:
            manifest_status = "error"
        
        # Проверка директории клиентов
        clients_status = "ok"
        try:
            if not CLIENTS_DIR.exists():
                clients_status = "missing"
            else:
                # Проверяем наличие хотя бы одного клиента
                client_files = [f for f in CLIENTS_DIR.glob("*.json")]
                if not client_files:
                    clients_status = "empty"
        except:
            clients_status = "error"
        
        # Общая оценка состояния
        overall_status = "ok"
        if db_status == "error" or manifest_status == "error":
            overall_status = "error"
        elif clients_status == "missing":
            overall_status = "warning"
        
        result = {
            "service": "XVPN Control API",
            "version": "1.0",
            "status": overall_status,
            "timestamp": int(time.time()),
            "components": {
                "database": db_status,
                "manifest": manifest_status,
                "clients": clients_status
            },
            "uptime": int(time.time())  # Простой uptime счетчик
        }
        
        log_api_event("status", "check", "success")
        return jsonify(result)
        
    except Exception as e:
        log_api_event("status", "check", "error", str(e))
        return jsonify({"error": "status check failed", "details": str(e)}), 500

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
    """Получение конфигурации клиента по UUID с автоматическим переключением транспортов"""
    try:
        # Проверяем существование клиента
        client_path = os.path.join(CLIENTS_DIR, f"{client_uuid}.json")
        client_exists = os.path.exists(client_path)
        
        # Загружаем манифест транспортов
        manifest_path = Path.home() / "chatvpn" / "client" / "transports" / "manifest.json"
        if not manifest_path.exists():
            log_api_event("client", "fetch", "manifest_not_found", client_uuid)
            return jsonify({"error": "transport manifest not found"}), 404
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Получаем список доступных транспортов
        transports = manifest_data.get("transports", [])
        
        # Фильтруем активные транспорты
        active_transports = []
        for transport in transports:
            # Проверяем доступность транспорта
            is_available = check_transport_availability(transport)
            if is_available:
                active_transports.append(transport)
        
        # Сортируем по приоритету
        active_transports.sort(key=lambda x: x.get("priority", 999))
        
        if not active_transports:
            log_api_event("client", "fetch", "no_available_transports", client_uuid)
            return jsonify({"error": "no available transports"}), 503
        
        # Формируем конфигурацию клиента
        client_config = {
            "uuid": client_uuid,
            "generated_at": int(time.time()),
            "client_exists": client_exists,
            "available_transports": len(active_transports),
            "selected_transport": active_transports[0],  #首选
            "fallback_transports": active_transports[1:3] if len(active_transports) > 1 else [],
            "auto_fallback_enabled": True,
            "health_check": {
                "enabled": True,
                "interval": 30,
                "timeout": 5,
                "max_failures": 3
            },
            "metadata": {
                "manifest_version": manifest_data.get("version", "1.0"),
                "last_updated": manifest_data.get("last_updated", ""),
                "load_balancing": manifest_data.get("load_balancing", {}),
                "fallback_policy": manifest_data.get("fallback_policy", {})
            }
        }
        
        # Если клиент существует, дополняем его данные
        if client_exists:
            with open(client_path) as f:
                existing_data = json.load(f)
            client_config.update(existing_data)
        
        log_api_event("client", "fetch", "success", client_uuid)
        return jsonify(client_config)
        
    except Exception as e:
        logger.error(f"Error in client_config: {e}")
        log_api_event("client", "fetch", "error", f"{client_uuid}: {str(e)}")
        return jsonify({"error": "internal server error"}), 500

def check_transport_availability(transport):
    """Проверка доступности транспорта"""
    try:
        config = transport.get("config", {})
        host = config.get("server")
        port = config.get("port")
        
        if not host or not port:
            return False
        
        import socket
        
        # Проверка базовой доступности
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        # Для TLS проверяем доступность через HTTPS
        if config.get("tls", {}).get("enabled", False):
            try:
                import ssl
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((host, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        return True
            except:
                return False
        
        return result == 0
        
    except Exception as e:
        logger.debug(f"Transport availability check failed: {e}")
        return False

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

def create_https_context():
    """Создание HTTPS контекста для сервера"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # Настройка безопасности - отключаем проверку клиентских сертификатов для самоподписанных
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_NONE  # Изменено с CERT_REQUIRED на CERT_NONE
    context.check_hostname = False
    
    # Списки безопасных шифров
    context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:'
                       'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
                       'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
                       'AES128-GCM-SHA256:AES256-GCM-SHA384')
    
    # Загрузка сертификатов Let's Encrypt (если доступны)
    cert_file = "/etc/letsencrypt/live/api.uss.hopto.org/fullchain.pem"
    key_file = "/etc/letsencrypt/live/api.uss.hopto.org/privkey.pem"
    
    fallback_cert_file = BASE_DIR / "tls" / "selfsigned.crt"
    fallback_key_file = BASE_DIR / "tls" / "selfsigned.key"
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info("🔐 Using Let's Encrypt certificates")
        context.load_cert_chain(cert_file, key_file)
    elif os.path.exists(fallback_cert_file) and os.path.exists(fallback_key_file):
        logger.info("🔐 Using fallback self-signed certificates")
        context.load_cert_chain(fallback_cert_file, fallback_key_file)
    else:
        logger.warning("⚠️ No certificates found, creating self-signed")
        # Создаем самоподписанный сертификат как запасной вариант
        os.makedirs(BASE_DIR / "tls", exist_ok=True, mode=0o755)
        
        # Генерируем самоподписанный сертификат
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        
        # Создаем приватный ключ
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Создаем самоподписанный сертификат
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Novosibirsk"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Novosibirsk"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "XVPN"),
            x509.NameAttribute(NameOID.COMMON_NAME, "api.uss.hopto.org"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("api.uss.hopto.org")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Сохраняем сертификат и ключ
        with open(fallback_cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(fallback_key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        # Устанавливаем правильные права
        os.chmod(fallback_cert_file, 0o644)
        os.chmod(fallback_key_file, 0o600)
        
        context.load_cert_chain(fallback_cert_file, fallback_key_file)
    
    return context

@app.before_request
def enforce_https():
    """Принудительное использование HTTPS"""
    if not request.is_secure and not app.debug:
        return jsonify({"error": "HTTPS required"}), 403

@app.after_request
def add_security_headers(response):
    """Добавление заголовков безопасности"""
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

if __name__ == "__main__":
    logger.info("🚀 Starting XVPN Control API")
    
    # Создаем HTTPS контекст
    https_context = create_https_context()
    
    logger.info("🔐 Starting with HTTPS")
    app.run(
        host="0.0.0.0",
        port=8443,
        ssl_context=https_context,
        debug=False,
        threaded=True
    )
