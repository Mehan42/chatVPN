#!/usr/bin/env python3
"""
XVPN Telegram Bot
Административный бот для управления системой XVPN
"""

import time
import sys
import json
import requests
import threading
from pathlib import Path
from datetime import datetime
import os
from urllib.parse import urlparse

class XVPNBot:
    """Основной класс Telegram бота XVPN"""
    
    def __init__(self):
        # Загружаем конфигурацию
        self.config = self._load_config()
        self.bot_token = self.config.get("bot_token", os.getenv("BOT_TOKEN", ""))
        self.admin_chat_id = self.config.get("admin_chat_id", os.getenv("ADMIN_CHAT_ID", ""))
        self.api_server = self.config.get("api_server", "https://api.uss.hopto.org")
        
        self.running = False
        self.log_file = Path("/var/log/xvpn/bot.log")
        self.data_dir = Path("/opt/xvpn/data")
        
        # Создаем необходимые директории
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # История команд
        self.command_history = []
    
    def _load_config(self):
        """Загрузка конфигурации бота"""
        config_file = Path("/opt/xvpn/data/bot_config.json")
        default_config = {
            "bot_token": "YOUR_BOT_TOKEN_HERE",
            "admin_chat_id": "YOUR_CHAT_ID_HERE",
            "api_server": "https://api.uss.hopto.org",
            "webhook_enabled": False,
            "polling_interval": 10,
            "log_level": "INFO"
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Обновляем с дефолтными значениями
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Error loading bot config, using defaults: {e}")
        
        # Создаем файл конфигурации с примером
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    def _log(self, message, level="INFO"):
        """Логирование сообщений"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Пишем в файл
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # Пишем в stdout
        print(log_entry.strip())
    
    def _send_telegram_message(self, chat_id, text, parse_mode="HTML"):
        """Отправка сообщения в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self._log(f"Error sending Telegram message: {e}", "ERROR")
            return False
    
    def _get_updates(self):
        """Получение обновлений от Telegram API"""
        try:
            # Используем offset для получения новых сообщений
            if not hasattr(self, '_last_update_id'):
                self._last_update_id = 0
            
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                "offset": self._last_update_id + 1,
                "timeout": 30
            }
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    updates = result.get("result", [])
                    if updates:
                        self._last_update_id = updates[-1]["update_id"]
                    return updates
            return []
        except Exception as e:
            self._log(f"Error getting updates: {e}", "ERROR")
            return []
    
    def _handle_command(self, message):
        """Обработка команды от пользователя"""
        try:
            chat_id = message["message"]["chat"]["id"]
            text = message["message"]["text"]
            user_id = message["message"]["from"]["id"]
            
            # Проверяем, является ли пользователь администратором
            if str(chat_id) != str(self.admin_chat_id) and str(user_id) != str(self.admin_chat_id):
                self._send_telegram_message(chat_id, "❌ Доступ запрещен")
                return
            
            # Логируем команду
            command_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "chat_id": chat_id,
                "command": text
            }
            self.command_history.append(command_entry)
            
            # Обработка команд
            if text == "/start":
                response = self._handle_start_command()
            elif text == "/status":
                response = self._handle_status_command()
            elif text == "/stats":
                response = self._handle_stats_command()
            elif text.startswith("/create_client"):
                response = self._handle_create_client_command(text)
            elif text.startswith("/get_config"):
                response = self._handle_get_config_command(text)
            elif text == "/help":
                response = self._handle_help_command()
            else:
                response = self._handle_unknown_command(text)
            
            if response:
                self._send_telegram_message(chat_id, response)
                
        except Exception as e:
            self._log(f"Error handling command: {e}", "ERROR")
    
    def _handle_start_command(self):
        """Обработка команды /start"""
        return """🚀 <b>XVPN Telegram Bot</b>

Добро пожаловать в систему управления XVPN!

Доступные команды:
/status - Проверить статус системы
/stats - Статистика системы
/create_client - Создать нового клиента
/get_config &lt;uuid&gt; - Получить конфигурацию клиента
/help - Помощь

Для административного доступа ваш ID должен быть указан в конфигурации."""
    
    def _handle_status_command(self):
        """Обработка команды /status"""
        try:
            # Получаем статус с API сервера
            url = f"{self.api_server}/mcp/v1/vpn.health"
            self._log(f"Attempting to connect to: {url}", "INFO")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                mask_score = health_data.get("mask_score", "N/A")
                status = health_data.get("status", "unknown")
                
                return f"""📊 <b>Состояние системы</b>

<b>Статус:</b> {status}
<b>Маскировка:</b> {mask_score}/5
<b>Версия:</b> {health_data.get('version', 'N/A')}
<b>Время:</b> {datetime.fromtimestamp(health_data.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}"""
            else:
                self._log(f"Status API returned non-200 status: {response.status_code}", "ERROR")
                return f"❌ Не удалось получить статус системы (код: {response.status_code})"
        except requests.exceptions.ConnectionError as e:
            self._log(f"Connection error when getting status: {e}", "ERROR")
            return f"❌ Не удалось подключиться к API серверу: {self.api_server}"
        except requests.exceptions.Timeout as e:
            self._log(f"Timeout error when getting status: {e}", "ERROR")
            return "❌ Время ожидания запроса к API истекло"
        except Exception as e:
            self._log(f"Error getting status: {e}", "ERROR")
            return f"❌ Ошибка при получении статуса системы: {str(e)}"
    
    def _handle_stats_command(self):
        """Обработка команды /stats"""
        try:
            import psutil
            import os
            
            # Собираем статистику системы
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            uptime = time.time() - psutil.boot_time()
            
            stats = f"""📈 <b>Статистика системы</b>

<b>CPU:</b> {cpu_percent}%
<b>Память:</b> {memory_percent}%
<b>Диск:</b> {disk_percent}%
<b>Время работы:</b> {uptime/3600:.1f} часов

<b>Количество команд:</b> {len(self.command_history)}
<b>Последняя команда:</b> {self.command_history[-1]['command'] if self.command_history else 'Нет'}"""
            
            return stats
        except Exception as e:
            self._log(f"Error getting stats: {e}", "ERROR")
            return "❌ Ошибка при получении статистики"
    
    def _handle_create_client_command(self, command):
        """Обработка команды /create_client"""
        try:
            # Отправляем запрос на создание клиента через API
            url = f"{self.api_server}/mcp/v1/admin.newclient"
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                client_data = response.json()
                if client_data.get("success"):
                    client_uuid = client_data["uuid"]
                    config_url = client_data["config_url"]
                    
                    return f"""✅ <b>Клиент создан</b>

<b>UUID:</b> <code>{client_uuid}</code>
<b>Конфигурация:</b> {config_url}

Для получения конфигурации используйте:
/get_config {client_uuid}"""
                else:
                    return "❌ Ошибка при создании клиента"
            else:
                return "❌ Сервер недоступен для создания клиента"
        except Exception as e:
            self._log(f"Error creating client: {e}", "ERROR")
            return "❌ Ошибка при создании клиента"
    
    def _handle_get_config_command(self, command):
        """Обработка команды /get_config UUID"""
        try:
            parts = command.split(" ")
            if len(parts) < 2:
                return "❌ Укажите UUID клиента: /get_config UUID\n\nПример: <code>/get_config 123e4567-e89b-12d3-a456-426614174000</code>"
            
            client_uuid = parts[1].strip()
            
            # Проверяем формат UUID
            import uuid
            try:
                uuid.UUID(client_uuid)
            except ValueError:
                return "❌ Неверный формат UUID"
            
            # Получаем конфигурацию клиента
            url = f"{self.api_server}/clients/{client_uuid}.json"
            self._log(f"Attempting to get config for UUID: {client_uuid} from {url}", "INFO")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                
                # Формируем сообщение с конфигурацией
                config_info = f"""📋 <b>Конфигурация клиента</b>

<b>UUID:</b> <code>{config.get('uuid', 'N/A')}</code>

<b>Доступные транспорты:</b> {len(config.get('transports', []))}
"""
                
                for i, transport in enumerate(config.get('transports', [])[:3]):  # Показываем первые 3
                    config_info += f"""
<b>Транспорт #{i+1}:</b>
  - ID: {transport.get('id', 'N/A')}
  - Название: {transport.get('name', 'N/A')}
  - Приоритет: {transport.get('priority', 'N/A')}
"""
                
                return config_info
            elif response.status_code == 404:
                self._log(f"Client with UUID {client_uuid} not found", "WARNING")
                return f"❌ Клиент с UUID {client_uuid} не найден"
            else:
                self._log(f"Unexpected status code {response.status_code} when getting config for UUID {client_uuid}", "ERROR")
                return f"❌ Ошибка получения конфигурации (код: {response.status_code})"
        except requests.exceptions.ConnectionError as e:
            self._log(f"Connection error when getting config for UUID {client_uuid}: {e}", "ERROR")
            return f"❌ Не удалось подключиться к API серверу: {self.api_server}"
        except requests.exceptions.Timeout as e:
            self._log(f"Timeout error when getting config for UUID {client_uuid}: {e}", "ERROR")
            return "❌ Время ожидания запроса к API истекло"
        except Exception as e:
            self._log(f"Error getting config: {e}", "ERROR")
            return f"❌ Ошибка при получении конфигурации: {str(e)}"
    
    def _handle_help_command(self):
        """Обработка команды /help"""
        return """📚 <b>Справка по командам XVPN Bot</b>

/start - Приветственное сообщение
/status - Проверить статус системы
/stats - Статистика системы
/create_client - Создать нового клиента
/get_config &lt;uuid&gt; - Получить конфигурацию клиента
/help - Это сообщение

Доступно только администраторам."""
    
    def _handle_unknown_command(self, command):
        """Обработка неизвестной команды"""
        return f"❓ Неизвестная команда: {command}\nИспользуйте /help для списка команд."
    
    def bot_loop(self):
        """Основной цикл работы бота"""
        self._log("XVPN Telegram Bot started")
        
        while self.running:
            try:
                # Получаем обновления
                updates = self._get_updates()
                
                # Обрабатываем каждое обновление
                for update in updates:
                    if "message" in update and "text" in update["message"]:
                        self._handle_command(update)
                
                # Засыпаем перед следующей проверкой
                time.sleep(self.config.get("polling_interval", 10))
                
            except Exception as e:
                self._log(f"Error in bot loop: {e}", "ERROR")
                time.sleep(5)  # Небольшая задержка перед продолжением
    
    def start(self):
        """Запуск бота"""
        if not self.bot_token or self.bot_token == "YOUR_BOT_TOKEN_HERE":
            self._log("Bot token not configured", "ERROR")
            return False
        
        if not self.admin_chat_id or self.admin_chat_id == "YOUR_CHAT_ID_HERE":
            self._log("Admin chat ID not configured", "ERROR")
            return False
        
        self.running = True
        self.bot_loop()
    
    def stop(self):
        """Остановка бота"""
        self.running = False
        self._log("XVPN Telegram Bot stopped")


def main():
    """Основная функция запуска бота"""
    bot = XVPNBot()
    
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()
        return 0
    except Exception as e:
        print(f"Unexpected error in bot: {e}")
        return 1
    finally:
        bot.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
