package main

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

func main() {
	// 1. Загрузка конфигурации
	cfg, err := config.Load("config.yaml")
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

	// 2. Настройка iptables (через interceptor.Setup())
	if err := interceptor.Setup(cfg.Interceptor); err != nil {
		log.Printf("Warning: failed to setup iptables: %v", err)
		// Не завершаем программу, если не можем настроить iptables
	}
	defer interceptor.Cleanup() // Гарантированная очистка при выходе

	// 3. Создание движка
	engine := core.NewEngine()

	// 4. Создание и регистрация Шагов
	if cfg.Steps.GeoIP.Enabled {
		geoStep, err := steps.NewGeoIPStep(cfg.Steps.GeoIP.DatabasePath, cfg.Steps.GeoIP.DirectRouteCountries)
		if err != nil {
			log.Printf("Failed to create GeoIP step: %v", err)
			// Если не можем создать GeoIP шаг, используем заглушку
		} else {
			defer geoStep.Close()
			engine.RegisterStep(geoStep)
		}
	}

	if cfg.Steps.Tunnel.Enabled {
		tunnelStep, err := steps.NewTunnelRouteStep(cfg.Steps.Tunnel.RemoteServer)
		if err != nil {
			log.Printf("Failed to create Tunnel step: %v", err)
		} else {
			defer tunnelStep.Close()
			engine.RegisterStep(tunnelStep)
		}
	}

	// ... другие шаги ...

	// 5. Запуск перехватчика
	nfqInterceptor, err := interceptor.NewNFQueueInterceptor(engine.EventChannel(), cfg.Interceptor)
	if err != nil {
		log.Printf("Failed to create interceptor: %v", err)
	} else {
		go nfqInterceptor.Start() // Запускаем в отдельной горутине
	}

	// 6. Запуск движка
	go engine.Start()

	// Ожидание сигнала для завершения (Ctrl+C)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	log.Println("Shutting down...")
	
	// Остановка движка
	engine.Stop()
}