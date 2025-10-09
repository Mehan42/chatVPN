#!/bin/bash
# Скрипт для копирования обновленных файлов из директории разработки в установленного клиента

set -e

SOURCE_DIR="/home/uss/chatvpn/client"
TARGET_DIR="/home/uss/xvpn_client"

echo "=== Копирование обновленных файлов клиента ==="
echo "Исходная директория: $SOURCE_DIR"
echo "Целевая директория: $TARGET_DIR"
echo ""

# Проверка существования директорий
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Ошибка: Исходная директория $SOURCE_DIR не существует"
    exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo "Ошибка: Целевая директория $TARGET_DIR не существует"
    exit 1
fi

echo "Копирование Python файлов..."
rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/" --include="*.py" --exclude="*" --delete

echo ""
echo "Копирование других файлов (конфиги, иконки и т.д.)..."
rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/" \
    --include="*.json" \
    --include="*.png" \
    --include="*.conf" \
    --include="*.sh" \
    --exclude="*.py" \
    --exclude="*.pyc" \
    --exclude="__pycache__/" \
    --exclude="*.log" \
    --exclude="logs/" \
    --exclude="states/" \
    --exclude="clients/" \
    --exclude="profiles/"

echo ""
echo "Обновление прав доступа..."
chmod +x "$TARGET_DIR"/*.sh 2>/dev/null || true

echo ""
echo "=== Копирование завершено ==="
echo "Обновленные файлы скопированы в $TARGET_DIR"
echo ""
echo "Для тестирования клиента выполните:"
echo "  cd $TARGET_DIR"
echo "  python3 chatvpn_gui.py"