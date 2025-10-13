package interceptor

import (
	"log"
	"xvpn-client-go/internal/gateway/core"
)

// Config - конфигурация перехватчика
type Config struct {
	RedirectPorts []int  `yaml:"redirect_ports"`
	ExcludeSubnets []string `yaml:"exclude_subnets"`
}

// NFQueueInterceptor - перехватчик трафика с использованием netfilter queue
type NFQueueInterceptor struct {
	config       Config
	eventChannel chan<- core.Event
	// В реальной реализации здесь будут поля для работы с netfilter queue
}

// NewNFQueueInterceptor создает новый экземпляр перехватчика
func NewNFQueueInterceptor(eventChannel chan<- core.Event, config Config) (*NFQueueInterceptor, error) {
	// В реальной реализации здесь будет инициализация netfilter queue
	log.Println("Creating NFQueue interceptor")
	
	return &NFQueueInterceptor{
		config:       config,
		eventChannel: eventChannel,
	}, nil
}

// Start запускает перехват трафика
func (n *NFQueueInterceptor) Start() {
	log.Println("Starting NFQueue interceptor")
	// В реальной реализации здесь будет цикл получения пакетов из очереди
	// и отправка их в eventChannel как события NewConnection
	
	// Для демонстрации отправим несколько фиктивных событий
	for i := 0; i < 5; i++ {
		packetInfo := &core.PacketInfo{
			PacketID: uint32(i),
			Payload:  []byte("dummy packet data"),
			DestIP:   []byte{8, 8, 8, 8}, // Пример: Google DNS
			DestPort: 443,
			Protocol: "tcp",
		}
		
		event := core.Event{
			Type: "NewConnection",
			Data: packetInfo,
		}
		
		n.eventChannel <- event
		log.Printf("Sent dummy event %d to engine", i)
		
		// Имитация задержки
		// time.Sleep(1 * time.Second)
	}
}

// Setup настраивает правила iptables для перенаправления трафика
func Setup(config Config) error {
	log.Printf("Setting up iptables rules for ports %v", config.RedirectPorts)
	// В реальной реализации здесь будут выполняться команды iptables
	// для перенаправления трафика на netfilter queue
	return nil
}

// Cleanup очищает правила iptables
func Cleanup() {
	log.Println("Cleaning up iptables rules")
	// В реальной реализации здесь будут удаляться правила iptables
}