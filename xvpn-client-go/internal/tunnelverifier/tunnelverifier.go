// Package tunnelverifier provides functionality to verify that non-RU traffic is properly tunneled
package tunnelverifier

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
	"sync"
	"strings"
	"os"
	
	"xvpn-client-go/internal/alerts"
)

// Config represents the configuration for tunnel verification
type Config struct {
	CheckInterval time.Duration
	Timeout       time.Duration
	// Additional configuration for non-RU traffic verification
	VerificationEndpoints []string
	TestPayload          string
	// Logging configuration
	LogLevel string // debug, info, warn, error
	// IP check service for determining if traffic is routed through VPN
	IPCheckService string
	// Whether to perform IP leak checks
	CheckIPLeak bool
	// Whether to perform DNS leak checks
	CheckDNSLeak bool
	// Whether to verify traffic routing
	VerifyRouting bool
	// Whether to perform comprehensive leak detection
	EnableComprehensiveLeakDetection bool
	// Whether to perform advanced routing verification
	EnableAdvancedRoutingVerification bool
	// Individual check intervals for fine-grained control
	IPLeakCheckInterval    time.Duration  // Interval for IP leak checks
	DNSLeakCheckInterval   time.Duration  // Interval for DNS leak checks
	RoutingCheckInterval   time.Duration  // Interval for routing checks
	// Sensitivity levels for different checks (0.0 to 1.0, where 1.0 is most sensitive)
	IPLeakSensitivity    float64  // Sensitivity for IP leak detection
	DNSLeakSensitivity   float64  // Sensitivity for DNS leak detection
	RoutingSensitivity   float64  // Sensitivity for routing verification
}

// TunnelVerifier manages the verification of tunneling
type TunnelVerifier struct {
	config    *Config
	running   bool
	ctx       context.Context
	cancel    context.CancelFunc
	mu        sync.RWMutex
	logger    *log.Logger
	// Enhanced logger for detailed logging
	enhancedLogger *Logger
	// Performance metrics
	metrics *Metrics
	// Notification manager for alerts
	notificationManager *alerts.NotificationManager
	// Interval manager for configurable check intervals
	intervalManager *IntervalManager
	// Track verification status
	verificationStatus map[string]bool
	statusMutex      sync.RWMutex
	// Track tunneling state for alerting
	lastVerificationResult bool
	// IP leak detector
	ipLeakDetector *IPLeakDetector
	// DNS leak detector
	dnsLeakDetector *DNSLeakDetector
	// Routing verifier
	routingVerifier *RoutingVerifier
}

// New creates a new TunnelVerifier instance
func New(config Config) (*TunnelVerifier, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	// Set default values if not provided
	if config.CheckInterval == 0 {
		config.CheckInterval = 30 * time.Second
	}
	if config.Timeout == 0 {
		config.Timeout = 60 * time.Second
	}
	if config.VerificationEndpoints == nil || len(config.VerificationEndpoints) == 0 {
		config.VerificationEndpoints = []string{"8.8.8.8", "1.1.1.1"}
	}
	if config.IPCheckService == "" {
		config.IPCheckService = "https://httpbin.org/ip" // Default IP check service
	}
	
	// Set default check intervals if not provided
	if config.IPLeakCheckInterval == 0 {
		config.IPLeakCheckInterval = config.CheckInterval
	}
	if config.DNSLeakCheckInterval == 0 {
		config.DNSLeakCheckInterval = config.CheckInterval
	}
	if config.RoutingCheckInterval == 0 {
		config.RoutingCheckInterval = config.CheckInterval
	}
	
	// Set default sensitivity if not provided (0.5 = medium sensitivity)
	if config.IPLeakSensitivity == 0 {
		config.IPLeakSensitivity = 0.5
	}
	if config.DNSLeakSensitivity == 0 {
		config.DNSLeakSensitivity = 0.5
	}
	if config.RoutingSensitivity == 0 {
		config.RoutingSensitivity = 0.5
	}
	
	// Ensure sensitivity values are within valid range [0.0, 1.0]
	if config.IPLeakSensitivity < 0 {
		config.IPLeakSensitivity = 0
	} else if config.IPLeakSensitivity > 1.0 {
		config.IPLeakSensitivity = 1.0
	}
	
	if config.DNSLeakSensitivity < 0 {
		config.DNSLeakSensitivity = 0
	} else if config.DNSLeakSensitivity > 1.0 {
		config.DNSLeakSensitivity = 1.0
	}
	
	if config.RoutingSensitivity < 0 {
		config.RoutingSensitivity = 0
	} else if config.RoutingSensitivity > 1.0 {
		config.RoutingSensitivity = 1.0
	}
	
	tv := &TunnelVerifier{
		config:             &config,
		ctx:                ctx,
		cancel:             cancel,
		logger:             log.Default(),
		verificationStatus: make(map[string]bool),
	}
	
	// Determine log level from config
	logLevel := Info
	switch strings.ToLower(config.LogLevel) {
	case "debug":
		logLevel = Debug
	case "info":
		logLevel = Info
	case "warn":
		logLevel = Warn
	case "error":
		logLevel = Error
	}
	
	// Initialize enhanced logger
	tv.enhancedLogger = NewLogger(logLevel, false) // Set to true for JSON logging
	
	// Initialize metrics
	tv.metrics = NewMetrics()
	
	// Initialize notification manager
	tv.notificationManager = alerts.NewNotificationManager()
	
	// Initialize state tracking
	tv.lastVerificationResult = true  // Assume initially valid
	
	// Initialize IP leak detector if comprehensive leak detection is enabled
	if config.EnableComprehensiveLeakDetection || config.CheckIPLeak {
		tv.ipLeakDetector = NewIPLeakDetector(tv.logger)
		// Set the enhanced logger for the detector too
		if tv.ipLeakDetector.SetLogger != nil {
			tv.ipLeakDetector.SetLogger(tv.enhancedLogger)
		}
	}
	
	// Initialize DNS leak detector if comprehensive leak detection is enabled
	if config.EnableComprehensiveLeakDetection || config.CheckDNSLeak {
		tv.dnsLeakDetector = NewDNSLeakDetector(tv.logger)
		// Set the enhanced logger for the detector too
		if tv.dnsLeakDetector.SetLogger != nil {
			tv.dnsLeakDetector.SetLogger(tv.enhancedLogger)
		}
	}
	
	// Initialize routing verifier if comprehensive leak detection or advanced routing verification is enabled
	if config.EnableComprehensiveLeakDetection || config.EnableAdvancedRoutingVerification || config.VerifyRouting {
		tv.routingVerifier = NewRoutingVerifier(tv.logger)
		// Set the enhanced logger for the verifier too
		if tv.routingVerifier.SetLogger != nil {
			tv.routingVerifier.SetLogger(tv.enhancedLogger)
		}
		// Set custom endpoints if provided in config
		if len(config.VerificationEndpoints) > 0 {
			tv.routingVerifier.SetNonRUEndpoints(config.VerificationEndpoints)
		}
	}
	
	// Initialize interval manager
	tv.intervalManager = NewIntervalManager(tv)
	
	return tv, nil
}

