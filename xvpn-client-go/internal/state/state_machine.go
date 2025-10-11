package state

import (
	"log"
	"sync"
	"time"
)

// State определяет возможные состояния VPN клиента
type State string

const (
	StateInitializing      State = "initializing"
	StateIdle             State = "idle"
	StateConfigFetching   State = "config_fetching"
	StateConfigValidating State = "config_validating"
	StateStarting         State = "starting"
	StateRunning          State = "running"
	StateHealthChecking   State = "health_checking"
	StateSwitchingTransport State = "switching_transport"
	StateStopping         State = "stopping"
	StateError            State = "error"
	StateRecovering       State = "recovering"
	StateUpdating         State = "updating"
)

// Event определяет возможные события для машины состояний
type Event string

const (
	EventStartRequested         Event = "start_requested"
	EventStopRequested          Event = "stop_requested"
	EventConfigFetched          Event = "config_fetched"
	EventConfigValidated        Event = "config_validated"
	EventStartSuccess           Event = "start_success"
	EventStartFailed            Event = "start_failed"
	EventHealthCheckFailed      Event = "health_check_failed"
	EventHealthCheckPassed      Event = "health_check_passed"
	EventTransportSwitchFailed  Event = "transport_switch_failed"
	EventTransportSwitchSuccess Event = "transport_switch_success"
	EventErrorOccurred          Event = "error_occurred"
	EventRecoverySuccess        Event = "recovery_success"
	EventRecoveryFailed         Event = "recovery_failed"
	EventUpdateAvailable        Event = "update_available"
	EventUpdateCompleted        Event = "update_completed"
)

// Context хранит контекст машины состояний
type Context struct {
	ClientUUID       string `json:"client_uuid"`
	CurrentState     State  `json:"current_state"`
	PreviousState    *State `json:"previous_state,omitempty"`
	StateEnteredAt   int64  `json:"state_entered_at"`
	LastError        string `json:"last_error,omitempty"`
	ErrorCount       int    `json:"error_count"`
	CurrentTransport *Transport `json:"current_transport,omitempty"`
	HealthScore      int    `json:"health_score"`
	NetworkInfo      *NetworkInfo `json:"network_info,omitempty"`
	RetryCount       int    `json:"retry_count"`
	MaxRetries       int    `json:"max_retries"`
	LastHealthCheck  int64  `json:"last_health_check"`
	HealthCheckInterval int `json:"health_check_interval"`
	FallbackTransports []Transport `json:"fallback_transports"`
	Config           map[string]interface{} `json:"config,omitempty"`
}

// Transport описывает транспорт
type Transport struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Type     string `json:"type"`
	Priority int    `json:"priority"`
	IPv6     bool   `json:"ipv6"`
	NeedUDP  bool   `json:"need_udp"`
	Config   map[string]interface{} `json:"config"`
}

// NetworkInfo описывает информацию о сети
type NetworkInfo struct {
	LocalIPs    map[string]string `json:"local_ips"`
	ExternalIPs map[string]string `json:"external_ips"`
	IPLeak      bool             `json:"ip_leak"`
	VPNActive   bool             `json:"vpn_active"`
	DualStack   bool             `json:"dual_stack"`
}

// Transition определяет правило перехода состояний
type Transition struct {
	FromState State
	Event     Event
	ToState   State
	Action    func(*Context) error // Опциональная функция действия
}

// VPNStateMachine реализует полную машину состояний VPN клиента
type VPNStateMachine struct {
	context        *Context
	running        bool
	stateHistory   []State
	eventQueue     chan Event
	logger         *log.Logger
	transitionMap  map[State]map[Event]Transition
	mutex          sync.RWMutex
}

