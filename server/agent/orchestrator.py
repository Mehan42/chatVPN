#!/usr/bin/env python3
"""
XVPN Orchestrator
Оркестратор для управления всеми компонентами системы
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

class XVPNOrchestrator:
    """Основной класс оркестратора XVPN"""
    
    def __init__(self):
        self.running = False
        self.processes = {}
        self.log_file = Path("/var/log/xvpn/orchestration.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Логирование сообщений"""
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Пишем в файл
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Пишем в stdout
        print(log_entry.strip())
    
    def start_component(self, name, command):
        """Запуск компонента"""
        try:
            self.log(f"Starting component: {name}")
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes[name] = process
            self.log(f"Component {name} started with PID {process.pid}")
            return True
        except Exception as e:
            self.log(f"Failed to start component {name}: {e}", "ERROR")
            return False
    
    def stop_component(self, name):
        """Остановка компонента"""
        if name in self.processes:
            try:
                process = self.processes[name]
                process.terminate()
                process.wait(timeout=5)
                del self.processes[name]
                self.log(f"Component {name} stopped")
                return True
            except Exception as e:
                self.log(f"Failed to stop component {name}: {e}", "ERROR")
                return False
        return True
    
    def check_component_health(self, name):
        """Проверка здоровья компонента"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                return True
            else:
                # Процесс завершен
                stdout, stderr = process.communicate()
                if stderr:
                    self.log(f"Component {name} crashed: {stderr.decode()}", "ERROR")
                return False
        return False
    
    def start_all_components(self):
        """Запуск всех компонентов"""
        components = [
            ("api", "python3 server/api/app.py"),
            ("agent", "python3 server/agent/agent.py"),
            ("bot", "python3 server/admin/tg_bot.py"),
            ("worker", "python3 server/worker/worker.py")
        ]
        
        success = True
        for name, command in components:
            if not self.start_component(name, command):
                success = False
        
        return success
    
    def monitor_components(self):
        """Мониторинг компонентов"""
        while self.running:
            try:
                for name in list(self.processes.keys()):
                    if not self.check_component_health(name):
                        self.log(f"Component {name} is not healthy, restarting...", "WARNING")
                        # Перезапуск компонента
                        # В реальной системе здесь будет более сложная логика
                        
                time.sleep(10)  # Проверяем каждые 10 секунд
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}", "ERROR")
                time.sleep(5)
    
    def start(self):
        """Запуск оркестратора"""
        self.log("Starting XVPN Orchestrator...")
        
        # Запуск всех компонентов
        if not self.start_all_components():
            self.log("Failed to start all components", "ERROR")
            return False
        
        # Установка флага запуска
        self.running = True
        
        # Запуск мониторинга в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_components, daemon=True)
        monitor_thread.start()
        
        self.log("XVPN Orchestrator started successfully")
        return True
    
    def stop(self):
        """Остановка оркестратора"""
        self.log("Stopping XVPN Orchestrator...")
        self.running = False
        
        # Остановка всех компонентов
        for name in list(self.processes.keys()):
            self.stop_component(name)
        
        self.log("XVPN Orchestrator stopped")

def main():
    """Основная функция оркестратора"""
    orchestrator = XVPNOrchestrator()
    
    try:
        if orchestrator.start():
            # Держим оркестратор запущенным
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                orchestrator.log("Received interrupt signal, shutting down...")
        else:
            return 1
    except Exception as e:
        orchestrator.log(f"Unexpected error: {e}", "ERROR")
        return 1
    finally:
        orchestrator.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())