#!/bin/bash

# Скрипт обновления серверной части XVPN
# Используется на удаленном сервере

set -e  # Остановить выполнение при ошибке

echo "=== Обновление серверной части XVPN ==="

# Переменные
REPO_URL="https://github.com/Mehan42/chatVPN.git"
REPO_DIR="/opt/xvpn/server"
BRANCH="тест"
DOCKER_COMPOSE_FILE="docker-compose.go.yml"

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo "Ошибка: Git не установлен"
    exit 1
fi

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "Ошибка: Docker не установлен"
    exit 1
fi

# Создание директории если не существует
if [ ! -d "$REPO_DIR" ]; then
    echo "Создание директории: $REPO_DIR"
    sudo mkdir -p "$REPO_DIR"
    sudo chown $USER:$USER "$REPO_DIR"
fi

# Клонирование или обновление репозитория
cd "$REPO_DIR"
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

# Проверка наличия docker-compose файла
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Ошибка: Файл $DOCKER_COMPOSE_FILE не найден"
    exit 1
fi

# Остановка старых контейнеров
echo "Остановка старых контейнеров..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down

# Сборка и запуск новых контейнеров
echo "Сборка и запуск новых контейнеров..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

# Проверка статуса контейнеров
echo "Проверка статуса контейнеров..."
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Проверка логов
echo "Последние логи сервера..."
docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=20 xvpn-go-server

# Проверка здоровья сервера
echo "Проверка здоровья сервера..."
sleep 10
if curl -k -f https://localhost:8443/health > /dev/null 2>&1; then
    echo "✅ Сервер успешно запущен и работает"
else
    echo "❌ Ошибка: Сервер не отвечает на проверку здоровья"
    exit 1
fi

echo "=== Обновление серверной части завершено успешно ==="