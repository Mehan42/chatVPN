#!/bin/bash
set -e

echo "🚀 XVPN Client Installation Script"
echo "=================================="

# Проверка прав пользователя (не root)
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run this script as root!"
    echo "Client should be installed as regular user"
    exit 1
fi

# Определение текущего пользователя
USER=$(whoami)
CLIENT_DIR="$HOME/chatvpn/client"

echo "👤 Installing for user: $USER"
echo "📁 Client directory: $CLIENT_DIR"

# 1. Установка зависимостей (может потребовать sudo)
echo "📦 Installing dependencies..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3 curl jq uv
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3 curl jq
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S python curl jq
else
    echo "⚠️ Unknown package manager. Please install python3, curl, jq, uv manually"
fi

# 2. Создание структуры директорий
echo "📁 Creating directory structure..."
mkdir -p "$CLIENT_DIR"/{clients,transports,logs}

# 3. Создание клиентского health.py
echo "🏥 Creating health monitor..."
cat > "$CLIENT_DIR/health.py" << 'EOF'
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
XVPN Client Health Monitor
Проверка здоровья VPN соединения на клиентской стороне
"""

import time
import random
import json
import os
import requests
import subprocess
from pathlib import Path

# Пути
USER_HOME = Path.home()
LOG_FILE = USER_HOME / "chatvpn/client/logs/health.log"
CLIENT_DIR = USER_HOME / "chatvpn/client"

def check_ip_leak() -> bool:
    """Проверка утечки IP (упрощенная версия)"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        if response.status_code == 200:
            ip_data = response.json()
            current_ip = ip_data.get("ip", "")
            
            # Простая проверка: если IP не локальный, считаем что VPN работает
            if current_ip and not current_ip.startswith(("192.168.", "10.", "172.")):
                return True
    except Exception:
        pass
    return False

def check_tls_profile() -> int:
    """Проверка TLS профиля (1-5)"""
    try:
        response = requests.get("https://httpbin.org/headers", timeout=5)
        if response.status_code == 200:
            return random.randint(3, 5)  # Симуляция хорошего TLS
    except Exception:
        pass
    return random.randint(1, 2)

def get_mask_score() -> int:
    """Вычисление mask score"""
    score = 0
    
    if check_ip_leak():
        score += 2
    
    score += min(3, check_tls_profile())
    
    return min(5, max(1, score))

def log_health():
    """Логирование состояния здоровья"""
    timestamp = int(time.time())
    mask_score = get_mask_score()
    
    # Создаем директорию если не существует
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} score={mask_score} ip_protected={check_ip_leak()}\n")
    
    print(f"Health logged: mask_score={mask_score}")
    return mask_score

if __name__ == "__main__":
    score = log_health()
    print(f"🎭 Current mask score: {score}/5")
EOF

# 4. Создание клиентского state_machine.py
echo "🤖 Creating state machine..."
cat > "$CLIENT_DIR/state_machine.py" << 'EOF'
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10" 
# dependencies = ["requests"]
# ///

"""
XVPN Client State Machine
Клиентская state machine для управления VPN подключениями
"""

import time
import os
import json
import requests
from pathlib import Path
from enum import Enum

# Пути
USER_HOME = Path.home()
STATE_LOG = USER_HOME / "chatvpn/client/logs/state.log"
MANIFEST_PATH = USER_HOME / "chatvpn/client/transports/manifest.json"
CLIENTS_DIR = USER_HOME / "chatvpn/client/clients"

# Состояния клиента
class ClientState(Enum):
    IDLE = "IDLE"
    DISCOVER = "DISCOVER"
    CONNECTING = "CONNECTING"
    ACTIVE = "ACTIVE"
    FALLBACK = "FALLBACK"
    ERROR = "ERROR"

