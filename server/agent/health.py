#!/usr/bin/env python3
"""
Health monitoring utilities for XVPN
Модуль для мониторинга здоровья VPN соединения и маскировки
"""

import time
import random
import subprocess
import socket
import requests
import json
from typing import Dict, List, Optional

class HealthMonitor:
    """Класс для мониторинга здоровья системы"""
    
    def __init__(self):
        self.last_check = 0
        self.check_interval = 30  # секунд
        self.mask_history = []
        
    def check_ip_leak(self) -> bool:
        """Проверка утечки IP адреса"""
        try:
            # Проверяем IP через несколько сервисов
            services = [
                "https://api.ipify.org?format=json",
                "https://httpbin.org/ip",
                "https://api64.ipify.org?format=json"
            ]
            
            ips = []
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        ip = data.get('ip') or data.get('origin', '').split(',')[0].strip()
                        if ip:
                            ips.append(ip)
                except Exception:
                    continue
            
            # Если все IP одинаковые и не являются локальными, то утечки нет
            if len(set(ips)) == 1 and not self._is_local_ip(ips[0]):
                return True
            
            return False
        except Exception:
            return False
    
    def _is_local_ip(self, ip: str) -> bool:
        """Проверка, является ли IP локальным"""
        local_prefixes = ['192.168.', '10.', '172.16.', '127.', '169.254.']
        return any(ip.startswith(prefix) for prefix in local_prefixes)
    
    def check_tls_profile(self) -> int:
        """Проверка TLS профиля (оценка маскировки)"""
        try:
            # Проверяем TLS fingerprint через несколько эндпоинтов
            test_urls = [
                "https://www.cloudflare.com/cdn-cgi/trace",
                "https://httpbin.org/headers"
            ]
            
            score = 0
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        # Простая эвристика: если запрос прошел успешно, даем очки
                        score += 1
                        
                        # Дополнительные проверки заголовков
                        headers = response.headers
                        if 'Server' in headers and 'cloudflare' in headers['Server'].lower():
                            score += 1
                except Exception:
                    pass
            
            # Нормализуем score к шкале 1-5
            return min(5, max(1, score))
            
        except Exception:
            return 1
    
    def check_dns_resolution(self) -> bool:
        """Проверка работы DNS"""
        test_domains = ['google.com', 'cloudflare.com', '1.1.1.1']
        
        for domain in test_domains:
            try:
                socket.gethostbyname(domain)
                return True
            except socket.gaierror:
                continue
        
        return False
    
    def check_connectivity(self) -> bool:
        """Проверка общей связности"""
        try:
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def ping_test(self, host: str = "8.8.8.8") -> Optional[float]:
        """Ping тест для измерения задержки"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', host],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Парсим время из вывода ping
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split(' ')[0]
                        return float(time_str)
            
            return None
        except Exception:
            return None
    
    def get_mask_score(self) -> int:
        """Вычисление общего mask score (1-5)"""
        score = 0
        
        # IP leak test (2 балла)
        if self.check_ip_leak():
            score += 2
        
        # TLS profile test (2 балла)  
        tls_score = self.check_tls_profile()
        score += min(2, tls_score)
        
        # DNS test (1 балл)
        if self.check_dns_resolution():
            score += 1
        
        # Нормализуем к шкале 1-5
        final_score = max(1, min(5, score))
        
        # Сохраняем в историю
        self.mask_history.append({
            'timestamp': int(time.time()),
            'score': final_score
        })
        
        # Оставляем только последние 100 записей
        if len(self.mask_history) > 100:
            self.mask_history = self.mask_history[-100:]
        
        return final_score
    
    def get_network_stats(self) -> Dict:
        """Получение сетевой статистики"""
        stats = {}
        
        try:
            # Ping латентность
            ping_time = self.ping_test()
            stats['ping_ms'] = ping_time
            
            # Проверка связности
            stats['connectivity'] = self.check_connectivity()
            stats['dns_working'] = self.check_dns_resolution()
            stats['ip_leak_detected'] = not self.check_ip_leak()
            
            # Статус интерфейсов (упрощенно)
            stats['interfaces'] = self._get_network_interfaces()
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _get_network_interfaces(self) -> List[Dict]:
        """Получение информации о сетевых интерфейсах"""
        interfaces = []
        
        try:
            # Простая проверка через ip addr
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if line and line[0].isdigit():
                        # Новый интерфейс
                        parts = line.split(':')
                        if len(parts) >= 2:
                            name = parts[1].strip()
                            status = 'UP' if 'UP' in line else 'DOWN'
                            
                            current_interface = {
                                'name': name,
                                'status': status,
                                'ips': []
                            }
                            interfaces.append(current_interface)
                    
                    elif 'inet ' in line and current_interface:
                        # IP адрес
                        ip = line.split('inet ')[1].split('/')[0]
                        current_interface['ips'].append(ip)
        
        except Exception:
            pass
        
        return interfaces
    
    def run_full_health_check(self) -> Dict:
        """Полная проверка здоровья системы"""
        start_time = time.time()
        
        health_report = {
            'timestamp': int(start_time),
            'mask_score': self.get_mask_score(),
            'network_stats': self.get_network_stats(),
            'check_duration': 0
        }
        
        health_report['check_duration'] = time.time() - start_time
        
        return health_report
    
    def get_health_trend(self) -> str:
        """Анализ тренда здоровья на основе истории"""
        if len(self.mask_history) < 3:
            return "insufficient_data"
        
        recent_scores = [h['score'] for h in self.mask_history[-5:]]
        avg_recent = sum(recent_scores) / len(recent_scores)
        
        older_scores = [h['score'] for h in self.mask_history[-10:-5]] if len(self.mask_history) >= 10 else []
        
        if older_scores:
            avg_older = sum(older_scores) / len(older_scores)
            
            if avg_recent > avg_older + 0.5:
                return "improving"
            elif avg_recent < avg_older - 0.5:
                return "degrading"
            else:
                return "stable"
        else:
            return "stable"

if __name__ == "__main__":
    # Тестирование при прямом запуске
    monitor = HealthMonitor()
    
    print("🏥 Running health check...")
    health = monitor.run_full_health_check()
    
    print(f"🎭 Mask Score: {health['mask_score']}/5")
    print(f"📊 Network Stats: {json.dumps(health['network_stats'], indent=2)}")
    print(f"⏱️ Check Duration: {health['check_duration']:.2f}s")
    print(f"📈 Health Trend: {monitor.get_health_trend()}")
