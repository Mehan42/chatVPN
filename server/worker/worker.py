#!/usr/bin/env python3
"""XVPN Worker Stub"""

import time
import sys
from pathlib import Path

def main():
    print("XVPN Worker Started")
    # Создаем необходимые директории
    Path("/var/log/xvpn").mkdir(parents=True, exist_ok=True)
    
    # Простой цикл работы воркера
    try:
        while True:
            print("Worker running...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("Worker stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main())
