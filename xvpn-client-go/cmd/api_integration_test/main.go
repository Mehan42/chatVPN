package main

import (
	"fmt"
	"log"
	"time"

	"xvpn-client-go/internal/api"
)

func main() {
	fmt.Println("=== Тестирование интеграции с XVPN API ===")
	
	// Создаем API клиент
	serverURL := "https://localhost:8443"
	clientUUID := "test-client-uuid"
	
	apiClient := api.NewAPIClient(serverURL, clientUUID)
	
	// Тест 1: Проверка состояния сервера
	fmt.Println("\n1. Тестирование проверки состояния сервера:")
	testServerHealth(apiClient)
	
	// Тест 2: Получение манифеста транспортов
	fmt.Println("\n2. Тестирование получения манифеста транспортов:")
	testTransportManifest(apiClient)
	
	// Тест 3: Получение конфигурации клиента
	fmt.Println("\n3. Тестирование получения конфигурации клиента:")
	testClientConfig(apiClient)
	
	// Тест 4: Регистрация клиента на сервере (для администраторов)
	fmt.Println("\n4. Тестирование регистрации клиента на сервере:")
	testRegisterClientOnServer(apiClient)
	
	// Тест 5: Периодическая проверка состояния
	fmt.Println("\n5. Тестирование периодической проверки состояния:")
	testPeriodicHealthCheck(apiClient)
	
	// Тест 6: Получение версии и оценки маскировки
	fmt.Println("\n6. Тестирование получения версии и оценки маскировки:")
	testVersionAndMaskScore(apiClient)
	
	fmt.Println("\n=== Тестирование интеграции завершено ===")
}

func testServerHealth(apiClient *api.APIClient) {
	// Проверяем здоровье сервера
	health, err := apiClient.HealthCheck()
	if err != nil {
		log.Printf("   ❌ Ошибка проверки состояния сервера: %v", err)
		return
	}
	
	fmt.Printf("   Статус сервера: %s\n", health.Status)
	fmt.Printf("   Версия сервера: %s\n", health.Version)
	fmt.Printf("   Оценка маскировки: %d/5\n", health.MaskScore)
	
	// Проверяем системные метрики
	if metrics, ok := health.SystemMetrics["cpu_percent"]; ok {
		fmt.Printf("   Загрузка CPU: %.1f%%\n", metrics.(float64))
	}
	
	if metrics, ok := health.SystemMetrics["memory_percent"]; ok {
		fmt.Printf("   Использование памяти: %.1f%%\n", metrics.(float64))
	}
	
	// Проверяем статус сервисов
	fmt.Println("   Статус сервисов:")
	for service, status := range health.Services {
		statusStr := "❌"
		if status {
			statusStr = "✅"
		}
		fmt.Printf("     %s %s\n", statusStr, service)
	}
	
	fmt.Println("   ✅ Проверка состояния сервера завершена")
}

func testTransportManifest(apiClient *api.APIClient) {
	// Получаем манифест транспортов
	manifest, err := apiClient.GetTransportManifest()
	if err != nil {
		log.Printf("   ❌ Ошибка получения манифеста транспортов: %v", err)
		return
	}
	
	fmt.Printf("   Версия манифеста: %d\n", manifest.Version)
	fmt.Printf("   Доступно транспортов: %d\n", len(manifest.Transports))
	
	// Выводим информацию о каждом транспорте
	for i, transport := range manifest.Transports {
		fmt.Printf("   Транспорт %d: %s (%s)\n", i+1, transport.Name, transport.Type)
		fmt.Printf("     Приоритет: %d\n", transport.Priority)
		fmt.Printf("     Поддержка IPv6: %t\n", transport.IPv6)
		fmt.Printf("     Требуется UDP: %t\n", transport.NeedUDP)
		fmt.Printf("     Трафик РУ: %t\n", transport.RUTraffic)
		fmt.Printf("     Трафик неРУ: %t\n", transport.NonRUTraffic)
		
		// Выводим конфигурацию
		if len(transport.Config) > 0 {
			fmt.Printf("     Конфигурация: %d параметров\n", len(transport.Config))
		}
		
		if i >= 2 { // Ограничиваем вывод первыми 3 транспортами
			fmt.Printf("     ...\n")
			break
		}
		fmt.Println()
	}
	
	fmt.Println("   ✅ Получение манифеста транспортов завершено")
}

