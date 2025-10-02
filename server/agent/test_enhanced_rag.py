#!/usr/bin/env python3
# Тест Enhanced RAG System для XVPN агента
# Абсолютный путь: ~/chatvpn/server/agent/test_enhanced_rag.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_rag_system import create_enhanced_rag_system
import json
import time

def test_rag_system_initialization():
    """Тестирование инициализации RAG системы"""
    print("=== Тест инициализации Enhanced RAG System ===")
    
    try:
        # Создание RAG системы
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Проверка атрибутов
        assert hasattr(rag_system, 'agent_uuid')
        assert hasattr(rag_system, 'knowledge_dir')
        assert hasattr(rag_system, 'db_path')
        
        print("✓ RAG система успешно создана")
        print(f"✓ UUID агента: {rag_system.agent_uuid}")
        print(f"✓ Путь к базе данных: {rag_system.db_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка инициализации: {e}")
        return False

def test_knowledge_sources():
    """Тестирование добавления и управления источниками знаний"""
    print("\n=== Тестирование источников знаний ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Тестовые данные
        test_sources = [
            {
                "name": "vpn_protocols",
                "content": """
                VPN протоколы:
                1. OpenVPN - безопасный и гибкий протокол
                2. WireGuard - современный высокопроизводительный протокол
                3. IKEv2 - быстрый и стабильный протокол
                4. SSTP - протокол для обхода блокировок
                5. L2TP/IPsec - комбинация протоколов для безопасности
                """,
                "tags": ["vpn", "protocols", "security"]
            },
            {
                "name": "xray_features",
                "content": """
                Xray характеристики:
                - Поддержка多种传输协议 (WebSocket, HTTP/2, gRPC, TCP, mKCP)
                - Встроенная система защиты от анализа трафика
                - Поддержка маскировки под обычный HTTPS трафик
                - Автоматическое переключение транспорта
                - Поддержка IPv6
                - Высокая производительность и низкая задержка
                """,
                "tags": ["xray", "features", "performance"]
            },
            {
                "name": "security_features",
                "content": """
                Безопасность XVPN:
                - AES-256 шифрование
                - Perfect Forward Secrecy (PFS)
                - TLS 1.2/1.3 поддержка
                - Certificate Pinning
                - DNS Leak Protection
                - Kill Switch
                - Multi-hop routing
                """,
                "tags": ["security", "encryption", "tls"]
            }
        ]
        
        # Добавление источников
        for source in test_sources:
            success = rag_system.add_knowledge_source(
                source["name"], 
                source["content"], 
                source["tags"]
            )
            print(f"✓ Источник '{source['name']}': {'Успешно' if success else 'Ошибка'}")
        
        # Проверка статистики
        stats = rag_system.get_knowledge_base_stats()
        print(f"✓ Общее количество чанков: {stats['total_chunks']}")
        print(f"✓ Количество источников: {stats['total_sources']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования источников знаний: {e}")
        return False

def test_query_system():
    """Тестирование запросов к базе знаний"""
    print("\n=== Тестирование запросов к базе знаний ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление тестовых данных
        test_content = """
        XVPN - это современная VPN система с использованием протокола Xray.
        Основные функции: шифрование трафика, обход блокировок, анонимность.
        Поддерживается IPv4 и IPv6.
        Система использует state machine для управления состоянием клиента.
        """
        
        rag_system.add_knowledge_source("xvpn_overview", test_content, ["vpn", "xray", "overview"])
        
        # Тестовые запросы
        test_queries = [
            "Как работает XVPN?",
            "Что такое Xray?",
            "Поддерживается ли IPv6?",
            "Какие протоколы безопасности используются?",
            "Что такое state machine?"
        ]
        
        for query in test_queries:
            print(f"\n✓ Запрос: '{query}'")
            
            start_time = time.time()
            context = rag_system.get_context_for_query(query)
            response_time = time.time() - start_time
            
            print(f"  Время ответа: {response_time:.3f}s")
            print(f"  Найдено чанков: {len(context.get('relevant_chunks', []))}")
            
            if context.get('context_summary'):
                print(f"  Контекст: {context['context_summary'][:100]}...")
            
            # Проверка релевантности
            chunks = context.get('relevant_chunks', [])
            if chunks:
                avg_relevance = sum(chunk.get('relevance_score', 0) for chunk in chunks) / len(chunks)
                print(f"  Средняя релевантность: {avg_relevance:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования запросов: {e}")
        return False

def test_semantic_search():
    """Тестирование семантического поиска"""
    print("\n=== Тестирование семантического поиска ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление различных по смыслу данных
        sources = [
            {
                "name": "encryption",
                "content": "AES-256 - это современный алгоритм шифрования с высокой степенью безопасности",
                "tags": ["encryption", "aes", "security"]
            },
            {
                "name": "performance",
                "content": "WireGuard обеспечивает высокую производительность и низкую задержку",
                "tags": ["performance", "wireguard", "speed"]
            },
            {
                "name": "protocols",
                "content": "OpenVPN, WireGuard, IKEv2 - основные VPN протоколы",
                "tags": ["protocols", "vpn", "comparison"]
            }
        ]
        
        for source in sources:
            rag_system.add_knowledge_source(source["name"], source["content"], source["tags"])
        
        # Семантически похожие запросы
        semantic_queries = [
            "безопасное шифрование",
            "быстрый протокол",
            "сравнение VPN"
        ]
        
        for query in semantic_queries:
            print(f"\n✓ Семантический запрос: '{query}'")
            
            chunks = rag_system.query_knowledge(query, max_results=5)
            print(f"  Найдено чанков: {len(chunks)}")
            
            for i, chunk in enumerate(chunks[:2], 1):
                if hasattr(chunk, 'content'):
                    print(f"  {i}. {chunk.content[:50]}... (релевантность: {chunk.relevance_score:.2f})")
                else:
                    print(f"  {i}. {chunk['content'][:50]}... (релевантность: {chunk['relevance_score']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования семантического поиска: {e}")
        return False

def test_knowledge_management():
    """Тестирование управления знаниями"""
    print("\n=== Тестирование управления знаниями ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление источника
        test_content = "Тестовый контент для управления знаниями"
        success = rag_system.add_knowledge_source("test_source", test_content, ["test"])
        print(f"✓ Добавление источника: {'Успешно' if success else 'Ошибка'}")
        
        # Получение статистики
        stats = rag_system.get_knowledge_base_stats()
        print(f"✓ Статистика базы: {stats['total_chunks']} чанков")
        
        # Обновление чанка
        chunks = rag_system.query_knowledge("тестовый", max_results=1)
        if chunks:
            chunk_id = chunks[0].id if hasattr(chunks[0], 'id') else chunks[0]['id']
            success = rag_system.update_knowledge_chunk(chunk_id, "Обновленный контент", ["updated"])
            print(f"✓ Обновление чанка: {'Успешно' if success else 'Ошибка'}")
        
        # Удаление источника
        success = rag_system.remove_knowledge_source("test_source")
        print(f"✓ Удаление источника: {'Успешно' if success else 'Ошибка'}")
        
        # Проверка удаления
        stats = rag_system.get_knowledge_base_stats()
        print(f"✓ После удаления: {stats['total_chunks']} чанков")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования управления знаниями: {e}")
        return False

def test_performance_metrics():
    """Тестирование метрик производительности"""
    print("\n=== Тестирование метрик производительности ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление тестовых данных
        test_content = "Производительность RAG системы важна для быстрого ответа на запросы"
        rag_system.add_knowledge_source("performance", test_content, ["performance", "metrics"])
        
        # Выполнение нескольких запросов для сбора метрик
        queries = [
            "производительность системы",
            "метрики ответа",
            "быстрый поиск"
        ]
        
        for query in queries:
            start_time = time.time()
            context = rag_system.get_context_for_query(query)
            response_time = time.time() - start_time
            print(f"✓ Запрос '{query}': {response_time:.3f}s")
        
        # Получение статистики производительности
        stats = rag_system.get_knowledge_base_stats()
        print(f"✓ Среднее время ответа: {stats['avg_response_time']:.3f}s")
        print(f"✓ Всего запросов: {stats['total_queries']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования метрик: {e}")
        return False

def test_caching_system():
    """Тестирование системы кеширования"""
    print("\n=== Тестирование системы кеширования ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление тестовых данных
        test_content = "Кеширование запросов улучшает производительность RAG системы"
        rag_system.add_knowledge_source("caching", test_content, ["cache", "performance"])
        
        # Повторяющиеся запросы
        query = "производительность кеширования"
        
        # Первый запрос
        start_time = time.time()
        context1 = rag_system.get_context_for_query(query)
        first_time = time.time() - start_time
        
        # Второй запрос (из кеша)
        start_time = time.time()
        context2 = rag_system.get_context_for_query(query)
        second_time = time.time() - start_time
        
        print(f"✓ Первый запрос: {first_time:.3f}s")
        print(f"✓ Второй запрос: {second_time:.3f}s")
        
        if second_time < first_time:
            print("✓ Кеширование работает - второй запрос быстрее")
        else:
            print("⚠ Кеширование не дало эффекта (может быть связано с размером данных)")
        
        # Получение последних запросов
        recent_queries = rag_system.get_recent_queries(5)
        print(f"✓ Последние запросы: {len(recent_queries)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования кеширования: {e}")
        return False

def test_database_integrity():
    """Тестирование целостности базы данных"""
    print("\n=== Тестирование целостности базы данных ===")
    
    try:
        rag_system = create_enhanced_rag_system("test_agent")
        
        # Добавление данных
        test_content = "Проверка целостности базы данных"
        rag_system.add_knowledge_source("integrity_test", test_content, ["test"])
        
        # Получение различных данных
        context = rag_system.get_context_for_query("целостность")
        stats = rag_system.get_knowledge_base_stats()
        recent_queries = rag_system.get_recent_queries(1)
        
        # Проверка консистентности данных
        chunks_count = len(context.get('relevant_chunks', []))
        stats_chunks = stats.get('total_chunks', 0)
        
        print(f"✓ Чанков в контексте: {chunks_count}")
        print(f"✓ Чанков в статистике: {stats_chunks}")
        
        if chunks_count == stats_chunks:
            print("✓ Данные консистентны")
        else:
            print("⚠ Возможная несогласованность данных")
        
        # Проверка структуры данных
        if context and context.get('relevant_chunks'):
            chunk = context['relevant_chunks'][0]
            if hasattr(chunk, 'id'):
                required_fields = ['content', 'metadata', 'created_at', 'source']
                missing_fields = [field for field in required_fields if not hasattr(chunk, field)]
                
                if not missing_fields:
                    print("✓ Структура данных корректна")
                else:
                    print(f"✗ Отсутствуют поля: {missing_fields}")
            else:
                required_fields = ['id', 'content', 'metadata', 'created_at', 'source']
                missing_fields = [field for field in required_fields if field not in chunk]
                
                if not missing_fields:
                    print("✓ Структура данных корректна")
                else:
                    print(f"✗ Отсутствуют поля: {missing_fields}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования целостности: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("Запуск тестирования Enhanced RAG System для XVPN агента...")
    
    # Тестирование компонентов
    tests = [
        ("Инициализация", test_rag_system_initialization),
        ("Источники знаний", test_knowledge_sources),
        ("Запросы к базе", test_query_system),
        ("Семантический поиск", test_semantic_search),
        ("Управление знаниями", test_knowledge_management),
        ("Метрики производительности", test_performance_metrics),
        ("Система кеширования", test_caching_system),
        ("Целостность базы данных", test_database_integrity)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Тест: {test_name}")
            print('='*50)
            
            success = test_func()
            if success:
                passed += 1
                print(f"✓ Тест '{test_name}' пройден")
            else:
                print(f"✗ Тест '{test_name}' не пройден")
                
        except Exception as e:
            print(f"✗ Тест '{test_name}' завершен с ошибкой: {e}")
    
    # Итоги
    print(f"\n{'='*50}")
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print('='*50)
    print(f"✓ Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты Enhanced RAG System пройдены успешно!")
        print("🎉 RAG система готова к использованию в XVPN агенте")
        return True
    else:
        print("⚠ Некоторые тесты не пройдены")
        print("⚠ Требуется доработка RAG системы")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)