// NewVPNStateMachine создает новую машину состояний
func NewVPNStateMachine(clientUUID string) *VPNStateMachine {
	sm := &VPNStateMachine{
		context: &Context{
			ClientUUID:        clientUUID,
			CurrentState:      StateInitializing,
			StateEnteredAt:    time.Now().Unix(),
			MaxRetries:        3,
			HealthCheckInterval: 30,
			FallbackTransports: make([]Transport, 0),
		},
		running:      false,
		stateHistory: make([]State, 0),
		eventQueue:   make(chan Event, 100),
		logger:       log.Default(),
		transitionMap: make(map[State]map[Event]Transition),
	}

	// Определяем правила переходов
	sm.defineTransitions()

	return sm
}

// defineTransitions определяет правила переходов состояний
func (sm *VPNStateMachine) defineTransitions() {
	// Инициализация
	sm.addTransition(StateInitializing, EventStartRequested, StateConfigFetching, nil)
	
	// Ожидание конфигурации
	sm.addTransition(StateConfigFetching, EventConfigFetched, StateConfigValidating, nil)
	sm.addTransition(StateConfigFetching, EventErrorOccurred, StateError, nil)
	
	// Валидация конфигурации
	sm.addTransition(StateConfigValidating, EventConfigValidated, StateIdle, nil)
	sm.addTransition(StateConfigValidating, EventErrorOccurred, StateError, nil)
	
	// Запуск VPN
	sm.addTransition(StateIdle, EventStartRequested, StateStarting, nil)
	sm.addTransition(StateStarting, EventStartSuccess, StateRunning, nil)
	sm.addTransition(StateStarting, EventStartFailed, StateError, nil)
	sm.addTransition(StateStarting, EventErrorOccurred, StateError, nil)
	
	// Работа VPN
	sm.addTransition(StateRunning, EventHealthCheckFailed, StateHealthChecking, nil)
	sm.addTransition(StateRunning, EventTransportSwitchFailed, StateSwitchingTransport, nil)
	sm.addTransition(StateRunning, EventStopRequested, StateStopping, nil)
	sm.addTransition(StateRunning, EventUpdateAvailable, StateUpdating, nil)
	
	// Проверка здоровья
	sm.addTransition(StateHealthChecking, EventHealthCheckPassed, StateRunning, nil)
	sm.addTransition(StateHealthChecking, EventHealthCheckFailed, StateSwitchingTransport, nil)
	sm.addTransition(StateHealthChecking, EventErrorOccurred, StateError, nil)
	
	// Переключение транспорта
	sm.addTransition(StateSwitchingTransport, EventTransportSwitchSuccess, StateRunning, nil)
	sm.addTransition(StateSwitchingTransport, EventTransportSwitchFailed, StateRecovering, nil)
	sm.addTransition(StateSwitchingTransport, EventErrorOccurred, StateError, nil)
	
	// Остановка VPN
	sm.addTransition(StateStopping, EventStopRequested, StateIdle, nil)
	sm.addTransition(StateStopping, EventErrorOccurred, StateError, nil)
	
	// Восстановление
	sm.addTransition(StateRecovering, EventRecoverySuccess, StateRunning, nil)
	sm.addTransition(StateRecovering, EventRecoveryFailed, StateError, nil)
	sm.addTransition(StateError, EventStartRequested, StateRecovering, nil)
	
	// Обновление
	sm.addTransition(StateUpdating, EventUpdateCompleted, StateRunning, nil)
	sm.addTransition(StateUpdating, EventErrorOccurred, StateError, nil)
}

// addTransition добавляет правило перехода
func (sm *VPNStateMachine) addTransition(fromState State, event Event, toState State, action func(*Context) error) {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	if sm.transitionMap[fromState] == nil {
		sm.transitionMap[fromState] = make(map[Event]Transition)
	}
	
	sm.transitionMap[fromState][event] = Transition{
		FromState: fromState,
		Event:     event,
		ToState:   toState,
		Action:    action,
	}
}

// TriggerEvent вызывает событие в машине состояний
func (sm *VPNStateMachine) TriggerEvent(event Event) {
	select {
	case sm.eventQueue <- event:
		sm.logger.Printf("Event queued: %s", event)
	default:
		sm.logger.Printf("Event queue full, dropping event: %s", event)
	}
}

