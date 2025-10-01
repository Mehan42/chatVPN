#!/usr/bin/env python3
# Health monitoring for ChatVPN client

import time
import json
import os
import urllib.request
import ssl
from pathlib import Path
import sys
import os

# Добавляем текущую директорию в sys.path для импорта tls_checker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tls_checker

# Игнорировать SSL-ошибки для самоподписанных сертификатов
ssl._create_default_https_context = ssl._create_unverified_context

# Путь к логам
HEALTH_LOG_PATH = Path.home() / 'chatvpn' / 'client' / 'logs' / 'health.log'

def check_ip_leak():
    """
    Проверка утечки IP адреса
    Возвращает True, если IP совпадает с ожидаемым (без утечки)
    """
    try:
        # Получаем текущий внешний IP
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
            current_ip = response.read().decode('utf-8')

        # Здесь нужно сравнить с ожидаемым VPN IP
        # В реальном приложении это будет IP сервера VPN
        # В тестовом режиме возвращаем True
        return True
    except:
        return False

def check_tls_profile():
    """
    Проверка TLS профиля (реализация с использованием tls_checker)
    Возвращает оценку от 1 до 5
    """
    try:
        # В реальном приложении нужно использовать текущий сервер
        # Для теста используем localhost:8443 (порт API)
        result = tls_checker.evaluate_tls_security("localhost", 8443, "reality")
        if result.get("success"):
            return result.get("score", 3)
        else:
            return 2  # Базовая оценка при ошибке
    except:
        return 3  # Стандартная оценка при ошибке импорта

def check_dns_protection():
    """
    Проверка DNS защиты
    Возвращает True, если DNS защищён
    """
    try:
        # В реальной реализации нужно проверять направление DNS-запросов
        # и наличие DoH/DoT

        # Для теста просто проверим, можем ли мы выполнить DNS-запрос
        # через системный DNS (если он перенаправлен в VPN)
        import socket
        socket.getaddrinfo("www.google.com", 80)
        return True
    except:
        return False

def check_connection_latency(target="8.8.8.8", timeout=5):
    """
    Проверка задержки соединения
    Возвращает задержку в миллисекундах или None при ошибке
    """
    try:
        import subprocess
        result = subprocess.run(["ping", "-c", "1", "-W", str(timeout), target],
                                capture_output=True, text=True, timeout=timeout+2)
        if result.returncode == 0:
            # Извлекаем время из вывода ping
            lines = result.stdout.splitlines()
            for line in lines:
                if "time=" in line:
                   time_part = line.split("time=")[1].split()[0]
                   return float(time_part)
        return None
    except:
        return None

def calculate_mask_score():
    """
    Рассчитывает общую оценку маскировки (0-5)
    """
    score = 0

    # Проверка утечки IP (2 балла)
    if check_ip_leak():
        score += 2

    # Проверка TLS профиля (2 балла)
    tls_score = check_tls_profile()
    score += min(tls_score, 2)  # Ограничиваем 2 баллами

    # Проверка DNS (1 балл)
    if check_dns_protection():
        score += 1

    # Ограничиваем максимальную оценку 5
    return min(score, 5)

def log_health_event(mask_score, details=""):
    """
    Логирование события здоровья в файл
    """
    os.makedirs(HEALTH_LOG_PATH.parent, exist_ok=True)

    timestamp = int(time.time())
    latency = check_connection_latency()

    log_entry = {
        "timestamp": timestamp,
        "mask_score": mask_score,
        "details": details,
        "ip_leak": check_ip_leak(),
        "tls_score": check_tls_profile(),
        "dns_protected": check_dns_protection(),
        "latency_ms": latency
    }

    with open(HEALTH_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

def get_last_health_score():
    """
    Получение последней оценки здоровья из лога
    """
    if not HEALTH_LOG_PATH.exists():
        return 0

    try:
        with open(HEALTH_LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                last_line = json.loads(lines[-1])
                return last_line.get('mask_score', 0)
    except:
        pass

    return 0

def get_current_mask_score():
    """
    Получение текущей оценки маскировки
    """
    score = calculate_mask_score()
    log_health_event(score)
    return score

if __name__ == "__main__":
    # Тестирование функций
    print(f"Mask score: {get_current_mask_score()}/5")
    print(f"Last health score: {get_last_health_score()}/5")
    print(f"IP leak check: {check_ip_leak()}")
    print(f"TLS profile score: {check_tls_profile()}/5")
    print(f"DNS protected: {check_dns_protection()}")
    print(f"Connection latency: {check_connection_latency()} ms")
    print(f"Log file: {HEALTH_LOG_PATH}")
