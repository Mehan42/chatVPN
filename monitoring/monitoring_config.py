# XVPN Monitoring and Logging Configuration
# Конфигурация мониторинга и логирования

# === Prometheus Configuration ===
# monitoring/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  # XVPN API metrics
  - job_name: 'xvpn-api'
    static_configs:
      - targets: ['xvpn-api:8443']
    scrape_interval: 5s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  # XVPN Agent metrics
  - job_name: 'xvpn-agent'
    static_configs:
      - targets: ['xvpn-agent:8443']
    scrape_interval: 10s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  # XVPN Bot metrics
  - job_name: 'xvpn-bot'
    static_configs:
      - targets: ['xvpn-bot:8443']
    scrape_interval: 30s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  # XVPN Worker metrics
  - job_name: 'xvpn-worker'
    static_configs:
      - targets: ['xvpn-worker:8443']
    scrape_interval: 15s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  # XVPN Orchestrator metrics
  - job_name: 'xvpn-orchestrator'
    static_configs:
      - targets: ['xvpn-orchestrator:8080']
    scrape_interval: 20s
    metrics_path: /metrics
    scheme: http

  # Node exporter metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
    metrics_path: /metrics

  # Docker container metrics
  - job_name: 'docker-containers'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
    metrics_path: /metrics

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 15s
    metrics_path: /metrics
    scheme: http

  # PostgreSQL metrics
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s
    metrics_path: /metrics
    scheme: http

# === Alert Rules ===
# monitoring/prometheus/rules/alerts.yml

groups:
  # XVPN API alerts
  - name: xvpn-api-alerts
    rules:
      # High error rate
      - alert: XVPNAPIHighErrorRate
        expr: rate(xvpn_api_requests_total{status=~"5.."}[5m]) / rate(xvpn_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "XVPN API high error rate"
          description: "XVPN API error rate is above 5% (current value: {{ $value }}%)"

      # High latency
      - alert: XVPNAPIHighLatency
        expr: histogram_quantile(0.95, rate(xvpn_api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "XVPN API high latency"
          description: "XVPN API 95th percentile latency is above 1 second (current value: {{ $value }}s)"

      # Low availability
      - alert: XVPNAPIUnavailable
        expr: up{xvpn-api} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "XVPN API unavailable"
          description: "XVPN API is unreachable"

  # XVPN Agent alerts
  - name: xvpn-agent-alerts
    rules:
      # Low health score
      - alert: XVPNAGLowHealthScore
        expr: xvpn_agent_health_score < 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "XVPN Agent low health score"
          description: "XVPN Agent health score is below 3 (current value: {{ $value }})"

      # Transport switching
      - alert: XVPNAGTransportSwitching
        expr: increase(xvpn_agent_transport_switches_total[5m]) > 0
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "XVPN Agent transport switching"
          description: "XVPN Agent is switching transports (current value: {{ $value }})"

      # Agent offline
      - alert: XVPNAGOffline
        expr: up{xvpn-agent} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "XVPN Agent offline"
          description: "XVPN Agent is unreachable"

  # XVPN Bot alerts
  - name: xvpn-bot-alerts
    rules:
      # Bot errors
      - alert: XVPNBotErrors
        expr: increase(xvpn_bot_errors_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "XVPN Bot errors"
          description: "XVPN Bot has encountered errors (current value: {{ $value }})"

      # Bot inactive
      - alert: XVPNBotInactive
        expr: up{xvpn-bot} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "XVPN Bot inactive"
          description: "XVPN Bot is not responding"

  # System alerts
  - name: system-alerts
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80% (current value: {{ $value }}%)"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 85% (current value: {{ $value }}%)"

      # Low disk space
      - alert: LowDiskSpace
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk usage is above 90% (current value: {{ $value }}%)"

      # High network errors
      - alert: HighNetworkErrors
        expr: rate(node_network_receive_errs_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High network errors"
          description: "Network receive errors are above 10/s (current value: {{ $value }})"

# === Grafana Configuration ===
# monitoring/grafana/provisioning/datasources/prometheus.yml

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
    editable: true

# === Grafana Dashboards ===
# monitoring/grafana/provisioning/dashboards/xvpn-overview.json

{
  "dashboard": {
    "id": null,
    "title": "XVPN Overview",
    "tags": ["xvpn", "vpn", "overview"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "type": "graph",
        "title": "API Requests",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(xvpn_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "reqps", "label": "Requests per second"},
          {"format": "short"}
        ]
      },
      {
        "id": 2,
        "type": "singlestat",
        "title": "Current Health Score",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "xvpn_agent_health_score",
            "refId": "A"
          }
        ],
        "format": "none",
        "valueName": "current",
        "prefix": "Score: ",
        "colorBackground": true,
        "colors": ["#d44a3a", "rgba(237, 129, 40, 0.89)", "#299c46"]
      },
      {
        "id": 3,
        "type": "singlestat",
        "title": "Active Connections",
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
        "targets": [
          {
            "expr": "xvpn_active_connections",
            "refId": "A"
          }
        ],
        "format": "none",
        "valueName": "current",
        "prefix": "Connections: ",
        "colorBackground": false,
        "colors": ["#299c46", "rgba(237, 129, 40, 0.89)", "#d44a3a"]
      },
      {
        "id": 4,
        "type": "graph",
        "title": "Agent Health Score Over Time",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "xvpn_agent_health_score",
            "legendFormat": "Health Score",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "none", "label": "Score", "min": 0, "max": 5},
          {"format": "short"}
        ]
      },
      {
        "id": 5,
        "type": "graph",
        "title": "Transport Switches",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "increase(xvpn_agent_transport_switches_total[5m])",
            "legendFormat": "Switches",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "none", "label": "Switches"},
          {"format": "short"}
        ]
      },
      {
        "id": 6,
        "type": "table",
        "title": "Recent Errors",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "xvpn_errors_total",
            "legendFormat": "{{component}}: {{error}}",
            "refId": "A"
          }
        ],
        "columns": [
          {"text": "Time", "value": "time"},
          {"text": "Component", "value": "component"},
          {"text": "Error", "value": "error"},
          {"text": "Count", "value": "count"}
        ]
      }
    ]
  }
}

