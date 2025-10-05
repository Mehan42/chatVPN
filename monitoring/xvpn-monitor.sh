#!/bin/bash

# XVPN System Monitoring Script
# Скрипт для мониторинга состояния системы

# === Configuration ===
LOG_DIR="/var/log/xvpn"
MONITORING_DIR="/opt/xvpn/monitoring"
INTERVAL=60  # seconds

# === Functions ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/system_monitor.log"
}

check_cpu() {
    # Get CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -f1 -d"%" | sed 's/%us,/%/')
    
    # Log CPU usage
    log "CPU Usage: ${cpu_usage}%"
    
    # Alert if CPU usage is high
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log "WARNING: High CPU usage detected (${cpu_usage}%)"
        # TODO: Send alert
    fi
}

check_memory() {
    # Get memory usage
    memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    # Log memory usage
    log "Memory Usage: ${memory_usage}%"
    
    # Alert if memory usage is high
    if [ "$memory_usage" -gt 85 ]; then
        log "WARNING: High memory usage detected (${memory_usage}%)"
        # TODO: Send alert
    fi
}

check_disk() {
    # Get disk usage
    disk_usage=$(df -h / | awk 'NR==2{print $5}' | cut -f1 -d"%")
    
    # Log disk usage
    log "Disk Usage: ${disk_usage}%"
    
    # Alert if disk usage is high
    if [ "$disk_usage" -gt 90 ]; then
        log "WARNING: High disk usage detected (${disk_usage}%)"
        # TODO: Send alert
    fi
}

check_network() {
    # Get network interfaces
    interfaces=$(ip link show | grep -E "^[0-9]+:" | grep -v "lo:" | awk -F': ' '{print $2}')
    
    # Check each interface
    for interface in $interfaces; do
        # Get RX/TX bytes
        rx_bytes=$(cat /sys/class/net/$interface/statistics/rx_bytes 2>/dev/null || echo "0")
        tx_bytes=$(cat /sys/class/net/$interface/statistics/tx_bytes 2>/dev/null || echo "0")
        
        # Convert to MB
        rx_mb=$((rx_bytes / 1024 / 1024))
        tx_mb=$((tx_bytes / 1024 / 1024))
        
        # Log network usage
        log "Network $interface: RX ${rx_mb}MB, TX ${tx_mb}MB"
    done
}

check_processes() {
    # Get process count
    process_count=$(ps aux | wc -l)
    
    # Log process count
    log "Processes: $process_count"
    
    # Alert if too many processes
    if [ "$process_count" -gt 500 ]; then
        log "WARNING: High process count detected ($process_count)"
        # TODO: Send alert
    fi
}

check_services() {
    # Check XVPN services
    services=("xvpn-api" "xvpn-agent" "xvpn-bot" "xvpn-worker" "xvpn-orchestrator")
    
    for service in "${services[@]}"; do
        status=$(systemctl is-active "$service" 2>/dev/null)
        if [ "$status" != "active" ]; then
            log "ERROR: Service $service is not active (status: $status)"
            # TODO: Send alert
        else
            log "Service $service is active"
        fi
    done
}

check_docker() {
    # Check if Docker is running
    if ! systemctl is-active --quiet docker; then
        log "ERROR: Docker service is not running"
        # TODO: Send alert
    else
        log "Docker service is running"
        
        # Get Docker container count
        container_count=$(docker ps -q | wc -l)
        log "Docker containers: $container_count"
        
        # Check XVPN containers
        xvpn_containers=$(docker ps --filter "label=traefik.enable=true" -q | wc -l)
        log "XVPN Docker containers: $xvpn_containers"
    fi
}

check_connectivity() {
    # Check internet connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log "Internet connectivity: OK"
    else
        log "ERROR: Internet connectivity is DOWN"
        # TODO: Send alert
    fi
    
    # Check DNS resolution
    if nslookup google.com >/dev/null 2>&1; then
        log "DNS resolution: OK"
    else
        log "ERROR: DNS resolution is DOWN"
        # TODO: Send alert
    fi
}

# === Main Loop ===
main() {
    log "Starting XVPN system monitoring..."
    
    while true; do
        log "--- System Monitoring Check ---"
        
        # Perform checks
        check_cpu
        check_memory
        check_disk
        check_network
        check_processes
        check_services
        check_docker
        check_connectivity
        
        log "--- End Monitoring Check ---"
        
        # Wait for next check
        sleep $INTERVAL
    done
}

# === Run ===
main "$@"