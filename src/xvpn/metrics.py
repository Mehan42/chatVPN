#!/usr/bin/env python3
# XVPN Metrics Collection Module
# Модуль сбора метрик

import time
import functools
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge

# === API Metrics ===
# Метрики API

# Total API requests counter
API_REQUESTS = Counter(
    'xvpn_api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)

# API request duration histogram
API_REQUEST_DURATION = Histogram(
    'xvpn_api_request_duration_seconds', 
    'API request duration', 
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf'))
)

# API errors counter
API_ERRORS = Counter(
    'xvpn_api_errors_total', 
    'Total API errors', 
    ['error']
)

# === Agent Metrics ===
# Метрики агента

# Current agent health score gauge
AGENT_HEALTH_SCORE = Gauge(
    'xvpn_agent_health_score', 
    'Current agent health score'
)

# Total transport switches counter
AGENT_TRANSPORT_SWITCHES = Counter(
    'xvpn_agent_transport_switches_total', 
    'Total transport switches'
)

# Agent errors counter
AGENT_ERRORS = Counter(
    'xvpn_agent_errors_total', 
    'Total agent errors', 
    ['error']
)

# === Bot Metrics ===
# Метрики бота

# Total bot messages counter
BOT_MESSAGES = Counter(
    'xvpn_bot_messages_total', 
    'Total bot messages', 
    ['type']
)

# Bot errors counter
BOT_ERRORS = Counter(
    'xvpn_bot_errors_total', 
    'Total bot errors', 
    ['error']
)

# === Worker Metrics ===
# Метрики воркера

# Total worker tasks counter
WORKER_TASKS = Counter(
    'xvpn_worker_tasks_total', 
    'Total worker tasks', 
    ['type']
)

# Worker errors counter
WORKER_ERRORS = Counter(
    'xvpn_worker_errors_total', 
    'Total worker errors', 
    ['error']
)

# === Connection Metrics ===
# Метрики подключений

# Active connections gauge
ACTIVE_CONNECTIONS = Gauge(
    'xvpn_active_connections', 
    'Current active connections'
)

# Total connections counter
TOTAL_CONNECTIONS = Counter(
    'xvpn_total_connections', 
    'Total connections'
)

# === Metrics Collection Decorator ===
# Декоратор для сбора метрик

def metrics_collector(func):
    """Decorator to collect metrics for functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            # Record successful execution
            API_REQUEST_DURATION.labels(
                method=func.__name__, 
                endpoint='/'
            ).observe(time.time() - start_time)
            return result
        except Exception as e:
            # Record error
            API_ERRORS.labels(error=str(e)).inc()
            raise
    return wrapper

# === Metrics Recording Functions ===
# Функции записи метрик

def record_health_score(score: int):
    """Record current health score"""
    AGENT_HEALTH_SCORE.set(score)

def record_transport_switch():
    """Record transport switch"""
    AGENT_TRANSPORT_SWITCHES.inc()

def record_api_request(method: str, endpoint: str, status: str):
    """Record API request"""
    API_REQUESTS.labels(
        method=method, 
        endpoint=endpoint, 
        status=status
    ).inc()

def record_api_error(error: str):
    """Record API error"""
    API_ERRORS.labels(error=str(error)).inc()

def record_agent_error(error: str):
    """Record agent error"""
    AGENT_ERRORS.labels(error=str(error)).inc()

def record_bot_error(error: str):
    """Record bot error"""
    BOT_ERRORS.labels(error=str(error)).inc()

def record_worker_error(error: str):
    """Record worker error"""
    WORKER_ERRORS.labels(error=str(error)).inc()

def record_active_connections(count: int):
    """Record active connections"""
    ACTIVE_CONNECTIONS.set(count)

def record_total_connections():
    """Record total connections"""
    TOTAL_CONNECTIONS.inc()

def record_bot_message(message_type: str):
    """Record bot message"""
    BOT_MESSAGES.labels(type=message_type).inc()

def record_worker_task(task_type: str):
    """Record worker task"""
    WORKER_TASKS.labels(type=task_type).inc()

# === Metrics Export Functions ===
# Функции экспорта метрик

def export_metrics() -> Dict[str, Any]:
    """Export all metrics as dictionary"""
    # Note: Prometheus client doesn't expose internal values directly
    # This is a simplified version that returns placeholder values
    # In a real implementation, you would use the Prometheus exposition format
    
    return {
        'api_requests': {
            'total': 0,  # Placeholder
            'errors': 0,  # Placeholder
            'duration': 0.0  # Placeholder
        },
        'agent_metrics': {
            'health_score': 0,  # Placeholder
            'transport_switches': 0,  # Placeholder
            'errors': 0  # Placeholder
        },
        'bot_metrics': {
            'messages': 0,  # Placeholder
            'errors': 0  # Placeholder
        },
        'worker_metrics': {
            'tasks': 0,  # Placeholder
            'errors': 0  # Placeholder
        },
        'connection_metrics': {
            'active_connections': 0,  # Placeholder
            'total_connections': 0  # Placeholder
        }
    }

def reset_metrics():
    """Reset all metrics counters"""
    # Note: In production, you might not want to reset gauges
    API_REQUESTS._value.set(0)
    API_ERRORS._value.set(0)
    AGENT_ERRORS._value.set(0)
    BOT_ERRORS._value.set(0)
    WORKER_ERRORS._value.set(0)
    TOTAL_CONNECTIONS._value.set(0)
    BOT_MESSAGES._value.set(0)
    WORKER_TASKS._value.set(0)
    AGENT_TRANSPORT_SWITCHES._value.set(0)

# === Context Manager for Metrics ===
# Контекстный менеджер для метрик

class MetricsContext:
    """Context manager for collecting metrics"""
    
    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Record error
            API_ERRORS.labels(error=str(exc_val)).inc()
        else:
            # Record successful execution
            duration = time.time() - self.start_time
            API_REQUEST_DURATION.labels(
                method=self.method, 
                endpoint=self.endpoint
            ).observe(duration)

# === Utility Functions ===
# Вспомогательные функции

def get_metrics_summary() -> str:
    """Get human-readable metrics summary"""
    # В реальной реализации здесь будет код для получения актуальных метрик
    # Сейчас возвращаем заглушку для тестирования
    
    summary = [
        "=== XVPN Metrics Summary ===",
        "API Requests: 0",
        "API Errors: 0",
        "Average Request Duration: 0.000s",
        "Agent Health Score: 0",
        "Transport Switches: 0",
        "Agent Errors: 0",
        "Bot Messages: 0",
        "Bot Errors: 0",
        "Worker Tasks: 0",
        "Worker Errors: 0",
        "Active Connections: 0",
        "Total Connections: 0",
        "============================"
    ]
    
    return "\n".join(summary)

if __name__ == "__main__":
    # Test metrics collection
    print("Testing XVPN metrics collection...")
    
    # Record some metrics
    record_health_score(5)
    record_api_request("GET", "/mcp/v1/vpn.health", "200")
    record_api_request("POST", "/transports/manifest.json", "200")
    record_agent_error("Transport not available")
    record_bot_message("info")
    record_worker_task("health_check")
    record_active_connections(10)
    record_total_connections()
    record_transport_switch()
    
    # Print metrics summary
    print(get_metrics_summary())
    
    print("Metrics collection test completed!")