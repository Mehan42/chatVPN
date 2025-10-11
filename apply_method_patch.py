#!/usr/bin/env python3
"""
Скрипт для замены метода reload_config в файле vpn_client.py
"""

def replace_reload_config_method():
    # Читаем оригинальный файл
    with open('client/vpn_client_original.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим начало и конец метода reload_config
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if line.strip() == 'def reload_config(self) -> bool:':
            start_line = i
        elif start_line is not None and line.strip() == 'def get_client_uuid(self) -> str:':
            end_line = i
            break
    
    if start_line is None or end_line is None:
        print("Ошибка: не найдены границы метода reload_config")
        return False
    
    # Читаем патч метода
    with open('method_patch.txt', 'r', encoding='utf-8') as f:
        patch_lines = f.readlines()
    
    # Заменяем метод
    result_lines = lines[:start_line] + patch_lines + lines[end_line-1:]
    
    # Записываем результат
    with open('client/vpn_client.py', 'w', encoding='utf-8') as f:
        f.writelines(result_lines)
    
    print("Метод reload_config успешно заменен")
    return True

if __name__ == '__main__':
    replace_reload_config_method()