package config

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config представляет основную конфигурацию сервера
type Config struct {
	Server   ServerConfig   `json:"server"`
	API      APIConfig      `json:"api"`
	Gateway  GatewayConfig  `json:"gateway"`
	Database DatabaseConfig `json:"database"`
	Telegram TelegramConfig `json:"telegram"`
	TLS      TLSConfig      `json:"tls"`
}

// ServerConfig конфигурация основного сервера
type ServerConfig struct {
	Port int `json:"port"`
}

// APIConfig конфигурация API сервера
type APIConfig struct {
	Port     int    `json:"port"`
	BasePath string `json:"base_path"`
}

// GatewayConfig конфигурация Gateway
type GatewayConfig struct {
	Port     int    `json:"port"`
	BasePath string `json:"base_path"`
}

// DatabaseConfig конфигурация базы данных
type DatabaseConfig struct {
	Path string `json:"path"`
}

// TelegramConfig конфигурация Telegram бота
type TelegramConfig struct {
	Token  string `json:"token"`
	ChatID string `json:"chat_id"`
}

// TLSConfig конфигурация TLS
type TLSConfig struct {
	CertFile string `json:"cert_file"`
	KeyFile  string `json:"key_file"`
}

// Load загружает конфигурацию из файла или переменных окружения
func Load() (*Config, error) {
	config := &Config{
		Server: ServerConfig{
			Port: 8443,
		},
		API: APIConfig{
			Port:     8443,
			BasePath: "/api/v1",
		},
		Gateway: GatewayConfig{
			Port:     8443,
			BasePath: "/gateway",
		},
		Database: DatabaseConfig{
			Path: "/opt/xvpn/data/xvpn.db",
		},
		Telegram: TelegramConfig{
			Token:  os.Getenv("TELEGRAM_BOT_TOKEN"),
			ChatID: os.Getenv("TELEGRAM_CHAT_ID"),
		},
		TLS: TLSConfig{
			CertFile: "/opt/xvpn/tls/server.crt",
			KeyFile:  "/opt/xvpn/tls/server.key",
		},
	}

	// Попытка загрузки из файла конфигурации
	if configFile := os.Getenv("XVPN_CONFIG_FILE"); configFile != "" {
		if err := loadFromFile(configFile, config); err != nil {
			return nil, fmt.Errorf("ошибка загрузки конфигурации из файла: %w", err)
		}
	}

	// Переопределение из переменных окружения
	loadFromEnv(config)

	return config, nil
}

// loadFromFile загружает конфигурацию из JSON файла
func loadFromFile(filename string, config *Config) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	decoder := json.NewDecoder(file)
	return decoder.Decode(config)
}

// loadFromEnv загружает конфигурацию из переменных окружения
func loadFromEnv(config *Config) {
	if port := os.Getenv("XVPN_SERVER_PORT"); port != "" {
		fmt.Sscanf(port, "%d", &config.Server.Port)
	}

	if dbPath := os.Getenv("XVPN_DATABASE_PATH"); dbPath != "" {
		config.Database.Path = dbPath
	}

	if token := os.Getenv("TELEGRAM_BOT_TOKEN"); token != "" {
		config.Telegram.Token = token
	}

	if chatID := os.Getenv("TELEGRAM_CHAT_ID"); chatID != "" {
		config.Telegram.ChatID = chatID
	}

	if certFile := os.Getenv("XVPN_TLS_CERT"); certFile != "" {
		config.TLS.CertFile = certFile
	}

	if keyFile := os.Getenv("XVPN_TLS_KEY"); keyFile != "" {
		config.TLS.KeyFile = keyFile
	}
}
