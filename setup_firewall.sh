#!/bin/bash
# Скрипт настройки фаервола для XVPN клиента

echo "Настройка фаервола для XVPN клиента..."

# Проверка, что запущен с root правами
if [ "$EUID" -ne 0 ]; then
  echo "Пожалуйста, запустите скрипт с root правами: sudo $0"
  exit 1
fi

echo "Настройка правил iptables..."

# Сброс текущих правил (осторожно!)
# iptables -F

# Политика по умолчанию: разрешить всё (в начальной настройке)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Разрешить loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Разрешить установленные соединения
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Открыть только необходимые порты для XVPN
# SSH (если нужен удаленный доступ)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Разрешить трафик для установленного VPN соединения
iptables -A OUTPUT -o tun+ -j ACCEPT
iptables -A INPUT -i tun+ -j ACCEPT

# Разрешить подключения к VPN серверу (адаптируйте под свои порты)
# Обычно VPN использует порты 443, 80, 53, 1194, 8443
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT  # DNS
iptables -A OUTPUT -p tcp --dport 1194 -j ACCEPT  # OpenVPN
iptables -A OUTPUT -p tcp --dport 8443 -j ACCEPT  # XVPN

# Правила для конкретного VPN сервера (замените IP на реальный)
# iptables -A OUTPUT -d [VPN_SERVER_IP] -p tcp --dport [VPN_PORT] -j ACCEPT

# Блокировать все остальные исходящие соединения (опционально)
# iptables -A OUTPUT -j DROP

# Логирование подключений (для отладки)
iptables -A INPUT -j LOG --log-prefix "XVPN-Firewall-IN: "
iptables -A OUTPUT -j LOG --log-prefix "XVPN-Firewall-OUT: "

echo "Правила фаервола применены."
echo "Проверить правила: sudo iptables -L -v"
echo "Для сохранения правил между перезагрузками установите iptables-persistent"
echo "sudo apt-get install iptables-persistent"

# Для systemd сервиса
cat > /etc/systemd/system/xvpn-firewall.service << 'EOF'
[Unit]
Description=XVPN Firewall Rules
After=network.target

[Service]
Type=oneshot
ExecStart=/home/uss/chatvpn/client/setup_firewall.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

echo "Создан systemd сервис для автоматической настройки фаервола"
echo "Включить автозапуск: sudo systemctl enable xvpn-firewall.service"
echo "Запустить сейчас: sudo systemctl start xvpn-firewall.service"