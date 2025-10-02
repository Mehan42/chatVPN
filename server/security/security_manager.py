#!/usr/bin/env python3
# Менеджер безопасности XVPN
# Абсолютный путь: ~/chatvpn/server/security/security_manager.py

import os
import sys
import json
import time
import logging
import hashlib
import secrets
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
import ipaddress
import threading
from dataclasses import dataclass, asdict

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
LOG_DIR = os.path.expanduser("~/chatvpn/server/security/logs")
LOG_FILE = os.path.join(LOG_DIR, "security_manager.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityRule:
    """Класс для представления правил безопасности"""
    id: str
    name: str
    type: str  # 'ip_whitelist', 'ip_blacklist', 'rate_limit', 'auth_rule'
    enabled: bool
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class SecurityEvent:
    """Класс для представления событий безопасности"""
    id: str
    timestamp: datetime
    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    source_ip: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class SecurityMetrics:
    """Класс для метрик безопасности"""
    total_events: int
    critical_events: int
    blocked_ips: int
    active_sessions: int
    failed_logins: int
    bandwidth_anomalies: int
    last_scan: datetime

class SecurityManager:
    """Комплексный менеджер безопасности XVPN"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: Dict[str, SecurityRule] = {}
        self.events: List[SecurityEvent] = []
        self.metrics = SecurityMetrics(
            total_events=0,
            critical_events=0,
            blocked_ips=0,
            active_sessions=0,
            failed_logins=0,
            bandwidth_anomalies=0,
            last_scan=datetime.now()
        )
        
        # Блокировки
        self.blocked_ips: Set[str] = set()
        self.failed_login_attempts: Dict[str, int] = {}
        self.rate_limits: Dict[str, List[float]] = {}
        
        # Настройки
        self.settings = {
            'max_failed_logins': 5,
            'block_duration': 3600,  # 1 час
            'rate_limit_requests': 100,
            'rate_limit_window': 3600,  # 1 час
            'enable_ip_whitelist': False,
            'enable_ip_blacklist': True,
            'enable_rate_limiting': True,
            'enable_anomaly_detection': True,
            'scan_interval': 300,  # 5 минут
            'log_retention_days': 30
        }
        
        # Инициализация
        self.init_security_manager()
        
        # Запуск сканера в отдельном потоке
        self.scanner_thread = threading.Thread(target=self.security_scanner_loop, daemon=True)
        self.scanner_thread.start()
        
        logger.info("Security Manager initialized successfully")
    
    def init_security_manager(self):
        """Инициализация менеджера безопасности"""
        try:
            # Создание директорий
            self.create_directories()
            
            # Загрузка правил
            self.load_security_rules()
            
            # Загрузка заблокированных IP
            self.load_blocked_ips()
            
            # Инициализация системных настроек безопасности
            self.init_system_security()
            
            logger.info("Security Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Security Manager: {e}")
            raise
    
    def create_directories(self):
        """Создание необходимых директорий"""
        directories = [
            LOG_DIR,
            os.path.expanduser("~/chatvpn/server/security/rules"),
            os.path.expanduser("~/chatvpn/server/security/events"),
            os.path.expanduser("~/chatvpn/server/security/ips"),
            os.path.expanduser("~/chatvpn/server/security/backups")
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def init_system_security(self):
        """Инициализация системных настроек безопасности"""
        logger.info("Initializing system security settings...")
        
        # Обновление системы
        self.update_system()
        
        # Настройка файрвола
        self.configure_firewall()
        
        # Настройка SSH
        self.configure_ssh()
        
        # Настройка системы обнаружения вторжений
        self.configure_intrusion_detection()
        
        # Шифрование дисков
        self.configure_disk_encryption()
        
        logger.info("System security initialized successfully")
    
    def update_system(self):
        """Обновление системы безопасности"""
        logger.info("Updating system packages...")
        
        try:
            # Обновление пакетов
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'], check=True)
            
            # Установка пакетов безопасности
            security_packages = [
                'fail2ban',
                'ufw',
                'clamav',
                'rkhunter',
                'auditd',
                'apparmor',
                'libpam-tmpdir',
                'libpam-namespace',
                'libpam-cracklib',
                'fail2ban'
            ]
            
            for package in security_packages:
                try:
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', package], check=True)
                    logger.info(f"Installed security package: {package}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to install {package}: {e}")
            
            logger.info("System update completed successfully")
            
        except Exception as e:
            logger.error(f"Error updating system: {e}")
    
    def configure_firewall(self):
        """Настройка файрвола"""
        logger.info("Configuring firewall...")
        
        try:
            # Сброс правил
            subprocess.run(['sudo', 'ufw', '--reset'], check=True)
            
            # Базовые политики
            subprocess.run(['sudo', 'ufw', 'default', 'deny', 'incoming'], check=True)
            subprocess.run(['sudo', 'ufw', 'default', 'allow', 'outgoing'], check=True)
            
            # Разрешенные порты
            allowed_ports = [
                ('22', 'SSH'),
                ('80', 'HTTP'),
                ('443', 'HTTPS'),
                ('5000', 'Admin API'),
                ('8080', 'Proxy API'),
                ('9090', 'Metrics')
            ]
            
            for port, service in allowed_ports:
                subprocess.run(['sudo', 'ufw', 'allow', f'{port}/tcp'], check=True)
                logger.info(f"Allowed port {port} ({service})")
            
            # Разрешение локальной сети
            subprocess.run(['sudo', 'ufw', 'allow', '10.0.0.0/8'], check=True)
            subprocess.run(['sudo', 'ufw', 'allow', '172.16.0.0/12'], check=True)
            subprocess.run(['sudo', 'ufw', 'allow', '192.168.0.0/16'], check=True)
            
            # Включение файрвола
            subprocess.run(['sudo', 'ufw', 'enable'], check=True)
            
            logger.info("Firewall configured successfully")
            
        except Exception as e:
            logger.error(f"Error configuring firewall: {e}")
    
    def configure_ssh(self):
        """Настройка SSH безопасности"""
        logger.info("Configuring SSH security...")
        
        try:
            ssh_config_path = Path('/etc/ssh/sshd_config')
            
            if ssh_config_path.exists():
                # Чтение текущей конфигурации
                with open(ssh_config_path, 'r') as f:
                    ssh_config = f.read()
                
                # Обновление настроек безопасности
                security_settings = {
                    'PermitRootLogin': 'no',
                    'PasswordAuthentication': 'no',
                    'PubkeyAuthentication': 'yes',
                    'ChallengeResponseAuthentication': 'no',
                    'UsePAM': 'yes',
                    'X11Forwarding': 'no',
                    'AllowTcpForwarding': 'no',
                    'PermitTunnel': 'no',
                    'MaxAuthTries': '3',
                    'LoginGraceTime': '30',
                    'ClientAliveInterval': '300',
                    'ClientAliveCountMax': '0',
                    'Protocol': '2',
                    'LogLevel': 'VERBOSE',
                    'MaxStartups': '10:30:60',
                    'IgnoreRhosts': 'yes',
                    'HostbasedAuthentication': 'no',
                    'PermitUserEnvironment': 'no'
                }
                
                # Применение настроек
                for setting, value in security_settings.items():
                    ssh_config = re.sub(
                        rf'^{setting}\s+.*$',
                        f'{setting} {value}',
                        ssh_config,
                        flags=re.MULTILINE
                    )
                
                # Запись обратно
                with open(ssh_config_path, 'w') as f:
                    f.write(ssh_config)
                
                # Перезапуск SSH
                subprocess.run(['sudo', 'systemctl', 'restart', 'ssh'], check=True)
                
                logger.info("SSH security configured successfully")
            
        except Exception as e:
            logger.error(f"Error configuring SSH: {e}")
    
    def configure_intrusion_detection(self):
        """Настройка системы обнаружения вторжений"""
        logger.info("Configuring intrusion detection...")
        
        try:
            # Настройка fail2ban
            fail2ban_config = Path('/etc/fail2ban/jail.local')
            
            fail2ban_config_content = f"""[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
banaction = ufw
banaction_allports = ufw
protocol = tcp

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
"""
            
            with open(fail2ban_config, 'w') as f:
                f.write(fail2ban_config_content)
            
            # Перезапуск fail2ban
            subprocess.run(['sudo', 'systemctl', 'restart', 'fail2ban'], check=True)
            
            logger.info("Intrusion detection configured successfully")
            
        except Exception as e:
            logger.error(f"Error configuring intrusion detection: {e}")
    
    def configure_disk_encryption(self):
        """Настройка шифрования дисков"""
        logger.info("Configuring disk encryption...")
        
        try:
            # Проверка поддержки шифрования
            if os.path.exists('/usr/bin/cryptsetup'):
                logger.info("LUKS encryption available")
                
                # Создание резервной копии важных файлов
                self.backup_critical_files()
                
                logger.info("Disk encryption setup completed")
            else:
                logger.warning("LUKS not available, skipping disk encryption")
                
        except Exception as e:
            logger.error(f"Error configuring disk encryption: {e}")
    
    def backup_critical_files(self):
        """Создание резервной копии критических файлов"""
        logger.info("Creating backup of critical files...")
        
        backup_dir = os.path.expanduser("~/chatvpn/server/security/backups")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
        
        try:
            # Создание резервной копии конфигураций
            critical_files = [
                '/etc/ssh/sshd_config',
                '/etc/nginx/nginx.conf',
                '/etc/fail2ban/jail.local',
                '/etc/ufw/before.rules',
                '/etc/ufw/before6.rules'
            ]
            
            os.makedirs(backup_path, exist_ok=True)
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    backup_file = os.path.join(backup_path, file_name)
                    
                    # Копирование файла
                    subprocess.run(['sudo', 'cp', file_path, backup_file], check=True)
                    
                    # Установка прав
                    subprocess.run(['sudo', 'chown', os.getlogin(), backup_file], check=True)
                    subprocess.run(['sudo', 'chmod', '600', backup_file], check=True)
                    
                    logger.info(f"Backed up: {file_path}")
            
            logger.info("Critical files backup completed successfully")
            
        except Exception as e:
            logger.error(f"Error backing up critical files: {e}")
    
    def load_security_rules(self):
        """Загрузка правил безопасности"""
        try:
            rules_dir = os.path.expanduser("~/chatvpn/server/security/rules")
            
            # Загрузка правил по умолчанию
            default_rules = [
                SecurityRule(
                    id="ip_blacklist",
                    name="IP Blacklist",
                    type="ip_blacklist",
                    enabled=True,
                    parameters={"max_attempts": 5, "block_duration": 3600},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                SecurityRule(
                    id="rate_limit",
                    name="Rate Limiting",
                    type="rate_limit",
                    enabled=True,
                    parameters={"max_requests": 100, "window_seconds": 3600},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                SecurityRule(
                    id="auth_rule",
                    name="Authentication",
                    type="auth_rule",
                    enabled=True,
                    parameters={"max_failed_attempts": 3, "lockout_duration": 1800},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            for rule in default_rules:
                self.rules[rule.id] = rule
            
            logger.info(f"Loaded {len(self.rules)} security rules")
            
        except Exception as e:
            logger.error(f"Error loading security rules: {e}")
    
    def load_blocked_ips(self):
        """Загрузка заблокированных IP"""
        try:
            blocked_ips_file = os.path.expanduser("~/chatvpn/server/security/ips/blocked_ips.txt")
            
            if os.path.exists(blocked_ips_file):
                with open(blocked_ips_file, 'r') as f:
                    blocked_ips = f.read().splitlines()
                
                for ip in blocked_ips:
                    if ip.strip():
                        self.blocked_ips.add(ip.strip())
                
                logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs")
            else:
                logger.info("No blocked IPs file found")
                
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
    
    def security_scanner_loop(self):
        """Основной цикл сканера безопасности"""
        while True:
            try:
                # Выполнение сканирования
                self.perform_security_scan()
                
                # Очистка старых событий
                self.cleanup_old_events()
                
                # Ожидание следующего сканирования
                time.sleep(self.settings['scan_interval'])
                
            except Exception as e:
                logger.error(f"Error in security scanner loop: {e}")
                time.sleep(60)  # Ожидание при ошибке
    
    def perform_security_scan(self):
        """Выполнение полного сканирования безопасности"""
        logger.info("Performing security scan...")
        
        try:
            scan_start = datetime.now()
            
            # Сканирование уязвимостей
            self.scan_vulnerabilities()
            
            # Мониторинг аномалий
            self.monitor_anomalies()
            
            # Проверка целостности
            self.check_integrity()
            
            # Анализ логов
            self.analyze_logs()
            
            # Обновление метрик
            self.update_metrics()
            
            scan_duration = (datetime.now() - scan_start).total_seconds()
            logger.info(f"Security scan completed in {scan_duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error performing security scan: {e}")
    
    def scan_vulnerabilities(self):
        """Сканирование уязвимостей"""
        logger.info("Scanning for vulnerabilities...")
        
        try:
            # Проверка обновлений безопасности
            result = subprocess.run(['sudo', 'apt', 'list', '--upgradable'], 
                                  capture_output=True, text=True)
            
            if result.stdout and "security" in result.stdout.lower():
                security_updates = [line for line in result.stdout.split('\n') 
                                  if 'security' in line.lower()]
                
                if security_updates:
                    event = SecurityEvent(
                        id=f"sec_update_{int(time.time())}",
                        timestamp=datetime.now(),
                        event_type="security_updates_available",
                        severity="high",
                        source_ip="localhost",
                        details={"updates": security_updates},
                        resolved=False
                    )
                    
                    self.add_security_event(event)
                    logger.warning(f"Found {len(security_updates)} security updates")
            
            # Проверка открытых портов
            self.check_open_ports()
            
            # Проверка слабых паролей
            self.check_weak_passwords()
            
        except Exception as e:
            logger.error(f"Error scanning vulnerabilities: {e}")
    
    def monitor_anomalies(self):
        """Мониторинг аномалий"""
        logger.info("Monitoring for anomalies...")
        
        try:
            # Мониторинг трафика
            self.monitor_traffic_anomalies()
            
            # Мониторинг процессов
            self.monitor_process_anomalies()
            
            # Мониторинг файловой системы
            self.monitor_filesystem_anomalies()
            
        except Exception as e:
            logger.error(f"Error monitoring anomalies: {e}")
    
    def check_open_ports(self):
        """Проверка открытых портов"""
        try:
            # Проверка с помощью netstat
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
            
            open_ports = []
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        port_info = parts[3]
                        open_ports.append(port_info)
            
            # Проверка на подозрительные порты
            suspicious_ports = [1337, 31337, 12345, 54321]
            
            for port_info in open_ports:
                for suspicious_port in suspicious_ports:
                    if str(suspicious_port) in port_info:
                        event = SecurityEvent(
                            id=f"suspicious_port_{int(time.time())}",
                            timestamp=datetime.now(),
                            event_type="suspicious_port_open",
                            severity="medium",
                            source_ip="localhost",
                            details={"port": port_info},
                            resolved=False
                        )
                        
                        self.add_security_event(event)
                        logger.warning(f"Suspicious port detected: {port_info}")
        
        except Exception as e:
            logger.error(f"Error checking open ports: {e}")
    
    def check_weak_passwords(self):
        """Проверка слабых паролей"""
        logger.info("Checking for weak passwords...")
        
        try:
            # Проверка пользователей с пустыми паролями
            result = subprocess.run(['sudo', 'passwd', '-S'], capture_output=True, text=True)
            
            weak_passwords = []
            for line in result.stdout.split('\n'):
                if 'P' in line:  # Пароль установлен
                    parts = line.split()
                    if len(parts) >= 2:
                        username = parts[0]
                        password_status = parts[1]
                        
                        if password_status == 'P':  # Пароль не истек
                            weak_passwords.append(username)
            
            if weak_passwords:
                event = SecurityEvent(
                    id=f"weak_password_{int(time.time())}",
                    timestamp=datetime.now(),
                    event_type="weak_passwords_detected",
                    severity="high",
                    source_ip="localhost",
                    details={"users": weak_passwords},
                    resolved=False
                )
                
                self.add_security_event(event)
                logger.warning(f"Weak passwords detected for users: {weak_passwords}")
        
        except Exception as e:
            logger.error(f"Error checking weak passwords: {e}")
    
    def monitor_traffic_anomalies(self):
        """Мониторинг аномалий трафика"""
        try:
            # Получение статистики трафика
            result = subprocess.run(['iftop', '-t', '-s', '5'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Анализ трафика на аномалии
            # (Здесь можно добавить более сложную логику анализа)
            
        except Exception as e:
            logger.debug(f"Traffic monitoring error: {e}")
    
    def monitor_process_anomalies(self):
        """Мониторинг аномалий процессов"""
        try:
            # Проверка подозрительных процессов
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            
            suspicious_processes = []
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in 
                      ['malware', 'virus', 'backdoor', 'rootkit']):
                    suspicious_processes.append(line)
            
            if suspicious_processes:
                event = SecurityEvent(
                    id=f"suspicious_process_{int(time.time())}",
                    timestamp=datetime.now(),
                    event_type="suspicious_process_detected",
                    severity="critical",
                    source_ip="localhost",
                    details={"processes": suspicious_processes},
                    resolved=False
                )
                
                self.add_security_event(event)
                logger.warning(f"Suspicious processes detected: {suspicious_processes}")
        
        except Exception as e:
            logger.error(f"Error monitoring processes: {e}")
    
    def monitor_filesystem_anomalies(self):
        """Мониторинг аномалий файловой системы"""
        try:
            # Проверка измененных системных файлов
            result = subprocess.run(['sudo', 'debsums'], capture_output=True, text=True)
            
            changed_files = []
            for line in result.stdout.split('\n'):
                if 'OK' not in line and line.strip():
                    changed_files.append(line)
            
            if changed_files:
                event = SecurityEvent(
                    id=f"file_change_{int(time.time())}",
                    timestamp=datetime.now(),
                    event_type="system_file_changed",
                    severity="medium",
                    source_ip="localhost",
                    details={"files": changed_files},
                    resolved=False
                )
                
                self.add_security_event(event)
                logger.warning(f"System files changed: {changed_files}")
        
        except Exception as e:
            logger.error(f"Error monitoring filesystem: {e}")
    
    def check_integrity(self):
        """Проверка целостности системы"""
        logger.info("Checking system integrity...")
        
        try:
            # Проверка с помощью rkhunter
            result = subprocess.run(['sudo', 'rkhunter', '--checkall'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                event = SecurityEvent(
                    id=f"integrity_check_{int(time.time())}",
                    timestamp=datetime.now(),
                    event_type="integrity_check_failed",
                    severity="high",
                    source_ip="localhost",
                    details={"output": result.stdout},
                    resolved=False
                )
                
                self.add_security_event(event)
                logger.warning("System integrity check failed")
        
        except Exception as e:
            logger.error(f"Error checking integrity: {e}")
    
    def analyze_logs(self):
        """Анализ логов"""
        logger.info("Analyzing logs...")
        
        try:
            # Анализ логов аутентификации
            self.analyze_auth_logs()
            
            # Анализ логов доступа
            self.analyze_access_logs()
            
            # Анализ системных логов
            self.analyze_system_logs()
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
    
    def analyze_auth_logs(self):
        """Анализ логов аутентификации"""
        try:
            auth_log = '/var/log/auth.log'
            
            if os.path.exists(auth_log):
                with open(auth_log, 'r') as f:
                    lines = f.readlines()[-1000:]  # Последние 1000 строк
                
                failed_logins = []
                for line in lines:
                    if 'Failed password' in line or 'Authentication failure' in line:
                        failed_logins.append(line)
                
                if len(failed_logins) > 10:
                    event = SecurityEvent(
                        id=f"auth_scan_{int(time.time())}",
                        timestamp=datetime.now(),
                        event_type="multiple_failed_logins",
                        severity="medium",
                        source_ip="localhost",
                        details={"failed_logins": len(failed_logins)},
                        resolved=False
                    )
                    
                    self.add_security_event(event)
                    logger.warning(f"Detected {len(failed_logins)} failed login attempts")
        
        except Exception as e:
            logger.error(f"Error analyzing auth logs: {e}")
    
    def analyze_access_logs(self):
        """Анализ логов доступа"""
        try:
            access_log = '/var/log/nginx/access.log'
            
            if os.path.exists(access_log):
                with open(access_log, 'r') as f:
                    lines = f.readlines()[-1000:]  # Последние 1000 строк
                
                suspicious_requests = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in 
                          ['sql injection', 'xss', 'path traversal', 'command injection']):
                        suspicious_requests.append(line)
                
                if suspicious_requests:
                    event = SecurityEvent(
                        id=f"access_scan_{int(time.time())}",
                        timestamp=datetime.now(),
                        event_type="suspicious_requests",
                        severity="high",
                        source_ip="localhost",
                        details={"requests": suspicious_requests},
                        resolved=False
                    )
                    
                    self.add_security_event(event)
                    logger.warning(f"Detected {len(suspicious_requests)} suspicious requests")
        
        except Exception as e:
            logger.error(f"Error analyzing access logs: {e}")
    
    def analyze_system_logs(self):
        """Анализ системных логов"""
        try:
            system_log = '/var/log/syslog'
            
            if os.path.exists(system_log):
                with open(system_log, 'r') as f:
                    lines = f.readlines()[-1000:]  # Последние 1000 строк
                
                system_errors = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in 
                          ['error', 'failed', 'exception', 'panic']):
                        system_errors.append(line)
                
                if len(system_errors) > 50:
                    event = SecurityEvent(
                        id=f"system_scan_{int(time.time())}",
                        timestamp=datetime.now(),
                        event_type="system_errors_detected",
                        severity="medium",
                        source_ip="localhost",
                        details={"errors": len(system_errors)},
                        resolved=False
                    )
                    
                    self.add_security_event(event)
                    logger.warning(f"Detected {len(system_errors)} system errors")
        
        except Exception as e:
            logger.error(f"Error analyzing system logs: {e}")
    
    def add_security_event(self, event: SecurityEvent):
        """Добавление события безопасности"""
        self.events.append(event)
        self.metrics.total_events += 1
        
        if event.severity == 'critical':
            self.metrics.critical_events += 1
        
        # Сохранение события в файл
        self.save_security_event(event)
        
        logger.info(f"Security event added: {event.event_type} ({event.severity})")
    
    def save_security_event(self, event: SecurityEvent):
        """Сохранение события безопасности в файл"""
        try:
            events_dir = os.path.expanduser("~/chatvpn/server/security/events")
            event_file = os.path.join(events_dir, f"event_{event.id}.json")
            
            with open(event_file, 'w') as f:
                json.dump(asdict(event), f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error saving security event: {e}")
    
    def cleanup_old_events(self):
        """Очистка старых событий"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.settings['log_retention_days'])
            
            # Удаление старых событий
            self.events = [event for event in self.events 
                          if event.timestamp > cutoff_date]
            
            # Удаление старых файлов событий
            events_dir = os.path.expanduser("~/chatvpn/server/security/events")
            
            for event_file in os.listdir(events_dir):
                event_path = os.path.join(events_dir, event_file)
                if os.path.isfile(event_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(event_path))
                    if file_time < cutoff_date:
                        os.remove(event_path)
            
            logger.info(f"Cleaned up old events, remaining: {len(self.events)}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
    
    def update_metrics(self):
        """Обновление метрик безопасности"""
        try:
            self.metrics.blocked_ips = len(self.blocked_ips)
            self.metrics.active_sessions = len(self.get_active_sessions())
            self.metrics.failed_logins = sum(self.failed_login_attempts.values())
            self.metrics.bandwidth_anomalies = self.detect_bandwidth_anomalies()
            self.metrics.last_scan = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def get_active_sessions(self):
        """Получение активных сессий"""
        try:
            sessions = []
            result = subprocess.run(['who'], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        session = {
                            'user': parts[0],
                            'terminal': parts[1],
                            'remote_host': parts[2] if parts[2] != ':' else None,
                            'login_time': ' '.join(parts[3:5])
                        }
                        sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def detect_bandwidth_anomalies(self):
        """Обнаружение аномалий пропускной способности"""
        try:
            # Здесь можно добавить логику обнаружения аномалий трафика
            # Например, сравнение с нормальным уровнем трафика
            
            return 0  # Временно возвращаем 0
            
        except Exception as e:
            logger.error(f"Error detecting bandwidth anomalies: {e}")
            return 0
    
    def check_ip_security(self, ip: str) -> Tuple[bool, str]:
        """Проверка безопасности IP адреса"""
        try:
            # Проверка на заблокированные IP
            if ip in self.blocked_ips:
                return False, "IP is blocked"
            
            # Проверка на недопустимые IP
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private or ip_obj.is_loopback:
                    return False, "Private or loopback IP not allowed"
            except ValueError:
                return False, "Invalid IP address"
            
            # Проверка rate limiting
            if self.settings['enable_rate_limiting']:
                if self.check_rate_limit(ip):
                    return False, "Rate limit exceeded"
            
            # Проверка на blacklist
            if self.settings['enable_ip_blacklist']:
                if self.check_ip_blacklist(ip):
                    return False, "IP is in blacklist"
            
            # Проверка на whitelist
            if self.settings['enable_ip_whitelist']:
                if not self.check_ip_whitelist(ip):
                    return False, "IP is not in whitelist"
            
            return True, "IP is secure"
            
        except Exception as e:
            logger.error(f"Error checking IP security: {e}")
            return False, "Security check failed"
    
    def check_rate_limit(self, ip: str) -> bool:
        """Проверка rate limiting для IP"""
        try:
            current_time = time.time()
            
            # Очистка старых записей
            if ip in self.rate_limits:
                self.rate_limits[ip] = [
                    timestamp for timestamp in self.rate_limits[ip]
                    if current_time - timestamp < self.settings['rate_limit_window']
                ]
            
            # Добавление текущего времени
            if ip not in self.rate_limits:
                self.rate_limits[ip] = []
            
            self.rate_limits[ip].append(current_time)
            
            # Проверка лимита
            return len(self.rate_limits[ip]) > self.settings['rate_limit_requests']
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    def check_ip_blacklist(self, ip: str) -> bool:
        """Проверка IP в blacklist"""
        return ip in self.blocked_ips
    
    def check_ip_whitelist(self, ip: str) -> bool:
        """Проверка IP в whitelist"""
        # Здесь можно реализовать whitelist
        return True
    
    def block_ip(self, ip: str, duration: int = None):
        """Блокировка IP адреса"""
        try:
            if duration is None:
                duration = self.settings['block_duration']
            
            self.blocked_ips.add(ip)
            
            # Добавление в файрвол
            subprocess.run(['sudo', 'ufw', 'deny', 'from', ip], check=True)
            
            # Сохранение в файл
            self.save_blocked_ip(ip, duration)
            
            # Создание события
            event = SecurityEvent(
                id=f"ip_block_{int(time.time())}",
                timestamp=datetime.now(),
                event_type="ip_blocked",
                severity="medium",
                source_ip=ip,
                details={"duration": duration},
                resolved=False
            )
            
            self.add_security_event(event)
            
            logger.info(f"IP {ip} blocked for {duration} seconds")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    def save_blocked_ip(self, ip: str, duration: int):
        """Сохранение заблокированного IP в файл"""
        try:
            blocked_ips_file = os.path.expanduser("~/chatvpn/server/security/ips/blocked_ips.txt")
            
            with open(blocked_ips_file, 'a') as f:
                f.write(f"{ip} - blocked until {datetime.now() + timedelta(seconds=duration)}\n")
            
        except Exception as e:
            logger.error(f"Error saving blocked IP: {e}")
    
    def unblock_ip(self, ip: str):
        """Разблокировка IP адреса"""
        try:
            if ip in self.blocked_ips:
                self.blocked_ips.remove(ip)
                
                # Удаление из файрвола
                subprocess.run(['sudo', 'ufw', 'delete', 'deny', 'from', ip], check=True)
                
                logger.info(f"IP {ip} unblocked")
                
                # Создание события
                event = SecurityEvent(
                    id=f"ip_unblock_{int(time.time())}",
                    timestamp=datetime.now(),
                    event_type="ip_unblocked",
                    severity="low",
                    source_ip=ip,
                    details={},
                    resolved=False
                )
                
                self.add_security_event(event)
        
        except Exception as e:
            logger.error(f"Error unblocking IP: {e}")
    
    def get_security_report(self) -> Dict[str, Any]:
        """Получение отчета о безопасности"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'metrics': asdict(self.metrics),
                'blocked_ips': list(self.blocked_ips),
                'recent_events': [
                    asdict(event) for event in self.events[-10:]
                ],
                'system_info': self.get_system_security_info(),
                'recommendations': self.get_security_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {}
    
    def get_system_security_info(self) -> Dict[str, Any]:
        """Получение информации о безопасности системы"""
        try:
            info = {
                'os_info': self.get_os_info(),
                'kernel_info': self.get_kernel_info(),
                'uptime': self.get_uptime(),
                'disk_encryption': self.get_disk_encryption_status(),
                'firewall_status': self.get_firewall_status(),
                'fail2ban_status': self.get_fail2ban_status(),
                'antivirus_status': self.get_antivirus_status()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting system security info: {e}")
            return {}
    
    def get_os_info(self) -> Dict[str, Any]:
        """Получение информации об ОС"""
        try:
            result = subprocess.run(['lsb_release', '-a'], capture_output=True, text=True)
            
            os_info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    os_info[key.strip()] = value.strip()
            
            return os_info
            
        except Exception as e:
            logger.error(f"Error getting OS info: {e}")
            return {}
    
    def get_kernel_info(self) -> Dict[str, Any]:
        """Получение информации о ядре"""
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
            
            return {
                'kernel_version': result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Error getting kernel info: {e}")
            return {}
    
    def get_uptime(self) -> str:
        """Получение времени работы системы"""
        try:
            result = subprocess.run(['uptime'], capture_output=True, text=True)
            return result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return "Unknown"
    
    def get_disk_encryption_status(self) -> Dict[str, Any]:
        """Получение статуса шифрования дисков"""
        try:
            result = subprocess.run(['sudo', 'lsblk', '-o', 'NAME,FSTYPE,MOUNTPOINT'], 
                                  capture_output=True, text=True)
            
            encrypted_partitions = []
            for line in result.stdout.split('\n'):
                if 'crypto_LUKS' in line:
                    encrypted_partitions.append(line.strip())
            
            return {
                'encrypted_partitions': encrypted_partitions,
                'total_partitions': len(encrypted_partitions)
            }
            
        except Exception as e:
            logger.error(f"Error getting disk encryption status: {e}")
            return {}
    
    def get_firewall_status(self) -> Dict[str, Any]:
        """Получение статуса файрвола"""
        try:
            result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True)
            
            return {
                'status': result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Error getting firewall status: {e}")
            return {}
    
    def get_fail2ban_status(self) -> Dict[str, Any]:
        """Получение статуса fail2ban"""
        try:
            result = subprocess.run(['sudo', 'fail2ban-client', 'status'], 
                                  capture_output=True, text=True)
            
            return {
                'status': result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Error getting fail2ban status: {e}")
            return {}
    
    def get_antivirus_status(self) -> Dict[str, Any]:
        """Получение статуса антивируса"""
        try:
            result = subprocess.run(['sudo', 'clamscan', '--version'], 
                                  capture_output=True, text=True)
            
            return {
                'status': 'installed' if result.returncode == 0 else 'not installed',
                'version': result.stdout.strip() if result.returncode == 0 else None
            }
            
        except Exception as e:
            logger.error(f"Error getting antivirus status: {e}")
            return {}
    
    def get_security_recommendations(self) -> List[str]:
        """Получение рекомендаций по безопасности"""
        recommendations = []
        
        try:
            # Проверка обновлений
            result = subprocess.run(['sudo', 'apt', 'list', '--upgradable'], 
                                  capture_output=True, text=True)
            
            if "security" in result.stdout.lower():
                recommendations.append("Install security updates")
            
            # Проверка паролей
            result = subprocess.run(['sudo', 'passwd', '-S'], capture_output=True, text=True)
            weak_passwords = [line.split()[0] for line in result.stdout.split('\n') 
                            if 'P' in line and len(line.split()) > 1]
            
            if weak_passwords:
                recommendations.append("Review user passwords")
            
            # Проверка открытых портов
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
            open_ports = [line.split()[3] for line in result.stdout.split('\n') 
                         if 'LISTEN' in line and len(line.split()) > 3]
            
            suspicious_ports = [1337, 31337, 12345, 54321]
            if any(str(port) in str(open_ports) for port in suspicious_ports):
                recommendations.append("Check for suspicious open ports")
            
            # Проверка SSH настроек
            ssh_config_path = Path('/etc/ssh/sshd_config')
            if ssh_config_path.exists():
                with open(ssh_config_path, 'r') as f:
                    ssh_config = f.read()
                
                if 'PermitRootLogin yes' in ssh_config:
                    recommendations.append("Disable root login via SSH")
                
                if 'PasswordAuthentication yes' in ssh_config:
                    recommendations.append("Disable password authentication for SSH")
            
            # Проверка брандмауэра
            result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True)
            if 'Status: active' not in result.stdout:
                recommendations.append("Enable firewall")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating security recommendations: {e}")
            return []

def create_security_manager(config: Dict[str, Any] = None) -> SecurityManager:
    """Фабричная функция для создания Security Manager"""
    if config is None:
        config = {}
    
    return SecurityManager(config)

if __name__ == "__main__":
    # Пример использования
    config = {
        'max_failed_logins': 5,
        'block_duration': 3600,
        'rate_limit_requests': 100,
        'rate_limit_window': 3600
    }
    
    security_manager = create_security_manager(config)
    
    # Тестирование безопасности IP
    test_ip = "192.168.1.100"
    is_secure, message = security_manager.check_ip_security(test_ip)
    print(f"IP {test_ip} is secure: {is_secure} - {message}")
    
    # Получение отчета о безопасности
    report = security_manager.get_security_report()
    print(f"Security report: {report}")