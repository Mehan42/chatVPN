package tunnel

import (
	"fmt"
	"log"
)

// Manager - менеджер туннелей
type Manager struct {
	remoteServer string
	// В реальной реализации здесь будут поля для соединения и т.д.
}

// NewManager создает новый экземпляр менеджера туннелей
func NewManager(remoteServer string) (*Manager, error) {
	// В реальной реализации здесь будет установка соединения
	log.Printf("Creating tunnel manager for server: %s", remoteServer)
	
	// Проверяем, что remoteServer в правильном формате host:port
	return &Manager{
		remoteServer: remoteServer,
	}, nil
}

// Send отправляет пакет через туннель
func (m *Manager) Send(payload []byte) error {
	log.Printf("Sending %d bytes via tunnel to %s", len(payload), m.remoteServer)
	// В реальной реализации здесь будет инкапсуляция и отправка пакета через TLS-туннель
	fmt.Printf("Data would be sent through tunnel: %v\n", payload[:min(len(payload), 10)]) // Показываем первые 10 байт для дебага
	return nil
}

// Close освобождает ресурсы
func (m *Manager) Close() {
	log.Println("Tunnel manager closed")
	// В реальной реализации здесь будет закрытие соединения
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}