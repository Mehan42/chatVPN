// Package tunnelverifier provides performance analysis tools
package tunnelverifier

import (
	"context"
	"fmt"
	"runtime"
	"time"
)

// PerformanceAnalyzer analyzes the performance impact of the tunnel verifier
type PerformanceAnalyzer struct {
	verifier *TunnelVerifier
}

// NewPerformanceAnalyzer creates a new performance analyzer
func NewPerformanceAnalyzer(tv *TunnelVerifier) *PerformanceAnalyzer {
	return &PerformanceAnalyzer{
		verifier: tv,
	}
}

// AnalyzePerformance performs a comprehensive performance analysis
func (pa *PerformanceAnalyzer) AnalyzePerformance(duration time.Duration) (map[string]interface{}, error) {
	pa.verifier.enhancedLogger.Info("Starting performance analysis", map[string]interface{}{
		"duration": duration.Seconds(),
	})

	startTime := time.Now()

	// Capture initial state
	initialMetrics := pa.verifier.GetMetrics()
	initialMemStats := &runtime.MemStats{}
	runtime.GC() // Run garbage collection before measuring
	runtime.ReadMemStats(initialMemStats)

	initialGoroutines := runtime.NumGoroutine()

	pa.verifier.enhancedLogger.Info("Initial system state", map[string]interface{}{
		"goroutines":  initialGoroutines,
		"alloc_bytes": initialMemStats.Alloc,
		"sys_bytes":   initialMemStats.Sys,
	})

	// Run the tunnel verifier for the specified duration
	ctx, cancel := context.WithTimeout(context.Background(), duration)
	defer cancel()

	// Run analysis in a separate goroutine to monitor continuously
	done := make(chan bool)
	go func() {
		<-ctx.Done()
		close(done)
	}()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	verificationCount := 0

	// Continuously call IsTunnelingValid to simulate real usage
	for {
		select {
		case <-done:
			pa.verifier.enhancedLogger.Info("Performance analysis completed", nil)
			goto finalize
		case <-ticker.C:
			// Call the main verification function to measure its performance
			_, err := pa.verifier.IsTunnelingValid()
			if err != nil {
				pa.verifier.enhancedLogger.Warn("Verification error during performance test", map[string]interface{}{
					"error": err.Error(),
				})
			}
			verificationCount++
		}
	}

finalize:
	// Capture final state
	finalMetrics := pa.verifier.GetMetrics()
	finalMemStats := &runtime.MemStats{}
	runtime.GC() // Run garbage collection before final measurement
	runtime.ReadMemStats(finalMemStats)

	finalGoroutines := runtime.NumGoroutine()
	totalDuration := time.Since(startTime)

	// Calculate performance metrics
	allocDelta := int64(finalMemStats.Alloc) - int64(initialMemStats.Alloc)
	sysDelta := int64(finalMemStats.Sys) - int64(initialMemStats.Sys)

	// Calculate verification metrics
	totalVerifications := finalMetrics.TotalVerifications - initialMetrics.TotalVerifications
	successfulVerifications := finalMetrics.SuccessfulVerifications - initialMetrics.SuccessfulVerifications
	failedVerifications := finalMetrics.FailedVerifications - initialMetrics.FailedVerifications

	var successRate float64
	if totalVerifications > 0 {
		successRate = float64(successfulVerifications) / float64(totalVerifications) * 100
	}

	// Calculate rate metrics
	verificationsPerSecond := float64(totalVerifications) / totalDuration.Seconds()

	analysisResults := map[string]interface{}{
		"duration_seconds":         totalDuration.Seconds(),
		"total_verifications":      totalVerifications,
		"successful_verifications": successfulVerifications,
		"failed_verifications":     failedVerifications,
		"success_rate_percentage":  successRate,
		"verifications_per_second": verificationsPerSecond,
		"initial_goroutines":       initialGoroutines,
		"final_goroutines":         finalGoroutines,
		"goroutine_delta":          finalGoroutines - initialGoroutines,
		"initial_memory_alloc":     initialMemStats.Alloc,
		"final_memory_alloc":       finalMemStats.Alloc,
		"memory_alloc_delta":       allocDelta,
		"initial_memory_sys":       initialMemStats.Sys,
		"final_memory_sys":         finalMemStats.Sys,
		"memory_sys_delta":         sysDelta,
		"gc_cycles":                finalMemStats.NumGC - initialMemStats.NumGC,
		"avg_verification_time":    finalMetrics.AvgVerificationTime.Seconds(),
		"max_verification_time":    finalMetrics.MaxVerificationTime.Seconds(),
		"min_verification_time":    finalMetrics.MinVerificationTime.Seconds(),
	}

	pa.verifier.enhancedLogger.Info("Performance analysis results", analysisResults)

	return analysisResults, nil
}