// processEvents обрабатывает события в машине состояний
func (sm *VPNStateMachine) processEvents() {
	for sm.running {
		select {
		case event := <-sm.eventQueue:
			sm.handleEvent(event)
		case <-time.After(100 * time.Millisecond): // Таймаут для проверки running
			if !sm.running {
				return
			}
		}
	}
}

// handleEvent обрабатывает событие
func (sm *VPNStateMachine) handleEvent(event Event) {
	sm.mutex.RLock()
	currentState := sm.context.CurrentState
	transitionMap := sm.transitionMap[currentState]
	sm.mutex.RUnlock()
	
	// Ищем переход для текущего состояния и события
	transition, exists := transitionMap[event]
	
	if exists {
		sm.executeTransition(transition)
	} else {
		sm.logger.Printf("No transition found for %s -> %s", currentState, event)
	}
}

// executeTransition выполняет переход состояний
func (sm *VPNStateMachine) executeTransition(transition Transition) {
	oldState := sm.context.CurrentState
	newState := transition.ToState

	sm.logger.Printf("State transition: %s -> %s", oldState, newState)

	// Выполняем действие перехода
	if transition.Action != nil {
		err := transition.Action(sm.context)
		if err != nil {
			sm.logger.Printf("Error in transition action: %v", err)
			sm.TriggerEvent(EventErrorOccurred)
			return
		}
	}

	// Обновляем контекст
	sm.mutex.Lock()
	previousState := oldState
	sm.context.PreviousState = &previousState
	sm.context.CurrentState = newState
	sm.context.StateEnteredAt = time.Now().Unix()
	sm.mutex.Unlock()

	// Сохраняем историю состояний
	sm.stateHistory = append(sm.stateHistory, newState)
	
	// Выполняем действия для нового состояния
	sm.executeStateActions(newState)
}

// executeStateActions выполняет действия для состояния
func (sm *VPNStateMachine) executeStateActions(state State) {
	switch state {
	case StateInitializing:
		sm.actionInitializing()
	case StateConfigFetching:
		sm.actionConfigFetching()
	case StateConfigValidating:
		sm.actionConfigValidating()
	case StateIdle:
		sm.actionIdle()
	case StateStarting:
		sm.actionStarting()
	case StateRunning:
		sm.actionRunning()
	case StateHealthChecking:
		sm.actionHealthChecking()
	case StateSwitchingTransport:
		sm.actionSwitchingTransport()
	case StateStopping:
		sm.actionStopping()
	case StateError:
		sm.actionError()
	case StateRecovering:
		sm.actionRecovering()
	case StateUpdating:
		sm.actionUpdating()
	}
}

// actionInitializing реализует действия для состояния инициализации
func (sm *VPNStateMachine) actionInitializing() {
	sm.logger.Printf("Initializing VPN client...")
	
	// После инициализации переходим к запросу конфигурации
	sm.TriggerEvent(EventStartRequested)
}

// actionConfigFetching реализует действия для состояния загрузки конфигурации
func (sm *VPNStateMachine) actionConfigFetching() {
	sm.logger.Printf("Fetching configuration from server...")
	
	// Здесь была бы логика загрузки конфигурации
	// Для примера, просто имитируем успешную загрузку
	sm.context.Config = map[string]interface{}{
		"uuid": sm.context.ClientUUID,
		"transports": []interface{}{
			map[string]interface{}{
				"id": "vless-reality",
				"name": "VLESS + Reality",
				"type": "vless-reality",
				"priority": float64(1),
			},
		},
	}
	
	// Добавляем транспорты в список fallback
	if transports, ok := sm.context.Config["transports"].([]interface{}); ok {
		for _, t := range transports {
			if transportMap, ok := t.(map[string]interface{}); ok {
				transport := Transport{
					ID:       transportMap["id"].(string),
					Name:     transportMap["name"].(string),
					Type:     transportMap["type"].(string),
					Priority: int(transportMap["priority"].(float64)),
				}
				sm.context.FallbackTransports = append(sm.context.FallbackTransports, transport)
			}
		}
	}
	
	sm.TriggerEvent(EventConfigFetched)
}

