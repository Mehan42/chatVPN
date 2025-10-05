#!/usr/bin/env python3
"""
XVPN Agent
Компонент для управления локальными службами VPN
"""

import time
import sys
import json
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import psutil
import os

class XVPNAgent:
    """Основной класс агента XVPN"""
    
    def __init__(self):
        self.running = False
        self.log_file = Path("/var/log/xvpn/agent.log")
        self.data_dir = Path("/opt/xvpn/data")
        self.config_file = self.data_dir / "agent_config.json"
        
        # Создаем необходимые директории
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем конфигурацию
        self.config = self._load_config()
        
    def _load_config(self):
        """Загрузка конфигурации агента"""
        default_config = {
            "api_server": "https://api.uss.hopto.org",
            "agent_id": self._get_or_create_agent_id(),
            "check_interval": 30,
            "metrics_collection": True,
            "log_level": "INFO"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Обновляем с дефолтными значениями
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self._log(f"Error loading config, using defaults: {e}", "ERROR")
        
        # Сохраняем конфигурацию
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    def _get_or_create_agent_id(self):
        """Получение или создание ID агента"""
        agent_id_file = self.data_dir / "agent_id"
        
        if agent_id_file.exists():
            with open(agent_id_file, 'r') as f:
                return f.read().strip()
        
        import uuid
        agent_id = str(uuid.uuid4())
        with open(agent_id_file, 'w') as f:
            f.write(agent_id)
        return agent_id
    
    def _log(self, message, level="INFO"):
        """Логирование сообщений"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Пишем в файл
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Пишем в stdout
        print(log_entry.strip())
    
    def collect_metrics(self):
        """Сбор метрик системы"""
        try:
            # Сбор системных метрик
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.config["agent_id"],
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0),
                "process_count": len(psutil.pids()),
                "network_io": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv
                },
                "uptime": time.time() - psutil.boot_time()
            }
            
            # Добавляем информацию о VPN процессах
            vpn_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any('xray' in cmd.lower() for cmd in proc.info['cmdline'] or []):
                        vpn_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cmdline": proc.info['cmdline']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            metrics["vpn_processes"] = vpn_processes
            return metrics
        except Exception as e:
            self._log(f"Error collecting metrics: {e}", "ERROR")
            return None
    
    def send_metrics(self, metrics):
        """Отправка метрик на сервер"""
        try:
            url = f"{self.config['api_server']}/api/v1/metrics"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.get('api_token', '')}"
            }
            response = requests.post(url, json=metrics, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self._log(f"Error sending metrics: {e}", "WARNING")
            return False
    
    def check_xray_status(self):
        """Проверка статуса XRay сервиса"""
        try:
            # Проверяем запущен ли процесс XRay
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any('xray' in cmd.lower() for cmd in proc.info['cmdline'] or []):
                        return {
                            "running": True,
                            "pid": proc.info['pid'],
                            "name": proc.info['name']
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return {"running": False}
        except Exception as e:
            self._log(f"Error checking XRay status: {e}", "ERROR")
            return {"running": False, "error": str(e)}
    
    def start_xray_service(self):
        """Запуск XRay сервиса"""
        try:
            # Проверяем наличие бинарника xray
            if not Path("/usr/bin/xray").exists():
                self._log("XRay binary not found at /usr/bin/xray", "ERROR")
                return False
            
            # Запускаем XRay через системный вызов
            result = subprocess.run(["systemctl", "start", "xray"], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                self._log("XRay service started successfully")
                return True
            else:
                self._log(f"Failed to start XRay: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self._log(f"Error starting XRay service: {e}", "ERROR")
            return False
    
    def stop_xray_service(self):
        """Остановка XRay сервиса"""
        try:
            result = subprocess.run(["systemctl", "stop", "xray"], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                self._log("XRay service stopped successfully")
                return True
            else:
                self._log(f"Failed to stop XRay: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self._log(f"Error stopping XRay service: {e}", "ERROR")
            return False
    
    def agent_loop(self):
        """Основной цикл работы агента"""
        self._log("XVPN Agent started")
        
        while self.running:
            try:
                # Сбор и отправка метрик
                if self.config.get("metrics_collection", True):
                    metrics = self.collect_metrics()
                    if metrics:
                        self.send_metrics(metrics)
                
                # Проверка статуса XRay
                xray_status = self.check_xray_status()
                
                # Логирование статуса XRay
                if not xray_status.get("running"):
                    self._log("XRay service is not running", "WARNING")
                
                # Проверка других задач
                # ... другие проверки
                
                # Засыпаем на заданный интервал
                time.sleep(self.config.get("check_interval", 30))
                
            except Exception as e:
                self._log(f"Error in agent loop: {e}", "ERROR")
                time.sleep(5)  # Небольшая задержка перед продолжением
    
    def start(self):
        """Запуск агента"""
        self.running = True
        self.agent_loop()
    
    def stop(self):
        """Остановка агента"""
        self.running = False
        self._log("XVPN Agent stopped")


def main():
    """Основная функция запуска агента"""
    agent = XVPNAgent()
    
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
        return 0
    except Exception as e:
        print(f"Unexpected error in agent: {e}")
        return 1
    finally:
        agent.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
