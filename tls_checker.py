#!/usr/bin/env python3
# TLS checker for ChatVPN client

import ssl
import socket
import time
import logging
import datetime
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tls_profile(hostname, port=443, timeout=10, attempts=3):
    """
    Проверка TLS профиля соединения с повторными попытками
    Возвращает оценку от 1 до 5
    """
    last_error = None
    
    for attempt in range(attempts):
        try:
            # Создаем SSL контекст с более строгими настройками
            context = ssl.create_default_context()
            context.check_hostname = False  # Используем для самоподписанных сертификатов
            context.verify_mode = ssl.CERT_NONE  # Не проверяем сертификаты
            
            # Пробуем разные типы сокетов для лучшей совместимости
            sock = None
            connected = False
            
            # Пробуем IPv4
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((hostname, port))
                connected = True
            except:
                if sock:
                    sock.close()
                # Пробуем IPv6
                try:
                    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    sock.connect((hostname, port))
                    connected = True
                except:
                    if sock:
                        sock.close()
            
            if not connected:
                raise Exception(f"Failed to connect to {hostname}:{port}")
            
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Получаем информацию о подключении
                cipher = ssock.cipher()
                version = ssock.version()
                compression = ssock.compression()
                cert = ssock.getpeercert()
                
                # Дополнительная информация
                key_exchange = getattr(ssock, 'key_exchange', None)
                signature_algorithms = getattr(ssock, 'signature_algorithms', None)

                score = 3  # Базовая оценка
                details = {
                    'version': version,
                    'cipher': cipher[0] if cipher else 'Unknown',
                    'cipher_strength': cipher[1] if cipher and len(cipher) > 1 else 0,
                    'compression_used': compression is not None,
                    'key_exchange': key_exchange,
                    'signature_algorithms': signature_algorithms,
                    'cert_issuer': cert.get('issuer', [('', '')])[0][1] if cert and cert.get('issuer') else 'Unknown',
                    'cert_subject': cert.get('subject', [('', '')])[0][1] if cert and cert.get('subject') else 'Unknown'
                }

                # Проверяем версию TLS
                if version == 'TLSv1.3':
                    score += 1
                    details['tls_version_score'] = 'excellent'
                elif version == 'TLSv1.2':
                    details['tls_version_score'] = 'good'
                elif version in ['TLSv1.1', 'SSLv3']:
                    score -= 1
                    details['tls_version_score'] = 'poor'
                else:
                    score -= 2
                    details['tls_version_score'] = 'very_poor'

                # Проверяем шифр
                if cipher and len(cipher) > 0:
                    cipher_name = cipher[0]
                    cipher_strength = cipher[1] if len(cipher) > 1 else 0
                    
                    if 'TLS_AES_256_GCM_SHA384' in cipher_name or 'TLS_CHACHA20_POLY1305_SHA256' in cipher_name:
                        score += 1
                        details['cipher_score'] = 'excellent'
                    elif 'TLS_AES_128_GCM_SHA256' in cipher_name or 'ECDHE' in cipher_name:
                        details['cipher_score'] = 'good'
                    elif 'RC4' in cipher_name or 'MD5' in cipher_name or 'DES' in cipher_name:
                        score -= 2
                        details['cipher_score'] = 'very_poor'
                    else:
                        details['cipher_score'] = 'moderate'

                # Проверка на использование слабых криптографических параметров
                if compression:
                    score -= 1
                    details['compression_warning'] = True
                
                # Проверка сертификата
                if cert:
                    not_before = cert.get('notBefore')
                    not_after = cert.get('notAfter')
                    if not_after:
                        import datetime
                        try:
                            expiry_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                            days_left = (expiry_date - datetime.datetime.now()).days
                            details['cert_days_left'] = days_left
                            if days_left < 30:
                                score -= 1
                                details['cert_expiry_warning'] = True
                        except:
                            pass

                # Ограничиваем оценку диапазоном 1-5
                score = max(1, min(5, score))
                
                details['overall_score'] = score
                details['attempts'] = attempt + 1

                return {
                    'score': score,
                    'details': details,
                    'success': True
                }
                
        except Exception as e:
            last_error = str(e)
            logger.debug(f"TLS check attempt {attempt + 1} failed: {e}")
            # Ждем перед следующей попыткой
            if attempt < attempts - 1:
                time.sleep(1)
    
    # Все попытки провалились
    return {
        'score': 1,
        'error': last_error or "All connection attempts failed",
        'success': False,
        'attempts': attempts
    }

