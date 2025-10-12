// Package tunnelverifier provides methods to access performance metrics
package tunnelverifier

// GetMetrics returns the current performance metrics
func (tv *TunnelVerifier) GetMetrics() Metrics {
	return *tv.metrics
}

// GetVerificationStats returns verification statistics
func (tv *TunnelVerifier) GetVerificationStats() map[string]interface{} {
	return tv.metrics.GetVerificationStats()
}

// GetIPLeakCheckStats returns IP leak check statistics
func (tv *TunnelVerifier) GetIPLeakCheckStats() map[string]interface{} {
	return tv.metrics.GetCheckStats(tv.metrics.IPLeakCheckMetrics)
}

// GetDNSLeakCheckStats returns DNS leak check statistics
func (tv *TunnelVerifier) GetDNSLeakCheckStats() map[string]interface{} {
	return tv.metrics.GetCheckStats(tv.metrics.DNSLeakCheckMetrics)
}

// GetTrafficRoutingStats returns traffic routing check statistics
func (tv *TunnelVerifier) GetTrafficRoutingStats() map[string]interface{} {
	return tv.metrics.GetCheckStats(tv.metrics.TrafficRoutingMetrics)
}

// ResetMetrics resets all performance metrics to zero
func (tv *TunnelVerifier) ResetMetrics() {
	tv.metrics.ResetMetrics()
}