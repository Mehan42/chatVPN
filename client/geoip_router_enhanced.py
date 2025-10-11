#!/usr/bin/env python3
"""
Расширенный GeoIP роутер с онлайн-обновлением и DNS-резолвингом
"""
import sys
import json
import ipaddress
import socket
import requests
import time
import os
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from urllib.parse import urlparse
import re

# Базовые страны СНГ и дружественные регионы (РУ сегмент)
RU_COUNTRIES = {"RU", "BY", "KZ", "KG", "MD", "TJ", "TM", "UZ", "AM", "AZ", "GE"}

# Локальные сети (всегда напрямую)
LOCAL_NETWORKS = [
    "127.0.0.0/8",      # Loopback
    "10.0.0.0/8",       # Private network
    "172.16.0.0/12",    # Private network
    "192.168.0.0/16",   # Private network
    "169.254.0.0/16",   # Link-local
    "::1/128",          # IPv6 loopback
    "fc00::/7",         # IPv6 unique local
    "fe80::/10",        # IPv6 link-local
]

class IPCache:
    """Кэш IP → страна для повышения производительности"""
    
    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, ip: str) -> Optional[str]:
        """Получение страны для IP из кэша"""
        if ip in self.cache:
            country, timestamp = self.cache[ip]
            if time.time() - timestamp < self.ttl:
                return country
            else:
                del self.cache[ip]
        return None
    
    def set(self, ip: str, country: str):
        """Сохранение страны для IP в кэш"""
        # Очистка старых записей если нужно
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[ip] = (country, time.time())

class CIDRMatcher:
    """Сопоставитель CIDR масок для определения стран"""
    
    def __init__(self):
        self.networks: List[Tuple[ipaddress.IPv4Network, str]] = []
        self.ipv6_networks: List[Tuple[ipaddress.IPv6Network, str]] = []
        self._load_static_cidr_data()
    
    def _load_static_cidr_data(self):
        """Загрузка статических CIDR данных"""
        # Россия (основные диапазоны)
        ru_cidrs = [
            "77.0.0.0/8", "80.0.0.0/8", "81.0.0.0/8", "82.0.0.0/8",
            "83.0.0.0/8", "84.0.0.0/8", "85.0.0.0/8", "86.0.0.0/8",
            "87.0.0.0/8", "88.0.0.0/8", "89.0.0.0/8", "90.0.0.0/8",
            "91.0.0.0/8", "92.0.0.0/8", "93.0.0.0/8", "94.0.0.0/8",
            "95.0.0.0/8", "176.0.0.0/8", "178.0.0.0/8", "185.0.0.0/8",
            "188.0.0.0/8", "193.0.0.0/8", "194.0.0.0/8", "195.0.0.0/8"
        ]
        
        # Другие страны СНГ
        cis_cidrs = {
            "UA": ["37.0.0.0/8", "31.0.0.0/8"],
            "BY": ["178.0.0.0/8"],
            "KZ": ["178.0.0.0/8"],  # Частично
            "AM": ["46.0.0.0/8"],
            "AZ": ["5.0.0.0/8"],
            "GE": ["31.0.0.0/8"],   # Частично
            "KG": ["178.0.0.0/8"]   # Частично
        }
        
        # Загрузка RU сетей
        for cidr in ru_cidrs:
            try:
                network = ipaddress.IPv4Network(cidr)
                self.networks.append((network, "RU"))
            except ValueError:
                pass
        
        # Загрузка сетей других стран СНГ
        for country, cidrs in cis_cidrs.items():
            for cidr in cidrs:
                try:
                    network = ipaddress.IPv4Network(cidr)
                    self.networks.append((network, country))
                except ValueError:
                    pass
    
    def add_network(self, cidr: str, country: str):
        """Добавление новой сети в сопоставитель"""
        try:
            if ':' in cidr:
                # IPv6
                network = ipaddress.IPv6Network(cidr)
                self.ipv6_networks.append((network, country))
            else:
                # IPv4
                network = ipaddress.IPv4Network(cidr)
                self.networks.append((network, country))
        except ValueError:
            pass
    
    def match_ip(self, ip_str: str) -> Optional[str]:
        """Сопоставление IP с известными сетями"""
        try:
            ip = ipaddress.ip_address(ip_str)
            
            if isinstance(ip, ipaddress.IPv4Address):
                # Поиск в IPv4 сетях
                for network, country in self.networks:
                    if ip in network:
                        return country
            else:
                # Поиск в IPv6 сетях
                for network, country in self.ipv6_networks:
                    if ip in network:
                        return country
            
            return None
        except ValueError:
            return None

