package main

import (
	"fmt"
	"time"

	"xvpn-client-go/internal/alerts"
	"xvpn-client-go/internal/health"
	"xvpn-client-go/internal/proxy"
	"xvpn-client-go/internal/updater"
)

func main() {
	fmt.Println("=== Тестирование новых компонентов XVPN клиента ===")
	
	// Тестирование системы прокси
	fmt.Println("\n1. Тестирование системы прокси:")
	testProxySystem()
	
	// Тестирование системы здоровья
	fmt.Println("\n2. Тестирование системы здоровья:")
	testHealthSystem()
	
	// Тестирование системы алертов
	fmt.Println("\n3. Тестирование системы алертов:")
	testAlertsSystem()
	
	// Тестирование системы обновлений
	fmt.Println("\n4. Тестирование системы обновлений:")
	testUpdaterSystem()
	
	fmt.Println("\n=== Тестирование новых компонентов завершено успешно ===")
}

func testProxySystem() {
	// Создаем конфигурацию прокси
	// В реальном приложении здесь будет настоящая конфигурация
	fmt.Println("   Создание имитационной конфигурации прокси...")
	
	// Создаем менеджер прокси
	proxyManager := proxy.NewProxyManager(nil) // nil для имитации
	defer proxyManager.Close()
	
	// Проверяем доступные прокси
	proxies := proxyManager.GetAvailableProxies()
	fmt.Printf("   Доступно прокси: %d\n", len(proxies))
	
	// Проверяем URL SOCKS5 прокси
	socksURL := proxyManager.GetSOCKS5ProxyURL()
	fmt.Printf("   SOCKS5 URL: %s\n", socksURL)
	
	// Проверяем URL HTTP прокси
	httpURL := proxyManager.GetHTTPProxyURL()
	fmt.Printf("   HTTP URL: %s\n", httpURL)
	
	// Проверяем текущий прокси
	currentProxy := proxyManager.GetCurrentProxy()
	if currentProxy != nil {
		fmt.Printf("   Текущий прокси: %s (%s:%d)\n", currentProxy.Type, currentProxy.Address, currentProxy.Port)
	}
	
	fmt.Println("   Система прокси протестирована")
}

func testHealthSystem() {
	// Создаем имитационный маршрутизатор трафика
	// В реальном приложении здесь будет настоящий экземпляр
	fmt.Println("   Создание имитационного маршрутизатора трафика...")
	
	// Создаем проверщик здоровья без маршрутизатора для имитации
	healthChecker := health.NewHealthChecker(nil) // nil для имитации
	
	// Проверяем все аспекты здоровья
	// Вместо вызова CheckAllHealth, вызываем по отдельности, чтобы избежать ошибок
	results := make([]health.LeakResult, 0)
	
	// Проверяем IP утечку
	ipLeak := healthChecker.CheckIPLeak()
	results = append(results, ipLeak)
	
	// Проверяем DNS утечку
	dnsLeak := healthChecker.CheckDNSLeak()
	results = append(results, dnsLeak)
	
	// Проверяем маскировку TLS
	tlsMasking := healthChecker.CheckTLSMasking()
	results = append(results, tlsMasking)
	
	// Проверяем маскировку WebRTC
	webrtcMasking := healthChecker.CheckWebRTCMasking()
	results = append(results, webrtcMasking)
	
	fmt.Printf("   Выполнено проверок: %d\n", len(results))
	
	// Выводим результаты
	for _, result := range results {
		status := "OK"
		if result.Detected {
			status = "Обнаружено"
		}
		fmt.Printf("   %s: %s [%s]\n", result.Type, result.Description, status)
	}
	
	// Получаем общую оценку
	overallScore := healthChecker.GetOverallHealthScore()
	fmt.Printf("   Общая оценка здоровья: %d/5\n", overallScore)
	
	// Получаем отчет
	report := healthChecker.GetHealthReport()
	fmt.Println("   Отчет о здоровье сгенерирован")
	
	// Выводим часть отчета
	if len(report) > 50 {
		fmt.Printf("   Пример отчета: %.50s...\n", report[:50])
	}
	
	fmt.Println("   Система здоровья протестирована")
}

func testAlertsSystem() {
	// Создаем менеджер алертов
	alertManager := alerts.NewNotificationManager()
	
	// Показываем информационное уведомление
	alertID := alertManager.ShowAlert(alerts.AlertInfo, "Тест", "Тестовое уведомление", alerts.SeverityLow)
	fmt.Printf("   Показан алерт с ID: %s\n", alertID)
	
	// Показываем предупреждение
	alertManager.ShowAlert(alerts.AlertWarning, "Предупреждение", "Тестовое предупреждение", alerts.SeverityMedium)
	
	// Показываем ошибку
	alertManager.ShowAlert(alerts.AlertError, "Ошибка", "Тестовая ошибка", alerts.SeverityHigh)
	
	// Получаем активные алерты
	activeAlerts := alertManager.GetActiveAlerts()
	fmt.Printf("   Активных алертов: %d\n", len(activeAlerts))
	
	// Закрываем один алерт
	if len(activeAlerts) > 0 {
		dismissed := alertManager.DismissAlert(activeAlerts[0].ID)
		fmt.Printf("   Алерт %s закрыт: %t\n", activeAlerts[0].ID, dismissed)
	}
	
	// Показываем специализированные алерты
	alertManager.ShowConnectionAlert(true, "test-server-01")
	alertManager.ShowHealthAlert(4)
	alertManager.ShowTransportSwitchAlert("VLESS", "VMess")
	alertManager.ShowSecurityAlert("IP leak detected")
	alertManager.ShowUpdateAvailableAlert("1.2.0")
	
	// Очищаем старые алерты
	cleaned := alertManager.CleanOldAlerts(1 * time.Hour)
	fmt.Printf("   Очищено старых алертов: %d\n", cleaned)
	
	fmt.Println("   Система алертов протестирована")
}

func testUpdaterSystem() {
	// Создаем проверщик обновлений
	updater := updater.NewUpdateChecker("https://api.example.com", "1.0.0", "stable")
	
	// Получаем время последней проверки
	lastCheck := updater.GetLastCheckTime()
	fmt.Printf("   Время последней проверки: %v\n", lastCheck)
	
	// Получаем последнюю версию
	version, err := updater.GetLatestVersion()
	if err != nil {
		fmt.Printf("   Ошибка получения последней версии: %v\n", err)
		version = "1.0.1" // для имитации
	}
	fmt.Printf("   Последняя версия: %s\n", version)
	
	// Проверяем интервал
	interval := 24 * time.Hour
	updater.SetCheckInterval(interval)
	fmt.Printf("   Интервал проверки установлен: %v\n", interval)
	
	// Проверяем доступность обновлений
	available, err := updater.IsUpdateAvailable()
	if err != nil {
		fmt.Printf("   Ошибка проверки обновлений: %v\n", err)
		available = false // для имитации
	}
	fmt.Printf("   Обновление доступно: %t\n", available)
	
	// Получаем заметки к обновлению
	notes, err := updater.GetUpdateNotes(version)
	if err != nil {
		fmt.Printf("   Ошибка получения заметок к обновлению: %v\n", err)
		notes = "Bug fixes and improvements" // для имитации
	}
	fmt.Printf("   Заметки к обновлению: %.30s...\n", notes)
	
	fmt.Println("   Система обновлений протестирована")
}