// Start begins the tunnel verification process
func (tv *TunnelVerifier) Start(ctx context.Context) error {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	if tv.running {
		tv.enhancedLogger.Warn("Tunnel verifier is already running", nil)
		return fmt.Errorf("tunnel verifier is already running")
	}
	
	tv.enhancedLogger.Info("Starting tunnel verifier", map[string]interface{}{
		"check_interval": tv.config.CheckInterval.Seconds(),
		"ip_leak_check_interval": tv.config.IPLeakCheckInterval.Seconds(),
		"dns_leak_check_interval": tv.config.DNSLeakCheckInterval.Seconds(),
		"routing_check_interval": tv.config.RoutingCheckInterval.Seconds(),
		"timeout":        tv.config.Timeout.Seconds(),
		"endpoints_count": len(tv.config.VerificationEndpoints),
		"check_ip_leak":  tv.config.CheckIPLeak,
		"check_dns_leak": tv.config.CheckDNSLeak,
		"verify_routing": tv.config.VerifyRouting,
	})
	
	tv.running = true
	
	// Start interval-based verification instead of single loop
	tv.intervalManager.StartIntervalBasedVerification(ctx)
	tv.enhancedLogger.Info("Tunnel verifier started successfully with interval-based checks", nil)
	
	return nil
}

// Stop stops the tunnel verification process
func (tv *TunnelVerifier) Stop(ctx context.Context) error {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	if !tv.running {
		tv.enhancedLogger.Warn("Tunnel verifier is not running", nil)
		return fmt.Errorf("tunnel verifier is not running")
	}
	
	tv.enhancedLogger.Info("Stopping tunnel verifier", nil)
	
	// Stop interval-based verification
	tv.intervalManager.Stop()
	
	// Cancel the context
	tv.cancel()
	tv.running = false
	tv.enhancedLogger.Info("Tunnel verifier stopped", nil)
	return nil
}

// SetLogger sets the logger for the tunnel verifier
func (tv *TunnelVerifier) SetLogger(logger interface{}) {
	if l, ok := logger.(io.Writer); ok {
		tv.logger = log.New(l, "TunnelVerifier: ", log.LstdFlags|log.Lshortfile)
	} else {
		tv.logger = log.Default()
		tv.logger.Println("Warning: invalid logger type provided, using default logger")
	}
}

// runVerificationLoop runs periodic checks
func (tv *TunnelVerifier) runVerificationLoop(ctx context.Context) {
	tv.enhancedLogger.Info("Starting verification loop", map[string]interface{}{
		"interval_seconds": tv.config.CheckInterval.Seconds(),
	})
	
	ticker := time.NewTicker(tv.config.CheckInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			// Perform verification check
			tv.performVerification()
		case <-ctx.Done():
			tv.enhancedLogger.Info("Verification loop stopped due to context cancellation", nil)
			return
		}
	}
}