// actionConfigValidating реализует действия для состояния валидации конфигурации
func (sm *VPNStateMachine) actionConfigValidating() {
	sm.logger.Printf("Validating configuration...")
	
	// Проверяем структуру конфигурации
	if sm.context.Config == nil {
		sm.logger.Println("No configuration data")
		sm.TriggerEvent(EventErrorOccurred)
		return
	}
	
	// Выбираем текущий транспорт
	if len(sm.context.FallbackTransports) > 0 {
		sm.context.CurrentTransport = &sm.context.FallbackTransports[0]
		sm.TriggerEvent(EventConfigValidated)
	} else {
		sm.logger.Println("No available transport")
		sm.TriggerEvent(EventErrorOccurred)
		return
	}
}

// actionIdle реализует действия для состояния ожидания
func (sm *VPNStateMachine) actionIdle() {
	sm.logger.Printf("VPN client idle")
	
	// Периодическая проверка конфигурации
	if time.Now().Unix() - sm.context.LastHealthCheck > 300 { // 5 минут
		sm.TriggerEvent(EventStartRequested)
	}
}

// actionStarting реализует действия для состояния запуска
func (sm *VPNStateMachine) actionStarting() {
	sm.logger.Printf("Starting VPN...")
	
	// Здесь была бы логика запуска VPN (например, XRay)
	// Для примера, просто имитируем успешный запуск
	sm.TriggerEvent(EventStartSuccess)
}

// actionRunning реализует действия для состояния работы
func (sm *VPNStateMachine) actionRunning() {
	sm.logger.Printf("VPN running")
	
	// Запускаем мониторинг здоровья в отдельной горутине
	go sm.startHealthMonitoring()
	
	// Обновляем информацию о сети
	sm.context.NetworkInfo = sm.getNetworkInfo()
}

// startHealthMonitoring запускает мониторинг здоровья
func (sm *VPNStateMachine) startHealthMonitoring() {
	for sm.isState(StateRunning) {
		time.Sleep(time.Duration(sm.context.HealthCheckInterval) * time.Second)
		
		// Здесь будет вызов функции проверки здоровья
		healthScore := 5 // для примера
		
		// Обновляем информацию о здоровье
		sm.context.HealthScore = healthScore
		sm.context.NetworkInfo = sm.getNetworkInfo()
		sm.context.LastHealthCheck = time.Now().Unix()
		
		// Если оценка здоровья низкая, переходим к проверке здоровья
		if healthScore < 3 {
			sm.logger.Printf("Health score is low (%d), triggering health check", healthScore)
			sm.TriggerEvent(EventHealthCheckFailed)
		} else {
			sm.logger.Printf("Health score is good (%d)", healthScore)
		}
	}
}

// getNetworkInfo возвращает информацию о сети
func (sm *VPNStateMachine) getNetworkInfo() *NetworkInfo {
	return &NetworkInfo{
		LocalIPs:    map[string]string{"ipv4": "192.168.1.10", "ipv6": "2001:db8::1"},
		ExternalIPs: map[string]string{"ipv4": "203.0.113.10", "ipv6": "2001:4860:4860::8888"},
		IPLeak:      false,
		VPNActive:   true,
		DualStack:   true,
	}
}

// actionHealthChecking реализует действия для проверки здоровья
func (sm *VPNStateMachine) actionHealthChecking() {
	sm.logger.Printf("Performing health check...")
	
	// Здесь будет логика проверки здоровья
	healthScore := 4 // для примера
	
	sm.context.HealthScore = healthScore
	
	// Если оценка здоровья хорошая, возвращаемся к нормальному состоянию
	if healthScore >= 3 {
		sm.TriggerEvent(EventHealthCheckPassed)
	} else {
		// Если оценка здоровья плохая, инициируем переключение транспорта
		sm.logger.Printf("Health score is low (%d), initiating transport switch", healthScore)
		sm.TriggerEvent(EventHealthCheckFailed)
	}
}

