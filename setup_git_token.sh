#!/bin/bash

echo "🔐 Настройка Git для работы с Personal Access Token"
echo "=================================================="
echo ""
echo "⚠️  ВНИМАНИЕ: Этот скрипт сохранит ваш токен в Git credential helper"
echo "Это безопасно только на вашем личном компьютере!"
echo ""

# Включаем credential helper для сохранения токена
git config --global credential.helper store

echo "✅ Git credential helper включен"
echo ""
echo "Теперь выполните:"
echo "1. git push -u origin main"
echo "2. Введите ваши данные:"
echo "   Username: Avtandil42"
echo "   Password: [ваш Personal Access Token]"
echo ""
echo "После этого Git запомнит токен и больше не будет спрашивать!"
echo ""
echo "💡 Чтобы проверить сохранение, посмотрите файл:"
echo "   ~/.git-credentials (будет создан после первого push)"
