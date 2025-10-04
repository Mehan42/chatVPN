#!/usr/bin/env python3
"""
Скрипт для логирования всех действий оркестратора
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ActionLogger:
    """Класс для логирования действий оркестратора"""
    
    def __init__(self, log_dir: str = "/var/log/xvpn/orchestration"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка логирования
        self.logger = logging.getLogger("xvpn_orchestrator")
        self.logger.setLevel(logging.INFO)
        
        # Файл логов
        log_file = self.log_dir / f"actions_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # JSON лог для структурированных данных
        self.json_log_file = self.log_dir / f"actions_{datetime.now().strftime('%Y%m%d')}.json"
        
    def log_action(self, action_type: str, details: Dict[str, Any]):
        """Логирование действия"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "details": details,
            "status": details.get("status", "unknown"),
            "error": details.get("error", None)
        }
        
        # Логирование в текстовый файл
        self.logger.info(f"[{action_type}] {json.dumps(log_entry, ensure_ascii=False)}")
        
        # Логирование в JSON файл
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Логирование ошибки"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "severity": "error"
        }
        
        self.logger.error(f"[ERROR] {json.dumps(error_entry, ensure_ascii=False)}")
        
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
            
    def log_success(self, action: str, details: Dict[str, Any]):
        """Логирование успешного действия"""
        success_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "status": "success"
        }
        
        self.logger.info(f"[SUCCESS] {json.dumps(success_entry, ensure_ascii=False)}")
        
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(success_entry, ensure_ascii=False) + "\n")

# Создаем глобальный экземпляр
action_logger = ActionLogger()