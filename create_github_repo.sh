#!/bin/bash

# Скрипт для создания репозитория на GitHub и настройки локального репозитория

REPO_URL="https://github.com/Avtandil42/chatVPN.git"
REPO_NAME="chatVPN"

echo "🚀 Начинаю создание репозитория $REPO_NAME на GitHub..."

# Проверка, установлен ли GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI не установлен. Установите его:"
    echo "   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "   echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "   sudo apt update"
    echo "   sudo apt install gh"
    exit 1
fi

# Аутентификация в GitHub
echo "🔐 Аутентификация в GitHub..."
gh auth status

# Создание репозитория на GitHub
echo "📦 Создание репозитория $REPO_NAME на GitHub..."
gh repo create $REPO_NAME --public --source=. --remote=origin --push

if [ $? -eq 0 ]; then
    echo "✅ Репозиторий успешно создан и настроен!"
    echo "🔗 URL репозитория: $REPO_URL"
else
    echo "❌ Не удалось создать репозиторий. Проверьте права доступа и наличие GitHub CLI."
    exit 1
fi

# Проверка состояния
echo "🔍 Проверка состояния Git репозитория..."
git status
echo "🔍 Проверка remote origin..."
git remote -v

echo "🎉 Настройка завершена!"