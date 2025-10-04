#!/usr/bin/env python3
"""
Скрипт для очистки логов старше 7 дней
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

class LogCleaner:
    """Класс для очистки логов"""
    
    def __init__(self, log_dirs: List[str]):
        self.log_dirs = [Path(log_dir) for log_dir in log_dirs]
        self.retention_days = 7
        self.backup_dir = Path("/var/log/xvpn/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def clean_old_logs(self) -> Dict[str, Any]:
        """Очистка старых логов"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "retention_days": self.retention_days,
            "cleaned_files": [],
            "compressed_files": [],
            "deleted_files": [],
            "errors": []
        }
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for log_dir in self.log_dirs:
            if not log_dir.exists():
                continue
                
            # Очистка текстовых логов
            for log_file in log_dir.glob("*.log"):
                try:
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_date < cutoff_date:
                        # Архивируем перед удалением
                        backup_file = self.backup_dir / f"{log_file.name}_{datetime.now().strftime('%Y%m%d')}.gz"
                        
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(backup_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Удаляем оригинал
                        log_file.unlink()
                        
                        results["compressed_files"].append(str(log_file))
                        results["deleted_files"].append(str(log_file))
                        
                except Exception as e:
                    results["errors"].append({
                        "file": str(log_file),
                        "error": str(e)
                    })
                    
            # Очистка JSON логов
            for json_file in log_dir.glob("*.json"):
                try:
                    file_date = datetime.fromtimestamp(json_file.stat().st_mtime)
                    
                    if file_date < cutoff_date:
                        # Архивируем перед удалением
                        backup_file = self.backup_dir / f"{json_file.name}_{datetime.now().strftime('%Y%m%d')}.gz"
                        
                        with open(json_file, 'rb') as f_in:
                            with gzip.open(backup_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Удаляем оригинал
                        json_file.unlink()
                        
                        results["compressed_files"].append(str(json_file))
                        results["deleted_files"].append(str(json_file))
                        
                except Exception as e:
                    results["errors"].append({
                        "file": str(json_file),
                        "error": str(e)
                    })
                    
            # Очистка старых бэкапов (старше 30 дней)
            for backup_file in self.backup_dir.glob("*.gz"):
                try:
                    backup_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if backup_date < datetime.now() - timedelta(days=30):
                        backup_file.unlink()
                        results["deleted_files"].append(f"backup: {str(backup_file)}")
                        
                except Exception as e:
                    results["errors"].append({
                        "file": str(backup_file),
                        "error": str(e)
                    })
                    
        # Очистка пустых директорий
        for log_dir in self.log_dirs:
            try:
                for empty_dir in log_dir.glob("*"):
                    if empty_dir.is_dir() and not any(empty_dir.iterdir()):
                        empty_dir.rmdir()
                        results["cleaned_files"].append(f"directory: {str(empty_dir)}")
            except Exception as e:
                results["errors"].append({
                    "directory": str(log_dir),
                    "error": str(e)
                })
                
        return results
        
    def get_log_stats(self) -> Dict[str, Any]:
        """Получение статистики логов"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "directories": [],
            "total_files": 0,
            "total_size_mb": 0,
            "oldest_file": None,
            "newest_file": None
        }
        
        for log_dir in self.log_dirs:
            if not log_dir.exists():
                continue
                
            dir_stats = {
                "directory": str(log_dir),
                "files": 0,
                "size_mb": 0,
                "oldest_file": None,
                "newest_file": None
            }
            
            for file_path in log_dir.rglob("*"):
                if file_path.is_file():
                    dir_stats["files"] += 1
                    file_size = file_path.stat().st_size
                    dir_stats["size_mb"] += file_size / (1024 * 1024)
                    
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if dir_stats["oldest_file"] is None or file_time < dir_stats["oldest_file"]["time"]:
                        dir_stats["oldest_file"] = {
                            "file": str(file_path),
                            "time": file_time
                        }
                    if dir_stats["newest_file"] is None or file_time > dir_stats["newest_file"]["time"]:
                        dir_stats["newest_file"] = {
                            "file": str(file_path),
                            "time": file_time
                        }
                        
            stats["directories"].append(dir_stats)
            stats["total_files"] += dir_stats["files"]
            stats["total_size_mb"] += dir_stats["size_mb"]
            
            if dir_stats["oldest_file"]:
                if stats["oldest_file"] is None or dir_stats["oldest_file"]["time"] < stats["oldest_file"]["time"]:
                    stats["oldest_file"] = dir_stats["oldest_file"]
            if dir_stats["newest_file"]:
                if stats["newest_file"] is None or dir_stats["newest_file"]["time"] > stats["newest_file"]["time"]:
                    stats["newest_file"] = dir_stats["newest_file"]
                    
        return stats

# Создаем глобальный экземпляр
log_cleaner = LogCleaner([
    "/var/log/xvpn/orchestration",
    "/var/log/xvpn/agent",
    "/var/log/xvpn/api",
    "/var/log/xvpn/core"
])