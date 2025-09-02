#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["python-telegram-bot==13.15", "requests"]
# ///

"""
XVPN Telegram Bot Agent
Telegram-бот для управления клиентами, выдачи конфигураций и получения отчетов
"""

import os
import logging
import json
import time
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
API_BASE_URL = "https://127.0.0.1:8443"

# Состояния для ConversationHandler
WAITING_UUID = 1

class XVPNTelegramBot:
    """Главный класс Telegram бота"""
    
    def __init__(self):
        if not BOT_TOKEN or not CHAT_ID:
            raise ValueError("BOT_TOKEN and CHAT_ID must be set in environment")
        
        self.allowed_chat_id = CHAT_ID
        self.updater = Updater(BOT_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        
        # Регистрация обработчиков команд
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        
        # Основные команды
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help_command))
        self.dp.add_handler(CommandHandler("status", self.status))
        self.dp.add_handler(CommandHandler("newclient", self.new_client))
        
        # Команды с параметрами
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("rotate", self.rotate_start),
                CommandHandler("report", self.report_start)
            ],
            states={
                WAITING_UUID: [MessageHandler(Filters.text & ~Filters.command, self.handle_uuid)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        self.dp.add_handler(conv_handler)
        
        # Обработка ошибок
        self.dp.add_error_handler(self.error_handler)
    
    def _check_auth(self, update) -> bool:
        """Проверка авторизации пользователя"""
        chat_id = str(update.effective_chat.id)
        if chat_id != self.allowed_chat_id:
            update.message.reply_text("❌ Доступ запрещен")
            logger.warning(f"Unauthorized access attempt from chat_id: {chat_id}")
            return False
        return True
    
    def _api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Выполнение запроса к API"""
        url = f"{API_BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, verify=False, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, verify=False, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start(self, update, context):
        """Обработчик команды /start"""
        if not self._check_auth(update):
            return
        
        welcome_text = """
🚀 **XVPN Control Bot**

Доступные команды:
• `/help` - Показать это сообщение
• `/status` - Статус системы 
• `/newclient` - Создать нового клиента
• `/rotate` - Ротировать ключи клиента
• `/report` - Получить отчет по клиенту

Для команд с UUID используйте интерактивный режим.
        """
        
        update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    def help_command(self, update, context):
        """Обработчик команды /help"""
        if not self._check_auth(update):
            return
        
        help_text = """
📖 **Справка по командам**

**Основные команды:**
• `/status` - Показать статус VPN сервера и агентов
• `/newclient` - Создать нового клиента и получить UUID+конфиг

**Управление клиентами:**
• `/rotate` - Ротировать ключи существующего клиента
• `/report` - Получить детальный отчет по клиенту

**Система:**
• `/cancel` - Отменить текущую операцию

**Примеры:**
1. Создание клиента: `/newclient`
2. Ротация ключей: `/rotate` → введите UUID
3. Отчет: `/report` → введите UUID
        """
        
        update.message.reply_text(help_text, parse_mode='Markdown')
    
    def status(self, update, context):
        """Обработчик команды /status"""
        if not self._check_auth(update):
            return
        
        # Получение статуса здоровья
        health_result = self._api_request("/mcp/v1/vpn.health")
        
        if health_result["success"]:
            health_data = health_result["data"]
            mask_score = health_data.get("mask_score", 0)
            status = health_data.get("status", "UNKNOWN")
            transports = health_data.get("transports_status", {})
            
            status_icon = "🟢" if status == "OK" else "🟡" if status == "WARNING" else "🔴"
            
            status_text = f"""
{status_icon} **Статус системы: {status}**

🎭 **Mask Score:** {mask_score}/5
📡 **Транспорты:**
"""
            
            for transport_id, transport_status in transports.items():
                icon = "🟢" if transport_status == "active" else "🟡"
                status_text += f"  • {transport_id}: {icon} {transport_status}\n"
            
            status_text += f"\n🕐 **Обновлено:** {time.strftime('%H:%M:%S')}"
        else:
            status_text = f"❌ **Ошибка получения статуса:** {health_result['error']}"
        
        update.message.reply_text(status_text, parse_mode='Markdown')
    
    def new_client(self, update, context):
        """Обработчик команды /newclient"""
        if not self._check_auth(update):
            return
        
        update.message.reply_text("🔄 Создаю нового клиента...")
        
        # Создание нового клиента через API
        result = self._api_request("/mcp/v1/admin.newclient", method="POST")
        
        if result["success"]:
            client_data = result["data"]
            uuid = client_data["uuid"]
            download_url = client_data["download_url"]
            
            # Получение конфигурации клиента
            config_result = self._api_request(download_url)
            
            if config_result["success"]:
                config_json = json.dumps(config_result["data"], indent=2)
                
                response_text = f"""
✅ **Клиент создан успешно!**

🆔 **UUID:** `{uuid}`
📥 **Статус:** Активен

**Конфигурация клиента:**
```json
{config_json}
```

💡 **Инструкции:**
1. Сохраните этот JSON как `{uuid}.json`
2. Поместите файл в `~/chatvpn/client/clients/`
3. Запустите клиент на локальном ПК
                """
                
                update.message.reply_text(response_text, parse_mode='Markdown')
            else:
                update.message.reply_text(f"❌ Ошибка получения конфигурации: {config_result['error']}")
        else:
            update.message.reply_text(f"❌ Ошибка создания клиента: {result['error']}")
    
    def rotate_start(self, update, context):
        """Начало процесса ротации ключей"""
        if not self._check_auth(update):
            return
        
        context.user_data['action'] = 'rotate'
        update.message.reply_text(
            "🔄 **Ротация ключей клиента**\n\n"
            "Пожалуйста, введите UUID клиента для ротации ключей:",
            parse_mode='Markdown'
        )
        
        return WAITING_UUID
    
    def report_start(self, update, context):
        """Начало процесса получения отчета"""
        if not self._check_auth(update):
            return
        
        context.user_data['action'] = 'report'
        update.message.reply_text(
            "📊 **Отчет по клиенту**\n\n"
            "Пожалуйста, введите UUID клиента для получения отчета:",
            parse_mode='Markdown'
        )
        
        return WAITING_UUID
    
    def handle_uuid(self, update, context):
        """Обработка введенного UUID"""
        if not self._check_auth(update):
            return ConversationHandler.END
        
        uuid = update.message.text.strip()
        action = context.user_data.get('action')
        
        # Валидация UUID (упрощенная)
        if len(uuid) < 8:
            update.message.reply_text("❌ Неверный формат UUID. Попробуйте еще раз:")
            return WAITING_UUID
        
        if action == 'rotate':
            self._handle_rotate(update, uuid)
        elif action == 'report':
            self._handle_report(update, uuid)
        
        return ConversationHandler.END
    
    def _handle_rotate(self, update, uuid: str):
        """Выполнение ротации ключей"""
        update.message.reply_text("🔄 Выполняю ротацию ключей...")
        
        result = self._api_request(f"/mcp/v1/agent.rotate/{uuid}", method="POST")
        
        if result["success"]:
            data = result["data"]
            new_uuid = data["new_uuid"]
            
            # Получение новой конфигурации
            config_result = self._api_request(f"/clients/{new_uuid}.json")
            
            if config_result["success"]:
                config_json = json.dumps(config_result["data"], indent=2)
                
                response_text = f"""
✅ **Ротация выполнена успешно!**

🔄 **Старый UUID:** `{uuid}` (деактивирован)
🆕 **Новый UUID:** `{new_uuid}`

**Новая конфигурация:**
```json
{config_json}
```

💡 **Действия:**
1. Замените старый файл `{uuid}.json` на `{new_uuid}.json`
2. Перезапустите клиент
                """
                
                update.message.reply_text(response_text, parse_mode='Markdown')
            else:
                update.message.reply_text(f"⚠️ Ротация выполнена, но ошибка получения конфига: {config_result['error']}")
        else:
            update.message.reply_text(f"❌ Ошибка ротации: {result['error']}")
    
    def _handle_report(self, update, uuid: str):
        """Получение отчета по клиенту"""
        update.message.reply_text("📊 Генерирую отчет...")
        
        result = self._api_request(f"/mcp/v1/agent.report/{uuid}")
        
        if result["success"]:
            report_data = result["data"]
            logs_count = report_data["logs_count"]
            period_hours = (report_data["period_end"] - report_data["period_start"]) // 3600
            
            report_text = f"""
📊 **Отчет по клиенту**

🆔 **UUID:** `{uuid}`
🕐 **Период:** {period_hours}ч
📝 **Записей в логе:** {logs_count}

**Последние события:**
"""
            
            # Показываем последние 5 записей
            recent_logs = report_data["logs"][:5]
            for log in recent_logs:
                timestamp = time.strftime('%H:%M:%S', time.localtime(log["timestamp"]))
                report_text += f"• {timestamp} - {log['component']}: {log['action']} → {log['result']}\n"
            
            if logs_count > 5:
                report_text += f"\n... и еще {logs_count - 5} записей"
            
            update.message.reply_text(report_text, parse_mode='Markdown')
        else:
            update.message.reply_text(f"❌ Ошибка получения отчета: {result['error']}")
    
    def cancel(self, update, context):
        """Отмена текущей операции"""
        if not self._check_auth(update):
            return ConversationHandler.END
        
        update.message.reply_text("❌ Операция отменена", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    def error_handler(self, update, context):
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.message:
            update.message.reply_text("💥 Произошла ошибка. Попробуйте позже.")
    
    def run(self):
        """Запуск бота"""
        logger.info("🤖 Starting XVPN Telegram Bot")
        logger.info(f"📱 Authorized chat_id: {self.allowed_chat_id}")
        
        # Запуск polling
        self.updater.start_polling()
        
        # Отправка уведомления о запуске
        try:
            self.updater.bot.send_message(
                chat_id=self.allowed_chat_id,
                text="🟢 **XVPN Bot запущен**\n\nВведите /start для начала работы",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
        
        # Работаем до остановки
        self.updater.idle()
        
        logger.info("🛑 XVPN Telegram Bot stopped")

if __name__ == "__main__":
    bot = XVPNTelegramBot()
    bot.run()
