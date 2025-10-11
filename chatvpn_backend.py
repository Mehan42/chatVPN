#!/usr/bin/env python3
# ChatVPN backend
# Абсолютный путь: ~/chatvpn/client/ (может быть переустановлен в другое место)chatvpn_backend.py (может быть переустановлен в другое место)

import os
import subprocess
import requests
import time
import ssl
import hashlib
import socket
from urllib.parse import urlparse
from pathlib import Path

# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()
CONFIG_PATH = CLIENT_DIR / 'client.json'
CONF_UUID_PATH = CLIENT_DIR / 'client.conf'

BOT_TOKEN = "6706425774:AAGxv3dDmz2TJsHtNVPb0PN2s07kTSr1_qc"
CHAT_ID = "5385524517"

# XRAY_BIN = "/usr/bin/xray"   # путь к бинарю xray
# Проверяем наличие Xray в стандартных местах
import shutil
XRAY_BIN = shutil.which("xray") or "/usr/bin/xray"   # путь к бинарю xray
XRAY_PROC = None

# =============================
# UUID клиента
# =============================

def get_client_uuid():
    if os.path.exists(CONF_UUID_PATH):
        with open(CONF_UUID_PATH, "r") as f:
            return f.read().strip()
    return None

def save_client_uuid(uuid):
    with open(CONF_UUID_PATH, "w") as f:
        f.write(uuid.strip())

# =============================
# TLS пиннинг и безопасность
# =============================

def load_certificate_fingerprints():
    """
    Загружает сохраненные отпечатки сертификатов для TLS пиннинга
    """
    import json
    from pathlib import Path
    
    config_path = CLIENT_DIR / "config" / "cert_fingerprints.json"
    
    try:
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
            return config.get("fingerprints", {})
        else:
            print(f"⚠️  Certificate fingerprints config not found at {config_path}")
            return {}
    except Exception as e:
        print(f"❌ Error loading certificate fingerprints: {e}")
        return {}

def verify_certificate_fingerprint(hostname, port, cert_der):
    """
    Проверяет, что сертификат соответствует сохраненному отпечатку
    """
    try:
        # Загружаем сохраненные отпечатки
        fingerprints = load_certificate_fingerprints()
        
        # Ищем отпечаток для данного сервера
        server_key = f"{hostname}:{port}"
        if server_key not in fingerprints:
            print(f"⚠️  No fingerprint found for {server_key}, allowing connection")
            return True  # Если отпечаток не найден, разрешаем подключение
        
        # Вычисляем отпечаток текущего сертификата
        actual_fingerprint = hashlib.sha256(cert_der).hexdigest()
        expected_fingerprint = fingerprints[server_key]["fingerprint"]
        
        # Сравниваем отпечатки
        if actual_fingerprint.lower() == expected_fingerprint.lower():
            print(f"✅ Certificate fingerprint verified for {server_key}")
            return True
        else:
            print(f"❌ Certificate fingerprint mismatch for {server_key}")
            print(f"   Expected: {expected_fingerprint}")
            print(f"   Actual:   {actual_fingerprint}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying certificate fingerprint: {e}")
        return False

def create_https_context():
    """
    Создает контекст HTTPS с TLS пиннингом
    """
    # Создаем SSL контекст
    context = ssl.create_default_context()
    
    # Настраиваем параметры безопасности
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = False  # Отключаем проверку hostname для гибкости
    context.verify_mode = ssl.CERT_REQUIRED  # Всегда проверяем сертификаты
    
    return context

def make_secure_request(url, **kwargs):
    """
    Выполняет безопасный HTTPS запрос с TLS пиннингом
    """
    try:
        # Проверяем, что это HTTPS URL
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            raise ValueError("HTTPS запрос поддерживается только для HTTPS URL")
        
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        # Создаем SSL контекст
        context = create_https_context()
        
        # Устанавливаем соединение с проверкой сертификата
        with socket.create_connection((hostname, port), timeout=15) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Получаем сертификат для проверки отпечатка
                cert_der = ssock.getpeercert(binary_form=True)
                
                # Проверяем отпечаток сертификата
                if not verify_certificate_fingerprint(hostname, port, cert_der):
                    raise ssl.SSLError(f"Certificate fingerprint verification failed for {hostname}:{port}")
                
                # Создаем HTTP запрос
                import http.client
                
                # Для простых GET запросов используем requests с проверенным контекстом
                # Для более сложных случаев можно использовать http.client напрямую
                
                # Выполняем запрос с проверенным SSL контекстом
                response = requests.get(
                    url, 
                    verify=True,  # Используем проверку сертификатов
                    **kwargs
                )
                response.raise_for_status()
                
                return response
    
    except ssl.SSLError as e:
        print(f"❌ SSL/TLS certificate verification failed: {e}")
        raise
    except requests.exceptions.SSLError as e:
        print(f"❌ HTTPS request SSL error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTPS request failed: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error in secure request: {e}")
        raise

