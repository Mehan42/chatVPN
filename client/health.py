#!/usr/bin/env python3
# XVPN Health Monitoring Module
# Абсолютный путь: ~/chatvpn/client/health.py

import os
import json
import time
import requests
import subprocess
import socket
import ssl
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

LOG_DIR = os.path.expanduser("~/chatvpn/client/logs")
LOG_FILE = os.path.join(LOG_DIR, "health.log")

# Создаем директорию для логов
os.makedirs(LOG_DIR, exist_ok=True)

class HealthMonitor:
    """Класс для мониторинга здоровья и оценки маскировки VPN"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10
        self.last_score = 0
        self.last_check = None
        
        # Конфигурация проверок
        self.config = {
            "external_ip_services": [
                "https://api.ipify.org",
                "https://httpbin.org/ip",
                "https://ifconfig.me/ip"
            ],
            "tls_test_services": [
                "https://www.google.com",
                "https://www.cloudflare.com",
                "https://www.github.com"
            ],
            "port_scan_targets": ["8.8.8.8:53", "1.1.1.1:53"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Инициализируем логирование
        self._init_logging()
    
    def _init_logging(self):
        """Инициализация логирования"""
        self.log("Health Monitor initialized")
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование сообщений"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        
        # Запись в файл
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        print(f"[{timestamp}] {level}: {message}")
    
    def get_external_ip(self) -> Optional[str]:
        """Получение внешнего IPv4 адреса через несколько сервисов"""
        for service in self.config["external_ip_services"]:
            try:
                response = self.session.get(service, headers={"User-Agent": self.config["user_agent"]})
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip) and self._is_ipv4(ip):
                        self.log(f"External IPv4 detected: {ip} via {service}")
                        return ip
            except Exception as e:
                self.log(f"Failed to get IPv4 from {service}: {e}", "WARNING")
        
        self.log("Failed to get external IPv4", "ERROR")
        return None
    
    def get_external_ipv6(self) -> Optional[str]:
        """Получение внешнего IPv6 адреса через несколько сервисов"""
        ipv6_services = [
            "https://api6.ipify.org",
            "https://ifconfig.co/ip",
            "https://icanhazip.com"
        ]
        
        for service in ipv6_services:
            try:
                response = self.session.get(service, headers={"User-Agent": self.config["user_agent"]})
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip) and self._is_ipv6(ip):
                        self.log(f"External IPv6 detected: {ip} via {service}")
                        return ip
            except Exception as e:
                self.log(f"Failed to get IPv6 from {service}: {e}", "WARNING")
        
        self.log("Failed to get external IPv6", "ERROR")
        return None
    
    def get_external_ips(self) -> Dict[str, str]:
        """Получение всех внешних IP адресов (IPv4 и IPv6)"""
        ips = {
            "ipv4": self.get_external_ip(),
            "ipv6": self.get_external_ipv6(),
            "dual_stack": False
        }
        
        # Проверка dual stack
        if ips["ipv4"] and ips["ipv6"]:
            ips["dual_stack"] = True
        
        return ips
    
    def get_local_ip(self) -> Optional[str]:
        """Получение локального IPv4 адреса"""
        try:
            # Подключение к внешнему сервису для определения локального IPv4 адреса
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except Exception as e:
            self.log(f"Failed to get local IPv4 IP: {e}", "ERROR")
            return None
    
    def get_local_ipv6(self) -> Optional[str]:
        """Получение локального IPv6 адреса"""
        try:
            # Получение IPv6 адреса через подключение к IPv6 сервису
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect(("2001:4860:4860::8888", 80))
            local_ipv6 = sock.getsockname()[0]
            sock.close()
            return local_ipv6
        except Exception as e:
            self.log(f"Failed to get local IPv6 IP: {e}", "ERROR")
            return None
    
    def get_local_ips(self) -> Dict[str, str]:
        """Получение всех локальных IP адресов (IPv4 и IPv6)"""
        ips = {
            "ipv4": self.get_local_ip(),
            "ipv6": self.get_local_ipv6(),
            "dual_stack": False
        }
        
        # Проверка dual stack
        if ips["ipv4"] and ips["ipv6"]:
            ips["dual_stack"] = True
        
        return ips
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Проверка валидности IP адреса (поддержка IPv4 и IPv6)"""
        try:
            # Проверка IPv4
            socket.inet_aton(ip)
            return True
        except socket.error:
            try:
                # Проверка IPv6
                socket.inet_pton(socket.AF_INET6, ip)
                return True
            except socket.error:
                return False
    
    def _is_ipv4(self, ip: str) -> bool:
        """Проверка, что IP является IPv4"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    def _is_ipv6(self, ip: str) -> bool:
        """Проверка, что IP является IPv6"""
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False
    
    def check_ip_leak(self) -> bool:
                """Проверка утечки IP (сравнение локального и внешнего IP)"""
                self.log("Checking for IP leak...")
                
                local_ips = self.get_local_ips()
                external_ips = self.get_external_ips()
                
                # Проверка IPv4
                ipv4_leak = False
                if local_ips["ipv4"] and external_ips["ipv4"]:
                    ipv4_leak = local_ips["ipv4"] == external_ips["ipv4"]
                    if ipv4_leak:
                        self.log(f"IPv4 LEAK DETECTED! Local: {local_ips['ipv4']}, External: {external_ips['ipv4']}", "CRITICAL")
                
                # Проверка IPv6
                ipv6_leak = False
                if local_ips["ipv6"] and external_ips["ipv6"]:
                    ipv6_leak = local_ips["ipv6"] == external_ips["ipv6"]
                    if ipv6_leak:
                        self.log(f"IPv6 LEAK DETECTED! Local: {local_ips['ipv6']}, External: {external_ips['ipv6']}", "CRITICAL")
                
                # Если есть утечка хотя бы по одной версии IP
                ip_leak = ipv4_leak or ipv6_leak
                
                if not ip_leak:
                    self.log(f"IP leak check passed. IPv4 - Local: {local_ips.get('ipv4')}, External: {external_ips.get('ipv4')}")
                    self.log(f"IPv6 - Local: {local_ips.get('ipv6')}, External: {external_ips.get('ipv6')}")
                
                return ip_leak
    
    def analyze_tls_fingerprint(self, domain: str = "www.google.com") -> Dict[str, Any]:
        """Анализ TLS fingerprint и профиля"""
        self.log(f"Analyzing TLS fingerprint for {domain}...")
        
        try:
            # Создаем SSL контекст
            context = ssl.create_default_context()
            
            # Устанавливаем соединение
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Получаем информацию о сертификате
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # Анализируем параметры
                    analysis = {
                        "domain": domain,
                        "tls_version": version,
                        "cipher": cipher[0] if cipher and len(cipher) > 0 else "Unknown",
                        "cipher_strength": cipher[1] if cipher and len(cipher) > 1 else 0,
                        "issuer": cert.get("issuer", [("", "")])[0][1] if cert.get("issuer") else "Unknown",
                        "subject": cert.get("subject", [("", "")])[0][1] if cert.get("subject") else "Unknown",
                        "not_after": cert.get("notAfter"),
                        "san": cert.get("subjectAltName", []),
                        "analysis_result": "secure",
                        "score": 5
                    }
                    
                    # Оценка безопасности
                    score = 5
                    issues = []
                    
                    # Проверка версии TLS
                    if version not in ["TLSv1.2", "TLSv1.3"]:
                        score -= 2
                        issues.append(f"Weak TLS version: {version}")
                    
                    # Проверка strength cipher
                    if cipher and cipher[1] < 128:
                        score -= 1
                        issues.append(f"Weak cipher strength: {cipher[1]}")
                    
                    # Проверка issuer
                    if "Let's Encrypt" not in analysis["issuer"]:
                        score -= 1
                        issues.append(f"Unusual issuer: {analysis['issuer']}")
                    
                    analysis["score"] = max(0, score)
                    analysis["issues"] = issues
                    analysis["analysis_result"] = "secure" if score >= 3 else "warning" if score >= 1 else "critical"
                    
                    self.log(f"TLS analysis result: {analysis['analysis_result']} (Score: {analysis['score']})")
                    if issues:
                        self.log(f"Issues found: {', '.join(issues)}", "WARNING")
                    
                    return analysis
                    
        except Exception as e:
            self.log(f"TLS analysis failed: {e}", "ERROR")
            return {
                "domain": domain,
                "analysis_result": "error",
                "error": str(e),
                "score": 0
            }
    
    def check_connectivity(self) -> Dict[str, Any]:
        """Проверка сетевой connectivity"""
        self.log("Checking network connectivity...")
        
        results = {
            "dns_resolved": False,
            "tcp_connectivity": False,
            "http_connectivity": False,
            "latency_ms": None
        }
        
        # Проверка DNS
        try:
            start_time = time.time()
            socket.gethostbyname("www.google.com")
            results["dns_resolved"] = True
            results["latency_ms"] = int((time.time() - start_time) * 1000)
        except Exception as e:
            self.log(f"DNS resolution failed: {e}", "WARNING")
        
        # Проверка TCP connectivity
        for target in self.config["port_scan_targets"]:
            try:
                host, port = target.split(":")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                if result == 0:
                    results["tcp_connectivity"] = True
                    break
            except Exception as e:
                self.log(f"TCP check to {target} failed: {e}", "DEBUG")
        
        # Проверка HTTP connectivity
        try:
            response = self.session.get("https://www.google.com", timeout=10)
            if response.status_code == 200:
                results["http_connectivity"] = True
        except Exception as e:
            self.log(f"HTTP connectivity check failed: {e}", "WARNING")
        
        self.log(f"Connectivity check: DNS={results['dns_resolved']}, "
                f"TCP={results['tcp_connectivity']}, HTTP={results['http_connectivity']}")
        
        return results
    
    def calculate_mask_score(self) -> int:
        """Расчет оценки маскировки (0-5)"""
        self.log("Calculating mask score...")
        
        score = 5  # Начинаем с максимального балла
        deductions = []
        
        # 1. Проверка утечки IP
        if self.check_ip_leak():
            score -= 3
            deductions.append("IP leak detected")
        
        # 2. Анализ TLS fingerprint
        tls_analysis = self.analyze_tls_fingerprint()
        tls_deduction = 5 - tls_analysis["score"]
        score -= tls_deduction
        if tls_deduction > 0:
            deductions.append(f"Weak TLS profile: {tls_analysis['analysis_result']}")
        
        # 3. Проверка connectivity
        connectivity = self.check_connectivity()
        if not connectivity["dns_resolved"]:
            score -= 1
            deductions.append("DNS resolution failed")
        if not connectivity["tcp_connectivity"]:
            score -= 1
            deductions.append("TCP connectivity issues")
        
        # 4. Дополнительные проверки
        # Проверка на использование стандартных портов VPN
        vpn_ports = [1194, 1195, 1196, 1197, 1198, 8080, 8443]
        if self._is_vpn_port_exposed(vpn_ports):
            score -= 2
            deductions.append("VPN port exposure detected")
        
        # Ограничение диапазона оценки
        score = max(0, min(5, score))
        
        # Сохраняем результат
        self.last_score = score
        self.last_check = datetime.now()
        
        # Логируем результат
        self.log(f"Mask score calculated: {score}/5")
        if deductions:
            self.log(f"Deductions applied: {', '.join(deductions)}", "WARNING")
        
        return score
    
    def _is_vpn_port_exposed(self, ports: list) -> bool:
        """Проверка на открытые VPN порты"""
        # Это упрощенная проверка - в реальности нужно более сложное сканирование
        for port in ports[:3]:  # Проверяем первые 3 порта для экономии времени
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(("127.0.0.1", port))
                sock.close()
                if result == 0:
                    return True
            except:
                continue
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение полного статуса здоровья"""
        self.log("Getting comprehensive health status...")
        
        mask_score = self.calculate_mask_score()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "mask_score": mask_score,
            "status": "excellent" if mask_score >= 4 else 
                     "good" if mask_score >= 3 else 
                     "warning" if mask_score >= 1 else 
                     "critical",
            "ip_leak": self.check_ip_leak(),
            "tls_analysis": self.analyze_tls_fingerprint(),
            "connectivity": self.check_connectivity(),
            "last_check": self.last_check.isoformat() if self.last_check else None
        }
        
        self.log(f"Health status: {status['status']} (Score: {mask_score})")
        return status
    
    def get_mask_score_simple(self) -> int:
        """Упрощенный API для получения оценки маскировки"""
        return self.calculate_mask_score()

