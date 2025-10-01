#!/bin/bash

# Скрипт для отправки кода в GitHub репозиторий

echo "🚀 Готовлю отправку кода в GitHub репозиторий..."
echo "📋 Требуется предварительно создать репозиторий на GitHub:"
echo "   https://github.com/Avtandil42/chatVPN"
echo ""

# Проверка состояния
echo "🔍 Текущее состояние Git репозитория:"
git status
echo ""

echo "🔍 Настройки remote origin:"
git remote -v
echo ""

echo "🔍 Последние коммиты:"
git log --oneline -3
echo ""

echo "📦 Если репозиторий уже создан на GitHub, выполните:"
echo "   git push -u origin main"
echo ""

echo "📝 Если возникает ошибка 404, сначала создайте репозиторий на GitHub:"
echo "   1. Зайдите: https://github.com/Avtandil42/chatVPN"
echo "   2. Нажмите 'New'"
echo "   3. Заполните: Repository name = 'chatVPN', Public, Add README"
echo "   4. Нажмите 'Create repository'"
echo "   5. Затем выполните: git push -u origin main"
echo ""

echo "✅ Все готово к отправке в GitHub!"