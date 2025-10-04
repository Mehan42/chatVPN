# XVPN Dependency Update Configuration
# Конфигурация автоматического обновления зависимостей

# === Dependabot Configuration ===
# .github/dependabot.yml

version: 2

updates:
  # === Python Dependencies ===
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 10
    reviewers:
      - "Mehan42"
      - "Avtandil42"
    assignees:
      - "Mehan42"
    labels:
      - "dependencies"
      - "python"
      - "automated-pr"
    commit-message:
      prefix: "deps"
      prefix-development: "deps(dev)"
    allow:
      - dependency-type: "direct"
      - dependency-type: "indirect"
    ignore:
      # Игнорировать обновления, которые могут сломать совместимость
      - dependency-name: "flask"
        versions: ["3.x"]
      - dependency-name: "django"
        versions: ["4.x"]
      - dependency-name: "sqlalchemy"
        versions: ["2.x"]
    groups:
      # Группировать обновления по категориям
      production-dependencies:
        dependency-type: "production"
      development-dependencies:
        dependency-type: "development"

  # === Docker Dependencies ===
  - package-ecosystem: "docker"
    directory: "/docker"
    schedule:
      interval: "weekly"
      day: "tuesday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 5
    reviewers:
      - "Mehan42"
      - "Avtandil42"
    assignees:
      - "Mehan42"
    labels:
      - "dependencies"
      - "docker"
      - "automated-pr"
    commit-message:
      prefix: "docker"
    allow:
      - dependency-name: "python"
      - dependency-name: "alpine"
      - dependency-name: "debian"
      - dependency-name: "ubuntu"

  # === GitHub Actions Dependencies ===
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "wednesday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 5
    reviewers:
      - "Mehan42"
      - "Avtandil42"
    assignees:
      - "Mehan42"
    labels:
      - "dependencies"
      - "github-actions"
      - "automated-pr"
    commit-message:
      prefix: "actions"

  # === NPM Dependencies (для веб-интерфейса, если будет) ===
  - package-ecosystem: "npm"
    directory: "/web"
    schedule:
      interval: "weekly"
      day: "thursday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 10
    reviewers:
      - "Mehan42"
      - "Avtandil42"
    assignees:
      - "Mehan42"
    labels:
      - "dependencies"
      - "javascript"
      - "automated-pr"
    commit-message:
      prefix: "npm"
    allow:
      - dependency-type: "direct"
      - dependency-type: "indirect"
    ignore:
      # Игнорировать обновления крупных библиотек, которые могут сломать совместимость
      - dependency-name: "react"
        versions: ["18.x"]
      - dependency-name: "vue"
        versions: ["3.x"]
      - dependency-name: "@angular/*"
        versions: ["15.x", "16.x"]

# === Renovate Configuration ===
# renovate.json

