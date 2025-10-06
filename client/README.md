# XVPN Client

Клиентская часть XVPN системы.

## Установка и запуск "из коробки"

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Mehan42/chatVPN.git
   cd chatVPN
   ```

2. Перейдите в директорию клиента:
   ```bash
   cd client
   ```

3. Установите зависимости:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install curl jq

   # Установка Xray для подключения (опционально)
   # См. https://github.com/XTLS/Xray-core
   ```

## Использование

### 1. Настройка клиента
```bash
./scripts/configure_client.sh
```

### 2. Добавление дополнительных серверов (опционально)
```bash
./scripts/add_server.sh
```

### 3. Получение конфигурации от сервера
```bash
./scripts/get_config.sh
```

### 4. Запуск клиента
```bash
./scripts/start_client.sh
```

## Архитектура

- `config/` - конфигурационные файлы
- `scripts/` - скрипты установки и управления
- `profiles/` - профили подключения
- `logs/` - логи подключений

## Многосерверная архитектура

Конфигурационный файл поддерживает подключение к нескольким серверам с возможностью автоматического переключения.