// Package tunnelverifier provides HTTP-based verification functionality
package tunnelverifier

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// HTTPChecker performs HTTP-based verification checks
type HTTPChecker struct {
	client         *http.Client
	enhancedLogger *Logger
	timeout        time.Duration
	retryAttempts  int
}

// HTTPCheckResult represents the result of an HTTP check
type HTTPCheckResult struct {
	URL           string
	StatusCode    int
	ResponseTime  time.Duration
	Success       bool
	Error         error
	ResponseBody  string
	Headers       map[string]string
}

// NewHTTPChecker creates a new HTTP checker
func NewHTTPChecker(logger *Logger) *HTTPChecker {
	client := &http.Client{
		Timeout: 30 * time.Second, // Default timeout, will be overridden by config
	}
	
	return &HTTPChecker{
		client:         client,
		enhancedLogger: logger,
		timeout:        30 * time.Second,
		retryAttempts:  2,
	}
}

// SetTimeout sets the timeout for HTTP requests
func (hc *HTTPChecker) SetTimeout(timeout time.Duration) {
	hc.timeout = timeout
	hc.client.Timeout = timeout
}

// SetRetryAttempts sets the number of retry attempts for failed requests
func (hc *HTTPChecker) SetRetryAttempts(attempts int) {
	hc.retryAttempts = attempts
}

// CheckHTTPConnectivity checks if an HTTP endpoint is accessible
func (hc *HTTPChecker) CheckHTTPConnectivity(url string) *HTTPCheckResult {
	hc.enhancedLogger.Debug("Starting HTTP connectivity check", map[string]interface{}{
		"url": url,
	})
	
	startTime := time.Now()
	
	// Create a context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()
	
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		hc.enhancedLogger.Warn("Failed to create HTTP request", map[string]interface{}{
			"url":   url,
			"error": err.Error(),
		})
		return &HTTPCheckResult{
			URL:        url,
			Success:    false,
			Error:      err,
			ResponseTime: time.Since(startTime),
		}
	}
	
	var resp *http.Response
	var lastErr error
	
	// Retry logic
	for attempt := 0; attempt <= hc.retryAttempts; attempt++ {
		resp, lastErr = hc.client.Do(req)
		if lastErr == nil {
			break // Success
		}
		
		hc.enhancedLogger.Debug("HTTP request failed, retrying", map[string]interface{}{
			"url":     url,
			"attempt": attempt + 1,
			"error":   lastErr.Error(),
		})
		
		if attempt < hc.retryAttempts {
			// Wait before retrying
			time.Sleep(time.Duration(attempt+1) * time.Second)
		}
	}
	
	if lastErr != nil {
		hc.enhancedLogger.Warn("HTTP connectivity check failed after retries", map[string]interface{}{
			"url":   url,
			"error": lastErr.Error(),
			"attempts": hc.retryAttempts + 1,
		})
		return &HTTPCheckResult{
			URL:          url,
			Success:      false,
			Error:        lastErr,
			ResponseTime: time.Since(startTime),
		}
	}
	defer resp.Body.Close()
	
	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		hc.enhancedLogger.Warn("Failed to read HTTP response body", map[string]interface{}{
			"url":   url,
			"error": err.Error(),
		})
		return &HTTPCheckResult{
			URL:          url,
			StatusCode:   resp.StatusCode,
			Success:      false,
			Error:        err,
			ResponseTime: time.Since(startTime),
		}
	}
	
	// Collect headers
	headers := make(map[string]string)
	for name, values := range resp.Header {
		if len(values) > 0 {
			headers[name] = values[0] // Take first value
		}
	}
	
	isSuccess := resp.StatusCode >= 200 && resp.StatusCode < 400
	
	hc.enhancedLogger.Debug("HTTP connectivity check completed", map[string]interface{}{
		"url":         url,
		"status_code": resp.StatusCode,
		"success":     isSuccess,
		"response_time_ms": time.Since(startTime).Milliseconds(),
		"body_length": len(body),
	})
	
	return &HTTPCheckResult{
		URL:          url,
		StatusCode:   resp.StatusCode,
		ResponseTime: time.Since(startTime),
		Success:      isSuccess,
		ResponseBody: string(body),
		Headers:      headers,
	}
}