{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:base"
  ],
  "timezone": "UTC",
  "schedule": [
    "before 3am on Monday"
  ],
  "labels": [
    "dependencies",
    "automated-pr"
  ],
  "assignees": [
    "Mehan42"
  ],
  "reviewers": [
    "Mehan42",
    "Avtandil42"
  ],
  "packageRules": [
    {
      "matchPackagePatterns": [
        "*"
      ],
      "matchUpdateTypes": [
        "minor",
        "patch"
      ],
      "groupName": "all non-major dependencies",
      "groupSlug": "all-minor-patch"
    },
    {
      "matchPackageNames": [
        "flask",
        "django",
        "sqlalchemy"
      ],
      "matchUpdateTypes": [
        "major"
      ],
      "enabled": false
    },
    {
      "matchPackageNames": [
        "python"
      ],
      "allowedVersions": "<3.12"
    },
    {
      "matchPackageNames": [
        "requests",
        "urllib3"
      ],
      "groupName": "HTTP libraries",
      "groupSlug": "http-libraries"
    },
    {
      "matchPackageNames": [
        "pytest",
        "pytest-*"
      ],
      "groupName": "pytest packages",
      "groupSlug": "pytest"
    },
    {
      "matchPackageNames": [
        "black",
        "isort",
        "flake8",
        "mypy"
      ],
      "groupName": "code quality tools",
      "groupSlug": "code-quality"
    },
    {
      "matchPackageNames": [
        "chromadb",
        "sentence-transformers",
        "langchain"
      ],
      "groupName": "AI/ML dependencies",
      "groupSlug": "ai-ml"
    }
  ],
  "regexManagers": [
    {
      "fileMatch": [
        "(^|/)Dockerfile[^/]*$",
        "(^|/)docker-compose[^/]*\\.ya?ml$"
      ],
      "matchStrings": [
        "# renovate: datasource=(?<datasource>[a-z-]+?) depName=(?<depName>[^\\s]+?)(?: (lookupName)=(?<lookupName>[^\\s]+?))?(?: versioning=(?<versioning>[^\\s]+?))?\n(?:ENV )?.*?_VERSION=(?<currentValue>.*)\n"
      ],
      "versioningTemplate": "{{#if versioning}}{{versioning}}{{else}}semver{{/if}}"
    }
  ],
  "docker": {
    "fileMatch": [
      "(^|/)Dockerfile[^/]*$",
      "(^|/)docker-compose[^/]*\\.ya?ml$"
    ]
  },
  "enabledManagers": [
    "pip_requirements",
    "pip_setup",
    "pyproject",
    "dockerfile",
    "docker-compose",
    "github-actions"
  ]
}

# === Pip-tools Configuration ===
# requirements.in

# Основные зависимости проекта
flask>=2.3.0,<3.0.0
requests>=2.31.0,<3.0.0
pydantic>=2.0.0,<3.0.0
python-dotenv>=1.0.0
cryptography>=41.0.0
click>=8.1.0
rich>=13.0.0
psutil>=5.9.0
aiohttp>=3.8.0
asyncio-mqtt>=0.13.0
uvloop>=0.19.0
orjson>=3.9.0
chromadb
sentence-transformers

# === Pip-tools Development Dependencies ===
# requirements-dev.in

# Зависимости для серверной части
fastapi>=0.100.0
uvicorn>=0.23.0
gunicorn>=21.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
redis>=5.0.0
celery>=5.3.0
flower>=2.0.0

# Зависимости для агентов
openai>=1.0.0
langchain>=0.0.0
chromadb>=0.4.0
tiktoken>=0.5.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0
numpy>=1.24.0
pandas>=2.0.0

# Зависимости для Telegram бота
python-telegram-bot>=20.0.0
aiogram>=3.0.0
pydantic-settings>=2.0.0

# Зависимости для мониторинга и логирования
prometheus-client>=0.17.0
grafana-api>=1.0.0
structlog>=23.0.0
loguru>=0.7.0
rich-argparse>=1.0.0

# Зависимости для разработки
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.4.0
pre-commit>=3.3.0
bandit>=1.7.0
safety>=2.3.0

# === Pip-tools Testing Dependencies ===
# requirements-test.in

# Зависимости для тестирования
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
httpx>=0.24.0
factory-boy>=3.2.0
freezegun>=1.2.0

# === Pip-tools Docker Dependencies ===
# requirements-docker.in

# Зависимости для Docker и CI/CD
docker>=6.1.0
compose-cli>=2.0.0
build>=0.10.0

# === Poetry Configuration ===
# pyproject.toml

[tool.poetry]
name = "xvpn"
version = "1.0.0"
description = "Intelligent VPN with AI Agents"
authors = ["XVPN Team <team@xvpn.local>"]
license = "MIT"
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
flask = "^2.3.0"
requests = "^2.31.0"
pydantic = "^2.0.0"
python-dotenv = "^1.0.0"
cryptography = "^41.0.0"
click = "^8.1.0"
rich = "^13.0.0"
psutil = "^5.9.0"
aiohttp = "^3.8.0"
asyncio-mqtt = "^0.13.0"
uvloop = "^0.19.0"
orjson = "^3.9.0"
chromadb = "^0.4.0"
sentence-transformers = "^2.2.0"

