package api

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"

	"xvpn-client-go/internal/config"
)

// APIClient клиент для взаимодействия с XVPN API сервером
type APIClient struct {
	baseURL    string
	clientUUID string
	httpClient *http.Client
	config     *config.ClientConfig
}

// TransportManifest структура манифеста транспортов
type TransportManifest struct {
	Version    int        `json:"version"`
	Transports []Transport `json:"transports"`
}

// Transport структура транспорта
type Transport struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	IPv6        bool                   `json:"ipv6"`
	NeedUDP     bool                   `json:"need_udp"`
	RUTraffic   bool                   `json:"ru_traffic"`
	NonRUTraffic bool                  `json:"non_ru_traffic"`
	Config      map[string]interface{} `json:"config"`
}

// HealthResponse структура ответа о состоянии здоровья
type HealthResponse struct {
	Status        string                 `json:"status"`
	MaskScore     int                    `json:"mask_score"`
	Timestamp     float64                `json:"timestamp"`
	Version       string                 `json:"version"`
	Services      map[string]bool        `json:"services"`
	SystemMetrics map[string]interface{} `json:"system_metrics"`
}

// NewAPIClient создает новый экземпляр API клиента
func NewAPIClient(serverURL, clientUUID string) *APIClient {
	// Создаем HTTP клиент с таймаутом и отключенной проверкой сертификатов для разработки
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true, // Отключаем проверку сертификатов для разработки
		},
	}
	
	client := &http.Client{
		Timeout:   30 * time.Second,
		Transport: transport,
	}
	
	return &APIClient{
		baseURL:    serverURL,
		clientUUID: clientUUID,
		httpClient: client,
	}
}

// GetTransportManifest получает манифест транспортов с сервера
func (ac *APIClient) GetTransportManifest() (*TransportManifest, error) {
	url := fmt.Sprintf("%s/transports/manifest.json", ac.baseURL)
	
	resp, err := ac.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("ошибка выполнения запроса: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения ответа: %v", err)
	}
	
	var manifest TransportManifest
	err = json.Unmarshal(body, &manifest)
	if err != nil {
		return nil, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}
	
	return &manifest, nil
}

// GetClientConfig получает конфигурацию клиента с сервера
func (ac *APIClient) GetClientConfig() (*config.ClientConfig, error) {
	url := fmt.Sprintf("%s/clients/%s.json", ac.baseURL, ac.clientUUID)
	
	resp, err := ac.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("ошибка выполнения запроса: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения ответа: %v", err)
	}
	
	var clientConfig config.ClientConfig
	err = json.Unmarshal(body, &clientConfig)
	if err != nil {
		return nil, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}
	
	return &clientConfig, nil
}

// HealthCheck проверяет состояние здоровья сервера
func (ac *APIClient) HealthCheck() (*HealthResponse, error) {
	url := fmt.Sprintf("%s/mcp/v1/vpn.health", ac.baseURL)
	
	resp, err := ac.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("ошибка выполнения запроса: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения ответа: %v", err)
	}
	
	var health HealthResponse
	err = json.Unmarshal(body, &health)
	if err != nil {
		return nil, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}
	
	return &health, nil
}

// RegisterClientOnServer регистрирует клиента на сервере (для администраторов)
func (ac *APIClient) RegisterClientOnServer() (string, error) {
	// url := fmt.Sprintf("%s/mcp/v1/admin.newclient", ac.baseURL)
	
	// В реальной реализации здесь будет POST запрос с данными нового клиента
	// Для имитации просто возвращаем тестовый UUID
	
	// req, err := http.NewRequest("POST", url, nil)
	// if err != nil {
	// 	return "", fmt.Errorf("ошибка создания запроса: %v", err)
	// }
	
	// resp, err := ac.httpClient.Do(req)
	// if err != nil {
	// 	return "", fmt.Errorf("ошибка выполнения запроса: %v", err)
	// }
	// defer resp.Body.Close()
	
	// if resp.StatusCode != http.StatusOK {
	// 	return "", fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	// }
	
	// // В реальной реализации здесь будет парсинг ответа
	
	return "test-uuid-generated-by-server", nil
}

// SetClientUUID устанавливает UUID клиента
func (ac *APIClient) SetClientUUID(uuid string) {
	ac.clientUUID = uuid
}

// GetClientUUID возвращает UUID клиента
func (ac *APIClient) GetClientUUID() string {
	return ac.clientUUID
}

// SetBaseURL устанавливает базовый URL сервера
func (ac *APIClient) SetBaseURL(baseURL string) {
	ac.baseURL = baseURL
}

// GetBaseURL возвращает базовый URL сервера
func (ac *APIClient) GetBaseURL() string {
	return ac.baseURL
}

// UpdateClientConfig обновляет конфигурацию клиента
func (ac *APIClient) UpdateClientConfig(newConfig *config.ClientConfig) error {
	// В реальной реализации здесь будет отправка обновленной конфигурации на сервер
	ac.config = newConfig
	return nil
}

// GetCachedConfig возвращает кэшированную конфигурацию клиента
func (ac *APIClient) GetCachedConfig() *config.ClientConfig {
	return ac.config
}

// IsServerHealthy проверяет, здоров ли сервер
func (ac *APIClient) IsServerHealthy() bool {
	health, err := ac.HealthCheck()
	if err != nil {
		return false
	}
	
	return health.Status == "healthy" || health.Status == "degraded"
}

// GetServerVersion возвращает версию сервера
func (ac *APIClient) GetServerVersion() (string, error) {
	health, err := ac.HealthCheck()
	if err != nil {
		return "", err
	}
	
	return health.Version, nil
}

// GetMaskScore возвращает оценку маскировки сервера
func (ac *APIClient) GetMaskScore() (int, error) {
	health, err := ac.HealthCheck()
	if err != nil {
		return 0, err
	}
	
	return health.MaskScore, nil
}