# === Loki Configuration ===
# monitoring/loki/loki.yml

auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://alertmanager:9093

# === Promtail Configuration ===
# monitoring/promtail/promtail.yml

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # XVPN API logs
  - job_name: xvpn-api
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn-api
          __path__: /var/log/xvpn/api.log

  # XVPN Agent logs
  - job_name: xvpn-agent
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn-agent
          __path__: /var/log/xvpn/agent.log

  # XVPN Bot logs
  - job_name: xvpn-bot
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn-bot
          __path__: /var/log/xvpn/bot.log

  # XVPN Worker logs
  - job_name: xvpn-worker
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn-worker
          __path__: /var/log/xvpn/worker.log

  # XVPN Orchestrator logs
  - job_name: xvpn-orchestrator
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn-orchestrator
          __path__: /var/log/xvpn/orchestrator.log

  # System logs
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: system
          __path__: /var/log/syslog

# === Alertmanager Configuration ===
# monitoring/alertmanager/alertmanager.yml

global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@xvpn.local'
  smtp_auth_username: 'alerts@xvpn.local'
  smtp_auth_password: 'your-smtp-password'
  smtp_require_tls: true

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'telegram-notifications'

receivers:
  - name: 'telegram-notifications'
    webhook_configs:
      - url: 'http://bot:8443/webhook/alerts'
        send_resolved: true

  - name: 'email-notifications'
    email_configs:
      - to: 'admin@xvpn.local'
        send_resolved: true

  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        send_resolved: true

# === Logging Configuration ===
# config/logging.conf

[loggers]
keys=root,xvpn,api,agent,bot,worker,orchestrator

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,jsonFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_xvpn]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn

[logger_api]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn.api

[logger_agent]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn.agent

[logger_bot]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn.bot

[logger_worker]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn.worker

[logger_orchestrator]
level=INFO
handlers=fileHandler,rotatingFileHandler
propagate=0
qualname=xvpn.orchestrator

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=jsonFormatter
args=('/var/log/xvpn/application.log',)

