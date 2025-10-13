package core

import "net"

// Event - базовое событие в системе
type Event struct {
	Type string      // Тип события, например, "NewConnection"
	Data interface{} // Данные события, например, *PacketInfo
}

// PacketInfo - информация о перехваченном пакете
type PacketInfo struct {
	PacketID   uint32
	Payload    []byte
	DestIP     net.IP
	DestPort   int
	Protocol   string // "tcp", "udp"
	SourceIP   net.IP
	SourcePort int
}

// Step - интерфейс для всех шагов обработки
type Step interface {
	// Process обрабатывает событие и может вернуть новое событие
	Process(event Event, emit func(Event)) error
	// Name возвращает имя шага
	Name() string
}