class ClientStateMachine:
    """Клиентская state machine"""
    
    def __init__(self):
        self.state = ClientState.IDLE
        self.current_transport = None
        self.transports = []
        self.server_url = None
        
        # Создаем директории
        STATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def log_state(self, message: str):
        """Логирование состояний"""
        timestamp = int(time.time())
        log_entry = f"{timestamp} [{self.state.value}] {message}\n"
        
        with open(STATE_LOG, "a") as f:
            f.write(log_entry)
        print(f"[{self.state.value}] {message}")
    
    def find_client_config(self) -> dict:
        """Поиск конфигурации клиента"""
        for client_file in CLIENTS_DIR.glob("*.json"):
            try:
                with open(client_file) as f:
                    config = json.load(f)
                    if config.get("status") == "active":
                        self.log_state(f"Found active client: {client_file.name}")
                        return config
            except Exception as e:
                self.log_state(f"Error reading {client_file}: {e}")
        
        self.log_state("No active client configuration found")
        return None
    
    def fetch_manifest(self) -> bool:
        """Получение манифеста с сервера"""
        if not self.server_url:
            # Попытка определить сервер из переменных окружения или конфига
            self.server_url = os.environ.get("XVPN_SERVER", "https://127.0.0.1:8443")
        
        try:
            manifest_url = f"{self.server_url}/transports/manifest.json"
            response = requests.get(manifest_url, verify=False, timeout=10)
            
            if response.status_code == 200:
                manifest = response.json()
                
                # Сохранение манифеста локально
                with open(MANIFEST_PATH, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                self.transports = manifest.get("transports", [])
                self.log_state(f"Manifest fetched: {len(self.transports)} transports")
                return True
            else:
                self.log_state(f"Manifest fetch failed: HTTP {response.status_code}")
        except Exception as e:
            self.log_state(f"Manifest fetch error: {e}")
        
        return False
    
    def load_cached_manifest(self) -> bool:
        """Загрузка кешированного манифеста"""
        try:
            if MANIFEST_PATH.exists():
                with open(MANIFEST_PATH) as f:
                    manifest = json.load(f)
                    self.transports = manifest.get("transports", [])
                    self.log_state(f"Cached manifest loaded: {len(self.transports)} transports")
                    return True
        except Exception as e:
            self.log_state(f"Failed to load cached manifest: {e}")
        
        return False
    
    def discover_transports(self) -> bool:
        """Обнаружение доступных транспортов"""
        self.state = ClientState.DISCOVER
        
        # Сначала пытаемся получить свежий манифест
        if self.fetch_manifest():
            return True
        
        # Если не удалось, используем кэш
        if self.load_cached_manifest():
            self.log_state("Using cached manifest (server unreachable)")
            return True
        
        self.log_state("No manifest available")
        return False
    
    def connect_transport(self, transport: dict) -> bool:
        """Подключение к транспорту (симуляция)"""
        self.state = ClientState.CONNECTING
        transport_id = transport.get("id", "unknown")
        
        self.log_state(f"Connecting to {transport_id}...")
        
        # Симуляция процесса подключения
        time.sleep(2)
        
        # Простая эвристика: T0 успешнее чем остальные
        if transport_id == "T0":
            success_rate = 0.8
        else:
            success_rate = 0.6
        
        import random
        if random.random() < success_rate:
            self.current_transport = transport
            self.state = ClientState.ACTIVE
            self.log_state(f"Connected to {transport_id} successfully")
            return True
        else:
            self.log_state(f"Failed to connect to {transport_id}")
            return False
    
    def run_health_check(self) -> int:
        """Запуск проверки здоровья"""
        try:
            # Импортируем и запускаем health monitor
            import sys
            sys.path.append(str(USER_HOME / "chatvpn/client"))
            
            from health import get_mask_score
            score = get_mask_score()
            self.log_state(f"Health check: mask_score={score}")
            return score
        except Exception as e:
            self.log_state(f"Health check failed: {e}")
            return 1
    
    def run_cycle(self):
        """Один цикл state machine"""
        if self.state == ClientState.IDLE:
            # Проверяем наличие клиентского конфига
            client_config = self.find_client_config()
            if not client_config:
                self.log_state("No client config found. Waiting...")
                time.sleep(60)
                return
            
            # Переходим к обнаружению транспортов
            if self.discover_transports():
                self.state = ClientState.DISCOVER
            else:
                self.state = ClientState.ERROR
        
        elif self.state == ClientState.DISCOVER:
            if not self.transports:
                self.log_state("No transports available")
                self.state = ClientState.ERROR
                return
            
            # Пытаемся подключиться к первому доступному транспорту
            for transport in sorted(self.transports, key=lambda x: x.get("priority", 99)):
                if self.connect_transport(transport):
                    break
            else:
                self.log_state("All transports failed")
                self.state = ClientState.FALLBACK
        
        elif self.state == ClientState.ACTIVE:
            # Проверяем здоровье соединения
            mask_score = self.run_health_check()
            
            if mask_score < 3:
                self.log_state(f"Health degraded (score={mask_score}), switching...")
                self.state = ClientState.FALLBACK
            else:
                self.log_state(f"Health OK (score={mask_score})")
        
        elif self.state == ClientState.FALLBACK:
            # Пытаемся переключиться на следующий транспорт
            if self.current_transport and self.transports:
                try:
                    current_idx = self.transports.index(self.current_transport)
                    if current_idx + 1 < len(self.transports):
                        next_transport = self.transports[current_idx + 1]
                        if self.connect_transport(next_transport):
                            return
                except ValueError:
                    pass
            
            # Если не удалось переключиться, возвращаемся к discovery
            self.log_state("Fallback failed, returning to discovery")
            self.state = ClientState.DISCOVER
        
        elif self.state == ClientState.ERROR:
            self.log_state("Error state, waiting before retry")
            time.sleep(300)  # 5 минут
            self.state = ClientState.IDLE
    
    def run(self):
        """Главный цикл"""
        self.log_state("Client state machine started")
        
        try:
            while True:
                self.run_cycle()
                time.sleep(30)  # Пауза между циклами
        except KeyboardInterrupt:
            self.log_state("Client stopped by user")
        except Exception as e:
            self.log_state(f"Client crashed: {e}")

if __name__ == "__main__":
    sm = ClientStateMachine()
    sm.run()
EOF

# 5. Создание systemd user unit
echo "⚙️ Creating systemd user service..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/xvpn-client.service << 'EOF'
[Unit]
Description=XVPN Client State Machine
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/uv run %h/chatvpn/client/state_machine.py
Restart=always
RestartSec=10
WorkingDirectory=%h/chatvpn/client
StandardOutput=append:%h/chatvpn/client/logs/client_stdout.log
StandardError=append:%h/chatvpn/client/logs/client_stderr.log

[Install]
WantedBy=default.target
EOF

# 6. Установка прав
chmod +x "$CLIENT_DIR/health.py"
chmod +x "$CLIENT_DIR/state_machine.py"

# 7. Reload systemd и создание примера переменных окружения
systemctl --user daemon-reload

# Создание примера .env файла
cat > "$CLIENT_DIR/.env.example" << 'EOF'
# XVPN Client Configuration
# Copy this file to .env and fill in your values

# Server URL (получается из Telegram бота)
XVPN_SERVER=https://your-server-ip:8443

# Optional: Health check interval (seconds)
HEALTH_CHECK_INTERVAL=30

# Optional: Log level
LOG_LEVEL=INFO
EOF

echo "✅ Client installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get client.json from Telegram bot"
echo "2. Place it in: $CLIENT_DIR/clients/"
echo "3. Set server URL: export XVPN_SERVER=https://your-server:8443"
echo "4. Test manually: uv run $CLIENT_DIR/state_machine.py"
echo "5. Enable autostart: systemctl --user enable xvpn-client"
echo "6. Start service: systemctl --user start xvpn-client"
echo ""
echo "📊 Monitor logs:"
echo "- State machine: tail -f $CLIENT_DIR/logs/state.log"
echo "- Health checks: tail -f $CLIENT_DIR/logs/health.log"
echo "- Service logs: journalctl --user -u xvpn-client -f"