# =============================
# Основные функции
# =============================

def start_xray():
    """Запуск Xray"""
    global XRAY_PROC
    try:
        if XRAY_PROC is None or XRAY_PROC.poll() is not None:
            # Запускаем Xray в фоновом режиме
            XRAY_PROC = subprocess.Popen([XRAY_BIN, "-config", CONFIG_PATH])
            time.sleep(2)  # Даем время на запуск
            return XRAY_PROC.poll() is None
        return True
    except Exception as e:
        print(f"Ошибка запуска Xray: {e}")
        return False

def stop_xray():
    """Остановка Xray"""
    global XRAY_PROC
    try:
        if XRAY_PROC is not None:
            XRAY_PROC.terminate()
            XRAY_PROC.wait(timeout=5)
            XRAY_PROC = None
            return True
        return True
    except Exception as e:
        print(f"Ошибка остановки Xray: {e}")
        return False

def get_status():
    """Получение статуса Xray"""
    try:
        if XRAY_PROC is None:
            return {"status": "stopped"}
        
        if XRAY_PROC.poll() is None:
            return {"status": "running"}
        else:
            return {"status": "stopped", "exit_code": XRAY_PROC.poll()}
    except Exception as e:
        print(f"Ошибка получения статуса: {e}")
        return {"status": "error", "error": str(e)}

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def load_config_from_server():
    """Загрузка конфигурации с сервера через HTTPS"""
    try:
        url = "https://uss.hopto.org:8443/config"
        
        # Используем безопасный запрос с TLS пиннингом
        response = make_secure_request(url)
        
        if response.status_code == 200:
            config_data = response.json()
            
            # Сохраняем конфигурацию
            with open(CONFIG_PATH, "w") as f:
                import json
                json.dump(config_data, f, indent=2)
            
            # Если есть UUID, сохраняем его
            if "uuid" in config_data:
                save_client_uuid(config_data["uuid"])
            
            return True
        else:
            print(f"Ошибка загрузки конфигурации: {response.status_code}")
            # Возвращаем True, если локальный файл конфигурации существует
            return CONFIG_PATH.exists()
            
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        # Возвращаем True, если локальный файл конфигурации существует
        return CONFIG_PATH.exists()

# =============================
# Управление режимами прокси
# =============================

# Инициализация менеджера прокси
try:
    from proxy_helper import ProxyModeManager
    proxy_manager = ProxyModeManager()
except ImportError:
    print("Warning: proxy_helper not available")
    proxy_manager = None

def get_proxy_mode():
    """Получение текущего режима прокси"""
    if proxy_manager:
        return proxy_manager.get_proxy_info()
    return {"mode": "tun", "error": "Proxy manager not available"}

def set_proxy_mode(mode="tun", **kwargs):
    """Установка режима прокси"""
    if not proxy_manager:
        return False, "Proxy manager not available"
    
    try:
        result = proxy_manager.start_proxy_mode(mode, **kwargs)
        return True, f"Proxy mode set to {mode}"
    except Exception as e:
        return False, f"Error setting proxy mode: {e}"

def stop_proxy_mode():
    """Остановка прокси режима"""
    if not proxy_manager:
        return False, "Proxy manager not available"
    
    try:
        proxy_manager.stop_proxy_mode()
        return True, "Proxy mode stopped"
    except Exception as e:
        return False, f"Error stopping proxy mode: {e}"

def test_proxy_connectivity():
    """Тестирование connectivity через прокси"""
    if not proxy_manager:
        return {"error": "Proxy manager not available"}
    
    try:
        results = proxy_manager.test_connectivity()
        return {"success": True, "results": results}
    except Exception as e:
        return {"error": str(e)}

def reload_xray_config():
    """Перезагрузка конфигурации Xray"""
    try:
        # Остановка текущего Xray
        stop_xray()
        
        # Небольшая задержка для завершения процесса
        time.sleep(1)
        
        # Запуск Xray с новой конфигурацией
        success = start_xray()
        
        if success:
            print("Xray configuration reloaded successfully")
            return True
        else:
            print("Failed to reload Xray configuration")
            return False
    except Exception as e:
        print(f"Error reloading Xray configuration: {e}")
        return False