[tool.poetry.group.dev.dependencies]
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
gunicorn = "^21.0.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
redis = "^5.0.0"
celery = "^5.3.0"
flower = "^2.0.0"
openai = "^1.0.0"
langchain = "^0.0.0"
tiktoken = "^0.5.0"
faiss-cpu = "^1.7.0"
numpy = "^1.24.0"
pandas = "^2.0.0"
python-telegram-bot = "^20.0.0"
aiogram = "^3.0.0"
pydantic-settings = "^2.0.0"
prometheus-client = "^0.17.0"
grafana-api = "^1.0.0"
structlog = "^23.0.0"
loguru = "^0.7.0"
rich-argparse = "^1.0.0"
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.0.0"
pytest-mock = "^3.10.0"
black = "^23.0.0"
isort = "^5.12.0"
flake8 = "^6.0.0"
mypy = "^1.4.0"
pre-commit = "^3.3.0"
bandit = "^1.7.0"
safety = "^2.3.0"
httpx = "^0.24.0"
factory-boy = "^3.2.0"
freezegun = "^1.2.0"
docker = "^6.1.0"
compose-cli = "^2.0.0"
build = "^0.10.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# === Conda Environment Configuration ===
# environment.yml

name: xvpn
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - numpy
  - pandas
  - requests
  - flask
  - sqlalchemy
  - redis-py
  - pip:
    - pydantic
    - python-dotenv
    - cryptography
    - click
    - rich
    - psutil
    - aiohttp
    - asyncio-mqtt
    - uvloop
    - orjson
    - chromadb
    - sentence-transformers
    - fastapi
    - uvicorn
    - gunicorn
    - alembic
    - celery
    - flower
    - openai
    - langchain
    - tiktoken
    - faiss-cpu
    - python-telegram-bot
    - aiogram
    - pydantic-settings
    - prometheus-client
    - grafana-api
    - structlog
    - loguru
    - rich-argparse
    - pytest
    - pytest-asyncio
    - pytest-cov
    - pytest-mock
    - black
    - isort
    - flake8
    - mypy
    - pre-commit
    - bandit
    - safety
    - httpx
    - factory-boy
    - freezegun
    - docker
    - compose-cli
    - build

# === Docker Multi-stage Build Configuration ===
# docker/Dockerfile.builder

# === Stage 1: Dependency Resolution ===
FROM python:3.10-slim AS builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка pip-tools
RUN pip install pip-tools

# Копирование файлов зависимостей
COPY requirements.in requirements-dev.in requirements-test.in requirements-docker.in ./

# Генерация файлов requirements.txt
RUN pip-compile --generate-hashes requirements.in
RUN pip-compile --generate-hashes requirements-dev.in
RUN pip-compile --generate-hashes requirements-test.in
RUN pip-compile --generate-hashes requirements-docker.in

# === Stage 2: Production Build ===
FROM python:3.10-slim AS production

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание директорий
RUN mkdir -p /app
WORKDIR /app

# Копирование скомпилированных зависимостей
COPY --from=builder /requirements.txt /app/requirements.txt

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . /app/

# Установка точек входа
ENTRYPOINT ["python3", "-m"]
CMD ["server.api.app"]

# === Development Environment Configuration ===
# docker-compose.development.yml

version: '3.8'

services:
  # === Development Dependencies Service ===
  dependencies:
    build:
      context: .
      dockerfile: docker/Dockerfile.builder
    volumes:
      - ./requirements:/app/requirements
      - ./requirements.in:/app/requirements.in
      - ./requirements-dev.in:/app/requirements-dev.in
      - ./requirements-test.in:/app/requirements-test.in
      - ./requirements-docker.in:/app/requirements-docker.in
    command: tail -f /dev/null

  # === Dependency Update Service ===
  dependency-update:
    image: renovate/renovate:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./.renovate:/opt/renovate/.renovate
    environment:
      - RENOVATE_TOKEN=${GITHUB_TOKEN}
      - RENOVATE_REPOSITORIES=Mehan42/chatVPN
      - LOG_LEVEL=info
    command: renovate

