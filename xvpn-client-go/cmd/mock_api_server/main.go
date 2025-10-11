package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

// HealthResponse структура ответа о состоянии здоровья
type HealthResponse struct {
	Status        string                 `json:"status"`
	MaskScore     int                    `json:"mask_score"`
	Timestamp     float64                `json:"timestamp"`
	Version       string                 `json:"version"`
	Services      map[string]bool        `json:"services"`
	SystemMetrics map[string]interface{} `json:"system_metrics"`
}

// Transport структура транспорта
type Transport struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	IPv6        bool                   `json:"ipv6"`
	NeedUDP     bool                   `json:"need_udp"`
	RUTraffic   bool                   `json:"ru_traffic"`
	NonRUTraffic bool                  `json:"non_ru_traffic"`
	Config      map[string]interface{} `json:"config"`
}

// TransportManifest структура манифеста транспортов
type TransportManifest struct {
	Version    int        `json:"version"`
	Transports []Transport `json:"transports"`
}

// ClientConfig структура конфигурации клиента
type ClientConfig struct {
	UUID          string                 `json:"uuid"`
	CreatedAt     float64                `json:"created_at"`
	Routing       RoutingConfig          `json:"routing"`
	Transports    []Transport           `json:"transports"`
	ServerConfig  ServerConfig           `json:"server_config"`
	ClientOptions ClientOptions          `json:"client_options"`
	ProxyModes    ProxyConfig            `json:"proxy_modes"`
	GeoIPSettings GeoIPConfig            `json:"geoip_settings"`
}

// RoutingConfig структура конфигурации маршрутизации
type RoutingConfig struct {
	Rules map[string][]string `json:"rules"`
}

// ServerConfig структура конфигурации сервера
type ServerConfig struct {
	APIEndpoint     string   `json:"api_endpoint"`
	ManifestURL     string   `json:"manifest_url"`
	HealthCheckURL  string   `json:"health_check_url"`
	Timeout         int      `json:"timeout"`
	RetryAttempts   int      `json:"retry_attempts"`
	AllowedDomains  []string `json:"allowed_domains"`
	IPV6Support     bool     `json:"ipv6_support"`
	CertificatePin  string   `json:"certificate_pin"`
}

// ClientOptions структура опций клиента
type ClientOptions struct {
	AutoConnect     bool `json:"auto_connect"`
	AutoUpdate      bool `json:"auto_update"`
	MinimizeToTray  bool `json:"minimize_to_tray"`
	ShowNotifications bool `json:"show_notifications"`
	LogLevel        string `json:"log_level"`
	LogToFile       bool   `json:"log_to_file"`
	LogDirectory    string `json:"log_directory"`
	AutoSwitch      bool   `json:"auto_switch"`
	SwitchThreshold int    `json:"switch_threshold"`
	MaxRetries      int    `json:"max_retries"`
}

// ProxyConfig структура конфигурации прокси
type ProxyConfig struct {
	Enabled          bool   `json:"enabled"`
	Mode             string `json:"mode"`
	LocalSocksPort   int    `json:"local_socks_port"`
	LocalHTTPPort    int    `json:"local_http_port"`
	AuthRequired     bool   `json:"auth_required"`
	Username         string `json:"username,omitempty"`
	Password         string `json:"password,omitempty"`
	AllowedNetworks  []string `json:"allowed_networks"`
}

// GeoIPConfig структура конфигурации GeoIP
type GeoIPConfig struct {
	RUCountries    []string `json:"ru_countries"`
	AutoUpdate     bool     `json:"auto_update"`
	UpdateInterval int      `json:"update_interval"`
	CacheTTL       int      `json:"cache_ttl"`
	DatabasePath   string   `json:"database_path"`
}

// MockAPIServer имитирует XVPN API сервер
type MockAPIServer struct {
	server *http.Server
}

