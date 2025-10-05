#!/bin/bash

# XVPN Monitoring Setup Script
# Скрипт для установки и настройки мониторинга

set -e  # Exit on any error

echo "🚀 Setting up XVPN Monitoring System..."
echo "======================================"

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

# === Create directories ===
echo "📁 Creating directories..."
mkdir -p "$MONITORING_DIR" "$LOG_DIR" "$XVPN_DIR/data" "$XVPN_DIR/config"
chown -R "$XVPN_USER:$XVPN_USER" "$MONITORING_DIR" "$LOG_DIR" "$XVPN_DIR/data" "$XVPN_DIR/config"

# === Install monitoring tools ===
echo "📦 Installing monitoring tools..."
apt update
apt install -y \
    prometheus-node-exporter \
    prometheus-alertmanager \
    grafana \
    loki \
    promtail \
    cadvisor \
    process-exporter \
    bc \
    jq

# === Copy monitoring scripts ===
echo "📋 Copying monitoring scripts..."
cp "$MONITORING_DIR/xvpn-monitor.sh" /usr/local/bin/
chmod +x /usr/local/bin/xvpn-monitor.sh
chown "$XVPN_USER:$XVPN_USER" /usr/local/bin/xvpn-monitor.sh

# === Copy systemd service ===
echo "⚙️ Installing systemd service..."
cp "$SYSTEMD_DIR/xvpn-monitor.service" /etc/systemd/system/
systemctl daemon-reload

# === Configure Prometheus ===
echo "📊 Configuring Prometheus..."
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

scrape_configs:
  # XVPN services
  - job_name: 'xvpn-api'
    static_configs:
      - targets: ['localhost:8443']
    scrape_interval: 5s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  - job_name: 'xvpn-agent'
    static_configs:
      - targets: ['localhost:8443']
    scrape_interval: 10s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  - job_name: 'xvpn-bot'
    static_configs:
      - targets: ['localhost:8443']
    scrape_interval: 30s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  - job_name: 'xvpn-worker'
    static_configs:
      - targets: ['localhost:8443']
    scrape_interval: 15s
    metrics_path: /metrics
    scheme: https
    tls_config:
      insecure_skip_verify: true

  - job_name: 'xvpn-orchestrator'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 20s
    metrics_path: /metrics
    scheme: http

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'docker-containers'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    scrape_interval: 15s
    metrics_path: /metrics
    scheme: http

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:5432']
    scrape_interval: 30s
    metrics_path: /metrics
    scheme: http

  # Process metrics
  - job_name: 'process-exporter'
    static_configs:
      - targets: ['localhost:9256']
    scrape_interval: 15s
    metrics_path: /metrics
EOF

# === Configure Grafana ===
echo "📈 Configuring Grafana..."
cat > /etc/grafana/grafana.ini << EOF
[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3000
domain = grafana.xvpn.local
enforce_domain = false
root_url = %(protocol)s://%(domain)s:%(http_port)s/

[database]
type = sqlite3
path = grafana.db

[session]
provider = file
provider_config = sessions

[analytics]
reporting_enabled = false
check_for_updates = true

[security]
admin_user = admin
admin_password = ${GRAFANA_PASSWORD:-admin}
secret_key = SW2YcwTIb9zpOOhoPsMm
disable_gravatar = false

[users]
allow_sign_up = false
auto_assign_org = true
auto_assign_org_role = Viewer

[auth.anonymous]
enabled = false

[log]
mode = console file
level = info

[metrics]
enabled = true
EOF

# === Configure Loki ===
echo "📝 Configuring Loki..."
cat > /etc/loki/local-config.yaml << EOF
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
EOF

# === Configure Promtail ===
echo "📋 Configuring Promtail..."
cat > /etc/promtail/config.yml << EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  # XVPN logs
  - job_name: xvpn
    static_configs:
      - targets:
          - localhost
        labels:
          job: xvpn
          __path__: /var/log/xvpn/*.log

  # System logs
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: system
          __path__: /var/log/syslog
EOF

# === Enable and start services ===
echo "🔄 Enabling and starting services..."
systemctl enable prometheus-node-exporter
systemctl enable prometheus-alertmanager
systemctl enable grafana-server
systemctl enable loki
systemctl enable promtail
systemctl enable xvpn-monitor

systemctl start prometheus-node-exporter
systemctl start prometheus-alertmanager
systemctl start grafana-server
systemctl start loki
systemctl start promtail
systemctl start xvpn-monitor

# === Configure firewall ===
echo "🛡️ Configuring firewall..."
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus
ufw allow 9100/tcp  # Node Exporter
ufw allow 3100/tcp  # Loki
ufw allow 9080/tcp  # Promtail

# === Show status ===
echo "🔍 Checking service status..."
systemctl status prometheus-node-exporter --no-pager || true
systemctl status prometheus-alertmanager --no-pager || true
systemctl status grafana-server --no-pager || true
systemctl status loki --no-pager || true
systemctl status promtail --no-pager || true
systemctl status xvpn-monitor --no-pager || true

echo ""
echo "✅ XVPN Monitoring System setup completed!"
echo ""
echo "📊 Access monitoring tools:"
echo "   Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "   Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo "   Loki: http://$(hostname -I | awk '{print $1}'):3100"
echo ""
echo "🔐 Default credentials:"
echo "   Grafana: admin / ${GRAFANA_PASSWORD:-admin}"
echo ""
echo "📋 To view logs:"
echo "   journalctl -u xvpn-monitor -f"
echo ""
echo "💡 Next steps:"
echo "   1. Configure Grafana dashboards"
echo "   2. Set up alerting rules"
echo "   3. Configure monitoring alerts"
echo "   4. Set up log aggregation"