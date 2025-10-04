#!/usr/bin/env python3
"""
Интеграция AI-оркестратора XVPN в систему
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

class OrchestratorIntegrator:
    """Класс для интеграции AI-оркестратора"""
    
    def __init__(self):
        self.project_root = Path("/opt/xvpn")
        self.agent_dir = self.project_root / "agent"
        self.systemd_dir = Path("/etc/systemd/system")
        
    def integrate_all_components(self) -> Dict[str, Any]:
        """Интеграция всех компонентов"""
        results = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "components": {},
            "errors": []
        }
        
        # Копирование файлов
        results["components"]["orchestrator"] = self.copy_orchestrator_files()
        results["components"]["scripts"] = self.copy_scripts()
        results["components"]["config"] = self.copy_config()
        results["components"]["systemd"] = self.setup_systemd()
        
        # Настройка прав
        results["components"]["permissions"] = self.setup_permissions()
        
        # Обновление systemd
        results["components"]["systemd_reload"] = self.reload_systemd()
        
        # Запуск сервисов
        results["components"]["services"] = self.start_services()
        
        return results
        
    def copy_orchestrator_files(self) -> Dict[str, Any]:
        """Копирование файлов оркестратора"""
        results = {"status": "success", "copied_files": [], "errors": []}
        
        try:
            # Копирование основного файла
            source = Path(__file__).parent.parent / "orchestrator.py"
            dest = self.agent_dir / "orchestrator.py"
            
            shutil.copy2(source, dest)
            results["copied_files"].append(str(dest))
            
            # Копирование конфигурации
            source_config = Path(__file__).parent.parent / "orchestrator_config.json"
            dest_config = self.agent_dir / "orchestrator_config.json"
            
            shutil.copy2(source_config, dest_config)
            results["copied_files"].append(str(dest_config))
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def copy_scripts(self) -> Dict[str, Any]:
        """Копирование скриптов"""
        results = {"status": "success", "copied_files": [], "errors": []}
        
        try:
            # Копирование скриптов логирования
            scripts_source = Path(__file__).parent
            scripts_dest = self.agent_dir / "scripts"
            
            for script_file in scripts_source.glob("*.py"):
                if script_file.name != "integrate_orchestrator.py":
                    dest = scripts_dest / script_file.name
                    shutil.copy2(script_file, dest)
                    results["copied_files"].append(str(dest))
                    
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def copy_config(self) -> Dict[str, Any]:
        """Копирование конфигурации"""
        results = {"status": "success", "copied_files": [], "errors": []}
        
        try:
            # Создание директорий для логов
            log_dirs = [
                "/var/log/xvpn/orchestration",
                "/var/log/xvpn/agent",
                "/var/log/xvpn/api",
                "/var/log/xvpn/core"
            ]
            
            for log_dir in log_dirs:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
                results["copied_files"].append(f"created: {log_dir}")
                
            # Копирование конфигурационных файлов
            config_source = Path(__file__).parent.parent / "config"
            if config_source.exists():
                for config_file in config_source.glob("*.json"):
                    dest = self.project_root / "config" / config_file.name
                    shutil.copy2(config_file, dest)
                    results["copied_files"].append(str(dest))
                    
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def setup_systemd(self) -> Dict[str, Any]:
        """Настройка systemd"""
        results = {"status": "success", "copied_files": [], "errors": []}
        
        try:
            # Копирование unit-файла
            source = Path(__file__).parent.parent.parent / "systemd" / "xvpn-orchestrator.service"
            dest = self.systemd_dir / "xvpn-orchestrator.service"
            
            shutil.copy2(source, dest)
            results["copied_files"].append(str(dest))
            
            # Копирование других unit-файлов
            for service_file in ["xvpn-api.service", "xvpn-agent.service", "xvpn-core.service"]:
                source = Path(__file__).parent.parent.parent / "systemd" / service_file
                if source.exists():
                    dest = self.systemd_dir / service_file
                    shutil.copy2(source, dest)
                    results["copied_files"].append(str(dest))
                    
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def setup_permissions(self) -> Dict[str, Any]:
        """Настройка прав доступа"""
        results = {"status": "success", "updated_files": [], "errors": []}
        
        try:
            # Установка прав
            files_to_chmod = [
                self.agent_dir / "orchestrator.py",
                self.agent_dir / "scripts" / "*.py",
                "/var/log/xvpn/orchestration",
                "/var/log/xvpn/agent",
                "/var/log/xvpn/api",
                "/var/log/xvpn/core"
            ]
            
            for file_path in files_to_chmod:
                if isinstance(file_path, Path):
                    if file_path.is_file():
                        os.chmod(file_path, 0o755)
                        results["updated_files"].append(f"chmod 755: {file_path}")
                    elif file_path.is_dir():
                        os.chmod(file_path, 0o755)
                        results["updated_files"].append(f"chmod 755: {file_path}")
                else:
                    # Глобальный паттерн
                    for file in Path(file_path.parent).glob(file_path.name):
                        os.chmod(file, 0o755)
                        results["updated_files"].append(f"chmod 755: {file}")
                        
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def reload_systemd(self) -> Dict[str, Any]:
        """Перезагрузка systemd"""
        results = {"status": "success", "reloaded": True, "errors": []}
        
        try:
            subprocess.run(["systemctl", "daemon-reload"], check=True)
        except subprocess.CalledProcessError as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
        
    def start_services(self) -> Dict[str, Any]:
        """Запуск сервисов"""
        results = {"status": "success", "started_services": [], "errors": []}
        
        services = [
            "xvpn-api",
            "xvpn-agent", 
            "xvpn-core",
            "xvpn-orchestrator"
        ]
        
        for service in services:
            try:
                # Включение автозапуска
                subprocess.run(["systemctl", "enable", service], check=True)
                
                # Запуск сервиса
                subprocess.run(["systemctl", "start", service], check=True)
                
                results["started_services"].append(service)
                
            except subprocess.CalledProcessError as e:
                results["status"] = "partial"
                results["errors"].append(f"Ошибка запуска {service}: {e}")
                
        return results
        
    def verify_installation(self) -> Dict[str, Any]:
        """Проверка установки"""
        results = {"status": "success", "verified": [], "errors": []}
        
        # Проверка файлов
        files_to_check = [
            self.agent_dir / "orchestrator.py",
            self.agent_dir / "orchestrator_config.json",
            self.agent_dir / "scripts" / "action_logger.py",
            self.agent_dir / "scripts" / "test_runner.py",
            self.agent_dir / "scripts" / "log_cleaner.py"
        ]
        
        for file_path in files_to_check:
            if file_path.exists():
                results["verified"].append(f"✓ {file_path}")
            else:
                results["errors"].append(f"✗ {file_path} не найден")
                
        # Проверка сервисов
        services = ["xvpn-api", "xvpn-agent", "xvpn-core", "xvpn-orchestrator"]
        
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    results["verified"].append(f"✓ Сервис {service} активен")
                else:
                    results["errors"].append(f"✗ Сервис {service} неактивен")
                    
            except Exception as e:
                results["errors"].append(f"✗ Ошибка проверки {service}: {e}")
                
        # Проверка логов
        log_dirs = [
            "/var/log/xvpn/orchestration",
            "/var/log/xvpn/agent",
            "/var/log/xvpn/api",
            "/var/log/xvpn/core"
        ]
        
        for log_dir in log_dirs:
            if Path(log_dir).exists():
                results["verified"].append(f"✓ Директория логов {log_dir}")
            else:
                results["errors"].append(f"✗ Директория логов {log_dir} не найдена")
                
        # Обновление статуса
        if results["errors"]:
            results["status"] = "partial"
            
        return results

def main():
    """Основная функция"""
    print("Начало интеграции AI-оркестратора XVPN...")
    
    integrator = OrchestratorIntegrator()
    
    try:
        # Интеграция всех компонентов
        results = integrator.integrate_all_components()
        
        print("\n=== РЕЗУЛЬТАТЫ ИНТЕГРАЦИИ ===")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
        # Проверка установки
        verification = integrator.verify_installation()
        
        print("\n=== ПРОВЕРКА УСТАНОВКИ ===")
        print(json.dumps(verification, ensure_ascii=False, indent=2))
        
        # Если есть ошибки, выводим их
        if results["errors"]:
            print("\n=== ОШИБКИ ===")
            for error in results["errors"]:
                print(f"✗ {error}")
                
        if verification["errors"]:
            print("\n=== ОШИБКИ ПРОВЕРКИ ===")
            for error in verification["errors"]:
                print(f"✗ {error}")
                
        print("\nИнтеграция завершена!")
        
    except Exception as e:
        print(f"Критическая ошибка интеграции: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())