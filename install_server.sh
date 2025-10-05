#!/bin/bash
# XVPN Server Installation Script

set -e  # Выход при ошибке

echo "🚀 Установка XVPN серверной части"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Функция установки зависимостей с резервными вариантами
install_dependencies() {
    echo "📦 Установка зависимостей для сервера..."
    
    # Попытка 1: Использовать uv если доступен
    if command -v uv &> /dev/null; then
        echo "✅ Найден uv, установка зависимостей через uv..."
        uv pip install -r requirements_server.txt
        return 0
    else
        echo "⚠️ uv не найден, проверяем pip..."
    fi
    
    # Попытка 2: Использовать pip3
    if command -v pip3 &> /dev/null; then
        echo "✅ Найден pip3, установка зависимостей через pip3..."
        pip3 install -r requirements_server.txt
        return 0
    else
        echo "❌ Ни uv, ни pip3 не найдены"
        exit 1
    fi
}

# Попытка установки зависимостей
if install_dependencies; then
    echo "✅ Зависимости успешно установлены"
else
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание системных директорий..."
sudo mkdir -p /opt/xvpn/data
sudo mkdir -p /var/log/xvpn
sudo mkdir -p /opt/xvpn/tls

# Установка XRay (если требуется)
echo "🌐 Проверка установки XRay..."
if ! command -v xray &> /dev/null; then
    echo "XRay не найден, установка..."
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
fi

# Установка systemd сервисов (если на Linux)
if command -v systemctl &> /dev/null; then
    echo "⚙️ Установка systemd сервисов..."
    sudo cp server/*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    echo "ℹ️  Сервисы установлены. Для запуска используйте:"
    echo "   sudo systemctl start xvpn-api"
    echo "   sudo systemctl start xvpn-agent"
    echo "   sudo systemctl start xvpn-orchestrator"
fi

echo "✅ Установка серверной части XVPN завершена!"
echo ""
echo "📋 Для запуска компонентов используйте:"
echo "   API: python3 server/api/app.py"
echo "   Agent: python3 server/agent/agent.py"
echo "   Orchestrator: python3 server/agent/orchestrator.py"