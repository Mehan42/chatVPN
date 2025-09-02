#!/bin/bash

# 📋 КОМАНДЫ ДЛЯ ПОДКЛЮЧЕНИЯ К GITHUB
# =====================================
# 
# ⚠️  ЗАМЕНИТЕ 'YOUR-USERNAME' НА ВАШ РЕАЛЬНЫЙ GITHUB USERNAME!
# 

echo "🔗 Подключение к GitHub репозиторию..."

# 1. Добавляем удаленный репозиторий (ЗАМЕНИТЕ YOUR-USERNAME!)
git remote add origin https://github.com/YOUR-USERNAME/chatvpn.git

# 2. Проверяем подключение
git remote -v

# 3. Отправляем код на GitHub
git push -u origin main

echo "✅ Проект успешно загружен на GitHub!"
echo ""
echo "🌐 Ваш репозиторий доступен по адресу:"
echo "   https://github.com/YOUR-USERNAME/chatvpn"
echo ""
echo "📋 Что делать дальше:"
echo "1. Проверьте что все файлы загружены"
echo "2. Настройте GitHub Secrets для CI/CD:"
echo "   - Settings → Secrets and variables → Actions"
echo "   - Добавьте: HOST, USERNAME, SSH_KEY, BOT_TOKEN, CHAT_ID"
echo "3. Готово! Можете использовать автоматическое развертывание"