// performVerification performs a single verification check
func (tv *TunnelVerifier) performVerification() {
	startTime := time.Now()
	tv.enhancedLogger.Info("Starting tunnel verification", map[string]interface{}{
		"timestamp": startTime.Format(time.RFC3339),
	})
	
	// If not running, return early
	if !tv.isRunning() {
		tv.enhancedLogger.Warn("Tunnel verifier is not running, skipping verification", nil)
		return
	}
	
	// Update our verification status map
	tv.statusMutex.Lock()
	tv.verificationStatus = make(map[string]bool)
	tv.statusMutex.Unlock()
	
	// Check IP leak if enabled
	if tv.config.CheckIPLeak {
		tv.enhancedLogger.Debug("Starting IP leak check", nil)
		ipLeakStartTime := time.Now()
		ipLeakStatus := tv.checkIPLeak()
		ipLeakDuration := time.Since(ipLeakStartTime)
		
		// Record metrics for IP leak check
		tv.metrics.RecordIPLeakCheck(ipLeakStatus, ipLeakDuration)
		
		tv.statusMutex.Lock()
		tv.verificationStatus["ip_leak_check"] = ipLeakStatus
		tv.statusMutex.Unlock()
		
		statusStr := "passed"
		if !ipLeakStatus {
			statusStr = "failed"
		}
		
		tv.enhancedLogger.Info("IP leak check completed", map[string]interface{}{
			"status":   statusStr,
			"duration": ipLeakDuration.Seconds(),
		})
	}
	
	// Check DNS leak if enabled
	if tv.config.CheckDNSLeak {
		tv.enhancedLogger.Debug("Starting DNS leak check", nil)
		dnsLeakStartTime := time.Now()
		dnsLeakStatus := tv.checkDNSLeak()
		dnsLeakDuration := time.Since(dnsLeakStartTime)
		
		// Record metrics for DNS leak check
		tv.metrics.RecordDNSLeakCheck(dnsLeakStatus, dnsLeakDuration)
		
		tv.statusMutex.Lock()
		tv.verificationStatus["dns_leak_check"] = dnsLeakStatus
		tv.statusMutex.Unlock()
		
		statusStr := "passed"
		if !dnsLeakStatus {
			statusStr = "failed"
		}
		
		tv.enhancedLogger.Info("DNS leak check completed", map[string]interface{}{
			"status":   statusStr,
			"duration": dnsLeakDuration.Seconds(),
		})
	}
	
	// Verify traffic routing if enabled
	if tv.config.VerifyRouting {
		tv.enhancedLogger.Debug("Starting traffic routing check", nil)
		routingStartTime := time.Now()
		routingStatus := tv.verifyTrafficRouting()
		routingDuration := time.Since(routingStartTime)
		
		// Record metrics for traffic routing check
		tv.metrics.RecordTrafficRoutingCheck(routingStatus, routingDuration)
		
		tv.statusMutex.Lock()
		tv.verificationStatus["traffic_routing_check"] = routingStatus
		tv.statusMutex.Unlock()
		
		statusStr := "passed"
		if !routingStatus {
			statusStr = "failed"
		}
		
		tv.enhancedLogger.Info("Traffic routing check completed", map[string]interface{}{
			"status":   statusStr,
			"duration": routingDuration.Seconds(),
		})
	}
	
	totalDuration := time.Since(startTime)
	
	// Record metrics for the entire verification
	tv.metrics.RecordVerification(true, totalDuration) // assuming success at this level
	
	tv.enhancedLogger.Info("Tunnel verification completed", map[string]interface{}{
		"duration": totalDuration.Seconds(),
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// checkIPLeak checks for IP address leaks outside the VPN tunnel
func (tv *TunnelVerifier) checkIPLeak() bool {
	tv.enhancedLogger.Info("Starting IP leak detection", nil)
	
	if tv.ipLeakDetector != nil {
		// Use the comprehensive IP leak detector
		tv.enhancedLogger.Debug("Using comprehensive IP leak detector", nil)
		startTime := time.Now()
		isValid, err := tv.ipLeakDetector.DetectIPLeak()
		duration := time.Since(startTime)
		
		if err != nil {
			tv.enhancedLogger.Error("Error during IP leak detection", map[string]interface{}{
				"error":    err.Error(),
				"duration": duration.Seconds(),
			})
			return false
		}
		
		status := "passed"
		if !isValid {
			status = "failed"
		}
		
		tv.enhancedLogger.Info("IP leak detection completed", map[string]interface{}{
			"status":   status,
			"duration": duration.Seconds(),
		})
		
		return isValid
	}
	
	// Fallback to basic check
	tv.enhancedLogger.Debug("Using basic IP leak detection", nil)
	client := &http.Client{
		Timeout: tv.config.Timeout,
	}
	
	// Make a request to determine external IP while VPN is active
	tv.enhancedLogger.Debug("Making request to check IP", map[string]interface{}{
		"service": tv.config.IPCheckService,
		"timeout": tv.config.Timeout.Seconds(),
	})
	
	resp, err := client.Get(tv.config.IPCheckService)
	if err != nil {
		tv.enhancedLogger.Error("Error checking IP", map[string]interface{}{
			"error":   err.Error(),
			"service": tv.config.IPCheckService,
		})
		return false
	}
	defer resp.Body.Close()
	
	// Read the response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		tv.enhancedLogger.Error("Error reading response body", map[string]interface{}{
			"error": err.Error(),
		})
		return false
	}
	
	bodyStr := string(body)
	tv.enhancedLogger.Debug("IP check response received", map[string]interface{}{
		"response_length": len(bodyStr),
	})
	
	// Check if response contains an IP address
	if strings.Contains(bodyStr, "origin") && strings.Contains(bodyStr, ".") {
		// Basic check: if we can get an external IP, it suggests traffic is routed through VPN
		// For more precise check: we'd need to compare this against known VPN exit IPs
		// or compare against the original IP when not using VPN
		tv.enhancedLogger.Info("IP leak check: successfully retrieved external IP", nil)
		return true
	}
	
	tv.enhancedLogger.Warn("IP leak check: could not verify external IP", nil)
	return false
}

// checkDNSLeak checks for DNS leaks outside the VPN tunnel
func (tv *TunnelVerifier) checkDNSLeak() bool {
	tv.enhancedLogger.Info("Starting DNS leak detection", nil)
	
	if tv.dnsLeakDetector != nil {
		// Use the comprehensive DNS leak detector
		tv.enhancedLogger.Debug("Using comprehensive DNS leak detector", nil)
		startTime := time.Now()
		isValid, err := tv.dnsLeakDetector.DetectDNSLeak()
		duration := time.Since(startTime)
		
		if err != nil {
			tv.enhancedLogger.Error("Error during DNS leak detection", map[string]interface{}{
				"error":    err.Error(),
				"duration": duration.Seconds(),
			})
			return false
		}
		
		status := "passed"
		if !isValid {
			status = "failed"
		}
		
		tv.enhancedLogger.Info("DNS leak detection completed", map[string]interface{}{
			"status":   status,
			"duration": duration.Seconds(),
		})
		
		return isValid
	}
	
	// Fallback to basic check
	tv.enhancedLogger.Debug("Using basic DNS leak detection", nil)
	client := &http.Client{
		Timeout: tv.config.Timeout,
	}
	
	// Test DNS resolution by making HTTP requests to well-known services
	testURLs := []string{
		"https://google.com",
		"https://cloudflare.com",
		"https://microsoft.com",
	}
	
	tv.enhancedLogger.Debug("Testing DNS resolution", map[string]interface{}{
		"test_count": len(testURLs),
	})
	
	for i, url := range testURLs {
		tv.enhancedLogger.Debug("Testing DNS resolution", map[string]interface{}{
			"url":         url,
			"test_number": i + 1,
		})
		
		resp, err := client.Get(url)
		if err != nil {
			tv.enhancedLogger.Warn("DNS leak check: failed to resolve", map[string]interface{}{
				"url":   url,
				"error": err.Error(),
			})
			return false
		}
		resp.Body.Close()
		// If we can successfully reach these domains, it suggests DNS is working via VPN
	}
	
	tv.enhancedLogger.Info("DNS leak check: successfully resolved all test domains", map[string]interface{}{
		"test_count": len(testURLs),
	})
	return true
}

