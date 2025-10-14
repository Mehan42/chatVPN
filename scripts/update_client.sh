#!/bin/bash

# Скрипт обновления клиентской части XVPN
# Используется на локальном ПК в /home/uss/xvpn_client

set -e  # Остановить выполнение при ошибке

echo "=== Обновление клиентской части XVPN ==="

# Переменные
REPO_URL="https://github.com/Mehan42/chatVPN.git"
CLIENT_DIR="/home/uss/xvpn_client"
BRANCH="тест"
CLIENT_BINARY="xvpn-client"
GUI_BINARY="xvpn-client-gui"

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo "Ошибка: Git не установлен"
    exit 1
fi

# Проверка наличия Go
if ! command -v go &> /dev/null; then
    echo "Ошибка: Go не установлен"
    exit 1
fi

# Проверка наличия директории клиента
if [ ! -d "$CLIENT_DIR" ]; then
    echo "Создание директории: $CLIENT_DIR"
    sudo mkdir -p "$CLIENT_DIR"
    sudo chown $USER:$USER "$CLIENT_DIR"
fi

# Клонирование или обновление репозитория
cd "$CLIENT_DIR"
if [ ! -d ".git" ]; then
    echo "Клонирование репозитория..."
    git clone "$REPO_URL" .
else
    echo "Обновление репозитория..."
    git fetch origin
fi

# Переключение на нужную ветку
echo "Переключение на ветку: $BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

# Сборка Go-клиента
echo "Сборка Go-клиента..."
cd xvpn-client-go
go mod tidy
go build -o "$CLIENT_BINARY" ./cmd/xvpn-client
go build -o "$GUI_BINARY" ./cmd/xvpn-gui

# Проверка успешности сборки
if [ ! -f "$CLIENT_BINARY" ] || [ ! -f "$GUI_BINARY" ]; then
    echo "Ошибка: Сборка клиента завершилась с ошибкой"
    exit 1
fi

# Установка прав выполнения
chmod +x "$CLIENT_BINARY"
chmod +x "$GUI_BINARY"

# Копирование бинарных файлов в основную директорию
cp "$CLIENT_BINARY" ../
cp "$GUI_BINARY" ../

# Проверка версий
echo "Проверка версий:"
echo "Клиент: $(./$CLIENT_BINARY --version 2>/dev/null || echo 'Версия не определена')"
echo "GUI: $(./$GUI_BINARY --version 2>/dev/null || echo 'Версия не определена')"

# Очистка старых бинарных файлов
if [ -f "xvpn-client" ]; then
    rm xvpn-client
fi
if [ -f "xvpn-client-gui" ]; then
    rm xvpn-client-gui
fi

cd ..

echo "=== Обновление клиентской части завершено успешно ==="
echo ""
echo "Для запуска клиента:"
echo "  CLI: ./$CLIENT_BINARY"
echo "  GUI: ./$GUI_BINARY"