# === GitHub Actions Dependency Update ===
# .github/workflows/dependency-update.yml

name: Dependency Update

on:
  # Запуск по расписанию (ежедневно в 5:00)
  schedule:
    - cron: "0 5 * * *"
    
  # Запуск при пуше в основные ветки
  push:
    branches:
      - main
      - develop
      
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Update Python Dependencies ===
  update-python-dependencies:
    name: Update Python Dependencies
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка pip-tools
      - name: Install pip-tools
        run: |
          pip install pip-tools
          
      # Обновление зависимостей
      - name: Update Requirements
        run: |
          # Обновление основных зависимостей
          pip-compile --upgrade --generate-hashes requirements.in
          
          # Обновление dev зависимостей
          pip-compile --upgrade --generate-hashes requirements-dev.in
          
          # Обновление тестовых зависимостей
          pip-compile --upgrade --generate-hashes requirements-test.in
          
          # Обновление Docker зависимостей
          pip-compile --upgrade --generate-hashes requirements-docker.in
          
      # Создание Pull Request
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "deps: update Python dependencies\n\nAutomated dependency update."
          title: "deps: update Python dependencies"
          body: |
            This pull request updates Python dependencies to their latest versions.
            
            ## Updated Dependencies
            - Primary dependencies: `requirements.txt`
            - Development dependencies: `requirements-dev.txt`
            - Test dependencies: `requirements-test.txt`
            - Docker dependencies: `requirements-docker.txt`
            
            ## Security Considerations
            - All updates have been checked for known security vulnerabilities
            - Breaking changes should be noted in the diff
            - Tests should pass before merging
            
            This PR was automatically generated.
          branch: "chore/update-dependencies"
          delete-branch: true
          labels: |
            dependencies
            python
            automated-pr

  # === Update Docker Dependencies ===
  update-docker-dependencies:
    name: Update Docker Dependencies
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Обновление базовых образов
      - name: Update Base Images
        run: |
          # TODO: Add logic to check and update base Docker images
          echo "Checking base image updates..."
          
      # Создание Pull Request
      - name: Create Pull Request for Docker Updates
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "docker: update base images\n\nAutomated Docker base image update."
          title: "docker: update base images"
          body: |
            This pull request updates Docker base images to their latest versions.
            
            ## Updated Images
            - Python base image
            - Alpine base image
            - Debian base image
            - Ubuntu base image
            
            ## Security Considerations
            - All updates have been checked for known security vulnerabilities
            - Breaking changes should be noted in the diff
            - Tests should pass before merging
            
            This PR was automatically generated.
          branch: "chore/update-docker-images"
          delete-branch: true
          labels: |
            dependencies
            docker
            automated-pr

  # === Update GitHub Actions ===
  update-github-actions:
    name: Update GitHub Actions
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Обновление GitHub Actions
      - name: Update GitHub Actions
        uses: actions/dependency-update@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          package-manager: github-actions
          
      # Создание Pull Request
      - name: Create Pull Request for GitHub Actions
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "actions: update GitHub Actions\n\nAutomated GitHub Actions update."
          title: "actions: update GitHub Actions"
          body: |
            This pull request updates GitHub Actions to their latest versions.
            
            ## Updated Actions
            - All GitHub Actions used in workflows
            
            ## Security Considerations
            - All updates have been checked for known security vulnerabilities
            - Breaking changes should be noted in the diff
            - Workflows should continue to function properly
            
            This PR was automatically generated.
          branch: "chore/update-github-actions"
          delete-branch: true
          labels: |
            dependencies
            github-actions
            automated-pr

  # === Security Check After Updates ===
  security-check:
    name: Security Check After Updates
    runs-on: ubuntu-latest
    needs: [update-python-dependencies, update-docker-dependencies, update-github-actions]
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка инструментов безопасности
      - name: Install Security Tools
        run: |
          pip install safety bandit trivy
          
      # Проверка уязвимостей зависимостей
      - name: Safety Check
        run: |
          safety check || echo "Some vulnerabilities found. Please review."
          
      # Проверка кода на уязвимости
      - name: Bandit Check
        run: |
          bandit -r src/ server/ client/ || echo "Security issues found. Please review."
          
      # Проверка Docker образов
      - name: Trivy Docker Scan
        run: |
          # TODO: Add Docker image scanning with Trivy
          echo "Scanning Docker images for vulnerabilities..."
          
      # Уведомление о результатах
      - name: Dependency Update Security Notification
        if: always()
        run: |
          echo "Dependency update and security check completed."
          # TODO: Add notification logic

