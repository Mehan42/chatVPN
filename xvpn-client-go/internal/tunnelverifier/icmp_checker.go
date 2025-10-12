// Package tunnelverifier provides ICMP-based verification functionality
package tunnelverifier

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
	"time"
)

// ICMPChecker performs ICMP-based verification checks
type ICMPChecker struct {
	enhancedLogger *Logger
	timeout        time.Duration
	retryAttempts  int
}

// ICMPCheckResult represents the result of an ICMP check
type ICMPCheckResult struct {
	Target        string
	ResponseTime  time.Duration
	Success       bool
	Error         error
	Sequence      uint16
	PacketSize    int
}

// ICMPHeader represents an ICMP packet header
type ICMPHeader struct {
	Type       uint8
	Code       uint8
	Checksum   uint16
	Identifier uint16
	Sequence   uint16
}

// NewICMPChecker creates a new ICMP checker
func NewICMPChecker(logger *Logger) *ICMPChecker {
	return &ICMPChecker{
		enhancedLogger: logger,
		timeout:        5 * time.Second,
		retryAttempts:  2,
	}
}

// SetTimeout sets the timeout for ICMP requests
func (ic *ICMPChecker) SetTimeout(timeout time.Duration) {
	ic.timeout = timeout
}

// SetRetryAttempts sets the number of retry attempts for failed requests
func (ic *ICMPChecker) SetRetryAttempts(attempts int) {
	ic.retryAttempts = attempts
}

// calculateChecksum calculates the ICMP checksum
func (ic *ICMPChecker) calculateChecksum(data []byte) uint16 {
	var sum uint32
	
	// Group bytes in 16-bit words and add them
	for i := 0; i < len(data)-1; i += 2 {
		sum += uint32(data[i])<<8 | uint32(data[i+1])
	}
	
	// If there's an odd number of bytes, pad with zero
	if len(data)%2 == 1 {
		sum += uint32(data[len(data)-1]) << 8
	}
	
	// Add carry bits
	for sum >> 16 != 0 {
		sum = (sum & 0xFFFF) + (sum >> 16)
	}
	
	// One's complement
	return ^uint16(sum)
}

// createICMPPacket creates an ICMP echo request packet
func (ic *ICMPChecker) createICMPPacket(id, seq uint16) []byte {
	// ICMP header
	header := ICMPHeader{
		Type:       8, // Echo request
		Code:       0,
		Checksum:   0,
		Identifier: id,
		Sequence:   seq,
	}
	
	// Create buffer for header
	buf := new(bytes.Buffer)
	binary.Write(buf, binary.BigEndian, header)
	
	// Add some data payload
	payload := []byte("TunnelVerifier ICMP Check")
	buf.Write(payload)
	
	// Calculate checksum
	packet := buf.Bytes()
	checksum := ic.calculateChecksum(packet)
	
	// Set the checksum in the packet
	binary.BigEndian.PutUint16(packet[2:4], checksum)
	
	return packet
}

// pingTarget performs a ping to the target IP
func (ic *ICMPChecker) pingTarget(targetIP string) *ICMPCheckResult {
	startTime := time.Now()
	
	// Resolve target if it's a hostname
	ipAddr, err := net.ResolveIPAddr("ip4", targetIP)
	if err != nil {
		ic.enhancedLogger.Warn("Failed to resolve target IP", map[string]interface{}{
			"target": targetIP,
			"error":  err.Error(),
		})
		return &ICMPCheckResult{
			Target: targetIP,
			Success: false,
			Error:  err,
		}
	}
	
	// Create ICMP packet
	packet := ic.createICMPPacket(1234, 1) // Using fixed ID and sequence for simplicity
	
	// Create a raw socket connection
	// Note: This requires elevated privileges on most systems
	conn, err := net.DialTimeout("ip4:icmp", ipAddr.IP.String(), ic.timeout)
	if err != nil {
		ic.enhancedLogger.Warn("Failed to create ICMP connection", map[string]interface{}{
			"target": ipAddr.IP.String(),
			"error":  err.Error(),
		})
		return &ICMPCheckResult{
			Target: targetIP,
			Success: false,
			Error:  err,
		}
	}
	defer conn.Close()
	
	// Set deadline for write
	conn.SetWriteDeadline(time.Now().Add(ic.timeout))
	
	// Send the ICMP packet
	_, err = conn.Write(packet)
	if err != nil {
		ic.enhancedLogger.Warn("Failed to send ICMP packet", map[string]interface{}{
			"target": ipAddr.IP.String(),
			"error":  err.Error(),
		})
		return &ICMPCheckResult{
			Target: targetIP,
			Success: false,
			Error:  err,
		}
	}
	
	// Set deadline for read
	conn.SetReadDeadline(time.Now().Add(ic.timeout))
	
	// Read response
	response := make([]byte, 1024)
	n, err := conn.Read(response)
	if err != nil {
		ic.enhancedLogger.Warn("Failed to read ICMP response", map[string]interface{}{
			"target": ipAddr.IP.String(),
			"error":  err.Error(),
		})
		return &ICMPCheckResult{
			Target: targetIP,
			Success: false,
			Error:  err,
		}
	}
	
	responseTime := time.Since(startTime)
	
	ic.enhancedLogger.Debug("ICMP ping successful", map[string]interface{}{
		"target": ipAddr.IP.String(),
		"response_time_ms": responseTime.Milliseconds(),
		"response_size": n,
	})
	
	return &ICMPCheckResult{
		Target:       targetIP,
		ResponseTime: responseTime,
		Success:      true,
		Sequence:     1,
		PacketSize:   n,
	}
}