[handler_rotatingFileHandler]
class=logging.handlers.RotatingFileHandler
level=INFO
formatter=jsonFormatter
args=('/var/log/xvpn/application.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_jsonFormatter]
class=xvpn.logging.JSONFormatter
format={"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}
datefmt=%Y-%m-%d %H:%M:%S

# === Structured Logging ===
# src/xvpn/logging.py

import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'getMessage', 'exc_info', 
                              'exc_text', 'stack_info']:
                    log_entry[key] = value
                    
        return json.dumps(log_entry, ensure_ascii=False)

# === Metrics Collection ===
# src/xvpn/metrics.py

import time
import functools
from prometheus_client import Counter, Histogram, Gauge

# API metrics
API_REQUESTS = Counter('xvpn_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
API_REQUEST_DURATION = Histogram('xvpn_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
API_ERRORS = Counter('xvpn_api_errors_total', 'Total API errors', ['error'])

# Agent metrics
AGENT_HEALTH_SCORE = Gauge('xvpn_agent_health_score', 'Current agent health score')
AGENT_TRANSPORT_SWITCHES = Counter('xvpn_agent_transport_switches_total', 'Total transport switches')
AGENT_ERRORS = Counter('xvpn_agent_errors_total', 'Total agent errors', ['error'])

# Bot metrics
BOT_MESSAGES = Counter('xvpn_bot_messages_total', 'Total bot messages', ['type'])
BOT_ERRORS = Counter('xvpn_bot_errors_total', 'Total bot errors', ['error'])

# Worker metrics
WORKER_TASKS = Counter('xvpn_worker_tasks_total', 'Total worker tasks', ['type'])
WORKER_ERRORS = Counter('xvpn_worker_errors_total', 'Total worker errors', ['error'])

# Connection metrics
ACTIVE_CONNECTIONS = Gauge('xvpn_active_connections', 'Current active connections')
TOTAL_CONNECTIONS = Counter('xvpn_total_connections', 'Total connections')

# === Metrics Decorator ===
def metrics_collector(func):
    """Decorator to collect metrics for functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            # Record successful execution
            API_REQUEST_DURATION.labels(method=func.__name__, endpoint='/').observe(time.time() - start_time)
            return result
        except Exception as e:
            # Record error
            API_ERRORS.labels(error=str(e)).inc()
            raise
    return wrapper

# === Health Check Metrics ===
def record_health_score(score):
    """Record current health score"""
    AGENT_HEALTH_SCORE.set(score)

def record_transport_switch():
    """Record transport switch"""
    AGENT_TRANSPORT_SWITCHES.inc()

def record_api_request(method, endpoint, status):
    """Record API request"""
    API_REQUESTS.labels(method=method, endpoint=endpoint, status=status).inc()

def record_api_error(error):
    """Record API error"""
    API_ERRORS.labels(error=str(error)).inc()

def record_agent_error(error):
    """Record agent error"""
    AGENT_ERRORS.labels(error=str(error)).inc()

def record_bot_error(error):
    """Record bot error"""
    BOT_ERRORS.labels(error=str(error)).inc()

def record_worker_error(error):
    """Record worker error"""
    WORKER_ERRORS.labels(error=str(error)).inc()

def record_active_connections(count):
    """Record active connections"""
    ACTIVE_CONNECTIONS.set(count)

def record_total_connections():
    """Record total connections"""
    TOTAL_CONNECTIONS.inc()

# === Логирование в разных компонентах ===
# server/api/app.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для API
api_logger = logging.getLogger('xvpn.api')
api_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/var/log/xvpn/api.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/var/log/xvpn/api.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
api_logger.addHandler(console_handler)
api_logger.addHandler(file_handler)
api_logger.addHandler(rotating_handler)

# === Логирование в агенте ===
# server/agent/agent.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для агента
agent_logger = logging.getLogger('xvpn.agent')
agent_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/var/log/xvpn/agent.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/var/log/xvpn/agent.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
agent_logger.addHandler(console_handler)
agent_logger.addHandler(file_handler)
agent_logger.addHandler(rotating_handler)

# === Логирование в боте ===
# server/admin/tg_bot.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для бота
bot_logger = logging.getLogger('xvpn.bot')
bot_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/var/log/xvpn/bot.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/var/log/xvpn/bot.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
bot_logger.addHandler(console_handler)
bot_logger.addHandler(file_handler)
bot_logger.addHandler(rotating_handler)

# === Логирование в воркере ===
# server/worker/worker.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для воркера
worker_logger = logging.getLogger('xvpn.worker')
worker_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/var/log/xvpn/worker.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/var/log/xvpn/worker.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
worker_logger.addHandler(console_handler)
worker_logger.addHandler(file_handler)
worker_logger.addHandler(rotating_handler)

# === Логирование в оркестраторе ===
# server/agent/orchestrator.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для оркестратора
orchestrator_logger = logging.getLogger('xvpn.orchestrator')
orchestrator_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/var/log/xvpn/orchestrator.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/var/log/xvpn/orchestrator.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
orchestrator_logger.addHandler(console_handler)
orchestrator_logger.addHandler(file_handler)
orchestrator_logger.addHandler(rotating_handler)

# === Логирование в клиенте ===
# client/chatvpn_backend.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для клиента
client_logger = logging.getLogger('xvpn.client')
client_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/client.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/client.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
client_logger.addHandler(console_handler)
client_logger.addHandler(file_handler)
client_logger.addHandler(rotating_handler)

# === Логирование в GUI ===
# client/chatvpn_gui.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для GUI
gui_logger = logging.getLogger('xvpn.gui')
gui_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/gui.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/gui.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
gui_logger.addHandler(console_handler)
gui_logger.addHandler(file_handler)
gui_logger.addHandler(rotating_handler)

# === Логирование в состоянии ===
# client/state_machine.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для машины состояний
state_logger = logging.getLogger('xvpn.state')
state_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/state.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/state.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
state_logger.addHandler(console_handler)
state_logger.addHandler(file_handler)
state_logger.addHandler(rotating_handler)

# === Логирование в здоровье ===
# client/health.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для здоровья
health_logger = logging.getLogger('xvpn.health')
health_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/health.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/health.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
health_logger.addHandler(console_handler)
health_logger.addHandler(file_handler)
health_logger.addHandler(rotating_handler)

# === Логирование в открытии IPv6 ===
# client/ipv6_manager.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для IPv6 менеджера
ipv6_logger = logging.getLogger('xvpn.ipv6')
ipv6_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/ipv6.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/ipv6.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
ipv6_logger.addHandler(console_handler)
ipv6_logger.addHandler(file_handler)
ipv6_logger.addHandler(rotating_handler)

# === Логирование в помощи прокси ===
# client/proxy_helper.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для помощника прокси
proxy_logger = logging.getLogger('xvpn.proxy')
proxy_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/proxy.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/proxy.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
proxy_logger.addHandler(console_handler)
proxy_logger.addHandler(file_handler)
proxy_logger.addHandler(rotating_handler)

# === Логирование в режимах прокси ===
# client/proxy_modes.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для режимов прокси
modes_logger = logging.getLogger('xvpn.proxy_modes')
modes_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/modes.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/modes.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
modes_logger.addHandler(console_handler)
modes_logger.addHandler(file_handler)
modes_logger.addHandler(rotating_handler)

# === Логирование в открытии ===
# client/discover.py

import logging
from xvpn.logging import JSONFormatter

# Настройка логирования для открытия
discover_logger = logging.getLogger('xvpn.discover')
discover_logger.setLevel(logging.INFO)

# Создание обработчиков
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/home/uss/chatvpn/client/logs/discover.log')
rotating_handler = logging.handlers.RotatingFileHandler(
    '/home/uss/chatvpn/client/logs/discover.log', maxBytes=10485760, backupCount=5
)

# Установка форматировщиков
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)
file_handler.setFormatter(json_formatter)
rotating_handler.setFormatter(json_formatter)

# Добавление обработчиков
discover_logger.addHandler(console_handler)
discover_logger.addHandler(file_handler)
discover_logger.addHandler(rotating_handler)