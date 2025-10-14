# Инструкция по развертыванию XVPN

## Архитектура развертывания

Проект развертывается в двух местах:
1. **Удаленный сервер** - автоматическая проверка кода после обновления
2. **Локальный ПК** `/home/uss/xvpn_client` - ручное тестирование и демонстрация

## Ветка для развертывания

Для всех сред используется ветка: **`тест`**

## Шаги развертывания

### 1. Удаленный сервер

```bash
# Переключиться на ветку тест
git checkout тест
git pull origin тест

# Запустить Docker-контейнеры
cd /path/to/project
docker-compose -f docker-compose.go.yml up -d

# Проверить статус
docker-compose -f docker-compose.go.yml ps
docker-compose -f docker-compose.go.yml logs xvpn-go-server
```

### 2. Локальный ПК `/home/uss/xvpn_client`

```bash
# Перейти в директорию клиента
cd /home/uss/xvpn_client

# Обновить код с ветки тест
git checkout тест
git pull origin тест

# Запустить Go-клиент
./xvpn-client-go/xvpn-client

# Или запустить GUI
./xvpn-client-go/xvpn-client-gui
```

## Переменные окружения

Для удаленного сервера необходимо установить:
```bash
export TELEGRAM_BOT_TOKEN="ваш_токен"
export TELEGRAM_CHAT_ID="ваш_chat_id"
```

## Мониторинг

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Сервер API: https://localhost:8443

## Тестирование

После развертывания выполнить:
```bash
# Тестирование API
curl -k https://localhost:8443/health

# Тестирование метрик
curl -k https://localhost:8443/metrics