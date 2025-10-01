#!/bin/bash

# Скрипт для создания репозитория XVPN на GitHub и настройки локального репозитория

REPO_NAME="xvpn-project"
REPO_URL="https://github.com/Avtandil42/$REPO_NAME.git"

echo "🚀 Начинаю создание репозитория $REPO_NAME на GitHub..."

# Проверка, установлен ли GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI не установлен. Установка была выполнена ранее, но проверьте:"
    echo "   gh --version"
    exit 1
fi

# Аутентификация в GitHub
echo "🔐 Проверка аутентификации в GitHub..."
gh auth status

# Создание репозитория на GitHub
echo "📦 Создание репозитория $REPO_NAME на GitHub..."
gh repo create $REPO_NAME --public --description "XVPN - Intelligent VPN with AI Agents. Complete VPN system with intelligent agents for automatic transport management, monitoring and self-healing."

if [ $? -eq 0 ]; then
    echo "✅ Репозиторий успешно создан на GitHub!"
    echo "🔗 URL репозитория: $REPO_URL"
else
    echo "❌ Не удалось создать репозиторий. Проверьте права доступа и наличие GitHub CLI."
    exit 1
fi

# Настройка remote origin
echo "🔗 Настройка remote origin..."
git remote set-url origin $REPO_URL

# Проверка состояния
echo "🔍 Проверка состояния Git репозитория..."
git status
echo "🔍 Проверка remote origin..."
git remote -v

echo "🎉 Настройка завершена!"
echo ""
echo "📤 Следующий шаг: git push -u origin main"