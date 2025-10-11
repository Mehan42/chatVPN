package main

import (
	"fmt"
	"log"
	"runtime"
	"time"

	"xvpn-client-go/internal/geoip"
	"xvpn-client-go/internal/state"
)

func main() {
	fmt.Println("=== Профилирование производительности XVPN клиента ===")
	
	// Тест 1: Анализ использования памяти
	fmt.Println("\n1. Тестирование использования памяти:")
	testMemoryUsage()
	
	// Тест 2: Анализ производительности машины состояний
	fmt.Println("\n2. Тестирование производительности машины состояний:")
	testStateMachinePerformance()
	
	// Тест 3: Анализ производительности роутера трафика
	fmt.Println("\n3. Тестирование производительности роутера трафика:")
	testTrafficRouterPerformance()
	
	// Тест 4: Анализ времени запуска
	fmt.Println("\n4. Тестирование времени запуска:")
	testStartupTime()
	
	fmt.Println("\n=== Профилирование завершено ===")
}

func testMemoryUsage() {
	// Получаем начальные метрики памяти
	var m1, m2 runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&m1)
	
	// Создаем несколько экземпляров компонентов
	stateMachines := make([]*state.VPNStateMachine, 100)
	for i := 0; i < 100; i++ {
		stateMachines[i] = state.NewVPNStateMachine(fmt.Sprintf("test-client-%d", i))
	}
	
	// Создаем роутеры трафика
	routers := make([]*geoip.TrafficRouter, 50)
	for i := 0; i < 50; i++ {
		router, err := geoip.NewTrafficRouter("")
		if err == nil {
			routers[i] = router
		}
	}
	
	// Получаем метрики после создания объектов
	runtime.GC()
	runtime.ReadMemStats(&m2)
	
	// Выводим результаты
	fmt.Printf("   Выделено памяти для 100 машин состояний: %d KB\n", (m2.Alloc-m1.Alloc)/1024)
	fmt.Printf("   Общее выделение памяти: %d KB\n", m2.Alloc/1024)
	fmt.Printf("   Количество GC циклов: %d\n", m2.NumGC-m1.NumGC)
	
	// Освобождаем ресурсы
	for i := range routers {
		if routers[i] != nil {
			routers[i].Close()
		}
	}
	
	// Получаем финальные метрики
	runtime.GC()
	var m3 runtime.MemStats
	runtime.ReadMemStats(&m3)
	fmt.Printf("   Память после освобождения: %d KB\n", m3.Alloc/1024)
	fmt.Printf("   ✅ Тест использования памяти завершен")
}

func testStateMachinePerformance() {
	// Создаем машину состояний для тестирования
	sm := state.NewVPNStateMachine("perf-test-client")
	
	// Измеряем время выполнения операций
	start := time.Now()
	
	// Выполняем 1000 переходов между состояниями
	for i := 0; i < 1000; i++ {
		// Имитируем переходы между состояниями
		sm.TriggerEvent(state.EventStartRequested)
		time.Sleep(1 * time.Millisecond) // Небольшая задержка для реалистичности
		sm.TriggerEvent(state.EventStopRequested)
	}
	
	duration := time.Since(start)
	
	fmt.Printf("   Время выполнения 1000 переходов: %v\n", duration)
	fmt.Printf("   Среднее время одного перехода: %v\n", duration/1000)
	fmt.Printf("   Производительность: %.0f переходов/сек\n", float64(1000)/duration.Seconds())
	fmt.Printf("   ✅ Тест производительности машины состояний завершен")
}

func testTrafficRouterPerformance() {
	// Создаем роутер трафика для тестирования
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Printf("   ❌ Ошибка создания роутера: %v", err)
		return
	}
	defer router.Close()
	
	// Тестовые IP-адреса
	testIPs := []string{
		"77.88.8.8",    // Яндекс (РУ)
		"8.8.8.8",      // Google (неРУ)
		"192.168.1.1",  // Локальная сеть
		"176.192.1.1",  // РУ диапазон
		"208.67.222.222", // OpenDNS (неРУ)
		"185.10.10.10", // РУ диапазон
	}
	
	// Измеряем время выполнения операций
	start := time.Now()
	
	// Выполняем 10000 проверок маршрутизации
	for i := 0; i < 10000; i++ {
		ip := testIPs[i%len(testIPs)]
		router.GetRouteDecision(ip)
	}
	
	duration := time.Since(start)
	
	fmt.Printf("   Время выполнения 10000 проверок маршрутизации: %v\n", duration)
	fmt.Printf("   Среднее время одной проверки: %v\n", duration/10000)
	fmt.Printf("   Производительность: %.0f проверок/сек\n", float64(10000)/duration.Seconds())
	
	// Тестируем определенные IP-адреса
	fmt.Println("   Тестирование конкретных IP:")
	for _, ip := range testIPs {
		start := time.Now()
		decision := router.GetRouteDecision(ip)
		duration := time.Since(start)
		fmt.Printf("     %s -> Direct: %t (%v)\n", ip, decision.Direct, duration)
	}
	
	fmt.Printf("   ✅ Тест производительности роутера трафика завершен")
}

