#!/usr/bin/env python3
"""
Простой скрипт для запуска VPN клиента с подробным логированием
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
    log_filename = f"simple_client_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    print("Запуск XVPN клиента в упрощенном режиме отладки...")
    log_filepath = setup_logging()
    
    try:
        from vpn_client import VPNClient
        
        print("Создание экземпляра VPN клиента...")
        client = VPNClient()
        
        print("Инициализация клиента...")
        if client.initialize():
            print("Клиент успешно инициализирован")
            
            # Получение и вывод информации о клиенте
            print(f"UUID клиента: {client.get_client_uuid()}")
            print(f"Статус здоровья: {client.get_health_score()}/100")
            print(f"Информация о сети: {client.get_network_info()}")
            print(f"Поддержка IPv6: {client.support_ipv6()}")
            print(f"Информация об IPv6: {client.get_ipv6_info()}")
            
            # Информация о транспортах
            transport_info = client.get_transport_info()
            print(f"Транспортная информация: {transport_info}")
            
            # Попытка запустить VPN
            print("\nПопытка запуска VPN...")
            if client.start():
                print("VPN клиент запущен")
                
                # Попытка начать соединение
                if client.start_vpn():
                    print("Запрос запуска VPN отправлен")
                    print(f"Текущий статус: {client.get_status()}")
                    
                    # Ждем несколько секунд и проверяем статус
                    import time
                    print("\nОжидание соединения... (5 секунд)")
                    time.sleep(5)
                    
                    print(f"Текущий статус после ожидания: {client.get_status()}")
                    print(f"Запущен ли клиент: {client.is_running()}")
                    
                    # Останавливаем соединение
                    print("\nОстановка VPN...")
                    if client.stop_vpn():
                        print("Запрос остановки VPN отправлен")
                    else:
                        print("Ошибка остановки VPN")
                else:
                    print("Ошибка запуска VPN")
            else:
                print("Ошибка запуска VPN клиента")
        else:
            print("Ошибка инициализации клиента")
            
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Ошибка при работе приложения: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\nВсе логи сохранены в файл: {log_filepath}")
        print("Работа приложения завершена.")

if __name__ == "__main__":
    main()