func testClientConfig(apiClient *api.APIClient) {
	// Получаем конфигурацию клиента
	config, err := apiClient.GetClientConfig()
	if err != nil {
		log.Printf("   ❌ Ошибка получения конфигурации клиента: %v", err)
		return
	}
	
	fmt.Printf("   UUID клиента: %s\n", config.UUID)
	fmt.Printf("   Количество транспортов в конфигурации: %d\n", len(config.Transports))
	fmt.Printf("   Количество правил маршрутизации: %d\n", len(config.RoutingRules))
	
	// Проверяем настройки сервера
	fmt.Printf("   Endpoint API сервера: %s\n", config.ServerConfig.APIEndpoint)
	fmt.Printf("   URL манифеста: %s\n", config.ServerConfig.ManifestURL)
	
	// Проверяем опции клиента
	fmt.Printf("   Автоподключение: %t\n", config.ClientOptions.AutoConnect)
	fmt.Printf("   Автоматическое переключение: %t\n", config.ClientOptions.AutoSwitch)
	
	fmt.Println("   ✅ Получение конфигурации клиента завершено")
}

func testRegisterClientOnServer(apiClient *api.APIClient) {
	// Регистрируем клиента на сервере (для администраторов)
	newUUID, err := apiClient.RegisterClientOnServer()
	if err != nil {
		log.Printf("   ❌ Ошибка регистрации клиента на сервере: %v", err)
		// Это нормально, если у нас нет прав администратора
		fmt.Println("   ℹ️  Регистрация клиента доступна только администраторам")
		return
	}
	
	fmt.Printf("   Новый UUID клиента: %s\n", newUUID)
	
	// Устанавливаем новый UUID
	apiClient.SetClientUUID(newUUID)
	
	// Проверяем, что UUID установлен правильно
	if apiClient.GetClientUUID() == newUUID {
		fmt.Println("   ✅ UUID клиента успешно установлен")
	} else {
		fmt.Println("   ❌ Ошибка установки UUID клиента")
	}
	
	fmt.Println("   ✅ Регистрация клиента на сервере завершена")
}

// Дополнительные тесты

func testPeriodicHealthCheck(apiClient *api.APIClient) {
	fmt.Println("\n5. Тестирование периодической проверки состояния:")
	
	// Проверяем здоровье сервера несколько раз с интервалом
	for i := 0; i < 3; i++ {
		fmt.Printf("   Проверка #%d: ", i+1)
		
		if apiClient.IsServerHealthy() {
			health, _ := apiClient.HealthCheck()
			fmt.Printf("здоров (%s)\n", health.Status)
		} else {
			fmt.Println("нездоров")
		}
		
		if i < 2 { // Ждем перед следующей проверкой
			time.Sleep(1 * time.Second)
		}
	}
	
	fmt.Println("   ✅ Периодическая проверка состояния завершена")
}

func testVersionAndMaskScore(apiClient *api.APIClient) {
	fmt.Println("\n6. Тестирование получения версии и оценки маскировки:")
	
	// Получаем версию сервера
	version, err := apiClient.GetServerVersion()
	if err != nil {
		log.Printf("   ❌ Ошибка получения версии сервера: %v", err)
	} else {
		fmt.Printf("   Версия сервера: %s\n", version)
	}
	
	// Получаем оценку маскировки
	maskScore, err := apiClient.GetMaskScore()
	if err != nil {
		log.Printf("   ❌ Ошибка получения оценки маскировки: %v", err)
	} else {
		fmt.Printf("   Оценка маскировки: %d/5\n", maskScore)
		status := "❌"
		switch {
		case maskScore >= 4:
			status = "✅"
		case maskScore >= 3:
			status = "⚠️"
		}
		fmt.Printf("   Статус маскировки: %s\n", status)
	}
	
	fmt.Println("   ✅ Получение версии и оценки маскировки завершено")
}