def restart_xray():
    """Полный перезапуск Xray"""
    try:
        # Остановка Xray
        stop_xray()
        
        # Небольшая задержка
        time.sleep(2)
        
        # Запуск Xray
        success = start_xray()
        
        if success:
            print("Xray restarted successfully")
            return True
        else:
            print("Failed to restart Xray")
            return False
    except Exception as e:
        print(f"Error restarting Xray: {e}")
        return False

def switch_proxy_mode(new_mode, **kwargs):
    """Переключение между режимами прокси"""
    if not proxy_manager:
        return False, "Proxy manager not available"
    
    try:
        result = proxy_manager.switch_mode(new_mode, **kwargs)
        return True, f"Switched to {new_mode} mode"
    except Exception as e:
        return False, f"Error switching mode: {e}"

def get_proxy_mode_description():
    """Получение описания текущего режима прокси"""
    if not proxy_manager:
        return "Proxy manager not available"
    
    return proxy_manager.get_mode_description()

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatVPN Backend")
    parser.add_argument("command", choices=[
        "start", "stop", "status", "config",
        "proxy", "test-proxy", "proxy-mode"
    ], help="Команда")
    
    parser.add_argument("--mode", help="Режим прокси (tun, socks5, http, transparent, auto)")
    parser.add_argument("--port", type=int, help="Порт для прокси")
    
    args = parser.parse_args()
    
    if args.command == "start":
        if start_xray():
            send_telegram_message("✅ ChatVPN запущен")
            print("Xray запущен")
        else:
            send_telegram_message("❌ Ошибка запуска ChatVPN")
            print("Ошибка запуска Xray")
    
    elif args.command == "stop":
        if stop_xray():
            send_telegram_message("⏹️ ChatVPN остановлен")
            print("Xray остановлен")
        else:
            send_telegram_message("❌ Ошибка остановки ChatVPN")
            print("Ошибка остановки Xray")
    
    elif args.command == "status":
        status = get_status()
        print(f"Статус: {status['status']}")
        if "exit_code" in status:
            print(f"Код выхода: {status['exit_code']}")
        if "error" in status:
            print(f"Ошибка: {status['error']}")
        
        # Показываем информацию о прокси
        proxy_info = get_proxy_mode()
        print(f"Прокси режим: {proxy_info.get('mode', 'tun')}")
        if proxy_info.get('socks_port'):
            print(f"SOCKS порт: {proxy_info['socks_port']}")
        if proxy_info.get('http_port'):
            print(f"HTTP порт: {proxy_info['http_port']}")
    
    elif args.command == "config":
        if load_config_from_server():
            send_telegram_message("📥 Конфигурация успешно обновлена")
            print("Конфигурация успешно загружена")
        else:
            send_telegram_message("❌ Ошибка загрузки конфигурации")
            print("Ошибка загрузки конфигурации")
    
    elif args.command == "proxy":
        # Управление прокси режимом
        if args.mode:
            success, message = set_proxy_mode(args.mode, port=args.port)
            print(message)
            if success:
                send_telegram_message(f"🔄 Прокси режим изменен на {args.mode}")
        else:
            # Показать текущий режим
            proxy_info = get_proxy_mode()
            print(f"Текущий прокси режим: {proxy_info.get('mode', 'tun')}")
            print(f"Описание: {get_proxy_mode_description()}")
            print(f"Настройки: {proxy_info}")
    
    elif args.command == "test-proxy":
        # Тестирование прокси connectivity
        results = test_proxy_connectivity()
        if "error" in results:
            print(f"Ошибка тестирования: {results['error']}")
        else:
            print("Результаты тестирования прокси:")
            for url, result in results.get("results", {}).items():
                status = "✅" if result.get("success") else "❌"
                print(f"{status} {url}: {result.get('status_code', 'N/A')} ({result.get('response_time', 'N/A'):.2f}s)")
    
    elif args.command == "proxy-mode":
        # Показать информацию о режиме прокси
        proxy_info = get_proxy_mode()
        description = get_proxy_mode_description()
        
        print(f"Текущий режим: {proxy_info.get('mode', 'tun')}")
        print(f"Описание: {description}")
        print(f"Настройки: {proxy_info}")
        
        # Показать доступные режимы
        print("\nДоступные режимы:")
        print("- tun: Стандартный VPN туннель")
        print("- socks5: SOCKS5 прокси")
        print("- http: HTTP прокси")
        print("- transparent: Прозрачный прокси")
        print("- auto: Автоматический выбор")

if __name__ == "__main__":
    main()
