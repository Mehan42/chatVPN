#!/bin/bash
# XVPN Server Installation Script

set -e  # Выход при ошибке

echo "🚀 Установка XVPN серверной части"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Функция установки uv (системно)
install_uv_system_wide() {
    echo "📦 Установка uv (менеджер пакетов)..."
    
    # Установка uv в системную директорию для доступности всем пользователям
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh -s -- -p /usr/local/bin
        # Обновляем PATH для использования uv
        export PATH="$PATH:/root/.cargo/bin"
        source "$HOME/.cargo/env" 2>/dev/null || true
        echo "✅ uv установлен в /usr/local/bin"
        return 0
    else
        echo "❌ curl не найден, невозможно установить uv"
        return 1
    fi
}

# Функция установки зависимостей с резервными вариантами
install_dependencies() {
    echo "📦 Установка зависимостей для сервера..."
    
    # Проверяем, установлен ли uv системно
    if command -v /usr/local/bin/uv &> /dev/null; then
        echo "✅ Найден системный uv, установка зависимостей через uv..."
        /usr/local/bin/uv pip install -r requirements_server.txt
        return 0
    elif command -v uv &> /dev/null; then
        echo "✅ Найден uv, установка зависимостей через uv..."
        uv pip install -r requirements_server.txt
        return 0
    else
        echo "⚠️ uv не найден, устанавливаем..."
        if install_uv_system_wide; then
            # Повторная проверка после установки
            if command -v /usr/local/bin/uv &> /dev/null; then
                echo "✅ Найден системный uv, установка зависимостей через uv..."
                /usr/local/bin/uv pip install -r requirements_server.txt
                return 0
            else
                echo "⚠️ uv не доступен после установки, используем pip..."
            fi
        else
            echo "⚠️ Не удалось установить uv, используем pip..."
        fi
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