package transport

import (
	"log"
	"math/rand"
	"sync"
	"time"
)

// TransportType определяет тип транспорта
type TransportType string

const (
	TypeVLESS    TransportType = "vless"
	TypeVMess    TransportType = "vmess"
	TypeTrojan   TransportType = "trojan"
	TypeShadowsocks TransportType = "shadowsocks"
	TypeWireGuard TransportType = "wireguard"
	TypeHysteria2 TransportType = "hysteria2"
)

// Transport описывает транспорт
type Transport struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        TransportType          `json:"type"`
	Priority    int                    `json:"priority"`
	IPv6        bool                   `json:"ipv6"`
	NeedUDP     bool                   `json:"need_udp"`
	RUTraffic   bool                   `json:"ru_traffic"`   // Поддерживает российский трафик
	NonRUTraffic bool                  `json:"non_ru_traffic"` // Поддерживает международный трафик
	Config      map[string]interface{} `json:"config"`
	RTT         time.Duration          `json:"rtt"`          // Время отклика
	LastChecked time.Time              `json:"last_checked"` // Время последней проверки
	Healthy     bool                   `json:"healthy"`      // Состояние здоровья
}

// TransportManager управляет транспортами
type TransportManager struct {
	availableTransports []Transport
	currentTransport    *Transport
	fallbackTransports  []Transport
	mutex               sync.RWMutex
	logger              *log.Logger
	healthCheckInterval time.Duration
	ruTrafficOnly       bool // Режим только для РУ трафика
}

// NewTransportManager создает новый менеджер транспортов
func NewTransportManager() *TransportManager {
	return &TransportManager{
		availableTransports: make([]Transport, 0),
		fallbackTransports:  make([]Transport, 0),
		healthCheckInterval: 30 * time.Second,
		logger:              log.Default(),
	}
}

// AddTransport добавляет транспорт в список доступных
func (tm *TransportManager) AddTransport(transport Transport) {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()
	
	// Проверяем, существует ли уже транспорт с таким ID
	for i, t := range tm.availableTransports {
		if t.ID == transport.ID {
			// Обновляем существующий транспорт
			tm.availableTransports[i] = transport
			return
		}
	}
	
	// Добавляем новый транспорт
	tm.availableTransports = append(tm.availableTransports, transport)
	
	// Сортируем транспорты по приоритету
	tm.sortTransportsByPriority()
}

// sortTransportsByPriority сортирует транспорты по приоритету (меньше - выше приоритет)
func (tm *TransportManager) sortTransportsByPriority() {
	for i := 0; i < len(tm.availableTransports)-1; i++ {
		for j := i + 1; j < len(tm.availableTransports); j++ {
			if tm.availableTransports[i].Priority > tm.availableTransports[j].Priority {
				tm.availableTransports[i], tm.availableTransports[j] = tm.availableTransports[j], tm.availableTransports[i]
			}
		}
	}
}

// GetAvailableTransports возвращает список доступных транспортов
func (tm *TransportManager) GetAvailableTransports() []Transport {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	transports := make([]Transport, len(tm.availableTransports))
	copy(transports, tm.availableTransports)
	return transports
}

// GetTransportByID возвращает транспорт по ID
func (tm *TransportManager) GetTransportByID(id string) (*Transport, bool) {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	for _, transport := range tm.availableTransports {
		if transport.ID == id {
			return &transport, true
		}
	}
	
	return nil, false
}

// GetBestTransportForTraffic возвращает лучший транспорт для указанного типа трафика
func (tm *TransportManager) GetBestTransportForTraffic(isRUTraffic bool) *Transport {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	// Если нужен транспорт только для РУ трафика
	if isRUTraffic {
		// Ищем транспорт, который поддерживает РУ трафик
		for i := range tm.availableTransports {
			if tm.availableTransports[i].RUTraffic && tm.availableTransports[i].Healthy {
				transport := tm.availableTransports[i]
				return &transport
			}
		}
		// Если не нашли подходящий, используем любой здоровый
		for i := range tm.availableTransports {
			if tm.availableTransports[i].Healthy {
				transport := tm.availableTransports[i]
				return &transport
			}
		}
	} else {
		// Для неРУ трафика ищем транспорт, который поддерживает неРУ трафик
		for i := range tm.availableTransports {
			if tm.availableTransports[i].NonRUTraffic && tm.availableTransports[i].Healthy {
				transport := tm.availableTransports[i]
				return &transport
			}
		}
		// Если не нашли подходящий, используем любой здоровый
		for i := range tm.availableTransports {
			if tm.availableTransports[i].Healthy {
				transport := tm.availableTransports[i]
				return &transport
			}
		}
	}
	
	// Если нет здоровых транспортов, возвращаем первый из списка
	if len(tm.availableTransports) > 0 {
		transport := tm.availableTransports[0]
		return &transport
	}
	
	return nil
}

// GetCurrentTransport возвращает текущий транспорт
func (tm *TransportManager) GetCurrentTransport() *Transport {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	if tm.currentTransport != nil {
		transport := *tm.currentTransport
		return &transport
	}
	
	return nil
}