class DNSResolver:
    """DNS резолвер для определения стран по доменам"""
    
    def __init__(self, cache: IPCache, proxy_manager=None):
        self.cache = cache
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (XVPN Client/3.1.0) AppleWebKit/537.36'
        })
    
    def resolve_domain(self, domain: str) -> List[str]:
        """Резолвинг домена в IP адреса"""
        try:
            # Прямой DNS резолвинг
            ips = socket.getaddrinfo(domain, None, socket.AF_UNSPEC)
            ip_list = []
            for family, type_, proto, canonname, sockaddr in ips:
                ip_list.append(sockaddr[0])
            return list(set(ip_list))  # Удаление дубликатов
        except Exception:
            return []
    
    def resolve_with_proxy(self, domain: str) -> List[str]:
        """Резолвинг домена через прокси (если доступен)"""
        if not self.proxy_manager:
            return self.resolve_domain(domain)
        
        try:
            # Использование прокси для резолвинга
            proxies = self.proxy_manager.get_working_proxies()
            if not proxies:
                return self.resolve_domain(domain)
            
            # Попытка резолвинга через первый рабочий прокси
            proxy = proxies[0]
            resolver_url = f"http://{proxy}/dns-query?name={domain}&type=A"
            
            response = self.session.get(resolver_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [answer['data'] for answer in data.get('Answer', [])]
            
            return []
        except Exception:
            return self.resolve_domain(domain)

class OnlineGeoIPService:
    """Онлайн сервисы GeoIP для получения актуальных данных"""
    
    def __init__(self, cache: IPCache, proxy_manager=None):
        self.cache = cache
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (XVPN Client/3.1.0) AppleWebKit/537.36'
        })
        
        # Список онлайн сервисов GeoIP
        self.services = [
            {
                'name': 'ip-api',
                'url': 'http://ip-api.com/json/{ip}',
                'field': 'countryCode'
            },
            {
                'name': 'ipinfo',
                'url': 'https://ipinfo.io/{ip}/json',
                'field': 'country'
            }
        ]
    
    def get_country_online(self, ip: str) -> Optional[str]:
        """Получение страны для IP через онлайн сервисы"""
        # Проверка кэша
        cached_country = self.cache.get(ip)
        if cached_country:
            return cached_country
        
        # Попытка через онлайн сервисы
        for service in self.services:
            try:
                url = service['url'].format(ip=ip)
                proxies = {}
                
                # Использование прокси если доступен
                if self.proxy_manager:
                    proxy_list = self.proxy_manager.get_working_proxies()
                    if proxy_list:
                        proxy_addr = proxy_list[0]
                        proxies = {
                            'http': f'http://{proxy_addr}',
                            'https': f'http://{proxy_addr}'
                        }
                
                response = self.session.get(url, timeout=10, proxies=proxies)
                if response.status_code == 200:
                    data = response.json()
                    country = data.get(service['field'])
                    if country:
                        # Сохранение в кэш
                        self.cache.set(ip, country)
                        return country
                        
            except Exception:
                continue
        
        return None

