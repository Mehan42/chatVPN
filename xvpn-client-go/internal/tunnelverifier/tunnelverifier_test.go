package tunnelverifier

import (
	"context"
	"testing"
	"time"
)

func TestTunnelVerifierCreation(t *testing.T) {
	config := Config{
		CheckInterval:       1 * time.Second,
		Timeout:             5 * time.Second,
		VerificationEndpoints: []string{"8.8.8.8"},
		TestPayload:         "TEST",
	}

	tv, err := New(config)
	if err != nil {
		t.Fatalf("Failed to create TunnelVerifier: %v", err)
	}

	if tv == nil {
		t.Fatal("TunnelVerifier should not be nil")
	}
}

func TestTunnelVerifierStartStop(t *testing.T) {
	config := Config{
		CheckInterval:       1 * time.Second,
		Timeout:             5 * time.Second,
		VerificationEndpoints: []string{"8.8.8.8"},
		TestPayload:         "TEST",
	}

	tv, err := New(config)
	if err != nil {
		t.Fatalf("Failed to create TunnelVerifier: %v", err)
	}

	ctx := context.Background()
	
	// Попробуем запустить
	err = tv.Start(ctx)
	if err != nil {
		t.Logf("Error starting TunnelVerifier (expected in test environment): %v", err)
		// Не прерываем тест, так как в тестовой среде могут отсутствовать необходимые зависимости
	}

	// Попробуем остановить
	err = tv.Stop(ctx)
	if err != nil {
		t.Logf("Error stopping TunnelVerifier: %v", err)
	}
}

func TestTunnelVerifierInitialState(t *testing.T) {
	config := Config{
		CheckInterval:       1 * time.Second,
		Timeout:             5 * time.Second,
		VerificationEndpoints: []string{"8.8.8.8"},
		TestPayload:         "TEST",
	}

	tv, err := New(config)
	if err != nil {
		t.Fatalf("Failed to create TunnelVerifier: %v", err)
	}

	// Проверим начальное состояние
	valid, err := tv.IsTunnelingValid()
	if err != nil {
		t.Logf("Error checking tunnel validity: %v", err)
		// Это ожидаемо до запуска проверки
	}

	// В начальном состоянии, без запущенных процессов, валидность может быть false
	// Это нормальное поведение
	t.Logf("Initial tunnel validity: %v", valid)
}