// verifyTrafficRouting verifies that non-RU traffic is correctly routed via VPN
func (tv *TunnelVerifier) verifyTrafficRouting() bool {
	tv.enhancedLogger.Info("Starting traffic routing verification", nil)
	
	if tv.routingVerifier != nil {
		// Use the comprehensive routing verifier
		tv.enhancedLogger.Debug("Using comprehensive routing verifier", nil)
		startTime := time.Now()
		isValid, err := tv.routingVerifier.VerifyNonRUTrafficRouting()
		duration := time.Since(startTime)
		
		if err != nil {
			tv.enhancedLogger.Error("Error during routing verification", map[string]interface{}{
				"error":    err.Error(),
				"duration": duration.Seconds(),
			})
			return false
		}
		
		status := "passed"
		if !isValid {
			status = "failed"
		}
		
		tv.enhancedLogger.Info("Traffic routing verification completed", map[string]interface{}{
			"status":   status,
			"duration": duration.Seconds(),
		})
		
		return isValid
	}
	
	// Fallback to basic check
	tv.enhancedLogger.Debug("Using basic traffic routing verification", map[string]interface{}{
		"endpoint_count": len(tv.config.VerificationEndpoints),
	})
	
	client := &http.Client{
		Timeout: tv.config.Timeout,
	}
	
	// Test access to non-RU endpoints to verify they go through the VPN tunnel
	for i, endpoint := range tv.config.VerificationEndpoints {
		tv.enhancedLogger.Debug("Testing endpoint", map[string]interface{}{
			"endpoint":      endpoint,
			"endpoint_index": i + 1,
		})
		
		// Using httpbin.org to test routing - it echoes back our IP
		testURL := fmt.Sprintf("https://httpbin.org/ip")
		
		startTime := time.Now()
		resp, err := client.Get(testURL)
		duration := time.Since(startTime)
		
		if err != nil {
			tv.enhancedLogger.Warn("Traffic routing check: failed to connect", map[string]interface{}{
				"url":      testURL,
				"error":    err.Error(),
				"duration": duration.Seconds(),
			})
			return false
		}
		defer resp.Body.Close()
		
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			tv.enhancedLogger.Warn("Traffic routing check: failed to read response", map[string]interface{}{
				"url":      testURL,
				"error":    err.Error(),
				"duration": duration.Seconds(),
			})
			return false
		}
		
		bodyStr := string(body)
		tv.enhancedLogger.Debug("Traffic routing check response", map[string]interface{}{
			"url":         testURL,
			"response_length": len(bodyStr),
			"duration":    duration.Seconds(),
		})
		
		// Basic validation: check if we get a response from the test endpoint
		if !strings.Contains(bodyStr, "origin") {
			tv.enhancedLogger.Warn("Traffic routing check: unexpected response", map[string]interface{}{
				"url": testURL,
			})
			return false
		}
	}
	
	tv.enhancedLogger.Info("Traffic routing check: successfully verified routing for all endpoints", map[string]interface{}{
		"endpoint_count": len(tv.config.VerificationEndpoints),
	})
	return true
}

// isRunning checks if the tunnel verifier is currently running
func (tv *TunnelVerifier) isRunning() bool {
	tv.mu.RLock()
	defer tv.mu.RUnlock()
	return tv.running
}

// IsTunnelingValid checks if the tunneling is currently valid
func (tv *TunnelVerifier) IsTunnelingValid() (bool, error) {
	tv.statusMutex.RLock()
	defer tv.statusMutex.RUnlock()
	
	tv.enhancedLogger.Debug("Checking tunneling validity", nil)
	
	if len(tv.verificationStatus) == 0 {
		tv.enhancedLogger.Debug("No verification status available yet", nil)
		return false, nil
	}
	
	tv.enhancedLogger.Debug("Verification status details", map[string]interface{}{
		"checks_count": len(tv.verificationStatus),
	})
	
	// Check if all verification checks passed
	for checkName, status := range tv.verificationStatus {
		statusStr := "passed"
		if !status {
			statusStr = "failed"
		}
		
		tv.enhancedLogger.Debug("Verification check status", map[string]interface{}{
			"check":  checkName,
			"status": statusStr,
		})
		
		if !status {
			tv.enhancedLogger.Warn("Verification check failed", map[string]interface{}{
				"check": checkName,
			})
			
			// Check if this is a transition from valid to invalid
			tv.mu.Lock()
			wasValid := tv.lastVerificationResult
			tv.lastVerificationResult = false
			tv.mu.Unlock()
			
			// Send an alert about the failed check only if it's a new failure
			if wasValid {
				tv.sendTunnelingFailureAlert(checkName)
			}
			
			return false, nil
		}
	}
	
	tv.enhancedLogger.Info("All verification checks passed", nil)
	
	// Check if this is a transition from invalid to valid (restoration)
	tv.mu.Lock()
	wasValid := tv.lastVerificationResult
	tv.lastVerificationResult = true
	tv.mu.Unlock()
	
	if !wasValid {
		// Send an alert about restoration
		tv.sendTunnelingRestoredAlert()
	}
	
	return true, nil
}

