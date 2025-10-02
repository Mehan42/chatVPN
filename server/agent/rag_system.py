#!/usr/bin/env python3
"""
Улучшенная RAG система для XVPN агента с использованием ChromaDB
Семантический поиск, контекстуальное понимание и адаптивное обучение
"""

import json
import os
import re
import time
import hashlib
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import requests

from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeChunk:
    """Чанк знания для векторизации"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: float = 0.0

@dataclass
class QueryResult:
    """Результат поиска в базе знаний"""
    chunks: List[KnowledgeChunk]
    total_chunks: int
    query_context: str
    execution_time: float
    confidence_score: float = 0.0

class ChromaVectorStore:
    """Векторное хранилище на базе ChromaDB"""
    
    def __init__(self, collection_name: str = "xvpn_knowledge", persist_directory: str = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.path.join(os.path.expanduser("~"), ".xvpn", "chroma_db")
        
        # Создаем директорию для хранения ChromaDB
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Инициализация ChromaDB client
        self.chroma_client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.persist_directory
        ))
        
        # Загрузка или создание коллекции
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)
        
        # Загрузка модели для эмбеддингов
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SentenceTransformer model loaded successfully")
        except Exception as e:
            logger.error(f"⚠️ Failed to load SentenceTransformer model: {e}")
            self.embedding_model = None
    
    def _get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга для текста"""
        if self.embedding_model is None:
            # Fallback: простой хэш как эмбеддинг
            return [float(ord(c)) / 255.0 for c in text[:384]]  # ограничиваем длину
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Fallback: простой хэш как эмбеддинг
            return [float(ord(c)) / 255.0 for c in text[:384]]
    
    def add_chunk(self, chunk: KnowledgeChunk):
        """Добавление чанка в ChromaDB"""
        try:
            # Получаем эмбеддинг
            embedding = self._get_embedding(chunk.content)
            
            # Добавляем в коллекцию
            self.collection.add(
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[chunk.metadata],
                ids=[chunk.id]
            )
            
            logger.debug(f"✓ Added chunk: {chunk.id}")
            
        except Exception as e:
            logger.error(f"Failed to add chunk {chunk.id}: {e}")
    
    def search(self, query: str, limit: int = 10, min_relevance: float = 0.1) -> List[KnowledgeChunk]:
        """Поиск в ChromaDB"""
        start_time = time.time()
        
        try:
            # Получаем эмбеддинг запроса
            query_embedding = self._get_embedding(query)
            
            # Ищем похожие документы
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Преобразуем результаты в KnowledgeChunk
            chunks = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0], 
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    # Конвертируем расстояние в релевантность (0-1)
                    relevance = 1.0 - min(distance, 1.0)
                    
                    if relevance >= min_relevance:
                        chunk = KnowledgeChunk(
                            id=f"search_result_{i}",
                            content=doc,
                            metadata=metadata or {},
                            timestamp=time.time(),
                            relevance_score=relevance,
                            access_count=0,
                            last_accessed=0.0
                        )
                        chunks.append(chunk)
            
            logger.info(f"Search executed in {time.time() - start_time:.3f}s, found {len(chunks)} results")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def update_chunk(self, chunk_id: str, metadata: Dict = None, relevance_score: float = None):
        """Обновление метаданных чанка"""
        try:
            # Получаем текущие данные
            current = self.collection.get(ids=[chunk_id])
            
            if current["documents"]:
                # Обновляем метаданные
                new_metadata = current["metadatas"][0] or {}
                if metadata:
                    new_metadata.update(metadata)
                if relevance_score is not None:
                    new_metadata["relevance_score"] = relevance_score
                
                # Переиндексируем с новыми метаданными
                self.collection.update(
                    ids=[chunk_id],
                    metadatas=[new_metadata]
                )
                
        except Exception as e:
            logger.error(f"Failed to update chunk {chunk_id}: {e}")
    
    def get_collection_stats(self) -> Dict:
        """Получение статистики коллекции"""
        try:
            count = self.collection.count()
            stats = {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

class AdvancedRAGSystem:
    """Продвинутая RAG система с адаптивным обучением на базе ChromaDB"""
    
    def __init__(self, knowledge_dir: str, persist_directory: str = None):
        self.knowledge_dir = Path(knowledge_dir)
        self.persist_directory = persist_directory
        
        # Инициализация компонентов
        self.vector_store = ChromaVectorStore(persist_directory=persist_directory)
        self.knowledge_base = self._load_knowledge_base()
        self.query_history = []
        self.performance_metrics = defaultdict(list)
        
        # Параметры адаптации
        self.adaptation_threshold = 5  # количество запросов для адаптации
        self.relevance_boost = 0.15    # усиление релевантности
        self.relevance_decay = 0.98    #衰减系数 релевантности
        
        self._initialize_knowledge()
    
    def _load_knowledge_base(self) -> Dict:
        """Загрузка базовой базы знаний"""
        knowledge_base = {
            "protocols": {},
            "fallback_resources": [],
            "error_patterns": {},
            "performance_metrics": {},
            "adaptive_rules": []
        }
        
        return knowledge_base
    
    def _initialize_knowledge(self):
        """Инициализация знаний из файлов"""
        # Загрузка протоколов
        protocols_file = self.knowledge_dir / "protocols.md"
        if protocols_file.exists():
            self._load_protocols(protocols_file)
        
        # Загрузка fallback ресурсов
        fallback_file = self.knowledge_dir / "fallback.json"
        if fallback_file.exists():
            self._load_fallback_resources(fallback_file)
        
        logger.info(f"✅ Knowledge initialized with {self.vector_store.get_collection_stats().get('total_documents', 0)} documents")
    
    def _load_protocols(self, protocols_file: Path):
        """Загрузка и парсинг протоколов"""
        try:
            with open(protocols_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Преобразуем JSON в протоколы
                protocols_data = json.loads(content)
                
                for protocol_name, protocol_steps in protocols_data.items():
                    chunk = KnowledgeChunk(
                        id=f"protocol_{protocol_name}",
                        content=f"Protocol: {protocol_name}\nSteps: {'; '.join(protocol_steps)}",
                        metadata={
                            "type": "protocol",
                            "name": protocol_name,
                            "steps_count": len(protocol_steps),
                            "category": "network_management",
                            "priority": "high"
                        },
                        timestamp=time.time(),
                        relevance_score=1.0
                    )
                    self.vector_store.add_chunk(chunk)
                    
        except Exception as e:
            logger.error(f"Failed to load protocols: {e}")
    
    def _load_fallback_resources(self, fallback_file: Path):
        """Загрузка fallback ресурсов"""
        try:
            with open(fallback_file, 'r') as f:
                fallback_data = json.load(f)
                self.knowledge_base["fallback_resources"] = fallback_data.get("resources", [])
                
                # Добавляем ресурсы в векторное хранилище
                for i, resource in enumerate(self.knowledge_base["fallback_resources"]):
                    chunk = KnowledgeChunk(
                        id=f"fallback_{i}",
                        content=f"{resource['type']}: {resource['value']} (Priority: {resource['priority']})",
                        metadata=resource,
                        timestamp=time.time(),
                        relevance_score=1.0 / (resource.get("priority", 1) ** 2)
                    )
                    self.vector_store.add_chunk(chunk)
                    
        except Exception as e:
            logger.error(f"Failed to load fallback resources: {e}")
    
    def search_knowledge(self, query: str, context: Dict = None) -> QueryResult:
        """Поиск знаний с контекстуальным усилением"""
        start_time = time.time()
        
        # Расширенный поиск с учетом контекста
        enhanced_query = self._enhance_query(query, context)
        
        # Поиск в векторном хранилище
        chunks = self.vector_store.search(enhanced_query, limit=10)
        
        # Ранжирование результатов
        ranked_chunks = self._rank_chunks(chunks, query, context)
        
        # Рассчитываем метрики
        execution_time = time.time() - start_time
        confidence_score = self._calculate_confidence(ranked_chunks, query)
        
        # Сохраняем в историю запросов
        self._save_to_history(query, ranked_chunks, confidence_score)
        
        return QueryResult(
            chunks=ranked_chunks,
            total_chunks=len(ranked_chunks),
            query_context=enhanced_query,
            execution_time=execution_time,
            confidence_score=confidence_score
        )
    
    def _enhance_query(self, query: str, context: Dict = None) -> str:
        """Усиление запроса на основе контекста"""
        enhanced = query
        
        # Добавление контекстной информации
        if context:
            if context.get("current_state"):
                enhanced += f" state:{context['current_state']}"
            if context.get("error_type"):
                enhanced += f" error:{context['error_type']}"
            if context.get("transport_type"):
                enhanced += f" transport:{context['transport_type']}"
        
        # Добавление временного контекста
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:
            enhanced += " business_hours"
        
        return enhanced
    
    def _rank_chunks(self, chunks: List[KnowledgeChunk], query: str, context: Dict = None) -> List[KnowledgeChunk]:
        """Ранжирование чанков по релевантности"""
        if not chunks:
            return []
        
        # Факторы ранжирования
        for chunk in chunks:
            base_score = chunk.relevance_score
            
            # Бонус за свежесть
            age = time.time() - chunk.timestamp
            freshness_bonus = max(0, 1 - age / (30 * 24 * 3600))  # 30 дней
            
            # Бонус за популярность
            popularity_bonus = min(chunk.access_count / 10, 0.5)
            
            # Контекстуальный бонус
            context_bonus = 0
            if context:
                if context.get("current_state") in chunk.metadata.get("related_states", []):
                    context_bonus = 0.3
                if context.get("error_type") in chunk.metadata.get("related_errors", []):
                    context_bonus = 0.4
            
            # Итоговый счет
            chunk.relevance_score = base_score + freshness_bonus * 0.2 + popularity_bonus * 0.1 + context_bonus
            
        return sorted(chunks, key=lambda x: x.relevance_score, reverse=True)
    
    def _calculate_confidence(self, chunks: List[KnowledgeChunk], query: str) -> float:
        """Расчет уверенности в результатах"""
        if not chunks:
            return 0.0
        
        # Усредненная релевантность топ-3 результатов
        top_chunks = chunks[:3]
        avg_relevance = sum(chunk.relevance_score for chunk in top_chunks) / len(top_chunks)
        
        # Дополнительно: проверка покрытия запроса
        query_keywords = set(re.findall(r'\w+', query.lower()))
        coverage_score = 0
        
        for chunk in top_chunks:
            chunk_keywords = set(re.findall(r'\w+', chunk.content.lower()))
            intersection = query_keywords.intersection(chunk_keywords)
            coverage_score += len(intersection) / len(query_keywords) if query_keywords else 0
        
        avg_coverage = coverage_score / len(top_chunks) if top_chunks else 0
        
        # Итоговый счет уверенности
        confidence = (avg_relevance * 0.7 + avg_coverage * 0.3)
        return min(confidence, 1.0)
    
    def _save_to_history(self, query: str, chunks: List[KnowledgeChunk], confidence: float):
        """Сохранение запроса в историю"""
        history_entry = {
            "timestamp": time.time(),
            "query": query,
            "result_count": len(chunks),
            "confidence": confidence,
            "avg_relevance": sum(c.relevance_score for c in chunks) / len(chunks) if chunks else 0
        }
        
        self.query_history.append(history_entry)
        
        # Ограничиваем размер истории
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-500:]
    
    def learn_from_interaction(self, query: str, clicked_chunks: List[str], success: bool):
        """Обучение на основе взаимодействия пользователя"""
        if not clicked_chunks:
            return
        
        # Увеличиваем релевантность выбранных чанков
        for chunk_id in clicked_chunks:
            try:
                self.vector_store.update_chunk(
                    chunk_id,
                    relevance_score=1.0 if success else 0.5
                )
            except Exception as e:
                logger.error(f"Failed to update chunk {chunk_id}: {e}")
        
        logger.info(f"Learned from interaction: query='{query}', success={success}")
    
    def get_adaptive_suggestions(self, current_context: Dict) -> List[str]:
        """Получение адаптивных предложений на основе истории"""
        suggestions = []
        
        # Анализ недавних запросов
        recent_queries = [h["query"] for h in self.query_history[-10:]]
        
        # Поиск общих паттернов
        if recent_queries:
            common_patterns = self._find_common_patterns(recent_queries)
            suggestions.extend(common_patterns[:3])
        
        # Контекстуальные предложения
        if current_context.get("current_state"):
            state_suggestions = [
                f"handling_{current_context['current_state']}",
                f"troubleshoot_{current_context['current_state']}"
            ]
            suggestions.extend(state_suggestions)
        
        return suggestions[:5]
    
    def _find_common_patterns(self, queries: List[str]) -> List[str]:
        """Поиск общих паттернов в запросах"""
        patterns = []
        
        # Простая реализация: ищем общие слова
        word_freq = defaultdict(int)
        for query in queries:
            words = re.findall(r'\w+', query.lower())
            for word in words:
                if len(word) > 3:  # Игнорируем короткие слова
                    word_freq[word] += 1
        
        # Выбираем самые частые слова
        common_words = [word for word, count in word_freq.items() if count >= 2]
        patterns.extend(common_words)
        
        return patterns
    
    def generate_response(self, query: str, context: Dict = None) -> Dict:
        """Генерация ответа на основе найденных знаний"""
        # Поиск знаний
        search_result = self.search_knowledge(query, context)
        
        if not search_result.chunks:
            return {
                "response": "Извините, я не нашел релевантной информации по вашему запросу.",
                "confidence": 0.0,
                "sources": [],
                "suggestions": []
            }
        
        # Формирование ответа
        response_parts = []
        sources = []
        
        for i, chunk in enumerate(search_result.chunks[:3]):
            response_parts.append(f"{i+1}. {chunk.content}")
            sources.append({
                "id": chunk.id,
                "type": chunk.metadata.get("type", "unknown"),
                "relevance": chunk.relevance_score,
                "last_accessed": datetime.fromtimestamp(chunk.last_accessed).isoformat()
            })
        
        # Генерация адаптивных предложений
        suggestions = self.get_adaptive_suggestions(context or {})
        
        return {
            "response": "\n\n".join(response_parts),
            "confidence": search_result.confidence_score,
            "sources": sources,
            "suggestions": suggestions,
            "metadata": {
                "total_chunks_found": search_result.total_chunks,
                "search_time": search_result.execution_time,
                "query_context": search_result.query_context
            }
        }
    
    def get_performance_report(self) -> Dict:
        """Генерация отчета о производительности"""
        if not self.query_history:
            return {"message": "Нет данных для анализа"}
        
        recent_history = self.query_history[-100:]  # Последние 100 запросов
        
        avg_confidence = sum(h["confidence"] for h in recent_history) / len(recent_history)
        avg_relevance = sum(h["avg_relevance"] for h in recent_history) / len(recent_history)
        
        # Расчет метрик
        successful_queries = [h for h in recent_history if h["confidence"] > 0.5]
        success_rate = len(successful_queries) / len(recent_history)
        
        # Статистика векторного хранилища
        collection_stats = self.vector_store.get_collection_stats()
        
        return {
            "total_queries": len(self.query_history),
            "recent_queries": len(recent_history),
            "average_confidence": avg_confidence,
            "average_relevance": avg_relevance,
            "success_rate": success_rate,
            "top_queries": self._get_top_queries(recent_history),
            "performance_trend": self._analyze_performance_trend(recent_history),
            "collection_stats": collection_stats
        }
    
    def _get_top_queries(self, history: List[Dict], limit: int = 5) -> List[Dict]:
        """Получение самых частых запросов"""
        query_counts = defaultdict(int)
        for entry in history:
            query_counts[entry["query"]] += 1
        
        return sorted([
            {"query": query, "count": count}
            for query, count in query_counts.items()
        ], key=lambda x: x["count"], reverse=True)[:limit]
    
    def _analyze_performance_trend(self, history: List[Dict]) -> Dict:
        """Анализ тренда производительности"""
        if len(history) < 10:
            return {"insufficient_data": True}
        
        # Разделяем историю на две части
        mid_point = len(history) // 2
        first_half = history[:mid_point]
        second_half = history[mid_point:]
        
        first_avg = sum(h["confidence"] for h in first_half) / len(first_half)
        second_avg = sum(h["confidence"] for h in second_half) / len(second_half)
        
        trend = "improving" if second_avg > first_avg else "declining" if second_avg < first_avg else "stable"
        
        return {
            "trend": trend,
            "first_half_avg": first_avg,
            "second_half_avg": second_avg,
            "change": second_avg - first_avg
        }

# Пример использования
if __name__ == "__main__":
    # Инициализация RAG системы
    rag_system = AdvancedRAGSystem(
        knowledge_dir="server/agent/knowledge",
        persist_directory=os.path.join(os.path.expanduser("~"), ".xvpn", "chroma_db")
    )
    
    # Пример поиска
    context = {
        "current_state": "ACTIVE",
        "error_type": "timeout",
        "transport_type": "websocket"
    }
    
    result = rag_system.generate_response(
        "как обрабатывать таймауты при подключении к вебсокетам",
        context
    )
    
    print("Ответ:", result["response"])
    print("Уверенность:", result["confidence"])
    print("Источники:", result["sources"])
    
    # Получение отчета о производительности
    report = rag_system.get_performance_report()
    print("Отчет о производительности:", report)