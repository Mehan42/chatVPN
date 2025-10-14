package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"
)

// MetricsHandler handles Prometheus metrics endpoint
func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	metrics := s.collectMetrics()

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(http.StatusOK)

	// Write Prometheus format metrics
	w.Write([]byte("# HELP xvpn_active_connections Number of active VPN connections\n"))
	w.Write([]byte("# TYPE xvpn_active_connections gauge\n"))
	w.Write([]byte("xvpn_active_connections " + strconv.Itoa(metrics.ActiveConnections) + "\n\n"))

	w.Write([]byte("# HELP xvpn_total_clients Total number of registered clients\n"))
	w.Write([]byte("# TYPE xvpn_total_clients gauge\n"))
	w.Write([]byte("xvpn_total_clients " + strconv.Itoa(metrics.TotalClients) + "\n\n"))

	w.Write([]byte("# HELP xvpn_api_requests_total Total number of API requests\n"))
	w.Write([]byte("# TYPE xvpn_api_requests_total counter\n"))
	w.Write([]byte("xvpn_api_requests_total " + strconv.Itoa(metrics.TotalRequests) + "\n\n"))

	w.Write([]byte("# HELP xvpn_uptime_seconds Server uptime in seconds\n"))
	w.Write([]byte("# TYPE xvpn_uptime_seconds counter\n"))
	w.Write([]byte("xvpn_uptime_seconds " + strconv.FormatInt(metrics.UptimeSeconds, 10) + "\n\n"))

	w.Write([]byte("# HELP xvpn_memory_usage_bytes Current memory usage in bytes\n"))
	w.Write([]byte("# TYPE xvpn_memory_usage_bytes gauge\n"))
	w.Write([]byte("xvpn_memory_usage_bytes " + strconv.FormatInt(metrics.MemoryUsage, 10) + "\n\n"))
}

// Metrics represents server metrics
type Metrics struct {
	ActiveConnections int    `json:"active_connections"`
	TotalClients      int    `json:"total_clients"`
	TotalRequests     int    `json:"total_requests"`
	UptimeSeconds     int64  `json:"uptime_seconds"`
	MemoryUsage       int64  `json:"memory_usage"`
	Version           string `json:"version"`
	StartTime         time.Time
}

// collectMetrics gathers current server metrics
func (s *Server) collectMetrics() *Metrics {
	// This is a simplified implementation
	// In production, you would collect real metrics

	return &Metrics{
		ActiveConnections: 1,                                                       // Placeholder
		TotalClients:      1,                                                       // Placeholder
		TotalRequests:     42,                                                      // Placeholder
		UptimeSeconds:     int64(time.Since(time.Now().Add(-time.Hour)).Seconds()), // Placeholder
		MemoryUsage:       50 * 1024 * 1024,                                        // 50MB placeholder
		Version:           "1.0.0",
	}
}

// handleMetricsJSON returns metrics in JSON format
func (s *Server) handleMetricsJSON(w http.ResponseWriter, r *http.Request) {
	metrics := s.collectMetrics()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}
