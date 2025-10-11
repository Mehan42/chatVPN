#!/usr/bin/env python3
"""
Тесты для GeoIP роутера (PEX версия)
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем директорию клиента в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

from geoip_router_pex import GeoIPRouter

class TestGeoIPRouter(unittest.TestCase):
    """Тесты для GeoIP роутера"""
    
    def setUp(self):
        """Подготовка к тестам"""
        self.router = GeoIPRouter()
    
    def test_ru_ip_detection(self):
        """Тест определения российских IP адресов"""
        # Yandex IP (77.88.8.8) - должен быть определен как RU
        self.assertTrue(self.router.is_ru_destination("77.88.8.8"))
        
        # Mail.ru IP (77.88.8.8) - должен быть определен как RU
        self.assertTrue(self.router.is_ru_destination("77.88.8.8"))
        
        # VK IP (87.240.128.0/18) - должен быть определен как RU
        self.assertTrue(self.router.is_ru_destination("87.240.128.1"))
    
    def test_non_ru_ip_detection(self):
        """Тест определения неРУ IP адресов"""
        # Google DNS (8.8.8.8) - должен быть определен как неРУ
        self.assertFalse(self.router.is_ru_destination("8.8.8.8"))
        
        # Cloudflare DNS (1.1.1.1) - должен быть определен как неРУ
        self.assertFalse(self.router.is_ru_destination("1.1.1.1"))
        
        # OpenDNS (208.67.222.222) - должен быть определен как неРУ
        self.assertFalse(self.router.is_ru_destination("208.67.222.222"))
    
    def test_local_ip_detection(self):
        """Тест определения локальных IP адресов"""
        # Loopback IPv4
        self.assertTrue(self.router.is_ru_destination("127.0.0.1"))
        
        # Loopback IPv6
        self.assertTrue(self.router.is_ru_destination("::1"))
        
        # Private network IPv4
        self.assertTrue(self.router.is_ru_destination("192.168.1.1"))
        self.assertTrue(self.router.is_ru_destination("10.0.0.1"))
        self.assertTrue(self.router.is_ru_destination("172.16.0.1"))
    
    def test_invalid_ip_handling(self):
        """Тест обработки некорректных IP адресов"""
        # Некорректные IP адреса
        self.assertFalse(self.router.is_ru_destination("invalid.ip"))
        self.assertFalse(self.router.is_ru_destination("999.999.999.999"))
        self.assertFalse(self.router.is_ru_destination(""))
    
    def test_country_detection(self):
        """Тест определения стран"""
        # Российские IP
        self.assertEqual(self.router.get_country_for_ip("77.88.8.8"), "RU")
        
        # Локальные IP
        self.assertEqual(self.router.get_country_for_ip("127.0.0.1"), "LOCAL")
        self.assertEqual(self.router.get_country_for_ip("::1"), "LOCAL")
        
        # Некорректные IP
        self.assertEqual(self.router.get_country_for_ip("invalid.ip"), "INVALID")
        
        # Неизвестные IP
        self.assertEqual(self.router.get_country_for_ip("8.8.8.8"), "UNKNOWN")
    
    def test_detailed_routing_info(self):
        """Тест получения детальной информации о маршрутизации"""
        # Российский IP
        info_ru = self.router.get_detailed_routing_info("77.88.8.8")
        self.assertEqual(info_ru["ip"], "77.88.8.8")
        self.assertEqual(info_ru["country"], "RU")
        self.assertTrue(info_ru["direct"])
        self.assertIn("ru_country_", info_ru["reason"])
        
        # НеРУ IP
        info_non_ru = self.router.get_detailed_routing_info("8.8.8.8")
        self.assertEqual(info_non_ru["ip"], "8.8.8.8")
        self.assertEqual(info_non_ru["country"], "UNKNOWN")
        self.assertFalse(info_non_ru["direct"])
        self.assertEqual(info_non_ru["reason"], "unknown_country")
        
        # Локальный IP
        info_local = self.router.get_detailed_routing_info("127.0.0.1")
        self.assertEqual(info_local["ip"], "127.0.0.1")
        self.assertEqual(info_local["country"], "LOCAL")
        self.assertTrue(info_local["direct"])
        self.assertEqual(info_local["reason"], "local_network")
        
        # IPv6
        info_ipv6 = self.router.get_detailed_routing_info("::1")
        self.assertEqual(info_ipv6["ip"], "::1")
        self.assertEqual(info_ipv6["country"], "LOCAL")
        self.assertTrue(info_ipv6["direct"])
        self.assertEqual(info_ipv6["reason"], "local_address")
        self.assertEqual(info_ipv6["type"], "ipv6")
    
    def test_ru_networks_loading(self):
        """Тест загрузки RU сетей"""
        # Проверяем, что RU сети загружены
        self.assertGreater(len(self.router.ru_networks), 0)
        self.assertGreater(len(self.router.local_networks), 0)
    
    def test_network_membership(self):
        """Тест принадлежности к сетям"""
        # Проверяем, что RU IP принадлежит RU сети
        ru_network_found = False
        for network in self.router.ru_networks:
if __name__ == "__main__":
    unittest.main()