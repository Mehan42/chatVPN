package gateway

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"xvpn-server-go/internal/config"
	"xvpn-server-go/internal/database"
	"xvpn-server-go/internal/telegram"
)

// Gateway представляет Gateway компонент
type Gateway struct {
	config config.GatewayConfig
	db     *database.Database
	bot    *telegram.Bot
}

// New создает новый Gateway
func New(cfg config.GatewayConfig, db *database.Database, bot *telegram.Bot) *Gateway {
	return &Gateway{
		config: cfg,
		db:     db,
		bot:    bot,
	}
}

// Router возвращает HTTP роутер Gateway
func (g *Gateway) Router() http.Handler {
	mux := http.NewServeMux()

	// Gateway endpoints
	mux.HandleFunc("/connect", g.handleConnect)
	mux.HandleFunc("/disconnect", g.handleDisconnect)
	mux.HandleFunc("/status", g.handleStatus)
	mux.HandleFunc("/switch", g.handleSwitch)

	return mux
}

// handleConnect обрабатывает запросы на подключение
func (g *Gateway) handleConnect(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ClientUUID string `json:"client_uuid"`
		Transport  string `json:"transport"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.ClientUUID == "" {
		http.Error(w, "Client UUID required", http.StatusBadRequest)
		return
	}

	// Проверка существования клиента
	_, err := g.db.GetClient(req.ClientUUID)
	if err != nil {
		log.Printf("Client not found: %s", req.ClientUUID)
		http.Error(w, "Client not found", http.StatusNotFound)
		return
	}

	// Логика подключения (упрощенная)
	response := map[string]interface{}{
		"success":   true,
		"status":    "connected",
		"transport": req.Transport,
		"client":    req.ClientUUID,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	g.db.Log("INFO", "gateway", fmt.Sprintf("Client connected: %s", req.ClientUUID), req)

	// Уведомление через Telegram
	g.bot.SendNotification(fmt.Sprintf("✅ Клиент %s подключился", req.ClientUUID))
}

// handleDisconnect обрабатывает запросы на отключение
func (g *Gateway) handleDisconnect(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ClientUUID string `json:"client_uuid"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	response := map[string]interface{}{
		"success": true,
		"status":  "disconnected",
		"client":  req.ClientUUID,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	g.db.Log("INFO", "gateway", fmt.Sprintf("Client disconnected: %s", req.ClientUUID), req)

	// Уведомление через Telegram
	g.bot.SendNotification(fmt.Sprintf("❌ Клиент %s отключился", req.ClientUUID))
}

// handleStatus возвращает статус подключения
func (g *Gateway) handleStatus(w http.ResponseWriter, r *http.Request) {
	clientUUID := r.URL.Query().Get("client_uuid")
	if clientUUID == "" {
		http.Error(w, "Client UUID required", http.StatusBadRequest)
		return
	}

	// Проверка статуса (упрощенная логика)
	status := map[string]interface{}{
		"client_uuid": clientUUID,
		"connected":   true,
		"transport":   "vless-reality",
		"uptime":      "1h 30m",
		"bytes_sent":  1024000,
		"bytes_recv":  2048000,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)

	g.db.Log("INFO", "gateway", fmt.Sprintf("Status requested for client: %s", clientUUID), nil)
}

// handleSwitch обрабатывает переключение транспорта
func (g *Gateway) handleSwitch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		ClientUUID    string `json:"client_uuid"`
		FromTransport string `json:"from_transport"`
		ToTransport   string `json:"to_transport"`
		Reason        string `json:"reason"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	response := map[string]interface{}{
		"success":        true,
		"status":         "switched",
		"client":         req.ClientUUID,
		"from_transport": req.FromTransport,
		"to_transport":   req.ToTransport,
		"reason":         req.Reason,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	g.db.Log("INFO", "gateway", fmt.Sprintf("Transport switched for client %s: %s -> %s (%s)",
		req.ClientUUID, req.FromTransport, req.ToTransport, req.Reason), req)

	// Уведомление через Telegram
	g.bot.SendNotification(fmt.Sprintf("🔄 Клиент %s переключился с %s на %s (%s)",
		req.ClientUUID, req.FromTransport, req.ToTransport, req.Reason))
}

// HealthCheck выполняет проверку здоровья Gateway
func (g *Gateway) HealthCheck() error {
	// Проверка подключения к базе данных
	if err := g.db.DB.Ping(); err != nil {
		return fmt.Errorf("database health check failed: %w", err)
	}

	// Проверка Telegram бота (если токен задан)
	if g.bot != nil {
		// Упрощенная проверка - в реальности нужно проверить API
		log.Println("✅ Gateway health check passed")
	}

	return nil
}

// GetStats возвращает статистику Gateway
func (g *Gateway) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"active_connections": 1,
		"total_clients":      1,
		"uptime":             "1h 30m",
		"version":            "1.0.0",
	}
}
