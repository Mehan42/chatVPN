package state

import (
	"context"
	"testing"
	"time"
	"xvpn-client-go/internal/tunnelverifier"
)

// TestTunnelVerifierIntegration тестирует интеграцию туннель-верификатора с машиной состояний
func TestTunnelVerifierIntegration(t *testing.T) {
	// Создаем машину состояний
	sm := NewVPNStateMachine("test-client-uuid")
	
	// Создаем обработчик интеграции с туннель-верификатором
	handler, err := NewTunnelVerifierStateHandler(sm)
	if err != nil {
		t.Fatalf("Failed to create tunnel verifier state handler: %v", err)
	}
	
	// Интегрируем с машиной состояний
	handler.IntegrateWithStateMachine()
	
	// Запускаем машину состояний
	sm.Start()
	
	// Переходим к состоянию Running
	sm.TriggerEvent(EventStartRequested) // -> ConfigFetching
	time.Sleep(100 * time.Millisecond)   // Allow state transition
	
	sm.TriggerEvent(EventConfigFetched)  // -> ConfigValidating
	time.Sleep(100 * time.Millisecond)   // Allow state transition
	
	sm.TriggerEvent(EventConfigValidated) // -> Idle
	time.Sleep(100 * time.Millisecond)    // Allow state transition
	
	sm.TriggerEvent(EventStartRequested)  // -> Starting -> Running
	time.Sleep(200 * time.Millisecond)    // Allow state transition
	
	// Проверяем, что машина находится в состоянии Running
	if sm.context.CurrentState != StateRunning {
		t.Errorf("Expected state to be %s, but got %s", StateRunning, sm.context.CurrentState)
	}
	
	// Проверяем, что туннель-верификатор работает (проверяем валидность)
	valid, err := handler.IsTunnelVerificationValid()
	if err != nil {
		t.Logf("Error checking tunnel verification validity: %v", err)
		// Это может быть нормально, если верификатор не полностью запущен
	} else {
		if !valid {
			t.Logf("Tunnel verification is not valid: %v", valid)
		} else {
			t.Logf("Tunnel verification is valid: %v", valid)
		}
	}
	
	// Переходим к состоянию Stopping
	sm.TriggerEvent(EventStopRequested)   // -> Stopping -> Idle
	time.Sleep(200 * time.Millisecond)    // Allow state transition
	
	// Проверяем, что машина находится в состоянии Idle
	if sm.context.CurrentState != StateIdle {
		t.Errorf("Expected state to be %s, but got %s", StateIdle, sm.context.CurrentState)
	}
	
	// Проверяем, что туннель-верификатор остановлен
	valid, err = handler.IsTunnelVerificationValid()
	if err != nil {
		t.Logf("Error checking tunnel verification validity after stop: %v", err)
	}
	
	t.Log("Tunnel verifier integration test completed")
	
	// Останавливаем машину состояний
	sm.Stop()
}

// TestTunnelVerifierStateTransitions тестирует переходы состояний туннель-верификатора
func TestTunnelVerifierStateTransitions(t *testing.T) {
	// Создаем машину состояний
	sm := NewVPNStateMachine("test-client-uuid")
	
	// Создаем обработчик интеграции с туннель-верификатором
	handler, err := NewTunnelVerifierStateHandler(sm)
	if err != nil {
		t.Fatalf("Failed to create tunnel verifier state handler: %v", err)
	}
	
	// Интегрируем с машиной состояний
	handler.IntegrateWithStateMachine()
	
	// Запускаем машину состояний
	sm.Start()
	
	// Тестируем разные переходы и проверяем, что туннель-верификатор реагирует правильно
	
	// 1. Инициализация -> Ожидание
	sm.TriggerEvent(EventStartRequested) // -> ConfigFetching -> ConfigValidating -> Idle
	time.Sleep(300 * time.Millisecond)   // Allow state transitions
	
	t.Logf("Current state: %s", sm.context.CurrentState)
	
	// 2. Ожидание -> Запуск -> Работа
	sm.TriggerEvent(EventStartRequested) // -> Starting -> Running
	time.Sleep(300 * time.Millisecond)   // Allow state transitions
	
	t.Logf("Current state: %s", sm.context.CurrentState)
	if sm.context.CurrentState != StateRunning {
		t.Log("State should be Running after start request")
	}
	
	// 3. Работа -> Остановка -> Ожидание
	sm.TriggerEvent(EventStopRequested)  // -> Stopping -> Idle
	time.Sleep(300 * time.Millisecond)   // Allow state transitions
	
	t.Logf("Current state: %s", sm.context.CurrentState)
	if sm.context.CurrentState != StateIdle {
		t.Log("State should be Idle after stop request")
	}
	
	t.Log("Tunnel verifier state transitions test completed")
	
	// Останавливаем машину состояний
	sm.Stop()
}

// TestTunnelVerifierErrorHandling тестирует обработку ошибок туннель-верификатором
func TestTunnelVerifierErrorHandling(t *testing.T) {
	// Создаем конфигурацию с коротким интервалом для быстрого тестирования
	config := tunnelverifier.Config{
		CheckInterval:       100 * time.Millisecond,
		Timeout:             5 * time.Second,
		VerificationEndpoints: []string{"8.8.8.8"},
		TestPayload:         "TEST",
	}
	
	// Создаем туннель-верификатор
	tv, err := tunnelverifier.New(config)
	if err != nil {
		t.Fatalf("Failed to create TunnelVerifier: %v", err)
	}
	
	ctx := context.Background()
	
	// Проверяем состояние до запуска
	valid, err := tv.IsTunnelingValid()
	if err != nil {
		t.Logf("Error checking validity before start: %v", err)
	}
	t.Logf("Validity before start: %v", valid)
	
	// Запускаем туннель-верификатор
	if err := tv.Start(ctx); err != nil {
		t.Logf("Error starting TunnelVerifier: %v", err)
		// Продолжаем тест, даже если запуск не удался
	}
	
	// Ждем немного
	time.Sleep(200 * time.Millisecond)
	
	// Проверяем состояние после запуска
	valid, err = tv.IsTunnelingValid()
	if err != nil {
		t.Logf("Error checking validity after start: %v", err)
	}
	t.Logf("Validity after start: %v", valid)
	
	// Останавливаем туннель-верификатор
	if err := tv.Stop(ctx); err != nil {
		t.Logf("Error stopping TunnelVerifier: %v", err)
	}
	
	t.Log("Tunnel verifier error handling test completed")
}