#!/usr/bin/env python3
"""
Автономный GeoIP роутер с встроенными зависимостями (PEX версия)
Разделение трафика на РУ и неРУ сегменты для XVPN клиента

Использование:
    ./geoip_router.pex <ip_address>
    
    Возвращает:
    - Код выхода 0: РУ трафик (идет напрямую)
    - Код выхода 1: неРУ трафик (проксируется)
    
Примеры:
    ./geoip_router.pex 8.8.8.8        # Возвращает 1 (неРУ)
    ./geoip_router.pex 77.88.8.8      # Возвращает 0 (РУ)
    ./geoip_router.pex ::1            # Возвращает 0 (локальный)
"""

import sys
import json
import ipaddress
from typing import Dict, List, Optional, Set
import os
from pathlib import Path

# Встроенные данные GeoIP (упрощенная реализация)
# Для production будет использоваться полноценная GeoIP база
GEOIP_DATA = {
    # Россия (основные диапазоны)
    "77.0.0.0/8": "RU",
    "80.0.0.0/8": "RU",
    "81.0.0.0/8": "RU",
    "82.0.0.0/8": "RU",
    "83.0.0.0/8": "RU",
    "84.0.0.0/8": "RU",
    "85.0.0.0/8": "RU",
    "86.0.0.0/8": "RU",
    "87.0.0.0/8": "RU",
    "88.0.0.0/8": "RU",
    "89.0.0.0/8": "RU",
    "90.0.0.0/8": "RU",
    "91.0.0.0/8": "RU",
    "92.0.0.0/8": "RU",
    "93.0.0.0/8": "RU",
    "94.0.0.0/8": "RU",
    "95.0.0.0/8": "RU",
    "176.0.0.0/8": "RU",
    "178.0.0.0/8": "RU",
    "185.0.0.0/8": "RU",
    "188.0.0.0/8": "RU",
    "193.0.0.0/8": "RU",
    "194.0.0.0/8": "RU",
    "195.0.0.0/8": "RU",
    
    # Украина
    "37.0.0.0/8": "UA",
    "31.0.0.0/8": "UA",
    
    # Беларусь
    "178.0.0.0/8": "BY",  # Частично
    
    # Казахстан
    "178.0.0.0/8": "KZ",  # Частично
    
    # Армения
    "46.0.0.0/8": "AM",   # Частично
    
    # Азербайджан
    "5.0.0.0/8": "AZ",    # Частично
    
    # Грузия
    "31.0.0.0/8": "GE",   # Частично
    
    # Киргизия
    "178.0.0.0/8": "KG",  # Частично
}

# Страны СНГ и дружественные регионы (РУ сегмент)
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

