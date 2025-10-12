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
	_ "xvpn-client-go/internal/tunnelverifier"
)

func main() {
	clientUUID := "4176be2c-5368-4a7b-af50-456f4cc0ca89"
	serverURL := "https://uss.hopto.org:8443" // Для разработки
	
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
		// Применяем конфигурацию к клиенту - обновляем транспорты в машине состояний
		if clientConfig != nil {
			// Преобразуем транспорты из config в формат state машины
			var transports []state.Transport
			for _, transport := range clientConfig.Transports {
				transports = append(transports, state.Transport{
					ID:       transport.ID,
					Name:     transport.Name,
					Type:     transport.Type,
					Priority: transport.Priority,
					IPv6:     transport.IPv6,
					NeedUDP:  transport.NeedUDP,
					Config:   transport.Config,
				})
			}
			
			// Обновляем конфигурацию машины состояний
			stateMachine.UpdateConfig(transports)
			
			// Триггерим событие получения конфигурации
			stateMachine.TriggerEvent(state.EventConfigFetched)
		}
	}
	
	// Создаем обработчик проверки туннелирования
	tunnelHandler, err := state.NewTunnelVerifierStateHandler(stateMachine)
	if err != nil {
		log.Printf("⚠️  Предупреждение: Не удалось создать обработчик проверки туннелирования: %v", err)
	} else {
		// Интегрируем обработчик с машиной состояний
		tunnelHandler.IntegrateWithStateMachine()
		log.Printf("✅ Обработчик проверки туннелирования интегрирован")
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
					if updatedConfig, err := apiClient.GetClientConfig(); err == nil {
						log.Printf("🔄 Конфигурация обновлена с сервера")
						// Применяем обновленную конфигурацию
						if updatedConfig != nil {
							// Преобразуем транспорты из updatedConfig в формат state машины
							var transports []state.Transport
							for _, transport := range updatedConfig.Transports {
								transports = append(transports, state.Transport{
									ID:       transport.ID,
									Name:     transport.Name,
									Type:     transport.Type,
									Priority: transport.Priority,
									IPv6:     transport.IPv6,
									NeedUDP:  transport.NeedUDP,
									Config:   transport.Config,
								})
							}
							
							// Обновляем конфигурацию машины состояний
							stateMachine.UpdateConfig(transports)
							
							// Событие обновления конфигурации
							stateMachine.TriggerEvent(state.EventUpdateAvailable)
						}
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