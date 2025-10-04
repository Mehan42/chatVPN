
#!/usr/bin/env python3
"""
Скрипт для запуска тестов при сбоях
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TestRunner:
    """Класс для запуска тестов при сбоях"""
    
    def __init__(self, test_dir: str = "/opt/xvpn/tests"):
        self.test_dir = Path(test_dir)
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def run_network_tests(self) -> Dict[str, Any]:
        """Запуск сетевых тестов"""
        tests = [
            {"name": "connectivity", "command": ["ping", "-c", "4", "8.8.8.8"]},
            {"name": "dns_resolution", "command": ["nslookup", "google.com"]},
            {"name": "port_scan", "command": ["nc", "-zv", "127.0.0.1", "443"]},
            {"name": "api_health", "command": ["curl", "-sk", "https://127.0.0.1:8443/mcp/v1/vpn.health"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except subprocess.TimeoutExpired:
                test_result = {
                    "test_name": test["name"],
                    "status": "timeout",
                    "duration": 30,
                    "output": "",
                    "error": "Test timed out after 30 seconds",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "network",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "timeout_tests": len([r for r in results if r["status"] == "timeout"]),
            "error_tests": len([r for r in results if r["status"] == "error"]),
            "results": results
        }
        
    def run_vpn_tests(self) -> Dict[str, Any]:
        """Запуск VPN тестов"""
        tests = [
            {"name": "vpn_connectivity", "command": ["curl", "-sk", "https://127.0.0.1:8443/transports/manifest.json"]},
            {"name": "vpn_health", "command": ["curl", "-sk", "https://127.0.0.1:8443/mcp/v1/vpn.health"]},
            {"name": "vpn_status", "command": ["systemctl", "status", "xvpn-core"]},
            {"name": "vpn_logs", "command": ["journalctl", "-u", "xvpn-core", "--since", "5 minutes ago", "-n", "20"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "vpn",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    def run_system_tests(self) -> Dict[str, Any]:
        """Запуск системных тестов"""
        tests = [
            {"name": "disk_usage", "command": ["df", "-h"]},
            {"name": "memory_usage", "command": ["free", "-h"]},
            {"name": "cpu_usage", "command": ["top", "-bn1", "|", "head", "-20"]},
            {"name": "processes", "command": ["ps", "aux", "|", "grep", "-E", "(xray|vpn|agent)", "|", "grep", "-v", "grep"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "system",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов"""
        start_time = time.time()
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "total_start_time": start_time,
            "tests": {}
        }
        
        # Запуск сетевых тестов
        all_results["tests"]["network"] = self.run_network_tests()
        
        # Запуск VPN тестов
        all_results["tests"]["vpn"] = self.run_vpn_tests()
        
        # Запуск системных тестов
        all_results["tests"]["system"] = self.run_system_tests()
        
        # Общая статистика
        total_tests = sum([
            len(all_results["tests"][category]["results"])
            for category in all_results["tests"]
        ])
        
        successful_tests = sum([
            len([r for r in all_results["tests"][category]["results"] if r["status"] == "success"])
            for category in all_results["tests"]
        ])
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_duration": time.time() - start_time
        }
        
        # Сохранение результатов
        result_file = self.results_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        return all_results

# Создаем глобальный экземпляр
test_runner = TestRunner()