class GeoIPRouter:
    """Маршрутизатор трафика по географическим признакам"""
    
    def __init__(self):
        """Инициализация роутера с предварительной обработкой сетей"""
        # Преобразуем строки в объекты IP-сетей для быстрого поиска
        self.ru_networks = []
        self.local_networks = []
        
        # Обработка RU сетей из GEOIP_DATA
        for network_str, country in GEOIP_DATA.items():
            if country in RU_COUNTRIES:
                try:
                    network = ipaddress.ip_network(network_str)
                    self.ru_networks.append(network)
                except ValueError:
                    # Игнорируем некорректные сети
                    pass
        
        # Обработка локальных сетей
        for network_str in LOCAL_NETWORKS:
            try:
                network = ipaddress.ip_network(network_str)
                self.local_networks.append(network)
            except ValueError:
                # Игнорируем некорректные сети
                pass
    
    def is_ru_destination(self, ip_address: str) -> bool:
        """
        Проверка, является ли IP адрес российским (или СНГ)
        
        Args:
            ip_address: IP адрес назначения
            
        Returns:
            True если адрес принадлежит России или СНГ, False если нет
        """
        try:
            # Парсинг IP адреса
            ip = ipaddress.ip_address(ip_address)
            
            # Проверка локальных сетей (всегда напрямую)
            if self._is_local_ip(ip):
                return True
            
            # Проверка RU сетей
            if self._is_ru_network_ip(ip):
                return True
            
            # Все остальное - неРУ трафик
            return False
            
        except ValueError:
            # Некорректный IP адрес - считаем неРУ для безопасности
            return False
        except Exception:
            # Любая другая ошибка - считаем неРУ для безопасности
            return False
    
    def _is_local_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """
        Проверка, является ли IP адрес локальным
        
        Args:
            ip: IP адрес
            
        Returns:
            True если адрес локальный, False если нет
        """
        for network in self.local_networks:
            if ip in network:
                return True
        return False
    
    def _is_ru_network_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """
        Проверка, принадлежит ли IP адрес российской (или СНГ) сети
        
        Args:
            ip: IP адрес
            
        Returns:
            True если адрес принадлежит RU сети, False если нет
        """
        for network in self.ru_networks:
            if ip in network:
                return True
        return False
    
    def get_country_for_ip(self, ip_address: str) -> Optional[str]:
        """
        Получение страны для IP адреса
        
        Args:
            ip_address: IP адрес
            
        Returns:
            Код страны (ISO 3166-1 alpha-2) или None если не определено
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Проверка локальных адресов
            if self._is_local_ip(ip):
                return "LOCAL"
            
            # Поиск в GEOIP_DATA
            for network_str, country in GEOIP_DATA.items():
                try:
                    network = ipaddress.ip_network(network_str)
                    if ip in network:
                        return country
                except ValueError:
                    continue
            
            return "UNKNOWN"
            
        except ValueError:
            return "INVALID"
        except Exception:
            return "ERROR"
    
    def get_detailed_routing_info(self, ip_address: str) -> Dict[str, any]:
        """
        Получение детальной информации о маршрутизации для IP адреса
        
        Args:
            ip_address: IP адрес назначения
            
        Returns:
            Словарь с информацией о маршрутизации
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            country = self.get_country_for_ip(ip_address)
            is_ru = self.is_ru_destination(ip_address)
            
            return {
                "ip": str(ip),
                "country": country,
                "direct": is_ru,
                "reason": self._get_routing_reason(ip, country, is_ru),
                "type": "ipv6" if ip.version == 6 else "ipv4"
            }
            
        except Exception as e:
            return {
                "ip": ip_address,
                "country": "ERROR",
                "direct": False,
                "reason": f"Ошибка обработки: {str(e)}",
                "type": "unknown",
                "error": str(e)
            }
    
    def _get_routing_reason(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address, 
                          country: str, is_ru: bool) -> str:
        """
        Получение причины маршрутизации
        
        Args:
            ip: IP адрес
            country: Страна
            is_ru: Флаг RU маршрутизации
            
        Returns:
            Причина маршрутизации
        """
        if self._is_local_ip(ip):
            return "local_network"
        elif country in RU_COUNTRIES:
            return f"ru_country_{country}"
        elif country == "LOCAL":
            return "local_address"
        elif country == "UNKNOWN":
            return "unknown_country"
        elif country == "INVALID":
            return "invalid_ip"
        elif country == "ERROR":
            return "processing_error"
        else:
            return f"foreign_country_{country}"

def main():
    """Главная точка входа"""
    # Проверка аргументов командной строки
    if len(sys.argv) < 2:
        print("Использование: geoip_router <ip_address>")
        print("")
        print("Примеры:")
        print("  geoip_router 8.8.8.8        # Google DNS (неРУ)")
        print("  geoip_router 77.88.8.8      # Yandex (РУ)")
        print("  geoip_router ::1            # Loopback (напрямую)")
        sys.exit(1)
    
    # Получение IP адреса из аргументов
    ip_address = sys.argv[1].strip()
    
    # Создание роутера
    router = GeoIPRouter()
    
    # Получение детальной информации
    info = router.get_detailed_routing_info(ip_address)
    
    # Вывод информации (для отладки)
    if "--verbose" in sys.argv or "-v" in sys.argv:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    # Определение маршрута
    is_ru = router.is_ru_destination(ip_address)
    
    # Возврат кода выхода
    # 0 - РУ трафик (идет напрямую)
    # 1 - неРУ трафик (проксируется)
    sys.exit(0 if is_ru else 1)

if __name__ == "__main__":
    main()