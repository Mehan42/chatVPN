// Package tunnelverifier provides load testing functionality
package tunnelverifier

import (
	"context"
	"sync"
	"time"
	"fmt"
)

// LoadTestConfig holds configuration for load testing
type LoadTestConfig struct {
	ConcurrentVerifications int           // Number of concurrent verification processes
	TestDuration          time.Duration // Duration of the load test
	Interval             time.Duration // Interval between verifications
	MemoryCheckInterval  time.Duration // How often to check memory usage
}

// LoadTester performs load testing on the tunnel verifier
type LoadTester struct {
	config       *LoadTestConfig
	tunnelVerifier *TunnelVerifier
	results      *LoadTestResults
	stopChan     chan struct{}
	wg          sync.WaitGroup
}

// LoadTestResults holds the results of a load test
type LoadTestResults struct {
	TotalVerifications  int
	SuccessfulVerifications int
	FailedVerifications    int
	TotalDuration     time.Duration
	AvgVerificationTime time.Duration
	MaxVerificationTime time.Duration
	MinVerificationTime time.Duration
	Errors            []error
	MemoryUsage       []MemorySnapshot
}

// MemorySnapshot holds a memory usage snapshot
type MemorySnapshot struct {
	Timestamp time.Time
	Usage     int64 // in bytes
}

// NewLoadTester creates a new load tester
func NewLoadTester(tv *TunnelVerifier, config *LoadTestConfig) *LoadTester {
	if config.ConcurrentVerifications <= 0 {
		config.ConcurrentVerifications = 5 // default
	}
	if config.TestDuration <= 0 {
		config.TestDuration = 30 * time.Second // default
	}
	if config.Interval <= 0 {
		config.Interval = 1 * time.Second // default
	}
	if config.MemoryCheckInterval <= 0 {
		config.MemoryCheckInterval = 5 * time.Second // default
	}
	
	return &LoadTester{
		config:         config,
		tunnelVerifier: tv,
		results: &LoadTestResults{
			Errors:      make([]error, 0),
			MemoryUsage: make([]MemorySnapshot, 0),
		},
		stopChan: make(chan struct{}),
	}
}

// Run performs the load test
func (lt *LoadTester) Run(ctx context.Context) (*LoadTestResults, error) {
	lt.tunnelVerifier.enhancedLogger.Info("Starting load test", map[string]interface{}{
		"concurrent_verifications": lt.config.ConcurrentVerifications,
		"test_duration":            lt.config.TestDuration.Seconds(),
		"interval":                 lt.config.Interval.Seconds(),
	})
	
	startTime := time.Now()
	
	// Start monitoring goroutine
	lt.wg.Add(1)
	go lt.memoryMonitor()
	
	// Start verification goroutines
	for i := 0; i < lt.config.ConcurrentVerifications; i++ {
		lt.wg.Add(1)
		go lt.runVerificationWorker(ctx, i)
	}
	
	// Wait for test duration
	select {
	case <-time.After(lt.config.TestDuration):
	case <-ctx.Done():
	}
	
	// Stop monitoring
	close(lt.stopChan)
	lt.wg.Wait()
	
	lt.results.TotalDuration = time.Since(startTime)
	
	// Calculate average verification time if any verifications ran
	if lt.results.TotalVerifications > 0 {
		lt.results.AvgVerificationTime = time.Duration(
			lt.results.AvgVerificationTime.Nanoseconds() / int64(lt.results.TotalVerifications),
		)
	}
	
	lt.tunnelVerifier.enhancedLogger.Info("Load test completed", map[string]interface{}{
		"total_verifications":       lt.results.TotalVerifications,
		"successful_verifications":  lt.results.SuccessfulVerifications,
		"failed_verifications":      lt.results.FailedVerifications,
		"total_duration":            lt.results.TotalDuration.Seconds(),
		"avg_verification_time":     lt.results.AvgVerificationTime.Seconds(),
		"max_verification_time":     lt.results.MaxVerificationTime.Seconds(),
		"min_verification_time":     lt.results.MinVerificationTime.Seconds(),
		"error_count":              len(lt.results.Errors),
		"memory_snapshots_count":   len(lt.results.MemoryUsage),
	})
	
	return lt.results, nil
}

