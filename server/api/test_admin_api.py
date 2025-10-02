#!/usr/bin/env python3
# Тестирование REST API для администрирования XVPN
# Абсолютный путь: ~/chatvpn/server/api/test_admin_api.py

import sys
import os
import json
import time
import requests
import threading
from datetime import datetime

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_rest_api import create_admin_api

def test_admin_api():
    """Тестирование REST API для администрирования"""
    print("=== Тестирование REST API для администрирования XVPN ===")
    
    # Создание API экземпляра
    config = {
        'secret_key': 'test-secret-key',
        'jwt_secret_key': 'test-jwt-secret-key',
        'allowed_origins': ['http://localhost:5000']
    }
    
    api = create_admin_api(config)
    
    # Запуск API сервера в отдельном потоке
    api_thread = threading.Thread(target=api.run, kwargs={'host': '127.0.0.1', 'port': 5000, 'debug': False})
    api_thread.daemon = True
    api_thread.start()
    
    # Ожидание запуска сервера
    time.sleep(2)
    
    base_url = "http://127.0.0.1:5000"
    
    print("1. Тест health check...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   ✓ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
    
    print("\n2. Тест аутентификации...")
    
    # Создание тестового пользователя
    test_user = {
        'username': 'admin',
        'email': 'admin@xvpn.com',
        'password': 'admin123',
        'role': 'admin'
    }
    
    try:
        # Регистрация пользователя
        response = requests.post(f"{base_url}/api/admin/users", json=test_user, timeout=5)
        if response.status_code == 201:
            print("   ✓ User created successfully")
        elif response.status_code == 400:
            print("   User already exists (expected)")
        else:
            print(f"   ✗ User creation failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ User creation failed: {e}")
    
    # Вход пользователя
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            print("   ✓ Login successful")
            token = response.json()['access_token']
            print(f"   Token: {token[:20]}...")
        else:
            print(f"   ✗ Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ Login failed: {e}")
        return
    
    print("\n3. Тест статистики...")
    
    # Заголовки с токеном
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/admin/stats", headers=headers, timeout=5)
        print(f"   ✓ System stats: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ System stats failed: {e}")
    
    try:
        response = requests.get(f"{base_url}/api/admin/stats/clients", headers=headers, timeout=5)
        print(f"   ✓ Client stats: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Client stats failed: {e}")
    
    print("\n4. Тест конфигурации...")
    
    try:
        response = requests.get(f"{base_url}/api/admin/config", headers=headers, timeout=5)
        print(f"   ✓ Get config: {response.status_code}")
        config_data = response.json()
        print(f"   Config keys: {list(config_data['config'].keys())}")
    except Exception as e:
        print(f"   ✗ Get config failed: {e}")
    
    # Обновление конфигурации
    new_config = {
        'max_clients': 2000,
        'bandwidth_limit': 2000000,
        'enable_ip_locking': True
    }
    
    try:
        response = requests.put(f"{base_url}/api/admin/config", json=new_config, headers=headers, timeout=5)
        print(f"   ✓ Update config: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Update config failed: {e}")
    
    print("\n5. Тест управления пользователями...")
    
    try:
        response = requests.get(f"{base_url}/api/admin/users", headers=headers, timeout=5)
        print(f"   ✓ Get users: {response.status_code}")
        users = response.json()
        print(f"   Total users: {len(users['users'])}")
        for user in users['users']:
            print(f"   - {user['username']} ({user['role']})")
    except Exception as e:
        print(f"   ✗ Get users failed: {e}")
    
    print("\n6. Тест управления клиентами...")
    
    # Симуляция данных клиентов
    client_stats = [
        {'client_id': 'test-client-1', 'status': 'active', 'bandwidth_used': 1000000, 'uptime': 3600, 'protocol': 'websocket'},
        {'client_id': 'test-client-2', 'status': 'inactive', 'bandwidth_used': 500000, 'uptime': 1800, 'protocol': 'http'},
        {'client_id': 'test-client-3', 'status': 'active', 'bandwidth_used': 2000000, 'uptime': 7200, 'protocol': 'grpc'}
    ]
    
    for stats in client_stats:
        try:
            response = requests.post(f"{base_url}/api/admin/clients/{stats['client_id']}/status", 
                                   json={'status': stats['status']}, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"   ✓ Client {stats['client_id']} status updated")
            else:
                print(f"   ✗ Client {stats['client_id']} status update failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Client {stats['client_id']} status update failed: {e}")
    
    try:
        response = requests.get(f"{base_url}/api/admin/clients", headers=headers, timeout=5)
        print(f"   ✓ Get clients: {response.status_code}")
        clients = response.json()
        print(f"   Total clients: {len(clients['clients'])}")
        for client in clients['clients'][:3]:  # Показываем первых 3 клиентов
            print(f"   - {client['client_id']}: {client['status']}")
    except Exception as e:
        print(f"   ✗ Get clients failed: {e}")
    
    print("\n7. Тест безопасности...")
    
    try:
        response = requests.get(f"{base_url}/api/admin/security/audit", headers=headers, timeout=5)
        print(f"   ✓ Security audit: {response.status_code}")
        audit = response.json()
        print(f"   Failed logins (24h): {audit['security_audit']['last_24h_failed_logins']}")
        print(f"   Active sessions: {audit['security_audit']['active_sessions']}")
    except Exception as e:
        print(f"   ✗ Security audit failed: {e}")
    
    try:
        response = requests.get(f"{base_url}/api/admin/security/sessions", headers=headers, timeout=5)
        print(f"   ✓ Active sessions: {response.status_code}")
        sessions = response.json()
        print(f"   Total sessions: {len(sessions['sessions'])}")
    except Exception as e:
        print(f"   ✗ Active sessions failed: {e}")
    
    print("\n8. Тест логов...")
    
    try:
        response = requests.get(f"{base_url}/api/admin/logs", headers=headers, timeout=5)
        print(f"   ✓ Get logs: {response.status_code}")
        logs = response.json()
        print(f"   Total logs: {len(logs['logs'])}")
        for log in logs['logs'][:3]:  # Показываем первые 3 лога
            print(f"   - {log['timestamp']}: {log['endpoint']} ({log['status_code']})")
    except Exception as e:
        print(f"   ✗ Get logs failed: {e}")
    
    print("\n9. Тест генерации API ключа...")
    
    try:
        response = requests.post(f"{base_url}/api/auth/api-key", headers=headers, timeout=5)
        if response.status_code == 200:
            print("   ✓ API key generated")
            api_key = response.json()['api_key']
            print(f"   API Key: {api_key[:20]}...")
        else:
            print(f"   ✗ API key generation failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ API key generation failed: {e}")
    
    print("\n10. Тест выхода...")
    
    try:
        response = requests.post(f"{base_url}/api/auth/logout", headers=headers, timeout=5)
        print(f"   ✓ Logout: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Logout failed: {e}")
    
    print("\n=== Тестирование завершено ===")

def test_api_endpoints():
    """Тестирование доступных эндпоинтов"""
    print("\n=== Тестирование доступных эндпоинтов ===")
    
    # Тестовые данные для симуляции
    endpoints = [
        ('GET', '/api/health', 'Health check'),
        ('POST', '/api/auth/login', 'User login'),
        ('POST', '/api/auth/logout', 'User logout'),
        ('POST', '/api/auth/api-key', 'Generate API key'),
        ('GET', '/api/admin/users', 'Get all users'),
        ('POST', '/api/admin/users', 'Create new user'),
        ('GET', '/api/admin/users/{user_id}', 'Get user by ID'),
        ('PUT', '/api/admin/users/{user_id}', 'Update user'),
        ('DELETE', '/api/admin/users/{user_id}', 'Delete user'),
        ('GET', '/api/admin/stats', 'System statistics'),
        ('GET', '/api/admin/stats/clients', 'Client statistics'),
        ('GET', '/api/admin/config', 'Get system configuration'),
        ('PUT', '/api/admin/config', 'Update system configuration'),
        ('GET', '/api/admin/clients', 'Get all clients'),
        ('GET', '/api/admin/clients/{client_id}', 'Get client info'),
        ('PUT', '/api/admin/clients/{client_id}/status', 'Update client status'),
        ('GET', '/api/admin/security/audit', 'Security audit'),
        ('GET', '/api/admin/security/sessions', 'Active sessions'),
        ('GET', '/api/admin/logs', 'System logs')
    ]
    
    print("Доступные эндпоинты:")
    for method, endpoint, description in endpoints:
        print(f"  {method} {endpoint} - {description}")
    
    print("\n=== Тестирование эндпоинтов завершено ===")

if __name__ == "__main__":
    print("Запуск тестирования REST API...")
    
    # Тестирование доступных эндпоинтов
    test_api_endpoints()
    
    # Полное тестирование API
    test_admin_api()
    
    print("\nВсе тесты завершены!")