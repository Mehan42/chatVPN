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
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from ipv6_manager import get_ipv6_manager

LOG_DIR = os.path.expanduser("~/chatvpn/client/logs")
LOG_FILE = os.path.join(LOG_DIR, "health.log")
CACHE_DIR = os.path.join(LOG_DIR, "cache")
CACHE_TTL = 300  # 5 минут кэширования

# Создаем директории
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Класс для мониторинга здоровья и оценки маскировки VPN с улучшенной стабильностью"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Добавляем retry стратегию
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.last_score = 0
        self.last_check = None
        self.cache = {}
        self.cache_lock = threading.Lock()
        
        # Конфигурация проверок
        self.config = {
            "external_ip_services": [
                "https://api.ipify.org",
                "https://httpbin.org/ip",
                "https://ifconfig.me/ip",
                "https://icanhazip.com",
                "https://ident.me"
            ],
            "tls_test_services": [
                "https://www.google.com",
                "https://www.cloudflare.com",
                "https://www.github.com",
                "https://www.microsoft.com"
            ],
            "port_scan_targets": ["8.8.8.8:53", "1.1.1.1:53", "208.67.222.222:53"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Инициализируем логирование
        self._init_logging()
        
        # Запускаем очистку кэша в фоновом режиме
        self._start_cache_cleanup()
    
    def _init_logging(self):
        """Инициализация логирования"""
        self.log("Health Monitor initialized")
    
    def _start_cache_cleanup(self):
        """Запуск фонового процесса очистки кэша"""
        def cleanup():
            while True:
                time.sleep(3600)  # Чистка раз в час
                self._cleanup_cache()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_cache(self):
        """Очистка устаревших записей кэша"""
        with self.cache_lock:
            current_time = datetime.now()
            expired_keys = []
            
            for key, (timestamp, _) in self.cache.items():
                if current_time - timestamp > timedelta(seconds=CACHE_TTL):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                logger.debug(f"Cache entry expired: {key}")
            
            if expired_keys:
                logger.info(f"Cache cleanup removed {len(expired_keys)} expired entries")
    
    def _get_cache_key(self, method_name: str, **kwargs) -> str:
        """Генерация ключа для кэширования"""
        import hashlib
        key_data = f"{method_name}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str):
        """Получение данных из кэша"""
        with self.cache_lock:
            if cache_key in self.cache:
                timestamp, data = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return data
                else:
                    del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data):
        """Сохранение данных в кэш"""
        with self.cache_lock:
            self.cache[cache_key] = (datetime.now(), data)
            logger.debug(f"Cache saved for key: {cache_key}")
    
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
        """Получение внешнего IPv4 адреса через несколько сервисов с кэшированием"""
        cache_key = self._get_cache_key("external_ip")
        
        # Попробуем получить из кэша
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        last_error = None
        successful_services = []
        
        for service in self.config["external_ip_services"]:
            try:
                logger.debug(f"Trying to get IPv4 from {service}")
                response = self.session.get(service, timeout=10)
                
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip) and self._is_ipv4(ip):
                        self.log(f"External IPv4 detected: {ip} via {service}")
                        successful_services.append((service, ip))
                        
                        # Сохраняем в кэширование
                        self._save_to_cache(cache_key, ip)
                        return ip
                    else:
                        logger.warning(f"Invalid IPv4 response from {service}: {ip}")
                else:
                    logger.warning(f"HTTP {response.status_code} from {service}")
                    
            except requests.exceptions.Timeout:
                last_error = f"Timeout from {service}"
                logger.debug(f"Timeout getting IPv4 from {service}")
            except requests.exceptions.ConnectionError:
                last_error = f"Connection error from {service}"
                logger.debug(f"Connection error getting IPv4 from {service}")
            except Exception as e:
                last_error = f"Error from {service}: {str(e)}"
                logger.debug(f"Error getting IPv4 from {service}: {e}")
        
        # Если есть успешные сервисы, но что-то пошло не так с последним запросом
        if successful_services:
            last_service, last_ip = successful_services[-1]
            self.log(f"Fallback IPv4 from {last_service}: {last_ip}", "WARNING")
            self._save_to_cache(cache_key, last_ip)
            return last_ip
        
        # Если все провалилось
        if last_error:
            self.log(f"Failed to get external IPv4: {last_error}", "ERROR")
        else:
            self.log("Failed to get external IPv4: All services failed", "ERROR")
        
        return None
    
    def get_external_ipv6(self) -> Optional[str]:
        """Получение внешнего IPv6 адреса через несколько сервисов с использованием IPv6Manager и кэшированием"""
        cache_key = self._get_cache_key("external_ipv6")
        
        # Попробуем получить из кэша
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Сначала пробуем IPv6Manager
        try:
            ipv6_manager = get_ipv6_manager()
            ipv6_result = ipv6_manager.get_external_ipv6()
            if ipv6_result:
                self.log(f"External IPv6 detected via IPv6Manager: {ipv6_result}")
                self._save_to_cache(cache_key, ipv6_result)
                return ipv6_result
        except Exception as e:
            logger.debug(f"IPv6Manager error: {e}")
            
        # Fallback ручная проверка
        ipv6_services = [
            "https://api6.ipify.org",
            "https://ifconfig.co/ip",
            "https://icanhazip.com",
            "https://v6.ident.me"
        ]
        
        last_error = None
        successful_services = []
        
        for service in ipv6_services:
            try:
                logger.debug(f"Trying to get IPv6 from {service}")
                response = self.session.get(service, timeout=10)
                
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip) and self._is_ipv6(ip):
                        self.log(f"External IPv6 detected: {ip} via {service}")
                        successful_services.append((service, ip))
                        
                        # Сохраняем в кэш
                        self._save_to_cache(cache_key, ip)
                        return ip
                    else:
                        logger.warning(f"Invalid IPv6 response from {service}: {ip}")
                else:
                    logger.warning(f"HTTP {response.status_code} from {service}")
                    
            except requests.exceptions.Timeout:
                last_error = f"Timeout from {service}"
                logger.debug(f"Timeout getting IPv6 from {service}")
            except requests.exceptions.ConnectionError:
                last_error = f"Connection error from {service}"
                logger.debug(f"Connection error getting IPv6 from {service}")
            except Exception as e:
                last_error = f"Error from {service}: {str(e)}"
                logger.debug(f"Error getting IPv6 from {service}: {e}")
        
        # Если есть успешные сервисы, но что-то пошло не так с последним запросом
        if successful_services:
            last_service, last_ip = successful_services[-1]
            self.log(f"Fallback IPv6 from {last_service}: {last_ip}", "WARNING")
            self._save_to_cache(cache_key, last_ip)
            return last_ip
        
        # Если все провалилось
        if last_error:
            self.log(f"Failed to get external IPv6: {last_error}", "ERROR")
        else:
            self.log("Failed to get external IPv6: All services failed", "ERROR")
        
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
        """Получение локального IPv6 адреса с использованием IPv6Manager"""
        try:
            ipv6_manager = get_ipv6_manager()
            local_ipv6_addresses = ipv6_manager.get_local_ipv6_addresses()
            if local_ipv6_addresses:
                self.log(f"Local IPv6 addresses found: {local_ipv6_addresses}")
                return local_ipv6_addresses[0]  # Возвращаем первый адрес
            else:
                self.log("No local IPv6 addresses found", "WARNING")
                return None
        except Exception as e:
            self.log(f"IPv6Manager error getting local IPv6: {e}", "WARNING")
            
            # Fallback ручная проверка
            try:
                # Получение IPv6 адреса через подключение к IPv6 сервису
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                sock.connect(("2001:4860:4860::8888", 80))
                local_ipv6 = sock.getsockname()[0]
                sock.close()
                self.log(f"Local IPv6 detected via fallback: {local_ipv6}")
                return local_ipv6
            except Exception as e:
                self.log(f"Failed to get local IPv6 IP via fallback: {e}", "ERROR")
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
            context.check_hostname = False  # Временно отключаем для тестирования
            context.verify_mode = ssl.CERT_NONE  # Временно отключаем проверку
            
            # Устанавливаем соединение
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Получаем информацию о сертификате
                    cert = ssock.getpeercert()
                    
                    # Безопасно извлекаем информацию о шифре
                    cipher = ssock.cipher()
                    if cipher and isinstance(cipher, tuple) and len(cipher) >= 2:
                        cipher_name = cipher[0]
                        cipher_bits = cipher[1]
                        cipher_protocol = cipher[2] if len(cipher) > 2 else "Unknown"
                    else:
                        cipher_name = "Unknown"
                        cipher_bits = 0
                        cipher_protocol = "Unknown"
                    
                    version = ssock.version()
                    
                    # Извлекаем информацию о сертификате безопасно
                    issuer = "Unknown"
                    subject = "Unknown"
                    
                    if cert and isinstance(cert, dict):
                        # Извлекаем issuer
                        issuer_list = cert.get("issuer", [])
                        if issuer_list and isinstance(issuer_list, list) and len(issuer_list) > 0:
                            first_issuer = issuer_list[0]
                            if isinstance(first_issuer, tuple) and len(first_issuer) > 1:
                                issuer = first_issuer[1]
                        
                        # Извлекаем subject
                        subject_list = cert.get("subject", [])
                        if subject_list and isinstance(subject_list, list) and len(subject_list) > 0:
                            first_subject = subject_list[0]
                            if isinstance(first_subject, tuple) and len(first_subject) > 1:
                                subject = first_subject[1]
                    
                    # Анализируем параметры
                    analysis = {
                        "domain": domain,
                        "tls_version": version,
                        "cipher": cipher_name,
                        "cipher_strength": cipher_bits,
                        "cipher_protocol": cipher_protocol,
                        "issuer": issuer,
                        "subject": subject,
                        "not_after": cert.get("notAfter") if cert else None,
                        "san": cert.get("subjectAltName", []) if cert else [],
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
                    if cipher_bits is not None and isinstance(cipher_bits, int) and cipher_bits > 0 and cipher_bits < 128:
                        score -= 1
                        issues.append(f"Weak cipher strength: {cipher_bits}")
                    
                    # Проверка issuer
                    if issuer != "Unknown" and "Let's Encrypt" not in issuer:
                        score -= 1
                        issues.append(f"Unusual issuer: {issuer}")
                    
                    analysis["score"] = max(0, score)
                    analysis["issues"] = issues
                    analysis["analysis_result"] = "secure" if score >= 3 else "warning" if score >= 1 else "critical"
                    
                    self.log(f"TLS analysis result: {analysis['analysis_result']} (Score: {analysis['score']})")
                    if issues:
                        self.log(f"Issues found: {', '.join(issues)}", "WARNING")
                    
                    return analysis
                    
        except socket.timeout:
            self.log(f"TLS analysis timeout for {domain}", "ERROR")
            return {
                "domain": domain,
                "analysis_result": "error",
                "error": "Connection timeout",
                "score": 0
            }
        except ConnectionRefusedError:
            self.log(f"Connection refused for {domain}", "ERROR")
            return {
                "domain": domain,
                "analysis_result": "error", 
                "error": "Connection refused",
                "score": 0
            }
        except Exception as e:
            self.log(f"TLS analysis failed: {e}", "ERROR")
            return {
                "domain": domain,
                "analysis_result": "error",
                "error": str(e),
                "score": 0
            }
    
    def check_connectivity(self) -> Dict[str, Any]:
        """Проверка сетевой connectivity с поддержкой IPv6"""
        self.log("Checking network connectivity...")
        
        results = {
            "dns_resolved": False,
            "dns_resolved_ipv6": False,
            "tcp_connectivity": False,
            "tcp_connectivity_ipv6": False,
            "http_connectivity": False,
            "http_connectivity_ipv6": False,
            "latency_ms": None,
            "latency_ms_ipv6": None
        }
        
        # Проверка DNS IPv4
        try:
            start_time = time.time()
            socket.gethostbyname("www.google.com")
            results["dns_resolved"] = True
            results["latency_ms"] = int((time.time() - start_time) * 1000)
        except Exception as e:
            self.log(f"IPv4 DNS resolution failed: {e}", "WARNING")
        
        # Проверка DNS IPv6
        try:
            start_time = time.time()
            socket.getaddrinfo("www.google.com", 80, socket.AF_INET6)
            results["dns_resolved_ipv6"] = True
            results["latency_ms_ipv6"] = int((time.time() - start_time) * 1000)
        except Exception as e:
            self.log(f"IPv6 DNS resolution failed: {e}", "WARNING")
        
        # Проверка TCP connectivity IPv4
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
                self.log(f"IPv4 TCP check to {target} failed: {e}", "DEBUG")
        
        # Проверка TCP connectivity IPv6
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("2001:4860:4860::8888", 80))
            sock.close()
            if result == 0:
                results["tcp_connectivity_ipv6"] = True
        except Exception as e:
            self.log(f"IPv6 TCP connectivity check failed: {e}", "DEBUG")
        
        # Проверка HTTP connectivity IPv4
        try:
            response = self.session.get("https://www.google.com", timeout=10)
            if response.status_code == 200:
                results["http_connectivity"] = True
        except Exception as e:
            self.log(f"IPv4 HTTP connectivity check failed: {e}", "WARNING")
        
        # Проверка HTTP connectivity IPv6
        try:
            response = self.session.get("https://ipv6.google.com", timeout=10)
            if response.status_code == 200:
                results["http_connectivity_ipv6"] = True
        except Exception as e:
            self.log(f"IPv6 HTTP connectivity check failed: {e}", "WARNING")
        
        # Обновляем общий статус
        results["dual_stack_connectivity"] = (
            results["dns_resolved"] and results["dns_resolved_ipv6"] and
            results["tcp_connectivity"] and results["tcp_connectivity_ipv6"] and
            results["http_connectivity"] and results["http_connectivity_ipv6"]
        )
        
        self.log(f"Connectivity check: IPv4-DNS={results['dns_resolved']}, "
                f"IPv6-DNS={results['dns_resolved_ipv6']}, "
                f"IPv4-TCP={results['tcp_connectivity']}, "
                f"IPv6-TCP={results['tcp_connectivity_ipv6']}, "
                f"IPv4-HTTP={results['http_connectivity']}, "
                f"IPv6-HTTP={results['http_connectivity_ipv6']}, "
                f"Dual-Stack={results['dual_stack_connectivity']}")
        
        return results
    
    def calculate_mask_score(self) -> int:
        """Улучшенный расчет оценки маскировки (0-5) с обработкой ошибок"""
        self.log("Calculating mask score...")
        
        score = 5  # Начинаем с максимального балла
        deductions = []
        failed_checks = []
        
        try:
            # 1. Проверка утечки IP
            try:
                if self.check_ip_leak():
                    score -= 3
                    deductions.append("IP leak detected")
                    failed_checks.append("IP leak check")
            except Exception as e:
                self.log(f"IP leak check failed: {e}", "ERROR")
                score -= 1  # Снижаем балл за неработающую проверку
                failed_checks.append("IP leak check error")
            
            # 2. Анализ TLS fingerprint
            try:
                tls_analysis = self.analyze_tls_fingerprint()
                if tls_analysis.get("analysis_result") != "error":
                    tls_deduction = 5 - tls_analysis.get("score", 0)
                    score -= tls_deduction
                    if tls_deduction > 0:
                        deductions.append(f"Weak TLS profile: {tls_analysis.get('analysis_result', 'unknown')}")
                else:
                    score -= 2  # Снижаем балл за неработающую проверку TLS
                    failed_checks.append("TLS analysis error")
                    if tls_analysis.get("error"):
                        self.log(f"TLS analysis error: {tls_analysis['error']}", "ERROR")
            except Exception as e:
                self.log(f"TLS analysis failed: {e}", "ERROR")
                score -= 1
                failed_checks.append("TLS analysis exception")
            
            # 3. Проверка connectivity
            try:
                connectivity = self.check_connectivity()
                if not connectivity.get("dns_resolved", False):
                    score -= 1
                    deductions.append("DNS resolution failed")
                if not connectivity.get("tcp_connectivity", False):
                    score -= 1
                    deductions.append("TCP connectivity issues")
                if not connectivity.get("http_connectivity", False):
                    score -= 1
                    deductions.append("HTTP connectivity issues")
            except Exception as e:
                self.log(f"Connectivity check failed: {e}", "ERROR")
                score -= 1
                failed_checks.append("Connectivity check error")
            
            # 4. IPv6 поддержка и dual-stack
            try:
                ipv6_manager = get_ipv6_manager()
                ipv6_status = ipv6_manager.get_ipv6_connectivity_status()
                
                if not ipv6_status.get("ipv6_supported", False):
                    score -= 1
                    deductions.append("IPv6 not supported")
                elif ipv6_status.get("ipv6_connectivity", False):
                    # Бонус за IPv6 подключение
                    score += 1
                    deductions.append("IPv6 connectivity detected")
                
                if ipv6_status.get("dual_stack_connectivity", False):
                    # Бонус за dual-stack
                    score += 1
                    deductions.append("Dual-stack connectivity detected")
            except Exception as e:
                self.log(f"IPv6 connectivity check failed: {e}", "WARNING")
                # Не снижаем балл, просто пропускаем IPv6 проверку
            
            # 5. Проверка на использование стандартных портов VPN
            try:
                vpn_ports = [1194, 1195, 1196, 1197, 1198, 8080, 8443]
                if self._is_vpn_port_exposed(vpn_ports):
                    score -= 2
                    deductions.append("VPN port exposure detected")
            except Exception as e:
                self.log(f"VPN port check failed: {e}", "WARNING")
                # Не снижаем балл, просто пропускаем проверку портов
            
        except Exception as e:
            self.log(f"Score calculation failed: {e}", "ERROR")
            # В случае критической ошибки, возвращаем базовый балл
            score = 2
        
        # Ограничение диапазона оценки
        score = max(0, min(5, score))
        
        # Сохраняем результат
        self.last_score = score
        self.last_check = datetime.now()
        
        # Логируем результат
        self.log(f"Mask score calculated: {score}/5")
        if deductions:
            self.log(f"Deductions applied: {', '.join(deductions)}", "WARNING")
        if failed_checks:
            self.log(f"Failed checks: {', '.join(failed_checks)}", "ERROR")
        
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
        """Улучшенное получение полного статуса здоровья с обработкой ошибок"""
        self.log("Getting comprehensive health status...")
        
        try:
            mask_score = self.calculate_mask_score()
            
            # Получаем IP утечку с обработкой ошибок
            ip_leak = None
            try:
                ip_leak = self.check_ip_leak()
            except Exception as e:
                self.log(f"IP leak check failed: {e}", "WARNING")
                ip_leak = "unknown"
            
            # Получаем TLS анализ с обработкой ошибок
            tls_analysis = None
            try:
                tls_analysis = self.analyze_tls_fingerprint()
            except Exception as e:
                self.log(f"TLS analysis failed: {e}", "WARNING")
                tls_analysis = {
                    "analysis_result": "error",
                    "error": str(e),
                    "score": 0
                }
            
            # Получаем connectivity с обработкой ошибок
            connectivity = None
            try:
                connectivity = self.check_connectivity()
            except Exception as e:
                self.log(f"Connectivity check failed: {e}", "WARNING")
                connectivity = {
                    "dns_resolved": False,
                    "tcp_connectivity": False,
                    "http_connectivity": False,
                    "error": str(e)
                }
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "mask_score": mask_score,
                "status": "excellent" if mask_score >= 4 else
                         "good" if mask_score >= 3 else
                         "warning" if mask_score >= 1 else
                         "critical",
                "ip_leak": ip_leak,
                "tls_analysis": tls_analysis,
                "connectivity": connectivity,
                "last_check": self.last_check.isoformat() if self.last_check else None,
                "network_constraints": {
                    "available_ports": [80, 443],
                    "proxy_detection": "active",
                    "provider_restriction": "confirmed"
                },
                "health_checks": {
                    "ip_leak": ip_leak is not None,
                    "tls_analysis": tls_analysis is not None,
                    "connectivity": connectivity is not None
                }
            }
            
            self.log(f"Health status: {status['status']} (Score: {mask_score})")
            return status
            
        except Exception as e:
            self.log(f"Health status generation failed: {e}", "ERROR")
            return {
                "timestamp": datetime.now().isoformat(),
                "mask_score": 0,
                "status": "error",
                "error": str(e),
                "ip_leak": "unknown",
                "tls_analysis": {"analysis_result": "error", "error": str(e)},
                "connectivity": {"error": str(e)},
                "last_check": None,
                "network_constraints": {
                    "available_ports": [80, 443],
                    "proxy_detection": "active",
                    "provider_restriction": "confirmed"
                },
                "health_checks": {
                    "ip_leak": False,
                    "tls_analysis": False,
                    "connectivity": False
                }
            }
    
    def get_mask_score_simple(self) -> int:
        """Упрощенная функция для интеграции с GUI"""
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
    """Получение информации о IPv6 сети с использованием IPv6Manager"""
    try:
        ipv6_manager = get_ipv6_manager()
        monitor = HealthMonitor()
        
        # Используем IPv6Manager для получения статуса
        ipv6_status = ipv6_manager.get_ipv6_connectivity_status()
        
        # Дополнительно проверяем через HealthMonitor
        local_ips = monitor.get_local_ips()
        external_ips = monitor.get_external_ips()
        
        ipv6_info = {
            "local_ipv6": local_ips["ipv6"],
            "local_ipv6_addresses": ipv6_status.get("local_ipv6_addresses", []),
            "external_ipv6": external_ips["ipv6"],
            "ipv6_supported": ipv6_status.get("ipv6_supported", False),
            "ipv6_enabled": ipv6_status.get("ipv6_enabled", False),
            "dual_stack_enabled": ipv6_status.get("dual_stack_enabled", False),
            "ipv6_leak": False,
            "ipv6_connectivity": ipv6_status.get("ipv6_connectivity", False),
            "dual_stack_support": local_ips["dual_stack"] and external_ips["dual_stack"],
            "dual_stack_connectivity": ipv6_status.get("dual_stack_connectivity", False),
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверка IPv6 утечки
        if local_ips["ipv6"] and external_ips["ipv6"]:
            ipv6_info["ipv6_leak"] = local_ips["ipv6"] == external_ips["ipv6"]
        
        # Обновляем IPv6 connectivity на основе полных данных
        ipv6_info["ipv6_connectivity"] = (
            ipv6_info["ipv6_connectivity"] or
            (external_ips["ipv6"] is not None)
        )
        
        return ipv6_info
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_health_status() -> Dict[str, Any]:
    """Упрощенная функция для получения статуса здоровья"""
    monitor = HealthMonitor()
    return monitor.get_health_status()

if __name__ == "__main__":
    # Тестирование модуля
    print("Testing XVPN Health Monitor...")
    
    monitor = HealthMonitor()
    
    print(f"Mask Score: {monitor.get_mask_score()}")
    print(f"Health Status: {monitor.get_health_status()}")