// runVerificationWorker runs a worker that continuously performs verifications
func (lt *LoadTester) runVerificationWorker(ctx context.Context, workerID int) {
	defer lt.wg.Done()
	
	ticker := time.NewTicker(lt.config.Interval)
	defer ticker.Stop()
	
	lt.tunnelVerifier.enhancedLogger.Debug("Load test worker started", map[string]interface{}{
		"worker_id": workerID,
	})
	
	for {
		select {
		case <-ticker.C:
			// Perform a verification
			startTime := time.Now()
			
			_, err := lt.tunnelVerifier.IsTunnelingValid()
			
			verificationTime := time.Since(startTime)
			
			// Update results
			lt.results.TotalVerifications++
			
			if err != nil {
				lt.results.FailedVerifications++
				lt.results.Errors = append(lt.results.Errors, err)
				lt.tunnelVerifier.enhancedLogger.Debug("Verification failed in load test", map[string]interface{}{
					"worker_id": workerID,
					"error":     err.Error(),
				})
			} else {
				lt.results.SuccessfulVerifications++
			}
			
			// Update timing metrics
			lt.results.AvgVerificationTime += verificationTime
			if verificationTime > lt.results.MaxVerificationTime {
				lt.results.MaxVerificationTime = verificationTime
			}
			if verificationTime < lt.results.MinVerificationTime || lt.results.MinVerificationTime == 0 {
				lt.results.MinVerificationTime = verificationTime
			}
			
		case <-lt.stopChan:
			lt.tunnelVerifier.enhancedLogger.Debug("Load test worker stopping", map[string]interface{}{
				"worker_id": workerID,
			})
			return
		case <-ctx.Done():
			lt.tunnelVerifier.enhancedLogger.Debug("Load test worker context cancelled", map[string]interface{}{
				"worker_id": workerID,
			})
			return
		}
	}
}

// memoryMonitor periodically checks memory usage
func (lt *LoadTester) memoryMonitor() {
	defer lt.wg.Done()
	
	ticker := time.NewTicker(lt.config.MemoryCheckInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			// In a real implementation, we would check actual memory usage
			// For now, we'll just add a timestamp to track when we checked
			snapshot := MemorySnapshot{
				Timestamp: time.Now(),
				// In a real implementation: Usage: getActualMemoryUsage(),
				Usage: 0, // Placeholder
			}
			lt.results.MemoryUsage = append(lt.results.MemoryUsage, snapshot)
		case <-lt.stopChan:
			return
		}
	}
}

// RunStressTest performs a stress test with increasing load
func (lt *LoadTester) RunStressTest(ctx context.Context, startWorkers, maxWorkers int, stepDuration time.Duration) (*LoadTestResults, error) {
	lt.tunnelVerifier.enhancedLogger.Info("Starting stress test", map[string]interface{}{
		"start_workers": startWorkers,
		"max_workers":   maxWorkers,
		"step_duration": stepDuration.Seconds(),
	})
	
	var finalResults *LoadTestResults
	var finalErr error
	
	currentWorkers := startWorkers
	
	for currentWorkers <= maxWorkers {
		// Update config for current stress level
		testConfig := *lt.config
		testConfig.ConcurrentVerifications = currentWorkers
		testConfig.TestDuration = stepDuration
		
		tempTester := NewLoadTester(lt.tunnelVerifier, &testConfig)
		
		lt.tunnelVerifier.enhancedLogger.Info("Running stress test step", map[string]interface{}{
			"workers": currentWorkers,
		})
		
		results, err := tempTester.Run(ctx)
		if err != nil {
			lt.tunnelVerifier.enhancedLogger.Error("Stress test step failed", map[string]interface{}{
				"workers": currentWorkers,
				"error":   err.Error(),
			})
			finalErr = err
			break
		}
		
		// Log results for this step
		lt.tunnelVerifier.enhancedLogger.Info("Stress test step completed", map[string]interface{}{
			"workers":                  currentWorkers,
			"successful_verifications": results.SuccessfulVerifications,
			"failed_verifications":     results.FailedVerifications,
		})
		
		finalResults = results
		
		// Check if we should continue increasing load
		failureRate := float64(results.FailedVerifications) / float64(results.TotalVerifications)
		if failureRate > 0.1 { // If more than 10% failures, stop increasing load
			lt.tunnelVerifier.enhancedLogger.Warn("High failure rate detected, stopping stress test", map[string]interface{}{
				"workers":     currentWorkers,
				"failure_rate": fmt.Sprintf("%.2f%%", failureRate*100),
			})
			break
		}
		
		currentWorkers += (maxWorkers - startWorkers) / 5 // Increase by 20% each step
		if currentWorkers > maxWorkers {
			currentWorkers = maxWorkers
		}
	}
	
	lt.tunnelVerifier.enhancedLogger.Info("Stress test completed", map[string]interface{}{
		"final_worker_count": currentWorkers,
	})
	
	return finalResults, finalErr
}

// GetLoadTestConfig returns a default configuration for load testing
func GetLoadTestConfig() *LoadTestConfig {
	return &LoadTestConfig{
		ConcurrentVerifications: 10,
		TestDuration:          60 * time.Second,
		Interval:             500 * time.Millisecond,
		MemoryCheckInterval:  5 * time.Second,
	}
}

// GetStressTestConfig returns a default configuration for stress testing
func GetStressTestConfig() *LoadTestConfig {
	return &LoadTestConfig{
		ConcurrentVerifications: 5, // Starting point
		TestDuration:          30 * time.Second,
		Interval:             100 * time.Millisecond,
		MemoryCheckInterval:  2 * time.Second,
	}
}