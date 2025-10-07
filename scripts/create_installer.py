#!/usr/bin/env python3
# Создание установщика XVPN
# Абсолютный путь: ~/chatvpn/scripts/create_installer.py

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def create_installer():
    """Создание универсального установщика XVPN"""
    print("=== Создание установщика XVPN ===")
    
    try:
        # Создание директории для установщика
        installer_dir = Path.home() / 'chatvpn' / 'installer'
        installer_dir.mkdir(parents=True, exist_ok=True)
        
        # Создание скрипта установки
        install_script = """#!/bin/bash
# Установщик XVPN
# Автоматическая установка XVPN системы

set -e

echo "=== Установка XVPN ==="
echo "Дата: $(date)"
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   echo "Используйте: sudo ./install_xvpn.sh"
   exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Установка Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не найден. Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание пользователя XVPN
if ! id "xvpn" &>/dev/null; then
    echo "Создание пользователя xvpn..."
    useradd -m -s /bin/bash xvpn
    passwd -d xvpn  # Установка пустого пароля
else
    echo "Пользователь xvpn уже существует"
fi

# Создание директорий
echo "Создание директорий..."
mkdir -p /home/xvpn/chatvpn
mkdir -p /home/xvpn/chatvpn/client
mkdir -p /home/xvpn/chatvpn/server
mkdir -p /home/xvpn/chatvpn/server/security
mkdir -p /home/xvpn/chatvpn/server/api
mkdir -p /home/xvpn/chatvpn/server/agent
mkdir -p /home/xvpn/chatvpn/server/deploy
mkdir -p /home/xvpn/chatvpn/docker
mkdir -p /home/xvpn/chatvpn/scripts
mkdir -p /home/xvpn/chatvpn/docs
mkdir -p /home/xvpn/chatvpn/systemd
mkdir -p /var/log/xvpn
mkdir -p /etc/xvpn

# Копирование файлов
echo "Копирование файлов..."
cp -r client/* /home/xvpn/chatvpn/client/
cp -r server/* /home/xvpn/chatvpn/server/
cp -r docker/* /home/xvpn/chatvpn/docker/
cp -r scripts/* /home/xvpn/chatvpn/scripts/
cp -r systemd/* /etc/systemd/system/

# Установка прав
echo "Установка прав..."
chown -R xvpn:xvpn /home/xvpn/chatvpn
chmod +x /home/xvpn/chatvpn/client/*.py
chmod +x /home/xvpn/chatvpn/server/*.py
chmod +x /home/xvpn/chatvpn/scripts/*.sh
chmod +x /home/xvpn/chatvpn/scripts/*.py

# Установка зависимостей
echo "Установка зависимостей..."
cd /home/xvpn/chatvpn
pip3 install -r requirements.txt

# Копирование конфигурации
echo "Копирование конфигурации..."
if [ ! -f /etc/xvpn/config.json ]; then
    cp client/client.json.example /etc/xvpn/config.json
    chown xvpn:xvpn /etc/xvpn/config.json
fi

# Настройка systemd
echo "Настройка systemd..."
systemctl daemon-reload

# Включение сервисов
echo "Включение сервисов..."
systemctl enable xvpn-api.service
systemctl enable xvpn-bot.service
systemctl enable xvpn-agent.service
systemctl enable xvpn-worker.service

# Запуск сервисов
echo "Запуск сервисов..."
systemctl start xvpn-api.service
systemctl start xvpn-bot.service
systemctl start xvpn-agent.service
systemctl start xvpn-worker.service

# Настройка Docker
echo "Настройка Docker..."
cd /home/xvpn/chatvpn
docker-compose up -d

# Проверка установки
echo "Проверка установки..."
sleep 10

# Проверка сервисов
if systemctl is-active --quiet xvpn-api.service; then
    echo "✓ API сервис запущен"
else
    echo "✗ API сервис не запущен"
fi

if systemctl is-active --quiet xvpn-bot.service; then
    echo "✓ Bot сервис запущен"
else
    echo "✗ Bot сервис не запущен"
fi

if docker ps | grep -q xvpn-api; then
    echo "✓ Docker контейнер API запущен"
else
    echo "✗ Docker контейнер API не запущен"
fi

# Завершение установки
echo ""
echo "=== Установка XVPN завершена ==="
echo "Логи:"
echo "  - Системные: journalctl -u xvpn-api.service"
echo "  - Docker: docker logs xvpn-api"
echo "  - Приложения: tail -f /var/log/xvpn/*.log"
echo ""
echo "Управление сервисами:"
echo "  - Запуск: sudo systemctl start xvpn-*.service"
echo "  - Остановка: sudo systemctl stop xvpn-*.service"
echo "  - Статус: sudo systemctl status xvpn-*.service"
echo ""
echo "Документация: /home/xvpn/chatvpn/docs/"
echo ""
echo "Для перезагрузки системы: sudo reboot"
"""

        # Сохранение скрипта установки
        install_script_path = installer_dir / 'install_xvpn.sh'
        with open(install_script_path, 'w') as f:
            f.write(install_script)
        
        # Установка прав на выполнение
        os.chmod(install_script_path, 0o755)
        
        print(f"✓ Скрипт установки создан: {install_script_path}")
        
        # Создание скрипта удаления
        uninstall_script = """#!/bin/bash
# Деинсталлятор XVPN

set -e

echo "=== Деинсталляция XVPN ==="
echo "Дата: $(date)"
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   echo "Используйте: sudo ./uninstall_xvpn.sh"
   exit 1
fi

# Остановка сервисов
echo "Остановка сервисов..."
systemctl stop xvpn-api.service
systemctl stop xvpn-bot.service
systemctl stop xvpn-agent.service
systemctl stop xvpn-worker.service

# Отключение сервисов
echo "Отключение сервисов..."
systemctl disable xvpn-api.service
systemctl disable xvpn-bot.service
systemctl disable xvpn-agent.service
systemctl disable xvpn-worker.service

# Удаление контейнеров Docker
echo "Удаление контейнеров Docker..."
cd /home/xvpn/chatvpn
docker-compose down -v

# Удаление systemd сервисов
echo "Удаление systemd сервисов..."
rm -f /etc/systemd/system/xvpn-*.service
systemctl daemon-reload

# Удаление директорий
echo "Удаление директорий..."
rm -rf /home/xvpn/chatvpn
rm -rf /etc/xvpn
rm -rf /var/log/xvpn

# Удаление пользователя
if id "xvpn" &>/dev/null; then
    echo "Удаление пользователя xvpn..."
    userdel -r xvpn
fi

# Удаление Docker (опционально)
read -p "Удалить Docker? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Удаление Docker..."
    apt-get purge -y docker-ce docker-ce-cli containerd.io docker-compose
    rm -rf /var/lib/docker
fi

# Очистка
echo "Очистка..."
apt-get autoremove -y
apt-get clean

echo ""
echo "=== Деинсталляция XVPN завершена ==="
"""

        # Сохранение скрипта удаления
        uninstall_script_path = installer_dir / 'uninstall_xvpn.sh'
        with open(uninstall_script_path, 'w') as f:
            f.write(uninstall_script)
        
        # Установка прав на выполнение
        os.chmod(uninstall_script_path, 0o755)
        
        print(f"✓ Скрипт удаления создан: {uninstall_script_path}")
        
        # Создание ZIP архива
        print("Создание ZIP архива...")
        archive_name = f"xvpn_installer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_path = installer_dir / f"{archive_name}.zip"
        
        # Создание временной директории для архива
        temp_dir = installer_dir / 'temp'
        temp_dir.mkdir(exist_ok=True)
        
        # Копирование файлов в временную директорию
        shutil.copy2(install_script_path, temp_dir / 'install_xvpn.sh')
        shutil.copy2(uninstall_script_path, temp_dir / 'uninstall_xvpn.sh')
        shutil.copy2('README.md', temp_dir)
        shutil.copy2('requirements.txt', temp_dir)
        
        # Создание архива
        shutil.make_archive(str(archive_path).replace('.zip', ''), 'zip', temp_dir)
        
        # Удаление временной директории
        shutil.rmtree(temp_dir)
        
        print(f"✓ ZIP архив создан: {archive_path}")
        
        # Создание Windows установщика (базовый)
        windows_installer = """@echo off
REM Установщик XVPN для Windows
echo === Установка XVPN ===
echo Дата: %date% %time%
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Этот скрипт должен быть запущен с правами администратора
    echo Запустите от имени администратора
    pause
    exit /b 1
)

REM Проверка Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python не найден. Установка Python...
    REM Здесь можно добавить установку Python
    echo Пожалуйста, установите Python вручную с python.org
    pause
    exit /b 1
)

REM Проверка Docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker не найден. Установка Docker...
    REM Здесь можно добавить установку Docker
    echo Пожалуйста, установите Docker Desktop вручную
    pause
    exit /b 1
)

REM Создание директорий
echo Создание директорий...
if not exist "C:\\xvpn" mkdir C:\\xvpn
if not exist "C:\\xvpn\\client" mkdir C:\\xvpn\\client
if not exist "C:\\xvpn\\server" mkdir C:\\xvpn\\server
if not exist "C:\\xvpn\\logs" mkdir C:\\xvpn\\logs

REM Копирование файлов
echo Копирование файлов...
xcopy client C:\\xvpn\\client\\ /E /I /Y
xcopy server C:\\xvpn\\server\\ /E /I /Y

REM Установка зависимостей
echo Установка зависимостей...
cd C:\\xvpn
pip install -r requirements.txt

REM Запуск сервисов
echo Запуск сервисов...
start /B python server\\api\\app.py
start /B python server\\bot_src\\__main__.py

REM Завершение установки
echo.
echo === Установка XVPN завершена ===
echo.
echo Логи: C:\\xvpn\\logs\\
echo.
echo Для управления используйте:
echo - Запуск/остановка: taskkill /F /IM python.exe
echo - Перезапуск: restart_xvpn.bat
echo.
pause
"""

        # Сохранение Windows установщика
        windows_installer_path = installer_dir / 'install_xvpn.bat'
        with open(windows_installer_path, 'w') as f:
            f.write(windows_installer)
        
        print(f"✓ Windows установщик создан: {windows_installer_path}")
        
        # Создание скрипта обновления
        update_script = """#!/bin/bash
# Обновление XVPN

set -e

echo "=== Обновление XVPN ==="
echo "Дата: $(date)"
echo ""

# Остановка сервисов
echo "Остановка сервисов..."
systemctl stop xvpn-api.service
systemctl stop xvpn-bot.service
systemctl stop xvpn-agent.service
systemctl stop xvpn-worker.service

# Остановка Docker
echo "Остановка Docker..."
cd /home/xvpn/chatvpn
docker-compose down

# Создание резервной копии
echo "Создание резервной копии..."
backup_dir="/home/xvpn/chatvpn_backup_$(date +%Y%m%d_%H%M%S)"
cp -r /home/xvpn/chatvpn "$backup_dir"

# Обновление файлов
echo "Обновление файлов..."
git pull origin main

# Обновление зависимостей
echo "Обновление зависимостей..."
pip3 install -r requirements.txt

# Обновление Docker образов
echo "Обновление Docker образов..."
docker-compose pull

# Запуск сервисов
echo "Запуск сервисов..."
docker-compose up -d

systemctl start xvpn-api.service
systemctl start xvpn-bot.service
systemctl start xvpn-agent.service
systemctl start xvpn-worker.service

# Проверка обновления
echo "Проверка обновления..."
sleep 10

if docker ps | grep -q xvpn-api; then
    echo "✓ Обновление успешно завершено"
else
    echo "✗ Ошибка обновления"
    echo "Восстановление из резервной копии..."
    cp -r "$backup_dir"/* /home/xvpn/chatvpn/
    docker-compose up -d
fi

echo ""
echo "=== Обновление XVPN завершено ==="
"""

        # Сохранение скрипта обновления
        update_script_path = installer_dir / 'update_xvpn.sh'
        with open(update_script_path, 'w') as f:
            f.write(update_script)
        
        # Установка прав на выполнение
        os.chmod(update_script_path, 0o755)
        
        print(f"✓ Скрипт обновления создан: {update_script_path}")
        
        # Создание отчета об установке
        report = {
            'installer_version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'files_created': [
                str(install_script_path),
                str(uninstall_script_path),
                str(archive_path),
                str(windows_installer_path),
                str(update_script_path)
            ],
            'features': [
                'Автоматическая установка зависимостей',
                'Настройка systemd сервисов',
                'Docker интеграция',
                'IPv6 поддержка',
                'Система безопасности',
                'REST API для администрирования',
                'Графический интерфейс',
                'Мониторинг здоровья'
            ],
            'supported_systems': [
                'Ubuntu 20.04+',
                'Debian 10+',
                'CentOS 7+',
                'RHEL 7+',
                'Windows 10+ (базовая поддержка)'
            ]
        }
        
        # Сохранение отчета
        report_path = installer_dir / 'installer_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Отчет об установке создан: {report_path}")
        
        print("\n=== Установщик XVPN создан успешно ===")
        print(f"Директория установщика: {installer_dir}")
        print(f"ZIP архив: {archive_path}")
        print(f"Windows установщик: {windows_installer_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка создания установщика: {e}")
        return False

if __name__ == "__main__":
    success = create_installer()
    if success:
        print("\n🎉 Установщик XVPN создан успешно!")
        sys.exit(0)
    else:
        print("\n❌ Ошибка создания установщика")
        sys.exit(1)