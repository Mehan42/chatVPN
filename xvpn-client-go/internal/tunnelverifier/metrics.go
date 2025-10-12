// Package tunnelverifier provides performance metrics functionality
package tunnelverifier

import (
	"sync"
	"time"
)

// Metrics holds performance metrics for the tunnel verifier
type Metrics struct {
	mu sync.RWMutex
	
	// Verification metrics
	TotalVerifications     int64
	SuccessfulVerifications int64
	FailedVerifications    int64
	
	// Timing metrics
	TotalVerificationTime time.Duration
	AvgVerificationTime   time.Duration
	MinVerificationTime   time.Duration
	MaxVerificationTime   time.Duration
	
	// Check-specific metrics
	IPLeakCheckMetrics     *CheckMetrics
	DNSLeakCheckMetrics    *CheckMetrics
	TrafficRoutingMetrics  *CheckMetrics
	
	// Resource usage metrics
	MaxMemoryUsed int64
	CurrentMemory int64
}

// CheckMetrics holds metrics for a specific check
type CheckMetrics struct {
	TotalCalls   int64
	SuccessCount int64
	ErrorCount   int64
	AvgDuration  time.Duration
	TotalTime    time.Duration
	StartTime    time.Time // For tracking ongoing operations
}

// NewMetrics creates a new metrics instance
func NewMetrics() *Metrics {
	return &Metrics{
		IPLeakCheckMetrics:    &CheckMetrics{},
		DNSLeakCheckMetrics:   &CheckMetrics{},
		TrafficRoutingMetrics: &CheckMetrics{},
		MinVerificationTime:   time.Duration(1<<63 - 1), // Max int64 value as initial minimum
	}
}

// RecordVerification records metrics for a verification run
func (m *Metrics) RecordVerification(success bool, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.TotalVerifications++
	
	// Update verification time metrics
	m.TotalVerificationTime += duration
	if duration < m.MinVerificationTime {
		m.MinVerificationTime = duration
	}
	if duration > m.MaxVerificationTime {
		m.MaxVerificationTime = duration
	}
	
	// Calculate new average (we could optimize this by calculating on demand)
	if m.TotalVerifications > 0 {
		m.AvgVerificationTime = m.TotalVerificationTime / time.Duration(m.TotalVerifications)
	}
	
	if success {
		m.SuccessfulVerifications++
	} else {
		m.FailedVerifications++
	}
}

// RecordIPLeakCheck records metrics for an IP leak check
func (m *Metrics) RecordIPLeakCheck(success bool, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.IPLeakCheckMetrics.TotalCalls++
	if success {
		m.IPLeakCheckMetrics.SuccessCount++
	} else {
		m.IPLeakCheckMetrics.ErrorCount++
	}
	
	m.IPLeakCheckMetrics.TotalTime += duration
	if m.IPLeakCheckMetrics.TotalCalls > 0 {
		m.IPLeakCheckMetrics.AvgDuration = m.IPLeakCheckMetrics.TotalTime / time.Duration(m.IPLeakCheckMetrics.TotalCalls)
	}
}

// RecordDNSLeakCheck records metrics for a DNS leak check
func (m *Metrics) RecordDNSLeakCheck(success bool, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.DNSLeakCheckMetrics.TotalCalls++
	if success {
		m.DNSLeakCheckMetrics.SuccessCount++
	} else {
		m.DNSLeakCheckMetrics.ErrorCount++
	}
	
	m.DNSLeakCheckMetrics.TotalTime += duration
	if m.DNSLeakCheckMetrics.TotalCalls > 0 {
		m.DNSLeakCheckMetrics.AvgDuration = m.DNSLeakCheckMetrics.TotalTime / time.Duration(m.DNSLeakCheckMetrics.TotalCalls)
	}
}

