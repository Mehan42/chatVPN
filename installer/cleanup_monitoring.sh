#!/bin/bash

# XVPN Monitoring Cleanup Script
# Скрипт для очистки мониторинга

set -e  # Exit on any error

echo "🧹 Cleaning up XVPN Monitoring System..."
echo "====================================="

# === Check if running as root ===
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# === Configuration ===
XVPN_USER="xvpn"
XVPN_DIR="/opt/xvpn"
MONITORING_DIR="$XVPN_DIR/monitoring"
LOG_DIR="/var/log/xvpn"
SYSTEMD_DIR="/etc/systemd/system"

# === Stop services ===
echo "⏹️ Stopping monitoring services..."
systemctl stop xvpn-monitor || true
systemctl stop prometheus-node-exporter || true
systemctl stop prometheus-alertmanager || true
systemctl stop grafana-server || true
systemctl stop loki || true
systemctl stop promtail || true

# === Disable services ===
echo "🚫 Disabling monitoring services..."
systemctl disable xvpn-monitor || true
systemctl disable prometheus-node-exporter || true
systemctl disable prometheus-alertmanager || true
systemctl disable grafana-server || true
systemctl disable loki || true
systemctl disable promtail || true

# === Remove systemd services ===
echo "🗑️ Removing systemd services..."
rm -f /etc/systemd/system/xvpn-monitor.service
rm -f /etc/systemd/system/prometheus-node-exporter.service
rm -f /etc/systemd/system/prometheus-alertmanager.service
rm -f /etc/systemd/system/grafana-server.service
rm -f /etc/systemd/system/loki.service
rm -f /etc/systemd/system/promtail.service

# === Reload systemd ===
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# === Remove monitoring tools ===
echo "📦 Removing monitoring tools..."
apt remove -y \
    prometheus-node-exporter \
    prometheus-alertmanager \
    grafana \
    loki \
    promtail \
    cadvisor \
    process-exporter || true

# === Remove configuration files ===
echo "🗑️ Removing configuration files..."
rm -rf /etc/prometheus/
rm -rf /etc/grafana/
rm -rf /etc/loki/
rm -rf /etc/promtail/
rm -f /usr/local/bin/xvpn-monitor.sh

# === Remove data ===
echo "🗑️ Removing monitoring data..."
rm -rf /var/lib/prometheus/
rm -rf /var/lib/grafana/
rm -rf /var/lib/loki/
rm -rf /var/lib/promtail/
rm -rf $MONITORING_DIR/
rm -rf $LOG_DIR/

# === Remove firewall rules ===
echo "🛡️ Removing firewall rules..."
ufw delete allow 3000/tcp || true  # Grafana
ufw delete allow 9090/tcp || true  # Prometheus
ufw delete allow 9100/tcp || true  # Node Exporter
ufw delete allow 3100/tcp || true  # Loki
ufw delete allow 9080/tcp || true  # Promtail

# === Show status ===
echo "🔍 Checking service status..."
systemctl status xvpn-monitor --no-pager || true
systemctl status prometheus-node-exporter --no-pager || true
systemctl status prometheus-alertmanager --no-pager || true
systemctl status grafana-server --no-pager || true
systemctl status loki --no-pager || true
systemctl status promtail --no-pager || true

echo ""
echo "✅ XVPN Monitoring System cleanup completed!"
echo ""
echo "📋 To reinstall monitoring:"
echo "   sudo $XVPN_DIR/installer/install_monitoring.sh"
echo ""
echo "💡 Remember to backup any important data before reinstalling"