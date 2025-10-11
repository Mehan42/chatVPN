#!/bin/bash

echo "Запуск XVPN клиента..."

# Определяем, какой клиент запускать (Go или Python)
CLIENT_TYPE=${1:-go}

case $CLIENT_TYPE in
    "go")
        echo "Запуск Go-клиента..."
        cd /home/uss/xvpn_client/xvpn-client-go
        if [ -f "./xvpn-client" ]; then
            echo "Запускаем Go-клиент с подключением к uss.hopto.org:8443"
            ./xvpn-client
        else
            echo "Ошибка: Go-клиент не найден"
            exit 1
        fi
        ;;
    "python")
        echo "Запуск Python-клиента..."
        cd /home/uss/xvpn_client
        if [ -f "chatvpn_gui.py" ]; then
            echo "Запускаем Python GUI клиент"
            python3 chatvpn_gui.py
        else
            echo "Ошибка: Python клиент не найден"
            exit 1
        fi
        ;;
    "help")
        echo "Использование: $0 [go|python]"
        echo "  go (по умолчанию) - запустить Go-клиент"
        echo "  python - запустить Python-клиент"
        echo "  help - показать эту справку"
        ;;
    *)
        echo "Неизвестный тип клиента: $CLIENT_TYPE"
        echo "Используйте: $0 help для справки"
        exit 1
        ;;
esac