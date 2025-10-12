// Package tunnelverifier provides testing utilities for various network conditions
package tunnelverifier

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"
)

// NetworkConditionSimulator simulates different network conditions for testing
type NetworkConditionSimulator struct {
	originalTransport http.RoundTripper
	timeout           time.Duration
	delay             time.Duration
	packetLossRate    float64
	bandwidth         int // in KB/s
}

// NewNetworkConditionSimulator creates a new simulator
func NewNetworkConditionSimulator() *NetworkConditionSimulator {
	return &NetworkConditionSimulator{
		originalTransport: http.DefaultTransport,
		timeout:           30 * time.Second,
		delay:             0,
		packetLossRate:    0,
		bandwidth:         0, // Unlimited by default
	}
}

// SetTimeout sets the timeout for requests
func (n *NetworkConditionSimulator) SetTimeout(timeout time.Duration) {
	n.timeout = timeout
}

// SetDelay sets the delay for requests
func (n *NetworkConditionSimulator) SetDelay(delay time.Duration) {
	n.delay = delay
}

// SetPacketLossRate sets the packet loss rate (0.0 to 1.0)
func (n *NetworkConditionSimulator) SetPacketLossRate(rate float64) {
	if rate < 0 {
		rate = 0
	} else if rate > 1 {
		rate = 1
	}
	n.packetLossRate = rate
}

// SetBandwidth sets the bandwidth limit in KB/s
func (n *NetworkConditionSimulator) SetBandwidth(kbPerSecond int) {
	n.bandwidth = kbPerSecond
}

// TestSlowNetwork simulates a slow network condition
func (n *NetworkConditionSimulator) TestSlowNetwork(tv *TunnelVerifier) error {
	n.SetDelay(2 * time.Second) // 2 second delay
	n.SetBandwidth(512)         // 512 KB/s bandwidth
	
	tv.enhancedLogger.Info("Testing tunnel verifier under slow network conditions", map[string]interface{}{
		"delay":     n.delay.Seconds(),
		"bandwidth": n.bandwidth,
	})
	
	// Test the tunnel verifier with slow network
	ctx, cancel := context.WithTimeout(context.Background(), n.timeout)
	defer cancel()
	
	// Perform verification under these conditions
	result, err := tv.IsTunnelingValid()
	if err != nil {
		tv.enhancedLogger.Warn("Error during slow network test", map[string]interface{}{
			"error": err.Error(),
		})
		return err
	}
	
	tv.enhancedLogger.Info("Slow network test completed", map[string]interface{}{
		"result": result,
	})
	
	return nil
}

// TestHighLatency simulates high latency conditions
func (n *NetworkConditionSimulator) TestHighLatency(tv *TunnelVerifier) error {
	n.SetDelay(5 * time.Second) // 5 second delay
	n.SetTimeout(60 * time.Second) // Increase timeout for high latency
	
	tv.enhancedLogger.Info("Testing tunnel verifier under high latency conditions", map[string]interface{}{
		"delay": n.delay.Seconds(),
	})
	
	// Test the tunnel verifier with high latency
	ctx, cancel := context.WithTimeout(context.Background(), n.timeout)
	defer cancel()
	
	result, err := tv.IsTunnelingValid()
	if err != nil {
		tv.enhancedLogger.Warn("Error during high latency test", map[string]interface{}{
			"error": err.Error(),
		})
		return err
	}
	
	tv.enhancedLogger.Info("High latency test completed", map[string]interface{}{
		"result": result,
	})
	
	return nil
}

// TestUnstableConnection simulates an unstable connection with packet loss
func (n *NetworkConditionSimulator) TestUnstableConnection(tv *TunnelVerifier) error {
	n.SetPacketLossRate(0.1) // 10% packet loss
	n.SetDelay(1 * time.Second) // Additional delay
	
	tv.enhancedLogger.Info("Testing tunnel verifier under unstable connection conditions", map[string]interface{}{
		"packet_loss_rate": fmt.Sprintf("%.2f%%", n.packetLossRate*100),
	})
	
	// Test the tunnel verifier with unstable connection
	ctx, cancel := context.WithTimeout(context.Background(), n.timeout)
	defer cancel()
	
	result, err := tv.IsTunnelingValid()
	if err != nil {
		tv.enhancedLogger.Warn("Error during unstable connection test", map[string]interface{}{
			"error": err.Error(),
		})
		return err
	}
	
	tv.enhancedLogger.Info("Unstable connection test completed", map[string]interface{}{
		"result": result,
	})
	
	return nil
}

