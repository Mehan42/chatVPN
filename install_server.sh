#!/bin/bash
# XVPN Server Installation Script

set -e  # Выход при ошибке

echo "🚀 Установка XVPN серверной части"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Создание виртуального окружения для избежания проблем с PEP 668
setup_virtual_environment() {
    echo "🔧 Создание виртуального окружения для избежания PEP 668..."
    
    # Установка виртуального окружения
    python3 -m venv /opt/xvpn/venv
    source /opt/xvpn/venv/bin/activate
    
    # Установка pip в виртуальном окружении
    pip install --upgrade pip
    
    echo "✅ Виртуальное окружение создано"
    return 0
}

# Функция установки uv и создание системного symlink
install_uv_system_wide() {
    echo "📦 Установка uv (менеджер пакетов)..."
    
    # Установка uv в локальную директорию, затем создание системного symlink
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Обновляем PATH для использования uv в текущей сессии
        export PATH="$HOME/.local/bin:$PATH"
        
        # Создаем системный symlink для доступности другим пользователям
        if command -v sudo &> /dev/null; then
            sudo ln -sf "$HOME/.local/bin/uv" /usr/local/bin/uv 2>/dev/null || true
        fi
        echo "✅ uv установлен и доступен системно"
        return 0
    else
        echo "❌ curl не найден, невозможно установить uv"
        return 1
    fi
}

# Функция установки зависимостей с резервными вариантами
install_dependencies() {
    echo "📦 Установка зависимостей для сервера..."
    
    # Обработка PEP 668 - сначала пробуем в виртуальном окружении
    if [ -d "/opt/xvpn/venv" ]; then
        echo "✅ Использование существующего виртуального окружения"
        source /opt/xvpn/venv/bin/activate
    else
        echo "⚠️ Виртуальное окружение не найдено, создание..."
        setup_virtual_environment
        source /opt/xvpn/venv/bin/activate
    fi
    
    # Проверяем, установлен ли uv в системе
    if command -v uv &> /dev/null; then
        echo "✅ Найден uv, установка зависимостей через uv..."
        # Используем uv в виртуальном окружении
        uv pip install -r requirements_server.txt
        return 0
    else
        echo "⚠️ uv не найден, пробуем установить..."
        if install_uv_system_wide; then
            if command -v uv &> /dev/null; then
                echo "✅ Найден uv, установка зависимостей через uv..."
                uv pip install -r requirements_server.txt
                return 0
            else
                echo "⚠️ uv не доступен после установки, используем pip из виртуального окружения..."
            fi
        else
            echo "⚠️ Не удалось установить uv, используем pip из виртуального окружения..."
        fi
    fi
    
    # Установка через pip в виртуальном окружении
    echo "✅ Установка зависимостей через pip в виртуальном окружении..."
    pip install -r requirements_server.txt
    return 0
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

# Настройка Nginx для маршрутизации (если требуется)
if command -v nginx &> /dev/null; then
    echo "🌐 Настройка Nginx для маршрутизации MCP/API..."
    sudo apt install -y nginx || true
    
    # Создание конфигурации Nginx
    sudo tee /etc/nginx/sites-available/xvpn > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /opt/xvpn/tls/cert.pem;
    ssl_certificate_key /opt/xvpn/tls/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Все пути кроме внутренних API перенаправляем на XRay (VPN)
    location / {
        proxy_pass http://127.0.0.1:443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Внутренние API пути перенаправляем на MCP (порт 8443)
    location ~ ^/(mcp|api|admin) {
        proxy_pass https://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_verify off;
    }
}
EOF

    # Включение сайта
    sudo ln -sf /etc/nginx/sites-available/xvpn /etc/nginx/sites-enabled/
    sudo systemctl restart nginx 2>/dev/null || echo "⚠️  Nginx не запущен, запустите вручную: sudo systemctl start nginx"
fi

echo "✅ Установка серверной части XVPN завершена!"
echo ""
echo "📋 Для запуска компонентов используйте:"
echo "   API: sudo systemctl start xvpn-api (порт 8443)"
echo "   Agent: sudo systemctl start xvpn-agent"
echo "   Orchestrator: sudo systemctl start xvpn-orchestrator"
echo ""
echo "ℹ️  XRay работает на порту 443 (VPN)"
echo "ℹ️  MCP/API работает на порту 8443 (управление)"
echo "ℹ️  Nginx маршрутизирует внешний трафик при необходимости"