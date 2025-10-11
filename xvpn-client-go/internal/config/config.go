package config

import (
	"encoding/json"
	"io/ioutil"
	"os"
	"path/filepath"
)

// ClientConfig описывает конфигурацию клиента
type ClientConfig struct {
	UUID          string                 `json:"uuid"`
	Transports    []TransportConfig      `json:"transports"`
	RoutingRules  []RoutingRule          `json:"routing_rules"`
	ServerConfig  ServerConfig           `json:"server_config"`
	ClientOptions ClientOptions          `json:"client_options"`
	ProxyModes    ProxyConfig            `json:"proxy_modes"`
	GeoIPSettings GeoIPConfig            `json:"geoip_settings"`
}

// TransportConfig описывает конфигурацию транспорта
type TransportConfig struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	IPv6        bool                   `json:"ipv6"`
	NeedUDP     bool                   `json:"need_udp"`
	RUTraffic   bool                   `json:"ru_traffic"`
	NonRUTraffic bool                  `json:"non_ru_traffic"`
	Config      map[string]interface{} `json:"config"`
	Enabled     bool                   `json:"enabled"`
}

// RoutingRule описывает правило маршрутизации
type RoutingRule struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	TargetIPs   []string `json:"target_ips"`
	TargetPorts []int    `json:"target_ports"`
	Protocol    string   `json:"protocol"` // tcp, udp, both
	Destination string   `json:"destination"` // direct, proxy, vpn
	Enabled     bool     `json:"enabled"`
}

// ServerConfig описывает конфигурацию сервера
type ServerConfig struct {
	APIEndpoint     string   `json:"api_endpoint"`
	ManifestURL     string   `json:"manifest_url"`
	HealthCheckURL  string   `json:"health_check_url"`
	Timeout         int      `json:"timeout"` // в секундах
	RetryAttempts   int      `json:"retry_attempts"`
	AllowedDomains  []string `json:"allowed_domains"`
	IPV6Support     bool     `json:"ipv6_support"`
	CertificatePin  string   `json:"certificate_pin"`
}

// ClientOptions описывает опции клиента
type ClientOptions struct {
	AutoConnect     bool `json:"auto_connect"`
	AutoUpdate      bool `json:"auto_update"`
	MinimizeToTray  bool `json:"minimize_to_tray"`
	ShowNotifications bool `json:"show_notifications"`
	LogLevel        string `json:"log_level"` // debug, info, warn, error
	LogToFile       bool   `json:"log_to_file"`
	LogDirectory    string `json:"log_directory"`
	AutoSwitch      bool   `json:"auto_switch"`
	SwitchThreshold int    `json:"switch_threshold"` // в секундах
	MaxRetries      int    `json:"max_retries"`
}

// ProxyConfig описывает конфигурацию прокси
type ProxyConfig struct {
	Enabled          bool   `json:"enabled"`
	Mode             string `json:"mode"` // system, manual, auto
	LocalSocksPort   int    `json:"local_socks_port"`
	LocalHTTPPort    int    `json:"local_http_port"`
	AuthRequired     bool   `json:"auth_required"`
	Username         string `json:"username,omitempty"`
	Password         string `json:"password,omitempty"`
	AllowedNetworks  []string `json:"allowed_networks"`
}

// GeoIPConfig описывает конфигурацию GeoIP
type GeoIPConfig struct {
	RUCountries    []string `json:"ru_countries"`
	AutoUpdate     bool     `json:"auto_update"`
	UpdateInterval int      `json:"update_interval"` // в часах
	CacheTTL       int      `json:"cache_ttl"`      // в минутах
	DatabasePath   string   `json:"database_path"`
}

// ConfigManager управляет конфигурацией
type ConfigManager struct {
	configFile string
	config     *ClientConfig
}

// NewConfigManager создает новый менеджер конфигурации
func NewConfigManager(configFile string) *ConfigManager {
	cm := &ConfigManager{
		configFile: configFile,
		config: &ClientConfig{
			ServerConfig: ServerConfig{
				APIEndpoint:    "https://example.com:8443",
				ManifestURL:    "/transports/manifest.json",
				HealthCheckURL: "/mcp/v1/vpn.health",
				Timeout:        30,
				RetryAttempts:  3,
				IPV6Support:    true,
			},
			ClientOptions: ClientOptions{
				AutoConnect:     false,
				AutoUpdate:      true,
				MinimizeToTray:  true,
				ShowNotifications: true,
				LogLevel:        "info",
				LogToFile:       true,
				LogDirectory:    "~/xvpn-client/logs",
				AutoSwitch:      true,
				SwitchThreshold: 30,
				MaxRetries:      3,
			},
			ProxyModes: ProxyConfig{
				Enabled:        true,
				Mode:          "auto",
				LocalSocksPort: 1080,
				LocalHTTPPort:  8080,
				AuthRequired:   false,
			},
			GeoIPSettings: GeoIPConfig{
				RUCountries:    []string{"RU", "BY", "KZ", "KG", "MD", "TJ", "TM", "UZ", "AM", "AZ", "GE"},
				AutoUpdate:     true,
				UpdateInterval: 24,
				CacheTTL:       60,
				DatabasePath:   "~/xvpn-client/geoip.db",
			},
		},
	}
	
	return cm
}

