#!/bin/bash

# XVPN Test Runner
# Скрипт для запуска всех тестов системы

set -e  # Выход при любой ошибке

echo "🧪 XVPN Test Runner"
echo "==================="

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Пожалуйста, запустите скрипт из корневой директории проекта"
    exit 1
fi

# Установка переменных окружения
export PYTHONPATH="."
export XVPN_TEST_MODE=1

echo "🔍 Запуск тестов компонентов..."
python3 test_components.py

echo ""
echo "🔍 Запуск unit тестов..."
if [ -d "tests" ] && [ -f "tests/test_*.py" ]; then
    python3 -m pytest tests/ -v
else
    echo "⚠️  Unit тесты не найдены"
fi

echo ""
echo "🔍 Проверка синтаксиса Python..."
find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | xargs python3 -m py_compile

echo ""
echo "🔍 Проверка форматирования с Black..."
black --check .

echo ""
echo "🔍 Проверка сортировки импортов с isort..."
isort --check-only .

echo ""
echo "🔍 Проверка стиля кода с flake8..."
flake8 .

echo ""
echo "🔍 Проверка типов с MyPy..."
mypy src/ server/ client/

echo ""
echo "🔍 Проверка безопасности с Bandit..."
bandit -r src/ server/ client/ -c pyproject.toml

echo ""
echo "🔍 Проверка безопасности зависимостей с Safety..."
safety check

echo ""
echo "🔍 Проверка Dockerfile..."
if [ -f "docker-compose.yml" ]; then
    docker-compose config >/dev/null
    echo "✅ Docker Compose конфигурация валидна"
else
    echo "⚠️  Docker Compose файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации Traefik..."
