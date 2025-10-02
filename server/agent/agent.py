#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "sqlite3"]
# ///

"""
XVPN Main Agent (State Machine + RAG + Health Monitor)
Основной агент с логикой мониторинга, переключения транспортов и самовосстановления
"""

import time
import sqlite3
import json
import os
import logging
import requests
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from enhanced_rag_system import create_enhanced_rag_system

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы - используем относительные пути и домашнюю директорию
from pathlib import Path

# Определяем базовую директорию в домашней папке пользователя или в temp
BASE_DIR = Path.home() / ".xvpn"
if not BASE_DIR.exists():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "agent.db"
KNOWLEDGE_PATH = BASE_DIR / "knowledge"
LOG_FILE = BASE_DIR / "logs" / "agent.log"
MANIFEST_URL = "https://127.0.0.1:8443/transports/manifest.json"
HEALTH_URL = "https://127.0.0.1:8443/mcp/v1/vpn.health"

# Минимальные пороги
MIN_MASK_THRESHOLD = 3
MIN_HOLD_TIME = 30  # секунд
POLL_INTERVAL = 30  # секунд
MAX_CONSECUTIVE_FAILS = 3

class AgentState(Enum):
    """Состояния агента"""
    IDLE = "IDLE"
    DISCOVER = "DISCOVER"  
    CONNECTING = "CONNECTING"
    ACTIVE = "ACTIVE"
    FALLBACK = "FALLBACK"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"

class Transport:
    """Класс для транспорта"""
    def __init__(self, transport_data: Dict):
        self.id = transport_data["id"]
        self.name = transport_data["name"]
        self.type = transport_data["type"]
        self.priority = transport_data["priority"]
        self.config = transport_data["config"]
        self.fail_count = 0
        self.last_success = 0