// GetSystemResourceUsage returns current system resource usage
func (pa *PerformanceAnalyzer) GetSystemResourceUsage() map[string]interface{} {
	var m runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&m)

	return map[string]interface{}{
		"goroutines":         runtime.NumGoroutine(),
		"memory_alloc":       m.Alloc,
		"memory_total_alloc": m.TotalAlloc,
		"memory_sys":         m.Sys,
		"memory_heap_alloc":  m.HeapAlloc,
		"memory_heap_sys":    m.HeapSys,
		"memory_heap_idle":   m.HeapIdle,
		"memory_heap_inuse":  m.HeapInuse,
		"gc_cycles":          m.NumGC,
		"gc_pause_total":     m.PauseTotalNs,
		"last_gc":            time.Unix(0, int64(m.LastGC)).Format(time.RFC3339),
	}
}

// GeneratePerformanceReport generates a human-readable performance report
func (pa *PerformanceAnalyzer) GeneratePerformanceReport(results map[string]interface{}) string {
	report := "=== Performance Analysis Report ===\n\n"

	report += fmt.Sprintf("Test Duration: %.2f seconds\n", results["duration_seconds"])
	report += fmt.Sprintf("Total Verifications: %d\n", results["total_verifications"])
	report += fmt.Sprintf("Successful Verifications: %d\n", results["successful_verifications"])
	report += fmt.Sprintf("Failed Verifications: %d\n", results["failed_verifications"])
	report += fmt.Sprintf("Success Rate: %.2f%%\n", results["success_rate_percentage"])
	report += fmt.Sprintf("Verifications per Second: %.2f\n\n", results["verifications_per_second"])

	report += fmt.Sprintf("Goroutine Delta: %d (%d → %d)\n",
		results["goroutine_delta"], results["initial_goroutines"], results["final_goroutines"])

	report += fmt.Sprintf("Memory Allocation Delta: %s (%s → %s)\n",
		formatBytes(results["memory_alloc_delta"].(int64)),
		formatBytes(int64(results["initial_memory_alloc"].(uint64))),
		formatBytes(int64(results["final_memory_alloc"].(uint64))))

	report += fmt.Sprintf("System Memory Delta: %s (%s → %s)\n\n",
		formatBytes(results["memory_sys_delta"].(int64)),
		formatBytes(int64(results["initial_memory_sys"].(uint64))),
		formatBytes(int64(results["final_memory_sys"].(uint64))))

	report += fmt.Sprintf("Average Verification Time: %.4f seconds\n", results["avg_verification_time"])
	report += fmt.Sprintf("Max Verification Time: %.4f seconds\n", results["max_verification_time"])
	report += fmt.Sprintf("Min Verification Time: %.4f seconds\n", results["min_verification_time"])

	report += fmt.Sprintf("GC Cycles During Test: %d\n", results["gc_cycles"])

	return report
}

// formatBytes formats a byte count into a human-readable string
func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// CheckPerformanceThresholds checks if performance is within acceptable thresholds
func (pa *PerformanceAnalyzer) CheckPerformanceThresholds(results map[string]interface{}) map[string]bool {
	thresholds := map[string]bool{
		"low_goroutine_increase":       (results["goroutine_delta"].(int)) < 10,                          // Less than 10 new goroutines
		"low_memory_increase":          results["memory_alloc_delta"].(int64) < 10*1024*1024,             // Less than 10MB increase
		"acceptable_success_rate":      results["success_rate_percentage"].(float64) >= 95.0,             // At least 95% success
		"reasonable_verification_time": results["avg_verification_time"].(time.Duration).Seconds() < 5.0, // Under 5 seconds avg
	}

	pa.verifier.enhancedLogger.Info("Performance threshold check", map[string]interface{}{
		"thresholds": thresholds,
	})

	return thresholds
}