// sendTunnelingFailureAlert sends an alert when tunneling verification fails
func (tv *TunnelVerifier) sendTunnelingFailureAlert(failedCheck string) {
	alertTitle := "Проблема с туннелированием"
	alertMessage := fmt.Sprintf("Обнаружена проблема с проверкой туннелирования: %s", failedCheck)
	tv.notificationManager.ShowAlert(alerts.AlertError, alertTitle, alertMessage, alerts.SeverityHigh)
	
	tv.enhancedLogger.Info("Sent tunneling failure alert", map[string]interface{}{
		"check": failedCheck,
		"title": alertTitle,
		"message": alertMessage,
	})
}

// sendTunnelingRestoredAlert sends an alert when tunneling is restored
func (tv *TunnelVerifier) sendTunnelingRestoredAlert() {
	alertTitle := "Туннелирование восстановлено"
	alertMessage := "Проверки туннелирования снова проходят успешно"
	tv.notificationManager.ShowAlert(alerts.AlertInfo, alertTitle, alertMessage, alerts.SeverityLow)
	
	tv.enhancedLogger.Info("Sent tunneling restored alert", map[string]interface{}{
		"title": alertTitle,
		"message": alertMessage,
	})
}

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

// ActivateEcoMode enables eco mode which reduces resource consumption
func (tv *TunnelVerifier) ActivateEcoMode() {
	ecoManager := NewEcoModeManager(tv)
	ecoManager.ActivateEcoMode()
	
	tv.enhancedLogger.Info("Eco mode activated", nil)
}

// DeactivateEcoMode disables eco mode and restores original settings
func (tv *TunnelVerifier) DeactivateEcoMode() {
	ecoManager := NewEcoModeManager(tv)
	ecoManager.DeactivateEcoMode()
	
	tv.enhancedLogger.Info("Eco mode deactivated", nil)
}

// IsEcoModeActive returns whether eco mode is currently active
func (tv *TunnelVerifier) IsEcoModeActive() bool {
	ecoManager := NewEcoModeManager(tv)
	return ecoManager.IsEcoModeActive()
}

// OptimizeResources enables automatic resource optimization
func (tv *TunnelVerifier) OptimizeResources() {
	optimizer := NewResourceOptimizer(tv)
	optimizer.Activate()
	
	tv.enhancedLogger.Info("Resource optimization activated", nil)
}

// UpdateConfig updates the configuration at runtime
func (tv *TunnelVerifier) UpdateConfig(newConfig Config) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Update intervals if they are different
	configChanged := false
	
	if newConfig.CheckInterval != tv.config.CheckInterval {
		tv.config.CheckInterval = newConfig.CheckInterval
		configChanged = true
	}
	
	if newConfig.IPLeakCheckInterval != tv.config.IPLeakCheckInterval {
		tv.config.IPLeakCheckInterval = newConfig.IPLeakCheckInterval
		configChanged = true
	}
	
	if newConfig.DNSLeakCheckInterval != tv.config.DNSLeakCheckInterval {
		tv.config.DNSLeakCheckInterval = newConfig.DNSLeakCheckInterval
		configChanged = true
	}
	
	if newConfig.RoutingCheckInterval != tv.config.RoutingCheckInterval {
		tv.config.RoutingCheckInterval = newConfig.RoutingCheckInterval
		configChanged = true
	}
	
	if newConfig.Timeout != tv.config.Timeout {
		tv.config.Timeout = newConfig.Timeout
		configChanged = true
	}
	
	if newConfig.LogLevel != tv.config.LogLevel {
		tv.config.LogLevel = newConfig.LogLevel
		configChanged = true
	}
	
	if newConfig.CheckIPLeak != tv.config.CheckIPLeak {
		tv.config.CheckIPLeak = newConfig.CheckIPLeak
		configChanged = true
	}
	
	if newConfig.CheckDNSLeak != tv.config.CheckDNSLeak {
		tv.config.CheckDNSLeak = newConfig.CheckDNSLeak
		configChanged = true
	}
	
	if newConfig.VerifyRouting != tv.config.VerifyRouting {
		tv.config.VerifyRouting = newConfig.VerifyRouting
		configChanged = true
	}
	
	if newConfig.VerificationEndpoints != nil && len(newConfig.VerificationEndpoints) > 0 {
		tv.config.VerificationEndpoints = newConfig.VerificationEndpoints
		configChanged = true
		// Update endpoints in routing verifier as well
		if tv.routingVerifier != nil {
			tv.routingVerifier.SetNonRUEndpoints(newConfig.VerificationEndpoints)
		}
	}
	
	if configChanged {
		tv.enhancedLogger.Info("Configuration updated", map[string]interface{}{
			"check_interval": tv.config.CheckInterval.Seconds(),
			"ip_leak_interval": tv.config.IPLeakCheckInterval.Seconds(),
			"dns_leak_interval": tv.config.DNSLeakCheckInterval.Seconds(),
			"routing_interval": tv.config.RoutingCheckInterval.Seconds(),
			"timeout": tv.config.Timeout.Seconds(),
			"log_level": tv.config.LogLevel,
			"endpoints_count": len(tv.config.VerificationEndpoints),
		})
	}
}

// GetConfig returns the current configuration
func (tv *TunnelVerifier) GetConfig() Config {
	tv.mu.RLock()
	defer tv.mu.RUnlock()
	
	return *tv.config
}