// CheckHTTPHeaders checks specific headers in HTTP response
func (hc *HTTPChecker) CheckHTTPHeaders(url string, requiredHeaders map[string]string) *HTTPCheckResult {
	result := hc.CheckHTTPConnectivity(url)
	if !result.Success {
		return result
	}
	
	// Check if required headers are present with correct values
	for headerName, expectedValue := range requiredHeaders {
		if actualValue, exists := result.Headers[headerName]; !exists {
			result.Success = false
			result.Error = fmt.Errorf("required header '%s' not found", headerName)
			hc.enhancedLogger.Debug("HTTP header check failed - header missing", map[string]interface{}{
				"url":        url,
				"header":     headerName,
				"expected":   expectedValue,
			})
			break
		} else if !strings.Contains(strings.ToLower(actualValue), strings.ToLower(expectedValue)) {
			result.Success = false
			result.Error = fmt.Errorf("header '%s' has value '%s', expected '%s'", headerName, actualValue, expectedValue)
			hc.enhancedLogger.Debug("HTTP header check failed - value mismatch", map[string]interface{}{
				"url":        url,
				"header":     headerName,
				"actual":     actualValue,
				"expected":   expectedValue,
			})
			break
		}
	}
	
	if result.Success {
		hc.enhancedLogger.Debug("HTTP header check passed", map[string]interface{}{
			"url": url,
		})
	}
	
	return result
}

// CheckHTTPResponseContent checks if response contains expected content
func (hc *HTTPChecker) CheckHTTPResponseContent(url string, expectedContent string) *HTTPCheckResult {
	result := hc.CheckHTTPConnectivity(url)
	if !result.Success {
		return result
	}
	
	if !strings.Contains(strings.ToLower(result.ResponseBody), strings.ToLower(expectedContent)) {
		result.Success = false
		result.Error = fmt.Errorf("response does not contain expected content '%s'", expectedContent)
		hc.enhancedLogger.Debug("HTTP content check failed", map[string]interface{}{
			"url":            url,
			"expected":       expectedContent,
			"response_start": result.ResponseBody[:min(100, len(result.ResponseBody))],
		})
	} else {
		hc.enhancedLogger.Debug("HTTP content check passed", map[string]interface{}{
			"url": url,
		})
	}
	
	return result
}

// CheckHTTPStatusCode checks if response has expected status code
func (hc *HTTPChecker) CheckHTTPStatusCode(url string, expectedCode int) *HTTPCheckResult {
	result := hc.CheckHTTPConnectivity(url)
	if !result.Success {
		return result
	}
	
	if result.StatusCode != expectedCode {
		result.Success = false
		result.Error = fmt.Errorf("status code is %d, expected %d", result.StatusCode, expectedCode)
		hc.enhancedLogger.Debug("HTTP status code check failed", map[string]interface{}{
			"url":      url,
			"actual":   result.StatusCode,
			"expected": expectedCode,
		})
	} else {
		hc.enhancedLogger.Debug("HTTP status code check passed", map[string]interface{}{
			"url": url,
		})
	}
	
	return result
}

// CheckMultipleHTTPEndpoints performs HTTP checks on multiple endpoints
func (hc *HTTPChecker) CheckMultipleHTTPEndpoints(urls []string) []*HTTPCheckResult {
	hc.enhancedLogger.Info("Starting multiple HTTP endpoint checks", map[string]interface{}{
		"endpoint_count": len(urls),
	})
	
	results := make([]*HTTPCheckResult, 0, len(urls))
	
	for i, url := range urls {
		hc.enhancedLogger.Debug("Checking HTTP endpoint", map[string]interface{}{
			"url":   url,
			"index": i,
		})
		
		result := hc.CheckHTTPConnectivity(url)
		results = append(results, result)
	}
	
	// Count successful checks
	successful := 0
	for _, result := range results {
		if result.Success {
			successful++
		}
	}
	
	hc.enhancedLogger.Info("Multiple HTTP endpoint checks completed", map[string]interface{}{
		"total_checks":  len(results),
		"successful":    successful,
		"failed":        len(results) - successful,
		"success_rate":  float64(successful) / float64(len(results)) * 100,
	})
	
	return results
}

// min is a helper function to return the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}