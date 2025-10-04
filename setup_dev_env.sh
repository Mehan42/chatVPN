#!/bin/bash

# XVPN Development Environment Setup Script
# Автоматическая настройка окружения для разработки

set -e  # Выход при любой ошибке

echo "🚀 Setting up XVPN Development Environment..."
echo "==========================================="

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Обновление системы
echo "🔄 Updating system packages..."
sudo apt update

# Установка системных зависимостей
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3 python3-pip python3-venv \
    curl wget git \
    docker.io docker-compose \
    jq

# Установка uv (современный Python пакетный менеджер)
echo "🔧 Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Создание виртуального окружения
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -e ".[dev,server,agent,bot,monitoring,test]"

# Установка дополнительных инструментов разработки
echo "🛠️ Installing development tools..."
pip install black isort flake8 mypy pre-commit bandit safety

# Настройка pre-commit хуков
echo "🔗 Setting up pre-commit hooks..."
pre-commit install

# Создание директорий для разработки
echo "📁 Creating development directories..."
mkdir -p logs data/clients data/transports db

# Настройка прав доступа
chmod -R 755 logs data db

# Создание файла .env для разработки
echo "📝 Creating development .env file..."
cat > .env << EOF
# XVPN Development Environment Variables

# Telegram Bot Configuration (replace with your own)
BOT_TOKEN=your_development_bot_token_here
CHAT_ID=your_development_chat_id_here

# Server Configuration
SERVER_IP=localhost
API_BASE_URL=https://localhost:8443
DATABASE_URL=sqlite:///db/xvpn.db
REDIS_URL=redis://localhost:6379/0

# Security Configuration
JWT_SECRET=your_development_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FILE=logs/development.log

# Development Configuration
FLASK_ENV=development
FLASK_DEBUG=true
PYTHONUNBUFFERED=1

# Feature Flags
FEATURE_AI_ORCHESTRATOR=true
FEATURE_IPV6_SUPPORT=true
FEATURE_PROXY_MODES=true
FEATURE_HEALTH_MONITORING=true

# Performance Configuration
WORKER_COUNT=2
HEALTH_CHECK_INTERVAL=30
TRANSPORT_SWITCH_THRESHOLD=3
EOF

# Создание примера конфигурации клиента
echo "📝 Creating example client configuration..."
cat > example_client_config.json << EOF
{
  "uuid": "example-client-uuid",
  "created_at": "$(date -Iseconds)",
  "expires_at": "$(date -Iseconds -d '+1 year')",
  "name": "Example Client",
  "description": "Example client configuration for development",
  "transports": [
    {
      "id": "vless-reality-dev",
      "name": "VLESS + Reality (Development)",
      "type": "vless-reality",
      "priority": 1,
      "ipv6": true,
      "need_udp": false,
      "config": {
        "server": "localhost",
        "port": 443,
        "protocol": "tcp"
      }
    }
  ],
  "settings": {
    "auto_connect": true,
    "auto_transport_switch": true,
    "transport_switch_threshold": 3,
    "health_check_interval": 30,
    "proxy_mode": "tun",
    "ipv6_enabled": true,
    "kill_switch": true,
    "dns_leak_protection": true,
    "log_level": "DEBUG"
  }
}
EOF

# Запуск тестов для проверки установки
echo "🧪 Running initial tests..."
python -m pytest tests/ -v --tb=short || echo "⚠️ Some tests failed, but continuing setup..."

# Вывод информации о завершении
echo ""
echo "✅ Development environment setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Update .env with your actual values"
echo "3. Run development server: make server"
echo "4. Run tests: make test"
echo "5. Format code: make format"
echo "6. Check code quality: make lint"
echo ""
echo "🐳 Docker development:"
echo "1. Build images: make docker-build"
echo "2. Run services: make docker-run"
echo ""
echo " Happy coding! 🚀"