class ProxyManager:
    """Управление прокси для обхода ограничений"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.working_proxies: Set[str] = set()
        self.last_check = 0
        self.check_interval = 300  # 5 минут
    
    def add_proxy(self, proxy: str):
        """Добавление прокси в список"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
    
    def load_proxies_from_file(self, filepath: str):
        """Загрузка прокси из файла"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith('#'):
                        self.add_proxy(proxy)
        except Exception:
            pass
    
    def check_proxy(self, proxy: str) -> bool:
        """Проверка работоспособности прокси"""
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxies, 
                                  timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def update_working_proxies(self):
        """Обновление списка рабочих прокси"""
        if time.time() - self.last_check < self.check_interval:
            return
        
        working = set()
        for proxy in self.proxies:
            if self.check_proxy(proxy):
                working.add(proxy)
        
        self.working_proxies = working
        self.last_check = time.time()
    
    def get_working_proxies(self) -> List[str]:
        """Получение списка рабочих прокси"""
        self.update_working_proxies()
        return list(self.working_proxies)

class EnhancedGeoIPRouter:
    """Расширенный маршрутизатор трафика по географическим признакам"""
    
    def __init__(self):
        """Инициализация расширенного роутера"""
        self.ip_cache = IPCache()
        self.cidr_matcher = CIDRMatcher()
        self.proxy_manager = ProxyManager()
        self.online_geoip = OnlineGeoIPService(self.ip_cache, self.proxy_manager)
        self.dns_resolver = DNSResolver(self.ip_cache, self.proxy_manager)
        
        # Загрузка локальных сетей
        self.local_networks = []
        for network_str in LOCAL_NETWORKS:
            try:
                network = ipaddress.ip_network(network_str)
                self.local_networks.append(network)
            except ValueError:
                pass
    
    def is_ru_destination(self, destination: str) -> bool:
        """
        Проверка, является ли назначение российским (или СНГ)
        
        Args:
            destination: IP адрес или доменное имя
            
        Returns:
            True если назначение принадлежит России или СНГ, False если нет
        """
        try:
            # Проверка, является ли destination IP адресом
            if self._is_valid_ip(destination):
                return self._is_ru_ip(destination)
            else:
                # destination - доменное имя
                return self._is_ru_domain(destination)
                
        except Exception:
            # В случае ошибки считаем неРУ для безопасности
            return False
    
    def _is_valid_ip(self, address: str) -> bool:
        """Проверка, является ли строка корректным IP адресом"""
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            return False
    
    def _is_ru_ip(self, ip_address: str) -> bool:
        """Проверка, является ли IP адрес российским"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Проверка локальных сетей
            if self._is_local_ip(ip):
                return True
            
            # Проверка через CIDR matcher
            country = self.cidr_matcher.match_ip(ip_address)
            if country and country in RU_COUNTRIES:
                return True
            
            # Проверка через онлайн сервисы
            country = self.online_geoip.get_country_online(ip_address)
            if country and country in RU_COUNTRIES:
                return True
            
            # Все остальное - неРУ трафик
            return False
            
        except Exception:
            return False
    
    def _is_ru_domain(self, domain: str) -> bool:
        """Проверка, является ли домен российским"""
        try:
            # Проверка по TLD
            if domain.endswith(('.ru', '.su', '.рф')):
                return True
            
            # Проверка по списку известных RU доменов
            ru_domains = {
                'yandex.ru', 'mail.ru', 'vk.com', 'ok.ru', 'rambler.ru',
                'rbc.ru', 'lenta.ru', 'ria.ru', 'tass.ru', 'regnum.ru'
            }
            
            if domain in ru_domains:
                return True
            
            # Резолвинг домена и проверка IP адресов
            ips = self.dns_resolver.resolve_domain(domain)
            for ip in ips:
                if self._is_ru_ip(ip):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_local_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Проверка, является ли IP адрес локальным"""
        for network in self.local_networks:
            if ip in network:
                return True
        return False
    
    def get_detailed_routing_info(self, destination: str) -> Dict[str, any]:
        """
        Получение детальной информации о маршрутизации для назначения
        
        Args:
            destination: IP адрес или доменное имя
            
        Returns:
            Словарь с информацией о маршрутизации
        """
        try:
            is_ip = self._is_valid_ip(destination)
            
            if is_ip:
                # Обработка IP адреса
                ip = destination
                country = self._get_country_for_ip(ip)
                is_ru = self._is_ru_ip(ip)
                reason = self._get_ip_routing_reason(ip, country, is_ru)
                
                return {
                    "destination": ip,
                    "type": "ip",
                    "country": country,
                    "direct": is_ru,
                    "reason": reason,
                    "ip_version": "ipv6" if ':' in ip else "ipv4"
                }
            else:
                # Обработка доменного имени
                domain = destination
                is_ru = self._is_ru_domain(domain)
                tld_check = domain.endswith(('.ru', '.su', '.рф'))
                ips = self.dns_resolver.resolve_domain(domain)
                
                # Проверка IP адресов домена
                ip_countries = []
                for ip in ips:
                    country = self._get_country_for_ip(ip)
                    ip_countries.append({"ip": ip, "country": country})
                
                return {
                    "destination": domain,
                    "type": "domain",
                    "direct": is_ru,
                    "reason": "ru_tld" if tld_check else "ru_ip_resolved" if is_ru else "non_ru_destination",
                    "tld": domain.split('.')[-1] if '.' in domain else "",
                    "resolved_ips": ip_countries,
                    "ip_count": len(ips)
                }
                
        except Exception as e:
            return {
                "destination": destination,
                "type": "unknown",
                "direct": False,
                "reason": f"error_processing: {str(e)}",
                "error": str(e)
            }
    
    def _get_country_for_ip(self, ip_address: str) -> str:
        """Получение страны для IP адреса"""
        # Проверка через CIDR matcher
        country = self.cidr_matcher.match_ip(ip_address)
        if country:
            return country
        
        # Проверка через онлайн сервисы
        country = self.online_geoip.get_country_online(ip_address)
        if country:
            return country
        
        return "UNKNOWN"
    
    def _get_ip_routing_reason(self, ip: str, country: str, is_ru: bool) -> str:
        """Получение причины маршрутизации для IP"""
        if self._is_local_ip(ipaddress.ip_address(ip)):
            return "local_network"
        elif country in RU_COUNTRIES:
            return f"ru_country_{country}"
        elif country != "UNKNOWN":
            return f"foreign_country_{country}"
        else:
            return "unknown_country"

def main():
    """Главная точка входа"""
    if len(sys.argv) < 2:
        print("Использование: enhanced_geoip_router <destination> [--verbose]")
        print("")
        print("Примеры:")
        print("  enhanced_geoip_router 8.8.8.8          # Google DNS (неРУ)")
        print("  enhanced_geoip_router 77.88.8.8        # Yandex (РУ)")
        print("  enhanced_geoip_router yandex.ru        # Домен (РУ)")
        print("  enhanced_geoip_router google.com       # Домен (неРУ)")
        print("  enhanced_geoip_router ::1              # Loopback (напрямую)")
        sys.exit(1)
    
    # Получение назначения из аргументов
    destination = sys.argv[1].strip()
    
    # Создание роутера
    router = EnhancedGeoIPRouter()
    
    # Проверка verbose режима
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Получение детальной информации
    if verbose:
        info = router.get_detailed_routing_info(destination)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    # Определение маршрута
    is_ru = router.is_ru_destination(destination)
    
    # Возврат кода выхода
    # 0 - РУ трафик (идет напрямую)
    # 1 - неРУ трафик (проксируется)
    sys.exit(0 if is_ru else 1)

if __name__ == "__main__":
    main()