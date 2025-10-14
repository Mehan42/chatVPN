package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"testing"
	"time"
)

const (
	testServerURL = "http://localhost:8443"
	testTimeout   = 10 * time.Second
)

func TestMain(m *testing.M) {
	// Setup test environment
	fmt.Println("🚀 Starting XVPN Go Server tests...")

	// Check if server is running
	if !isServerRunning() {
		fmt.Println("❌ Server is not running. Please start the server first.")
		os.Exit(1)
	}

	// Run tests
	code := m.Run()

	// Cleanup
	fmt.Println("✅ Tests completed")
	os.Exit(code)
}

func isServerRunning() bool {
	client := &http.Client{Timeout: testTimeout}
	resp, err := client.Get(testServerURL + "/health")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}

func TestHealthEndpoint(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	resp, err := client.Get(testServerURL + "/health")
	if err != nil {
		t.Fatalf("Failed to call health endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var health map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode health response: %v", err)
	}

	if health["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %v", health["status"])
	}

	fmt.Println("✅ Health endpoint test passed")
}

func TestMetricsEndpoint(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	// Test Prometheus metrics
	resp, err := client.Get(testServerURL + "/metrics")
	if err != nil {
		t.Fatalf("Failed to call metrics endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("Failed to read metrics response: %v", err)
	}

	metrics := string(body)
	if !contains(metrics, "xvpn_active_connections") {
		t.Error("Metrics do not contain active connections")
	}

	fmt.Println("✅ Metrics endpoint test passed")
}

func TestMetricsJSONEndpoint(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	resp, err := client.Get(testServerURL + "/metrics/json")
	if err != nil {
		t.Fatalf("Failed to call metrics JSON endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var metrics map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&metrics); err != nil {
		t.Fatalf("Failed to decode metrics JSON response: %v", err)
	}

	if _, exists := metrics["active_connections"]; !exists {
		t.Error("Metrics JSON does not contain active_connections")
	}

	fmt.Println("✅ Metrics JSON endpoint test passed")
}

func TestClientsEndpoint(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	// Test getting non-existent client
	resp, err := client.Get(testServerURL + "/clients/nonexistent.json")
	if err != nil {
		t.Fatalf("Failed to call clients endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("Expected status 404 for non-existent client, got %d", resp.StatusCode)
	}

	fmt.Println("✅ Clients endpoint test passed")
}

func TestTransportsEndpoint(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	resp, err := client.Get(testServerURL + "/transports/manifest.json")
	if err != nil {
		t.Fatalf("Failed to call transports endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var manifest map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&manifest); err != nil {
		t.Fatalf("Failed to decode transport manifest: %v", err)
	}

	if _, exists := manifest["transports"]; !exists {
		t.Error("Transport manifest does not contain transports array")
	}

	fmt.Println("✅ Transports endpoint test passed")
}

func TestMCPEndpoints(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	// Test VPN health MCP endpoint
	resp, err := client.Get(testServerURL + "/mcp/v1/vpn.health")
	if err != nil {
		t.Fatalf("Failed to call MCP VPN health endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var health map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode MCP health response: %v", err)
	}

	if health["status"] != "operational" {
		t.Errorf("Expected MCP status 'operational', got %v", health["status"])
	}

	fmt.Println("✅ MCP endpoints test passed")
}

func TestAdminEndpoints(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	// Test without auth header
	resp, err := client.Get(testServerURL + "/admin/clients")
	if err != nil {
		t.Fatalf("Failed to call admin endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("Expected status 401 for unauthenticated request, got %d", resp.StatusCode)
	}

	// Test with auth header
	req, err := http.NewRequest("GET", testServerURL+"/admin/clients", nil)
	if err != nil {
		t.Fatalf("Failed to create authenticated request: %v", err)
	}
	req.Header.Set("Authorization", "Bearer admin-token")

	resp, err = client.Do(req)
	if err != nil {
		t.Fatalf("Failed to call authenticated admin endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200 for authenticated request, got %d", resp.StatusCode)
	}

	fmt.Println("✅ Admin endpoints test passed")
}

func TestDatabaseOperations(t *testing.T) {
	// Skip database test for now - requires internal package access
	// This would be tested in integration tests within the same module
	t.Skip("Database operations test skipped - requires internal package access")

	fmt.Println("✅ Database operations test skipped (integration test)")
}

func TestLoadTesting(t *testing.T) {
	client := &http.Client{Timeout: testTimeout}

	// Simple load test - make multiple concurrent requests
	concurrency := 10
	requests := 50

	results := make(chan bool, requests)

	for i := 0; i < concurrency; i++ {
		go func() {
			for j := 0; j < requests/concurrency; j++ {
				resp, err := client.Get(testServerURL + "/health")
				if err == nil && resp.StatusCode == http.StatusOK {
					resp.Body.Close()
					results <- true
				} else {
					results <- false
				}
			}
		}()
	}

	successCount := 0
	for i := 0; i < requests; i++ {
		if <-results {
			successCount++
		}
	}

	successRate := float64(successCount) / float64(requests)
	if successRate < 0.95 { // 95% success rate
		t.Errorf("Load test failed: %d/%d successful requests (%.1f%%)",
			successCount, requests, successRate*100)
	}

	fmt.Printf("✅ Load testing passed: %d/%d successful requests (%.1f%%)\n",
		successCount, requests, successRate*100)
}

// Helper function to check if string contains substring
func contains(s, substr string) bool {
	return bytes.Contains([]byte(s), []byte(substr))
}
