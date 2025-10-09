#!/bin/bash
# Скрипт установки XVPN клиента с поддержкой произвольной директории установки

set -e  # Выход при ошибке

# Параметры по умолчанию
INSTALL_DIR="$HOME/xvpn_client"
REPO_URL="https://github.com/Mehan42/chatVPN.git"
BRANCH="main"

# Функция вывода справки
usage() {
    echo "Использование: $0 [опции]"
    echo "Опции:"
    echo "  -d DIR     Директория установки (по умолчанию: $HOME/xvpn_client)"
    echo "  -r URL     URL репозитория (по умолчанию: $REPO_URL)"
    echo "  -b BRANCH  Ветка репозитория (по умолчанию: $BRANCH)"
    echo "  -h         Показать эту справку"
    exit 1
}

# Парсинг аргументов
while getopts "d:r:b:h" opt; do
    case $opt in
        d) INSTALL_DIR="$OPTARG" ;;
        r) REPO_URL="$OPTARG" ;;
        b) BRANCH="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

echo "=== Установка XVPN клиента ==="
echo "Директория установки: $INSTALL_DIR"
echo "Репозиторий: $REPO_URL"
echo "Ветка: $BRANCH"
echo ""

# Проверка зависимостей
echo "Проверка зависимостей..."
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: python3 не найден"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Ошибка: git не найден"
    exit 1
fi

echo "Python3: $(python3 --version)"
echo "Git: $(git --version)"
echo ""

# Создание директории установки
echo "Создание директории установки..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Клонирование репозитория если нужно
if [ ! -d ".git" ]; then
    echo "Клонирование репозитория..."
    git clone --branch "$BRANCH" "$REPO_URL" ./
else
    echo "Репозиторий уже существует, обновляем..."
    git fetch origin
    git reset --hard "origin/$BRANCH"
fi

echo ""

# Установка Python зависимостей
echo "Установка Python зависимостей..."
if [ -f "requirements_client.txt" ]; then
    python3 -m pip install --user -r requirements_client.txt
else
    echo "Файл requirements_client.txt не найден, устанавливаем основные зависимости..."
    python3 -m pip install --user requests pystray pillow
fi

echo ""

# Копирование конфигурации watcher'а
if [ -f "$HOME/chatvpn/deployment_config.json" ]; then
    echo "Копирование конфигурации watcher'а..."
    cp "$HOME/chatvpn/deployment_config.json" ./
    cp "$HOME/chatvpn/advanced_deployment_watcher.py" ./
    echo "Для запуска watcher'а используйте: python3 advanced_deployment_watcher.py --config deployment_config.json"
fi

echo ""

# Создание systemd сервиса (опционально)
echo "Создание systemd сервиса (для автозапуска)..."
mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/xvpn-client.service" << EOF
[Unit]
Description=XVPN Client Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $(realpath .)/client/state_machine.py
Restart=always
RestartSec=10
WorkingDirectory=$(realpath .)/client
Environment=PYTHONPATH=$(realpath .)/client
StandardOutput=append:$(realpath .)/client/logs/client_stdout.log
StandardError=append:$(realpath .)/client/logs/client_stderr.log

[Install]
WantedBy=default.target
EOF

echo "Сервис systemd создан: $HOME/.config/systemd/user/xvpn-client.service"
echo ""

# Запуск systemd daemon-reload
systemctl --user daemon-reload

echo "=== Установка завершена ==="
echo "Клиент установлен в: $INSTALL_DIR"
echo ""
echo "Для запуска GUI: cd $INSTALL_DIR && python3 client/chatvpn_gui.py"
echo "Для запуска автостарт сервиса: systemctl --user enable --now xvpn-client.service"
echo "Для проверки статуса сервиса: systemctl --user status xvpn-client.service"
echo ""
echo "Для запуска watcher'а (если скопирован):"
echo "  cd $INSTALL_DIR"
echo "  python3 advanced_deployment_watcher.py --config deployment_config.json"