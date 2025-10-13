package core

import (
	"log"
)

// RoutingEngine - ядро системы, аналог движка в Motia
type RoutingEngine struct {
	steps         []Step
	eventChannel  chan Event
	stopChannel   chan bool
}

// NewEngine создает новый экземпляр RoutingEngine
func NewEngine() *RoutingEngine {
	return &RoutingEngine{
		steps:        make([]Step, 0),
		eventChannel: make(chan Event, 100), // буферизированный канал для событий
		stopChannel:  make(chan bool),
	}
}

// RegisterStep регистрирует новый шаг обработки
func (e *RoutingEngine) RegisterStep(step Step) {
	e.steps = append(e.steps, step)
	log.Printf("Registered step: %s", step.Name())
}

// EventChannel возвращает канал для отправки событий в движок
func (e *RoutingEngine) EventChannel() chan Event {
	return e.eventChannel
}

// Start запускает обработку событий
func (e *RoutingEngine) Start() {
	log.Println("Routing Engine started")
	
	for {
		select {
		case event := <-e.eventChannel:
			e.processEvent(event)
		case <-e.stopChannel:
			log.Println("Routing Engine stopped")
			return
		}
	}
}

// Stop останавливает обработку событий
func (e *RoutingEngine) Stop() {
	close(e.stopChannel)
}

// processEvent обрабатывает событие через все зарегистрированные шаги
func (e *RoutingEngine) processEvent(event Event) {
	emit := func(newEvent Event) {
		// Отправляем новое событие в канал для дальнейшей обработки
		select {
		case e.eventChannel <- newEvent:
		default:
			log.Printf("Warning: event channel is full, dropping event: %s", newEvent.Type)
		}
	}
	
	for _, step := range e.steps {
		err := step.Process(event, emit)
		if err != nil {
			log.Printf("Error processing event %s in step %s: %v", event.Type, step.Name(), err)
			// В реальной реализации можно добавить логику обработки ошибок
		}
	}
}