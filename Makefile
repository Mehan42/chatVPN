# XVPN Makefile
# Удобные команды для разработки и развертывания

# === Переменные ===
PYTHON := python3
PIP := pip3
UV := uv
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := xvpn
VERSION := 1.0.0

# === Директории ===
SRC_DIR := .
BUILD_DIR := build
DIST_DIR := dist
TEST_DIR := tests
LOGS_DIR := logs
DATA_DIR := data

# === Цели по умолчанию ===
.PHONY: help install test clean build docker-run docker-build docs dev-setup format lint type-check security-check pre-commit install-dev install-prod run-dev run-prod stop-dev stop-prod logs-dev logs-prod test-unit test-integration test-all coverage check check-all update-deps clean-all

# === Помощь ===
help:
	@echo "XVPN Development Commands"
	@echo "========================="
	@echo "make install          - Установка зависимостей"
	@echo "make test             - Запуск тестов"
	@echo "make clean            - Очистка сборочных файлов"
	@echo "make build            - Сборка проекта"
	@echo "make docker-run       - Запуск в Docker"
	@echo "make docker-build     - Сборка Docker образов"
	@echo "make docs             - Генерация документации"
	@echo "make dev-setup        - Настройка окружения разработки"
	@echo "make format           - Форматирование кода"
	@echo "make lint             - Проверка стиля кода"
	@echo "make type-check       - Статическая типизация"
	@echo "make security-check   - Проверка безопасности"
	@echo "make pre-commit       - Запуск pre-commit хуков"
	@echo "make install-dev      - Установка для разработки"
	@echo "make install-prod     - Установка для продакшена"
	@echo "make run-dev          - Запуск в режиме разработки"
	@echo "make run-prod         - Запуск в режиме продакшена"
	@echo "make stop-dev         - Остановка разработки"
	@echo "make stop-prod        - Остановка продакшена"
	@echo "make logs-dev         - Логи разработки"
	@echo "make logs-prod        - Логи продакшена"
	@echo "make test-unit        - Юнит тесты"
	@echo "make test-integration - Интеграционные тесты"
	@echo "make test-all         - Все тесты"
	@echo "make coverage         - Покрытие кода"
	@echo "make check            - Быстрая проверка"
	@echo "make check-all        - Полная проверка"
	@echo "make update-deps      - Обновление зависимостей"
	@echo "make clean-all        - Полная очистка"

# === Установка ===
install:
	@echo "🚀 Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,server,agent,bot,monitoring,test]"
	@echo "✅ Dependencies installed successfully!"

# === Тестирование ===
test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v
	@echo "✅ Tests completed!"

test-unit:
	@echo "🔬 Running unit tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v -m unit
	@echo "✅ Unit tests completed!"

test-integration:
	@echo "🔗 Running integration tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v -m integration
	@echo "✅ Integration tests completed!"

test-all:
	@echo "🚀 Running all tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v -m "unit or integration"
	@echo "✅ All tests completed!"

# === Очистка ===
clean:
	@echo "🧹 Cleaning build files..."
	rm -rf $(BUILD_DIR) $(DIST_DIR) *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	@echo "✅ Clean completed!"

clean-all: clean
	@echo "🧨 Deep cleaning..."
	rm -rf venv .venv .pytest_cache .mypy_cache .coverage htmlcov
	docker system prune -f
	@echo "🔥 Deep clean completed!"

# === Сборка ===
build:
	@echo "🏗️ Building project..."
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "✅ Build completed!"

# === Docker ===
docker-build:
	@echo "🐳 Building Docker images..."
	$(DOCKER_COMPOSE) build
	@echo "✅ Docker images built successfully!"

docker-run:
	@echo "🚀 Starting services with Docker Compose..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started! Check status with: docker-compose ps"

docker-dev:
	@echo "🔧 Starting development services..."
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d
	@echo "✅ Development services started!"

# === Документация ===
docs:
	@echo "📚 Generating documentation..."
	# TODO: Add documentation generation commands
	@echo "✅ Documentation generation completed!"

# === Разработка ===
dev-setup:
	@echo "🔧 Setting up development environment..."
	./setup_dev_env.sh
	@echo "✅ Development environment setup completed!"

# === Форматирование ===
format:
	@echo "🎨 Formatting code..."
	black .
	isort .
	docformatter --in-place --recursive --wrap-descriptions=88 --wrap-summaries=88 .
	@echo "✅ Code formatted successfully!"

# === Линтинг ===
lint:
	@echo "🔍 Checking code style..."
	flake8 .
	pylint src/ server/ client/
	@echo "✅ Code style check completed!"

# === Статическая типизация ===
type-check:
	@echo "🧮 Checking types..."
	mypy src/ server/ client/
	@echo "✅ Type checking completed!"

# === Безопасность ===
security-check:
	@echo "🛡️ Checking security..."
	bandit -r src/ server/ client/
	safety check
	@echo "✅ Security check completed!"

# === Pre-commit ===
pre-commit:
	@echo "🔗 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks completed!"

# === Установка для разработки ===
install-dev: clean
	@echo "🔧 Installing for development..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,server,agent,bot,monitoring,test]"
	@echo "✅ Development installation completed!"

# === Установка для продакшена ===
install-prod: clean
	@echo "🚀 Installing for production..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[server,agent,bot,monitoring]"
	@echo "✅ Production installation completed!"

# === Запуск в режиме разработки ===
run-dev:
	@echo "🔧 Starting development server..."
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d
	@echo "✅ Development server started!"

# === Запуск в режиме продакшена ===
run-prod:
	@echo "🚀 Starting production server..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Production server started!"

# === Остановка разработки ===
stop-dev:
	@echo "🛑 Stopping development server..."
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down
	@echo "✅ Development server stopped!"

# === Остановка продакшена ===
stop-prod:
	@echo "🛑 Stopping production server..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Production server stopped!"

# === Логи разработки ===
logs-dev:
	@echo "📝 Development logs:"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

# === Логи продакшена ===
logs-prod:
	@echo "📝 Production logs:"
	$(DOCKER_COMPOSE) logs -f

# === Покрытие кода ===
coverage:
	@echo "📊 Running coverage..."
	$(PYTHON) -m pytest $(TEST_DIR) --cov=src --cov=server --cov=client --cov-report=html --cov-report=term
	@echo "✅ Coverage completed! Open htmlcov/index.html to view report."

# === Быстрая проверка ===
check:
	@echo "⚡ Quick check..."
	$(PYTHON) -m pytest $(TEST_DIR) -x --tb=line
	black --check .
	flake8 .
	mypy src/ server/ client/
	@echo "✅ Quick check passed!"

# === Полная проверка ===
check-all:
	@echo "🔍 Full check..."
	make check
	make lint
	make type-check
	make security-check
	make pre-commit
	@echo "✅ Full check passed!"

# === Обновление зависимостей ===
update-deps:
	@echo "🔄 Updating dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev,server,agent,bot,monitoring,test]"
	@echo "✅ Dependencies updated!"

# === Алиасы ===
server: run-prod
client: run-dev
agent: run-dev
bot: run-dev
orchestrator: run-dev
worker: run-dev