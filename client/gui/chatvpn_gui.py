#!/usr/bin/env python3
# GUI для ChatVPN клиента (гибридная схема)
# Абсолютный путь: ~/chatvpn/client/chatvpn_gui.py

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
from PIL import Image
import pystray
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chatvpn_backend as be
import os
# Установка бэкенда pystray в зависимости от платформы
if sys.platform.startswith('linux'):
    os.environ["PYSTRAY_BACKEND"] = "xorg"
elif sys.platform.startswith('win'):
    os.environ["PYSTRAY_BACKEND"] = "win32"
elif sys.platform.startswith('darwin'):
    os.environ["PYSTRAY_BACKEND"] = "quartz"

ICON_GREEN_PATH = os.path.expanduser("~/chatvpn/client/icon_green.png")
ICON_RED_PATH   = os.path.expanduser("~/chatvpn/client/icon_red.png")

def load_icon(path):
    try:
        img = Image.open(path)
        return img.resize((128, 128))   # крупная иконка
    except:
        return None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatVPN")
        self.geometry("420x320")
        self.resizable(False, False)

        # проверка UUID
        if not be.get_client_uuid():
            uuid = simpledialog.askstring("Регистрация", "Введите ваш Client UUID:")
            if uuid:
                be.save_client_uuid(uuid)

        # метки
        self.status_lbl = tk.Label(self, text="Статус: OFF", font=("Sans", 12))
        self.status_lbl.pack(pady=8)

        self.ip_lbl = tk.Label(self, text="IP: -", font=("Sans", 11))
        self.ip_lbl.pack(pady=4)

        self.speed_lbl = tk.Label(self, text="Скорость: 0 ↓ / 0 ↑ КБ/с", font=("Sans", 11))
        self.speed_lbl.pack(pady=4)

        # кнопки
        self.toggle_btn = tk.Button(self, text="Включить VPN", width=20, command=self.on_toggle)
        self.toggle_btn.pack(pady=10)

        self.cfg_btn = tk.Button(self, text="Запросить конфиг", width=20, command=self.on_fetch_config)
        self.cfg_btn.pack(pady=6)

        self.uuid_btn = tk.Button(self, text="Сменить UUID", width=20, command=self.on_change_uuid)
        self.uuid_btn.pack(pady=6)

        # создаём трэй-иконку
        self.current_icon = load_icon(ICON_RED_PATH)
        self.tray_icon = pystray.Icon("ChatVPN", self.current_icon, "ChatVPN")
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

        # автозагрузка client.json при старте
        ok, msg = be.load_config()
        print("[INIT]", msg)

        # цикл обновления статуса
        self.after(1500, self.refresh_status_loop)

    def set_tray_icon(self, on: bool):
        img = load_icon(ICON_GREEN_PATH if on else ICON_RED_PATH)
        if img:
            self.current_icon = img
            if self.tray_icon:
                self.tray_icon.icon = img

    def on_toggle(self):
        if be.is_running():
            ok, msg = be.stop_vpn()
            self.toggle_btn.config(text="Включить VPN")
        else:
            ok, msg = be.start_vpn()
            self.toggle_btn.config(text="Выключить VPN")
        messagebox.showinfo("ChatVPN", msg)
        self.refresh_status()

    def on_fetch_config(self):
        ok, msg = be.load_config()
        messagebox.showinfo("ChatVPN", msg)

    def on_change_uuid(self):
        uuid = simpledialog.askstring("Смена UUID", "Введите новый Client UUID:")
        if uuid:
            be.save_client_uuid(uuid)
            messagebox.showinfo("ChatVPN", f"UUID изменён на:\n{uuid}")

    def refresh_status(self):
        running = be.is_running()
        self.status_lbl.config(text="Статус: ON" if running else "Статус: OFF")
        self.set_tray_icon(running)
        ip = be.get_ip() if running else "-"
        self.ip_lbl.config(text=f"IP: {ip}")
        rx, tx = be.get_speed()
        self.speed_lbl.config(text=f"Скорость: {rx} ↓ / {tx} ↑ КБ/с")

    def refresh_status_loop(self):
        self.refresh_status()
        self.after(2000, self.refresh_status_loop)

if __name__ == "__main__":
    app = App()
    app.mainloop()