// CheckICMPConnectivity checks if a target is reachable via ICMP
func (ic *ICMPChecker) CheckICMPConnectivity(target string) *ICMPCheckResult {
	ic.enhancedLogger.Debug("Starting ICMP connectivity check", map[string]interface{}{
		"target": target,
	})
	
	var lastResult *ICMPCheckResult
	var lastErr error
	
	// Retry logic
	for attempt := 0; attempt <= ic.retryAttempts; attempt++ {
		result := ic.pingTarget(target)
		if result.Success {
			ic.enhancedLogger.Debug("ICMP connectivity check successful", map[string]interface{}{
				"target": target,
				"attempt": attempt + 1,
				"response_time_ms": result.ResponseTime.Milliseconds(),
			})
			return result
		}
		
		lastResult = result
		lastErr = result.Error
		
		ic.enhancedLogger.Debug("ICMP request failed, retrying", map[string]interface{}{
			"target":  target,
			"attempt": attempt + 1,
			"error":   result.Error.Error(),
		})
		
		if attempt < ic.retryAttempts {
			// Wait before retrying
			time.Sleep(time.Duration(attempt+1) * time.Second)
		}
	}
	
	ic.enhancedLogger.Warn("ICMP connectivity check failed after retries", map[string]interface{}{
		"target": target,
		"attempts": ic.retryAttempts + 1,
		"error": lastErr.Error(),
	})
	
	// Return the last failed result
	return lastResult
}

// CheckMultipleICMPTargets performs ICMP checks on multiple targets
func (ic *ICMPChecker) CheckMultipleICMPTargets(targets []string) []*ICMPCheckResult {
	ic.enhancedLogger.Info("Starting multiple ICMP target checks", map[string]interface{}{
		"target_count": len(targets),
	})
	
	results := make([]*ICMPCheckResult, 0, len(targets))
	
	for i, target := range targets {
		ic.enhancedLogger.Debug("Checking ICMP target", map[string]interface{}{
			"target": target,
			"index":  i,
		})
		
		result := ic.CheckICMPConnectivity(target)
		results = append(results, result)
	}
	
	// Count successful checks
	successful := 0
	for _, result := range results {
		if result.Success {
			successful++
		}
	}
	
	ic.enhancedLogger.Info("Multiple ICMP target checks completed", map[string]interface{}{
		"total_checks":  len(results),
		"successful":    successful,
		"failed":        len(results) - successful,
		"success_rate":  float64(successful) / float64(len(results)) * 100,
	})
	
	return results
}

// CheckICMPLatency performs a latency check using ICMP
func (ic *ICMPChecker) CheckICMPLatency(target string) (time.Duration, error) {
	result := ic.CheckICMPConnectivity(target)
	if !result.Success {
		return 0, result.Error
	}
	
	return result.ResponseTime, nil
}

// PerformICMPTraceroute performs a simplified traceroute using ICMP
func (ic *ICMPChecker) PerformICMPTraceroute(target string, maxHops int) ([]*ICMPCheckResult, error) {
	ic.enhancedLogger.Info("Starting ICMP traceroute", map[string]interface{}{
		"target": target,
		"max_hops": maxHops,
	})
	
	results := make([]*ICMPCheckResult, 0, maxHops)
	
	// Note: Real traceroute requires setting IP TTL and handling ICMP "Time Exceeded" messages
	// This is a simplified version that just tests reachability
	for hop := 1; hop <= maxHops; hop++ {
		// In a real implementation, we would set the TTL to 'hop' and expect 
		// ICMP "Time Exceeded" messages until we reach the destination
		// For now, we'll just check if the target is reachable
		
		result := ic.CheckICMPConnectivity(target)
		results = append(results, result)
		
		if result.Success {
			ic.enhancedLogger.Info("Traceroute completed - target reached", map[string]interface{}{
				"target": target,
				"hop":    hop,
				"response_time_ms": result.ResponseTime.Milliseconds(),
			})
			break
		}
		
		// If we want to implement real traceroute, we'd need to use lower-level networking
		// which might require elevated privileges
		
		// For this implementation, we'll just break after first attempt
		break
	}
	
	return results, nil
}

// IsPrivilegedPlatform checks if the platform supports raw ICMP sockets
// This is a simplified check - in real implementation, additional checks might be needed
func (ic *ICMPChecker) IsPrivilegedPlatform() bool {
	// On Unix-like systems, ICMP requires root privileges
	// On Windows, it requires administrator privileges
	// For this implementation, we'll assume it's available if not in restricted env
	return true // Simplified check
}

// CreateICMPCheckerWithValidation creates an ICMPChecker with validation of platform capability
func NewICMPCheckerWithValidation(logger *Logger) (*ICMPChecker, error) {
	checker := NewICMPChecker(logger)
	
	// For this simplified implementation, we'll just return the checker
	// In a real implementation, we would validate if raw sockets are available
	
	if !checker.IsPrivilegedPlatform() {
		return nil, fmt.Errorf("ICMP checks not supported on this platform - requires elevated privileges")
	}
	
	return checker, nil
}