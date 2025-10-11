package main

import (
	"fmt"
	"xvpn-client-go/internal/geoip"
	"xvpn-client-go/internal/state"
)

func main() {
	fmt.Println("Тестирование компонентов XVPN клиента...")
	
	// Тестирование машины состояний
	fmt.Println("\n1. Тестирование машины состояний:")
	sm := state.NewVPNStateMachine("test-uuid-123")
	sm.Start()
	
	// Проверка начального состояния
	info := sm.GetStateInfo()
	fmt.Printf("   Начальное состояние: %v\n", info["current_state"])
	
	// Триггерим событие для перехода
	sm.TriggerEvent(state.EventStartRequested)
	
	// Проверяем состояние после события
	info = sm.GetStateInfo()
	fmt.Printf("   Состояние после start_requested: %v\n", info["current_state"])
	
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
	testIPs := []string{
		"77.88.8.8",   // Яндекс, РУ
		"8.8.8.8",     // Google, не РУ
		"192.168.1.1", // Локальная сеть
		"invalid-ip",  // Невалидный IP
	}
	
	for _, ip := range testIPs {
		decision := router.GetRouteDecision(ip)
		fmt.Printf("   IP: %s -> Direct: %t, Country: %s, Reason: %s\n", 
			ip, decision.Direct, decision.Country, decision.Reason)
	}
	
	// Проверяем статус сервера
	serverStatus := router.GetServerStatus()
	fmt.Printf("   Статус сервера: %t\n", serverStatus)
	
	fmt.Println("\nТестирование завершено успешно!")
}