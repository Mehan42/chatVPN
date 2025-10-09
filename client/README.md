# XVPN Client

[English](#english) | [Русский](#russian)

---

## English

Client component of the XVPN system.

### Installation and "out-of-the-box" startup

1. Clone the repository:
   ```bash
   git clone https://github.com/Mehan42/chatVPN.git
   cd chatVPN
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements_client.txt
   ```

3. Run the client:
   ```bash
   python3 client/chatvpn_gui.py
   ```

### Flexible Installation

For installation in custom directories:
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client
```

Then run:
```bash
cd /opt/my_xvpn_client
python3 run_client.py
```

### Configuration

The client configuration is stored in `client.json` and `client.conf` files.
The client UUID is automatically generated on first run and saved to `client.conf`.

### Dependencies

- Python 3.10+
- tkinter (for GUI)
- requests
- Pillow (for icons)
- pystray (for tray icon)

---

## Russian

Клиентская часть системы XVPN.

### Установка и запуск "из коробки"

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Mehan42/chatVPN.git
   cd chatVPN
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements_client.txt
   ```

3. Запустите клиент:
   ```bash
   python3 client/chatvpn_gui.py
   ```

### Гибкая установка

Для установки в произвольные директории:
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client
```

Затем запустите:
```bash
cd /opt/my_xvpn_client
python3 run_client.py
```

### Конфигурация

Конфигурация клиента хранится в файлах `client.json` и `client.conf`.
UUID клиента автоматически генерируется при первом запуске и сохраняется в `client.conf`.

### Зависимости

- Python 3.10+
- tkinter (для GUI)
- requests
- Pillow (для иконок)
- pystray (для иконки в трее)