// LoadConfig загружает конфигурацию из файла
func (cm *ConfigManager) LoadConfig() error {
	data, err := ioutil.ReadFile(cm.configFile)
	if err != nil {
		// Если файл не существует, создаем с дефолтной конфигурацией
		if os.IsNotExist(err) {
			return cm.SaveConfig()
		}
		return err
	}
	
	err = json.Unmarshal(data, &cm.config)
	if err != nil {
		return err
	}
	
	return nil
}

// SaveConfig сохраняет конфигурацию в файл
func (cm *ConfigManager) SaveConfig() error {
	// Создаем директорию, если она не существует
	dir := filepath.Dir(cm.configFile)
	os.MkdirAll(dir, 0755)
	
	data, err := json.MarshalIndent(cm.config, "", "  ")
	if err != nil {
		return err
	}
	
	return ioutil.WriteFile(cm.configFile, data, 0644)
}

// GetConfig возвращает текущую конфигурацию
func (cm *ConfigManager) GetConfig() *ClientConfig {
	return cm.config
}

// UpdateConfig обновляет конфигурацию
func (cm *ConfigManager) UpdateConfig(newConfig *ClientConfig) {
	cm.config = newConfig
}

// GetTransportByID возвращает транспорт по ID
func (cm *ConfigManager) GetTransportByID(id string) *TransportConfig {
	for i := range cm.config.Transports {
		if cm.config.Transports[i].ID == id {
			return &cm.config.Transports[i]
		}
	}
	return nil
}

// GetRUCountries возвращает список РУ стран
func (cm *ConfigManager) GetRUCountries() []string {
	return cm.config.GeoIPSettings.RUCountries
}

// SetAutoConnect устанавливает автоподключение
func (cm *ConfigManager) SetAutoConnect(enabled bool) {
	cm.config.ClientOptions.AutoConnect = enabled
}

// IsAutoConnect проверяет, включено ли автоподключение
func (cm *ConfigManager) IsAutoConnect() bool {
	return cm.config.ClientOptions.AutoConnect
}

// SetProxyEnabled устанавливает статус прокси
func (cm *ConfigManager) SetProxyEnabled(enabled bool) {
	cm.config.ProxyModes.Enabled = enabled
}

// IsProxyEnabled проверяет, включен ли прокси
func (cm *ConfigManager) IsProxyEnabled() bool {
	return cm.config.ProxyModes.Enabled
}

// GetServerEndpoint возвращает endpoint сервера
func (cm *ConfigManager) GetServerEndpoint() string {
	return cm.config.ServerConfig.APIEndpoint
}

// GetManifestURL возвращает URL манифеста
func (cm *ConfigManager) GetManifestURL() string {
	return cm.config.ServerConfig.ManifestURL
}

// GetClientUUID возвращает UUID клиента
func (cm *ConfigManager) GetClientUUID() string {
	return cm.config.UUID
}

// SetClientUUID устанавливает UUID клиента
func (cm *ConfigManager) SetClientUUID(uuid string) {
	cm.config.UUID = uuid
}

// GetRoutingRules возвращает правила маршрутизации
func (cm *ConfigManager) GetRoutingRules() []RoutingRule {
	return cm.config.RoutingRules
}

// GetAutoSwitch возвращает статус автопереключения
func (cm *ConfigManager) GetAutoSwitch() bool {
	return cm.config.ClientOptions.AutoSwitch
}

// GetSwitchThreshold возвращает порог переключения
func (cm *ConfigManager) GetSwitchThreshold() int {
	return cm.config.ClientOptions.SwitchThreshold
}

// GetProxyConfig возвращает конфигурацию прокси
func (cm *ConfigManager) GetProxyConfig() ProxyConfig {
	return cm.config.ProxyModes
}

// GetGeoIPConfig возвращает конфигурацию GeoIP
func (cm *ConfigManager) GetGeoIPConfig() GeoIPConfig {
	return cm.config.GeoIPSettings
}

// AddTransport добавляет транспорт в конфигурацию
func (cm *ConfigManager) AddTransport(transport TransportConfig) {
	for i, t := range cm.config.Transports {
		if t.ID == transport.ID {
			// Обновляем существующий транспорт
			cm.config.Transports[i] = transport
			return
		}
	}
	
	// Добавляем новый транспорт
	cm.config.Transports = append(cm.config.Transports, transport)
}

// RemoveTransport удаляет транспорт из конфигурации
func (cm *ConfigManager) RemoveTransport(id string) {
	for i, t := range cm.config.Transports {
		if t.ID == id {
			// Удаляем транспорт из среза
			cm.config.Transports = append(cm.config.Transports[:i], cm.config.Transports[i+1:]...)
			return
		}
	}
}