#!/usr/bin/env python3
"""
XVPN CLI Interface
Интерфейс командной строки для управления XVPN системой
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any

# Добавляем пути к модулям
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "server"))
sys.path.append(str(Path(__file__).parent / "client"))

def load_client_config() -> Dict[str, Any]:
    """Загрузка конфигурации клиента"""
    config_path = Path.home() / 'chatvpn' / 'client' / 'client.json'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return {}
    return {}

def save_client_config(config: Dict[str, Any]):
    """Сохранение конфигурации клиента"""
    config_path = Path.home() / 'chatvpn' / 'client' / 'client.json'
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print("Конфигурация сохранена успешно")
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")

def get_client_uuid() -> str:
    """Получение UUID клиента"""
    config = load_client_config()
    return config.get('uuid', 'unknown')

def set_client_uuid(uuid: str):
    """Установка UUID клиента"""
    config = load_client_config()
    config['uuid'] = uuid
    save_client_config(config)

def start_vpn():
    """Запуск VPN"""
    print("Запуск VPN...")
    try:
        # Импортируем необходимые модули
        from client.chatvpn_backend import start_xray
        if start_xray():
            print("✅ VPN запущен успешно")
        else:
            print("❌ Ошибка запуска VPN")
    except Exception as e:
        print(f"❌ Ошибка запуска VPN: {e}")

def stop_vpn():
    """Остановка VPN"""
    print("Остановка VPN...")
    try:
        # Импортируем необходимые модули
        from client.chatvpn_backend import stop_xray
        if stop_xray():
            print("⏹️ VPN остановлен успешно")
        else:
            print("❌ Ошибка остановки VPN")
    except Exception as e:
        print(f"❌ Ошибка остановки VPN: {e}")

def get_status():
    """Получение статуса"""
    print("Получение статуса...")
    try:
        # Импортируем необходимые модули
        from client.chatvpn_backend import get_status
        status = get_status()
        print(f"Статус: {status['status']}")
        if 'exit_code' in status:
            print(f"Код выхода: {status['exit_code']}")
        if 'error' in status:
            print(f"Ошибка: {status['error']}")
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")

def request_config():
    """Запрос конфигурации с сервера"""
    print("Запрос конфигурации с сервера...")
    try:
        # Импортируем необходимые модули
        from client.chatvpn_backend import load_config_from_server
        if load_config_from_server():
            print("📥 Конфигурация успешно получена")
        else:
            print("❌ Ошибка получения конфигурации")
    except Exception as e:
        print(f"❌ Ошибка запроса конфигурации: {e}")

def get_health():
    """Получение информации о здоровье"""
    print("Получение информации о здоровье...")
    try:
        # Импортируем необходимые модули
        from client.health import get_mask_score, get_network_info
        mask_score = get_mask_score()
        network_info = get_network_info()
        
        print(f"Оценка маскировки: {mask_score}/5")
        print(f"IP адрес: {network_info.get('external_ip', 'Неизвестен')}")
        print(f"IPv6 поддержка: {'Да' if network_info.get('ipv6_supported', False) else 'Нет'}")
        print(f"VPN активен: {'Да' if network_info.get('vpn_active', False) else 'Нет'}")
    except Exception as e:
        print(f"❌ Ошибка получения информации о здоровье: {e}")

def switch_transport(transport_id: str):
    """Переключение транспорта"""
    print(f"Переключение на транспорт: {transport_id}")
    try:
        # Импортируем необходимые модули
        from client.transport_manager import get_transport_manager
        tm = get_transport_manager(get_client_uuid())
        if tm.force_transport_switch(transport_id):
            print(f"🔄 Транспорт успешно переключен на {transport_id}")
        else:
            print(f"❌ Ошибка переключения транспорта на {transport_id}")
    except Exception as e:
        print(f"❌ Ошибка переключения транспорта: {e}")

def list_transports():
    """Список доступных транспортов"""
    print("Список доступных транспортов:")
    try:
        # Импортируем необходимые модули
        from client.transport_manager import get_transport_manager
        tm = get_transport_manager(get_client_uuid())
        transports = tm.get_available_transports()
        
        if transports:
            for i, transport in enumerate(transports, 1):
                print(f"  {i}. {transport.get('id', 'unknown')} - {transport.get('name', 'Unnamed Transport')}")
        else:
            print("  Нет доступных транспортов")
    except Exception as e:
        print(f"❌ Ошибка получения списка транспортов: {e}")

def get_current_transport():
    """Получение текущего транспорта"""
    print("Текущий транспорт:")
    try:
        # Импортируем необходимые модули
        from client.transport_manager import get_transport_manager
        tm = get_transport_manager(get_client_uuid())
        current_transport = tm.get_current_transport()
        
        if current_transport:
            print(f"  ID: {current_transport.get('id', 'unknown')}")
            print(f"  Название: {current_transport.get('name', 'Unnamed Transport')}")
            print(f"  Тип: {current_transport.get('type', 'unknown')}")
        else:
            print("  Транспорт не установлен")
    except Exception as e:
        print(f"❌ Ошибка получения текущего транспорта: {e}")

def test_connectivity():
    """Тестирование подключения"""
    print("Тестирование подключения...")
    try:
        # Импортируем необходимые модули
        from client.health import get_network_info
        network_info = get_network_info()
        
        print("Результаты тестирования:")
        print(f"  IPv4 DNS: {'✅' if network_info.get('dns_resolved', False) else '❌'}")
        print(f"  IPv6 DNS: {'✅' if network_info.get('dns_resolved_ipv6', False) else '❌'}")
        print(f"  IPv4 TCP: {'✅' if network_info.get('tcp_connectivity', False) else '❌'}")
        print(f"  IPv6 TCP: {'✅' if network_info.get('tcp_connectivity_ipv6', False) else '❌'}")
        print(f"  IPv4 HTTP: {'✅' if network_info.get('http_connectivity', False) else '❌'}")
        print(f"  IPv6 HTTP: {'✅' if network_info.get('http_connectivity_ipv6', False) else '❌'}")
        print(f"  Dual-Stack: {'✅' if network_info.get('dual_stack_connectivity', False) else '❌'}")
    except Exception as e:
        print(f"❌ Ошибка тестирования подключения: {e}")

def show_logs(lines: int = 20):
    """Показ логов"""
    print(f"Последние {lines} строк логов:")
    try:
        log_path = Path.home() / 'chatvpn' / 'client' / 'logs' / 'client.log'
        if log_path.exists():
            with open(log_path, 'r') as f:
                log_lines = f.readlines()
                # Показываем последние N строк
                for line in log_lines[-lines:]:
                    print(f"  {line.strip()}")
        else:
            print("  Лог файл не найден")
    except Exception as e:
        print(f"❌ Ошибка чтения логов: {e}")

def main():
    """Основная функция CLI интерфейса"""
    parser = argparse.ArgumentParser(
        description="XVPN CLI Interface - Управление XVPN системой",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  xvpn-cli start                     # Запустить VPN
  xvpn-cli stop                      # Остановить VPN
  xvpn-cli status                    # Показать статус
  xvpn-cli config                    # Запросить конфигурацию с сервера
  xvpn-cli health                    # Показать информацию о здоровье
  xvpn-cli transport list            # Список доступных транспортов
  xvpn-cli transport current         # Показать текущий транспорт
  xvpn-cli transport switch <id>     # Переключить транспорт
  xvpn-cli test                      # Тестирование подключения
  xvpn-cli logs                      # Показать логи
  xvpn-cli uuid <new-uuid>           # Установить новый UUID клиента
        """
    )
    
    # Основные команды
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Запуск VPN
    subparsers.add_parser('start', help='Запустить VPN')
    
    # Остановка VPN
    subparsers.add_parser('stop', help='Остановить VPN')
    
    # Статус
    subparsers.add_parser('status', help='Показать статус')
    
    # Запрос конфигурации
    subparsers.add_parser('config', help='Запросить конфигурацию с сервера')
    
    # Здоровье
    subparsers.add_parser('health', help='Показать информацию о здоровье')
    
    # Транспорты
    transport_parser = subparsers.add_parser('transport', help='Управление транспортами')
    transport_subparsers = transport_parser.add_subparsers(dest='transport_command', help='Команды управления транспортами')
    
    # Список транспортов
    transport_subparsers.add_parser('list', help='Список доступных транспортов')
    
    # Текущий транспорт
    transport_subparsers.add_parser('current', help='Показать текущий транспорт')
    
    # Переключение транспорта
    switch_parser = transport_subparsers.add_parser('switch', help='Переключить транспорт')
    switch_parser.add_argument('transport_id', help='ID транспорта для переключения')
    
    # Тестирование
    subparsers.add_parser('test', help='Тестирование подключения')
    
    # Логи
    logs_parser = subparsers.add_parser('logs', help='Показать логи')
    logs_parser.add_argument('-n', '--lines', type=int, default=20, help='Количество строк для показа (по умолчанию: 20)')
    
    # UUID
    uuid_parser = subparsers.add_parser('uuid', help='Управление UUID клиента')
    uuid_parser.add_argument('new_uuid', nargs='?', help='Новый UUID клиента')
    
    # Парсинг аргументов
    args = parser.parse_args()
    
    # Если команда не указана, показываем помощь
    if not args.command:
        parser.print_help()
        return
    
    # Обработка команд
    if args.command == 'start':
        start_vpn()
    elif args.command == 'stop':
        stop_vpn()
    elif args.command == 'status':
        get_status()
    elif args.command == 'config':
        request_config()
    elif args.command == 'health':
        get_health()
    elif args.command == 'transport':
        if not args.transport_command:
            transport_parser.print_help()
            return
        
        if args.transport_command == 'list':
            list_transports()
        elif args.transport_command == 'current':
            get_current_transport()
        elif args.transport_command == 'switch':
            switch_transport(args.transport_id)
    elif args.command == 'test':
        test_connectivity()
    elif args.command == 'logs':
        show_logs(args.lines)
    elif args.command == 'uuid':
        if args.new_uuid:
            set_client_uuid(args.new_uuid)
            print(f"UUID клиента установлен: {args.new_uuid}")
        else:
            print(f"Текущий UUID клиента: {get_client_uuid()}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()