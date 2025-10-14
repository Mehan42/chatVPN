// Package tunnelverifier provides functionality to detect IP address leaks
package tunnelverifier

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
	"time"
)

// IPLocation contains information about an IP address location
type IPLocation struct {
	IP          string `json:"ip"`
	Country     string `json:"country"`
	CountryCode string `json:"country_code"`
	Region      string `json:"region"`
	City        string `json:"city"`
	ISP         string `json:"isp"`
	Org         string `json:"org"`
	ASN         string `json:"asn"`
}

// IPLeakDetector handles detection of IP address leaks
type IPLeakDetector struct {
	logger         *log.Logger
	enhancedLogger *Logger
	httpClient     *http.Client
	vpnIPs         []string // Known VPN IP addresses
	knownNonRUIPs  []string // IPs known to be outside RU region
}

// NewIPLeakDetector creates a new IP leak detector
func NewIPLeakDetector(logger *log.Logger) *IPLeakDetector {
	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	return &IPLeakDetector{
		logger:         logger,
		enhancedLogger: NewLogger(Info, false), // Default to Info level
		httpClient:     client,
		// These could come from configuration in a real implementation
		vpnIPs:        []string{},
		knownNonRUIPs: []string{},
	}
}

// SetLogger sets the enhanced logger
func (d *IPLeakDetector) SetLogger(logger *Logger) {
	if logger != nil {
		d.enhancedLogger = logger
	}
}

// DetectIPLeak checks for IP address leaks by comparing public IP before/after VPN activation
func (d *IPLeakDetector) DetectIPLeak() (bool, error) {
	d.enhancedLogger.Info("Starting IP leak detection", nil)

	// Get current public IP address
	startTime := time.Now()
	publicIP, err := d.getPublicIP()
	duration := time.Since(startTime)
	if err != nil {
		d.enhancedLogger.Error("Failed to get public IP", map[string]interface{}{
			"error":    err.Error(),
			"duration": duration.Seconds(),
		})
		return false, fmt.Errorf("failed to get public IP: %w", err)
	}

	d.enhancedLogger.Info("Current public IP retrieved", map[string]interface{}{
		"ip":       publicIP,
		"duration": duration.Seconds(),
	})

	// Check if IP is in Russia or other specified regions
	isInRestrictedRegion, err := d.isIPInRestrictedRegion(publicIP)
	if err != nil {
		d.enhancedLogger.Error("Failed to check IP region", map[string]interface{}{
			"ip":    publicIP,
			"error": err.Error(),
		})
		return false, fmt.Errorf("failed to check IP region: %w", err)
	}

	// If the IP is in a restricted region (like Russia), it may indicate an IP leak
	if isInRestrictedRegion {
		d.enhancedLogger.Warn("IP leak detected", map[string]interface{}{
			"ip": publicIP,
		})
		return false, nil
	}

	d.enhancedLogger.Info("No IP leak detected", map[string]interface{}{
		"ip": publicIP,
	})
	return true, nil
}

// getPublicIP retrieves the current public IP address
func (d *IPLeakDetector) getPublicIP() (string, error) {
	// Try multiple services to get public IP
	services := []string{
		"https://httpbin.org/ip",
		"https://api.ipify.org?format=json",
		"https://jsonip.com",
		"https://icanhazip.com",
	}

	for _, service := range services {
		ip, err := d.getIPFromService(service)
		if err == nil {
			return ip, nil
		}
		d.logger.Printf("Failed to get IP from %s: %v", service, err)
	}

	return "", fmt.Errorf("failed to get public IP from any service")
}

// getIPFromService retrieves the public IP from a specific service
func (d *IPLeakDetector) getIPFromService(service string) (string, error) {
	resp, err := d.httpClient.Get(service)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	// Different services return IP in different formats
	bodyStr := strings.TrimSpace(string(body))

	// Check if it's a JSON response
	if strings.HasPrefix(bodyStr, "{") {
		var result map[string]interface{}
		if err := json.Unmarshal([]byte(bodyStr), &result); err != nil {
			return "", err
		}

		// Check for common JSON field names for IP
		for _, field := range []string{"ip", "origin"} {
			if ip, ok := result[field].(string); ok {
				// Clean the IP (some services return it with quotes or other characters)
				return strings.TrimSpace(strings.Trim(ip, "\" \n\t")), nil
			}
		}

		return "", fmt.Errorf("IP field not found in JSON response")
	}

	// For plain text responses, return the cleaned content
	return strings.TrimSpace(strings.Trim(bodyStr, "\" \n\t")), nil
}