// SetCurrentTransport устанавливает текущий транспорт
func (tm *TransportManager) SetCurrentTransport(transport *Transport) {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()
	
	if transport != nil {
		t := *transport
		tm.currentTransport = &t
	}
}

// ForceTransportSwitch принудительно переключает транспорт
func (tm *TransportManager) ForceTransportSwitch(transportID string) bool {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()
	
	// Находим транспорт по ID
	for _, transport := range tm.availableTransports {
		if transport.ID == transportID {
			t := transport
			tm.currentTransport = &t
			tm.logger.Printf("Транспорт переключен на: %s", transport.ID)
			return true
		}
	}
	
	return false
}

// HealthCheck проводит проверку здоровья транспортов
func (tm *TransportManager) HealthCheck() {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()
	
	for i := range tm.availableTransports {
		transport := &tm.availableTransports[i]
		
		// Проверяем здоровье транспорта (имитация)
		healthy := tm.testTransportConnection(transport)
		
		// Обновляем состояние
		transport.Healthy = healthy
		transport.LastChecked = time.Now()
		
		if !healthy {
			tm.logger.Printf("Транспорт %s не здоров", transport.ID)
		}
	}
}

// testTransportConnection проверяет соединение с транспортом (имитация)
func (tm *TransportManager) testTransportConnection(transport *Transport) bool {
	// В реальной реализации здесь будет проверка соединения с транспортом
	// В этой демонстрации просто имитируем результат
	
	// 90% успеха для здоровых транспортов
	return rand.Float32() < 0.9
}

// DiscoverTransports имитирует обнаружение транспортов
func (tm *TransportManager) DiscoverTransports(manifestURL string) error {
	// В реальной реализации здесь будет загрузка манифеста транспортов с сервера
	// В этой демонстрации создаем фиктивные транспорты
	
	fakeTransports := []Transport{
		{
			ID:           "vless-reality",
			Name:         "VLESS + Reality",
			Type:         TypeVLESS,
			Priority:     1,
			IPv6:         true,
			NeedUDP:      false,
			RUTraffic:    true,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(443),
				"protocol": "tcp",
			},
		},
		{
			ID:           "v2ray-websocket",
			Name:         "V2Ray WebSocket",
			Type:         TypeVMess,
			Priority:     2,
			IPv6:         true,
			NeedUDP:      false,
			RUTraffic:    false,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(443),
				"protocol": "ws",
				"path":   "/v2ray",
			},
		},
		{
			ID:           "wireguard-tls",
			Name:         "WireGuard-over-TLS",
			Type:         TypeWireGuard,
			Priority:     3,
			IPv6:         true,
			NeedUDP:      true,
			RUTraffic:    false,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(51820),
				"protocol": "udp",
			},
		},
		{
			ID:           "trojan-tcp",
			Name:         "Trojan TCP",
			Type:         TypeTrojan,
			Priority:     4,
			IPv6:         true,
			NeedUDP:      false,
			RUTraffic:    true,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(443),
				"protocol": "tcp",
			},
		},
		{
			ID:           "shadowsocks-aead",
			Name:         "ShadowSocks AEAD",
			Type:         TypeShadowsocks,
			Priority:     5,
			IPv6:         true,
			NeedUDP:      true,
			RUTraffic:    false,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(8484),
				"protocol": "udp",
			},
		},
		{
			ID:           "hysteria2",
			Name:         "Hysteria 2",
			Type:         TypeHysteria2,
			Priority:     6,
			IPv6:         true,
			NeedUDP:      true,
			RUTraffic:    false,
			NonRUTraffic: true,
			Config: map[string]interface{}{
				"server": "example.com",
				"port":   float64(2096),
				"protocol": "udp",
			},
		},
	}
	
	// Добавляем транспорты в менеджер
	for _, transport := range fakeTransports {
		tm.AddTransport(transport)
	}
	
	return nil
}

// StartHealthCheckLoop запускает цикл проверки здоровья
func (tm *TransportManager) StartHealthCheckLoop() {
	go func() {
		for {
			tm.HealthCheck()
			time.Sleep(tm.healthCheckInterval)
		}
	}()
}

// GetHealthyTransports возвращает только здоровые транспорты
func (tm *TransportManager) GetHealthyTransports() []Transport {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	healthyTransports := make([]Transport, 0)
	for _, transport := range tm.availableTransports {
		if transport.Healthy {
			healthyTransports = append(healthyTransports, transport)
		}
	}
	
	return healthyTransports
}

// SelectTransportByRTT выбирает транспорт с наименьшим RTT
func (tm *TransportManager) SelectTransportByRTT() *Transport {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	
	var bestTransport *Transport
	var minRTT time.Duration = time.Duration(1<<63 - 1) // max duration
	
	for i := range tm.availableTransports {
		transport := &tm.availableTransports[i]
		if transport.Healthy && transport.RTT < minRTT {
			minRTT = transport.RTT
			bestTransport = transport
		}
	}
	
	return bestTransport
}

// UpdateTransportRTT обновляет RTT для транспорта
func (tm *TransportManager) UpdateTransportRTT(transportID string, rtt time.Duration) {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()
	
	for i := range tm.availableTransports {
		if tm.availableTransports[i].ID == transportID {
			tm.availableTransports[i].RTT = rtt
			return
		}
	}
}