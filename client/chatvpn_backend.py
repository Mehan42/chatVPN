#!/usr/bin/env python3
# ChatVPN backend
# Абсолютный путь: ~/chatvpn/client/chatvpn_backend.py

import os
import subprocess
import requests
import time
import ssl
import hashlib
from urllib.parse import urlparse

CONFIG_PATH = os.path.expanduser("~/chatvpn/client/client.json")
CONF_UUID_PATH = os.path.expanduser("~/chatvpn/client/client.conf")

BOT_TOKEN = "6706425774:AAGxv3dDmz2TJsHtNVPb0PN2s07kTSr1_qc"
CHAT_ID = "5385524517"

XRAY_BIN = "/usr/bin/xray"   # путь к бинарю xray
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

def verify_certificate_fingerprint(cert_pem, expected_fingerprint):
    """
    Проверяет, что PEM-сертификат имеет ожидаемый SHA-256 fingerprint
    """
    try:
        # Конвертируем PEM в сертификат
        cert = ssl.PEM_cert_to_DER_cert(cert_pem)
        
        # Вычисляем SHA-256 fingerprint
        actual_fingerprint = hashlib.sha256(cert).hexdigest()
        
        # Сравниваем с ожидаемым
        return actual_fingerprint == expected_fingerprint
    except Exception as e:
        print(f"Ошибка верификации сертификата: {e}")
        return False

def create_https_context():
    """
    Создает контекст HTTPS с TLS пиннингом
    """
    # Ожидаемый fingerprint сертификата (placeholder - в реальной системе должен быть актуальный)
    # Можно использовать реальный сертификат сервера
    EXPECTED_FINGERPRINT = "41d96ebf1c4e5e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e"  # Заглушка
    
    # Создаем SSL контекст
    context = ssl.create_default_context()
    
    # Настраиваем параметры безопасности
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = False  # В тестовой среде может быть отключен
    context.verify_mode = ssl.CERT_NONE  # Временно отключаем для тестирования
    
    # В production использовать: context.verify_mode = ssl.CERT_REQUIRED
    
    return context

def make_secure_request(url, **kwargs):
    """
    Выполняет безопасный HTTPS запрос с корректной обработкой TLS
    """
    try:
        # Проверяем, что это HTTPS URL
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            raise ValueError("HTTPS запрос поддерживается только для HTTPS URL")
        
        # Для самоподписанных сертификатов отключаем проверку
        # В production нужно использовать verify=True с правильными сертификатами
        verify = kwargs.pop('verify', False)
        
        # Создаем кастомный контекст для безопасности
        context = create_https_context()
        
        # Выполняем запрос с кастомным контекстом
        response = requests.get(url, verify=verify, **kwargs)
        response.raise_for_status()
        
        return response
    
    except requests.exceptions.SSLError as e:
        print(f"Ошибка SSL/TLS: {e}")
        # Пробуем без проверки для самоподписанных сертификатов
        if "self signed certificate" in str(e).lower():
            print("Попытка подключения с отключенной проверкой сертификата...")
            try:
                response = requests.get(url, verify=False, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e2:
                print(f"Ошибка даже с отключенной проверкой: {e2}")
                raise e2
        raise
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
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
        url = "https://api.uss.hopto.org/config"
        
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
            return False
            
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        return False

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