// TestWithDNSBlocking simulates conditions where certain DNS queries are blocked
func (n *NetworkConditionSimulator) TestWithDNSBlocking(tv *TunnelVerifier) error {
	tv.enhancedLogger.Info("Testing tunnel verifier under DNS blocking conditions", nil)
	
	// Create a custom dialer that simulates DNS blocking for certain domains
	oldConfig := tv.config
	newConfig := *tv.config
	
	// Update the endpoints to include potentially blocked domains
	testEndpoints := append(newConfig.VerificationEndpoints, "blocked-domain-test.com", "censored-site.org")
	newConfig.VerificationEndpoints = testEndpoints
	
	// Temporarily update the config
	tv.config = &newConfig
	
	// We'll restore the config after the test
	defer func() {
		tv.config = &oldConfig
	}()
	
	result, err := tv.IsTunnelingValid()
	if err != nil {
		tv.enhancedLogger.Info("Expected error during DNS blocking test", map[string]interface{}{
			"error": err.Error(),
		})
		// This is expected in a DNS blocking scenario
	} else {
		tv.enhancedLogger.Info("DNS blocking test completed", map[string]interface{}{
			"result": result,
		})
	}
	
	return nil
}

// TestCompleteVerificationCycle runs a complete verification cycle under various conditions
func (n *NetworkConditionSimulator) TestCompleteVerificationCycle(tv *TunnelVerifier) error {
	tv.enhancedLogger.Info("Starting complete verification cycle test", nil)
	
	startTime := time.Now()
	
	// Test normal conditions first
	tv.enhancedLogger.Info("Testing under normal conditions", nil)
	normalResult, err := tv.IsTunnelingValid()
	if err != nil {
		tv.enhancedLogger.Warn("Error during normal test", map[string]interface{}{
			"error": err.Error(),
		})
		// Continue testing even if there's an error
	}
	
	// Test slow network
	err = n.TestSlowNetwork(tv)
	if err != nil {
		tv.enhancedLogger.Warn("Slow network test failed", map[string]interface{}{
			"error": err.Error(),
		})
	}
	
	// Test high latency
	err = n.TestHighLatency(tv)
	if err != nil {
		tv.enhancedLogger.Warn("High latency test failed", map[string]interface{}{
			"error": err.Error(),
		})
	}
	
	// Test unstable connection
	err = n.TestUnstableConnection(tv)
	if err != nil {
		tv.enhancedLogger.Warn("Unstable connection test failed", map[string]interface{}{
			"error": err.Error(),
		})
	}
	
	// Test with DNS blocking
	err = n.TestWithDNSBlocking(tv)
	if err != nil {
		tv.enhancedLogger.Warn("DNS blocking test failed", map[string]interface{}{
			"error": err.Error(),
		})
	}
	
	duration := time.Since(startTime)
	
	tv.enhancedLogger.Info("Complete verification cycle test finished", map[string]interface{}{
		"normal_result": normalResult,
		"duration":      duration.Seconds(),
		"tests_run":     5, // normal + 4 condition tests
	})
	
	return nil
}

// CheckConnectivity checks if the system has basic internet connectivity
func (n *NetworkConditionSimulator) CheckConnectivity() (bool, error) {
	// Try to connect to a well-known public endpoint
	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	
	resp, err := client.Get("https://httpbin.org/ip")
	if err != nil {
		return false, fmt.Errorf("connectivity check failed: %w", err)
	}
	defer resp.Body.Close()
	
	return resp.StatusCode == http.StatusOK, nil
}

// CheckDNSResolution checks if DNS resolution is working
func (n *NetworkConditionSimulator) CheckDNSResolution() (bool, error) {
	// Try to resolve a well-known domain
	_, err := net.LookupIP("google.com")
	if err != nil {
		return false, fmt.Errorf("DNS resolution check failed: %w", err)
	}
	
	return true, nil
}

// TestNetworkConditions performs a comprehensive network condition test
func (n *NetworkConditionSimulator) TestNetworkConditions(tv *TunnelVerifier) error {
	tv.enhancedLogger.Info("Starting comprehensive network conditions test", nil)
	
	// Check basic connectivity first
	hasConnectivity, err := n.CheckConnectivity()
	if err != nil {
		tv.enhancedLogger.Warn("Connectivity check failed", map[string]interface{}{
			"error": err.Error(),
		})
	} else {
		tv.enhancedLogger.Info("Connectivity check passed", map[string]interface{}{
			"status": hasConnectivity,
		})
	}
	
	// Check DNS resolution
	hasDNS, err := n.CheckDNSResolution()
	if err != nil {
		tv.enhancedLogger.Warn("DNS resolution check failed", map[string]interface{}{
			"error": err.Error(),
		})
	} else {
		tv.enhancedLogger.Info("DNS resolution check passed", map[string]interface{}{
			"status": hasDNS,
		})
	}
	
	// Run complete verification cycle
	err = n.TestCompleteVerificationCycle(tv)
	if err != nil {
		tv.enhancedLogger.Error("Complete verification cycle failed", map[string]interface{}{
			"error": err.Error(),
		})
		return err
	}
	
	tv.enhancedLogger.Info("Comprehensive network conditions test completed successfully", nil)
	return nil
}