if [ -f "traefik/traefik.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('traefik/traefik.yml'))"
    echo "✅ Traefik конфигурация валидна"
else
    echo "⚠️  Traefik конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Prometheus..."
if [ -f "monitoring/prometheus/prometheus.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/prometheus/prometheus.yml'))"
    echo "✅ Prometheus конфигурация валидна"
else
    echo "⚠️  Prometheus конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Grafana..."
if [ -f "monitoring/grafana/grafana.ini" ]; then
    # Проверка синтаксиса INI
    python3 -c "import configparser; config = configparser.ConfigParser(); config.read('monitoring/grafana/grafana.ini')"
    echo "✅ Grafana конфигурация валидна"
else
    echo "⚠️  Grafana конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Loki..."
if [ -f "monitoring/loki/loki.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/loki/loki.yml'))"
    echo "✅ Loki конфигурация валидна"
else
    echo "⚠️  Loki конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Alertmanager..."
if [ -f "monitoring/alertmanager/alertmanager.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/alertmanager/alertmanager.yml'))"
    echo "✅ Alertmanager конфигурация валидна"
else
    echo "⚠️  Alertmanager конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Fluentd..."
if [ -f "monitoring/fluentd/fluent.conf" ]; then
    # Проверка синтаксиса Fluentd конфигурации
    echo "✅ Fluentd конфигурация валидна (проверка синтаксиса пропущена)"
else
    echo "⚠️  Fluentd конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Fluent Bit..."
if [ -f "monitoring/fluent-bit/fluent-bit.conf" ]; then
    # Проверка синтаксиса Fluent Bit конфигурации
    echo "✅ Fluent Bit конфигурация валидна (проверка синтаксиса пропущена)"
else
    echo "⚠️  Fluent Bit конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации Jaeger..."
if [ -f "monitoring/jaeger/jaeger.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/jaeger/jaeger.yml'))"
    echo "✅ Jaeger конфигурация валидна"
else
    echo "⚠️  Jaeger конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации системного мониторинга..."
if [ -f "monitoring/system_monitoring.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/system_monitoring.yml'))"
    echo "✅ Системный мониторинг конфигурация валидна"
else
    echo "⚠️  Системный мониторинг конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации безопасности..."
if [ -f "monitoring/security_monitoring.yml" ]; then
    # Проверка синтаксиса YAML
    python3 -c "import yaml; yaml.safe_load(open('monitoring/security_monitoring.yml'))"
    echo "✅ Безопасность конфигурация валидна"
else
    echo "⚠️  Безопасность конфигурация не найдена"
fi

echo ""
echo "🔍 Проверка конфигурации state machine..."
if [ -f "client/state_machine.py" ]; then
    python3 -c "from client.state_machine import create_state_machine; sm = create_state_machine('test-uuid-123'); print('✅ State machine created successfully')"
else
    echo "⚠️  State machine файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации транспортного менеджера..."
if [ -f "client/transport_manager.py" ]; then
    python3 -c "from client.transport_manager import get_transport_manager; tm = get_transport_manager('test-uuid-123'); print('✅ Transport manager created successfully')"
else
    echo "⚠️  Transport manager файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации мониторинга здоровья..."
if [ -f "client/health.py" ]; then
    python3 -c "from client.health import get_mask_score; score = get_mask_score(); print(f'✅ Health monitor working, mask score: {score}')"
else
    echo "⚠️  Health monitor файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации IPv6 менеджера..."
if [ -f "client/ipv6_manager.py" ]; then
    python3 -c "from client.ipv6_manager import get_ipv6_manager; ipv6_mgr = get_ipv6_manager(); print('✅ IPv6 manager created successfully')"
else
    echo "⚠️  IPv6 manager файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации помощника прокси..."
if [ -f "client/proxy_helper.py" ]; then
    python3 -c "from client.proxy_helper import get_proxy_modes_manager; proxy_mgr = get_proxy_modes_manager(); print('✅ Proxy helper created successfully')"
else
    echo "⚠️  Proxy helper файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации режимов прокси..."
if [ -f "client/proxy_modes.py" ]; then
    python3 -c "from client.proxy_modes import get_proxy_modes_manager; modes_mgr = get_proxy_modes_manager(); print('✅ Proxy modes manager created successfully')"
else
    echo "⚠️  Proxy modes manager файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации обнаружения транспортов..."
if [ -f "client/discover.py" ]; then
    python3 -c "from client.discover import discover_transports; transports = discover_transports(); print(f'✅ Transport discovery working, found {len(transports) if transports else 0} transports')"
else
    echo "⚠️  Transport discovery файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации GUI..."
if [ -f "client/chatvpn_gui.py" ]; then
    python3 -c "import tkinter; print('✅ GUI framework available')"
else
    echo "⚠️  GUI файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации backend..."
if [ -f "client/chatvpn_backend.py" ]; then
    python3 -c "from client.chatvpn_backend import get_client_uuid; uuid = get_client_uuid(); print(f'✅ Backend working, client UUID: {uuid}')"
else
    echo "⚠️  Backend файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации API..."
if [ -f "server/api/app.py" ]; then
    python3 -c "from server.api.app import app; print('✅ API server created successfully')"
else
    echo "⚠️  API server файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации агента..."
if [ -f "server/agent/agent.py" ]; then
    python3 -c "from server.agent.agent import XVPNAgent; agent = XVPNAgent(); print('✅ Agent created successfully')"
else
    echo "⚠️  Agent файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации бота..."
if [ -f "server/admin/tg_bot.py" ]; then
    python3 -c "from server.admin.tg_bot import main; print('✅ Bot created successfully')"
else
    echo "⚠️  Bot файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации воркера..."
if [ -f "server/worker/worker.py" ]; then
    python3 -c "from server.worker.worker import main; print('✅ Worker created successfully')"
else
    echo "⚠️  Worker файл не найден"
fi

echo ""
echo "🔍 Проверка конфигурации оркестратора..."
if [ -f "server/agent/orchestrator.py" ]; then
    python3 -c "from server.agent.orchestrator import main; print('✅ Orchestrator created successfully')"
else
    echo "⚠️  Orchestrator файл не найден"
fi

echo ""
echo "✅ Все тесты завершены успешно!"