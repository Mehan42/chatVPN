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
import health
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

        # Индикатор безопасности (светофор)
        self.security_frame = tk.Frame(self)
        self.security_frame.pack(pady=4)
        
        self.security_lbl = tk.Label(self.security_frame, text="Безопасность:", font=("Sans", 11))
        self.security_lbl.pack(side=tk.LEFT)
        
        self.security_indicator = tk.Label(self.security_frame, text="●", font=("Sans", 20), fg="gray")
        self.security_indicator.pack(side=tk.LEFT, padx=5)
        
        self.security_score_lbl = tk.Label(self.security_frame, text="Оценка: -", font=("Sans", 11))
        self.security_score_lbl.pack(side=tk.LEFT)

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

    def update_security_indicator(self):
        """Обновление индикатора безопасности на основе оценки маскировки"""
        try:
            mask_score = health.get_mask_score()
            
            # Определяем цвет и статус на основе оценки
            if mask_score >= 4:
                color = "green"
                status_text = "Отлично"
            elif mask_score >= 3:
                color = "yellow"
                status_text = "Хорошо"
            elif mask_score >= 1:
                color = "orange"
                status_text = "Внимание"
            else:
                color = "red"
                status_text = "Критично"
            
            self.security_indicator.config(fg=color)
            self.security_score_lbl.config(text=f"Оценка: {mask_score}/5 ({status_text})")
            
        except Exception as e:
            print(f"Error updating security indicator: {e}")
            self.security_indicator.config(fg="gray")
            self.security_score_lbl.config(text="Оценка: -")
    
    def refresh_status(self):
        running = be.is_running()
        self.status_lbl.config(text="Статус: ON" if running else "Статус: OFF")
        self.set_tray_icon(running)
        ip = be.get_ip() if running else "-"
        self.ip_lbl.config(text=f"IP: {ip}")
        rx, tx = be.get_speed()
        self.speed_lbl.config(text=f"Скорость: {rx} ↓ / {tx} ↑ КБ/с")
        
        # Обновляем индикатор безопасности
        self.update_security_indicator()

    def refresh_status_loop(self):
        self.refresh_status()
        self.after(5000, self.refresh_status_loop)  # Обновляем каждые 5 секунд для безопасности

if __name__ == "__main__":
    app = App()
    app.mainloop()
