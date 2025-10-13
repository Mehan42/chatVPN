#!/usr/bin/env python3
"""
Скрипт для запуска VPN клиента с указанным UUID
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Добавляем директорию скрипта в путь поиска модулей
CLIENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CLIENT_DIR))

def setup_logging():
    """Настройка логирования в файл с текущей датой и временем"""
    log_filename = f"client_manual_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = CLIENT_DIR / log_filename
    
    # Настройка основного логирования
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print(f"Логи будут сохраняться в файл: {log_filepath}")
    return log_filepath

def main():
    print("Запуск XVPN клиента с ручным UUID...")
    log_filepath = setup_logging()
    
    # Получаем UUID из аргумента командной строки или используем текущий
    if len(sys.argv) > 1:
        client_uuid = sys.argv[1]
        print(f"Используем UUID из аргумента: {client_uuid}")
    else:
        # Читаем UUID из файла client.conf
        uuid_file = CLIENT_DIR / "client.conf"
        if uuid_file.exists():
            with open(uuid_file, 'r') as f:
                client_uuid = f.read().strip()
            print(f"Используем UUID из файла client.conf: {client_uuid}")
        else:
            print("Файл client.conf не найден, используем тестовый UUID")
            client_uuid = "test-client-uuid"
    
    try:
        from vpn_client import VPNClient
        
        print("Создание экземпляра VPN клиента...")
        client = VPNClient(client_uuid)
        
        print("Инициализация клиента...")
        if client.initialize():
            print("✓ Клиент успешно инициализирован")
            
            # Получение и вывод информации о клиенте
            print(f"UUID клиента: {client.get_client_uuid()}")
            print(f"Статус здоровья: {client.get_health_score()}/100")
            print(f"Информация о сети: {client.get_network_info()}")
            print(f"Поддержка IPv6: {client.support_ipv6()}")
            print(f"Информация об IPv6: {client.get_ipv6_info()}")
            
            # Информация о транспортах
            transport_info = client.get_transport_info()
            print(f"Транспортная информация: {transport_info}")
            
            print("\n--- ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ ---")
            
            # Запускаем клиент
            print("Запуск VPN клиента...")
            if client.start():
                print("✓ VPN клиент запущен")
                
                # Проверяем начальный статус
                initial_status = client.get_status()
                print(f"Начальный статус: {initial_status}")
                
                # Попытка запустить VPN
                print("\nПопытка запуска VPN...")
                if client.start_vpn():
                    print("✓ Запрос запуска VPN отправлен")
                    print(f"Текущий статус: {client.get_status()}")
                    
                    # Ждем несколько секунд и проверяем статус
                    import time
                    print("\nОжидание соединения... (10 секунд)")
                    for i in range(10):
                        time.sleep(1)
                        status = client.get_status()
                        print(f"Статус после {i+1} сек: {status.get('current_state', 'unknown')}")
                        
                        # Если состояние изменилось на "running", выходим из цикла
                        if status.get('current_state') == 'running':
                            print("✓ VPN соединение установлено!")
                            break
                else:
                    print("✗ Ошибка запуска VPN")
                
                # Ждем немного перед остановкой
                time.sleep(3)
                
                # Останавливаем соединение
                print("\nОстановка VPN...")
                if client.stop_vpn():
                    print("✓ Запрос остановки VPN отправлен")
                else:
                    print("✗ Ошибка остановки VPN")
                
                # Ждем завершения
                time.sleep(2)
                
                # Останавливаем клиент
                if client.stop():
                    print("✓ VPN клиент остановлен")
                else:
                    print("⚠ Ошибка остановки VPN клиента")
            else:
                print("✗ Ошибка запуска VPN клиента")
        else:
            print("✗ Ошибка инициализации клиента")
            
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"✗ Ошибка при работе приложения: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\nВсе логи сохранены в файл: {log_filepath}")
        print("Работа приложения завершена.")

if __name__ == "__main__":
    main()