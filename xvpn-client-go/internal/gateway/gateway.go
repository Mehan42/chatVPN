// Package gateway предоставляет модуль маршрутизации трафика для XVPN клиента
// Он перехватывает сетевые пакеты и направляет их либо напрямую, либо через туннель
// в зависимости от географического положения адресата

package gateway

import (
	"log"
	"os"
	"os/signal"
	"syscall"
	"xvpn-client-go/internal/gateway/config"
	"xvpn-client-go/internal/gateway/core"
	"xvpn-client-go/internal/gateway/interceptor"
	"xvpn-client-go/internal/gateway/steps"
)

// Gateway - основная структура модуля маршрутизации
type Gateway struct {
	config       *config.Config
	engine       *core.RoutingEngine
	interceptor  *interceptor.NFQueueInterceptor
	geoStep      *steps.GeoIPStep
	tunnelStep   *steps.TunnelRouteStep
}

// New создает новый экземпляр Gateway
func New(configPath string) (*Gateway, error) {
	// Загрузка конфигурации
	cfg, err := config.Load(configPath)
	if err != nil {
		// Если config.yaml не найден, используем значения по умолчанию
		log.Println("Config file not found, using default values")
		cfg = &config.Config{
			Gateway: struct {
				LogLevel string `yaml:"log_level"`
			}{LogLevel: "info"},
			
			Steps: struct {
				GeoIP struct {
					Enabled              bool     `yaml:"enabled"`
					DatabasePath         string   `yaml:"database_path"`
					DirectRouteCountries []string `yaml:"direct_route_countries"`
				} `yaml:"geoip"`
				Tunnel struct {
					Enabled      bool   `yaml:"enabled"`
					RemoteServer string `yaml:"remote_server"`
					TLSSNI       string `yaml:"tls_sni"`
				} `yaml:"tunnel"`
			}{
				GeoIP: struct {
					Enabled              bool     `yaml:"enabled"`
					DatabasePath         string   `yaml:"database_path"`
					DirectRouteCountries []string `yaml:"direct_route_countries"`
				}{
					Enabled:              true,
					DatabasePath:         "/tmp/GeoLite2-Country.mmdb", // будет заменен на реальный путь
					DirectRouteCountries: []string{"RU"},
				},
				Tunnel: struct {
					Enabled      bool   `yaml:"enabled"`
					RemoteServer string `yaml:"remote_server"`
					TLSSNI       string `yaml:"tls_sni"`
				}{
					Enabled:      true,
					RemoteServer: "your-vps.com:443",
					TLSSNI:       "cloudflare.com",
				},
			},
			Interceptor: struct {
				RedirectPorts []int  `yaml:"redirect_ports"`
				ExcludeSubnets []string `yaml:"exclude_subnets"`
			}{
				RedirectPorts: []int{80, 443},
				ExcludeSubnets: []string{"127.0.0.0/8", "192.168.0.0/16", "10.0.0.0/8"},
			},
		}
	}

	gw := &Gateway{
		config: cfg,
		engine: core.NewEngine(),
	}

	// Создание и регистрация шагов, если они включены
	if cfg.Steps.GeoIP.Enabled {
		geoStep, err := steps.NewGeoIPStep(cfg.Steps.GeoIP.DatabasePath, cfg.Steps.GeoIP.DirectRouteCountries)
		if err != nil {
			log.Printf("Failed to create GeoIP step: %v", err)
			return nil, err
		}
		gw.geoStep = geoStep
		gw.engine.RegisterStep(geoStep)
	}

	if cfg.Steps.Tunnel.Enabled {
		tunnelStep, err := steps.NewTunnelRouteStep(cfg.Steps.Tunnel.RemoteServer)
		if err != nil {
			log.Printf("Failed to create Tunnel step: %v", err)
			return nil, err
		}
		gw.tunnelStep = tunnelStep
		gw.engine.RegisterStep(tunnelStep)
	}

	// Создание перехватчика
	nfqInterceptor, err := interceptor.NewNFQueueInterceptor(gw.engine.EventChannel(), cfg.Interceptor)
	if err != nil {
		log.Printf("Failed to create interceptor: %v", err)
		return nil, err
	}
	gw.interceptor = nfqInterceptor

	return gw, nil
}

// Start запускает работу Gateway
func (gw *Gateway) Start() {
	// Настройка iptables (через interceptor.Setup())
	if err := interceptor.Setup(gw.config.Interceptor); err != nil {
		log.Printf("Warning: failed to setup iptables: %v", err)
		// Не завершаем программу, если не можем настроить iptables
	}

	// Запуск перехватчика
	go gw.interceptor.Start()

	// Запуск движка
	go gw.engine.Start()

	// Ожидание сигнала для завершения (Ctrl+C)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	log.Println("Shutting down Gateway...")
}

// Stop останавливает работу Gateway
func (gw *Gateway) Stop() {
	if gw.engine != nil {
		gw.engine.Stop()
	}

	// Очистка iptables
	interceptor.Cleanup()

	// Закрытие шагов
	if gw.geoStep != nil {
		gw.geoStep.Close()
	}
	if gw.tunnelStep != nil {
		gw.tunnelStep.Close()
	}
}