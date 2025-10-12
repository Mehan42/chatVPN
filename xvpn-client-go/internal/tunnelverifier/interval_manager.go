// Package tunnelverifier provides configurable verification intervals
package tunnelverifier

import (
	"context"
	"sync"
	"time"
)

// IntervalManager manages different check intervals
type IntervalManager struct {
	mu                 sync.RWMutex
	ipLeakTicker       *time.Ticker
	dnsLeakTicker      *time.Ticker
	routingTicker      *time.Ticker
	ipLeakDone         chan bool
	dnsLeakDone        chan bool
	routingDone        chan bool
	verifier           *TunnelVerifier
	ctx                context.Context
	cancel             context.CancelFunc
}

// NewIntervalManager creates a new interval manager
func NewIntervalManager(tv *TunnelVerifier) *IntervalManager {
	ctx, cancel := context.WithCancel(context.Background())
	
	return &IntervalManager{
		verifier: tv,
		ctx:      ctx,
		cancel:   cancel,
		ipLeakDone: make(chan bool, 1),
		dnsLeakDone: make(chan bool, 1),
		routingDone: make(chan bool, 1),
	}
}

// StartIntervalBasedVerification starts verification with individual intervals
func (im *IntervalManager) StartIntervalBasedVerification(ctx context.Context) {
	im.mu.Lock()
	defer im.mu.Unlock()
	
	// Start individual tickers based on configuration
	if im.verifier.config.CheckIPLeak {
		im.ipLeakTicker = time.NewTicker(im.verifier.config.IPLeakCheckInterval)
		go im.runIPLeakChecks(ctx)
	}
	
	if im.verifier.config.CheckDNSLeak {
		im.dnsLeakTicker = time.NewTicker(im.verifier.config.DNSLeakCheckInterval)
		go im.runDNSLeakChecks(ctx)
	}
	
	if im.verifier.config.VerifyRouting {
		im.routingTicker = time.NewTicker(im.verifier.config.RoutingCheckInterval)
		go im.runRoutingChecks(ctx)
	}
	
	im.verifier.enhancedLogger.Info("Interval-based verification started", map[string]interface{}{
		"ip_leak_interval": im.verifier.config.IPLeakCheckInterval.Seconds(),
		"dns_leak_interval": im.verifier.config.DNSLeakCheckInterval.Seconds(),
		"routing_interval": im.verifier.config.RoutingCheckInterval.Seconds(),
	})
}

// runIPLeakChecks runs IP leak checks at the configured interval
func (im *IntervalManager) runIPLeakChecks(ctx context.Context) {
	for {
		select {
		case <-im.ipLeakTicker.C:
			im.verifier.mu.RLock()
			if !im.verifier.running {
				im.verifier.mu.RUnlock()
				return
			}
			im.verifier.mu.RUnlock()
			
			startTime := time.Now()
			ipLeakStatus := im.verifier.checkIPLeak()
			
			// Record metrics for IP leak check
			im.verifier.metrics.RecordIPLeakCheck(ipLeakStatus, time.Since(startTime))
			
			// Update verification status
			im.verifier.statusMutex.Lock()
			im.verifier.verificationStatus["ip_leak_check"] = ipLeakStatus
			im.verifier.statusMutex.Unlock()
			
			statusStr := "passed"
			if !ipLeakStatus {
				statusStr = "failed"
			}
			
			im.verifier.enhancedLogger.Info("IP leak check completed", map[string]interface{}{
				"status":   statusStr,
				"duration": time.Since(startTime).Seconds(),
			})
		case <-ctx.Done():
			im.ipLeakTicker.Stop()
			return
		}
	}
}

// runDNSLeakChecks runs DNS leak checks at the configured interval
func (im *IntervalManager) runDNSLeakChecks(ctx context.Context) {
	for {
		select {
		case <-im.dnsLeakTicker.C:
			im.verifier.mu.RLock()
			if !im.verifier.running {
				im.verifier.mu.RUnlock()
				return
			}
			im.verifier.mu.RUnlock()
			
			startTime := time.Now()
			dnsLeakStatus := im.verifier.checkDNSLeak()
			
			// Record metrics for DNS leak check
			im.verifier.metrics.RecordDNSLeakCheck(dnsLeakStatus, time.Since(startTime))
			
			// Update verification status
			im.verifier.statusMutex.Lock()
			im.verifier.verificationStatus["dns_leak_check"] = dnsLeakStatus
			im.verifier.statusMutex.Unlock()
			
			statusStr := "passed"
			if !dnsLeakStatus {
				statusStr = "failed"
			}
			
			im.verifier.enhancedLogger.Info("DNS leak check completed", map[string]interface{}{
				"status":   statusStr,
				"duration": time.Since(startTime).Seconds(),
			})
		case <-ctx.Done():
			im.dnsLeakTicker.Stop()
			return
		}
	}
}

// runRoutingChecks runs routing checks at the configured interval
func (im *IntervalManager) runRoutingChecks(ctx context.Context) {
	for {
		select {
		case <-im.routingTicker.C:
			im.verifier.mu.RLock()
			if !im.verifier.running {
				im.verifier.mu.RUnlock()
				return
			}
			im.verifier.mu.RUnlock()
			
			startTime := time.Now()
			routingStatus := im.verifier.verifyTrafficRouting()
			
			// Record metrics for traffic routing check
			im.verifier.metrics.RecordTrafficRoutingCheck(routingStatus, time.Since(startTime))
			
			// Update verification status
			im.verifier.statusMutex.Lock()
			im.verifier.verificationStatus["traffic_routing_check"] = routingStatus
			im.verifier.statusMutex.Unlock()
			
			statusStr := "passed"
			if !routingStatus {
				statusStr = "failed"
			}
			
			im.verifier.enhancedLogger.Info("Traffic routing check completed", map[string]interface{}{
				"status":   statusStr,
				"duration": time.Since(startTime).Seconds(),
			})
		case <-ctx.Done():
			im.routingTicker.Stop()
			return
		}
	}
}

// Stop stops all interval-based verifications
func (im *IntervalManager) Stop() {
	im.mu.Lock()
	defer im.mu.Unlock()
	
	if im.ipLeakTicker != nil {
		im.ipLeakTicker.Stop()
	}
	if im.dnsLeakTicker != nil {
		im.dnsLeakTicker.Stop()
	}
	if im.routingTicker != nil {
		im.routingTicker.Stop()
	}
	
	im.cancel()
	
	im.verifier.enhancedLogger.Info("Interval-based verification stopped", nil)
}