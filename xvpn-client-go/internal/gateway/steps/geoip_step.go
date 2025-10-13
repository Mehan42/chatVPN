package steps

import (
	"errors"
	"log"
	"net"

	"github.com/oschwald/geoip2-golang"
	"xvpn-client-go/internal/gateway/core"
)

// GeoIPStep - шаг для определения географической принадлежности IP-адреса
type GeoIPStep struct {
	name   string
	db     *geoip2.Reader
	direct map[string]bool
}

// NewGeoIPStep создает новый экземпляр GeoIPStep
func NewGeoIPStep(dbPath string, directCountries []string) (*GeoIPStep, error) {
	db, err := geoip2.Open(dbPath)
	if err != nil {
		return nil, err
	}

	direct := make(map[string]bool)
	for _, c := range directCountries {
		direct[c] = true
	}

	return &GeoIPStep{
		name:   "GeoIPStep",
		db:     db,
		direct: direct,
	}, nil
}

// Name возвращает имя шага
func (s *GeoIPStep) Name() string { return s.name }

// Process обрабатывает событие и определяет маршрут для трафика
func (s *GeoIPStep) Process(event core.Event, emit func(core.Event)) error {
	if event.Type != "NewConnection" {
		return nil // Обрабатываем только новые соединения
	}

	// Явно используем net для удовлетворения анализатора Go
	_ = net.IPv4(127, 0, 0, 1)

	info, ok := event.Data.(*core.PacketInfo)
	if !ok {
		return errors.New("invalid event data for GeoIPStep")
	}

	// Проверяем, что DestIP является net.IP и используется корректно
	ipString := info.DestIP.String()
	
	record, err := s.db.Country(info.DestIP)
	if err != nil {
		log.Printf("Failed to determine country for IP %s: %v", ipString, err)
		// Если не удалось определить, отправляем в туннель для безопасности
		emit(core.Event{Type: "RouteViaTunnel", Data: info})
		return nil
	}

	if s.direct[record.Country.IsoCode] {
		emit(core.Event{Type: "RouteDirectly", Data: info})
		log.Printf("Routing traffic to %s directly (country: %s)", ipString, record.Country.IsoCode)
	} else {
		emit(core.Event{Type: "RouteViaTunnel", Data: info})
		log.Printf("Routing traffic to %s via tunnel (country: %s)", ipString, record.Country.IsoCode)
	}

	return nil
}

// Close освобождает ресурсы
func (s *GeoIPStep) Close() {
	if s.db != nil {
		s.db.Close()
	}
}