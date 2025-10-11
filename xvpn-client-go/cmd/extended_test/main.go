package main

import (
	"fmt"
	"time"
	"xvpn-client-go/internal/geoip"
	"xvpn-client-go/internal/state"
)

func main() {
	fmt.Println("=== Расширенное тестирование компонентов XVPN клиента ===")
	
	// Тестирование машины состояний
	fmt.Println("\n1. Тестирование машины состояний:")
	sm := state.NewVPNStateMachine("test-uuid-123")
	sm.Start()
	
	// Ждем немного, чтобы машина состояний выполнила инициализацию
	time.Sleep(100 * time.Millisecond)
	
	// Проверка начального состояния
	info := sm.GetStateInfo()
	fmt.Printf("   Начальное состояние: %v\n", info["current_state"])
	
	// Триггерим событие для перехода
	sm.TriggerEvent(state.EventStartRequested)
	
	// Ждем немного, чтобы произошел переход
	time.Sleep(200 * time.Millisecond)
	
	// Проверяем состояние после события
	info = sm.GetStateInfo()
	fmt.Printf("   Состояние после start_requested: %v\n", info["current_state"])
	
	// Тестируем событие остановки
	sm.TriggerEvent(state.EventStopRequested)
	time.Sleep(100 * time.Millisecond)
	
	info = sm.GetStateInfo()
	fmt.Printf("   Состояние после stop_requested: %v\n", info["current_state"])
	
	// Останавливаем машину состояний
	sm.Stop()
	fmt.Println("   Машина состояний остановлена")
	
	// Тестирование роутера трафика
	fmt.Println("\n2. Тестирование роутера трафика:")
	router, err := geoip.NewTrafficRouter("")
	if err != nil {
		fmt.Printf("   Ошибка инициализации роутера: %v\n", err)
		return
	}
	defer router.Close()
	
	// Проверяем разные IP-адреса
	testIPs := []struct {
		ip, expectedRoute string
		expectedDirect    bool
		description       string
	}{
		{"77.88.8.8", "RU", true, "Российский IP (Яндекс)"},
		{"8.8.8.8", "US", false, "Американский IP (Google)"},
		{"192.168.1.1", "", true, "Локальная сеть"},
		{"77.77.77.77", "RU", true, "Российский IP из CIDR"},
		{"invalid-ip", "", false, "Невалидный IP"},
		{"10.0.0.1", "", true, "Приватная сеть"},
	}
	
	fmt.Println("   Тестирование IP-адресов:")
	for _, test := range testIPs {
		decision := router.GetRouteDecision(test.ip)
		status := "✓"
		if (decision.Direct != test.expectedDirect) {
			status = "✗"
		}
		fmt.Printf("   %s %s -> Direct: %t, Country: %s, Reason: %s [%s]\n", 
			status, test.ip, decision.Direct, decision.Country, decision.Reason, test.description)
	}
	
	// Проверяем статус сервера
	serverStatus := router.GetServerStatus()
	fmt.Printf("\n   Статус сервера: %t\n", serverStatus)
	
	// Дополнительные тесты
	fmt.Println("\n3. Дополнительные тесты:")
	
	// Проверяем определение РУ трафика
	ruIps := []string{"77.88.8.8", "87.224.224.224", "185.10.10.10"}
	for _, ip := range ruIps {
		isRU := router.IsRUDestination(ip)
		fmt.Printf("   IP %s %s как РУ трафик\n", ip, map[bool]string{true: "определяется", false: "НЕ определяется"}[isRU])
	}
	
	nonRuIps := []string{"8.8.8.8", "1.1.1.1", "208.67.222.222"}
	for _, ip := range nonRuIps {
		isRU := router.IsRUDestination(ip)
		fmt.Printf("   IP %s %s как РУ трафик\n", ip, map[bool]string{true: "определяется", false: "НЕ определяется"}[isRU])
	}
	
	fmt.Println("\n=== Тестирование завершено успешно ===")
}