package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"xvpn-client-go/internal/state"
	"xvpn-client-go/internal/geoip"
	"xvpn-client-go/internal/api"
)

func main() {
	clientUUID := "test-client-uuid"
	serverURL := "https://localhost:8443" // Для разработки
	
	// Создаем машину состояний
	stateMachine := state.NewVPNStateMachine(clientUUID)
	
	// Создаем роутер трафика
	trafficRouter, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Fatalf("Ошибка инициализации роутера трафика: %v", err)
	}
	defer trafficRouter.Close()
	
	// Создаем API клиент
	apiClient := api.NewAPIClient(serverURL, clientUUID)
	
	// Проверяем здоровье сервера перед запуском
	if !apiClient.IsServerHealthy() {
		log.Printf("⚠️  Предупреждение: Сервер в состоянии %s", func() string {
			health, err := apiClient.HealthCheck()
			if err != nil {
				return "недоступен"
			}
			return health.Status
		}())
	}
	
	// Получаем конфигурацию клиента с сервера
	clientConfig, err := apiClient.GetClientConfig()
	if err != nil {
		log.Printf("⚠️  Предупреждение: Не удалось получить конфигурацию с сервера: %v", err)
		log.Printf("    Будет использована локальная конфигурация")
	} else {
		log.Printf("✅ Конфигурация успешно получена с сервера")
		// Здесь будет применение конфигурации к клиенту
	}
	
	// Запускаем машину состояний
	stateMachine.Start()
	
	log.Println("🚀 XVPN клиент запущен")
	log.Printf("🆔 UUID клиента: %s", clientUUID)
	log.Printf("🌐 Сервер API: %s", serverURL)
	
	// Создаем канал для получения сигналов
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	
	// Запускаем горутину для периодической проверки состояния сервера
	go func() {
		ticker := time.NewTicker(60 * time.Second) // Проверяем каждую минуту
		defer ticker.Stop()
		
		for {
			select {
			case <-ticker.C:
				if apiClient.IsServerHealthy() {
					// Получаем обновленную конфигурацию
					if clientConfig, err := apiClient.GetClientConfig(); err == nil {
						log.Printf("🔄 Конфигурация обновлена с сервера")
						// Здесь будет применение обновленной конфигурации
					}
				} else {
					log.Printf("⚠️  Сервер не отвечает или в состоянии degraded")
				}
			}
		}
	}()
	
	// Ожидаем сигнал завершения
	<-sigChan
	log.Println("🛑 Получен сигнал завершения")
	stateMachine.Stop()
	
	log.Println("✅ XVPN клиент остановлен")
}