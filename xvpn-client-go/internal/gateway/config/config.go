package config

import (
	"gopkg.in/yaml.v3"
	"os"
)

// Config - основная конфигурация Gateway
type Config struct {
	Gateway struct {
		LogLevel string `yaml:"log_level"`
	} `yaml:"gateway"`
	
	Steps struct {
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
	} `yaml:"steps"`
	
	Interceptor struct {
		RedirectPorts []int  `yaml:"redirect_ports"`
		ExcludeSubnets []string `yaml:"exclude_subnets"`
	} `yaml:"interceptor"`
}

// Load загружает конфигурацию из YAML-файла
func Load(configPath string) (*Config, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}
	
	var cfg Config
	err = yaml.Unmarshal(data, &cfg)
	if err != nil {
		return nil, err
	}
	
	return &cfg, nil
}