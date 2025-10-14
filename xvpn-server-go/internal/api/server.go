package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"

	"xvpn-server-go/internal/config"
	"xvpn-server-go/internal/database"
	"xvpn-server-go/internal/telegram"
)

// Server представляет API сервер
type Server struct {
	config  config.APIConfig
	db      *database.Database
	bot     *telegram.Bot
	handler http.Handler
}

// NewServer создает новый API сервер
func NewServer(cfg config.APIConfig, db *database.Database, bot *telegram.Bot) *Server {
	server := &Server{
		config: cfg,
		db:     db,
		bot:    bot,
	}

	server.handler = server.setupRoutes()
	return server
}

// Router возвращает HTTP роутер сервера
func (s *Server) Router() http.Handler {
	return s.handler
}

// setupRoutes настраивает маршруты API
func (s *Server) setupRoutes() http.Handler {
	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("/health", s.handleHealth)

	// Metrics endpoints
	mux.HandleFunc("/metrics", s.handleMetrics)
	mux.HandleFunc("/metrics/json", s.handleMetricsJSON)

	// Client management
	mux.HandleFunc("/clients/", s.handleClients)

	// Transport management
	mux.HandleFunc("/transports/", s.handleTransports)

	// Admin endpoints
	mux.HandleFunc("/admin/", s.handleAdmin)

	// MCP endpoints (Model Context Protocol)
	mux.HandleFunc("/mcp/v1/", s.handleMCP)

	return mux
}

// handleHealth обрабатывает запросы health check
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	response := map[string]interface{}{
		"status":    "healthy",
		"version":   "1.0.0",
		"timestamp": "2025-10-14T12:00:00Z",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	s.db.Log("INFO", "api", "Health check requested", nil)
}

// handleClients обрабатывает запросы управления клиентами
func (s *Server) handleClients(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/clients/")

	switch r.Method {
	case http.MethodGet:
		s.handleGetClient(w, r, path)
	case http.MethodPost:
		s.handleCreateClient(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleGetClient получает конфигурацию клиента
func (s *Server) handleGetClient(w http.ResponseWriter, r *http.Request, uuid string) {
	if uuid == "" {
		http.Error(w, "UUID required", http.StatusBadRequest)
		return
	}

	client, err := s.db.GetClient(uuid)
	if err != nil {
		log.Printf("Error getting client %s: %v", uuid, err)
		http.Error(w, "Client not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(client)

	s.db.Log("INFO", "api", fmt.Sprintf("Client config served for UUID: %s", uuid), nil)
}

// handleCreateClient создает нового клиента
func (s *Server) handleCreateClient(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name string `json:"name"`
		UUID string `json:"uuid"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.Name == "" || req.UUID == "" {
		http.Error(w, "Name and UUID required", http.StatusBadRequest)
		return
	}

	client := &database.Client{
		ID:     req.UUID,
		Name:   req.Name,
		UUID:   req.UUID,
		Config: "{}",
		Status: "active",
	}

	if err := s.db.SaveClient(client); err != nil {
		log.Printf("Error saving client: %v", err)
		http.Error(w, "Failed to create client", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(client)

	s.db.Log("INFO", "api", fmt.Sprintf("New client created: %s", req.Name), req)
}

// handleTransports обрабатывает запросы управления транспортами
func (s *Server) handleTransports(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Пока возвращаем статичный манифест
	manifest := map[string]interface{}{
		"version": "1.0",
		"transports": []map[string]interface{}{
			{
				"id":       "vless-reality",
				"name":     "VLESS+Reality",
				"protocol": "vless",
				"priority": 1,
				"config": map[string]interface{}{
					"server":   "your-server.com",
					"port":     443,
					"id":       "uuid-here",
					"security": "reality",
				},
			},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(manifest)

	s.db.Log("INFO", "api", "Transport manifest served", nil)
}

// handleAdmin обрабатывает административные запросы
func (s *Server) handleAdmin(w http.ResponseWriter, r *http.Request) {
	// Простая аутентификация через токен
	token := r.Header.Get("Authorization")
	if !strings.HasPrefix(token, "Bearer ") {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	token = strings.TrimPrefix(token, "Bearer ")
	if token != "admin-token" { // В продакшене использовать реальную проверку
		http.Error(w, "Invalid token", http.StatusUnauthorized)
		return
	}

	path := strings.TrimPrefix(r.URL.Path, "/admin/")

	switch {
	case strings.HasPrefix(path, "clients"):
		s.handleAdminClients(w, r)
	case strings.HasPrefix(path, "stats"):
		s.handleAdminStats(w, r)
	default:
		http.Error(w, "Not found", http.StatusNotFound)
	}
}

// handleAdminClients обрабатывает административные запросы клиентов
func (s *Server) handleAdminClients(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Получить список всех клиентов (упрощенная версия)
	clients := []database.Client{
		{
			ID:     "test-uuid",
			Name:   "Test Client",
			UUID:   "test-uuid",
			Status: "active",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"clients": clients,
	})
}

// handleAdminStats возвращает статистику сервера
func (s *Server) handleAdminStats(w http.ResponseWriter, r *http.Request) {
	stats := map[string]interface{}{
		"total_clients":  1,
		"active_clients": 1,
		"uptime":         "1h 30m",
		"version":        "1.0.0",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// handleMCP обрабатывает MCP (Model Context Protocol) запросы
func (s *Server) handleMCP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/mcp/v1/")

	switch path {
	case "vpn.health":
		s.handleMCPHealth(w, r)
	case "admin.newclient":
		s.handleMCPNewClient(w, r)
	default:
		http.Error(w, "MCP endpoint not found", http.StatusNotFound)
	}
}

// handleMCPHealth возвращает статус здоровья VPN
func (s *Server) handleMCPHealth(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":      "operational",
		"connections": 1,
		"last_check":  "2025-10-14T12:00:00Z",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleMCPNewClient создает нового клиента через MCP
func (s *Server) handleMCPNewClient(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Name string `json:"name"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Генерация UUID (упрощенная версия)
	uuid := fmt.Sprintf("client-%d", 123456)

	client := &database.Client{
		ID:     uuid,
		Name:   req.Name,
		UUID:   uuid,
		Config: "{}",
		Status: "active",
	}

	if err := s.db.SaveClient(client); err != nil {
		log.Printf("Error saving client via MCP: %v", err)
		http.Error(w, "Failed to create client", http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"success": true,
		"client":  client,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	s.db.Log("INFO", "mcp", fmt.Sprintf("New client created via MCP: %s", req.Name), req)
}
