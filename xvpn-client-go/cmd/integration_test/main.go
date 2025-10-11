package main

import (
	"fmt"
	"log"
	"time"

	"xvpn-client-go/internal/config"
	"xvpn-client-go/internal/logging"
	"xvpn-client-go/internal/transport"
)

func main() {
	fmt.Println("=== Тестирование новых компонентов XVPN клиента ===")
	
	// Тестирование системы логирования
	fmt.Println("\n1. Тестирование системы логирования:")
	logger := logging.NewLogger("./logs", true)
	logger.Info("TestApp", "Система логирования инициализирована")
	logger.Debug("TestApp", "Отладочное сообщение")
	logger.Warn("TestApp", "Предупреждение")
	logger.Error("TestApp", "Сообщение об ошибке")
	
	// Тестирование менеджера транспортов
	fmt.Println("\n2. Тестирование менеджера транспортов:")
	transportManager := transport.NewTransportManager()
	
	// Добавляем фиктивные транспорты
	transportManager.DiscoverTransports("")
	
	// Проверяем доступные транспорты
	transports := transportManager.GetAvailableTransports()
	fmt.Printf("   Доступно транспортов: %d\n", len(transports))
	
	for i, t := range transports {
		fmt.Printf("   Транспорт %d: %s (Приоритет: %d, Тип: %s)\n", i+1, t.Name, t.Priority, t.Type)
	}
	
	// Проверяем выбор лучшего транспорта для РУ трафика
	bestRUTransport := transportManager.GetBestTransportForTraffic(true)
	if bestRUTransport != nil {
		fmt.Printf("   Лучший транспорт для РУ трафика: %s\n", bestRUTransport.Name)
	} else {
		fmt.Println("   Не найден транспорт для РУ трафика")
	}
	
	// Проверяем выбор лучшего транспорта для неРУ трафика
	bestNonRUTransport := transportManager.GetBestTransportForTraffic(false)
	if bestNonRUTransport != nil {
		fmt.Printf("   Лучший транспорт для неРУ трафика: %s\n", bestNonRUTransport.Name)
	} else {
		fmt.Println("   Не найден транспорт для неРУ трафика")
	}
	
	// Запускаем цикл проверки здоровья в отдельной горутине
	go transportManager.StartHealthCheckLoop()
	
	// Ждем немного для проверки здоровья
	time.Sleep(100 * time.Millisecond)
	
	// Проверяем здоровые транспорты
	healthyTransports := transportManager.GetHealthyTransports()
	fmt.Printf("   Здоровых транспортов: %d\n", len(healthyTransports))
	
	// Тестирование менеджера конфигурации
	fmt.Println("\n3. Тестирование менеджера конфигурации:")
	configManager := config.NewConfigManager("./test_config.json")
	
	// Загружаем конфигурацию (создаст файл с дефолтной конфигурацией)
	err := configManager.LoadConfig()
	if err != nil {
		log.Printf("Ошибка загрузки конфигурации: %v", err)
	}
	
	// Проверяем основные параметры конфигурации
	clientConfig := configManager.GetConfig()
	fmt.Printf("   UUID клиента: %s\n", clientConfig.UUID)
	fmt.Printf("   Автоподключение: %t\n", configManager.IsAutoConnect())
	fmt.Printf("   Автообновление: %t\n", clientConfig.ClientOptions.AutoUpdate)
	fmt.Printf("   Поддержка IPv6: %t\n", clientConfig.ServerConfig.IPV6Support)
	fmt.Printf("   Количество РУ стран: %d\n", len(clientConfig.GeoIPSettings.RUCountries))
	
	// Устанавливаем новый UUID
	configManager.SetClientUUID("test-uuid-12345")
	fmt.Printf("   Новый UUID: %s\n", configManager.GetClientUUID())
	
	// Добавляем транспорт
	newTransport := config.TransportConfig{
		ID:       "test-transport",
		Name:     "Test Transport",
		Type:     "vless",
		Priority: 10,
		IPv6:     true,
		NeedUDP:  false,
		Enabled:  true,
	}
	configManager.AddTransport(newTransport)
	
	// Проверяем добавленный транспорт
	transport := configManager.GetTransportByID("test-transport")
	if transport != nil {
		fmt.Printf("   Добавлен транспорт: %s\n", transport.Name)
	}
	
	// Проверяем серверный endpoint
	fmt.Printf("   Endpoint сервера: %s\n", configManager.GetServerEndpoint())
	
	fmt.Println("\n=== Тестирование новых компонентов завершено успешно ===")
}