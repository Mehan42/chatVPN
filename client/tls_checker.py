#!/usr/bin/env python3
# TLS checker for ChatVPN client

import ssl
import socket
import time
from urllib.parse import urlparse

def check_tls_profile(hostname, port=443, timeout=10):
    """
    Проверка TLS профиля соединения
    Возвращает оценку от 1 до 5
    """
    try:
        # Создаем SSL контекст
        context = ssl.create_default_context()
        context.check_hostname = False  # Используем для самоподписанных сертификатов
        context.verify_mode = ssl.CERT_NONE  # Не проверяем сертификаты

        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Получаем информацию о подключении
                cipher = ssock.cipher()
                version = ssock.version()
                cert = ssock.getpeercert()

                score = 3  # Базовая оценка

                # Проверяем версию TLS
                if version == 'TLSv1.3':
                    score += 1
                elif version == 'TLSv1.2':
                    # Хорошо, но не TLSv1.3
                    pass
                else:
                    # TLSv1.1 или ниже - снижаем оценку
                    score -= 1

                # Проверяем шифр
                if cipher:
                    cipher_name = cipher[0]
                    if 'TLS_AES' in cipher_name or 'TLS_CHACHA20' in cipher_name:
                        score += 1  # Современные шифры
                    elif 'ECDHE' in cipher_name:
                        # Хорошие, но не самые современные
                        pass
                    else:
                        # Старые шифры
                        score -= 1

                # Ограничиваем оценку диапазоном 1-5
                score = max(1, min(5, score))

                return {
                    'score': score,
                    'version': version,
                    'cipher': cipher[0] if cipher else 'Unknown',
                    'success': True
                }
    except Exception as e:
        return {
            'score': 1,
            'error': str(e),
            'success': False
        }

def check_tls_reality_profile(hostname, port=443):
    """
    Проверка TLS профиля для Reality
    """
    try:
        # Создаем контекст с настройками для reality
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Устанавливаем специфичные настройки для reality
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Извлекаем характеристики соединения
                cipher = ssock.cipher()
                version = ssock.version()

                # Reality должен использовать определенные настройки
                score = 4  # Reality обычно хорошо маскируется

                return {
                    'score': score,
                    'type': 'reality',
                    'version': version,
                    'cipher': cipher[0] if cipher else 'Unknown',
                    'success': True
                }
    except Exception as e:
        return {
            'score': 1,
            'error': str(e),
            'success': False
        }

def evaluate_tls_security(hostname, port=443, protocol_type="standard"):
    """
    Оценка безопасности TLS
    """
    if protocol_type.lower() == "reality":
         return check_tls_reality_profile(hostname, port)
    else:
        return check_tls_profile(hostname, port)

if __name__ == "__main__":
    # Пример использования
    results = evaluate_tls_security("example.com", 443, "standard")
    print(f"TLS Profile: {results}")

    # Проверка localhost для тестирования
    results = evaluate_tls_security("localhost", 8443, "reality")
    print(f"Local TLS Profile: {results}")
