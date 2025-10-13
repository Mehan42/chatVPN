package steps

import (
	"fmt"
	"log"
	"xvpn-client-go/internal/gateway/core"
	"xvpn-client-go/internal/gateway/tunnel"
)

// TunnelRouteStep - шаг для маршрутизации трафика через туннель
type TunnelRouteStep struct {
	name    string
	manager *tunnel.Manager
}

// NewTunnelRouteStep создает новый экземпляр TunnelRouteStep
func NewTunnelRouteStep(remoteServer string) (*TunnelRouteStep, error) {
	manager, err := tunnel.NewManager(remoteServer)
	if err != nil {
		return nil, fmt.Errorf("failed to create tunnel manager: %w", err)
	}
	return &TunnelRouteStep{
		name:    "TunnelRouteStep",
		manager: manager,
	}, nil
}

// Name возвращает имя шага
func (s *TunnelRouteStep) Name() string { return s.name }

// Process обрабатывает событие маршрутизации через туннель
func (s *TunnelRouteStep) Process(event core.Event, emit func(core.Event)) error {
	if event.Type != "RouteViaTunnel" {
		return nil
	}

	info, ok := event.Data.(*core.PacketInfo)
	if !ok {
		return fmt.Errorf("invalid event data for TunnelRouteStep")
	}

	log.Printf("Routing packet to %s via tunnel", info.DestIP)
	// Отправляем данные в туннель. Менеджер сам разберется с инкапсуляцией.
	return s.manager.Send(info.Payload)
}

// Close освобождает ресурсы
func (s *TunnelRouteStep) Close() {
	if s.manager != nil {
		s.manager.Close()
	}
}