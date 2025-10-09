#!/usr/bin/env python3
"""
Скрипт для обновления жестко заданных путей ~/chatvpn/client в файлах клиента
на относительные пути от директории скрипта.
"""
import os
import re
from pathlib import Path

def update_file_paths(file_path):
    """Обновляет пути в указанном файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, содержит ли файл проблематичные пути
    if '~/chatvpn/client/' not in content and 'Path.home() / \'chatvpn\' / \'client\'' not in content:
        print(f"Файл {file_path} не содержит проблемных путей, пропускаем")
        return False
    
    # Сохраняем оригинальное содержимое для сравнения
    original_content = content
    
    # Обновляем комментарии
    content = content.replace(
        '# Абсолютный путь: ~/chatvpn/client/',
        '# Абсолютный путь: ~/chatvpn/client/ (может быть переустановлен в другое место)'
    )
    
    # Добавляем импорт pathlib и определение CLIENT_DIR, если его нет
    if 'CLIENT_DIR = ' not in content:
        # Добавляем импорт pathlib и определение CLIENT_DIR после import блока
        import_section_end = content.find('\n', content.find('import pathlib')) if 'import pathlib' in content else content.find('\n\n', content.find('import os'))
        
        if import_section_end == -1:
            # Если не нашли явного места, добавим после первой строки import
            import_match = re.search(r'^import .*\n|^from .*\n', content, re.MULTILINE)
            if import_match:
                import_section_end = import_match.end()
                # Найдем конец блока импортов
                next_content = content[import_section_end:]
                # Ищем место до следующего блока (объявление класса/функции)
                lines = next_content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith(' ') and not line.startswith('#') and not line.startswith('import') and not line.startswith('from'):
                        import_section_end += sum(len(l) + 1 for l in lines[:i])
                        break
                else:
                    import_section_end = content.find('\n\n', import_section_end) or len(content)
            else:
                import_section_end = content.find('\n') + 1  # После первой строки
        
        if import_section_end != -1:
            # Проверяем, есть ли уже этот импорт
            if 'from pathlib import Path' not in content:
                content = content[:import_section_end] + 'from pathlib import Path\n\n' + content[import_section_end:]
                import_section_end += len('from pathlib import Path\n')
            
            # Добавляем определение CLIENT_DIR если его нет
            if 'CLIENT_DIR = ' not in content:
                client_dir_def = '\n# Определяем базовую директорию как директорию скрипта\nCLIENT_DIR = Path(__file__).parent if \'__file__\' in globals() else Path.cwd()\n\n'
                content = content[:import_section_end] + client_dir_def + content[import_section_end:]
    
    # Заменяем все проблемные пути
    replacements = [
        # Замены для expanduser
        ('os.path.expanduser("~/chatvpn/client/', 'CLIENT_DIR / "'),
        
        # Замены для Path.home()
        ('Path.home() / \'chatvpn\' / \'client\' / \'', 'CLIENT_DIR / "'),
        ('Path.home() / "chatvpn" / "client" / "', 'CLIENT_DIR / "'),
        ('Path.home() / \'chatvpn\' / \'client\' / "client.json"', 'CLIENT_DIR / "client.json"'),
        ('Path.home() / "chatvpn" / "client" / "client.json"', 'CLIENT_DIR / "client.json"'),
        ('Path.home() / \'chatvpn\' / \'client\' / "logs"', 'CLIENT_DIR / "logs"'),
        ('Path.home() / "chatvpn" / "client" / "logs"', 'CLIENT_DIR / "logs"'),
        ('Path.home() / \'chatvpn\' / \'client\' / "states"', 'CLIENT_DIR / "states"'),
        ('Path.home() / "chatvpn" / "client" / "states"', 'CLIENT_DIR / "states"'),
        ('Path.home() / \'chatvpn\' / \'client\' / "transports"', 'CLIENT_DIR / "transports"'),
        ('Path.home() / "chatvpn" / "client" / "transports"', 'CLIENT_DIR / "transports"'),
        ('Path.home() / \'chatvpn\' / \'client\' / "ipv6_config.json"', 'CLIENT_DIR / "ipv6_config.json"'),
        ('Path.home() / "chatvpn" / "client" / "ipv6_config.json"', 'CLIENT_DIR / "ipv6_config.json"'),
        ('Path.home() / \'chatvpn\' / \'client\' / "proxy_modes_config.json"', 'CLIENT_DIR / "proxy_modes_config.json"'),
        ('Path.home() / "chatvpn" / "client" / "proxy_modes_config.json"', 'CLIENT_DIR / "proxy_modes_config.json"'),
    ]
    
    for old_path, new_path in replacements:
        content = content.replace(old_path, new_path)
    
    # Если были изменения, записываем файл
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Обновлен файл: {file_path}")
        return True
    else:
        print(f"Файл {file_path} не требует обновления")
        return False

def main():
    client_dir = Path(__file__).parent / 'client'
    
    # Найти все Python файлы в клиентской директории
    py_files = list(client_dir.rglob('*.py'))
    
    updated_count = 0
    
    for file_path in py_files:
        try:
            if update_file_paths(file_path):
                updated_count += 1
        except Exception as e:
            print(f"Ошибка при обновлении файла {file_path}: {e}")
    
    print(f"\nОбновлено {updated_count} файлов")
    
    # Проверим, остались ли необработанные файлы
    remaining_files = []
    for file_path in py_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '~/chatvpn/client/' in content or 'Path.home() / \'chatvpn\' / \'client\'' in content:
                remaining_files.append(file_path)
    
    if remaining_files:
        print(f"\nОстались файлы с проблемными путями: {len(remaining_files)}")
        for f in remaining_files:
            print(f"  - {f}")
    else:
        print("\nВсе файлы успешно обновлены!")

if __name__ == '__main__':
    main()