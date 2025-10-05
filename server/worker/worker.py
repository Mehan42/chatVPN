#!/usr/bin/env python3
"""
XVPN Worker
Фоновый воркер для выполнения задач по расписанию и обработке событий
"""

import time
import sys
import json
import requests
import threading
import subprocess
import queue
from pathlib import Path
from datetime import datetime
import schedule
import psutil
import os

class XVPNWorker:
    """Основной класс воркера XVPN"""
    
    def __init__(self):
        self.running = False
        self.log_file = Path("/var/log/xvpn/worker.log")
        self.data_dir = Path("/opt/xvpn/data")
        self.task_queue = queue.Queue()
        self.api_server = "https://api.uss.hopto.org"
        
        # Создаем необходимые директории
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Файлы данных
        self.clients_file = self.data_dir / "clients.json"
        self.tasks_file = self.data_dir / "tasks.json"
        
        # Загружаем задачи
        self.tasks = self._load_tasks()
        
        # Рабочие потоки
        self.worker_threads = []
    
    def _load_tasks(self):
        """Загрузка задач воркера"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"Error loading tasks: {e}", "ERROR")
        
        # Создаем стандартный набор задач
        default_tasks = {
            "health_check": {
                "enabled": True,
                "interval": 300,  # 5 минут
                "last_run": 0
            },
            "metrics_collection": {
                "enabled": True,
                "interval": 60,  # 1 минута
                "last_run": 0
            },
            "config_sync": {
                "enabled": True,
                "interval": 3600,  # 1 час
                "last_run": 0
            },
            "log_rotation": {
                "enabled": True,
                "interval": 86400,  # 24 часа
                "last_run": 0
            }
        }
        
        with open(self.tasks_file, 'w') as f:
            json.dump(default_tasks, f, indent=2)
        return default_tasks
    
    def _log(self, message, level="INFO"):
        """Логирование сообщений"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Пишем в файл
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Пишем в stdout
        print(log_entry.strip())
    
    def health_check(self):
        """Проверка здоровья системы"""
        try:
            self._log("Running health check...")
            
            # Проверка основных сервисов
            services_status = self._check_services()
            
            # Проверка сетевой доступности
            network_status = self._check_network()
            
            # Проверка нагрузки на систему
            system_load = self._check_system_load()
            
            # Отчет о здоровье
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "services": services_status,
                "network": network_status,
                "system_load": system_load
            }
            
            # Отправка отчета на сервер
            self._send_health_report(health_report)
            
            self._log("Health check completed")
            return True
            
        except Exception as e:
            self._log(f"Error in health check: {e}", "ERROR")
            return False
    
    def _check_services(self):
        """Проверка статуса сервисов"""
        services = {
            "xray": False,
            "traefik": False,
            "redis": False,
            "postgresql": False
        }
        
        for service in services.keys():
            try:
                result = subprocess.run(["systemctl", "is-active", service], 
                                       capture_output=True, text=True)
                services[service] = result.stdout.strip() == "active"
            except Exception:
                services[service] = False
        
        return services
    
    def _check_network(self):
        """Проверка сетевой доступности"""
        try:
            # Проверка доступности основных хостов
            import socket
            
            test_hosts = [
                ("8.8.8.8", 53),      # Google DNS
                ("1.1.1.1", 53),      # Cloudflare DNS
                (self.api_server.replace("https://", "").split("/")[0], 443)  # API сервер
            ]
            
            network_status = {}
            for host, port in test_hosts:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    network_status[f"{host}:{port}"] = result == 0
                    sock.close()
                except Exception:
                    network_status[f"{host}:{port}"] = False
            
            return network_status
        except Exception as e:
            self._log(f"Error in network check: {e}", "ERROR")
            return {}
    
    def _check_system_load(self):
        """Проверка нагрузки на систему"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            self._log(f"Error in system load check: {e}", "ERROR")
            return {}
    
    def _send_health_report(self, report):
        """Отправка отчета о здоровье на сервер"""
        try:
            url = f"{self.api_server}/api/v1/health/report"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=report, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self._log(f"Error sending health report: {e}", "WARNING")
            return False
    
    def metrics_collection(self):
        """Сбор метрик системы"""
        try:
            self._log("Collecting metrics...")
            
            # Сбор детальных метрик
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
                },
                "memory": {
                    "percent": psutil.virtual_memory().percent,
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used
                },
                "disk": {
                    "percent": psutil.disk_usage('/').percent,
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                    "packets_sent": psutil.net_io_counters().packets_sent,
                    "packets_recv": psutil.net_io_counters().packets_recv
                },
                "processes": len(psutil.pids()),
                "uptime": time.time() - psutil.boot_time()
            }
            
            # Добавляем метрики VPN-сервисов
            vpn_metrics = self._collect_vpn_metrics()
            metrics["vpn"] = vpn_metrics
            
            # Отправка метрик
            self._send_metrics(metrics)
            
            self._log("Metrics collection completed")
            return True
            
        except Exception as e:
            self._log(f"Error in metrics collection: {e}", "ERROR")
            return False
    
    def _collect_vpn_metrics(self):
        """Сбор метрик VPN-сервисов"""
        try:
            vpn_metrics = {
                "xray": {"running": False, "connections": 0},
                "connections": []
            }
            
            # Проверяем запущенные процессы XRay
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    if 'xray' in proc.info['name'].lower():
                        vpn_metrics["xray"]["running"] = True
                        conns = proc.info['connections']
                        vpn_metrics["xray"]["connections"] = len(conns) if conns else 0
                        if conns:
                            for conn in conns:
                                vpn_metrics["connections"].append({
                                    "pid": proc.info['pid'],
                                    "laddr": str(conn.laddr) if conn.laddr else "N/A",
                                    "raddr": str(conn.raddr) if conn.raddr else "N/A",
                                    "status": conn.status
                                })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return vpn_metrics
        except Exception as e:
            self._log(f"Error collecting VPN metrics: {e}", "ERROR")
            return {}
    
    def _send_metrics(self, metrics):
        """Отправка метрик на сервер"""
        try:
            url = f"{self.api_server}/api/v1/metrics"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=metrics, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self._log(f"Error sending metrics: {e}", "WARNING")
            return False
    
    def config_sync(self):
        """Синхронизация конфигураций"""
        try:
            self._log("Syncing configurations...")
            
            # Получаем обновленные конфигурации с сервера
            clients_config = self._fetch_clients_config()
            
            if clients_config:
                # Сохраняем конфигурации
                with open(self.clients_file, 'w') as f:
                    json.dump(clients_config, f, indent=2)
                
                # Применяем обновления конфигураций
                self._apply_config_updates(clients_config)
            
            self._log("Configuration sync completed")
            return True
            
        except Exception as e:
            self._log(f"Error in config sync: {e}", "ERROR")
            return False
    
    def _fetch_clients_config(self):
        """Получение конфигураций клиентов с сервера"""
        try:
            url = f"{self.api_server}/api/v1/config/clients"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            self._log(f"Error fetching client configs: {e}", "ERROR")
            return {}
    
    def _apply_config_updates(self, configs):
        """Применение обновлений конфигураций"""
        try:
            # Применяем конфигурации к локальным сервисам
            for client_uuid, config in configs.items():
                # В реальной системе здесь будет логика обновления
                # конфигурации для конкретного клиента
                pass
            
            # Перезапускаем сервисы если необходимо
            self._restart_services_if_needed()
            
        except Exception as e:
            self._log(f"Error applying config updates: {e}", "ERROR")
    
    def _restart_services_if_needed(self):
        """Перезапуск сервисов при необходимости"""
        try:
            # Проверяем, нужен ли перезапуск XRay
            # В реальной системе будет проверка изменений конфигов
            pass
        except Exception as e:
            self._log(f"Error in service restart check: {e}", "ERROR")
    
    def log_rotation(self):
        """Ротация лог-файлов"""
        try:
            self._log("Performing log rotation...")
            
            import shutil
            from datetime import datetime
            
            # Создаем резервную копию лога
            log_backup = self.log_file.with_suffix(f".log.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if self.log_file.exists() and self.log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                shutil.copy2(self.log_file, log_backup)
                # Очищаем текущий лог
                self.log_file.write_text("")
            
            self._log("Log rotation completed")
            return True
            
        except Exception as e:
            self._log(f"Error in log rotation: {e}", "ERROR")
            return False
    
    def task_scheduler(self):
        """Планировщик задач"""
        while self.running:
            try:
                current_time = time.time()
                
                # Проверка задач по расписанию
                for task_name, task_config in self.tasks.items():
                    if task_config.get("enabled", False):
                        last_run = task_config.get("last_run", 0)
                        interval = task_config.get("interval", 300)
                        
                        if current_time - last_run >= interval:
                            # Запускаем задачу в отдельном потоке
                            task_thread = threading.Thread(
                                target=self._execute_task,
                                args=(task_name,),
                                daemon=True
                            )
                            task_thread.start()
                            
                            # Обновляем время последнего запуска
                            self.tasks[task_name]["last_run"] = current_time
                            # Сохраняем обновленные задачи
                            with open(self.tasks_file, 'w') as f:
                                json.dump(self.tasks, f, indent=2)
                
                # Засыпаем перед следующей проверкой
                time.sleep(10)
                
            except Exception as e:
                self._log(f"Error in task scheduler: {e}", "ERROR")
                time.sleep(5)
    
    def _execute_task(self, task_name):
        """Выполнение задачи по имени"""
        try:
            task_functions = {
                "health_check": self.health_check,
                "metrics_collection": self.metrics_collection,
                "config_sync": self.config_sync,
                "log_rotation": self.log_rotation
            }
            
            if task_name in task_functions:
                self._log(f"Executing task: {task_name}")
                result = task_functions[task_name]()
                if result:
                    self._log(f"Task {task_name} completed successfully")
                else:
                    self._log(f"Task {task_name} failed", "ERROR")
            else:
                self._log(f"Unknown task: {task_name}", "ERROR")
                
        except Exception as e:
            self._log(f"Error executing task {task_name}: {e}", "ERROR")
    
    def start(self):
        """Запуск воркера"""
        self._log("XVPN Worker started")
        self.running = True
        
        # Запускаем планировщик задач в отдельном потоке
        scheduler_thread = threading.Thread(target=self.task_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.worker_threads.append(scheduler_thread)
        
        # Основной цикл воркера
        try:
            while self.running:
                # Проверяем задачи в очереди
                try:
                    task = self.task_queue.get(timeout=1)
                    # В реальной системе обрабатываем задачи из очереди
                    # Пока что просто возвращаем задачу в очередь
                    self.task_queue.task_done()
                except queue.Empty:
                    continue
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """Остановка воркера"""
        self.running = False
        self._log("XVPN Worker stopped")


def main():
    """Основная функция запуска воркера"""
    worker = XVPNWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
        return 0
    except Exception as e:
        print(f"Unexpected error in worker: {e}")
        return 1
    finally:
        worker.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
