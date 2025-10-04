
# Инструкции для AI-оркестратора агента XVPN

## Введение
Документ содержит детальные инструкции для AI-оркестратора агента XVPN по действиям при различных сбоях и нештатных ситуациях. Инструкции основаны на анализе возможных проблем и лучших практиках восстановления системы.

## Принципы работы оркестратора

### 1. Приоритизация действий
1. **Критические ошибки** (мгновенное восстановление)
   - Потеря VPN соединения
   - Сбой API сервера
   - Недоступность базы данных

2. **Предупреждающие сигналы** (плановое восстановление)
   - Ухудшение качества маскировки
   - Повышение задержки
   - Нестабильное соединение

3. **Административные действия** (требуют вмешательства)
   - Физические проблемы сервера
   - Атака системы
   - Обновление компонентов

### 2. Эскалация проблем
- Автоматическое восстановление → Повторная попытка → Ручное вмешательство
- Логирование всех действий для анализа
- Уведомления через Telegram бот

## Детальные инструкции по сбоям

### 1. Протокол: Потеря VPN соединения

**Триггер**: `TRANSPORT_LOST`

**Симптомы**:
- Health check показывает `status: "ERROR"`
- Отсутствие пакетов более 120 секунд
- Низкий score маскировки (< 3)

**Действия оркестратора**:
```python
def handle_vpn_connection_loss():
    """
    1. Проверить текущее состояние транспорты
    2. Выполнить диагностику
    3. Попробовать переключиться на альтернативный транспорт
    4. При неудаче - использовать fallback ресурсы
    5. Логировать все этапы
    """
```

**Шаги**:
1. **Диагностика** (30 секунд):
   ```bash
   # Проверить доступность API
   curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health
   
   # Проверить манифест
   curl -sk https://127.0.0.1:8443/transports/manifest.json
   
   # Проверить системные ресурсы
   free -h && df -h && top -bn1 | head -20
   ```

2. **Переключение транспорта**:
   - Отключить текущий транспорт
   - Выбрать следующий по приоритету
   - Подключиться к новому транспорту

3. **Fallback действия**:
   - Использовать статический манифест
   - Переключиться на резервные IP адреса
   - Активировать альтернативные DoH серверы

4. **Уведомление**:
   - Telegram бот: `VPN соединение потеряно, переключаюсь на резервный транспорт`
   - Логируем в БД с уровнем CRITICAL

### 2. Протокол: API сервер недоступен

**Триггер**: `API_UNREACHABLE > 5min`

**Симптомы**:
- HTTP статус 5xx от API
- Таймауты при запросах
- Невозможность получить манифест

**Действия оркестратора**:
```python
def handle_api_unreachable():
    """
    1. Проверить доступность альтернативных API
    2. Использовать статический манифест
    3. Переключиться на автономный режим
    4. Мониторить восстановление API
    """
```

**Шаги**:
1. **Проверка альтернативных API**:
   ```bash
   # Проверить все возможные API endpoints
   curl -sk https://api-backup:8443/mcp/v1/vpn.health
   curl -sk https://api-secondary:8443/mcp/v1/vpn.health
   ```

2. **Использование статического манифеста**:
   ```bash
   # Загрузить статический манифест из fallback
   curl -sk https://cdn.example.com/manifest.json > /tmp/static_manifest.json
   
   # Проверить валидность
   jq . /tmp/static_manifest.json
   ```

3. **Автономный режим**:
   - Активировать последние известные настройки
   - Мониторить локальное состояние
   - Периодически проверять восстановление API

4. **Восстановление**:
   - При восстановлении API - синхронизировать состояние
   - Обновить манифест и настройки
   - Вернуться в обычный режим

### 3. Протокол: Все транспорты недоступны

**Триггер**: `ALL_TRANSPORTS_DOWN`

**Симптомы**:
- Все транспорты имеют fail_count > 3
- Невозможность подключиться ни к одному транспорту
- Health check показывает критические ошибки

