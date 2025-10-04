#!/usr/bin/env python3
"""XVPN Agent Stub"""

import time
import sys
from pathlib import Path

def main():
    print("XVPN Agent Started")
    # Создаем необходимые директории
    Path("/var/log/xvpn").mkdir(parents=True, exist_ok=True)
    Path("/opt/xvpn/data").mkdir(parents=True, exist_ok=True)
    
    # Простой цикл работы агента
    try:
        while True:
            print("Agent running...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("Agent stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main())
