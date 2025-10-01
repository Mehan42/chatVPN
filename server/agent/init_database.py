#!/usr/bin/env python3
"""
Скрипт инициализации базы данных XVPN
Создает структуру базы данных и заполняет начальными данными
"""

import sys
import os
import json
import time
from pathlib import Path

# Добавляем текущую директорию в sys.path для импорта db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import init_database, add_protocol, add_fallback_resource, add_client

def load_initial_protocols():
    """Загрузка начальных протоколов восстановления"""
    protocols = [
        {
            "name": "API /manifest unreachable > 5min",
            "situation": "API_UNREACHABLE",
            "steps": [
                "Проверить доступность сервера манифестов",
                "Попытаться получить статический манифест из fallback источников",
                "Если статический манифест недоступен, использовать последние известные конфигурации",
                "Уведомить администратора о проблеме",
                "Перезапустить агент через 5 минут"
            ]
        },
        {
            "name": "T0 failed 3x",
            "situation": "TRANSPORT_T0_FAILED",
            "steps": [
                "Проверить состояние транспорта T0",
                "Запустить диагностику подключенности",
                "Попытаться переключиться на резервный транспорт",
                "Если переключение не удалось, запустить процедуру восстановления",
                "Логировать все действия для анализа"
            ]
        },
        {
            "name": "All transports down",
            "situation": "ALL_TRANSPORTS_DOWN",
            "steps": [
                "Проверить состояние всех доступных транспортов",
                "Активировать emergency режим",
                "Использовать fallback конфигурации",
                "Отправить уведомление в Telegram",
                "Попытаться восстановить работу через 10 минут",
                "Если проблема сохраняется, запросить ручное вмешательство"
            ]
        },
        {
            "name": "Network connectivity lost",
            "situation": "NETWORK_CONNECTIVITY_LOST",
            "steps": [
                "Проверить сетевое подключение",
                "Проверить DNS разрешение",
                "Активировать резервные DNS серверы",
                "Проверить доступность шлюза",
                "Если проблема сетевая, использовать мобильные данные или другую сеть"
            ]
        },
        {
            "name": "Authentication failed",
            "situation": "AUTH_FAILED",
            "steps": [
                "Проверить учетные данные",
                "Обновить токены аутентификации",
                "Проверить валидность сертификатов",
                "Если проблема persists, сбросить сессию и перезапросить аутентификацию"
            ]
        },
        {
            "name": "VPN tunnel unstable",
            "situation": "VPN_TUNNEL_UNSTABLE",
            "steps": [
                "Проверить стабильность туннеля",
                "Измерить ping и потерю пакетов",
                "Запустить диагностику протокола VPN",
                "При необходимости перезапустить туннель",
                "Если проблема повторяется, переключиться на альтернативный протокол"
            ]
        },
        {
            "name": "DNS resolution failed",
            "situation": "DNS_RESOLUTION_FAILED",
            "steps": [
                "Проверить текущие DNS серверы",
                "Переключиться на fallback DNS серверы",
                "Проверить разрешение доменных имен",
                "Кэшировать успешные разрешения",
                "Логировать неуспешные попытки для анализа"
            ]
        },
        {
            "name": "Certificate validation error",
            "situation": "CERT_VALIDATION_ERROR",
            "steps": [
                "Проверить валидность SSL/TLS сертификатов",
                "Обновить кэш сертификатов",
                "Проверить доверенные корневые сертификаты",
                "При необходимости временно отключить строгую проверку (только для отладки)",
                "Сгенерировать новый запрос сертификата при необходимости"
            ]
        }
    ]
    
    added_count = 0
    for protocol in protocols:
        add_protocol(protocol["name"], protocol["situation"], protocol["steps"])
        added_count += 1
        print(f"✅ Добавлен протокол: {protocol['name']}")
    
    return added_count

def load_initial_fallback():
    """Загрузка начальных fallback конфигураций"""
    fallback_resources = [
        {
            "type": "ip",
            "value": "203.0.113.10",
            "priority": 1,
            "notes": "Primary fallback IP"
        },
        {
            "type": "ip", 
            "value": "198.51.100.20",
            "priority": 2,
            "notes": "Secondary fallback IP"
        },
        {
            "type": "domain",
            "value": "cdn.example.com",
            "priority": 3,
            "notes": "CDN fallback domain"
        },
        {
            "type": "static_manifest",
            "value": "https://cdn.example.com/manifest.json",
            "priority": 1,
            "notes": "Primary static manifest location"
        },
        {
            "type": "static_manifest",
            "value": "https://backup-cdn.example.com/manifest.json", 
            "priority": 2,
            "notes": "Backup static manifest"
        },
        {
            "type": "doh",
            "value": "https://1.1.1.1/dns-query",
            "priority": 1,
            "notes": "Cloudflare DoH"
        },
        {
            "type": "doh",
            "value": "https://8.8.8.8/dns-query",
            "priority": 2,
            "notes": "Google DoH"
        },
        {
            "type": "doh",
            "value": "https://9.9.9.9/dns-query",
            "priority": 3,
            "notes": "Quad9 DoH"
        },
        {
            "type": "telegram",
            "value": "https://t.me/your_emergency_bot",
            "priority": 1,
            "notes": "Emergency notification channel"
        }
    ]
    
    added_count = 0
    for resource in fallback_resources:
        add_fallback_resource(
            resource["type"], 
            resource["value"], 
            resource["priority"], 
            resource["notes"]
        )
        added_count += 1
        print(f"✅ Добавлен fallback ресурс: {resource['type']} - {resource['value']}")
    
    return added_count

def load_initial_clients():
    """Загрузка начальных данных клиентов"""
    initial_clients = [
        {
            "client_id": "demo-client-1",
            "name": "Demo Client 1",
            "config": '{"version": "1.0.0", "protocols": ["wireguard", "openvpn"]}'
        },
        {
            "client_id": "demo-client-2", 
            "name": "Demo Client 2",
            "config": '{"version": "1.0.0", "protocols": ["wireguard", "shadowsocks"]}'
        }
    ]
    
    added_count = 0
    for client in initial_clients:
        add_client(client["client_id"], client["name"], client["config"])
        added_count += 1
        print(f"✅ Добавлен клиент: {client['name']} ({client['client_id']})")
    
    return added_count

def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация базы данных XVPN...")
    
    # Инициализация структуры базы данных
    print("📁 Создание структуры базы данных...")
    init_database()
    print("✅ Структура базы данных создана")
    
    # Загрузка начальных данных
    print("\n📋 Загрузка начальных данных...")
    
    print("\n🔄 Загрузка протоколов восстановления...")
    protocols_count = load_initial_protocols()
    
    print("\n🔄 Загрузка fallback конфигураций...")
    fallback_count = load_initial_fallback()
    
    print("\n🔄 Загрузка начальных клиентов...")
    clients_count = load_initial_clients()
    
    # Логирование инициализации
    from db import log_event
    log_event("INIT", "database", "success", 
              f"protocols={protocols_count}, fallback={fallback_count}, clients={clients_count}")
    
    print(f"\n🎉 Инициализация базы данных завершена!")
    print(f"📊 Добавлено:")
    print(f"   • {protocols_count} протоколов восстановления")
    print(f"   • {fallback_count} fallback ресурсов")
    print(f"   • {clients_count} клиентов")
    
    # Вывод статистики
    from db import get_database_stats
    stats = get_database_stats()
    print(f"\n📈 Статистика базы данных:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print(f"\n📍 Файл базы данных: {Path.home()}/.xvpn/agent.db")
    print("✅ XVPN Database initialization completed successfully!")

if __name__ == "__main__":
    main()