def check_tls_reality_profile(hostname, port=443, timeout=10, attempts=3):
    """
    Проверка TLS профиля для Reality с улучшенной логикой маскировки
    """
    last_error = None
    
    for attempt in range(attempts):
        try:
            logger.info(f"Reality TLS check attempt {attempt + 1} for {hostname}:{port}")
            
            # Создаем контекст с настройками для reality
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Пробуем разные типы сокетов
            sock = None
            connected = False
            
            # Пробуем IPv4
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((hostname, port))
                connected = True
            except:
                if sock:
                    sock.close()
                # Пробуем IPv6
                try:
                    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    sock.connect((hostname, port))
                    connected = True
                except:
                    if sock:
                        sock.close()
            
            if not connected:
                raise Exception(f"Failed to connect to {hostname}:{port}")
            
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Извлекаем характеристики соединения
                cipher = ssock.cipher()
                version = ssock.version()
                compression = ssock.compression()
                cert = ssock.getpeercert()
                
                # Дополнительная информация
                key_exchange = getattr(ssock, 'key_exchange', None)
                signature_algorithms = getattr(ssock, 'signature_algorithms', None)
                
                # Проверка специфичных параметров Reality
                alpn_protocols = getattr(ssock, 'selected_alpn_protocol', None)
                sni = getattr(ssock, 'server_hostname', None)
                
                details = {
                    'type': 'reality',
                    'version': version,
                    'cipher': cipher[0] if cipher else 'Unknown',
                    'cipher_strength': cipher[1] if cipher and len(cipher) > 1 else 0,
                    'compression_used': compression is not None,
                    'key_exchange': key_exchange,
                    'signature_algorithms': signature_algorithms,
                    'alpn_protocols': alpn_protocols,
                    'sni_used': sni,
                    'cert_issuer': cert.get('issuer', [('', '')])[0][1] if cert and cert.get('issuer') else 'Unknown',
                    'cert_subject': cert.get('subject', [('', '')])[0][1] if cert and cert.get('subject') else 'Unknown'
                }
                
                # Reality обычно хорошо маскируется, используем базовую оценку
                score = 4
                
                # Reality поддерживает современные протоколы
                if version == 'TLSv1.3':
                    details['tls_version_score'] = 'excellent'
                elif version == 'TLSv1.2':
                    details['tls_version_score'] = 'good'
                    score -= 1  # Reality обычно использует TLS 1.3
                else:
                    details['tls_version_score'] = 'suspicious'
                    score -= 2
                
                # Анализ шифров Reality
                if cipher and len(cipher) > 0:
                    cipher_name = cipher[0]
                    if 'TLS_AES' in cipher_name:
                        details['cipher_score'] = 'excellent'
                    elif 'ECDHE' in cipher_name and 'CHACHA20' in cipher_name:
                        details['cipher_score'] = 'good'
                    else:
                        details['cipher_score'] = 'suspicious'
                        score -= 1
                
                # Проверка ALPN (Reality использует специфичные протоколы)
                if alpn_protocols:
                    details['alpn_detected'] = True
                    if 'h2' in alpn_protocols or 'http/1.1' in alpn_protocols:
                        details['web_protocol'] = True
                    else:
                        details['web_protocol'] = False
                        score -= 1
                
                # Проверка на признаки VPN (для оценки маскировки)
                vpn_indicators = []
                
                if compression:
                    vpn_indicators.append('compression')
                    score -= 1
                
                if cert and 'Let\'s Encrypt' not in details['cert_issuer']:
                    vpn_indicators.append('unusual_cert_issuer')
                    score -= 1
                
                # Reality обычно не показывает явных признаков VPN
                if vpn_indicators:
                    details['vpn_indicators'] = vpn_indicators
                    score -= 1
                
                # Ограничиваем оценку диапазоном 1-5
                score = max(1, min(5, score))
                
                details['overall_score'] = score
                details['attempts'] = attempt + 1
                details['masking_quality'] = 'good' if score >= 3 else 'poor'
                
                # Reality должен выглядеть как обычное HTTPS соединение
                expected_score = 3 if details['web_protocol'] else 2
                details['reality_masking_accuracy'] = abs(score - expected_score) <= 1
                
                logger.info(f"Reality TLS check completed with score {score}, masking quality: {details['masking_quality']}")
                
                return {
                    'score': score,
                    'details': details,
                    'success': True
                }
                
        except Exception as e:
            last_error = str(e)
            logger.debug(f"Reality TLS check attempt {attempt + 1} failed: {e}")
            # Ждем перед следующей попыткой
            if attempt < attempts - 1:
                time.sleep(1)
    
    # Все попытки провалились
    logger.warning(f"All Reality TLS check attempts failed for {hostname}:{port}: {last_error}")
    return {
        'score': 1,
        'error': last_error or "All Reality connection attempts failed",
        'success': False,
        'attempts': attempts
    }

