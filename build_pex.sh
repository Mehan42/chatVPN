#!/bin/bash
# XVPN PEX Build Script
# Создание автономных исполняемых файлов Python для XVPN

set -e  # Выход при ошибке

echo "🚀 Создание PEX-билдов для XVPN"

# Проверка наличия pip и pex
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Установка pex если не установлен
if ! python3 -c "import pex" &> /dev/null; then
    echo "📦 Установка pex..."
    pip3 install pex
fi

# Создание директории для билдов
BUILD_DIR="dist/pex"
mkdir -p "$BUILD_DIR"

# Функция для создания PEX для серверных компонентов
build_server_pex() {
    echo "🔨 Создание PEX для серверных компонентов..."

    # API сервер
    echo "  📡 Создание API сервера..."
    python3 -m pex \
        -r requirements_server.txt \
        -e "server.api.app:main" \
        -o "$BUILD_DIR/xvpn-api.pex" \
        --python-shebang='/usr/bin/env python3'

    # Агент
    echo "  🤖 Создание агента..."
    python3 -m pex \
        -r requirements_server.txt \
        -e "server.agent.agent:main" \
        -o "$BUILD_DIR/xvpn-agent.pex" \
        --python-shebang='/usr/bin/env python3'

    # Бот
    echo "  🤖 Создание Telegram бота..."
    python3 -m pex \
        -r requirements_server.txt \
        -e "server.admin.tg_bot:main" \
        -o "$BUILD_DIR/xvpn-bot.pex" \
        --python-shebang='/usr/bin/env python3'

    # Воркер
    echo "  ⚙️ Создание воркера..."
    python3 -m pex \
        -r requirements_server.txt \
        -e "server.worker.worker:main" \
        -o "$BUILD_DIR/xvpn-worker.pex" \
        --python-shebang='/usr/bin/env python3'

    # Оркестратор
    echo "  🎯 Создание оркестратора..."
    python3 -m pex \
        -r requirements_server.txt \
        -e "server.agent.orchestrator:main" \
        -o "$BUILD_DIR/xvpn-orchestrator.pex" \
        --python-shebang='/usr/bin/env python3'

    echo "✅ PEX-файлы сервера созданы в $BUILD_DIR/"
}

# Функция для создания PEX для клиентских компонентов
build_client_pex() {
    echo "🔨 Создание PEX для клиентских компонентов..."

    # Клиент
    echo "  💻 Создание VPN клиента..."
    python3 -m pex \
        -r requirements_client.txt \
        -e "client.vpn_client:main" \
        -o "$BUILD_DIR/xvpn-client.pex" \
        --python-shebang='/usr/bin/env python3'

    # GUI (если требуется)
    echo "  🖥️ Создание GUI клиента..."
    python3 -m pex \
        -r requirements_client.txt \
        -e "client.chatvpn_gui:main" \
        -o "$BUILD_DIR/xvpn-gui.pex" \
        --python-shebang='/usr/bin/env python3'

    echo "✅ PEX-файлы клиента созданы в $BUILD_DIR/"
}

# Обработка аргументов
case "${1:-all}" in
    server)
        build_server_pex
        ;;
    client)
        build_client_pex
        ;;
    all)
        build_server_pex
        build_client_pex
        ;;
    *)
        echo "Использование: $0 [server|client|all]"
        echo "  server - создать PEX для серверных компонентов"
        echo "  client - создать PEX для клиентских компонентов"
        echo "  all    - создать PEX для всех компонентов (по умолчанию)"
        exit 1
        ;;
esac

echo ""
echo "🎉 PEX-билды успешно созданы!"
echo "📍 Файлы находятся в: $BUILD_DIR/"
echo ""
echo "📋 Для запуска используйте:"
echo "   chmod +x $BUILD_DIR/xvpn-*.pex"
echo "   ./$BUILD_DIR/xvpn-api.pex"
echo "   ./$BUILD_DIR/xvpn-agent.pex"
echo "   ./$BUILD_DIR/xvpn-client.pex"