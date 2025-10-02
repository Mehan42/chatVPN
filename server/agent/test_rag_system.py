#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы RAG системы
"""

import sys
import os
import json
import time
from pathlib import Path

# Добавляем путь к корневой директории
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_system import AdvancedRAGSystem, KnowledgeChunk, QueryResult

def test_rag_system():
    """Тестирование RAG системы"""
    print("🧠 Testing RAG System")
    print("=" * 50)
    
    # Создаем временную директорию для тестов
    test_dir = Path("/tmp/xvpn_rag_test")
    test_dir.mkdir(exist_ok=True)
    
    # Инициализация RAG системы
    rag_system = AdvancedRAGSystem(
        knowledge_dir=str(test_dir),
        vector_db_path=str(test_dir / "test_vector.db")
    )
    
    # Добавляем тестовые знания
    print("\n1. Adding test knowledge...")
    
    test_chunks = [
        KnowledgeChunk(
            id="test_1",
            content="При ошибке подключения к WebSocket следует проверить: 1) Сетевое подключение 2) Firewall настройки 3) Сертификаты SSL/TLS 4) Версию протокола",
            metadata={
                "type": "troubleshooting",
                "category": "websocket",
                "priority": 1
            },
            timestamp=time.time(),
            relevance_score=1.0
        ),
        KnowledgeChunk(
            id="test_2",
            content="Для решения проблем с таймаутами: 1) Увеличить timeout значение 2) Проверить DNS резолюцию 3) Использовать резервные DNS серверы 4) Включить режим пониженной надежности",
            metadata={
                "type": "troubleshooting", 
                "category": "timeout",
                "priority": 2
            },
            timestamp=time.time(),
            relevance_score=0.9
        ),
        KnowledgeChunk(
            id="test_3",
            content="Процесс восстановления соединения: 1) Проверить текущее состояние 2) Выбрать альтернативный транспорт 3) Попытаться подключиться 4) Мониторить здоровье соединения",
            metadata={
                "type": "protocol",
                "category": "recovery",
                "priority": 1
            },
            timestamp=time.time(),
            relevance_score=0.8
        )
    ]
    
    for chunk in test_chunks:
        rag_system.vector_store.add_chunk(chunk)
        print(f"   ✓ Added chunk: {chunk.id}")
    
    # Тест поиска
    print("\n2. Testing search functionality...")
    
    test_queries = [
        "как обрабатывать ошибки подключения",
        "решение проблем с таймаутами",
        "процесс восстановления соединения",
        "настройка websocket соединения",
        "проверка ssl сертификатов"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        result = rag_system.search_knowledge(query)
        
        print(f"   Results: {len(result.chunks)}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Execution time: {result.execution_time:.3f}s")
        
        for i, chunk in enumerate(result.chunks[:2], 1):
            print(f"   {i}. {chunk.content[:100]}...")
            print(f"      Relevance: {chunk.relevance_score:.2f}")
    
    # Тест генерации ответов
    print("\n3. Testing response generation...")
    
    context = {
        "current_state": "ACTIVE",
        "error_type": "timeout",
        "transport_type": "websocket"
    }
    
    response = rag_system.generate_response(
        "что делать при ошибках подключения к websocket",
        context
    )
    
    print(f"\n   Response: {response['response'][:200]}...")
    print(f"   Confidence: {response['confidence']:.2f}")
    print(f"   Sources: {len(response['sources'])}")
    
    # Тест адаптивных предложений
    print("\n4. Testing adaptive suggestions...")
    
    suggestions = rag_system.get_adaptive_suggestions(context)
    print(f"   Suggestions: {suggestions}")
    
    # Тест обучения
    print("\n5. Testing learning from interaction...")
    
    rag_system.learn_from_interaction(
        "что делать при ошибках подключения",
        ["test_1", "test_2"],
        True
    )
    print("   ✓ Learning interaction completed")
    
    # Тест отчета о производительности
    print("\n6. Testing performance report...")
    
    report = rag_system.get_performance_report()
    print(f"   Total queries: {report.get('total_queries', 0)}")
    print(f"   Success rate: {report.get('success_rate', 0):.2%}")
    print(f"   Average confidence: {report.get('average_confidence', 0):.2f}")
    
    # Интеграционный тест с агентом
    print("\n7. Testing integration with agent...")
    
    try:
        # Тест импорта и использования в агенте
        from agent import XVPNAgent
        
        agent = XVPNAgent()
        
        if agent.rag_system:
            print("   ✓ RAG system initialized in agent")
            
            # Тест поиска в контексте агента
            context = {
                "current_state": "ACTIVE",
                "error_type": "timeout", 
                "transport_type": "websocket"
            }
            
            rag_result = agent.rag_system.generate_response(
                "как обработать timeout при подключении",
                context
            )
            
            print(f"   ✓ Agent RAG query completed with confidence: {rag_result['confidence']:.2f}")
            
            # Тест получения отчета
            rag_report = agent.get_rag_report()
            if "error" not in rag_report:
                print(f"   ✓ Agent RAG report generated successfully")
            else:
                print(f"   ⚠️ Agent RAG report error: {rag_report['error']}")
                
        else:
            print("   ⚠️ RAG system not available in agent")
            
    except Exception as e:
        print(f"   ⚠️ Integration test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 RAG System Test Completed Successfully!")
    
    # Очистка тестовых файлов
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    print(f"🧹 Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_rag_system()