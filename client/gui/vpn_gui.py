
#!/usr/bin/env python3
# Улучшенный GUI для XVPN с интеграцией state machine
# Абсолютный путь: ~/chatvpn/client/gui/vpn_gui.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Импорт модулей
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from vpn_client import get_vpn_client
from state_machine import State, Event

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XVPNGUI:
    """Улучшенный GUI для XVPN с интеграцией state machine"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("XVPN Client")
        self.root.geometry("800x600")
        
        # Инициализация клиента
        self.client = None
        self.client_uuid = None
        self.update_thread = None
        self.running = False
        
        # Цветовая схема
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#4CAF50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196f3'
        }
        
        # Создание интерфейса
        self.setup_ui()
        
        # Запуск обновления статуса
        self.start_status_update()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Главная рамка
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="XVPN Client", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        self.uuid_label = ttk.Label(title_frame, text="UUID: --", 
                                   font=('Arial', 10))
        self.uuid_label.pack(side=tk.RIGHT)
        
        # Основной контейнер с вкладками
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка Статус
        self.setup_status_tab()
        
        # Вкладка Управление
        self.setup_control_tab()
        
        # Вкладка Сеть
        self.setup_network_tab()
        
        # Вкладка Транспорт
        self.setup_transport_tab()
        
        # Вкладка Логи
        self.setup_logs_tab()
        
        # Статусная строка
        self.setup_status_bar()
    
    def setup_status_tab(self):
        """Настройка вкладки Статус"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="Статус")
        
        # Состояние VPN
        vpn_frame = ttk.LabelFrame(status_frame, text="VPN Состояние", padding=10)
        vpn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Текущее состояние
        state_frame = ttk.Frame(vpn_frame)
        state_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(state_frame, text="Текущее состояние:").pack(side=tk.LEFT)
        self.state_label = ttk.Label(state_frame, text="Не инициализирован", 
                                    font=('Arial', 12, 'bold'))
        self.state_label.pack(side=tk.RIGHT)
        
        # Цвет индикатора состояния
        self.state_indicator = tk.Canvas(vpn_frame, width=20, height=20, 
                                        bg='gray', highlightthickness=0)
        self.state_indicator.pack(anchor=tk.W, pady=(0, 5))
        self.update_state_indicator('gray')
        
        # Информация о состоянии
        self.state_info = scrolledtext.ScrolledText(vpn_frame, height=8, 
                                                   wrap=tk.WORD)
        self.state_info.pack(fill=tk.X, pady=(0, 5))
        
        # Оценка здоровья
        health_frame = ttk.LabelFrame(status_frame, text="Здоровье", padding=10)
        health_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Оценка маскировки
        mask_frame = ttk.Frame(health_frame)
        mask_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(mask_frame, text="Оценка маскировки:").pack(side=tk.LEFT)
        self.health_score_label = ttk.Label(mask_frame, text="--", 
                                          font=('Arial', 14, 'bold'))
        self.health_score_label.pack(side=tk.RIGHT)
        
        # Индикатор здоровья
        self.health_canvas = tk.Canvas(health_frame, width=200, height=20, 
                                     bg='gray', highlightthickness=1)
        self.health_canvas.pack(fill=tk.X, pady=(0, 5))
        
        # Информация о сети
        self.network_info_text = scrolledtext.ScrolledText(health_frame, height=6, 
                                                          wrap=tk.WORD)
        self.network_info_text.pack(fill=tk.X)
    
    def setup_control_tab(self):
        """Настройка вкладки Управление"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Управление")
        
        # Кнопки управления
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Запуск VPN", 
                                      command=self.start_vpn)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Остановка VPN", 
                                     command=self.stop_vpn, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.config_button = ttk.Button(button_frame, text="Обновить конфиг", 
                                       command=self.reload_config)
        self.config_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Сменить UUID", 
                  command=self.change_uuid).pack(side=tk.RIGHT)
        
        # Информация о клиенте
        info_frame = ttk.LabelFrame(control_frame, text="Информация о клиенте", 
                                   padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        self.client_info_text = scrolledtext.ScrolledText(info_frame, 
                                                         wrap=tk.WORD)
        self.client_info_text.pack(fill=tk.BOTH, expand=True)
        
        # История состояний
        history_frame = ttk.LabelFrame(control_frame, text="История состояний", 
                                      padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.history_tree = ttk.Treeview(history_frame, columns=('time', 'event'), 
                                        height=8)
        self.history_tree.heading('#0', text='Состояние')
        self.history_tree.heading('time', text='Время')
        self.history_tree.heading('event', text='Событие')
        self.history_tree.column('#0', width=150)
        self.history_tree.column('time', width=150)
        self.history_tree.column('event', width=200)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Добавить scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                 command=self.history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
    
    def setup_network_tab(self):
        """Настройка вкладки Сеть"""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="Сеть")
        
        # Информация о сети
        info_frame = ttk.LabelFrame(network_frame, text="Информация о сети", 
                                   padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.network_details_text = scrolledtext.ScrolledText(info_frame, 
                                                             wrap=tk.WORD)
        self.network_details_text.pack(fill=tk.BOTH, expand=True)
        
        # Проверка соединения
        test_frame = ttk.LabelFrame(network_frame, text="Тесты соединения", 
                                   padding=10)
        test_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(test_frame, text="Проверить DNS", 
                  command=self.test_dns).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(test_frame, text="Проверить IP", 
                  command=self.test_ip).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(test_frame, text="Проверить TLS", 
                  command=self.test_tls).pack(side=tk.LEFT)
        
        # Результаты тестов
        self.test_results_text = scrolledtext.ScrolledText(network_frame, 
                                                          height=8, wrap=tk.WORD)
        self.test_results_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_transport_tab(self):
        """Настройка вкладки Транспорт"""
        transport_frame = ttk.Frame(self.notebook)
        self.notebook.add(transport_frame, text="Транспорт")
        
        # Доступные транспорты
        available_frame = ttk.LabelFrame(transport_frame, text="Доступные транспорты", 
                                        padding=10)
        available_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview для транспортов
        self.transport_tree = ttk.Treeview(available_frame, 
                                         columns=('type', 'status', 'quality'), 
                                         height=10)
        self.transport_tree.heading('#0', text='ID')
        self.transport_tree.heading('type', text='Тип')
        self.transport_tree.heading('status', text='Статус')
        self.transport_tree.heading('quality', text='Качество')
        self.transport_tree.column('#0', width=100)
        self.transport_tree.column('type', width=100)
        self.transport_tree.column('status', width=100)
        self.transport_tree.column('quality', width=100)
        
        self.transport_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления транспортом
        transport_button_frame = ttk.Frame(available_frame)
        transport_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(transport_button_frame, text="Обновить список", 
                  command=self.update_transport_list).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(transport_button_frame, text="Переключить", 
                  command=self.switch_transport).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(transport_button_frame, text="Информация", 
                  command=self.show_transport_info).pack(side=tk.RIGHT)
        
        # Конфигурация транспорта
        config_frame = ttk.LabelFrame(transport_frame, text="Конфигурация", 
                                     padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        self.transport_config_text = scrolledtext.ScrolledText(config_frame, 
                                                            wrap=tk.WORD)
        self.transport_config_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_logs_tab(self):
        """Настройка вкладки Логи"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Логи")
        
        # Панель управления логами
        log_control_frame = ttk.Frame(logs_frame)
        log_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(log_control_frame, text="Обновить", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(log_control_frame, text="Очистить", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(log_control_frame, text="Сохранить", 
                  command=self.save_logs).pack(side=tk.RIGHT)
        
        # Текст логов
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Фильтр логов
        filter_frame = ttk.Frame(logs_frame)
        filter_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(filter_frame, text="Фильтр:").pack(side=tk.LEFT)
        self.log_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.log_filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        filter_entry.bind('<KeyRelease>', self.filter_logs)
    
    def setup_status_bar(self):
        """Настройка статусной строки"""
        self.status_bar = ttk.Label(self.root, text="Готов", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def init_client(self):
        """Инициализация клиента"""
        try:
            self.client = get_vpn_client()
            self.client_uuid = self.client.get_client_uuid()
            self.uuid_label.config(text=f"UUID: {self.client_uuid}")
            
            # Добавление callback для обновления GUI
            self.client.add_gui_callback(self.on_state_change)
            
            # Запуск клиента
            if self.client.initialize():
                self.running = True
                self.update_client_info()
                return True
            else:
                messagebox.showerror("Ошибка", "Не удалось инициализировать клиент")
                return False
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка инициализации: {e}")
            return False
    
    def start_vpn(self):
        """Запуск VPN"""
        if not self.client:
            if not self.init_client():
                return
        
        try:
            if self.client.start_vpn():
                self.status_bar.config(text="VPN запускается...")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Ошибка", "Не удалось запустить VPN")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска: {e}")
    
    def stop_vpn(self):
        """Остановка VPN"""
        if not self.client:
            return
        
        try:
            if self.client.stop_vpn():
                self.status_bar.config(text="VPN останавливается...")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Ошибка", "Не удалось остановить VPN")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка остановки: {e}")
    
    def reload_config(self):
        """Перезагрузка конфигурации"""
        if not self.client:
            return
        
        try:
            if self.client.reload_config():
                self.status_bar.config(text="Конфигурация обновляется...")
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить конфигурацию")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обновления: {e}")
    
    def change_uuid(self):
        """Смена UUID клиента"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Смена UUID")
        dialog.geometry("400x150")
        
        ttk.Label(dialog, text="Введите новый UUID:").pack(pady=10)
        
        uuid_entry = ttk.Entry(dialog, width=40)
        uuid_entry.pack(pady=5)
        
        def apply_uuid():
            new_uuid = uuid_entry.get().strip()
            if new_uuid:
                self.client = get_vpn_client(new_uuid)
                self.client_uuid = new_uuid
                self.uuid_label.config(text=f"UUID: {new_uuid}")
                dialog.destroy()
                messagebox.showinfo("Успех", "UUID изменен")
            else:
                messagebox.showerror("Ошибка", "UUID не может быть пустым")
        
        ttk.Button(dialog, text="Применить", command=apply_uuid).pack(pady=10)
    
    def on_state_change(self, event_type, context):
        """Callback для изменения состояния"""
        self.root.after(0, self.update_gui_state, event_type, context)
    
    def update_gui_state(self, event_type, context):
        """Обновление GUI при изменении состояния"""
        # Обновление статуса
        state_info = self.client.get_state_info()
        current_state = state_info.get('current_state', 'unknown')
        
        self.state_label.config(text=current_state.upper())
        
        # Обновление цвета индикатора
        if current_state == 'running':
            self.update_state_indicator('green')
        elif current_state == 'error':
            self.update_state_indicator('red')
        elif current_state == 'warning':
            self.update_state_indicator('orange')
        else:
            self.update_state_indicator('yellow')
        
        # Обновление информации о состоянии
        state_text = json.dumps(state_info, indent=2, ensure_ascii=False)
        self.state_info.delete(1.0, tk.END)
        self.state_info.insert(1.0, state_text)
        
        # Обновление истории состояний
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history_tree.insert('', 'end', text=current_state, 
                                values=(timestamp, event_type))
        
        # Обновление информации о сети
        network_info = self.client.get_network_info()
        network_text = json.dumps(network_info, indent=2, ensure_ascii=False)
        self.network_info_text.delete(1.0, tk.END)
        self.network_info_text.insert(1.0, network_text)
        
        # Обновление оценки здоровья
        health_score = self.client.get_health_score()
        self.health_score_label.config(text=f"{health_score}/5")
        self.update_health_indicator(health_score)
        
        # Обновление статуса кнопок
        if current_state == 'running':
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def update_state_indicator(self, color):
        """Обновление индикатора состояния"""
        self.state_indicator.config(bg=color)
    
    def update_health_indicator(self, score):
        """Обновление индикатора здоровья"""
        width = 200
        height = 20
        
        # Очистка canvas
        self.health_canvas.delete("all")
        
        # Рисуем фон
        self.health_canvas.create_rectangle(0, 0, width, height, fill='gray')
        
        # Рисуем оценку
        score_width = int((score / 5) * width)
        if score >= 4:
            color = 'green'
        elif score >= 2:
            color = 'orange'
        else:
            color = 'red'
        
        self.health_canvas.create_rectangle(0, 0, score_width, height, fill=color)
        
        # Текст оценки
        self.health_canvas.create_text(width/2, height/2, text=f"{score}/5", 
                                      fill='white', font=('Arial', 10, 'bold'))
    
    def update_client_info(self):
        """Обновление информации о клиенте"""
        if not self.client:
            return
        
        # Информация о клиенте
        info = {
            "UUID": self.client_uuid,
            "Текущее состояние": self.client.get_current_state().value,
            "Запущен": self.client.is_running(),
            "Сетевая информация": self.client.get_network_info(),
            "Оценка здоровья": self.client.get_health_score(),
            "Транспортная информация": self.client.get_transport_info()
        }
        
        info_text = json.dumps(info, indent=2, ensure_ascii=False)
        self.client_info_text.delete(1.0, tk.END)
        self.client_info_text.insert(1.0, info_text)
    
    def update_transport_list(self):
        """Обновление списка доступных транспортов"""
        if not self.client:
            return
        
        transport_info = self.client.get_transport_info()
        available_transports = transport_info.get('available_transports', [])
        
        # Очистка treeview
        for item in self.transport_tree.get_children():
            self.transport_tree.delete(item)
        
        # Добавление транспортов
        for transport in available_transports:
            self.transport_tree.insert('', 'end', text=transport['id'],
                                     values=(transport['type'], 'Доступен', 
                                           transport.get('quality', 'N/A')))
    
    def switch_transport(self):
        """Переключение транспорта"""
        selected = self.transport_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите транспорт для переключения")
            return
        
        transport_id = self.transport_tree.item(selected[0])['text']
        
        try:
            if self.client.force_transport_switch(transport_id):
                messagebox.showinfo("Успех", f"Транспорт переключен на {transport_id}")
            else:
                messagebox.showerror("Ошибка", "Не удалось переключить транспорт")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка переключения: {e}")
    
    def show_transport_info(self):
        """Показать информацию о выбранном транспорте"""
        selected = self.transport_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите транспорт")
            return
        
        transport_id = self.transport_tree.item(selected[0])['text']
        
        # Здесь можно показать подробную информацию о транспорте
        messagebox.showinfo("Информация о транспорте", 
                          f"ID: {transport_id}\n\nДетальная информация будет добавлена позже")
    
    def test_dns(self):
        """Тест DNS"""
        if not self.client:
            return
        
        try:
            network_info = self.client.get_network_info()
            dns_status = network_info.get('connectivity', {}).get('dns_resolved', False)
            
            result = f"DNS проверка: {'Успешно' if dns_status else 'Ошибка'}\n"
            result += f"Время: {datetime.now().strftime('%H:%M:%S')}\n"
            
            self.test_results_text.insert(tk.END, result + "\n")
        except Exception as e:
            self.test_results_text.insert(tk.END, f"Ошибка DNS теста: {e}\n")
    
    def test_ip(self):
        """Тест IP"""
        if not self.client:
            return
        
        try:
            network_info = self.client.get_network_info()
            local_ip = network_info.get('local_ip')
            external_ip = network_info.get('external_ip')
            ip_leak = network_info.get('ip_leak', False)
            
            result = f"Локальный IP: {local_ip}\n"
            result += f"Внешний IP: {external_ip}\n"
            result += f"Утечка IP: {'Да' if ip_leak else 'Нет'}\n"
            result += f"Время: {datetime.now().strftime('%H:%M:%S')}\n"
            
            self.test_results_text.insert(tk.END, result + "\n")
        except Exception as e:
            self.test_results_text.insert(tk.END, f"Ошибка IP теста: {e}\n")
    
    def test_tls(self):
        """Тест TLS"""
        if not self.client:
            return
        
        try:
            # Здесь можно добавить TLS тест
            result = "TLS тест: будет реализован\n"
            result += f"Время: {datetime.now().strftime('%H:%M:%S')}\n"
            
            self.test_results_text.insert(tk.END, result + "\n")
        except Exception as e:
            self.test_results_text.insert(tk.END, f"Ошибка TLS теста: {e}\n")
    
    def refresh_logs(self):
        """Обновление логов"""
        try:
            log_dir = Path.home() / 'chatvpn' / 'client' / 'logs'
            
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                
                self.logs_text.delete(1.0, tk.END)
                
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.logs_text.insert(tk.END, f"=== {log_file.name} ===\n")
                            self.logs_text.insert(tk.END, content)
                            self.logs_text.insert(tk.END, "\n\n")
                    except Exception as e:
                        self.logs_text.insert(tk.END, f"Ошибка чтения {log_file}: {e}\n")
            else:
                self.logs_text.insert(tk.END, "Директория с логами не найдена")
        except Exception as e:
            self.logs_text.insert(tk.END, f"Ошибка обновления логов: {e}")
    
    def clear_logs(self):
        """Очистка логов в GUI"""
        self.logs_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Сохранение логов"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
                title="Сохранить логи"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.logs_text.get(1.0, tk.END))
                messagebox.showinfo("Успех", "Логи сохранены успешно")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения логов: {e}")
    
    def filter_logs(self, event=None):
        """Фильтрация логов"""
        filter_text = self.log_filter_var.get().lower()
        
        # Здесь можно реализовать фильтрацию логов
        # Пока просто обновляем текст
        pass
    
    def start_status_update(self):
        """Запуск обновления статуса"""
        def update_status():
            while self.running:
                try:
                    if self.client:
                        self.update_client_info()
                    time.sleep(5)  # Обновление каждые 5 секунд
                except Exception as e:
                    logger.error(f"Ошибка обновления статуса: {e}")
                    time.sleep(10)  # При ошибке ждем дольше
        
        self.update_thread = threading.Thread(target=update_status, daemon=True)
        self.update_thread.start()
    
    def on_closing(self):
        """Обработка закрытия GUI"""
        self.running = False
        if self.client:
            try:
                self.client.stop_vpn()
            except:
                pass
        self.root.destroy()


def main():
    """Главная функция для запуска GUI"""
    root = tk.Tk()
    app = XVPNGUI(root)
    
    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Запуск главного цикла
    root.mainloop()


if __name__ == "__main__":
    main()