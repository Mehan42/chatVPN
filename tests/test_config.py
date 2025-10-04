# XVPN Test Configuration
# Конфигурация автоматического тестирования

# === Pytest Configuration ===
# pytest.ini

[pytest]
# Минимальная версия pytest
minversion = 7.0

# Добавляемые опции по умолчанию
addopts =
    -ra -q --strict-markers --strict-config
    --tb=short
    --color=yes
    --durations=10
    --maxfail=1
    --showlocals
    --no-header
    --disable-warnings

# Пути поиска тестов
testpaths = tests

# Форматы файлов тестов
python_files = test_*.py *_test.py tests/*.py

# Классы тестов
python_classes = Test*

# Функции тестов
python_functions = test_*

# Маркеры тестов
markers =
    unit: Помечает юнит-тесты
    integration: Помечает интеграционные тесты
    functional: Помечает функциональные тесты
    api: Помечает API тесты
    agent: Помечает тесты агентов
    bot: Помечает тесты бота
    worker: Помечает тесты воркеров
    orchestrator: Помечает тесты оркестратора
    security: Помечает тесты безопасности
    performance: Помечает тесты производительности
    stress: Помечает стресс-тесты
    slow: Помечает медленные тесты (для исключения в быстрых запусках)
    fast: Помечает быстрые тесты
    smoke: Помечает smoke тесты
    regression: Помечает регрессионные тесты
    acceptance: Помечает acceptance тесты
    ui: Помечает UI тесты
    cli: Помечает CLI тесты
    database: Помечает тесты базы данных
    network: Помечает сетевые тесты
    ipv6: Помечает IPv6 тесты
    tls: Помечает TLS тесты
    proxy: Помечает proxy тесты
    client: Помечает клиентские тесты
    server: Помечает серверные тесты
    mock: Помечает тесты с моками
    live: Помечает live тесты
    flaky: Помечает нестабильные тесты
    skipci: Пропускает тесты в CI
    onlyci: Запускает только в CI
    local: Запускает только локально
    remote: Запускает только удаленно
    windows: Запускает только в Windows
    linux: Запускает только в Linux
    macos: Запускает только в macOS
    docker: Запускает только в Docker
    kubernetes: Запускает только в Kubernetes

# Исключения
xfail_strict = true

# Параметризованные тесты
parametrize_combine = flat

# Логирование
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s (%(filename)s:%(lineno)d)
log_cli_date_format = %Y-%m-%d %H:%M:%S

log_file = logs/pytest.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s (%(filename)s:%(lineno)d)
log_file_date_format = %Y-%m-%d %H:%M:%S

# Покрытие кода
[coverage:run]
# Источники для покрытия
source = 
    src/
    server/
    client/
    tests/

# Исключения из покрытия
omit = 
    */tests/*
    */test_*
    *_test.py
    */venv/*
    */.venv/*
    */__pycache__/*
    */build/*
    */dist/*
    */.eggs/*
    */.git/*
    */node_modules/*
    */migrations/*

# Настройки отчета
[coverage:report]
# Исключить из отчета
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    pass
    ...

# Порог покрытия
fail_under = 80

# Показывать отсутствующие строки
show_missing = True

# Пропускать пустые файлы
skip_covered = False

# Сортировка
sort = Cover

# === Pytest Asyncio Configuration ===
[tool:pytest]
# Режим асинхронных тестов
asyncio_mode = auto

# Маркеры асинхронных тестов
asyncio_fixture_scope = function

# === Mock Configuration ===
[mock]
# Настройки моков
patch.multiple = True

# === Hypothesis Configuration ===
[hypothesis]
# Настройки генерации тестов
deadline = 2000
derandomize = True
max_examples = 100
phases = explicit, reuse, generate, shrink
print_blob = true
suppress_health_check = too_slow
verbosity = normal

# === Test Coverage Configuration ===
[coverage:html]
# Директория для HTML отчета
directory = htmlcov

# === Test Coverage Configuration ===
[coverage:xml]
# Файл XML отчета
output = coverage.xml

# === Pytest Cov Configuration ===
[coverage:paths]
# Пути для покрытия
source = 
    src/
    server/
    client/

# === Pytest Cov Configuration ===
[coverage:run]
# Параметры запуска
branch = True
data_file = .coverage
parallel = False

# === Pytest Cov Configuration ===
[coverage:report]
# Параметры отчета
precision = 2
show_missing = True
skip_covered = False
sort = Cover

# === Test Fixtures Configuration ===
# conftest.py

import pytest
import asyncio
import tempfile
import shutil
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# === Test Fixtures ===
@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def temp_dir():
    """Создание временной директории для тестов"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_config():
    """Мок для конфигурации"""
    config = Mock()
    config.get.return_value = "test_value"
    config.__getitem__ = lambda self, key: "test_value"
    yield config

@pytest.fixture(scope="function")
def mock_logger():
    """Мок для логгера"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    yield logger

@pytest.fixture(scope="function")
def mock_http_client():
    """Мок для HTTP клиента"""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        yield mock_session_instance

@pytest.fixture(scope="function")
def mock_database():
    """Мок для базы данных"""
    with patch("sqlalchemy.create_engine") as mock_engine:
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        yield mock_engine_instance

# === Test Utilities ===
class TestUtilities:
    """Утилиты для тестирования"""
    
    @staticmethod
    def create_temp_file(content="", suffix="", prefix=""):
        """Создание временного файла"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=suffix, 
            prefix=prefix, 
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def cleanup_temp_file(filepath):
        """Удаление временного файла"""
        if os.path.exists(filepath):
            os.unlink(filepath)
            
    @staticmethod
    def mock_async_return(value):
        """Создание мока для асинхронного возврата значения"""
        async def async_mock():
            return value
        return async_mock()
        
    @staticmethod
    def mock_async_exception(exception):
        """Создание мока для асинхронного исключения"""
        async def async_mock():
            raise exception
        return async_mock()

# === Test Data Factories ===
class TestDataFactories:
    """Фабрики для тестовых данных"""
    
    @staticmethod
    def create_test_client_config(uuid="test-uuid-123", **kwargs):
        """Создание тестовой конфигурации клиента"""
        return {
            "uuid": uuid,
            "name": "Test Client",
            "description": "Test client configuration",
            "created_at": "2025-01-01T00:00:00Z",
            "expires_at": "2026-01-01T00:00:00Z",
            "transports": [
                {
                    "id": "test-transport-1",
                    "name": "Test Transport 1",
                    "type": "vless-reality",
                    "priority": 1,
                    "ipv6": True,
                    "need_udp": False,
                    "config": {
                        "server": "localhost",
                        "port": 443,
                        "protocol": "tcp"
                    }
                }
            ],
            "settings": {
                "auto_connect": True,
                "auto_transport_switch": True,
                "transport_switch_threshold": 3,
                "health_check_interval": 30,
                "proxy_mode": "tun",
                "ipv6_enabled": True,
                "kill_switch": True,
                "dns_leak_protection": True,
                "log_level": "INFO"
            },
            **kwargs
        }
        
    @staticmethod
    def create_test_transport_manifest(**kwargs):
        """Создание тестового манифеста транспортов"""
        return {
            "version": 1,
            "generated_at": "2025-01-01T00:00:00Z",
            "transports": [
                {
                    "id": "vless-reality-1",
                    "name": "VLESS + Reality Transport 1",
                    "type": "vless-reality",
                    "priority": 1,
                    "ipv6": True,
                    "need_udp": False,
                    "config_template": {
                        "server": "example1.server.com",
                        "port": 443,
                        "protocol": "tcp"
                    },
                    "health_check": {
                        "interval": 30,
                        "timeout": 10,
                        "retries": 3
                    }
                }
            ],
            **kwargs
        }
        
    @staticmethod
    def create_test_health_status(**kwargs):
        """Создание тестового статуса здоровья"""
        return {
            "status": "healthy",
            "mask_score": 5,
            "timestamp": 1704067200,  # 2025-01-01T00:00:00Z
            "version": "1.0.0",
            **kwargs
        }

# === Test Assertions ===
class TestAssertions:
    """Пользовательские утверждения для тестов"""
    
    @staticmethod
    def assert_dict_contains(actual, expected):
        """Проверка, что словарь содержит ожидаемые значения"""
        for key, value in expected.items():
            assert key in actual, f"Key '{key}' not found in actual dictionary"
            assert actual[key] == value, f"Expected {key}={value}, got {key}={actual[key]}"
            
    @staticmethod
    def assert_list_contains(actual, expected_items):
        """Проверка, что список содержит ожидаемые элементы"""
        for item in expected_items:
            assert item in actual, f"Item '{item}' not found in actual list"
            
    @staticmethod
    def assert_json_response(response, expected_status=200):
        """Проверка JSON ответа"""
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
        assert response.headers.get('content-type', '').startswith('application/json'), "Response is not JSON"

# === Pytest Plugin Configuration ===
# pytest_plugins.py

def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line("markers", "slow: mark test as slow.")
    config.addinivalue_line("markers", "integration: mark test as integration test.")
    config.addinivalue_line("markers", "unit: mark test as unit test.")
    config.addinivalue_line("markers", "api: mark test as API test.")
    config.addinivalue_line("markers", "agent: mark test as agent test.")
    config.addinivalue_line("markers", "bot: mark test as bot test.")
    config.addinivalue_line("markers", "worker: mark test as worker test.")
    config.addinivalue_line("markers", "orchestrator: mark test as orchestrator test.")
    config.addinivalue_line("markers", "security: mark test as security test.")
    config.addinivalue_line("markers", "performance: mark test as performance test.")
    config.addinivalue_line("markers", "stress: mark test as stress test.")

def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов"""
    # Пропуск медленных тестов, если не указан --runslow
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Добавление опций командной строки"""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--integration", action="store_true", default=False, help="run integration tests only"
    )
    parser.addoption(
        "--unit", action="store_true", default=False, help="run unit tests only"
    )
    parser.addoption(
        "--api", action="store_true", default=False, help="run API tests only"
    )

# === Test Environment Configuration ===
# .env.test

# Переменные окружения для тестирования
TESTING=true
FLASK_ENV=test
FLASK_DEBUG=false
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/1
BOT_TOKEN=test_bot_token
CHAT_ID=test_chat_id
API_BASE_URL=https://test.xvpn.local:8443
JWT_SECRET=test_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=1

# === Docker Test Environment ===
# docker-compose.test.yml

version: '3.8'

services:
  # === Test Database ===
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: xvpn_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data
      
  # === Test Redis ===
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
      
  # === Test MQTT Broker ===
  test-mqtt:
    image: eclipse-mosquitto:2
    ports:
      - "1884:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
      
  # === Test HTTP Server ===
  test-http:
    image: kennethreitz/httpbin
    ports:
      - "8081:80"
      
  # === Test XRay Core ===
  test-xray:
    image: teddysun/xray:latest
    ports:
      - "1081:1080"
      - "8082:8080"
    volumes:
      - ./config/xray/test.json:/etc/xray/config.json
      
  # === Test Environment ===
  test-env:
    image: python:3.10-slim
    volumes:
      - .:/app
      - ./tests:/app/tests
    working_dir: /app
    environment:
      - TESTING=true
      - DATABASE_URL=postgresql://test_user:test_password@test-db:5432/xvpn_test
      - REDIS_URL=redis://test-redis:6379/1
      - MQTT_BROKER_HOST=test-mqtt
      - MQTT_BROKER_PORT=1883
      - HTTPBIN_URL=http://test-http:80
      - XRAY_CONFIG_PATH=/app/config/xray/test.json
    command: tail -f /dev/null

# === Test Configuration Files ===
# config/xray/test.json

{
  "inbounds": [
    {
      "port": 1080,
      "listen": "0.0.0.0",
      "protocol": "socks",
      "settings": {
        "auth": "noauth",
        "udp": false
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}

# === Test Scripts ===
# scripts/run_tests.sh

#!/bin/bash

# Скрипт для запуска тестов XVPN

set -e  # Выход при любой ошибке

echo "🚀 Running XVPN Tests..."
echo "========================"

# Переменные окружения
export TESTING=true
export PYTHONPATH=.
export LOG_LEVEL=INFO

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Установка переменных
TEST_TYPE=${1:-all}
COVERAGE=${2:-true}
VERBOSE=${3:-false}

# Функция для запуска юнит тестов
run_unit_tests() {
    echo "🧪 Running Unit Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/unit/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/unit \
            --cov-report=xml:coverage-unit.xml \
            --cov-report=term-missing \
            --junitxml=junit-unit.xml \
            --tb=short
    else
        pytest tests/unit/ -v \
            --tb=short
    fi
    
    echo "✅ Unit Tests Completed!"
}

# Функция для запуска интеграционных тестов
run_integration_tests() {
    echo "🔗 Running Integration Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/integration/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/integration \
            --cov-report=xml:coverage-integration.xml \
            --cov-report=term-missing \
            --junitxml=junit-integration.xml \
            --tb=short
    else
        pytest tests/integration/ -v \
            --tb=short
    fi
    
    echo "✅ Integration Tests Completed!"
}

# Функция для запуска функциональных тестов
run_functional_tests() {
    echo "⚙️ Running Functional Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/functional/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/functional \
            --cov-report=xml:coverage-functional.xml \
            --cov-report=term-missing \
            --junitxml=junit-functional.xml \
            --tb=short
    else
        pytest tests/functional/ -v \
            --tb=short
    fi
    
    echo "✅ Functional Tests Completed!"
}

# Функция для запуска тестов API
run_api_tests() {
    echo "🌐 Running API Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/api/ -v \
            --cov=server/api \
            --cov-report=html:htmlcov/api \
            --cov-report=xml:coverage-api.xml \
            --cov-report=term-missing \
            --junitxml=junit-api.xml \
            --tb=short
    else
        pytest tests/api/ -v \
            --tb=short
    fi
    
    echo "✅ API Tests Completed!"
}

# Функция для запуска тестов агентов
run_agent_tests() {
    echo "🤖 Running Agent Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/agent/ -v \
            --cov=server/agent \
            --cov-report=html:htmlcov/agent \
            --cov-report=xml:coverage-agent.xml \
            --cov-report=term-missing \
            --junitxml=junit-agent.xml \
            --tb=short
    else
        pytest tests/agent/ -v \
            --tb=short
    fi
    
    echo "✅ Agent Tests Completed!"
}

# Функция для запуска тестов бота
run_bot_tests() {
    echo "💬 Running Bot Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/bot/ -v \
            --cov=server/admin \
            --cov-report=html:htmlcov/bot \
            --cov-report=xml:coverage-bot.xml \
            --cov-report=term-missing \
            --junitxml=junit-bot.xml \
            --tb=short
    else
        pytest tests/bot/ -v \
            --tb=short
    fi
    
    echo "✅ Bot Tests Completed!"
}

# Функция для запуска тестов безопасности
run_security_tests() {
    echo "🛡️ Running Security Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/security/ -v \
            --cov=security \
            --cov-report=html:htmlcov/security \
            --cov-report=xml:coverage-security.xml \
            --cov-report=term-missing \
            --junitxml=junit-security.xml \
            --tb=short
    else
        pytest tests/security/ -v \
            --tb=short
    fi
    
    echo "✅ Security Tests Completed!"
}

# Функция для запуска тестов производительности
run_performance_tests() {
    echo "⚡ Running Performance Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/performance/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/performance \
            --cov-report=xml:coverage-performance.xml \
            --cov-report=term-missing \
            --junitxml=junit-performance.xml \
            --tb=short \
            -m "performance"
    else
        pytest tests/performance/ -v \
            --tb=short \
            -m "performance"
    fi
    
    echo "✅ Performance Tests Completed!"
}

# Функция для запуска всех тестов
run_all_tests() {
    echo "🎯 Running All Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/all \
            --cov-report=xml:coverage-all.xml \
            --cov-report=term-missing \
            --junitxml=junit-all.xml \
            --tb=short
    else
        pytest tests/ -v \
            --tb=short
    fi
    
    echo "✅ All Tests Completed!"
}

# Функция для запуска быстрых тестов
run_fast_tests() {
    echo "🏃 Running Fast Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/fast \
            --cov-report=xml:coverage-fast.xml \
            --cov-report=term-missing \
            --junitxml=junit-fast.xml \
            --tb=short \
            -m "not slow"
    else
        pytest tests/ -v \
            --tb=short \
            -m "not slow"
    fi
    
    echo "✅ Fast Tests Completed!"
}

# Функция для запуска медленных тестов
run_slow_tests() {
    echo "🐢 Running Slow Tests..."
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/ -v \
            --cov=src \
            --cov=server \
            --cov=client \
            --cov-report=html:htmlcov/slow \
            --cov-report=xml:coverage-slow.xml \
            --cov-report=term-missing \
            --junitxml=junit-slow.xml \
            --tb=short \
            -m "slow"
    else
        pytest tests/ -v \
            --tb=short \
            -m "slow"
    fi
    
    echo "✅ Slow Tests Completed!"
}

# === Обработка параметров ===
case $TEST_TYPE in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "functional")
        run_functional_tests
        ;;
    "api")
        run_api_tests
        ;;
    "agent")
        run_agent_tests
        ;;
    "bot")
        run_bot_tests
        ;;
    "security")
        run_security_tests
        ;;
    "performance")
        run_performance_tests
        ;;
    "fast")
        run_fast_tests
        ;;
    "slow")
        run_slow_tests
        ;;
    "all"|*)
        run_all_tests
        ;;
esac

# === Генерация отчета ===
echo "📊 Generating Test Report..."

# Комбинирование отчетов о покрытии, если их несколько
if [ "$COVERAGE" = "true" ]; then
    if [ -f "coverage-unit.xml" ] || [ -f "coverage-integration.xml" ] || [ -f "coverage-functional.xml" ]; then
        echo "Merging coverage reports..."
        # TODO: Add coverage report merging logic
    fi
fi

# Создание директории для отчетов
mkdir -p test-reports

# Перемещение junit отчетов
if [ -f "junit-unit.xml" ]; then
    mv junit-unit.xml test-reports/
fi

if [ -f "junit-integration.xml" ]; then
    mv junit-integration.xml test-reports/
fi

if [ -f "junit-functional.xml" ]; then
    mv junit-functional.xml test-reports/
fi

if [ -f "junit-all.xml" ]; then
    mv junit-all.xml test-reports/
fi

# Отправка уведомления
echo "🔔 Tests completed with coverage=$COVERAGE, verbose=$VERBOSE"
echo "📂 Test reports available in test-reports/ and htmlcov/ directories"

# === Проверка покрытия кода ===
if [ "$COVERAGE" = "true" ] && [ -f "coverage-all.xml" ]; then
    echo "📈 Checking code coverage..."
    coverage_report=$(coverage report --fail-under=80 2>&1 || echo "Coverage check failed")
    echo "$coverage_report"
fi

echo "🏁 Test execution completed!"

# === Конец скрипта ===
exit 0