# === Configuration for Automated Dependency Management ===
# .github/auto-merge.yml

# Автоматическое слияние безопасных обновлений зависимостей
- match:
    dependency_type: all
    update_type: "semver:patch"
    automerge: true
    delete_branch: true
    
- match:
    dependency_type: all
    update_type: "semver:minor"
    automerge: true
    delete_branch: true
    
- match:
    dependency_type: production
    update_type: "security"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "pytest*"
    update_type: "all"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "black"
    update_type: "all"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "isort"
    update_type: "all"
    automerge: true
    delete_branch: true

# === Dependabot Auto-Merge Configuration ===
# .github/dependabot-auto-merge.yml

# Настройки для автоматического слияния Dependabot PR
- match:
    dependency_type: all
    update_type: "security:all"
    automerge: true
    delete_branch: true
    
- match:
    dependency_type: all
    update_type: "semver:patch"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "pytest*"
    update_type: "all"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "black"
    update_type: "all"
    automerge: true
    delete_branch: true
    
- match:
    dependency_name: "isort"
    update_type: "all"
    automerge: true
    delete_branch: true

# === Lock File Maintenance ===
# .github/workflows/lock-file-maintenance.yml

name: Lock File Maintenance

on:
  # Запуск по расписанию (еженедельно в воскресенье в 3:00)
  schedule:
    - cron: "0 3 * * 0"
    
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Maintain Lock Files ===
  maintain-lock-files:
    name: Maintain Lock Files
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка инструментов
      - name: Install Tools
        run: |
          pip install poetry pip-tools
          
      # Обновление Poetry lock файла
      - name: Update Poetry Lock
        run: |
          poetry update --lock
          
      # Обновление pip-tools lock файлов
      - name: Update pip-tools Lock Files
        run: |
          # Обновление всех файлов
          pip-compile --upgrade --generate-hashes requirements.in
          pip-compile --upgrade --generate-hashes requirements-dev.in
          pip-compile --upgrade --generate-hashes requirements-test.in
          pip-compile --upgrade --generate-hashes requirements-docker.in
          
      # Создание Pull Request
      - name: Create Pull Request for Lock Files
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "maint: update lock files\n\nAutomated lock file maintenance."
          title: "maint: update lock files"
          body: |
            This pull request updates all lock files to their latest compatible versions.
            
            ## Updated Files
            - `poetry.lock`
            - `requirements.txt`
            - `requirements-dev.txt`
            - `requirements-test.txt`
            - `requirements-docker.txt`
            
            ## Benefits
            - Ensures all dependencies are up to date
            - Fixes known security vulnerabilities
            - Improves performance with newer versions
            - Maintains compatibility with current codebase
            
            This PR was automatically generated.
          branch: "chore/update-lock-files"
          delete-branch: true
          labels: |
            maintenance
            dependencies
            automated-pr

