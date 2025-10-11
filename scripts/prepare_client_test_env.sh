#!/bin/bash
# Скрипт подготовки тестовой среды клиента XVPN

set -e

echo "🔧 Подготовка тестовой среды клиента XVPN..."
echo "Исходная директория: /home/uss/chatvpn"
echo "Целевая директория: /home/uss/xvpn_client"
echo ""

# Проверка наличия необходимых директорий
if [ ! -d "/home/uss/chatvpn" ]; then
    echo "❌ Ошибка: Директория /home/uss/chatvpn не найдена"
    exit 1
fi

if [ ! -d "/home/uss/xvpn_client" ]; then
    echo "❌ Ошибка: Директория /home/uss/xvpn_client не найдена"
    exit 1
fi

echo "✅ Обе директории существуют"

# Проверка наличия необходимых файлов в исходной директории
required_files=(
    "client/chatvpn_gui.py"
    "client/chatvpn_backend.py"
    "client/state_machine.py"
    "client/health.py"
    "client/discover.py"
    "client/transport_manager.py"
    "client/vpn_client.py"
)

echo "🔍 Проверка наличия необходимых файлов..."
for file in "${required_files[@]}"; do
    if [ ! -f "/home/uss/chatvpn/$file" ]; then
        echo "❌ Ошибка: Файл $file не найден"
        exit 1
    fi
    echo "✅ $file"
done

echo ""
echo "📋 Структура клиентской директории:"
ls -la /home/uss/xvpn_client/ | head -10

echo ""
echo "🔧 Копирование обновленных файлов из разработки..."
cd /home/uss/chatvpn && ./copy_updated_client.sh

echo ""
echo "✅ Тестовая среда готова!"
echo "Теперь можно запускать клиент из /home/uss/xvpn_client"