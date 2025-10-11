#!/usr/bin/env python3
# Log analyzer for ChatVPN client

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import sys
# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()


def analyze_health_logs(days=1):
    """Анализ логов здоровья за последние N дней"""
    health_log_path = CLIENT_DIR / "logs' / 'health.log'

    if not health_log_path.exists():
        print("Файл лога здоровья не найден")
        return None

    cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
    logs = []

    try:
        with open(health_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get('timestamp', 0) >= cutoff_time:
                      logs.append(log_entry)
                except json.JSONDecodeError:
                    continue  # Пропускаем некорректные строки

    except Exception as e:
        print(f"Ошибка чтения логов: {e}")
        return None

    if not logs:
        print(f"Нет логов за последние {days} дней")
        return None

    # Анализ
    total_logs = len(logs)
    avg_score = sum(log['mask_score'] for log in logs) / len(logs)
    min_score = min(log['mask_score'] for log in logs)
    max_score = max(log['mask_score'] for log in logs)

    # Подсчет утечек IP
    ip_leak_count = sum(1 for log in logs if not log.get('ip_leak', True))

    # Подсчет времени с низкой оценкой (ниже 3)
    low_score_count = sum(1 for log in logs if log['mask_score'] < 3)

    analysis = {
        'period_days': days,
        'total_records': total_logs,
        'average_score': round(avg_score, 2),
        'min_score': min_score,
        'max_score': max_score,
        'ip_leak_events': ip_leak_count,
        'low_score_events': low_score_count,
        'reliability_percent': round(((total_logs - low_score_count) / total_logs) * 100, 2)
    }

    return analysis

def analyze_state_logs(days=1):
    """Анализ логов состояния за последние N дней"""
    state_log_path = CLIENT_DIR / "logs' / 'state.log'

    if not state_log_path.exists():
        print("Файл лога состояния не найден")
        return None

    cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
    logs = []

    try:
        with open(state_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get('timestamp', 0) >= cutoff_time:
                        logs.append(log_entry)
                except json.JSONDecodeError:
                    continue  # Пропускаем некорректные строки

    except Exception as e:
        print(f"Ошибка чтения логов состояния: {e}")
        return None

    if not logs:
        print(f"Нет логов состояния за последние {days} дней")
        return None

    # Подсчет состояний
    state_counts = {}
    for log in logs:
        state = log.get('state', 'UNKNOWN')
        state_counts[state] = state_counts.get(state, 0) + 1

    # Подсчет событий ошибок
    error_count = sum(1 for log in logs if 'ERROR' in log.get('message', '').upper())

    analysis = {
        'period_days': days,
        'total_records': len(logs),
        'state_distribution': state_counts,
        'error_events': error_count,
        'states_count': len(state_counts)
    }

    return analysis

def generate_report(days=7):
    """Генерация полного отчета"""
    print(f"=== Отчет за последние {days} дней ===\n")

    # Анализ здоровья
    health_analysis = analyze_health_logs(days)
    if health_analysis:
        print("📊 Мониторинг здоровья:")
        print(f"  Записей: {health_analysis['total_records']}")
        print(f"  Средняя оценка маскировки: {health_analysis['average_score']}/5")
        print(f"  Мин/Макс: {health_analysis['min_score']}/{health_analysis['max_score']}")
        print(f"  Событий утечки IP: {health_analysis['ip_leak_events']}")
        print(f"  Низкий уровень маскировки: {health_analysis['low_score_events']} раз")
        print(f"  Надежность: {health_analysis['reliability_percent']}%")
        print()

    # Анализ состояния
    state_analysis = analyze_state_logs(days)
    if state_analysis:
        print("🔄 Анализ состояний:")
        print(f"  Записей: {state_analysis['total_records']}")
        print(f"  Состояний: {state_analysis['states_count']}")
        print(f"  Ошибок: {state_analysis['error_events']}")
        print("  Распределение состояний:")
        for state, count in state_analysis['state_distribution'].items():
            print(f"    {state}: {count}")
        print()

    if not health_analysis and not state_analysis:
        print("Нет данных для анализа")

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    generate_report(days)
