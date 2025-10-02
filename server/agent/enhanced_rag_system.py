#!/usr/bin/env python3
# Enhanced RAG System for XVPN Agent
# Абсолютный путь: ~/chatvpn/server/agent/enhanced_rag_system.py

import os
import json
import time
import logging
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import uuid

# Для RAG системы
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available. Using fallback RAG system.")

# Для эмбеддингов
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: Sentence-transformers not available. Using TF-IDF fallback.")

LOG_DIR = os.path.expanduser("~/chatvpn/server/agent/logs")
LOG_FILE = os.path.join(LOG_DIR, "rag_system.log")

# Создаем директорию для логов
os.makedirs(LOG_DIR, exist_ok=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeChunk:
    """Класс для представления чанка знаний"""
    
    def __init__(self, content: str, metadata: Dict[str, Any], chunk_id: str = None):
        self.id = chunk_id or str(uuid.uuid4())
        self.content = content
        self.metadata = metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.source = metadata.get('source', 'unknown')
        self.tags = metadata.get('tags', [])
        
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'source': self.source,
            'tags': self.tags
        }

class EnhancedRAGSystem:
    """Enhanced RAG System для XVPN агента с использованием ChromaDB"""
    
    def __init__(self, agent_uuid: str):
        self.agent_uuid = agent_uuid
        
        # Используем абсолютный путь для надежности
        import os
        self.knowledge_dir = Path(os.path.expanduser('~/chatvpn/server/agent/knowledge'))
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # База данных SQLite для метаданных
        self.metadata_db_path = os.path.expanduser(f'~/chatvpn/server/agent/knowledge/rag_metadata_{agent_uuid}.db')
        self._init_metadata_database()
        
        # Инициализация ChromaDB
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=str(self.knowledge_dir / f"chroma_{agent_uuid}"))
                self.collection = self.client.get_or_create_collection(
                    name=f"xvpn_knowledge_{agent_uuid}",
                    metadata={"hnsw:space": "cosine"}
                )
                
                # Используем эмбеддинги sentence-transformers
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="all-MiniLM-L6-v2"
                    )
                else:
                    self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                    
                self.use_vector_db = True
                logger.info(f"Enhanced RAG System initialized with ChromaDB for agent {agent_uuid}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.use_vector_db = False
        else:
            self.use_vector_db = False
            logger.info("Using fallback RAG system without ChromaDB")
        
        # Метрики производительности
        self.metrics = {
            'total_queries': 0,
            'total_response_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_query_time': None
        }
        
        # Кеш для запросов
        self.query_cache = {}
        self.cache_ttl = 300  # 5 минут
        
        # Инициализация эмбеддингов для fallback
        if not self.use_vector_db and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.fallback_model = None
    
    def _init_metadata_database(self):
        """Инициализация базы данных метаданных"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_chunks (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        source TEXT,
                        tags TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        agent_uuid TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS query_contexts (
                        id TEXT PRIMARY KEY,
                        query_text TEXT NOT NULL,
                        context_data TEXT,
                        timestamp TEXT,
                        agent_uuid TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_text TEXT,
                        response_time REAL,
                        results_count INTEGER,
                        timestamp TEXT,
                        agent_uuid TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Metadata database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing metadata database: {e}")
            raise
    
    def add_knowledge_source(self, source_name: str, content: str, tags: List[str] = None) -> bool:
        """Добавление источника знаний"""
        try:
            if not content or not content.strip():
                logger.warning(f"Empty content for source: {source_name}")
                return False
            
            # Разбиваем контент на чанки
            chunks = self._chunk_content(content, source_name, tags or [])
            
            # Добавляем в векторную базу данных
            if self.use_vector_db:
                self._add_chunks_to_vector_db(chunks)
            else:
                # Fallback: используем SQLite
                self._add_chunks_to_sqlite(chunks)
            
            logger.info(f"Successfully added {len(chunks)} chunks from source: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge source: {e}")
            return False
    
    def _chunk_content(self, content: str, source_name: str, tags: List[str]) -> List[KnowledgeChunk]:
        """Разбивка контента на чанки"""
        chunks = []
        
        # Простая разбивка по параграфам
        paragraphs = content.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                chunk = KnowledgeChunk(
                    content=paragraph.strip(),
                    metadata={
                        'source': source_name,
                        'tags': tags,
                        'chunk_index': i,
                        'total_chunks': len(paragraphs)
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _add_chunks_to_vector_db(self, chunks: List[KnowledgeChunk]):
        """Добавление чанков в ChromaDB"""
        try:
            # Подготавливаем данные для ChromaDB
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            
            # Добавляем в коллекцию
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Сохраняем метаданные в SQLite
            self._save_chunks_metadata(chunks)
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector DB: {e}")
            raise
    
    def _add_chunks_to_sqlite(self, chunks: List[KnowledgeChunk]):
        """Добавление чанков в SQLite (fallback)"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                for chunk in chunks:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_chunks 
                        (id, content, metadata, source, tags, created_at, updated_at, agent_uuid)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        chunk.id,
                        chunk.content,
                        json.dumps(chunk.metadata),
                        chunk.source,
                        json.dumps(chunk.tags),
                        chunk.created_at.isoformat(),
                        chunk.updated_at.isoformat(),
                        self.agent_uuid
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error adding chunks to SQLite: {e}")
            raise
    
    def _save_chunks_metadata(self, chunks: List[KnowledgeChunk]):
        """Сохранение метаданных в SQLite"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                for chunk in chunks:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_chunks 
                        (id, content, metadata, source, tags, created_at, updated_at, agent_uuid)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        chunk.id,
                        chunk.content,
                        json.dumps(chunk.metadata),
                        chunk.source,
                        json.dumps(chunk.tags),
                        chunk.created_at.isoformat(),
                        chunk.updated_at.isoformat(),
                        self.agent_uuid
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving chunks metadata: {e}")
    
    def query_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Поиск в базе знаний"""
        try:
            start_time = time.time()
            
            # Проверяем кеш
            cache_key = hashlib.md5(query.encode()).hexdigest()
            if cache_key in self.query_cache:
                cached_data = self.query_cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    self.metrics['cache_hits'] += 1
                    logger.info(f"Cache hit for query: {query}")
                    return cached_data['results']
            
            self.metrics['cache_misses'] += 1
            
            # Поиск в векторной базе данных
            if self.use_vector_db:
                results = self._query_vector_db(query, max_results)
            else:
                # Fallback: используем поиск по ключевым словам
                results = self._query_fallback(query, max_results)
            
            # Обновляем метрики
            response_time = time.time() - start_time
            self.metrics['total_queries'] += 1
            self.metrics['total_response_time'] += response_time
            self.metrics['last_query_time'] = response_time
            
            # Сохраняем в кеш
            self.query_cache[cache_key] = {
                'results': results,
                'timestamp': time.time()
            }
            
            # Сохраняем метрики производительности
            self._save_performance_metrics(query, response_time, len(results))
            
            logger.info(f"Query '{query}' returned {len(results)} chunks in {response_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            return []
    
    def _query_vector_db(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Поиск в ChromaDB"""
        try:
            # Получаем эмбеддинг запроса
            query_embedding = self.embedding_function([query])[0]
            
            # Ищем похожие документы
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            # Форматируем результаты
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'relevance_score': results['distances'][0][i] if 'distances' in results else 0.0
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector DB: {e}")
            return []
    
    def _query_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback поиск без векторной базы данных"""
        try:
            results = []
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                # Поиск по ключевым словам
                cursor.execute('''
                    SELECT id, content, metadata, source 
                    FROM knowledge_chunks 
                    WHERE agent_uuid = ? 
                    AND (content LIKE ? OR source LIKE ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (self.agent_uuid, f'%{query}%', f'%{query}%', max_results))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    result = {
                        'id': row[0],
                        'content': row[1],
                        'metadata': json.loads(row[2]) if row[2] else {},
                        'source': row[3],
                        'relevance_score': 1.0  # Placeholder
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fallback query: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """Получение контекста для запроса"""
        try:
            chunks = self.query_knowledge(query, max_results=5)
            
            if not chunks:
                return {
                    'query': query,
                    'context_summary': '',
                    'relevant_chunks': [],
                    'total_chunks': 0,
                    'avg_relevance': 0.0
                }
            
            # Создаем сводку контекста
            context_summary = ' '.join([chunk['content'] for chunk in chunks])
            
            # Вычисляем среднюю релевантность
            avg_relevance = sum(chunk.get('relevance_score', 0) for chunk in chunks) / len(chunks)
            
            return {
                'query': query,
                'context_summary': context_summary,
                'relevant_chunks': chunks,
                'total_chunks': len(chunks),
                'avg_relevance': avg_relevance
            }
            
        except Exception as e:
            logger.error(f"Error getting context for query: {e}")
            return {
                'query': query,
                'context_summary': '',
                'relevant_chunks': [],
                'total_chunks': 0,
                'avg_relevance': 0.0
            }
    
    def update_knowledge_chunk(self, chunk_id: str, new_content: str, new_tags: List[str] = None) -> bool:
        """Обновление чанка знаний"""
        try:
            if self.use_vector_db:
                # Удаляем старый чанк и добавляем новый
                self.collection.delete(ids=[chunk_id])
                
                # Создаем новый чанк
                chunk = KnowledgeChunk(
                    content=new_content,
                    metadata={
                        'updated': True,
                        'tags': new_tags or []
                    }
                )
                
                # Добавляем в базу
                self._add_chunks_to_vector_db([chunk])
                
            else:
                # Обновляем в SQLite
                with sqlite3.connect(self.metadata_db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE knowledge_chunks 
                        SET content = ?, tags = ?, updated_at = ?
                        WHERE id = ? AND agent_uuid = ?
                    ''', (
                        new_content,
                        json.dumps(new_tags or []),
                        datetime.now().isoformat(),
                        chunk_id,
                        self.agent_uuid
                    ))
                    
                    conn.commit()
            
            logger.info(f"Successfully updated chunk: {chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge chunk: {e}")
            return False
    
    def remove_knowledge_source(self, source_name: str) -> bool:
        """Удаление источника знаний"""
        try:
            if self.use_vector_db:
                # Удаляем из ChromaDB
                results = self.collection.get(
                    where={"source": source_name}
                )
                
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
            
            # Удаляем метаданные из SQLite
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM knowledge_chunks 
                    WHERE source = ? AND agent_uuid = ?
                ''', (source_name, self.agent_uuid))
                
                conn.commit()
            
            logger.info(f"Successfully removed knowledge source: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing knowledge source: {e}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Получение статистики базы знаний"""
        try:
            stats = {
                'total_chunks': 0,
                'total_sources': 0,
                'total_queries': self.metrics['total_queries'],
                'avg_response_time': 0.0,
                'cache_hit_rate': 0.0,
                'total_cache_entries': len(self.query_cache)
            }
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                # Количество чанков
                cursor.execute('''
                    SELECT COUNT(*) FROM knowledge_chunks WHERE agent_uuid = ?
                ''', (self.agent_uuid,))
                stats['total_chunks'] = cursor.fetchone()[0]
                
                # Количество источников
                cursor.execute('''
                    SELECT COUNT(DISTINCT source) FROM knowledge_chunks WHERE agent_uuid = ?
                ''', (self.agent_uuid,))
                stats['total_sources'] = cursor.fetchone()[0]
                
                # Среднее время ответа
                if self.metrics['total_queries'] > 0:
                    stats['avg_response_time'] = self.metrics['total_response_time'] / self.metrics['total_queries']
                
                # Hit rate кеша
                total_cache_ops = self.metrics['cache_hits'] + self.metrics['cache_misses']
                if total_cache_ops > 0:
                    stats['cache_hit_rate'] = self.metrics['cache_hits'] / total_cache_ops
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return {}
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних запросов"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT query_text, response_time, results_count, timestamp
                    FROM performance_metrics
                    WHERE agent_uuid = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (self.agent_uuid, limit))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'query': row[0],
                        'response_time': row[1],
                        'results_count': row[2],
                        'timestamp': row[3]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting recent queries: {e}")
            return []
    
    def _save_performance_metrics(self, query: str, response_time: float, results_count: int):
        """Сохранение метрик производительности"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO performance_metrics (query_text, response_time, results_count, timestamp, agent_uuid)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    query,
                    response_time,
                    results_count,
                    datetime.now().isoformat(),
                    self.agent_uuid
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
    
    def clear_cache(self):
        """Очистка кеша запросов"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def export_knowledge_base(self, export_path: str) -> bool:
        """Экспорт базы знаний"""
        try:
            export_data = {
                'agent_uuid': self.agent_uuid,
                'export_timestamp': datetime.now().isoformat(),
                'stats': self.get_knowledge_base_stats(),
                'chunks': []
            }
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, content, metadata, source, tags, created_at
                    FROM knowledge_chunks 
                    WHERE agent_uuid = ?
                ''', (self.agent_uuid,))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    export_data['chunks'].append({
                        'id': row[0],
                        'content': row[1],
                        'metadata': json.loads(row[2]) if row[2] else {},
                        'source': row[3],
                        'tags': json.loads(row[4]) if row[4] else [],
                        'created_at': row[5]
                    })
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Knowledge base exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting knowledge base: {e}")
            return False
    
    def import_knowledge_base(self, import_path: str) -> bool:
        """Импорт базы знаний"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Очищаем текущую базу
            self.clear_knowledge_base()
            
            # Импортируем чанки
            for chunk_data in import_data.get('chunks', []):
                chunk = KnowledgeChunk(
                    content=chunk_data['content'],
                    metadata=chunk_data['metadata'],
                    chunk_id=chunk_data['id']
                )
                
                # Обновляем метаданные
                chunk.created_at = datetime.fromisoformat(chunk_data['created_at'])
                chunk.tags = chunk_data.get('tags', [])
                chunk.source = chunk_data.get('source', 'imported')
                
                # Добавляем в базу
                if self.use_vector_db:
                    self._add_chunks_to_vector_db([chunk])
                else:
                    self._add_chunks_to_sqlite([chunk])
            
            logger.info(f"Knowledge base imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing knowledge base: {e}")
            return False
    
    def clear_knowledge_base(self):
        """Очистка базы знаний"""
        try:
            if self.use_vector_db:
                self.collection.delete()
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM knowledge_chunks WHERE agent_uuid = ?', (self.agent_uuid,))
                cursor.execute('DELETE FROM query_contexts WHERE agent_uuid = ?', (self.agent_uuid,))
                cursor.execute('DELETE FROM performance_metrics WHERE agent_uuid = ?', (self.agent_uuid,))
                
                conn.commit()
            
            self.clear_cache()
            logger.info("Knowledge base cleared")
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")

def create_enhanced_rag_system(agent_uuid: str) -> EnhancedRAGSystem:
    """Фабричная функция для создания Enhanced RAG System"""
    return EnhancedRAGSystem(agent_uuid)

# Тестирование
if __name__ == "__main__":
    # Создаем тестовую систему
    rag_system = create_enhanced_rag_system("test_agent")
    
    # Добавляем тестовые данные
    test_sources = [
        {
            "name": "vpn_protocols",
            "content": """
            VPN протоколы:
            1. OpenVPN - безопасный и гибкий протокол с открытым исходным кодом
            2. WireGuard - современный высокопроизводительный протокол с малым кодом
            3. IKEv2 - быстрый и стабильный протокол с поддержкой мобильных устройств
            4. SSTP - протокол для обхода блокировок через HTTPS
            5. L2TP/IPsec - комбинация протоколов для высокой безопасности
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
            - Поддержка IPv6 и dual-stack
            - Высокая производительность и низкая задержка
            """,
            "tags": ["xray", "features", "performance"]
        }
    ]
    
    # Добавляем источники
    for source in test_sources:
        rag_system.add_knowledge_source(source["name"], source["content"], source["tags"])
    
    # Тестируем запросы
    queries = [
        "Какие протоколы VPN существуют?",
        "Что такое Xray?",
        "Какие есть особенности безопасности?"
    ]
    
    for query in queries:
        print(f"\nЗапрос: {query}")
        context = rag_system.get_context_for_query(query)
        print(f"Найдено чанков: {context['total_chunks']}")
        print(f"Средняя релевантность: {context['avg_relevance']:.2f}")
        if context['context_summary']:
            print(f"Контекст: {context['context_summary'][:100]}...")
    
    # Выводим статистику
    stats = rag_system.get_knowledge_base_stats()
    print(f"\nСтатистика базы: {stats}")