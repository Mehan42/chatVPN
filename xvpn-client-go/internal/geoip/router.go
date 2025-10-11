package geoip

import (
	"encoding/json"
	"log"
	"math/rand"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

// RouteDecision представляет решение о маршрутизации трафика
type RouteDecision struct {
	IP      string `json:"ip"`
	Country string `json:"country"`
	Direct  bool   `json:"direct"` // true = направлять напрямую (РУ), false = через VPN (неРУ)
	Reason  string `json:"reason"`
}

// Config содержит конфигурацию роутера
type Config struct {
	RUCountries  []string          `json:"ru_countries"`
	ServerConfig ServerConfig      `json:"server_config"`
	LocalNetworks []string         `json:"local_networks"`
	GeoIPData    map[string]string `json:"geoip_data"` // CIDR -> Country
}

// ServerConfig содержит конфигурацию удаленного сервера
type ServerConfig struct {
	Address     string `json:"address"`
	HealthCheck bool   `json:"health_check"`
	MaxInterval int    `json:"max_interval"` // максимальный интервал хаотичного пинга
	MinInterval int    `json:"min_interval"` // минимальный интервал хаотичного пинга
}

// TrafficRouter реализует логику маршрутизации трафика
type TrafficRouter struct {
	config       *Config
	ruNetworks   []*net.IPNet
	localNetworks []*net.IPNet
	mutex        sync.RWMutex
	serverStatus bool
	serverMutex  sync.RWMutex
}

// NewTrafficRouter создает новый экземпляр роутера трафика
func NewTrafficRouter(configPath string) (*TrafficRouter, error) {
	// В реальном приложении загружаем конфигурацию из файла
	config := &Config{
		RUCountries: []string{"RU", "BY", "KZ", "KG", "MD", "TJ", "TM", "UZ", "AM", "AZ", "GE"},
		ServerConfig: ServerConfig{
			Address:     "example.com:443",
			HealthCheck: true,
			MaxInterval: 300, // 5 минут
			MinInterval: 30,  // 30 секунд
		},
		LocalNetworks: []string{
			"127.0.0.0/8",    // Loopback
			"10.0.0.0/8",     // Private network
			"172.16.0.0/12",  // Private network
			"192.168.0.0/16", // Private network
			"169.254.0.0/16", // Link-local
		},
		GeoIPData: map[string]string{
			// Пример данных - в реальном приложении это будет полная база GeoIP
			"77.0.0.0/8":  "RU",
			"80.0.0.0/8":  "RU",
			"81.0.0.0/8":  "RU",
			"82.0.0.0/8":  "RU",
			"83.0.0.0/8":  "RU",
			"84.0.0.0/8":  "RU",
			"85.0.0.0/8":  "RU",
			"86.0.0.0/8":  "RU",
			"87.0.0.0/8":  "RU",
			"88.0.0.0/8":  "RU",
			"89.0.0.0/8":  "RU",
			"90.0.0.0/8":  "RU",
			"91.0.0.0/8":  "RU",
			"92.0.0.0/8":  "RU",
			"93.0.0.0/8":  "RU",
			"94.0.0.0/8":  "RU",
			"95.0.0.0/8":  "RU",
			"176.0.0.0/8": "RU",
			"178.0.0.0/8": "RU",  // Россия (часть IP)
"178.200.0.0/16": "BY",  // Беларусь (для примера)
			"185.0.0.0/8": "RU",
			"188.0.0.0/8": "RU",
			"193.0.0.0/8": "RU",
			"194.0.0.0/8": "RU",
			"195.0.0.0/8": "RU",
			"37.0.0.0/8":  "UA",
			"31.0.0.0/8":  "UA",
			"176.200.0.0/16": "BY",  // Беларусь (для примера)
		},
	}

	router := &TrafficRouter{
		config: config,
		serverStatus: true, // Изначально считаем сервер доступным
	}

	// Инициализация RU сетей
	router.initRUNetworks()

	// Инициализация локальных сетей
	router.initLocalNetworks()

	// Запуск хаотичного мониторинга сервера (если включен)
	if config.ServerConfig.HealthCheck {
		go router.startChaoticServerMonitoring()
	}

	return router, nil
}

// initRUNetworks инициализирует список RU сетей
func (r *TrafficRouter) initRUNetworks() {
	for cidr, country := range r.config.GeoIPData {
		// Проверяем, является ли страна РУ страной
		if r.isRUCountry(country) {
			_, network, _ := net.ParseCIDR(cidr)
			if network != nil {
				r.ruNetworks = append(r.ruNetworks, network)
			}
		}
	}
}

// initLocalNetworks инициализирует список локальных сетей
func (r *TrafficRouter) initLocalNetworks() {
	for _, cidrStr := range r.config.LocalNetworks {
		_, network, _ := net.ParseCIDR(cidrStr)
		if network != nil {
			r.localNetworks = append(r.localNetworks, network)
		}
	}
}

// isRUCountry проверяет, является ли страна РУ страной
func (r *TrafficRouter) isRUCountry(country string) bool {
	for _, ruCountry := range r.config.RUCountries {
		if strings.EqualFold(country, ruCountry) {
			return true
		}
	}
	return false
}

// IsRUNetwork проверяет, принадлежит ли IP к РУ сетям
func (r *TrafficRouter) IsRUNetwork(ip net.IP) bool {
	r.mutex.RLock()
	defer r.mutex.RUnlock()

	for _, network := range r.ruNetworks {
		if network.Contains(ip) {
			return true
		}
	}
	return false
}

// IsLocalNetwork проверяет, принадлежит ли IP к локальным сетям
func (r *TrafficRouter) IsLocalNetwork(ip net.IP) bool {
	r.mutex.RLock()
	defer r.mutex.RUnlock()

	for _, network := range r.localNetworks {
		if network.Contains(ip) {
			return true
		}
	}
	return false
}

// GetCountryByIP возвращает страну по IP-адресу (упрощенная реализация)
func (r *TrafficRouter) GetCountryByIP(ip net.IP) string {
	// В реальной реализации здесь будет обращение к встроенной GeoIP базе
	// В данном примере используем упрощенную логику из geoipData

	r.mutex.RLock()
	defer r.mutex.RUnlock()

	for cidr, country := range r.config.GeoIPData {
		_, network, _ := net.ParseCIDR(cidr)
		if network != nil && network.Contains(ip) {
			return country
		}
	}

	// В реальной реализации здесь будет вызов GeoIP базы
	// Для примера возвращаем пустую строку
	// Имитируем вызов GeoIP базы
	return r.simulateGeoIPCountry(ip)
}

// simulateGeoIPCountry симулирует получение страны через GeoIP (в реальности это будет точная база)
func (r *TrafficRouter) simulateGeoIPCountry(ip net.IP) string {
	// В реальной реализации здесь будет точное определение страны
	// через встроенную GeoLite2 базу. Для примера - простая логика.

	ipStr := ip.String()

	// Примеры IP-адресов для разных стран (в реальной версии это будет точное определение)
	if strings.HasPrefix(ipStr, "77.") || strings.HasPrefix(ipStr, "80.") || 
	   strings.HasPrefix(ipStr, "81.") || strings.HasPrefix(ipStr, "82.") ||
	   strings.HasPrefix(ipStr, "83.") || strings.HasPrefix(ipStr, "84.") ||
	   strings.HasPrefix(ipStr, "85.") || strings.HasPrefix(ipStr, "86.") ||
	   strings.HasPrefix(ipStr, "87.") || strings.HasPrefix(ipStr, "88.") ||
	   strings.HasPrefix(ipStr, "89.") || strings.HasPrefix(ipStr, "90.") ||
	   strings.HasPrefix(ipStr, "91.") || strings.HasPrefix(ipStr, "92.") ||
	   strings.HasPrefix(ipStr, "93.") || strings.HasPrefix(ipStr, "94.") ||
	   strings.HasPrefix(ipStr, "95.") || strings.HasPrefix(ipStr, "176.") ||
	   strings.HasPrefix(ipStr, "178.") || strings.HasPrefix(ipStr, "185.") ||
	   strings.HasPrefix(ipStr, "188.") || strings.HasPrefix(ipStr, "193.") ||
	   strings.HasPrefix(ipStr, "194.") || strings.HasPrefix(ipStr, "195.") {
		return "RU"
	}

	// Примеры для других стран
	if strings.HasPrefix(ipStr, "37.") || strings.HasPrefix(ipStr, "31.") {
		return "UA"
	}

	// По умолчанию - не РУ страна
	return "US" // Пример, в реальности будет точное определение
}

// IsRUDestination проверяет, является ли IP-адрес российским
func (r *TrafficRouter) IsRUDestination(ipStr string) bool {
	ip := net.ParseIP(ipStr)
	if ip == nil {
		return false // Некорректный IP
	}

	// Проверка локальных сетей
	if r.IsLocalNetwork(ip) {
		return true // Локальный трафик всегда напрямую
	}

	// Проверка РУ сетей
	if r.IsRUNetwork(ip) {
		return true // РУ сеть
	}

	// Проверка через GeoIP
	country := r.GetCountryByIP(ip)
	if country == "" {
		return false // Не удалось определить страну
	}

	// Проверка в списке РУ стран
	return r.isRUCountry(country)
}

// GetRouteDecision возвращает полное решение о маршрутизации
func (r *TrafficRouter) GetRouteDecision(ipStr string) *RouteDecision {
	ip := net.ParseIP(ipStr)
	if ip == nil {
		return &RouteDecision{
			IP:     ipStr,
			Direct: false,
			Reason: "invalid_ip",
		}
	}

	// Проверка локальных сетей
	if r.IsLocalNetwork(ip) {
		return &RouteDecision{
			IP:     ipStr,
			Direct: true,
			Reason: "local_network",
		}
	}

	// Проверка РУ сетей
	if r.IsRUNetwork(ip) {
		return &RouteDecision{
			IP:     ipStr,
			Direct: true,
			Reason: "ru_network",
		}
	}

	// Проверка через GeoIP
	country := r.GetCountryByIP(ip)
	if country == "" {
		return &RouteDecision{
			IP:      ipStr,
			Country: "unknown",
			Direct:  false,
			Reason:  "geoip_failed",
		}
	}

	// Проверка в списке РУ стран
	isRU := r.isRUCountry(country)

	return &RouteDecision{
		IP:      ipStr,
		Country: country,
		Direct:  isRU,
		Reason:  "geoip_country",
	}
}

// HandleHTTPRequest обрабатывает HTTP запросы для маршрутизации
func (r *TrafficRouter) HandleHTTPRequest(w http.ResponseWriter, req *http.Request) {
	ip := req.URL.Query().Get("ip")
	if ip == "" {
		http.Error(w, "требуется параметр ip", http.StatusBadRequest)
		return
	}

	decision := r.GetRouteDecision(ip)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(decision)
}

// StartHTTPServer запускает HTTP сервер
func (r *TrafficRouter) StartHTTPServer(port string) error {
	http.HandleFunc("/route", r.HandleHTTPRequest)
	http.HandleFunc("/health", func(w http.ResponseWriter, req *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	log.Printf("Traffic Router HTTP API запущен на порту %s", port)
	return http.ListenAndServe(":"+port, nil)
}

// CheckServerHealth проверяет доступность удаленного сервера
func (r *TrafficRouter) CheckServerHealth() bool {
	// В реальной реализации здесь будет проверка доступности сервера
	// через разные методы (ICMP ping, HTTP health check, и т.д.)
	
	// Имитация проверки сервера
	// В реальной реализации здесь будет реальная проверка
	healthy := true // предполагаем, что сервер здоров
	
	r.serverMutex.Lock()
	r.serverStatus = healthy
	r.serverMutex.Unlock()
	
	return healthy
}

// startChaoticServerMonitoring запускает хаотичное мониторинг сервера
func (r *TrafficRouter) startChaoticServerMonitoring() {
	for {
		// Получаем случайный интервал в пределах заданных границ
		interval := time.Duration(r.config.ServerConfig.MinInterval + 
			rand.Intn(r.config.ServerConfig.MaxInterval - r.config.ServerConfig.MinInterval)) * time.Second
		
		// Ждем случайное время (хаотичный пинг)
		time.Sleep(interval)
		
		// Проверяем статус сервера
		healthy := r.CheckServerHealth()
		
		if !healthy {
			log.Printf("Сервер недоступен: %s", r.config.ServerConfig.Address)
			// Здесь может быть логика уведомления или переключения на резервный сервер
		} else {
			log.Printf("Сервер доступен: %s", r.config.ServerConfig.Address)
		}
	}
}

// GetServerStatus возвращает статус сервера
func (r *TrafficRouter) GetServerStatus() bool {
	r.serverMutex.RLock()
	defer r.serverMutex.RUnlock()
	return r.serverStatus
}

// Close освобождает ресурсы
func (r *TrafficRouter) Close() {
	// В текущей реализации нет ресурсов для освобождения
	// В реальной реализации здесь будет закрытие GeoIP базы и т.д.
}