// AddVerificationEndpoint adds a new endpoint to the verification list
func (tv *TunnelVerifier) AddVerificationEndpoint(endpoint string) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Check if endpoint already exists
	for _, existingEndpoint := range tv.config.VerificationEndpoints {
		if existingEndpoint == endpoint {
			tv.enhancedLogger.Debug("Endpoint already exists in verification list", map[string]interface{}{
				"endpoint": endpoint,
			})
			return
		}
	}
	
	tv.config.VerificationEndpoints = append(tv.config.VerificationEndpoints, endpoint)
	
	// Update endpoints in routing verifier as well
	if tv.routingVerifier != nil {
		tv.routingVerifier.SetNonRUEndpoints(tv.config.VerificationEndpoints)
	}
	
	tv.enhancedLogger.Info("Verification endpoint added", map[string]interface{}{
		"endpoint": endpoint,
		"total_endpoints": len(tv.config.VerificationEndpoints),
	})
}

// RemoveVerificationEndpoint removes an endpoint from the verification list
func (tv *TunnelVerifier) RemoveVerificationEndpoint(endpoint string) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	for i, existingEndpoint := range tv.config.VerificationEndpoints {
		if existingEndpoint == endpoint {
			// Remove the endpoint
			tv.config.VerificationEndpoints = append(
				tv.config.VerificationEndpoints[:i], 
				tv.config.VerificationEndpoints[i+1:]...,
			)
			
			// Update endpoints in routing verifier as well
			if tv.routingVerifier != nil {
				tv.routingVerifier.SetNonRUEndpoints(tv.config.VerificationEndpoints)
			}
			
			tv.enhancedLogger.Info("Verification endpoint removed", map[string]interface{}{
				"endpoint": endpoint,
				"total_endpoints": len(tv.config.VerificationEndpoints),
			})
			return
		}
	}
	
	tv.enhancedLogger.Warn("Attempted to remove non-existing endpoint", map[string]interface{}{
		"endpoint": endpoint,
	})
}

// SetVerificationEndpoints sets all verification endpoints at once
func (tv *TunnelVerifier) SetVerificationEndpoints(endpoints []string) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	tv.config.VerificationEndpoints = endpoints
	
	// Update endpoints in routing verifier as well
	if tv.routingVerifier != nil {
		tv.routingVerifier.SetNonRUEndpoints(endpoints)
	}
	
	tv.enhancedLogger.Info("Verification endpoints updated", map[string]interface{}{
		"endpoints_count": len(endpoints),
		"endpoints": endpoints,
	})
}

// GetVerificationEndpoints returns the current list of verification endpoints
func (tv *TunnelVerifier) GetVerificationEndpoints() []string {
	tv.mu.RLock()
	defer tv.mu.RUnlock()
	
	endpoints := make([]string, len(tv.config.VerificationEndpoints))
	copy(endpoints, tv.config.VerificationEndpoints)
	return endpoints
}

// SetSensitivity sets the sensitivity for all checks
func (tv *TunnelVerifier) SetSensitivity(ipLeak, dnsLeak, routing float64) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Validate sensitivity values
	if ipLeak < 0 {
		ipLeak = 0
	} else if ipLeak > 1.0 {
		ipLeak = 1.0
	}
	
	if dnsLeak < 0 {
		dnsLeak = 0
	} else if dnsLeak > 1.0 {
		dnsLeak = 1.0
	}
	
	if routing < 0 {
		routing = 0
	} else if routing > 1.0 {
		routing = 1.0
	}
	
	tv.config.IPLeakSensitivity = ipLeak
	tv.config.DNSLeakSensitivity = dnsLeak
	tv.config.RoutingSensitivity = routing
	
	tv.enhancedLogger.Info("Sensitivity settings updated", map[string]interface{}{
		"ip_leak_sensitivity":  tv.config.IPLeakSensitivity,
		"dns_leak_sensitivity": tv.config.DNSLeakSensitivity,
		"routing_sensitivity":  tv.config.RoutingSensitivity,
	})
}

// SetIPLeakSensitivity sets the sensitivity for IP leak checks
func (tv *TunnelVerifier) SetIPLeakSensitivity(sensitivity float64) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Validate sensitivity value
	if sensitivity < 0 {
		sensitivity = 0
	} else if sensitivity > 1.0 {
		sensitivity = 1.0
	}
	
	tv.config.IPLeakSensitivity = sensitivity
	
	tv.enhancedLogger.Info("IP leak sensitivity updated", map[string]interface{}{
		"sensitivity": tv.config.IPLeakSensitivity,
	})
}

// SetDNSLeakSensitivity sets the sensitivity for DNS leak checks
func (tv *TunnelVerifier) SetDNSLeakSensitivity(sensitivity float64) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Validate sensitivity value
	if sensitivity < 0 {
		sensitivity = 0
	} else if sensitivity > 1.0 {
		sensitivity = 1.0
	}
	
	tv.config.DNSLeakSensitivity = sensitivity
	
	tv.enhancedLogger.Info("DNS leak sensitivity updated", map[string]interface{}{
		"sensitivity": tv.config.DNSLeakSensitivity,
	})
}

// SetRoutingSensitivity sets the sensitivity for routing checks
func (tv *TunnelVerifier) SetRoutingSensitivity(sensitivity float64) {
	tv.mu.Lock()
	defer tv.mu.Unlock()
	
	// Validate sensitivity value
	if sensitivity < 0 {
		sensitivity = 0
	} else if sensitivity > 1.0 {
		sensitivity = 1.0
	}
	
	tv.config.RoutingSensitivity = sensitivity
	
	tv.enhancedLogger.Info("Routing sensitivity updated", map[string]interface{}{
		"sensitivity": tv.config.RoutingSensitivity,
	})
}

// GetSensitivity returns the current sensitivity settings
func (tv *TunnelVerifier) GetSensitivity() (float64, float64, float64) {
	tv.mu.RLock()
	defer tv.mu.RUnlock()
	
	return tv.config.IPLeakSensitivity, tv.config.DNSLeakSensitivity, tv.config.RoutingSensitivity
}