class XVPNAgent:
    """Главный агент системы"""
    
    def __init__(self):
        self.state = AgentState.IDLE
        self.current_transport: Optional[Transport] = None
        self.transports: List[Transport] = []
        self.knowledge = self._load_knowledge()
        self.fallback_resources = self._load_fallback()
        
        # Инициализация улучшенной RAG системы
        try:
            self.rag_system = create_enhanced_rag_system("xvpn_agent")
            logger.info("✅ Enhanced RAG system initialized successfully")
        except Exception as e:
            logger.error(f"⚠️ Failed to initialize Enhanced RAG system: {e}")
            self.rag_system = None
        
        # Создание директорий если не существуют с правильными правами
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True, mode=0o755)
        os.makedirs(KNOWLEDGE_PATH, exist_ok=True, mode=0o755)
        
        # Устанавливаем правильные права для директорий
        os.chmod(os.path.dirname(LOG_FILE), 0o755)
        os.chmod(KNOWLEDGE_PATH, 0o755)
        
    def _load_knowledge(self) -> Dict:
        """Загрузка базы знаний из protocols.md"""
        knowledge = {}
        protocols_path = os.path.join(KNOWLEDGE_PATH, "protocols.md")
        
        if os.path.exists(protocols_path):
            try:
                with open(protocols_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Простой парсер markdown для протоколов
                    sections = content.split('# Protocol: ')
                    for section in sections[1:]:  # Пропускаем первую пустую секцию
                        lines = section.split('\n')
                        protocol_name = lines[0].strip()
                        steps = [line.strip('- ') for line in lines[1:] if line.startswith('- ')]
                        knowledge[protocol_name] = steps
            except Exception as e:
                logger.error(f"Failed to load knowledge: {e}")
        
        return knowledge
    
    def _load_fallback(self) -> List[Dict]:
        """Загрузка резервных ресурсов"""
        fallback_path = os.path.join(KNOWLEDGE_PATH, "fallback.json")
        fallback = []
        
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r') as f:
                    data = json.load(f)
                    fallback = data.get("resources", [])
                    # Сортировка по приоритету
                    fallback.sort(key=lambda x: x.get("priority", 100))
            except Exception as e:
                logger.error(f"Failed to load fallback resources: {e}")
        
        return fallback
    
    def log_event(self, state: str, action: str, result: str, details: str = ""):
        """Логирование событий в БД и файл"""
        timestamp = int(time.time())
        
        # Логирование в БД
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO logs VALUES (?,?,?,?,?,?)",
                (timestamp, "agent", state, action, result, details)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log to DB: {e}")
        
        # Логирование в файл
        try:
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp} {state} {action} {result} {details}\n")
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
        
        logger.info(f"[{state}] {action} -> {result} {details}")
    
    def fetch_manifest(self) -> Optional[Dict]:
        """Получение манифеста транспортов"""
        try:
            response = requests.get(MANIFEST_URL, verify=False, timeout=10)
            if response.status_code == 200:
                manifest = response.json()
                self.log_event("FETCH", "manifest", "success", f"v{manifest.get('version', 'unknown')}")
                return manifest
            else:
                self.log_event("FETCH", "manifest", "http_error", f"status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.log_event("FETCH", "manifest", "network_error", str(e))
            return self._try_fallback_manifest()
        except Exception as e:
            self.log_event("FETCH", "manifest", "error", str(e))
        
        return None
    
    def _try_fallback_manifest(self) -> Optional[Dict]:
        """Попытка получить манифест из резервных источников"""
        for resource in self.fallback_resources:
            if resource["type"] == "static_manifest":
                try:
                    response = requests.get(resource["value"], timeout=10)
                    if response.status_code == 200:
                        self.log_event("FALLBACK", "manifest", "success", resource["value"])
                        return response.json()
                except Exception as e:
                    self.log_event("FALLBACK", "manifest", "failed", f"{resource['value']}: {str(e)}")
        
        return None
    
    def run_health_checks(self) -> Dict:
        """Выполнение проверок здоровья"""
        try:
            response = requests.get(HEALTH_URL, verify=False, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                mask_score = health_data.get("mask_score", 0)
                
                self.log_event("HEALTH", "check", "success", f"score={mask_score}")
                return health_data
            else:
                self.log_event("HEALTH", "check", "api_error", f"status {response.status_code}")
        except Exception as e:
            self.log_event("HEALTH", "check", "error", str(e))
        
        # Дефолтные значения при ошибке
        return {"mask_score": 1, "status": "ERROR"}
    
    def load_transports(self, manifest: Dict):
        """Загрузка транспортов из манифеста"""
        self.transports = []
        transport_data = manifest.get("transports", [])
        
        for t in transport_data:
            transport = Transport(t)
            self.transports.append(transport)
        
        # Сортировка по приоритету
        self.transports.sort(key=lambda x: x.priority)
        self.log_event("LOAD", "transports", "success", f"loaded {len(self.transports)} transports")
    
    def select_next_transport(self, current: Optional[Transport] = None) -> Optional[Transport]:
        """Выбор следующего транспорта для подключения"""
        if not self.transports:
            return None
        
        if current is None:
            # Выбираем первый доступный
            return self.transports[0]
        
        # Находим текущий в списке и берем следующий
        try:
            current_idx = self.transports.index(current)
            if current_idx + 1 < len(self.transports):
                return self.transports[current_idx + 1]
        except ValueError:
            pass
        
        return None
    
    def connect_transport(self, transport: Transport) -> bool:
        """Подключение к транспорту"""
        self.log_event("CONNECT", "attempt", "start", f"{transport.id} ({transport.name})")
        
        # Симуляция подключения (здесь должна быть реальная логика подключения)
        try:
            time.sleep(2)  # Имитация времени подключения
            
            # Простая проверка: если fail_count меньше 2, считаем успешным
            if transport.fail_count < MAX_CONSECUTIVE_FAILS:
                transport.last_success = int(time.time())
                transport.fail_count = 0
                self.current_transport = transport
                self.log_event("CONNECT", "success", f"{transport.id}", f"type={transport.type}")
                return True
            else:
                transport.fail_count += 1
                self.log_event("CONNECT", "failed", f"{transport.id}", f"fail_count={transport.fail_count}")
                return False
        except Exception as e:
            transport.fail_count += 1
            self.log_event("CONNECT", "error", f"{transport.id}", str(e))
            return False
    
    def run_playbook(self, situation: str):
        """Выполнение playbook для конкретной ситуации с использованием Enhanced RAG"""
        if self.rag_system:
            try:
                # Используем Enhanced RAG систему для поиска релевантных действий
                context = self.rag_system.get_context_for_query(situation)
                
                if context and context.get('relevant_chunks'):
                    logger.info(f"🧠 Enhanced RAG context retrieved for situation: {situation}")
                    
                    # Записываем в лог
                    self.log_event("RAG", "retrieval", "success",
                                 f"situation={situation}, chunks={len(context.get('relevant_chunks', []))}")
                    
                    # Выполняем действия на основе контекста
                    for i, chunk in enumerate(context.get('relevant_chunks', [])[:3], 1):
                        logger.info(f"RAG Action {i}: {chunk['content'][:100]}...")
                        self.log_event("RAG", f"action_{i}", "retrieved",
                                     f"source={chunk['source']}, relevance={chunk['relevance_score']:.2f}")
                        time.sleep(1)
                    
                    # Добавляем контекст в базу знаний для обучения
                    knowledge_content = f"Situation: {situation}\nContext: {context.get('context_summary', '')}"
                    self.rag_system.add_knowledge_source("playbook_execution", knowledge_content, ["playbook", "recovery"])
                    
                    return
                    
            except Exception as e:
                logger.error(f"Enhanced RAG playbook execution failed: {e}")
        
        # Традиционный playbook как fallback
        if situation in self.knowledge:
            steps = self.knowledge[situation]
            self.log_event("PLAYBOOK", "execute", situation, f"{len(steps)} steps")
            
            for i, step in enumerate(steps, 1):
                logger.info(f"Playbook [{situation}] Step {i}: {step}")
                self.log_event("PLAYBOOK", f"step_{i}", step)
                time.sleep(1)  # Пауза между шагами
        else:
            self.log_event("PLAYBOOK", "not_found", situation)
    
    def transport_lost(self) -> bool:
        """Проверка потери связи с текущим транспортом"""
        if not self.current_transport:
            return False
        
        # Простая проверка: если не было успешных коннектов более 2 минут
        time_since_success = int(time.time()) - self.current_transport.last_success
        return time_since_success > 120
    
    def state_machine_cycle(self):
        """Один цикл state machine"""
        if self.state == AgentState.IDLE:
            manifest = self.fetch_manifest()
            if manifest:
                self.load_transports(manifest)
                self.state = AgentState.DISCOVER
            else:
                self.run_playbook("API /manifest unreachable > 5min")
                time.sleep(60)  # Ждем минуту перед повторной попыткой
        
        elif self.state == AgentState.DISCOVER:
            transport = self.select_next_transport()
            if transport:
                self.state = AgentState.CONNECTING
                if self.connect_transport(transport):
                    self.state = AgentState.ACTIVE
                else:
                    # Пробуем следующий транспорт
                    next_transport = self.select_next_transport(transport)
                    if next_transport:
                        self.state = AgentState.DISCOVER
                    else:
                        self.state = AgentState.FALLBACK
                        self.run_playbook("All transports down")
            else:
                self.state = AgentState.FALLBACK
        
        elif self.state == AgentState.ACTIVE:
            health = self.run_health_checks()
            mask_score = health.get("mask_score", 0)
            
            if mask_score < MIN_MASK_THRESHOLD:
                self.log_event("MASK_FAIL", "threshold", "breach", f"score={mask_score}")
                self.state = AgentState.FALLBACK
                self.run_playbook("T0 failed 3x")
            elif self.transport_lost():
                self.log_event("TRANSPORT_LOST", "connection", "lost")
                self.state = AgentState.FALLBACK
            # Иначе остаемся в ACTIVE
        
        elif self.state == AgentState.FALLBACK:
            # Пытаемся переключиться на следующий транспорт
            next_transport = self.select_next_transport(self.current_transport)
            if next_transport:
                if self.connect_transport(next_transport):
                    self.state = AgentState.ACTIVE
                else:
                    # Если не удалось подключиться к следующему
                    next_next = self.select_next_transport(next_transport)
                    if not next_next:
                        self.state = AgentState.MANUAL_INTERVENTION
                        self.run_playbook("All transports down")
            else:
                self.state = AgentState.MANUAL_INTERVENTION
        
        elif self.state == AgentState.MANUAL_INTERVENTION:
            self.log_event("MANUAL", "intervention", "required", "All automatic recovery failed")
            time.sleep(300)  # Ждем 5 минут перед повторной попыткой
            self.state = AgentState.IDLE  # Перезапуск цикла
    
    def get_rag_report(self) -> Dict:
        """Получение отчета о производительности Enhanced RAG системы"""
        if not self.rag_system:
            return {"error": "Enhanced RAG system not available"}
        
        try:
            stats = self.rag_system.get_knowledge_base_stats()
            return {
                "total_chunks": stats.get("total_chunks", 0),
                "total_sources": stats.get("total_sources", 0),
                "avg_response_time": stats.get("avg_response_time", 0),
                "total_queries": stats.get("total_queries", 0),
                "agent_uuid": self.rag_system.agent_uuid,
                "system_status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get Enhanced RAG report: {e}")
            return {"error": str(e)}
    
    def get_rag_suggestions(self) -> List[str]:
        """Получение адаптивных предложений от Enhanced RAG системы"""
        if not self.rag_system:
            return []
        
        try:
            # Формируем контекст на основе текущего состояния
            context = {
                "current_state": self.state.value,
                "transport_type": self.current_transport.type if self.current_transport else "unknown"
            }
            
            # Запрашиваем знания по текущей ситуации
            query = f"что делать при {self.state.value}"
            relevant_chunks = self.rag_system.query_knowledge(query, max_results=5)
            
            suggestions = []
            for chunk in relevant_chunks:
                suggestions.append(chunk['content'][:100] + "...")
            
            return suggestions
        except Exception as e:
            logger.error(f"Failed to get Enhanced RAG suggestions: {e}")
            return []
    
    def initialize_rag_knowledge_base(self):
        """Инициализация базы знаний агента"""
        if not self.rag_system:
            logger.warning("Enhanced RAG system not available")
            return
        
        try:
            # Добавляем базовые знания о VPN
            vpn_knowledge = """
            XVPN - современная VPN система с использованием протокола Xray
            Основные функции:
            - Шифрование трафика AES-256
            - Обход блокировок
            - Анонимность и приватность
            - Поддержка IPv4 и IPv6
            - Автоматическое переключение транспорта
            - State machine для управления состоянием
            """
            
            self.rag_system.add_knowledge_source("vpn_basics", vpn_knowledge, ["vpn", "basics", "xray"])
            
            # Добавляем знания о протоколах
            protocols_knowledge = """
            VPN протоколы:
            - OpenVPN: безопасный и гибкий протокол
            - WireGuard: современный высокопроизводительный протокол
            - IKEv2: быстрый и стабильный протокол
            - SSTP: протокол для обхода блокировок
            - L2TP/IPsec: комбинация протоколов для безопасности
            """
            
            self.rag_system.add_knowledge_source("vpn_protocols", protocols_knowledge, ["protocols", "security"])
            
            # Добавляем знания о восстановлении
            recovery_knowledge = """
            Восстановление VPN соединения:
            1. Проверка состояния соединения
            2. Анализ здоровья системы
            3. Переключение на альтернативный транспорт
            4. Повторная аутентификация
            5. Логирование ошибки для анализа
            """
            
            self.rag_system.add_knowledge_source("recovery_procedures", recovery_knowledge, ["recovery", "procedures"])
            
            logger.info("✅ Enhanced RAG knowledge base initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced RAG knowledge base: {e}")
    
    def run(self):
        """Главный цикл агента"""
        logger.info("🤖 Starting XVPN Agent")
        self.log_event("AGENT", "startup", "success", f"PID={os.getpid()}")
        
        # Инициализация базы знаний Enhanced RAG
        if self.rag_system:
            try:
                self.initialize_rag_knowledge_base()
                logger.info("🧠 Enhanced RAG knowledge base initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Enhanced RAG knowledge base: {e}")
        
        try:
            cycle_count = 0
            while True:
                # Каждые 10 циклов выводим отчет о Enhanced RAG системе
                if cycle_count % 10 == 0 and self.rag_system:
                    try:
                        rag_report = self.get_rag_report()
                        if "error" not in rag_report:
                            logger.info(f"🧠 Enhanced RAG Report - Chunks: {rag_report.get('total_chunks', 0)}, "
                                       f"Sources: {rag_report.get('total_sources', 0)}, "
                                       f"Queries: {rag_report.get('total_queries', 0)}, "
                                       f"Avg Response Time: {rag_report.get('avg_response_time', 0):.3f}s")
                    except Exception as e:
                        logger.error(f"Failed to generate Enhanced RAG report: {e}")
                
                self.state_machine_cycle()
                time.sleep(POLL_INTERVAL)
                cycle_count += 1
                
        except KeyboardInterrupt:
            logger.info("🛑 Agent stopped by user")
            self.log_event("AGENT", "shutdown", "manual")
        except Exception as e:
            logger.error(f"💥 Agent crashed: {e}")
            self.log_event("AGENT", "crash", "error", str(e))
            raise

if __name__ == "__main__":
    agent = XVPNAgent()
    agent.run()