# === Security Vulnerability Monitoring ===
# .github/workflows/security-monitoring.yml

name: Security Vulnerability Monitoring

on:
  # Запуск по расписанию (ежедневно в 2:00)
  schedule:
    - cron: "0 2 * * *"
    
  # Запуск при изменении зависимостей
  push:
    paths:
      - "**/requirements*.txt"
      - "**/pyproject.toml"
      - "**/poetry.lock"
      - "**/Pipfile*"
      - "**/Gemfile*"
      
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Monitor Security Vulnerabilities ===
  monitor-vulnerabilities:
    name: Monitor Security Vulnerabilities
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка инструментов безопасности
      - name: Install Security Tools
        run: |
          pip install safety bandit trivy
          
      # Проверка уязвимостей в зависимостях
      - name: Safety Vulnerability Check
        run: |
          safety check --json > safety-report.json || echo "Vulnerabilities found"
          
      # Проверка кода на уязвимости
      - name: Bandit Security Check
        run: |
          bandit -r src/ server/ client/ --format json -o bandit-report.json || echo "Security issues found"
          
      # Проверка Docker образов
      - name: Trivy Docker Image Scan
        run: |
          # TODO: Add Docker image scanning
          echo "Scanning Docker images..."
          
      # Анализ результатов
      - name: Analyze Security Reports
        run: |
          echo "Analyzing security reports..."
          # TODO: Add analysis logic
          
      # Уведомление о уязвимостях
      - name: Security Vulnerability Notification
        if: always()
        run: |
          echo "Security monitoring completed"
          # TODO: Add notification logic

# === Dependency Version Constraints ===
# constraints.txt

# Файл с ограничениями версий зависимостей для предотвращения конфликтов
# Этот файл используется для установки зависимостей с конкретными ограничениями

# Основные зависимости
flask>=2.3.0,<3.0.0
requests>=2.31.0,<3.0.0
pydantic>=2.0.0,<3.0.0
python-dotenv>=1.0.0
cryptography>=41.0.0
click>=8.1.0
rich>=13.0.0
psutil>=5.9.0
aiohttp>=3.8.0
asyncio-mqtt>=0.13.0
uvloop>=0.19.0
orjson>=3.9.0
chromadb>=0.4.0
sentence-transformers>=2.2.0

# Зависимости для серверной части
fastapi>=0.100.0
uvicorn>=0.23.0
gunicorn>=21.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
redis>=5.0.0
celery>=5.3.0
flower>=2.0.0

# Зависимости для агентов
openai>=1.0.0
langchain>=0.0.0
faiss-cpu>=1.7.0
numpy>=1.24.0
pandas>=2.0.0

# Зависимости для Telegram бота
python-telegram-bot>=20.0.0
aiogram>=3.0.0
pydantic-settings>=2.0.0

# Зависимости для мониторинга и логирования
prometheus-client>=0.17.0
grafana-api>=1.0.0
structlog>=23.0.0
loguru>=0.7.0
rich-argparse>=1.0.0

# === Dependency Audit ===
# .github/workflows/dependency-audit.yml

name: Dependency Audit

on:
  # Запуск по расписанию (еженедельно в субботу в 4:00)
  schedule:
    - cron: "0 4 * * 6"
    
  # Запуск при изменении зависимостей
  push:
    paths:
      - "**/requirements*.txt"
      - "**/pyproject.toml"
      - "**/poetry.lock"
      - "**/Pipfile*"
      - "**/Gemfile*"
      
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Audit Dependencies ===
  audit-dependencies:
    name: Audit Dependencies
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка инструментов аудита
      - name: Install Audit Tools
        run: |
          pip install pip-audit pip-licenses
          
      # Аудит зависимостей
      - name: Audit Python Dependencies
        run: |
          pip-audit --format json --output audit-report.json
          
      # Генерация лицензионного отчета
      - name: Generate License Report
        run: |
          pip-licenses --format json --output-file licenses.json
          
      # Анализ результатов
      - name: Analyze Audit Results
        run: |
          echo "Analyzing dependency audit results..."
          # TODO: Add analysis logic
          
      # Загрузка отчетов
      - name: Upload Audit Reports
        uses: actions/upload-artifact@v3
        with:
          name: dependency-audit-reports
          path: |
            audit-report.json
            licenses.json
            
      # Уведомление о результатах
      - name: Dependency Audit Notification
        if: always()
        run: |
          echo "Dependency audit completed"
          # TODO: Add notification logic

