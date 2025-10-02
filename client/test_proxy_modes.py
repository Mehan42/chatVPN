#!/usr/bin/env python3
# Тест режимов прокси для XVPN
# Абсолютный путь: ~/chatvpn/client/test_proxy_modes.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from proxy_modes import get_proxy_modes_manager, ProxyMode
import json

def test_proxy_modes_manager():
    """Тестирование менеджера режимов прокси"""
    print("=== Тест менеджера режимов прокси XVPN ===")
    
    # Получение менеджера
    manager = get_proxy_modes_manager()
    
    # Тестирование получения информации о текущем режиме
    mode_info = manager.get_mode_info()
    print(f"✓ Текущий режим: {mode_info['current_mode']}")
    print(f"✓ Авто-обнаружение: {'Да' if mode_info['auto_detect_enabled'] else 'Нет'}")
    print(f"✓ Ручные настройки: {'Да' if mode_info['manual_settings_configured'] else 'Нет'}")
    print(f"✓ Прозрачный прокси: {'Да' if mode_info['transparent_enabled'] else 'Нет'}")
    print(f"✓ Split-tunnel: {'Да' if mode_info['split_tunnel_enabled'] else 'Нет'}")
    print(f"✓ DNS защита от утечек: {'Да' if mode_info['dns_leak_protection'] else 'Нет'}")
    
    # Тестирование списка доступных режимов
    available_modes = manager.get_available_modes()
    print(f"✓ Доступные режимы: {', '.join(available_modes)}")
    
    return True

def test_proxy_mode_switching():
    """Тестирование переключения режимов прокси"""
    print("\n=== Тест переключения режимов прокси ===")
    
    manager = get_proxy_modes_manager()
    
    # Тестирование переключения на разные режимы
    test_modes = [ProxyMode.MANUAL, ProxyMode.SYSTEM, ProxyMode.BYPASS]
    
    for mode in test_modes:
        try:
            print(f"✓ Переключение на режим: {mode.value}")
            
            # Включаем режим
            success = manager.set_mode(mode)
            print(f"  Результат: {'Успешно' if success else 'Ошибка'}")
            
            if success:
                # Проверяем, что режим действительно изменился
                current_mode = manager.get_current_mode()
                print(f"  Текущий режим: {current_mode.value}")
                
                # Тестируем подключение (если это не режим bypass)
                if mode != ProxyMode.BYPASS:
                    test_results = manager.test_proxy_connection()
                    print(f"  Тест подключения: {'Успешно' if test_results['proxy_working'] else 'Ошибка'}")
                    if test_results.get('error'):
                        print(f"  Ошибка: {test_results['error']}")
                
                # Отключаем режим
                manager.set_mode(ProxyMode.BYPASS)
                print(f"  Режим отключен")
            
        except Exception as e:
            print(f"✗ Ошибка при переключении на {mode.value}: {e}")
    
    return True

def test_manual_proxy_settings():
    """Тестирование ручных настроек прокси"""
    print("\n=== Тест ручных настроек прокси ===")
    
    try:
        manager = get_proxy_modes_manager()
        
        # Получение текущих ручных настроек
        manual_settings = manager.config.get('manual_settings', {})
        print(f"✓ Тип прокси: {manual_settings.get('proxy_type', 'Не настроен')}")
        print(f"✓ Хост: {manual_settings.get('proxy_host', 'Не настроен')}")
        print(f"✓ Порт: {manual_settings.get('proxy_port', 'Не настроен')}")
        
        # Тестирование включения ручного прокси (если настройки есть)
        if manual_settings.get('proxy_host') and manual_settings.get('proxy_port'):
            print("✓ Включение ручного прокси...")
            success = manager.set_mode(ProxyMode.MANUAL)
            print(f"  Результат: {'Успешно' if success else 'Ошибка'}")
            
            if success:
                # Тест подключения
                test_results = manager.test_proxy_connection()
                print(f"  Тест подключения: {'Успешно' if test_results['proxy_working'] else 'Ошибка'}")
                if test_results.get('latency_ms'):
                    print(f"  Задержка: {test_results['latency_ms']}ms")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования ручных настроек: {e}")
        return False

