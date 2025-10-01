# Настройка systemd сервисов для XVPN

## Обзор

Этот документ описывает настройку и управление systemd сервисами для проекта XVPN. Все сервисы настроены для работы с новой структурой проекта в директории `~/.xvpn/`.

## Архитектура сервисов

### Основные сервисы

1. **xvpn.service** - Главный сервис для управления всеми компонентами
2. **xvpn-agent.service** - Агент мониторинга и управления транспортами
3. **xvpn-api.service** - REST API для управления VPN и клиентами
4. **xvpn-xray.service** - Xray VPN сервис
5. **xvpn-bot.service** - Telegram бот для управления
6. **xvpn-server-bot.service** - Дополнительный серверный бот (для обратной совместимости)

### Структура путей

Все сервисы используют пути в соответствии с новой структурой проекта:
- Базовая директория: `/home/%u/.xvpn/`
- Агент: `/home/%u/.xvpn/agent/`
- API: `/home/%u/.xvpn/api/`
- Бот: `/home/%u/.xvpn/bot_src/`
- Конфигурации: `/home/%u/.xvpn/`

## Установка сервисов

### Автоматическая установка

1. Запустите скрипт установки от root пользователя:
   ```bash
   sudo ./server/install_services.sh
   ```

2. Скрипт автоматически:
   - Скопирует сервисные файлы в `/etc/systemd/system/`
   - Создаст необходимые директории
   - Установит правильные права
   - Включит сервисы
   - Перезагрузит systemd

### Ручная установка

Если автоматическая установка невозможна, выполните следующие шаги:

1. Копируйте сервисные файлы:
   ```bash
   sudo cp server/*.service /etc/systemd/system/
   ```

2. Создайте директорию для проекта:
   ```bash
   mkdir -p ~/.xvpn
   ```

3. Перезагрузите systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

4. Включите сервисы:
   ```bash
   sudo systemctl enable xvpn.service
   sudo systemctl enable xvpn-agent.service
   sudo systemctl enable xvpn-api.service
   sudo systemctl enable xvpn-xray.service
   sudo systemctl enable xvpn-bot.service
   ```

## Управление сервисами

### Запуск и остановка

```bash
# Запуск всех сервисов
sudo systemctl start xvpn.service

# Остановка всех сервисов
sudo systemctl stop xvpn.service

# Перезапуск всех сервисов
sudo systemctl restart xvpn.service

# Перезапуск конкретного сервиса
sudo systemctl restart xvpn-agent.service
```

### Включение автозапуска

```bash
# Включение автозапуска при старте системы
sudo systemctl enable xvpn.service

# Отключение автозапуска
sudo systemctl disable xvpn.service
```

### Проверка статуса

```bash
# Статус главного сервиса
sudo systemctl status xvpn.service

# Статус всех сервисов XVPN
sudo systemctl status xvpn-*.service

# Детальная информация о сервисе
sudo systemctl show xvpn-agent.service
```

## Логирование

### Просмотр логов

```bash
# Логи главного сервиса
sudo journalctl -u xvpn.service -f

# Логи агента
sudo journalctl -u xvpn-agent.service -f

# Логи API
sudo journalctl -u xvpn-api.service -f

# Все логи XVPN
sudo journalctl -u xvpn-*.service -f

# Логи за последние 1 час
sudo journalctl -u xvpn-agent.service --since "1 hour ago"
```

### Фильтрация логов

```bash
# Логи по уровню критичности
sudo journalctl -u xvpn-agent.service -p err

# Логи конкретного процесса
sudo journalctl -u xvpn-api.service -g "ERROR"
```

## Конфигурация сервисов

### Общие параметры

Все сервисы имеют следующие общие параметры:
- `Restart=always` - автоматический перезапуск при падении
- `RestartSec=3` - пауза перед перезапуском
- `StartLimitIntervalSec=0` - ограничение на частоту запусков
- `StandardOutput=journal` - логирование в systemd journal
- `StandardError=journal` - ошибки в systemd journal

### Пользователи и права

- Все сервисы запускаются от имени текущего пользователя
- Права на директории: 755
- Права на файлы: 644 (исполняемые файлы: 755)

### Переменные окружения

- `PYTHONUNBUFFERED=1` - отключение буферизации вывода Python

## Обратная совместимость

### Старые имена сервисов

Для обратной совместимости сохранены старые имена сервисов:
- `server_bot.service` → `xvpn-server-bot.service`
- `xray.service` → `xvpn-xray.service`

### Старые пути

Если вы переходите со старой конфигурации, сервисы будут работать в режиме совместимости:
- Старые пути `/opt/xvpn/` автоматически перенаправляются на `~/.xvpn/`
- Конфигурационные файлы копируются автоматически при первом запуске

### Миграция данных

Для миграции данных со старой структуры:

1. Остановите старые сервисы:
   ```bash
   sudo systemctl stop server_bot.service xray.service
   ```

2. Скопируйте данные:
   ```bash
   cp -r /opt/xvpn/* ~/.xvpn/
   ```

3. Запустите новые сервисы:
   ```bash
   sudo systemctl start xvpn.service
   ```

## Устранение неполадок

### Common Issues

1. **Сервис не запускается**
   ```bash
   # Проверка статуса
   sudo systemctl status xvpn-agent.service
   
   # Просмотр ошибок
   sudo journalctl -u xvpn-agent.service -n 100
   ```

2. **Проблемы с правами доступа**
   ```bash
   # Проверка прав
   ls -la ~/.xvpn/
   
   # Исправление прав
   chmod -R 755 ~/.xvpn/
   chown -R $USER:$USER ~/.xvpn/
   ```

3. **Ошибки Python**
   ```bash
   # Проверка Python окружения
   python3 --version
   
   # Установка зависимостей
   pip3 install -r server/requirements.txt
   ```

### Диагностика

```bash
# Проверка зависимостей
sudo systemctl list-dependencies xvpn.service

# Проверка активных сервисов
sudo systemctl list-units --type=service | grep xvpn

# Проверка запущенных процессов
ps aux | grep -E "(agent|api|xray|bot)"
```

## Оптимизация производительности

### Настройка лимитов

Для высоконагруженных серверов можно настроить:

1. **Лимиты файловых дескрипторов**
   ```bash
   # В файле сервиса добавить:
   LimitNOFILE=65536
   ```

2. **Приоритет процесса**
   ```bash
   # В файле сервиса добавить:
   Nice=10
   ```

### Мониторинг

```bash
# Мониторинг использования ресурсов
htop

# Мониторинг сетевых соединений
sudo netstat -tulpn | grep xray

# Мониторинг логов в реальном времени
sudo journalctl -f -u xvpn-*.service
```

## Безопасность

### Рекомендации

1. **Обновление системных пакетов**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Firewall настройки**
   ```bash
   # Разрешить необходимые порты
   sudo ufw allow 8443/tcp  # API
   sudo ufw allow 443/tcp   # VPN
   sudo ufw allow 80/tcp    # Web
   ```

3. **Резервное копирование**
   ```bash
   # Резервная копия конфигурации
   tar -czf xvpn_backup.tar.gz ~/.xvpn/
   
   # Автоматическое резервное копирование
   0 2 * * * tar -czf /backup/xvpn_$(date +\%Y\%m\%d).tar.gz ~/.xvpn/
   ```

## Заключение

Эта настройка обеспечивает надежную работу всех компонентов XVPN с автоматическим восстановлением при сбоях, централизованным логированием и удобным управлением через systemd.