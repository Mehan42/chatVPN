# XVPN Гибкое развертывание и автоматическое обновление

## Обзор

Этот документ описывает изменения, внесенные в систему XVPN для поддержки гибкого развертывания в произвольных директориях и автоматического обновления. 

## Проблемы, которые решались

### 1. Жестко заданные пути
Ранее система XVPN использовала жестко заданные абсолютные пути вида `~/chatvpn/client/...`, что ограничивало установку только в конкретную директорию.

### 2. Отсутствие автоматического обновления
Не было механизма автоматического отслеживания изменений в репозитории и обновления клиентов/серверов.

### 3. Несовместимость с произвольной структурой
Относительные импорты Python не позволяли запускать клиент вне контекста пакета.

## Внесенные изменения

### 1. Унификация путей в клиентах
Файлы в директории `/home/uss/chatvpn/client/` были обновлены для использования относительных путей:

```python
# Было:
CONFIG_PATH = os.path.expanduser("~/chatvpn/client/client.json")
LOG_DIR = Path.home() / 'chatvpn' / 'client' / 'logs'

# Стало:
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()
CONFIG_PATH = CLIENT_DIR / 'client.json'
LOG_DIR = CLIENT_DIR / 'logs'
```

### 2. Исправление синтаксических ошибок
Создан и выполнен скрипт `fix_syntax_errors.py`, который исправил >50 синтаксических ошибок, возникших при автоматической замене путей:

- Неправильные кавычки: `"path' / 'filename"` → `"path" / "filename"`
- Лишние закрывающие скобки
- Дублирующиеся строки
- Незавершенные строковые литералы

### 3. Создание скриптов гибкой установки

#### install_client_flexible.sh
Поддерживает установку клиента в произвольную директорию:
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client -r https://github.com/myfork/chatVPN.git
```

#### install_server_flexible.sh
Поддерживает установку сервера с гибкой конфигурацией:
```bash
sudo ./install_server_flexible.sh -d /opt/xvpn -r https://github.com/myfork/chatVPN.git
```

### 4. Система автоматического обновления

#### deployment_watcher.py
Базовый watcher для отслеживания изменений в репозитории:
- Проверяет новые коммиты с заданным интервалом
- Определяет тип изменений (сервер/клиент)
- Выполняет соответствующие действия по обновлению

#### advanced_deployment_watcher.py
Расширенная система автоматического обновления:
- Поддержка конфигурационных файлов
- Интеллектуальный анализ содержания коммитов
- Уведомления через Telegram
- Поддержка нескольких репозиториев и веток
- Гибкая система действий (pip install, systemctl, custom scripts)

Пример конфигурации:
```json
{
  "repositories": [
    {
      "name": "main",
      "path": "/opt/xvpn",
      "branches": ["main", "develop"],
      "targets": {
        "server": {
          "files": ["server/", "api/", "bot/", "agent/"],
          "actions": [
            {"type": "pip_install", "requirements": "requirements_server.txt"},
            {"type": "systemctl", "services": ["xvpn-api", "xvpn-agent"], "sudo": true}
          ]
        },
        "client": {
          "files": ["client/", "requirements_client.txt"],
          "actions": [
            {"type": "pip_install", "requirements": "requirements_client.txt"},
            {"type": "systemctl", "services": ["xvpn-client"], "user": true}
          ]
        }
      }
    }
  ]
}
```

### 5. Исправление импортов в Python

Относительные импорты были заменены на абсолютные для совместимости:
```python
# Было:
from .discover import discover_transports

# Стало:
import discover
# Использование: discover.discover_transports()
```

### 6. Скрипт копирования обновлений

Создан `copy_updated_client.sh` для синхронизации изменений из директории разработки в установленный клиент:
```bash
./copy_updated_client.sh
```

## Структура файлов

### Основные скрипты и утилиты
```
/home/uss/chatvpn/
├── update_client_paths.py          # Обновление путей в файлах клиента
├── fix_syntax_errors.py             # Исправление синтаксических ошибок
├── deployment_watcher.py            # Базовый watcher обновлений
├── advanced_deployment_watcher.py   # Расширенный watcher обновлений
├── deployment_config.json           # Конфигурация для watcher'а
├── install_client_flexible.sh       # Гибкая установка клиента
├── install_server_flexible.sh       # Гибкая установка сервера
├── copy_updated_client.sh           # Копирование обновлений
└── run_client_fixed.py             # Исправленный скрипт запуска клиента
```

### Директории установки
```
Клиент: ~/xvpn_client/ (или любая другая)
Сервер: /opt/xvpn/ (или любая другая, при установке от root)
```

## Как использовать

### 1. Установка клиента в произвольную директорию
```bash
cd /home/uss/chatvpn
./install_client_flexible.sh -d /opt/my_xvpn_client
```

### 2. Установка сервера
```bash
cd /home/uss/chatvpn
sudo ./install_server_flexible.sh -d /opt/xvpn
```

### 3. Запуск автоматического обновления
```bash
cd /opt/xvpn
python3 advanced_deployment_watcher.py --config deployment_config.json
```

### 4. Ручное обновление клиента
```bash
cd /home/uss/chatvpn
./copy_updated_client.sh
```

## Проверка работоспособности

### Тестирование импорта модулей
```bash
cd /home/uss/chatvpn/client
python3 -c "import health, chatvpn_backend, state_machine, ipv6_manager"
```

### Запуск клиента
```bash
cd /home/uss/xvpn_client
python3 run_client.py
```

## Совместимость

### Поддерживаемые платформы
- Linux (Ubuntu/Debian)
- Windows (с поддержкой WSL)
- macOS (с поддержкой Homebrew)

### Поддерживаемые методы установки
1. Скрипты установки (`install_client_flexible.sh`, `install_server_flexible.sh`)
2. Docker Compose
3. Системные пакеты (deb, rpm)
4. Автономные исполняемые файлы (PEX)

## Безопасность

### Меры безопасности
- Все пути определяются динамически относительно местоположения скрипта
- Отсутствие жестко заданных абсолютных путей
- Поддержка переменных окружения для конфигурации
- Проверка целостности файлов при копировании

## Отладка

### Частые проблемы и решения

#### 1. ImportError: attempted relative import with no known parent package
**Решение**: Использовать `run_client.py` вместо прямого запуска модулей

#### 2. FileNotFoundError: [Errno 2] No such file or directory
**Решение**: Проверить, что CLIENT_DIR корректно определяется

#### 3. Permission denied при запуске скриптов
**Решение**: Выполнить `chmod +x script_name.sh`

## Поддержка

Для получения помощи по использованию системы гибкого развертывания:
1. Проверьте логи в `deployment_watcher.log`
2. Обратитесь к документации в README.md
3. Создайте issue в репозитории GitHub

---
*Документ создан: 09.10.2025*
*Автор: Система автоматического обновления XVPN*