// RecordTrafficRoutingCheck records metrics for a traffic routing check
func (m *Metrics) RecordTrafficRoutingCheck(success bool, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.TrafficRoutingMetrics.TotalCalls++
	if success {
		m.TrafficRoutingMetrics.SuccessCount++
	} else {
		m.TrafficRoutingMetrics.ErrorCount++
	}
	
	m.TrafficRoutingMetrics.TotalTime += duration
	if m.TrafficRoutingMetrics.TotalCalls > 0 {
		m.TrafficRoutingMetrics.AvgDuration = m.TrafficRoutingMetrics.TotalTime / time.Duration(m.TrafficRoutingMetrics.TotalCalls)
	}
}

// GetMetrics returns a copy of the current metrics
func (m *Metrics) GetMetrics() Metrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	// Return a copy of metrics to avoid race conditions
	return Metrics{
		TotalVerifications:      m.TotalVerifications,
		SuccessfulVerifications: m.SuccessfulVerifications,
		FailedVerifications:     m.FailedVerifications,
		TotalVerificationTime:   m.TotalVerificationTime,
		AvgVerificationTime:     m.AvgVerificationTime,
		MinVerificationTime:     m.MinVerificationTime,
		MaxVerificationTime:     m.MaxVerificationTime,
		IPLeakCheckMetrics:      &CheckMetrics(*m.IPLeakCheckMetrics),
		DNSLeakCheckMetrics:     &CheckMetrics(*m.DNSLeakCheckMetrics),
		TrafficRoutingMetrics:   &CheckMetrics(*m.TrafficRoutingMetrics),
		MaxMemoryUsed:           m.MaxMemoryUsed,
		CurrentMemory:           m.CurrentMemory,
	}
}

// ResetMetrics resets all metrics to zero
func (m *Metrics) ResetMetrics() {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.TotalVerifications = 0
	m.SuccessfulVerifications = 0
	m.FailedVerifications = 0
	m.TotalVerificationTime = 0
	m.AvgVerificationTime = 0
	m.MinVerificationTime = time.Duration(1<<63 - 1) // Max int64 value
	m.MaxVerificationTime = 0
	
	// Reset check-specific metrics
	m.IPLeakCheckMetrics = &CheckMetrics{}
	m.DNSLeakCheckMetrics = &CheckMetrics{}
	m.TrafficRoutingMetrics = &CheckMetrics{}
	
	m.MaxMemoryUsed = 0
	m.CurrentMemory = 0
}

// GetVerificationStats returns verification statistics
func (m *Metrics) GetVerificationStats() map[string]interface{} {
	metrics := m.GetMetrics()
	
	var successRate float64
	if metrics.TotalVerifications > 0 {
		successRate = float64(metrics.SuccessfulVerifications) / float64(metrics.TotalVerifications) * 100
	}
	
	return map[string]interface{}{
		"total_verifications":      metrics.TotalVerifications,
		"successful_verifications": metrics.SuccessfulVerifications,
		"failed_verifications":     metrics.FailedVerifications,
		"success_rate_percentage":  successRate,
		"avg_verification_time_ms": metrics.AvgVerificationTime.Milliseconds(),
		"min_verification_time_ms": metrics.MinVerificationTime.Milliseconds(),
		"max_verification_time_ms": metrics.MaxVerificationTime.Milliseconds(),
		"total_verification_time":  metrics.TotalVerificationTime.Seconds(),
	}
}

// GetCheckStats returns statistics for a specific check
func (m *Metrics) GetCheckStats(checkMetrics *CheckMetrics) map[string]interface{} {
	var successRate float64
	if checkMetrics.TotalCalls > 0 {
		successRate = float64(checkMetrics.SuccessCount) / float64(checkMetrics.TotalCalls) * 100
	}
	
	return map[string]interface{}{
		"total_calls":         checkMetrics.TotalCalls,
		"success_count":       checkMetrics.SuccessCount,
		"error_count":         checkMetrics.ErrorCount,
		"success_rate_percentage": successRate,
		"avg_duration_ms":     checkMetrics.AvgDuration.Milliseconds(),
		"total_time":          checkMetrics.TotalTime.Seconds(),
	}
}