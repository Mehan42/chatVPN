#!/usr/bin/env python3
# XVPN IPv6 Manager
# Управление IPv6 подключением и dual-stack режимом
# Абсолютный путь: ~/chatvpn/client/ (может быть переустановлен в другое место)ipv6_manager.py (может быть переустановлен в другое место)

import os
import json
import time
import socket
import subprocess
from pathlib import Path

# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()
import requests
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IPv6Manager:
    """Менеджер IPv6 подключений и dual-stack режима"""
    
    def __init__(self):
        self.config = self._load_config()
        self.ipv6_enabled = self.config.get('ipv6_enabled', True)
        self.dual_stack_enabled = self.config.get('dual_stack_enabled', True)
        self.preferred_v6_services = self.config.get('preferred_v6_services', [
            "https://api6.ipify.org",
            "https://ifconfig.co/ip",
            "https://icanhazip.com",
            "https://v6.ident.me"
        ])
        self.ipv6_dns_servers = self.config.get('ipv6_dns_servers', [
            "2001:4860:4860::8888",  # Google Public DNS
            "2606:4700:4700::1111",  # Cloudflare DNS
            "2001:503:BA3E::2:30"    # Verisign DNS
        ])
        
        # Пути к логам
        self.log_dir = CLIENT_DIR / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / 'ipv6_manager.log'
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка логирования"""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _load_config(self) -> Dict:
        """Загрузка конфигурации IPv6"""
        config_path = CLIENT_DIR / 'ipv6_config.json'
        default_config = {
            "ipv6_enabled": True,
            "dual_stack_enabled": True,
            "preferred_v6_services": [
                "https://api6.ipify.org",
                "https://ifconfig.co/ip",
                "https://icanhazip.com",
                "https://v6.ident.me"
            ],
            "ipv6_dns_servers": [
                "2001:4860:4860::8888",
                "2606:4700:4700::1111",
                "2001:503:BA3E::2:30"
            ],
            "ipv6_routing_table": "main",
            "prefer_ipv6_over_ipv4": False
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    logger.info(f"IPv6 config loaded from {config_path}")
            else:
                # Создаем файл конфигурации с настройками по умолчанию
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"IPv6 config created at {config_path}")
            
            return default_config
            
        except Exception as e:
            logger.error(f"Error loading IPv6 config: {e}")
            return default_config
    
    def save_config(self):
        """Сохранение конфигурации IPv6"""
        config_path = CLIENT_DIR / 'ipv6_config.json'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"IPv6 config saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving IPv6 config: {e}")
    
    def is_ipv6_supported(self) -> bool:
        """Проверка поддержки IPv6 в системе"""
        try:
            # Проверка наличия IPv6 интерфейса
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                sock.connect(('2001:4860:4860::8888', 80))
                sock.close()
                logger.info("IPv6 support detected")
                return True
            except:
                pass
            
            # Проверка через sysctl
            try:
                result = subprocess.run(['sysctl', '-n', 'net.ipv6.conf.all.disable_ipv6'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip() == '0':
                    logger.info("IPv6 enabled in kernel")
                    return True
            except:
                pass
            
            logger.warning("IPv6 support not detected")
            return False
            
        except Exception as e:
            logger.error(f"Error checking IPv6 support: {e}")
            return False
    
    def get_external_ipv6(self) -> Optional[str]:
        """Получение внешнего IPv6 адреса через несколько сервисов"""
        if not self.is_ipv6_supported():
            logger.warning("IPv6 not supported, skipping external IPv6 detection")
            return None
        
        for service in self.preferred_v6_services:
            try:
                response = requests.get(service, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    ipv6 = response.text.strip()
                    if self._is_valid_ipv6(ipv6):
                        logger.info(f"External IPv6 detected: {ipv6} via {service}")
                        return ipv6
            except Exception as e:
                logger.debug(f"Failed to get IPv6 from {service}: {e}")
        
        logger.warning("Failed to get external IPv6 from all services")
        return None
    
    def get_local_ipv6_addresses(self) -> List[str]:
        """Получение локальных IPv6 адресов"""
        ipv6_addresses = []
        
        try:
            # Получение всех IPv6 адресов через ip
            result = subprocess.run(['ip', '-6', '-o', 'addr', 'show'], 
                                  capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if 'inet6' in line and 'scope global' in line:
                    parts = line.split()
                    if len(parts) > 3:
                        ipv6 = parts[3].split('/')[0]
                        if self._is_valid_ipv6(ipv6):
                            ipv6_addresses.append(ipv6)
            
            logger.info(f"Found {len(ipv6_addresses)} local IPv6 addresses")
            return ipv6_addresses
            
        except Exception as e:
            logger.error(f"Error getting local IPv6 addresses: {e}")
            return []
    
    def _is_valid_ipv6(self, ip: str) -> bool:
        """Проверка валидности IPv6 адреса"""
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False
    
    def configure_ipv6_routing(self, enable: bool = True) -> bool:
        """Настройка IPv6 маршрутизации"""
        try:
            if enable:
                # Включение IPv6 forwarding
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.all.forwarding=1'], 
                             check=True, capture_output=True)
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.default.forwarding=1'], 
                             check=True, capture_output=True)
                logger.info("IPv6 forwarding enabled")
            else:
                # Отключение IPv6 forwarding
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.all.forwarding=0'], 
                             check=True, capture_output=True)
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.default.forwarding=0'], 
                             check=True, capture_output=True)
                logger.info("IPv6 forwarding disabled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error configuring IPv6 routing: {e}")
            return False
    
    def configure_ipv6_dns(self, dns_servers: List[str]) -> bool:
        """Настройка IPv6 DNS серверов"""
        try:
            # Создание файла resolv.conf для IPv6
            resolv_conf_path = Path('/etc/resolv.conf')
            backup_path = Path('/etc/resolv.conf.backup')
            
            # Создаем резервную копию
            if resolv_conf_path.exists():
                with open(resolv_conf_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
            
            # Записываем новые DNS серверы
            with open(resolv_conf_path, 'w') as f:
                f.write("# Generated by XVPN IPv6 Manager\n")
                f.write("# IPv6 DNS servers\n")
                for dns in dns_servers:
                    f.write(f"nameserver {dns}\n")
            
            logger.info(f"IPv6 DNS servers configured: {dns_servers}")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring IPv6 DNS: {e}")
            return False
    
    def get_ipv6_connectivity_status(self) -> Dict[str, Any]:
        """Получение статуса IPv6 подключения"""
        status = {
            "ipv6_supported": self.is_ipv6_supported(),
            "ipv6_enabled": self.ipv6_enabled,
            "dual_stack_enabled": self.dual_stack_enabled,
            "external_ipv6": None,
            "local_ipv6_addresses": [],
            "ipv6_connectivity": False,
            "dual_stack_connectivity": False
        }
        
        try:
            # Получение внешнего IPv6
            if status["ipv6_supported"]:
                status["external_ipv6"] = self.get_external_ipv6()
                status["local_ipv6_addresses"] = self.get_local_ipv6_addresses()
                
                # Проверка IPv6 connectivity
                if status["external_ipv6"]:
                    status["ipv6_connectivity"] = True
                    
                    # Проверка dual-stack connectivity
                    try:
                        # Проверка IPv4 DNS
                        socket.gethostbyname("www.google.com")
                        # Проверка IPv6 DNS
                        socket.getaddrinfo("www.google.com", 80, socket.AF_INET6)
                        status["dual_stack_connectivity"] = True
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Error getting IPv6 connectivity status: {e}")
        
        return status
    
    def enable_ipv6(self) -> bool:
        """Включение IPv6 поддержки"""
        try:
            if not self.is_ipv6_supported():
                logger.warning("IPv6 not supported by system")
                return False
            
            self.ipv6_enabled = True
            self.config['ipv6_enabled'] = True
            self.save_config()
            
            logger.info("IPv6 support enabled")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling IPv6: {e}")
            return False
    
    def disable_ipv6(self) -> bool:
        """Отключение IPv6 поддержки"""
        try:
            self.ipv6_enabled = False
            self.config['ipv6_enabled'] = False
            self.save_config()
            
            logger.info("IPv6 support disabled")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling IPv6: {e}")
            return False
    
    def enable_dual_stack(self) -> bool:
        """Включение dual-stack режима"""
        try:
            if not self.is_ipv6_supported():
                logger.warning("IPv6 not supported, cannot enable dual-stack")
                return False
            
            self.dual_stack_enabled = True
            self.config['dual_stack_enabled'] = True
            self.save_config()
            
            logger.info("Dual-stack mode enabled")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling dual-stack: {e}")
            return False
    
    def disable_dual_stack(self) -> bool:
        """Отключение dual-stack режима"""
        try:
            self.dual_stack_enabled = False
            self.config['dual_stack_enabled'] = False
            self.save_config()
            
            logger.info("Dual-stack mode disabled")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling dual-stack: {e}")
            return False
    
    def test_ipv6_connectivity(self) -> Dict[str, Any]:
        """Тестирование IPv6 подключения"""
        results = {
            "ipv6_dns_resolution": False,
            "ipv6_tcp_connectivity": False,
            "ipv6_http_connectivity": False,
            "dual_stack_support": False,
            "test_timestamp": time.time()
        }
        
        try:
            # Проверка IPv6 DNS разрешения
            try:
                socket.getaddrinfo("www.google.com", 80, socket.AF_INET6)
                results["ipv6_dns_resolution"] = True
                logger.info("IPv6 DNS resolution test passed")
            except:
                logger.warning("IPv6 DNS resolution test failed")
            
            # Проверка IPv6 TCP подключения
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(("2001:4860:4860::8888", 80))
                sock.close()
                if result == 0:
                    results["ipv6_tcp_connectivity"] = True
                    logger.info("IPv6 TCP connectivity test passed")
            except:
                logger.warning("IPv6 TCP connectivity test failed")
            
            # Проверка IPv6 HTTP подключения
            try:
                response = requests.get("https://www.google.com", timeout=10)
                if response.status_code == 200:
                    results["ipv6_http_connectivity"] = True
                    logger.info("IPv6 HTTP connectivity test passed")
            except:
                logger.warning("IPv6 HTTP connectivity test failed")
            
            # Проверка dual-stack поддержки
            try:
                # Проверка IPv4
                socket.gethostbyname("www.google.com")
                # Проверка IPv6
                socket.getaddrinfo("www.google.com", 80, socket.AF_INET6)
                results["dual_stack_support"] = True
                logger.info("Dual-stack support test passed")
            except:
                logger.warning("Dual-stack support test failed")
            
        except Exception as e:
            logger.error(f"Error testing IPv6 connectivity: {e}")
        
        return results

# Глобальный экземпляр
_ipv6_manager = None

def get_ipv6_manager() -> IPv6Manager:
    """Получение глобального экземпляра IPv6Manager"""
    global _ipv6_manager
    if _ipv6_manager is None:
        _ipv6_manager = IPv6Manager()
    return _ipv6_manager

if __name__ == "__main__":
    # Тестирование IPv6 менеджера
    print("Testing XVPN IPv6 Manager...")
    
    manager = get_ipv6_manager()
    
    # Проверка поддержки IPv6
    print(f"IPv6 supported: {manager.is_ipv6_supported()}")
    
    # Получение статуса подключения
    status = manager.get_ipv6_connectivity_status()
    print(f"IPv6 status: {status}")
    
    # Тестирование подключения
    connectivity = manager.test_ipv6_connectivity()
    print(f"IPv6 connectivity: {connectivity}")
    
    print("IPv6 Manager test completed")