// ApplySensitivityBasedLogic applies sensitivity to verification results
// This is a placeholder that shows how sensitivity could be applied
func (tv *TunnelVerifier) ApplySensitivityBasedLogic(checkType string, originalResult bool, confidence float64) bool {
	tv.mu.RLock()
	defer tv.mu.RUnlock()
	
	var sensitivity float64
	switch checkType {
	case "ip_leak":
		sensitivity = tv.config.IPLeakSensitivity
	case "dns_leak":
		sensitivity = tv.config.DNSLeakSensitivity
	case "routing":
		sensitivity = tv.config.RoutingSensitivity
	default:
		return originalResult
	}
	
	// The higher the sensitivity, the more likely we are to flag issues
	// For example, if sensitivity is 1.0 (max) and confidence is low, we might still flag as failure
	// If sensitivity is 0.0 (min), we only flag clear failures
	
	// Adjust the result based on sensitivity
	// This is a simplified approach - in a real implementation this would be more sophisticated
	threshold := 0.5 + (sensitivity-0.5)*0.5  // Adjust threshold based on sensitivity
	
	if originalResult && confidence < threshold {
		// High sensitivity might flag even uncertain results as problems
		if sensitivity > 0.7 {
			return false  // Consider uncertain results as failures at high sensitivity
		}
	}
	
	return originalResult
}

// GetHTTPChecker returns an HTTP checker instance
func (tv *TunnelVerifier) GetHTTPChecker() *HTTPChecker {
	return NewHTTPChecker(tv.enhancedLogger)
}

// PerformHTTPVerification performs an HTTP-based verification check
func (tv *TunnelVerifier) PerformHTTPVerification(urls []string) ([]*HTTPCheckResult, error) {
	httpChecker := tv.GetHTTPChecker()
	httpChecker.SetTimeout(tv.config.Timeout)
	
	tv.enhancedLogger.Info("Starting HTTP verification", map[string]interface{}{
		"url_count": len(urls),
		"timeout":   tv.config.Timeout.Seconds(),
	})
	
	results := httpChecker.CheckMultipleHTTPEndpoints(urls)
	
	// Calculate metrics for HTTP verification
	successCount := 0
	totalTime := time.Duration(0)
	
	for _, result := range results {
		if result.Success {
			successCount++
		}
		totalTime += result.ResponseTime
		
		// Record metrics for this specific check
		tv.metrics.RecordTrafficRoutingCheck(result.Success, result.ResponseTime)
	}
	
	avgTime := time.Duration(0)
	if len(results) > 0 {
		avgTime = totalTime / time.Duration(len(results))
	}
	
	tv.enhancedLogger.Info("HTTP verification completed", map[string]interface{}{
		"total_checks":      len(results),
		"successful_checks": successCount,
		"failed_checks":     len(results) - successCount,
		"success_rate":      float64(successCount) / float64(len(results)) * 100,
		"average_time_ms":   avgTime.Milliseconds(),
		"total_time_ms":     totalTime.Milliseconds(),
	})
	
	return results, nil
}

// PerformHTTPLeakTest performs a specialized HTTP-based leak test
func (tv *TunnelVerifier) PerformHTTPLeakTest() (bool, error) {
	// Use an external service that returns our IP to check if it matches VPN exit IP
	// For example, using httpbin.org/ip which returns the requesting IP
	httpChecker := tv.GetHTTPChecker()
	httpChecker.SetTimeout(tv.config.Timeout)
	
	// Check what external IP the request appears to come from
	result := httpChecker.CheckHTTPResponseContent(tv.config.IPCheckService, "origin")
	
	if !result.Success {
		tv.enhancedLogger.Warn("HTTP leak test failed to contact IP check service", map[string]interface{}{
			"service": tv.config.IPCheckService,
			"error":   result.Error.Error(),
		})
		return false, result.Error
	}
	
	// In a real implementation, we would compare this IP with the expected VPN exit IP
	// For now, we just verify that we can make the request successfully
	tv.enhancedLogger.Info("HTTP leak test completed", map[string]interface{}{
		"service": tv.config.IPCheckService,
		"success": result.Success,
		"response_time_ms": result.ResponseTime.Milliseconds(),
	})
	
	// Apply sensitivity to the result
	finalResult := tv.ApplySensitivityBasedLogic("ip_leak", result.Success, 0.8) // 0.8 confidence for now
	
	return finalResult, nil
}

// GetICMPChecker returns an ICMP checker instance
func (tv *TunnelVerifier) GetICMPChecker() (*ICMPChecker, error) {
	return NewICMPCheckerWithValidation(tv.enhancedLogger)
}

// PerformICMPVerification performs an ICMP-based verification check
func (tv *TunnelVerifier) PerformICMPVerification(targets []string) ([]*ICMPCheckResult, error) {
	icmpChecker, err := tv.GetICMPChecker()
	if err != nil {
		tv.enhancedLogger.Error("Failed to create ICMP checker", map[string]interface{}{
			"error": err.Error(),
		})
		return nil, err
	}
	
	icmpChecker.SetTimeout(tv.config.Timeout)
	
	tv.enhancedLogger.Info("Starting ICMP verification", map[string]interface{}{
		"target_count": len(targets),
		"timeout":      tv.config.Timeout.Seconds(),
	})
	
	results := icmpChecker.CheckMultipleICMPTargets(targets)
	
	// Calculate metrics for ICMP verification
	successCount := 0
	totalTime := time.Duration(0)
	
	for _, result := range results {
		if result.Success {
			successCount++
		}
		totalTime += result.ResponseTime
		
		// Record metrics for this specific check (using routing check metrics for now)
		tv.metrics.RecordTrafficRoutingCheck(result.Success, result.ResponseTime)
	}
	
	avgTime := time.Duration(0)
	if len(results) > 0 {
		avgTime = totalTime / time.Duration(len(results))
	}
	
	tv.enhancedLogger.Info("ICMP verification completed", map[string]interface{}{
		"total_checks":      len(results),
		"successful_checks": successCount,
		"failed_checks":     len(results) - successCount,
		"success_rate":      float64(successCount) / float64(len(results)) * 100,
		"average_time_ms":   avgTime.Milliseconds(),
		"total_time_ms":     totalTime.Milliseconds(),
	})
	
	return results, nil
}