func testStartupTime() {
	// Измеряем время запуска приложения
	start := time.Now()
	
	// Создаем основные компоненты приложения
	sm := state.NewVPNStateMachine("startup-test-client")
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Printf("   ❌ Ошибка создания роутера: %v", err)
		return
	}
	defer router.Close()
	
	// Запускаем машину состояний
	sm.Start()
	
	duration := time.Since(start)
	
	fmt.Printf("   Время инициализации компонентов: %v\n", duration)
	
	// Измеряем время первого запуска машины состояний
	start = time.Now()
	sm.TriggerEvent(state.EventStartRequested)
	time.Sleep(100 * time.Millisecond) // Даем время для обработки
	firstEventDuration := time.Since(start)
	
	fmt.Printf("   Время первого события: %v\n", firstEventDuration)
	
	// Останавливаем машину состояний
	sm.Stop()
	
	fmt.Printf("   ✅ Тест времени запуска завершен")
}

// Дополнительные тесты производительности

func testConcurrentAccess() {
	fmt.Println("\n5. Тестирование конкурентного доступа:")
	
	// Создаем роутер трафика
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Printf("   ❌ Ошибка создания роутера: %v", err)
		return
	}
	defer router.Close()
	
	// Запускаем несколько горутин для конкурентного доступа
	concurrentRequests := 1000
	results := make(chan bool, concurrentRequests)
	
	start := time.Now()
	
	// Запускаем горутины
	for i := 0; i < concurrentRequests; i++ {
		go func(ip string) {
			decision := router.GetRouteDecision(ip)
			results <- decision.Direct
		}(fmt.Sprintf("192.168.%d.%d", i/256, i%256))
	}
	
	// Собираем результаты
	directCount := 0
	for i := 0; i < concurrentRequests; i++ {
		if <-results {
			directCount++
		}
	}
	
	duration := time.Since(start)
	
	fmt.Printf("   Обработано %d конкурентных запросов за %v\n", concurrentRequests, duration)
	fmt.Printf("   Среднее время на запрос: %v\n", duration/time.Duration(concurrentRequests))
	fmt.Printf("   Производительность: %.0f запросов/сек\n", float64(concurrentRequests)/duration.Seconds())
	fmt.Printf("   Прямых маршрутов: %d\n", directCount)
	fmt.Printf("   ✅ Тест конкурентного доступа завершен")
}

func testCachePerformance() {
	fmt.Println("\n6. Тестирование производительности кэширования:")
	
	// Создаем роутер трафика
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Printf("   ❌ Ошибка создания роутера: %v", err)
		return
	}
	defer router.Close()
	
	// Тестовый IP для кэширования
	testIP := "77.88.8.8"
	
	// Первый запрос (без кэша)
	start := time.Now()
	firstDecision := router.GetRouteDecision(testIP)
	firstDuration := time.Since(start)
	
	// Второй запрос (с кэшем)
	start = time.Now()
	secondDecision := router.GetRouteDecision(testIP)
	secondDuration := time.Since(start)
	
	fmt.Printf("   Первый запрос (без кэша): %v\n", firstDuration)
	fmt.Printf("   Второй запрос (с кэшем): %v\n", secondDuration)
	fmt.Printf("   Ускорение: %.2fx\n", float64(firstDuration)/float64(secondDuration))
	fmt.Printf("   Результаты идентичны: %t\n", firstDecision.Direct == secondDecision.Direct)
	
	fmt.Printf("   ✅ Тест производительности кэширования завершен")
}

func testLargeDatasetPerformance() {
	fmt.Println("\n7. Тестирование с большими наборами данных:")
	
	// Создаем роутер трафика
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		log.Printf("   ❌ Ошибка создания роутера: %v", err)
		return
	}
	defer router.Close()
	
	// Генерируем большой набор тестовых данных
	largeIPSet := make([]string, 10000)
	for i := 0; i < 10000; i++ {
		largeIPSet[i] = fmt.Sprintf("192.168.%d.%d", i/256, i%256)
	}
	
	// Измеряем время обработки большого набора данных
	start := time.Now()
	
	directRoutes := 0
	for _, ip := range largeIPSet {
		decision := router.GetRouteDecision(ip)
		if decision.Direct {
			directRoutes++
		}
	}
	
	duration := time.Since(start)
	
	fmt.Printf("   Обработано 10000 IP-адресов за %v\n", duration)
	fmt.Printf("   Среднее время на IP: %v\n", duration/10000)
	fmt.Printf("   Прямых маршрутов: %d\n", directRoutes)
	fmt.Printf("   Производительность: %.0f IP/сек\n", float64(10000)/duration.Seconds())
	
	fmt.Printf("   ✅ Тест с большими наборами данных завершен")
}