**Действия оркестратора**:
```python
def handle_all_transports_down():
    """
    1. Собрать диагностическую информацию
    2. Активировать режим пониженной функциональности
    3. Уведомить администратора
    4. Запустить скрипты восстановления
    """
```

**Шаги**:
1. **Сбор диагностики**:
   ```bash
   # Системная диагностика
   uname -a && uptime && date
   
   # Сеть
   ip a && ip r && netstat -tlnp
   
   # Процессы
   ps aux | grep -E "(xray|vpn|agent)" | grep -v grep
   
   # Логи последних 10 минут
   journalctl -u xvpn-* --since "10 minutes ago" -n 50
   ```

2. **Диагностические скрипты**:
   - Запустить `diagnose_network.py`
   - Запустить `check_firewall.py`
   - Запустить `validate_configs.py`

3. **Режим пониженной функциональности**:
   - Сохранить текущее состояние
   - Отключить ненужные сервисы
   - Оставить только мониторинг

4. **Уведомление администратора**:
   ```bash
   # Отправить критическое уведомление
   curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/sendMessage \
     -d "chat_id=${CHAT_ID}" \
     -d "text=🚨 КРИТИЧЕСКАЯ ОШИБКА: Все VPN транспорты недоступны!"
   ```

### 4. Протокол: Ухудшение качества маскировки

**Триггер**: `MASK_SCORE_DEGRADATION`

**Симптомы**:
- Mask score падает ниже 3
- Увеличение задержки
- Повышение packet loss

**Действия оркестратора**:
```python
def handle_mask_score_degradation():
    """
    1. Мониторить тенденцию изменения score
    2. При ухудшении - переключиться на альтернативный транспорт
    3. Активировать дополнительные меры защиты
    4. Логировать изменения качества
    """
```

**Шаги**:
1. **Анализ тенденции**:
   ```python
   # Проверить последние 5 измерений
   SELECT mask_score, timestamp FROM health_logs 
   ORDER BY timestamp DESC LIMIT 5
   ```

2. **Переключение транспорта**:
   - Выбрать транспорт с лучшим score
   - Переключиться на более стабильный протокол
   - Изменить параметры шифрования

3. **Дополнительные меры**:
   - Активировать obfuscation
   - Изменить User-Agent
   - Переключиться на другой порт

4. **Мониторинг**:
   - Отслеживать изменения score каждые 30 секунд
   - При улучшении - вернуть исходные настройки

### 5. Протокол: Система мониторинга недоступна

**Триггер**: `MONITORING_UNAVAILABLE`

**Симптомы**:
- Невозможность получить health status
- Нет логов от health monitor
- Ошибки в проверках состояния

**Действия оркестратора**:
```python
def handle_monitoring_unavailable():
    """
    1. Проверить доступность health endpoints
    2. Запустить локальный мониторинг
    3. Восстановить систему мониторинга
    4. Синхронизировать данные
    """
```

**Шаги**:
1. **Проверка endpoints**:
   ```bash
   # Проверить все health endpoints
   curl -sk https://127.0.0.1:8443/mcp/v1/vpn.health
   
   # Проверить системный статус
   curl -sk https://127.0.0.1:8443/system/status
   ```

2. **Локальный мониторинг**:
   ```python
   # Запустить локальный health check
   python3 local_health_monitor.py
   
   # Включить расширенное логирование
   export LOG_LEVEL=DEBUG
   ```

3. **Восстановление**:
   - Перезапустить сервисы мониторинга
   - Проверить конфигурацию
   - Тестировать функциональность

4. **Синхронизация**:
   - Обновить статусы в базе данных
   - Синхронизировать с основным API
   - Восстановить регулярные проверки

## Скрипты логирования и тестов

### 1. Скрипт логирования всех действий

**Файл**: `server/agent/scripts/action_logger.py`

```python
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
```

### 2. Скрипт запуска тестов