// isIPInRestrictedRegion checks if the given IP is in a restricted region (like Russia)
func (d *IPLeakDetector) isIPInRestrictedRegion(ip string) (bool, error) {
	// Validate IP format
	parsedIP := net.ParseIP(ip)
	if parsedIP == nil {
		return false, fmt.Errorf("invalid IP address: %s", ip)
	}

	// Get location information for the IP
	location, err := d.getIPLocation(ip)
	if err != nil {
		return false, fmt.Errorf("failed to get location for IP %s: %w", ip, err)
	}

	// Check if the IP is in Russia or CIS countries (RU, BY, KZ, etc.)
	restrictedCountries := []string{"RU", "BY", "KZ", "AM", "AZ", "GE", "KG", "MD", "TJ", "TM", "UZ"}

	for _, country := range restrictedCountries {
		if strings.ToUpper(location.CountryCode) == country {
			d.logger.Printf("IP %s is in restricted country: %s (%s)", ip, location.Country, location.CountryCode)
			return true, nil
		}
	}

	return false, nil
}

// getIPLocation retrieves location information for an IP address
func (d *IPLeakDetector) getIPLocation(ip string) (*IPLocation, error) {
	// Try multiple IP geolocation services
	services := []string{
		"https://ipapi.co/%s/json/",
		"https://ipinfo.io/%s/json",
		"https://freegeoip.app/json/%s",
		"https://json.geoiplookup.app",
	}

	// For json.geoiplookup.app, we need to send the IP in the request body
	if strings.Contains(ip, ".") { // IPv4
		for _, service := range services {
			if strings.Contains(service, "geoiplookup") {
				continue // Handle this separately
			}

			serviceURL := fmt.Sprintf(service, ip)
			location, err := d.getLocationFromService(serviceURL)
			if err == nil {
				return location, nil
			}
			d.logger.Printf("Failed to get location from %s: %v", serviceURL, err)
		}
	}

	// Special handling for geoiplookup service with POST request
	location, err := d.getLocationFromGeoLookupService(ip)
	if err == nil {
		return location, nil
	}

	return nil, fmt.Errorf("failed to get location from any service")
}

// getLocationFromService gets location from a standard geolocation service
func (d *IPLeakDetector) getLocationFromService(serviceURL string) (*IPLocation, error) {
	resp, err := d.httpClient.Get(serviceURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("service returned status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var location IPLocation
	if err := json.Unmarshal(body, &location); err != nil {
		return nil, err
	}

	return &location, nil
}

// getLocationFromGeoLookupService gets location using the geoiplookup service
func (d *IPLeakDetector) getLocationFromGeoLookupService(ip string) (*IPLocation, error) {
	// Create a POST request to json.geoiplookup.app
	jsonData := fmt.Sprintf(`{"ip":"%s"}`, ip)
	resp, err := d.httpClient.Post("https://json.geoiplookup.app", "application/json", strings.NewReader(jsonData))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("geoiplookup service returned status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var location IPLocation
	if err := json.Unmarshal(body, &location); err != nil {
		return nil, err
	}

	return &location, nil
}

// SetVPNIPs sets the known VPN IP addresses for comparison
func (d *IPLeakDetector) SetVPNIPs(ips []string) {
	d.vpnIPs = ips
}

// SetKnownNonRUIPs sets known non-RU IP addresses for comparison
func (d *IPLeakDetector) SetKnownNonRUIPs(ips []string) {
	d.knownNonRUIPs = ips
}

// CompareWithVPNIPs checks if the current IP matches known VPN IPs
func (d *IPLeakDetector) CompareWithVPNIPs() (bool, error) {
	publicIP, err := d.getPublicIP()
	if err != nil {
		return false, err
	}

	for _, vpnIP := range d.vpnIPs {
		if publicIP == vpnIP {
			d.logger.Printf("IP matches known VPN IP: %s", publicIP)
			return true, nil
		}
	}

	d.logger.Printf("Current public IP %s does not match any known VPN IPs", publicIP)
	return false, nil
}