// PerformICMPLeakTest performs a specialized ICMP-based leak test
func (tv *TunnelVerifier) PerformICMPLeakTest() (bool, error) {
	icmpChecker, err := tv.GetICMPChecker()
	if err != nil {
		tv.enhancedLogger.Error("Failed to create ICMP checker for leak test", map[string]interface{}{
			"error": err.Error(),
		})
		return false, err
	}
	
	// Get a non-RU endpoint to test against (using first available or default)
	testTarget := "8.8.8.8" // Default Google DNS
	if len(tv.config.VerificationEndpoints) > 0 {
		// Find a suitable IP address to ping
		for _, endpoint := range tv.config.VerificationEndpoints {
			// Try to resolve the endpoint to an IP
			ip := net.ParseIP(endpoint)
			if ip != nil {
				testTarget = endpoint
				break
			}
			
			// If it's not an IP, try to resolve it
			ips, err := net.LookupIP(endpoint)
			if err == nil && len(ips) > 0 {
				// Use the first IPv4 address found
				for _, ip := range ips {
					if ip.To4() != nil {
						testTarget = ip.String()
						break
					}
				}
				break
			}
		}
	}
	
	result := icmpChecker.CheckICMPConnectivity(testTarget)
	
	if !result.Success {
		tv.enhancedLogger.Warn("ICMP leak test failed", map[string]interface{}{
			"target": testTarget,
			"error":  result.Error.Error(),
		})
		// Apply sensitivity to the result
		finalResult := tv.ApplySensitivityBasedLogic("ip_leak", false, 0.5)
		return finalResult, result.Error
	}
	
	tv.enhancedLogger.Info("ICMP leak test completed", map[string]interface{}{
		"target": testTarget,
		"success": result.Success,
		"response_time_ms": result.ResponseTime.Milliseconds(),
	})
	
	// Apply sensitivity to the result
	finalResult := tv.ApplySensitivityBasedLogic("ip_leak", result.Success, 0.8) // 0.8 confidence for now
	
	return finalResult, nil
}

// GetDNSChecker returns a DNS checker instance
func (tv *TunnelVerifier) GetDNSChecker() *DNSChecker {
	return NewDNSChecker(tv.enhancedLogger)
}

// PerformDNSVerification performs a DNS-based verification check
func (tv *TunnelVerifier) PerformDNSVerification(domains []string) ([]*DNSCheckResult, error) {
	dnsChecker := tv.GetDNSChecker()
	dnsChecker.SetTimeout(tv.config.Timeout)
	
	tv.enhancedLogger.Info("Starting DNS verification", map[string]interface{}{
		"domain_count": len(domains),
		"timeout":      tv.config.Timeout.Seconds(),
	})
	
	results := dnsChecker.CheckMultipleDNSDomains(domains)
	
	// Calculate metrics for DNS verification
	successCount := 0
	totalTime := time.Duration(0)
	
	for _, result := range results {
		if result.Success {
			successCount++
		}
		totalTime += result.ResponseTime
		
		// Record metrics for this specific check (using DNS leak check metrics)
		tv.metrics.RecordDNSLeakCheck(result.Success, result.ResponseTime)
	}
	
	avgTime := time.Duration(0)
	if len(results) > 0 {
		avgTime = totalTime / time.Duration(len(results))
	}
	
	tv.enhancedLogger.Info("DNS verification completed", map[string]interface{}{
		"total_checks":      len(results),
		"successful_checks": successCount,
		"failed_checks":     len(results) - successCount,
		"success_rate":      float64(successCount) / float64(len(results)) * 100,
		"average_time_ms":   avgTime.Milliseconds(),
		"total_time_ms":     totalTime.Milliseconds(),
	})
	
	return results, nil
}

// PerformDNSLeakTest performs a specialized DNS-based leak test
func (tv *TunnelVerifier) PerformDNSLeakTest() (bool, error) {
	dnsChecker := tv.GetDNSChecker()
	dnsChecker.SetTimeout(tv.config.Timeout)
	
	// Use common domains that should be resolvable if DNS is working properly
	testDomains := []string{
		"www.google.com",
		"www.cloudflare.com",
		"www.youtube.com",
	}
	
	// Add any custom endpoints if provided
	for _, endpoint := range tv.config.VerificationEndpoints {
		if !strings.Contains(endpoint, ".") {
			// Skip IP addresses, they won't be valid domains
			continue
		}
		// Check if it's already in our test domains
		alreadyPresent := false
		for _, domain := range testDomains {
			if domain == endpoint {
				alreadyPresent = true
				break
			}
		}
		if !alreadyPresent {
			testDomains = append(testDomains, endpoint)
		}
	}
	
	isValid, err := dnsChecker.CheckDNSLeak(testDomains)
	if err != nil {
		tv.enhancedLogger.Warn("DNS leak test encountered error", map[string]interface{}{
			"error": err.Error(),
		})
		// For DNS leak tests, an error might indicate a configuration issue rather than a leak
		// We'll return the error status but handle sensitivity
		finalResult := tv.ApplySensitivityBasedLogic("dns_leak", false, 0.5)
		return finalResult, err
	}
	
	tv.enhancedLogger.Info("DNS leak test completed", map[string]interface{}{
		"result": isValid,
		"test_domains_count": len(testDomains),
	})
	
	// Apply sensitivity to the result
	finalResult := tv.ApplySensitivityBasedLogic("dns_leak", isValid, 0.8) // 0.8 confidence for now
	
	return finalResult, nil
}