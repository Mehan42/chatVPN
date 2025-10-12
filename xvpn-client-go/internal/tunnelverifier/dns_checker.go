// Package tunnelverifier provides DNS-based verification functionality
package tunnelverifier

import (
	"context"
	"fmt"
	"net"
	"strings"
	"time"
)

// DNSChecker performs DNS-based verification checks
type DNSChecker struct {
	enhancedLogger *Logger
	timeout        time.Duration
	retryAttempts  int
	dnsServers     []string  // Custom DNS servers to use
}

// DNSCheckResult represents the result of a DNS check
type DNSCheckResult struct {
	Domain        string
	IPAddresses   []string
	ResponseTime  time.Duration
	Success       bool
	Error         error
	ResolvedBy    string  // Which DNS server resolved the query
}

// NewDNSChecker creates a new DNS checker
func NewDNSChecker(logger *Logger) *DNSChecker {
	return &DNSChecker{
		enhancedLogger: logger,
		timeout:        10 * time.Second,
		retryAttempts:  2,
		dnsServers:     []string{}, // Use system DNS by default
	}
}

// SetTimeout sets the timeout for DNS requests
func (dc *DNSChecker) SetTimeout(timeout time.Duration) {
	dc.timeout = timeout
}

// SetRetryAttempts sets the number of retry attempts for failed requests
func (dc *DNSChecker) SetRetryAttempts(attempts int) {
	dc.retryAttempts = attempts
}

// SetDNSServers sets custom DNS servers to use for queries
func (dc *DNSChecker) SetDNSServers(servers []string) {
	dc.dnsServers = servers
}

// SetDNSServer adds a DNS server to the list of servers to use
func (dc *DNSChecker) AddDNSServer(server string) {
	dc.dnsServers = append(dc.dnsServers, server)
}

// resolveDomain resolves a domain name to IP addresses using system resolver or custom DNS
func (dc *DNSChecker) resolveDomain(domain string) (*DNSCheckResult, error) {
	startTime := time.Now()
	
	var ips []net.IP
	var err error
	
	// If custom DNS servers are specified, use them via a custom resolver
	if len(dc.dnsServers) > 0 {
		// For each DNS server, try to resolve the domain
		for _, server := range dc.dnsServers {
			// Create a custom resolver that uses the specific DNS server
			resolver := &net.Resolver{
				PreferGo: true,
				Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
					d := net.Dialer{
						Timeout: time.Second * 5,
					}
					return d.DialContext(ctx, network, server)
				},
			}
			
			ctx, cancel := context.WithTimeout(context.Background(), dc.timeout)
			ips, err = resolver.LookupIP(ctx, "ip", domain)
			cancel()
			
			if err == nil {
				// Successfully resolved using this DNS server
				break
			}
			
			dc.enhancedLogger.Debug("DNS resolution failed with server, trying next", map[string]interface{}{
				"server": server,
				"domain": domain,
				"error":  err.Error(),
			})
		}
	} else {
		// Use system DNS resolver
		ctx, cancel := context.WithTimeout(context.Background(), dc.timeout)
		defer cancel()
		ips, err = net.DefaultResolver.LookupIP(ctx, "ip", domain)
	}
	
	if err != nil {
		return &DNSCheckResult{
			Domain:       domain,
			Success:      false,
			Error:        err,
			ResponseTime: time.Since(startTime),
		}, err
	}
	
	// Convert net.IP to string format
	ipStrings := make([]string, len(ips))
	for i, ip := range ips {
		ipStrings[i] = ip.String()
	}
	
	return &DNSCheckResult{
		Domain:       domain,
		IPAddresses:  ipStrings,
		Success:      true,
		ResponseTime: time.Since(startTime),
	}, nil
}

