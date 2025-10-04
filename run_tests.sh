#!/bin/bash

# XVPN Test Runner
# Запуск всех тестов системы

set -e

echo "🧪 XVPN Test Runner"
echo "==================="

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Пожалуйста, запустите скрипт из корневой директории проекта"
    exit 1
fi

# Установка переменных окружения
export PYTHONPATH="."
export XVPN_TEST_MODE=1

echo "🔍 Запуск тестов компонентов..."
python3 test_components.py

echo ""
echo "🔍 Запуск unit тестов..."
if [ -d "tests" ] && [ -f "tests/test_*.py" ]; then
    python3 -m pytest tests/ -v
else
    echo "⚠️  Unit тесты не найдены"
fi

echo ""
echo "🔍 Проверка синтаксиса Python..."
find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | xargs python3 -m py_compile

echo ""
echo "✅ Все тесты завершены!"