# Глобальный экземпляр для использования в GUI
health_monitor = HealthMonitor()

def get_mask_score() -> int:
    """Упрощенная функция для интеграции с GUI"""
    return health_monitor.get_mask_score_simple()

def get_network_info() -> Dict[str, Any]:
    """Получение информации о сети с поддержкой IPv6"""
    monitor = HealthMonitor()
    
    try:
        # Получаем все IP адреса
        local_ips = monitor.get_local_ips()
        external_ips = monitor.get_external_ips()
        
        network_info = {
            "local_ips": local_ips,
            "external_ips": external_ips,
            "ip_leak": monitor.check_ip_leak(),
            "connectivity": monitor.check_connectivity(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверка VPN активности для IPv4 и IPv6
        vpn_ipv4_active = None
        vpn_ipv6_active = None
        
        if local_ips["ipv4"] and external_ips["ipv4"]:
            vpn_ipv4_active = local_ips["ipv4"] != external_ips["ipv4"]
        
        if local_ips["ipv6"] and external_ips["ipv6"]:
            vpn_ipv6_active = local_ips["ipv6"] != external_ips["ipv6"]
        
        network_info["vpn_ipv4_active"] = vpn_ipv4_active
        network_info["vpn_ipv6_active"] = vpn_ipv6_active
        network_info["vpn_active"] = vpn_ipv4_active or vpn_ipv6_active
        network_info["dual_stack"] = local_ips["dual_stack"] and external_ips["dual_stack"]
        
        return network_info
        
    except Exception as e:
        print(f"Error getting network info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_ipv6_info() -> Dict[str, Any]:
    """Получение информации о IPv6 сети"""
    monitor = HealthMonitor()
    
    try:
        local_ips = monitor.get_local_ips()
        external_ips = monitor.get_external_ips()
        
        ipv6_info = {
            "local_ipv6": local_ips["ipv6"],
            "external_ipv6": external_ips["ipv6"],
            "ipv6_leak": False,
            "ipv6_connectivity": False,
            "dual_stack_support": local_ips["dual_stack"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверка IPv6 утечки
        if local_ips["ipv6"] and external_ips["ipv6"]:
            ipv6_info["ipv6_leak"] = local_ips["ipv6"] == external_ips["ipv6"]
        
        # Проверка IPv6 connectivity
        try:
            # Проверка IPv6 DNS
            socket.getaddrinfo("www.google.com", 80, socket.AF_INET6)
            ipv6_info["ipv6_connectivity"] = True
        except:
            pass
        
        return ipv6_info
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Тестирование модуля
    print("Testing XVPN Health Monitor...")
    
    monitor = HealthMonitor()
    
    print(f"Mask Score: {monitor.get_mask_score()}")
    print(f"Health Status: {monitor.get_health_status()}")