// NewMockAPIServer создает новый mock API сервер
func NewMockAPIServer() *MockAPIServer {
	mux := http.NewServeMux()
	
	server := &http.Server{
		Addr:    ":8443",
		Handler: mux,
	}
	
	mockServer := &MockAPIServer{
		server: server,
	}
	
	// Регистрируем обработчики
	mux.HandleFunc("/mcp/v1/vpn.health", mockServer.healthHandler)
	mux.HandleFunc("/transports/manifest.json", mockServer.manifestHandler)
	mux.HandleFunc("/clients/", mockServer.clientConfigHandler)
	mux.HandleFunc("/mcp/v1/admin.newclient", mockServer.createClientHandler)
	
	return mockServer
}

// healthHandler обрабатывает запросы к /mcp/v1/vpn.health
func (s *MockAPIServer) healthHandler(w http.ResponseWriter, r *http.Request) {
	health := HealthResponse{
		Status:    "healthy",
		MaskScore: 5,
		Timestamp: float64(time.Now().Unix()),
		Version:   "1.0.0-mock",
		Services: map[string]bool{
			"xray":    true,
			"traefik": true,
			"redis":   true,
		},
		SystemMetrics: map[string]interface{}{
			"cpu_percent":    15.5,
			"memory_percent": 32.1,
			"disk_percent":   45.2,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

// manifestHandler обрабатывает запросы к /transports/manifest.json
func (s *MockAPIServer) manifestHandler(w http.ResponseWriter, r *http.Request) {
	manifest := TransportManifest{
		Version: 1,
		Transports: []Transport{
			{
				ID:          "vless-reality",
				Name:        "VLESS + Reality",
				Type:        "vless-reality",
				Priority:    1,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   true,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "tcp",
				},
			},
			{
				ID:          "v2ray-websocket",
				Name:        "V2Ray WebSocket",
				Type:        "v2ray-websocket",
				Priority:    2,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "ws",
					"path":     "/v2ray",
				},
			},
			{
				ID:          "wireguard-tls",
				Name:        "WireGuard-over-TLS",
				Type:        "wireguard-tls",
				Priority:    3,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     51820,
					"protocol": "udp",
				},
			},
			{
				ID:          "trojan-tcp",
				Name:        "Trojan TCP",
				Type:        "trojan-tcp",
				Priority:    4,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   true,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "tcp",
				},
			},
			{
				ID:          "shadowsocks-aead",
				Name:        "ShadowSocks AEAD",
				Type:        "shadowsocks-aead",
				Priority:    5,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     8484,
					"protocol": "udp",
				},
			},
			{
				ID:          "hysteria2",
				Name:        "Hysteria 2",
				Type:        "hysteria2",
				Priority:    6,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     2096,
					"protocol": "udp",
				},
			},
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(manifest)
}

