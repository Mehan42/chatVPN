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
import ipv6_manager
import proxy_modes
import os
from vpn_client import get_vpn_client
from state_machine import State, Event
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

        # Инициализация VPN клиента с машиной состояний
        self.client = None
        self.init_client()

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
        
        # Индикатор IPv6 поддержки
        self.ipv6_frame = tk.Frame(self)
        self.ipv6_frame.pack(pady=2)
        
        self.ipv6_lbl = tk.Label(self.ipv6_frame, text="IPv6:", font=("Sans", 11))
        self.ipv6_lbl.pack(side=tk.LEFT)
        
        self.ipv6_indicator = tk.Label(self.ipv6_frame, text="○", font=("Sans", 16), fg="gray")
        self.ipv6_indicator.pack(side=tk.LEFT, padx=5)
        
        self.ipv6_status_lbl = tk.Label(self.ipv6_frame, text="Проверка...", font=("Sans", 11))
        self.ipv6_status_lbl.pack(side=tk.LEFT)
        
        # Индикатор режима прокси
        self.proxy_frame = tk.Frame(self)
        self.proxy_frame.pack(pady=2)
        
        self.proxy_lbl = tk.Label(self.proxy_frame, text="Режим прокси:", font=("Sans", 11))
        self.proxy_lbl.pack(side=tk.LEFT)
        
        self.proxy_mode_lbl = tk.Label(self.proxy_frame, text="Системный", font=("Sans", 11))
        self.proxy_mode_lbl.pack(side=tk.LEFT, padx=5)

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
        if self.client:
            ok, msg = self.client.reload_config()
            print("[INIT]", msg)

        # цикл обновления статуса
        self.after(1500, self.refresh_status_loop)

    def set_tray_icon(self, on: bool):
        img = load_icon(ICON_GREEN_PATH if on else ICON_RED_PATH)
        if img:
            self.current_icon = img
            if self.tray_icon:
                self.tray_icon.icon = img

    def init_client(self):
        """Инициализация VPN клиента"""
        try:
            self.client = get_vpn_client()
            if self.client.initialize():
                # Добавление callback для состояний
                self.client.add_gui_callback(self.on_state_change)
                print("[CLIENT] VPN client initialized with state machine")
            else:
                print("[CLIENT] Failed to initialize VPN client")
                messagebox.showerror("Ошибка", "Не удалось инициализировать VPN клиент")
        except Exception as e:
            print(f"[CLIENT] Error initializing client: {e}")
            messagebox.showerror("Ошибка", f"Ошибка инициализации: {e}")
    
    def on_state_change(self, event_type, context):
        """Callback для изменения состояния"""
        # Обновление GUI в основном потоке
        self.after(0, self.update_gui_state, event_type, context)
    
    def update_gui_state(self, event_type, context):
        """Обновление GUI при изменении состояния"""
        if not self.client:
            return
        
        # Обновление статуса
        state_info = self.client.get_state_info()
        current_state = state_info.get('current_state', 'unknown')
        
        if current_state == 'running':
            self.status_lbl.config(text="Статус: ON")
            self.toggle_btn.config(text="Выключить VPN")
            self.set_tray_icon(True)
        else:
            self.status_lbl.config(text="Статус: OFF")
            self.toggle_btn.config(text="Включить VPN")
            self.set_tray_icon(False)
        
        # Обновление индикатора безопасности
        try:
            health_score = self.client.get_health_score()
            self.update_security_indicator(health_score)
        except:
            self.security_indicator.config(fg="gray")
            self.security_score_lbl.config(text="Оценка: -")
        
        # Обновление информации о сети
        try:
            network_info = self.client.get_network_info()
            
            # IPv4 информация
            ipv4 = network_info.get("external_ips", {}).get("ipv4", "-")
            self.ip_lbl.config(text=f"IPv4: {ipv4}")
            
            # IPv6 информация
            ipv6 = network_info.get("external_ips", {}).get("ipv6", "-")
            if ipv6 != "-":
                self.ipv6_lbl.config(text=f"IPv6: {ipv6}")
                self.ipv6_lbl.config(fg="green")  # Зеленый цвет для активного IPv6
            else:
                self.ipv6_lbl.config(text="IPv6: Не поддерживается")
                self.ipv6_lbl.config(fg="gray")  # Серый цвет для неактивного IPv6
                
        except Exception as e:
            self.ip_lbl.config(text="IPv4: Ошибка")
            self.ipv6_lbl.config(text="IPv6: Ошибка")
        
        # Обновление скорости
        try:
            rx, tx = be.get_speed()
            self.speed_lbl.config(text=f"Скорость: {rx} ↓ / {tx} ↑ КБ/с")
        except:
            self.speed_lbl.config(text="Скорость: Ошибка")
    
    def update_security_indicator(self):
        """Обновление индикатора безопасности на основе оценки маскировки"""
        try:
            health_score = self.client.get_health_score()
            
            # Определяем цвет и статус на основе оценки
            if health_score >= 4:
                color = "green"
                status_text = "Отлично"
            elif health_score >= 3:
                color = "yellow"
                status_text = "Хорошо"
            elif health_score >= 1:
                color = "orange"
                status_text = "Внимание"
            else:
                color = "red"
                status_text = "Критично"
            
            self.security_indicator.config(fg=color)
            self.security_score_lbl.config(text=f"Оценка: {health_score}/5 ({status_text})")
            
        except Exception as e:
            print(f"Error updating security indicator: {e}")
            self.security_indicator.config(fg="gray")
            self.security_score_lbl.config(text="Оценка: -")
        
        # Обновляем индикатор IPv6
        self.update_ipv6_indicator()
    
    def update_ipv6_indicator(self):
        """Обновление индикатора IPv6 поддержки"""
        try:
            ipv6_mgr = ipv6_manager.get_ipv6_manager()
            ipv6_status = ipv6_mgr.get_ipv6_connectivity_status()
            
            if ipv6_status['ipv6_supported']:
                if ipv6_status['ipv6_connectivity']:
                    color = "green"
                    status_text = "Активен"
                elif ipv6_status['ipv6_enabled']:
                    color = "yellow"
                    status_text = "Поддерживается"
                else:
                    color = "gray"
                    status_text = "Отключен"
            else:
                color = "red"
                status_text = "Не поддерживается"
            
            self.ipv6_indicator.config(fg=color)
            self.ipv6_status_lbl.config(text=status_text)
            
        except Exception as e:
            print(f"Error updating IPv6 indicator: {e}")
            self.ipv6_indicator.config(fg="gray")
            self.ipv6_status_lbl.config(text="Ошибка")
        
        # Обновляем индикатор режима прокси
        self.update_proxy_mode_indicator()
    
    def update_proxy_mode_indicator(self):
        """Обновление индикатора режима прокси"""
        try:
            proxy_mgr = proxy_modes.get_proxy_modes_manager()
            mode_info = proxy_mgr.get_mode_info()
            
            # Определяем цвет и текст на основе режима
            current_mode = proxy_mgr.get_current_mode()
            mode_name = current_mode.value
            
            # Цветовая индикация
            if current_mode.value == 'bypass':
                color = "green"
                mode_text = "Обход"
            elif current_mode.value == 'system':
                color = "blue"
                mode_text = "Системный"
            elif current_mode.value == 'manual':
                color = "orange"
                mode_text = "Ручной"
            elif current_mode.value == 'transparent':
                color = "purple"
                mode_text = "Прозрачный"
            elif current_mode.value == 'split':
                color = "teal"
                mode_text = "Split-tunnel"
            else:
                color = "gray"
                mode_text = "Авто"
            
            self.proxy_mode_lbl.config(text=mode_text, fg=color)
            
        except Exception as e:
            print(f"Error updating proxy mode indicator: {e}")
            self.proxy_mode_lbl.config(text="Ошибка", fg="gray")
    
    def on_toggle(self):
        """Переключение VPN через state machine"""
        if not self.client:
            if not self.init_client():
                return
        
        try:
            if self.client.is_running():
                if self.client.stop_vpn():
                    messagebox.showinfo("ChatVPN", "VPN останавливается...")
                else:
                    messagebox.showerror("ChatVPN", "Не удалось остановить VPN")
            else:
                if self.client.start_vpn():
                    messagebox.showinfo("ChatVPN", "VPN запускается...")
                else:
                    messagebox.showerror("ChatVPN", "Не удалось запустить VPN")
        except Exception as e:
            messagebox.showerror("ChatVPN", f"Ошибка: {e}")

    def on_fetch_config(self):
        """Обновление конфигурации через state machine"""
        if not self.client:
            if not self.init_client():
                return
        
        try:
            if self.client.reload_config():
                messagebox.showinfo("ChatVPN", "Конфигурация обновляется...")
            else:
                messagebox.showerror("ChatVPN", "Не удалось обновить конфигурацию")
        except Exception as e:
            messagebox.showerror("ChatVPN", f"Ошибка обновления: {e}")

    def on_change_uuid(self):
        """Смена UUID клиента"""
        uuid = simpledialog.askstring("Смена UUID", "Введите новый Client UUID:")
        if uuid:
            try:
                # Создаем новый клиент с новым UUID
                self.client = get_vpn_client(uuid)
                if self.client.initialize():
                    be.save_client_uuid(uuid)
                    messagebox.showinfo("ChatVPN", f"UUID изменён на:\n{uuid}")
                else:
                    messagebox.showerror("ChatVPN", "Не удалось инициализировать новый клиент")
            except Exception as e:
                messagebox.showerror("ChatVPN", f"Ошибка смены UUID: {e}")

    
    def refresh_status(self):
        """Обновление статуса через VPN клиент"""
        if not self.client:
            return
        
        try:
            # Обновление состояния через client
            self.update_gui_state("refresh", None)
            
            # Обновление индикатора безопасности
            self.update_security_indicator()
        except Exception as e:
            print(f"Error refreshing status: {e}")

    def refresh_status_loop(self):
        self.refresh_status()
        self.after(5000, self.refresh_status_loop)  # Обновляем каждые 5 секунд для безопасности

if __name__ == "__main__":
    app = App()
    app.mainloop()
