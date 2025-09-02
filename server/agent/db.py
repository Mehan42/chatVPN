#!/usr/bin/env python3
"""
Database utilities for XVPN Agent
Модуль для работы с SQLite базой данных
"""

import sqlite3
import time
import json
from typing import List, Dict, Optional
from contextlib import contextmanager

DB_PATH = "/opt/xvpn/agent/db/agent.db"

@contextmanager
def get_db_connection():
    """Context manager для безопасной работы с БД"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Для доступа к полям по именам
        yield conn
    finally:
        if conn:
            conn.close()

def init_database():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Создание таблиц
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protocols (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                situation TEXT NOT NULL,
                steps TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fallback (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                priority INTEGER DEFAULT 100,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                ts INTEGER NOT NULL,
                component TEXT NOT NULL,
                state TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                details TEXT
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_component ON logs(component)")
        
        conn.commit()

def log_event(component: str, state: str, action: str, result: str, details: str = ""):
    """Добавление события в лог"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs VALUES (?,?,?,?,?,?)",
            (int(time.time()), component, state, action, result, details)
        )
        conn.commit()

def get_recent_logs(component: str = None, limit: int = 100) -> List[Dict]:
    """Получение последних записей логов"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if component:
            cursor.execute(
                "SELECT * FROM logs WHERE component=? ORDER BY ts DESC LIMIT ?",
                (component, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM logs ORDER BY ts DESC LIMIT ?",
                (limit,)
            )
        
        return [dict(row) for row in cursor.fetchall()]

def get_logs_since(since_timestamp: int, component: str = None) -> List[Dict]:
    """Получение логов с определенного времени"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if component:
            cursor.execute(
                "SELECT * FROM logs WHERE ts >= ? AND component=? ORDER BY ts DESC",
                (since_timestamp, component)
            )
        else:
            cursor.execute(
                "SELECT * FROM logs WHERE ts >= ? ORDER BY ts DESC",
                (since_timestamp,)
            )
        
        return [dict(row) for row in cursor.fetchall()]

def add_protocol(name: str, situation: str, steps: List[str]):
    """Добавление протокола в БД"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        steps_json = json.dumps(steps)
        cursor.execute(
            "INSERT OR REPLACE INTO protocols (name, situation, steps, updated_at) VALUES (?,?,?,?)",
            (name, situation, steps_json, int(time.time()))
        )
        conn.commit()

def get_protocol(situation: str) -> Optional[List[str]]:
    """Получение шагов протокола по ситуации"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT steps FROM protocols WHERE situation=?",
            (situation,)
        )
        
        row = cursor.fetchone()
        if row:
            return json.loads(row["steps"])
        return None

def add_fallback_resource(resource_type: str, value: str, priority: int = 100, notes: str = ""):
    """Добавление резервного ресурса"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fallback (type, value, priority, notes) VALUES (?,?,?,?)",
            (resource_type, value, priority, notes)
        )
        conn.commit()

def get_fallback_resources(resource_type: str = None) -> List[Dict]:
    """Получение резервных ресурсов"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if resource_type:
            cursor.execute(
                "SELECT * FROM fallback WHERE type=? ORDER BY priority ASC",
                (resource_type,)
            )
        else:
            cursor.execute(
                "SELECT * FROM fallback ORDER BY type, priority ASC"
            )
        
        return [dict(row) for row in cursor.fetchall()]

def cleanup_old_logs(days: int = 7):
    """Очистка старых логов"""
    cutoff_time = int(time.time()) - (days * 86400)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs WHERE ts < ?", (cutoff_time,))
        deleted = cursor.rowcount
        conn.commit()
    
    return deleted

def get_database_stats() -> Dict:
    """Получение статистики БД"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Подсчет записей в таблицах
        cursor.execute("SELECT COUNT(*) FROM logs")
        logs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM protocols")
        protocols_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fallback")
        fallback_count = cursor.fetchone()[0]
        
        # Размер файла БД
        cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        return {
            "logs_count": logs_count,
            "protocols_count": protocols_count,
            "fallback_count": fallback_count,
            "db_size_bytes": db_size
        }

if __name__ == "__main__":
    # Инициализация БД при прямом запуске
    init_database()
    print("✅ Database initialized successfully")
    
    stats = get_database_stats()
    print(f"📊 Database stats: {stats}")
