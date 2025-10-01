
# Руководство по интеграции Traefik и uv/uvx для XVPN

## 📋 Введение

Это руководство описывает процесс интеграции Traefik с заменой venv на uv и uvx для оптимизации производительности XVPN сервиса. Миграция на uv позволяет значительно ускорить установку зависимостей и уменьшить размер Docker образов.

## 🎯 Преимущества использования uv/uvx

### 1. Скорость установки зависимостей
- **В 10-50 раз быстрее** pip/venv
- Параллельная загрузка и установка пакетов
- Кэширование зависимостей на уровне файловой системы

### 2. Уменьшение размера Docker образов
- Многостадийная сборка с uv
- Оптимизированные слои Docker
- Кэширование на уровне сборки

### 3. Улучшенная производительность
- Быстрый запуск контейнеров
- Оптимизированное управление зависимостями
- Меньше потребление ресурсов

### 4. Современный инструмент
- Единый инструмент для управления зависимостями
- Поддержка современных форматов (pyproject.toml)
- Автоматическое разрешение зависимостей

## 🏗️ Архитектура интеграции

### Схема взаимодействия
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Docker Compose │    │     Traefik     │    │     uv/uvx      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   XVPN Services │    │   Load Balancer │    │ Package Manager │
│   - API         │    │   - SSL Termination│    │   - Fast Install│
│   - Agent       │    │   - Routing     │    │   - Caching     │
│   - Bot         │    │   - Health Check│    │   - Optimization│
│   - Worker      │    └─────────────────┘    └─────────────────┘
└─────────────────┘
```

### Компоненты системы

1. **Docker Compose** - Оркестрация контейнеров
2. **Traefik** - Reverse proxy и load balancer
3. **uv** - Менеджер пакетов Python
4. **uvx** - Исполнитель Python приложений
5. **Systemd** - Системные сервисы (опционально)

## 📦 Установка и настройка

### 1. Установка uv

```bash
# Установка uv для текущего пользователя
curl -LsSf https://astral.sh/uv/install.sh | sh

# Добавление в PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Проверка установки
uv --version
uvx --version
```

### 2. Системная установка (рекомендуется)

```bash
# Использование скрипта установки
sudo ./scripts/install_uv_system.sh

# Или ручная установка
sudo ln -sf "$HOME/.cargo/bin/uv" "/usr/local/bin/uv"
sudo ln -sf "$HOME/.cargo/bin/uvx" "/usr/local/bin/uvx"
```

### 3. Настройка pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "xvpn"
version = "1.0.0"
description = "XVPN - Интеллектуальная VPN с AI-агентами"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "XVPN Team", email = "team@xvpn.local"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "flask>=3.0.0",
    "requests>=2.31.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
server = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "gunicorn>=21.0.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "redis>=5.0.0",
    "celery>=5.3.0",
    "flower>=2.0.0",
]
agent = [
    "openai>=1.0.0",
    "langchain>=0.1.0",
    "chromadb>=0.4.0",
    "tiktoken>=0.5.0",
    "sentence-transformers>=2.2.0",
    "faiss-cpu>=1.7.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
]
bot = [
    "python-telegram-bot>=20.0.0",
    "aiogram>=3.0.0",
    "pydantic-settings>=2.0.0",
]
monitoring = [
    "prometheus-client>=0.19.0",
    "grafana-api>=1.0.0",
    "structlog>=23.0.0",
    "loguru>=0.7.0",
    "rich-argparse>=1.0.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.6.0",
    "pre-commit>=3.4.0",
    "bandit>=1.7.0",
    "safety>=3.0.0",
]

[project.scripts]
xvpn-api = "server.api.main:main"
xvpn-agent = "server.agent.main:main"
xvpn-bot = "server.admin.main:main"
xvpn-worker = "server.worker.main:main"

[project.urls]
Homepage = "https://xvpn.local"
Repository = "https://github.com/xvpn/xvpn"
Documentation = "https://docs.xvpn.local"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.6.0",
    "pre-commit>=3.4.0",
    "bandit>=1.7.0",
    "safety>=3.0.0",
]

[tool.uv.sources]
# Настройка источников пакетов при необходимости

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["xvpn"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=.",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "slow: marks tests as slow