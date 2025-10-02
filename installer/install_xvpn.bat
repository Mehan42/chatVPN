@echo off
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
if not exist "C:\xvpn" mkdir C:\xvpn
if not exist "C:\xvpn\client" mkdir C:\xvpn\client
if not exist "C:\xvpn\server" mkdir C:\xvpn\server
if not exist "C:\xvpn\logs" mkdir C:\xvpn\logs

REM Копирование файлов
echo Копирование файлов...
xcopy client C:\xvpn\client\ /E /I /Y
xcopy server C:\xvpn\server\ /E /I /Y

REM Установка зависимостей
echo Установка зависимостей...
cd C:\xvpn
pip install -r requirements.txt

REM Запуск сервисов
echo Запуск сервисов...
start /B python server\api\app.py
start /B python server\bot_src\__main__.py

REM Завершение установки
echo.
echo === Установка XVPN завершена ===
echo.
echo Логи: C:\xvpn\logs\
echo.
echo Для управления используйте:
echo - Запуск/остановка: taskkill /F /IM python.exe
echo - Перезапуск: restart_xvpn.bat
echo.
pause