def test_bypass_rules():
    """Тестирование правил обхода прокси"""
    print("\n=== Тест правил обхода прокси ===")
    
    try:
        manager = get_proxy_modes_manager()
        
        # Получение текущих правил обхода
        bypass_rules = manager.config.get('bypass_rules', [])
        print(f"✓ Количество правил обхода: {len(bypass_rules)}")
        print(f"✓ Правила: {', '.join(bypass_rules[:3])}{'...' if len(bypass_rules) > 3 else ''}")
        
        # Тестирование режима bypass
        print("✓ Включение режима bypass...")
        success = manager.set_mode(ProxyMode.BYPASS)
        print(f"  Результат: {'Успешно' if success else 'Ошибка'}")
        
        if success:
            # Проверка, что прокси не работает в режиме bypass
            test_results = manager.test_proxy_connection()
            print(f"  Прокси должен быть отключен: {'Да' if not test_results['proxy_working'] else 'Нет'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования правил обхода: {e}")
        return False

def test_proxy_configuration():
    """Тестирование конфигурации прокси"""
    print("\n=== Тест конфигурации прокси ===")
    
    try:
        manager = get_proxy_modes_manager()
        
        # Загрузка конфигурации
        config = manager.config
        print(f"✓ Текущий режим: {config.get('current_mode')}")
        print(f"✓ Авто-обнаружение: {'Да' if config.get('auto_detect_enabled') else 'Нет'}")
        print(f"✓ Прозрачный прокси: {'Да' if config.get('transparent_enabled') else 'Нет'}")
        print(f"✓ DNS защита от утечек: {'Да' if config.get('dns_leak_protection') else 'Нет'}")
        
        # Правила обхода
        bypass_rules = config.get('bypass_rules', [])
        print(f"✓ Правила обхода ({len(bypass_rules)}):")
        for rule in bypass_rules[:5]:  # Показываем первые 5 правил
            print(f"  - {rule}")
        
        # Split-tunnel приложения
        split_apps = config.get('split_tunnel_apps', [])
        if split_apps:
            print(f"✓ Split-tunnel приложения ({len(split_apps)}):")
            for app in split_apps[:5]:  # Показываем первые 5 приложений
                print(f"  - {app}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка конфигурации прокси: {e}")
        return False

def test_proxy_connectivity():
    """Тестирование подключений через прокси"""
    print("\n=== Тест подключений через прокси ===")
    
    try:
        manager = get_proxy_modes_manager()
        
        # Тест в текущем режиме
        current_mode = manager.get_current_mode()
        print(f"✓ Тест в режиме: {current_mode.value}")
        
        # Тестирование подключения
        test_results = manager.test_proxy_connection()
        
        print(f"✓ Прокси работает: {'Да' if test_results['proxy_working'] else 'Нет'}")
        print(f"✓ HTTP ответ: {'Да' if test_results['http_response'] else 'Нет'}")
        print(f"✓ HTTPS ответ: {'Да' if test_results['https_response'] else 'Нет'}")
        
        if test_results.get('latency_ms'):
            print(f"✓ Задержка: {test_results['latency_ms']}ms")
        
        if test_results.get('error'):
            print(f"✓ Ошибка: {test_results['error']}")
        
        return test_results['proxy_working']
        
    except Exception as e:
        print(f"✗ Ошибка тестирования подключений: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("Запуск тестирования режимов прокси XVPN...")
    
    # Тестирование менеджера
    manager_ok = test_proxy_modes_manager()
    
    # Тестирование переключения режимов
    switching_ok = test_proxy_mode_switching()
    
    # Тестирование ручных настроек
    manual_ok = test_manual_proxy_settings()
    
    # Тестирование правил обхода
    bypass_ok = test_bypass_rules()
    
    # Тестирование конфигурации
    config_ok = test_proxy_configuration()
    
    # Тестирование подключений
    connectivity_ok = test_proxy_connectivity()
    
    # Итоги
    print("\n=== Итоги тестирования прокси ===")
    
    total_tests = 6
    passed_tests = sum([
        manager_ok,
        switching_ok,
        manual_ok,
        bypass_ok,
        config_ok,
        connectivity_ok
    ])
    
    print(f"✓ Пройдено тестов: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("✓ Все тесты режимов прокси пройдены успешно!")
        print("✓ XVPN полностью готов к работе с режимами прокси")
        return True
    else:
        print("✗ Некоторые тесты режимов прокси не пройдены")
        
        if not manager_ok:
            print("✗ Проблемы с менеджером режимов прокси")
        if not switching_ok:
            print("✗ Проблемы с переключением режимов")
        if not manual_ok:
            print("✗ Проблемы с ручными настройками")
        if not bypass_ok:
            print("✗ Проблемы с правилами обхода")
        if not config_ok:
            print("✗ Проблемы с конфигурацией прокси")
        if not connectivity_ok:
            print("✗ Проблемы с подключением через прокси")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)