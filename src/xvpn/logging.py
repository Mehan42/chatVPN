#!/usr/bin/env python3
# XVPN Structured Logging Module
# Модуль структурированного логирования

import json
import logging
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
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

# Predefined formatters
SIMPLE_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

JSON_FORMATTER = JSONFormatter(
    '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Predefined handlers
def get_console_handler(formatter=SIMPLE_FORMATTER):
    """Get console handler with specified formatter"""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler

def get_file_handler(log_file: str, formatter=JSON_FORMATTER, max_bytes: int = 10485760, backup_count: int = 5):
    """Get rotating file handler with specified formatter"""
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    return file_handler

# Logger factory
def get_logger(name: str, level: int = logging.INFO, log_file: str = None, json_format: bool = False) -> logging.Logger:
    """Get logger with specified name and configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add console handler
    formatter = JSON_FORMATTER if json_format else SIMPLE_FORMATTER
    logger.addHandler(get_console_handler(formatter))
    
    # Add file handler if specified
    if log_file:
        logger.addHandler(get_file_handler(log_file, formatter))
    
    return logger

# Convenience functions
def log_info(logger: logging.Logger, message: str, **kwargs):
    """Log info message with extra data"""
    if kwargs:
        logger.info(f"{message} {json.dumps(kwargs, ensure_ascii=False)}")
    else:
        logger.info(message)

def log_warning(logger: logging.Logger, message: str, **kwargs):
    """Log warning message with extra data"""
    if kwargs:
        logger.warning(f"{message} {json.dumps(kwargs, ensure_ascii=False)}")
    else:
        logger.warning(message)

def log_error(logger: logging.Logger, message: str, **kwargs):
    """Log error message with extra data"""
    if kwargs:
        logger.error(f"{message} {json.dumps(kwargs, ensure_ascii=False)}")
    else:
        logger.error(message)

def log_debug(logger: logging.Logger, message: str, **kwargs):
    """Log debug message with extra data"""
    if kwargs:
        logger.debug(f"{message} {json.dumps(kwargs, ensure_ascii=False)}")
    else:
        logger.debug(message)

def log_critical(logger: logging.Logger, message: str, **kwargs):
    """Log critical message with extra data"""
    if kwargs:
        logger.critical(f"{message} {json.dumps(kwargs, ensure_ascii=False)}")
    else:
        logger.critical(message)

# Global logger instances
API_LOGGER = get_logger('xvpn.api')
AGENT_LOGGER = get_logger('xvpn.agent')
BOT_LOGGER = get_logger('xvpn.bot')
WORKER_LOGGER = get_logger('xvpn.worker')
ORCHESTRATOR_LOGGER = get_logger('xvpn.orchestrator')
CLIENT_LOGGER = get_logger('xvpn.client')
GUI_LOGGER = get_logger('xvpn.gui')
STATE_LOGGER = get_logger('xvpn.state')
HEALTH_LOGGER = get_logger('xvpn.health')
IPV6_LOGGER = get_logger('xvpn.ipv6')
PROXY_LOGGER = get_logger('xvpn.proxy')
MODES_LOGGER = get_logger('xvpn.proxy_modes')
DISCOVER_LOGGER = get_logger('xvpn.discover')

if __name__ == "__main__":
    # Test logging
    print("Testing XVPN structured logging...")
    
    # Test different log levels
    API_LOGGER.info("API started successfully")
    AGENT_LOGGER.warning("Agent health score is low", health_score=2)
    BOT_LOGGER.error("Bot failed to send message", error="Connection timeout")
    WORKER_LOGGER.debug("Worker processing task", task_id="12345")
    ORCHESTRATOR_LOGGER.critical("Orchestrator crashed", reason="Memory overflow")
    
    # Test structured logging
    log_info(CLIENT_LOGGER, "Client connected", client_id="test-client-123", ip="192.168.1.100")
    log_warning(GUI_LOGGER, "GUI update failed", widget="status_indicator", error="Network timeout")
    log_error(STATE_LOGGER, "State transition failed", from_state="running", to_state="stopping", error="Service unavailable")
    log_debug(HEALTH_LOGGER, "Health check performed", score=4, checks_passed=3, checks_total=5)
    log_critical(IPV6_LOGGER, "IPv6 connectivity lost", interface="eth0", reason="Router configuration changed")
    
    print("Structured logging test completed!")