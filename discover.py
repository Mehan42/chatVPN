import socket
import time
import json
from pathlib import Path


# Определяем базовую директорию как директорию скрипта
CLIENT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()

def test_ipv4_connectivity(host, port, timeout=5):
    """Тестирование IPv4 подключения"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()

        rtt = round((end_time - start_time) * 1000, 2)  # в миллисекундах
        return result == 0, rtt
    except Exception:
        return False, None

def test_ipv6_connectivity(host, port, timeout=5):
    """Тестирование IPv6 подключения"""
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()

        rtt = round((end_time - start_time) * 1000, 2)  # в миллисекундах
        return result == 0, rtt
    except Exception:
        return False, None

def discover_transports(manifest_path=None):
    """Обнаружение доступных транспортов с проверкой IPv4/IPv6.
    
    Args:
        manifest_path: Путь к файлу манифеста транспортов.
                     Если None, используется путь по умолчанию.
    
    Returns:
        Список результатов обнаружения транспортов с оценками.
    """
    if manifest_path is None:
        manifest_path = CLIENT_DIR / "transports" / "manifest.json"

    if not manifest_path.exists():
        print("Manifest file not found")
        return []

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return []

    results = []
    transports = manifest_data.get("transports", [])

    for transport in transports:
        host = transport["config"]["server"]
        port = transport["config"]["port"]

        # Проверка IPv4
        ipv4_success, ipv4_rtt = test_ipv4_connectivity(host, port)

        # Проверка IPv6
        ipv6_success, ipv6_rtt = test_ipv6_connectivity(host, port)

        # Оценка транспорта
        score = 0
        if ipv4_success:
            score += 2
        if ipv6_success:
            score += 2
        if ipv4_rtt and ipv4_rtt < 200:  # RTT < 200ms
            score += 1
        if ipv6_rtt and ipv6_rtt < 200:  # RTT < 200ms
            score += 1

        transport_result = {
            "transport": transport,
            "ipv4_available": ipv4_success,
            "ipv4_rtt": ipv4_rtt,
            "ipv6_available": ipv6_success,
            "ipv6_rtt": ipv6_rtt,
            "score": score,
            "preferred_family": None
        }

        # Выбираем предпочтительный протокол (IPv4 приоритетнее если оба доступны)
        if ipv4_success and ipv6_success:
            transport_result["preferred_family"] = (
                "ipv4" if ipv4_rtt <= ipv6_rtt else "ipv6"
            )
        elif ipv4_success:
            transport_result["preferred_family"] = "ipv4"
        elif ipv6_success:
            transport_result["preferred_family"] = "ipv6"

        results.append(transport_result)

    # Сортировка по оценке (от лучшего к худшему)
    results.sort(key=lambda x: x["score"], reverse=True)

    return results

if __name__ == "__main__":
    results = discover_transports()

    print("=== Discovery Results ===")
    for i, result in enumerate(results, 1):
        transport = result["transport"]
        print(f"\n{i}. {transport['name']} (ID: {transport['id']})")
        print(f"   Score: {result['score']}/5")
        ipv4_display = (
            f"{'✓' if result['ipv4_available'] else '✗'} "
            f"({result['ipv4_rtt']} ms)"
        ) if result['ipv4_rtt'] else f"{'✓' if result['ipv4_available'] else '✗'}"
        print(f"   IPv4: {ipv4_display}")
        
        ipv6_display = (
            f"{'✓' if result['ipv6_available'] else '✗'} "
            f"({result['ipv6_rtt']} ms)"
        ) if result['ipv6_rtt'] else f"{'✓' if result['ipv6_available'] else '✗'}"
        print(f"   IPv6: {ipv6_display}")
        
        print(f"   Preferred: {result['preferred_family'] or 'None'}")

    if results:
        print(f"\nBest choice: {results[0]['transport']['name']}")
    else:
        print("\nNo available transports found.")
