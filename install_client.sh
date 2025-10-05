#!/bin/bash
# XVPN Client Installation Script

set -e  # Выход при ошибке

echo "🚀 Установка XVPN клиентской части"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Функция установки зависимостей с резервными вариантами
install_dependencies() {
    echo "📦 Установка зависимостей для клиента..."
    
    # Попытка 1: Использовать uv если доступен
    if command -v uv &> /dev/null; then
        echo "✅ Найден uv, установка зависимостей через uv..."
        uv pip install -r requirements_client.txt
        return 0
    else
        echo "⚠️ uv не найден, проверяем pip..."
    fi
    
    # Попытка 2: Использовать pip3
    if command -v pip3 &> /dev/null; then
        echo "✅ Найден pip3, установка зависимостей через pip3..."
        pip3 install -r requirements_client.txt
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
echo "📁 Создание клиентских директорий..."
mkdir -p ~/chatvpn/client
mkdir -p ~/chatvpn/client/logs
mkdir -p ~/chatvpn/client/states
mkdir -p ~/chatvpn/client/transports

# Установка XRay (если требуется)
echo "🌐 Проверка установки XRay..."
if ! command -v xray &> /dev/null; then
    echo "XRay не найден, установка..."
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
fi

# Проверка GUI зависимостей (для Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🖥️ Установка GUI зависимостей для Linux..."
    # Установка системных зависимостей для GUI
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-tk python3-dev libxss-dev libxtst-dev
    elif command -v yum &> /dev/null; then
        sudo yum install -y tkinter python3-devel libXss-devel libXtst-devel
    fi
fi

echo "✅ Установка клиентской части XVPN завершена!"
echo ""
echo "📋 Клиент готов к использованию. Для запуска используйте:"
echo "   python3 client/vpn_client.py start"
echo ""
echo "🔧 Для настройки подключения отредактируйте ~/chatvpn/client/client.json"