// actionSwitchingTransport реализует действия для переключения транспорта
func (sm *VPNStateMachine) actionSwitchingTransport() {
	sm.logger.Printf("Switching transport...")
	
	if len(sm.context.FallbackTransports) > 0 && sm.context.CurrentTransport != nil {
		// Ищем следующий доступный транспорт
		for _, transport := range sm.context.FallbackTransports {
			if transport.ID != sm.context.CurrentTransport.ID {
				// Здесь будет логика переключения
				sm.context.CurrentTransport = &transport
				sm.TriggerEvent(EventTransportSwitchSuccess)
				return
			}
		}
	}
	
	// Если не нашли альтернативный транспорт
	sm.logger.Println("No fallback transport available")
	sm.TriggerEvent(EventErrorOccurred)
}

// actionStopping реализует действия для остановки
func (sm *VPNStateMachine) actionStopping() {
	sm.logger.Printf("Stopping VPN...")
	
	// Здесь будет логика остановки VPN
	sm.TriggerEvent(EventStopRequested)
}

// actionError реализует действия для состояния ошибки
func (sm *VPNStateMachine) actionError() {
	sm.logger.Printf("VPN client in error state: %s", sm.context.LastError)
	
	// Попытка восстановления
	if sm.context.ErrorCount < sm.context.MaxRetries {
		sm.context.ErrorCount++
		sm.logger.Printf("Retrying... Attempt %d", sm.context.ErrorCount)
		
		// Увеличиваем задержку между попытками
		time.Sleep(time.Duration(sm.context.ErrorCount*2) * time.Second) // экспоненциальный откат
		sm.TriggerEvent(EventStartRequested)
	} else {
		sm.logger.Println("Max retries reached, giving up")
		// Попытка перезапуска с нуля
		sm.context.ErrorCount = 0
		// Можно добавить оповещение о невозможности подключения
	}
}

// actionRecovering реализует действия для восстановления
func (sm *VPNStateMachine) actionRecovering() {
	sm.logger.Printf("Attempting recovery...")
	
	// Здесь будет логика восстановления
	// Для примера, просто имитируем успешное восстановление
	sm.TriggerEvent(EventRecoverySuccess)
}

// actionUpdating реализует действия для обновления
func (sm *VPNStateMachine) actionUpdating() {
	sm.logger.Printf("Updating VPN configuration...")
	
	// Здесь будет логика обновления конфигурации
	// Для примера, просто имитируем успешное обновление
	sm.TriggerEvent(EventUpdateCompleted)
}

// GetStateInfo возвращает информацию о текущем состоянии
func (sm *VPNStateMachine) GetStateInfo() map[string]interface{} {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	return map[string]interface{}{
		"current_state":     sm.context.CurrentState,
		"previous_state":    sm.context.PreviousState,
		"state_entered_at":  sm.context.StateEnteredAt,
		"last_error":        sm.context.LastError,
		"error_count":       sm.context.ErrorCount,
		"health_score":      sm.context.HealthScore,
		"network_info":      sm.context.NetworkInfo,
		"retry_count":       sm.context.RetryCount,
		"current_transport": sm.context.CurrentTransport,
		"client_uuid":       sm.context.ClientUUID,
	}
}

// isState проверяет, находится ли машина в определенном состоянии
func (sm *VPNStateMachine) isState(state State) bool {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	return sm.context.CurrentState == state
}

// Start запускает машину состояний
func (sm *VPNStateMachine) Start() {
	sm.mutex.Lock()
	sm.running = true
	sm.mutex.Unlock()
	
	sm.logger.Println("State Machine started")
	
	// Запуск обработки событий в отдельной горутине
	go sm.processEvents()
	
	// Выполняем действия для начального состояния
	sm.executeStateActions(sm.context.CurrentState)
}

// Stop останавливает машину состояний
func (sm *VPNStateMachine) Stop() {
	sm.mutex.Lock()
	sm.running = false
	sm.mutex.Unlock()
	
	close(sm.eventQueue)
	sm.logger.Println("State Machine stopped")
}