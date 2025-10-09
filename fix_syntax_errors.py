#!/usr/bin/env python3
"""
Скрипт для исправления синтаксических ошибок в Python файлах клиента,
в основном вызванных неправильной заменой кавычек и скобок при обновлении путей.
"""

import os
import re
from pathlib import Path

def fix_common_errors_in_file(file_path):
    """Исправляет часто встречающиеся синтаксические ошибки в файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines[:]
    fixed_count = 0
    
    for i, line in enumerate(lines):
        # Исправление неправильных кавычек: "path' / 'filename" -> "path" / "filename"
        fixed_line = re.sub(r'"([^"]*)\' / \'([^"]*)"', r'"\1" / "\2"', line)
        
        # Исправление лишних закрывающих скобок
        fixed_line = re.sub(r'(CLIENT_DIR / "[^"]*" / "[^"]*"\))', r'\1', fixed_line)
        
        # Удаление дублирующихся строк (если встречается одна и та же строка подряд)
        if i > 0 and fixed_line == lines[i-1]:
            lines[i] = ""  # Помечаем для удаления
            fixed_count += 1
            continue
        
        if fixed_line != line:
            lines[i] = fixed_line
            fixed_count += 1
    
    # Удаляем пустые строки, которые мы отметили для удаления
    lines = [line for line in lines if line != ""]
    
    if lines != original_lines:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Исправлено {fixed_count} ошибок в файле: {file_path}")
        return True
    
    if fixed_count > 0:
        print(f"Исправлено {fixed_count} ошибок в файле: {file_path}")
        return True
    
    return False

def main():
    client_dir = Path(__file__).parent / 'client'
    
    # Найти все Python файлы в клиентской директории
    py_files = list(client_dir.rglob('*.py'))
    
    print(f"Найдено {len(py_files)} Python файлов для проверки")
    
    fixed_files_count = 0
    for file_path in py_files:
        try:
            if fix_common_errors_in_file(file_path):
                fixed_files_count += 1
        except Exception as e:
            print(f"Ошибка при обработке файла {file_path}: {e}")
    
    print(f"Исправлено {fixed_files_count} файлов")

if __name__ == '__main__':
    main()