**Файл**: `server/agent/scripts/test_runner.py`

```python
#!/usr/bin/env python3
"""
Скрипт для запуска тестов при сбоях
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TestRunner:
    """Класс для запуска тестов при сбоях"""
    
    def __init__(self, test_dir: str = "/opt/xvpn/tests"):
        self.test_dir = Path(test_dir)
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def run_network_tests(self) -> Dict[str, Any]:
        """Запуск сетевых тестов"""
        tests = [
            {"name": "connectivity", "command": ["ping", "-c", "4", "8.8.8.8"]},
            {"name": "dns_resolution", "command": ["nslookup", "google.com"]},
            {"name": "port_scan", "command": ["nc", "-zv", "127.0.0.1", "443"]},
            {"name": "api_health", "command": ["curl", "-sk", "https://127.0.0.1:8443/mcp/v1/vpn.health"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except subprocess.TimeoutExpired:
                test_result = {
                    "test_name": test["name"],
                    "status": "timeout",
                    "duration": 30,
                    "output": "",
                    "error": "Test timed out after 30 seconds",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "network",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "timeout_tests": len([r for r in results if r["status"] == "timeout"]),
            "error_tests": len([r for r in results if r["status"] == "error"]),
            "results": results
        }
        
    def run_vpn_tests(self) -> Dict[str, Any]:
        """Запуск VPN тестов"""
        tests = [
            {"name": "vpn_connectivity", "command": ["curl", "-sk", "https://127.0.0.1:8443/transports/manifest.json"]},
            {"name": "vpn_health", "command": ["curl", "-sk", "https://127.0.0.1:8443/mcp/v1/vpn.health"]},
            {"name": "vpn_status", "command": ["systemctl", "status", "xvpn-core"]},
            {"name": "vpn_logs", "command": ["journalctl", "-u", "xvpn-core", "--since", "5 minutes ago", "-n", "20"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "vpn",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    def run_system_tests(self) -> Dict[str, Any]:
        """Запуск системных тестов"""
        tests = [
            {"name": "disk_usage", "command": ["df", "-h"]},
            {"name": "memory_usage", "command": ["free", "-h"]},
            {"name": "cpu_usage", "command": ["top", "-bn1", "|", "head", "-20"]},
            {"name": "processes", "command": ["ps", "aux", "|", "grep", "-E", "(xray|vpn|agent)", "|", "grep", "-v", "grep"]}
        ]
        
        results = []
        
        for test in tests:
            start_time = time.time()
            try:
                result = subprocess.run(
                    test["command"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                test_result = {
                    "test_name": test["name"],
                    "status": "success",
                    "duration": duration,
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                test_result = {
                    "test_name": test["name"],
                    "status": "error",
                    "duration": 0,
                    "output": "",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
            results.append(test_result)
            
        return {
            "test_type": "system",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "successful_tests": len([r for r in results if r["status"] == "success"]),
            "failed_tests": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов"""
        start_time = time.time()
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "total_start_time": start_time,
            "tests": {}
        }
        
        # Запуск сетевых тестов
        all_results["tests"]["network"] = self.run_network_tests()
        
        # Запуск VPN тестов
        all_results["tests"]["vpn"] = self.run_vpn_tests()
        
        # Запуск системных тестов
        all_results["tests"]["system"] = self.run_system_tests()
        
        # Общая статистика
        total_tests = sum([
            len(all_results["tests"][category]["results"]) 
            for category in all_results["tests"]
        ])
        
        successful_tests = sum([
            len([r for r in all_results["tests"][category]["results"] if r["status"] == "success"]) 
            for category in all_results["tests"]
        ])
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_duration": time.time() - start_time
        }
        
        # Сохранение результатов
        result_file = self.results_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        return all_results

# Создаем глобальный экземпляр
test_runner = TestRunner()
```

### 3. Скрипт очистки логов старше 7 дней

**Файл**: `server/agent/scripts/log_cleaner.py`

```python
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
               