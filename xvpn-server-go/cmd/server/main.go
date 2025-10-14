package main

import (
	"context"
	"crypto/tls"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"xvpn-server-go/internal/api"
	"xvpn-server-go/internal/config"
	"xvpn-server-go/internal/database"
	"xvpn-server-go/internal/gateway"
	"xvpn-server-go/internal/telegram"
)

func main() {
	// Загрузка конфигурации
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Ошибка загрузки конфигурации: %v", err)
	}

	// Инициализация базы данных
	db, err := database.New(cfg.Database)
	if err != nil {
		log.Fatalf("Ошибка инициализации базы данных: %v", err)
	}
	defer db.Close()

	// Инициализация Telegram бота
	tgBot, err := telegram.NewBot(cfg.Telegram.Token, cfg.Telegram.ChatID, db)
	if err != nil {
		log.Fatalf("Ошибка инициализации Telegram бота: %v", err)
	}

	// Инициализация API сервера
	apiServer := api.NewServer(cfg.API, db, tgBot)

	// Инициализация Gateway
	gw := gateway.New(cfg.Gateway, db, tgBot)

	// Настройка TLS
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{loadTLSCertificate(cfg.TLS)},
		MinVersion:   tls.VersionTLS12,
	}

	// Создание HTTP сервера с TLS
	server := &http.Server{
		Addr:      fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:   setupRoutes(apiServer, gw),
		TLSConfig: tlsConfig,
	}

	// Запуск сервера в горутине
	go func() {
		log.Printf("🚀 XVPN сервер запущен на порту %d", cfg.Server.Port)
		if err := server.ListenAndServeTLS("", ""); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Ошибка запуска сервера: %v", err)
		}
	}()

	// Запуск Telegram бота
	go func() {
		if err := tgBot.Start(); err != nil {
			log.Printf("Ошибка запуска Telegram бота: %v", err)
		}
	}()

	// Ожидание сигнала завершения
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("🛑 Получен сигнал завершения, останавливаем сервер...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Printf("Ошибка при остановке сервера: %v", err)
	}

	log.Println("✅ XVPN сервер остановлен")
}

func setupRoutes(apiServer *api.Server, gw *gateway.Gateway) http.Handler {
	mux := http.NewServeMux()

	// API маршруты
	mux.Handle("/api/v1/", http.StripPrefix("/api/v1", apiServer.Router()))

	// Gateway маршруты
	mux.Handle("/gateway/", http.StripPrefix("/gateway", gw.Router()))

	// Health check
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	return mux
}

func loadTLSCertificate(tlsCfg config.TLSConfig) tls.Certificate {
	cert, err := tls.LoadX509KeyPair(tlsCfg.CertFile, tlsCfg.KeyFile)
	if err != nil {
		log.Fatalf("Ошибка загрузки TLS сертификата: %v", err)
	}
	return cert
}
