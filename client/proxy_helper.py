#!/usr/bin/env python3
"""
Proxy Helper for XVPN Client
Утилиты для управления прокси-соединениями
"""

import subprocess
import os
import time
import socket
import random
import json
import threading
from pathlib import Path
from typing import Dict, Optional, Any

def find_free_port():
    """Поиск свободного порта"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def start_socks_proxy(target_host="127.0.0.1", target_port=1080):
    """Запуск SOCKS5 прокси для обхода ограничений"""
    # В реальной реализации это может быть часть Xray или отдельный прокси-сервер
    # Для демонстрации будем использовать заглушку

    # Находим свободный порт
    proxy_port = find_free_port()

    # В реальном приложении тут будет запуск SOCKS-прокси
    # через Xray или специализированное ПО
    print(f"Starting SOCKS proxy at 127.0.0.1:{proxy_port} -> {target_host}:{target_port}")

    # Пока возвращаем порт, к которому можно подключиться
    return proxy_port

def start_http_proxy(target_host="127.0.0.1", target_port=8080):
    """Запуск HTTP прокси"""
    # Находим свободный порт
    proxy_port = find_free_port()

    # В реальном приложении тут будет запуск HTTP-прокси
    print(f"Starting HTTP proxy at 127.0.0.1:{proxy_port} -> {target_host}:{target_port}")

    # Пока возвращаем порт, к которому можно подключиться
    return proxy_port

def configure_system_proxy(socks_port=None, http_port=None):
    """Настройка системного прокси (Linux)"""
    # В Linux можно настроить через переменные окружения
    if socks_port:
        os.environ['ALL_PROXY'] = f'socks5://127.0.0.1:{socks_port}'
        os.environ['all_proxy'] = f'socks5://127.0.0.1:{socks_port}'

    if http_port:
        os.environ['http_proxy'] = f'http://127.0.0.1:{http_port}'
        os.environ['https_proxy'] = f'http://127.0.0.1:{http_port}'

    print("System proxy configured")
    return True

def test_proxy_connection(proxy_host, proxy_port, test_url="https://api.ipify.org"):
    """Тестирование соединения через прокси"""
    try:
        # В реальной реализации тут будет тестирование через прокси
        # Для демонстрации просто проверим возможность подключения
        import urllib.request
        import urllib.parse

        # Настройка прокси для urllib
        proxy_handler = urllib.request.ProxyHandler({
              'http': f'http://{proxy_host}:{proxy_port}',
              'https': f'http://{proxy_host}:{proxy_port}'
        })

        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)

        response = urllib.request.urlopen(test_url, timeout=10)
        return True
    except:
        return False

class ProxyModeManager:
    """Продвинутый менеджер режимов прокси с поддержкой различных режимов"""

    def __init__(self):
        self.socks_port = None
        self.http_port = None
        self.transparent_proxy_port = None
        self.active_mode = "tun"  # tun, socks5, http, transparent, auto
        self.proxy_process = None
        self.config_file = os.path.expanduser("~/chatvpn/client/proxy_config.json")
        self.load_config()

    def load_config(self):
        """Загрузка конфигурации прокси"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.socks_port = config.get('socks_port')
                    self.http_port = config.get('http_port')
                    self.transparent_proxy_port = config.get('transparent_proxy_port')
                    self.active_mode = config.get('active_mode', 'tun')
        except Exception as e:
            print(f"Error loading proxy config: {e}")

    def save_config(self):
        """Сохранение конфигурации прокси"""
        try:
            config = {
                'socks_port': self.socks_port,
                'http_port': self.http_port,
                'transparent_proxy_port': self.transparent_proxy_port,
                'active_mode': self.active_mode
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving proxy config: {e}")

    def start_proxy_mode(self, mode="socks", **kwargs):
        """
        Запуск прокси-режима
        
        Режимы:
        - tun: стандартный VPN туннель (по умолчанию)
        - socks5: SOCKS5 прокси
        - http: HTTP прокси
        - transparent: прозрачный прокси (чесья iptables)
        - auto: автоматический выбор режима
        """
        # Остановка текущего режима
        self.stop_proxy_mode()
        
        if mode == "socks5":
            port = kwargs.get('port', None)
            self.socks_port = start_socks_proxy(port=port)
            configure_system_proxy(socks_port=self.socks_port)
            self.active_mode = "socks5"
            
        elif mode == "http":
            port = kwargs.get('port', None)
            self.http_port = start_http_proxy(port=port)
            configure_system_proxy(http_port=self.http_port)
            self.active_mode = "http"
            
        elif mode == "transparent":
            self.transparent_proxy_port = self._setup_transparent_proxy(**kwargs)
            self.active_mode = "transparent"
            
        elif mode == "auto":
            # Автоматический выбор режима на основе условий
            self.active_mode = self._auto_select_mode(**kwargs)
            
        else:
            raise ValueError(f"Unknown proxy mode: {mode}")
        
        self.save_config()
        return self.get_proxy_info()

    def _setup_transparent_proxy(self, **kwargs):
        """Настройка прозрачного прокси через iptables"""
        try:
            # Находим свободный порт для прозрачного прокси
            port = find_free_port()
            
            # Это упрощенная реализация
            # В реальной системе здесь будет настройка iptables для перехвата трафика
            print(f"Setting up transparent proxy on port {port}")
            
            # Пример настройки iptables (требует root прав)
            # iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port {port}
            # iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port {port}
            
            return port
            
        except Exception as e:
            print(f"Error setting up transparent proxy: {e}")
            return None

    def _auto_select_mode(self, **kwargs):
        """Автоматический выбор режима прокси"""
        # Логика автоматического выбора
        # Например, если есть ограничение на порт 443, используем прозрачный прокси
        # Если нужна совместимость с IPv6, используем SOCKS5
        # и т.д.
        
        default_mode = "socks5"
        print(f"Auto-selecting proxy mode: {default_mode}")
        return default_mode

    def stop_proxy_mode(self):
        """Остановка прокси-режима"""
        # Настройка обратно на прямое подключение
        if 'ALL_PROXY' in os.environ:
            del os.environ['ALL_PROXY']
        if 'all_proxy' in os.environ:
            del os.environ['all_proxy']
        if 'http_proxy' in os.environ:
            del os.environ['http_proxy']
        if 'https_proxy' in os.environ:
            del os.environ['https_proxy']

        self.active_mode = "tun"
        self.socks_port = None
        self.http_port = None
        self.transparent_proxy_port = None
        print("Proxy mode stopped")
        self.save_config()

    def get_proxy_info(self):
        """Получение информации о прокси"""
        return {
            "mode": self.active_mode,
            "socks_port": self.socks_port,
            "http_port": self.http_port,
            "transparent_proxy_port": self.transparent_proxy_port,
            "config_file": self.config_file
        }

    def test_connectivity(self, test_urls=None):
        """Тестирование connectivity через текущий прокси"""
        if test_urls is None:
            test_urls = [
                "https://api.ipify.org",
                "https://httpbin.org/ip",
                "https://www.google.com"
            ]
        
        results = {}
        
        for url in test_urls:
            try:
                response = self._make_request_through_proxy(url)
                results[url] = {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                results[url] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results

    def _make_request_through_proxy(self, url):
        """Выполнение запроса через текущий прокси"""
        import requests
        
        proxies = {}
        
        if self.active_mode == "socks5" and self.socks_port:
            proxies = {
                'http': f'socks5h://127.0.0.1:{self.socks_port}',
                'https': f'socks5h://127.0.0.1:{self.socks_port}'
            }
        elif self.active_mode == "http" and self.http_port:
            proxies = {
                'http': f'http://127.0.0.1:{self.http_port}',
                'https': f'http://127.0.0.1:{self.http_port}'
            }
        
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response

    def switch_mode(self, new_mode, **kwargs):
        """Переключение между режимами прокси"""
        if new_mode == self.active_mode:
            print(f"Already in {new_mode} mode")
            return self.get_proxy_info()
        
        print(f"Switching from {self.active_mode} to {new_mode}")
        return self.start_proxy_mode(new_mode, **kwargs)

    def get_mode_description(self, mode=None):
        """Получение описания режима прокси"""
        if mode is None:
            mode = self.active_mode
        
        descriptions = {
            "tun": "Стандартный VPN туннель (режим по умолчанию)",
            "socks5": "SOCKS5 прокси - универсальный режим для всех протоколов",
            "http": "HTTP прокси - оптимизирован для веб-трафика",
            "transparent": "Прозрачный прокси - автоматический перехват трафика",
            "auto": "Автоматический выбор режима на основе условий"
        }
        
        return descriptions.get(mode, "Неизвестный режим")

if __name__ == "__main__":
    # Пример использования
    proxy_manager = ProxyModeManager()

    print("Starting SOCKS proxy...")
    port = proxy_manager.start_proxy_mode("socks")
    print(f"SOCKS proxy running on port {port}")

    print(f"\nProxy info: {proxy_manager.get_proxy_info()}")

    # Выключение прокси
    proxy_manager.stop_proxy_mode()
    print(f"Proxy info after stop: {proxy_manager.get_proxy_info()}")