// clientConfigHandler обрабатывает запросы к /clients/{uuid}.json
func (s *MockAPIServer) clientConfigHandler(w http.ResponseWriter, r *http.Request) {
	// Извлекаем UUID из URL
	// В реальной реализации здесь будет парсинг пути
	
	clientConfig := ClientConfig{
		UUID:      "test-client-uuid-from-server",
		CreatedAt: float64(time.Now().Unix()),
		Routing: RoutingConfig{
			Rules: map[string][]string{
				"ru_traffic_transport":     {"vless-reality", "trojan-tcp"},
				"non_ru_traffic_transport": {"v2ray-websocket", "hysteria2", "wireguard-tls"},
				"fallback_transports":      {"trojan-tcp", "hysteria2", "shadowsocks-aead"},
			},
		},
		ServerConfig: ServerConfig{
			APIEndpoint:    "https://77.110.123.27:8443",
			ManifestURL:    "/transports/manifest.json",
			HealthCheckURL: "/mcp/v1/vpn.health",
			Timeout:        30,
			RetryAttempts:  3,
			AllowedDomains: []string{"*.example.com", "*.test.com"},
			IPV6Support:    true,
			CertificatePin: "sha256/example-certificate-pin",
		},
		ClientOptions: ClientOptions{
			AutoConnect:       true,
			AutoUpdate:        true,
			MinimizeToTray:    true,
			ShowNotifications: true,
			LogLevel:          "info",
			LogToFile:         true,
			LogDirectory:      "~/chatvpn/client/logs",
			AutoSwitch:        true,
			SwitchThreshold:   30,
			MaxRetries:        3,
		},
		ProxyModes: ProxyConfig{
			Enabled:        true,
			Mode:          "auto",
			LocalSocksPort: 1080,
			LocalHTTPPort:  8080,
			AuthRequired:   false,
			AllowedNetworks: []string{"127.0.0.0/8", "::1/128"},
		},
		GeoIPSettings: GeoIPConfig{
			RUCountries:    []string{"RU", "BY", "KZ", "KG", "MD", "TJ", "TM", "UZ", "AM", "AZ", "GE"},
			AutoUpdate:     true,
			UpdateInterval: 24,
			CacheTTL:       60,
			DatabasePath:   "~/chatvpn/client/geoip.db",
		},
		Transports: []Transport{
			{
				ID:          "vless-reality",
				Name:        "VLESS + Reality",
				Type:        "vless-reality",
				Priority:    1,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   true,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "tcp",
					"uuid":     "test-client-uuid-from-server",
				},
			},
			{
				ID:          "v2ray-websocket",
				Name:        "V2Ray WebSocket",
				Type:        "v2ray-websocket",
				Priority:    2,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "ws",
					"path":     "/v2ray/test-client-uuid-from-server",
					"uuid":     "test-client-uuid-from-server",
				},
			},
			{
				ID:          "wireguard-tls",
				Name:        "WireGuard-over-TLS",
				Type:        "wireguard-tls",
				Priority:    3,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":      "77.110.123.27",
					"port":        51820,
					"protocol":    "udp",
					"public_key":  "PLACEHOLDER_PUBLIC_KEY",
					"uuid":        "test-client-uuid-from-server",
				},
			},
			{
				ID:          "trojan-tcp",
				Name:        "Trojan TCP",
				Type:        "trojan-tcp",
				Priority:    4,
				IPv6:        true,
				NeedUDP:     false,
				RUTraffic:   true,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     443,
					"protocol": "tcp",
					"password": "test-client-uuid-from-server",
					"sni":      "77.110.123.27",
				},
			},
			{
				ID:          "shadowsocks-aead",
				Name:        "ShadowSocks AEAD",
				Type:        "shadowsocks-aead",
				Priority:    5,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     8484,
					"protocol": "udp",
					"method":   "2022-blake3-aes-256-gcm",
					"password": "test-client-uuid-from-server",
				},
			},
			{
				ID:          "hysteria2",
				Name:        "Hysteria 2",
				Type:        "hysteria2",
				Priority:    6,
				IPv6:        true,
				NeedUDP:     true,
				RUTraffic:   false,
				NonRUTraffic: true,
				Config: map[string]interface{}{
					"server":   "77.110.123.27",
					"port":     2096,
					"protocol": "udp",
					"password": "test-client-uuid-from-server",
					"sni":      "77.110.123.27",
				},
			},
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(clientConfig)
}

// createClientHandler обрабатывает запросы к /mcp/v1/admin.newclient
func (s *MockAPIServer) createClientHandler(w http.ResponseWriter, r *http.Request) {
	// В реальной реализации здесь будет создание нового клиента
	// Для имитации просто возвращаем тестовый UUID
	
	response := map[string]interface{}{
		"success":      true,
		"uuid":         "generated-test-uuid-by-server",
		"config_url":   "/clients/generated-test-uuid-by-server.json",
		"created_at":   time.Now().Unix(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Start запускает сервер
func (s *MockAPIServer) Start() error {
	log.Println("Mock API сервер запущен на порту :8443")
	return s.server.ListenAndServe()
}

// Stop останавливает сервер
func (s *MockAPIServer) Stop() error {
	return s.server.Close()
}

func main() {
	server := NewMockAPIServer()
	log.Fatal(server.Start())
}