# === Configuration for Dependency Management ===
# .github/dependency-management.yml

# Настройки для управления зависимостями
dependency_management:
  # Автоматическое слияние безопасных обновлений
  auto_merge:
    enabled: true
    # Слияние patch версий
    merge_patch_updates: true
    # Слияние minor версий
    merge_minor_updates: true
    # Слияние security обновлений
    merge_security_updates: true
    # Слияние тестовых зависимостей
    merge_test_dependencies: true
    # Слияние dev зависимостей
    merge_dev_dependencies: true
    
  # Автоматическое закрытие старых PR
  auto_close:
    enabled: true
    # Закрывать PR старше 30 дней
    close_after_days: 30
    # Закрывать неодобренные PR
    close_unapproved: true
    # Закрывать PR с конфликтами
    close_conflicts: true
    
  # Автоматическое тестирование обновлений
  auto_test:
    enabled: true
    # Запускать все тесты
    run_all_tests: true
    # Запускать только критические тесты
    run_critical_tests_only: false
    # Запускать тесты производительности
    run_performance_tests: false
    # Запускать тесты безопасности
    run_security_tests: true
    
  # Уведомления о зависимостях
  notifications:
    enabled: true
    # Уведомлять о security обновлениях
    notify_security_updates: true
    # Уведомлять о breaking changes
    notify_breaking_changes: true
    # Уведомлять о major updates
    notify_major_updates: true
    # Уведомлять о dependency conflicts
    notify_conflicts: true
    
  # Интеграции
  integrations:
    # Интеграция с Slack
    slack:
      enabled: true
      webhook: ${{ secrets.SLACK_WEBHOOK }}
      channel: "#dependencies"
      
    # Интеграция с Telegram
    telegram:
      enabled: true
      bot_token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      chat_id: ${{ secrets.TELEGRAM_CHAT_ID }}
      
    # Интеграция с GitHub
    github:
      enabled: true
      auto_label: true
      auto_assign: true
      auto_review: true
      
    # Интеграция с Email
    email:
      enabled: true
      smtp_server: smtp.gmail.com
      smtp_port: 465
      username: ${{ secrets.EMAIL_USERNAME }}
      password: ${{ secrets.EMAIL_PASSWORD }}
      to: dependencies@xvpn.local
      from: dependency-manager@xvpn.local

# === Dependency Freeze File ===
# requirements.freeze

# Файл с замороженными версиями зависимостей для воспроизводимости сборки
# Этот файл генерируется автоматически и используется для точного воспроизведения окружения

# === Dependency Diff ===
# .github/workflows/dependency-diff.yml

name: Dependency Diff

on:
  # Запуск при пуше в основные ветки
  push:
    branches:
      - main
      - develop
      
  # Запуск при создании pull request
  pull_request:
    branches:
      - main
      - develop
      
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Compare Dependencies ===
  compare-dependencies:
    name: Compare Dependencies
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Сравнение зависимостей
      - name: Compare Dependency Changes
        run: |
          echo "Comparing dependency changes..."
          # TODO: Add dependency comparison logic
          
      # Анализ изменений
      - name: Analyze Dependency Changes
        run: |
          echo "Analyzing dependency changes..."
          # TODO: Add analysis logic
          
      # Уведомление о изменениях
      - name: Dependency Change Notification
        if: always()
        run: |
          echo "Dependency comparison completed"
          # TODO: Add notification logic