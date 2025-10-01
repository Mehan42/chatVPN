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
from pathlib import Path

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
    """Менеджер режимов прокси"""

    def __init__(self):
        self.socks_port = None
        self.http_port = None
        self.active_mode = "tun"  # tun, proxy, auto
        self.proxy_process = None

    def start_proxy_mode(self, mode="socks"):
        """Запуск прокси-режима"""
        if mode == "socks":
            self.socks_port = start_socks_proxy()
            configure_system_proxy(socks_port=self.socks_port)
            self.active_mode = "proxy_socks"
            return self.socks_port
        elif mode == "http":
            self.http_port = start_http_proxy()
            configure_system_proxy(http_port=self.http_port)
            self.active_mode = "proxy_http"
            return self.http_port
        else:
            return None

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
        print("Proxy mode stopped")

    def get_proxy_info(self):
        """Получение информации о прокси"""
        return {
            "mode": self.active_mode,
            "socks_port": self.socks_port,
            "http_port": self.http_port
        }

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