def evaluate_tls_security(hostname, port=443, protocol_type="standard", timeout=10, attempts=3):
    """
    Улучшенная оценка безопасности TLS с поддержкой разных протоколов
    """
    logger.info(f"Evaluating TLS security for {hostname}:{port} (type: {protocol_type})")
    
    if protocol_type.lower() == "reality":
        result = check_tls_reality_profile(hostname, port, timeout, attempts)
    else:
        result = check_tls_profile(hostname, port, timeout, attempts)
    
    # Добавляем общую оценку безопасности
    if result['success']:
        score = result['score']
        security_level = "excellent"
        if score >= 4:
            security_level = "excellent"
        elif score >= 3:
            security_level = "good"
        elif score >= 2:
            security_level = "moderate"
        else:
            security_level = "poor"
        
        result['security_level'] = security_level
        result['recommendations'] = _get_tls_recommendations(result, protocol_type)
        
        logger.info(f"TLS evaluation completed: {security_level} (score: {score})")
    else:
        result['security_level'] = "unknown"
        result['recommendations'] = ["Check network connectivity and hostname"]
        logger.warning(f"TLS evaluation failed: {result.get('error', 'Unknown error')}")
    
    return result

def _get_tls_recommendations(result, protocol_type):
    """
    Генерация рекомендаций на основе результатов TLS проверки
    """
    recommendations = []
    
    if not result['success']:
        return ["Fix connection issues before proceeding"]
    
    details = result.get('details', {})
    score = result['score']
    
    # Рекомендации на основе версии TLS
    tls_version_score = details.get('tls_version_score', 'unknown')
    if tls_version_score == 'suspicious' or tls_version_score == 'very_poor':
        recommendations.append("Upgrade to TLS 1.2 or higher")
    
    # Рекомендации на основе шифров
    cipher_score = details.get('cipher_score', 'unknown')
    if cipher_score == 'very_poor':
        recommendations.append("Replace weak cipher suites")
    elif cipher_score == 'moderate':
        recommendations.append("Consider using stronger cipher suites")
    
    # Рекомендации на Reality
    if protocol_type.lower() == "reality":
        if not details.get('web_protocol', False):
            recommendations.append("Reality should mimic regular HTTPS traffic")
        if not details.get('reality_masking_accuracy', True):
            recommendations.append("Reality masking needs improvement")
    
    # Рекомендации на основе сертификатов
    if details.get('cert_expiry_warning'):
        recommendations.append("Certificate expires soon - renew it")
    
    if details.get('compression_used'):
        recommendations.append("Disable TLS compression for security")
    
    # Общие рекомендации
    if score < 3:
        recommendations.append("Overall TLS configuration needs improvement")
    
    return recommendations if recommendations else ["TLS configuration is secure"]

if __name__ == "__main__":
    # Пример использования
    results = evaluate_tls_security("example.com", 443, "standard")
    print(f"TLS Profile: {results}")

    # Проверка localhost для тестирования
    results = evaluate_tls_security("localhost", 8443, "reality")
    print(f"Local TLS Profile: {results}")