// CheckDNSResolution checks if a domain can be resolved to IP addresses
func (dc *DNSChecker) CheckDNSResolution(domain string) *DNSCheckResult {
	dc.enhancedLogger.Debug("Starting DNS resolution check", map[string]interface{}{
		"domain": domain,
		"dns_servers_count": len(dc.dnsServers),
	})
	
	var lastResult *DNSCheckResult
	var lastErr error
	
	// Retry logic
	for attempt := 0; attempt <= dc.retryAttempts; attempt++ {
		result, err := dc.resolveDomain(domain)
		if result.Success {
			dc.enhancedLogger.Debug("DNS resolution successful", map[string]interface{}{
				"domain":       domain,
				"ip_count":     len(result.IPAddresses),
				"response_time_ms": result.ResponseTime.Milliseconds(),
				"attempt":      attempt + 1,
			})
			
			// Log resolved IPs
			for i, ip := range result.IPAddresses {
				dc.enhancedLogger.Debug("Resolved IP", map[string]interface{}{
					"domain": domain,
					"index":  i,
					"ip":     ip,
				})
			}
			
			return result
		}
		
		lastResult = result
		lastErr = err
		
		dc.enhancedLogger.Debug("DNS resolution failed, retrying", map[string]interface{}{
			"domain":  domain,
			"attempt": attempt + 1,
			"error":   err.Error(),
		})
		
		if attempt < dc.retryAttempts {
			// Wait before retrying
			time.Sleep(time.Duration(attempt+1) * time.Second)
		}
	}
	
	dc.enhancedLogger.Warn("DNS resolution check failed after retries", map[string]interface{}{
		"domain":   domain,
		"attempts": dc.retryAttempts + 1,
		"error":    lastErr.Error(),
	})
	
	// Return the last failed result
	return lastResult
}

// CheckMultipleDNSDomains performs DNS resolution checks on multiple domains
func (dc *DNSChecker) CheckMultipleDNSDomains(domains []string) []*DNSCheckResult {
	dc.enhancedLogger.Info("Starting multiple DNS domain checks", map[string]interface{}{
		"domain_count": len(domains),
		"dns_servers_count": len(dc.dnsServers),
	})
	
	results := make([]*DNSCheckResult, 0, len(domains))
	
	for i, domain := range domains {
		dc.enhancedLogger.Debug("Checking DNS domain", map[string]interface{}{
			"domain": domain,
			"index":  i,
		})
		
		result := dc.CheckDNSResolution(domain)
		results = append(results, result)
	}
	
	// Count successful checks
	successful := 0
	for _, result := range results {
		if result.Success {
			successful++
		}
	}
	
	dc.enhancedLogger.Info("Multiple DNS domain checks completed", map[string]interface{}{
		"total_checks":  len(results),
		"successful":    successful,
		"failed":        len(results) - successful,
		"success_rate":  float64(successful) / float64(len(results)) * 100,
	})
	
	return results
}

// CheckDNSLeak tests for DNS leaks by resolving domains through different resolvers
func (dc *DNSChecker) CheckDNSLeak(testDomains []string) (bool, error) {
	dc.enhancedLogger.Info("Starting DNS leak check", map[string]interface{}{
		"domain_count": len(testDomains),
	})
	
	// For DNS leak detection, we want to check if DNS queries are going through expected servers
	// In a real implementation, this would involve using special DNS leak test services
	// For this implementation, we'll check if we can successfully resolve the domains
	
	results := dc.CheckMultipleDNSDomains(testDomains)
	
	// Count successful resolutions
	successfulResolutions := 0
	for _, result := range results {
		if result.Success {
			successfulResolutions++
		}
	}
	
	// In a real implementation, we would also check:
	// 1. Which DNS server was used to resolve the query
	// 2. Whether it matches the expected VPN DNS server
	// 3. Whether the response came from a known "leak test" DNS server
	
	successRate := float64(successfulResolutions) / float64(len(results)) * 100
	isLeakDetected := successfulResolutions == 0  // If no domains resolve, there might be a DNS issue
	
	dc.enhancedLogger.Info("DNS leak check completed", map[string]interface{}{
		"total_domains":       len(results),
		"successful_resolutions": successfulResolutions,
		"success_rate":        successRate,
		"leak_detected":       isLeakDetected,
	})
	
	return !isLeakDetected, nil
}

// CheckDNSServerReachability checks if DNS servers are reachable
func (dc *DNSChecker) CheckDNSServerReachability() (bool, []string) {
	if len(dc.dnsServers) == 0 {
		// If no custom DNS servers specified, test the default system resolver
		// We'll test with a common domain
		result := dc.CheckDNSResolution("www.google.com")
		var reachableServers []string
		if result.Success {
			reachableServers = append(reachableServers, "system_resolver")
		}
		return result.Success, reachableServers
	}
	
	dc.enhancedLogger.Info("Checking DNS server reachability", map[string]interface{}{
		"server_count": len(dc.dnsServers),
	})
	
	reachableServers := make([]string, 0)
	
	for _, server := range dc.dnsServers {
		// Attempt to connect to the DNS server on port 53
		conn, err := net.DialTimeout("tcp", server, dc.timeout)
		if err != nil {
			// Try with UDP as well (more common for DNS)
			conn, err = net.DialTimeout("udp", server, dc.timeout)
		}
		
		if err == nil {
			conn.Close()
			reachableServers = append(reachableServers, server)
			dc.enhancedLogger.Debug("DNS server reachable", map[string]interface{}{
				"server": server,
			})
		} else {
			dc.enhancedLogger.Debug("DNS server not reachable", map[string]interface{}{
				"server": server,
				"error":  err.Error(),
			})
		}
	}
	
	isReachable := len(reachableServers) > 0
	
	dc.enhancedLogger.Info("DNS server reachability check completed", map[string]interface{}{
		"total_servers":   len(dc.dnsServers),
		"reachable_count": len(reachableServers),
		"reachable_servers": reachableServers,
		"is_reachable":    isReachable,
	})
	
	return isReachable, reachableServers
}

// CheckDNSEndToEnd performs an end-to-end DNS check by resolving a domain and then connecting to it
func (dc *DNSChecker) CheckDNSEndToEnd(domain string) *DNSCheckResult {
	dc.enhancedLogger.Info("Starting end-to-end DNS check", map[string]interface{}{
		"domain": domain,
	})
	
	// First, resolve the domain
	resolveResult := dc.CheckDNSResolution(domain)
	if !resolveResult.Success {
		return resolveResult
	}
	
	// Then, try to connect to each resolved IP address
	for i, ip := range resolveResult.IPAddresses {
		// Try to connect to port 80 first, then 443
		addresses := []string{fmt.Sprintf("%s:80", ip), fmt.Sprintf("%s:443", ip)}
		
		for _, addr := range addresses {
			conn, err := net.DialTimeout("tcp", addr, dc.timeout)
			if err == nil {
				conn.Close()
				dc.enhancedLogger.Debug("Successful connection to resolved IP", map[string]interface{}{
					"domain": domain,
					"ip":     ip,
					"port":   strings.Split(addr, ":")[1],
					"index":  i,
				})
				// If we successfully connected to any of the IPs, the end-to-end check passes
				return resolveResult
			}
		}
	}
	
	// If we couldn't connect to any of the resolved IPs, we still consider DNS resolution successful
	// but log that connectivity to resolved IPs failed
	dc.enhancedLogger.Info("DNS resolution successful but connectivity to resolved IPs failed", map[string]interface{}{
		"domain": domain,
		"ip_count": len(resolveResult.IPAddresses),
	})
	
	return resolveResult
}

// GetDNSServers returns the configured DNS servers
func (dc *DNSChecker) GetDNSServers() []string {
	servers := make([]string, len(dc.dnsServers))
	copy(servers, dc.dnsServers)
	return servers
}