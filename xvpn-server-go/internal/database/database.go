package database

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	"xvpn-server-go/internal/config"

	_ "github.com/mattn/go-sqlite3"
)

// Database представляет подключение к базе данных
type Database struct {
	*sql.DB
}

// Client представляет VPN клиента
type Client struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	UUID      string    `json:"uuid"`
	Config    string    `json:"config"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Status    string    `json:"status"`
}

// LogEntry представляет запись лога
type LogEntry struct {
	ID        int       `json:"id"`
	Timestamp time.Time `json:"timestamp"`
	Level     string    `json:"level"`
	Component string    `json:"component"`
	Message   string    `json:"message"`
	Data      string    `json:"data"`
}

// New создает новое подключение к базе данных
func New(cfg config.DatabaseConfig) (*Database, error) {
	db, err := sql.Open("sqlite3", cfg.Path)
	if err != nil {
		return nil, fmt.Errorf("ошибка открытия базы данных: %w", err)
	}

	// Проверка подключения
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("ошибка подключения к базе данных: %w", err)
	}

	database := &Database{db}

	// Создание таблиц
	if err := database.createTables(); err != nil {
		return nil, fmt.Errorf("ошибка создания таблиц: %w", err)
	}

	log.Printf("✅ Подключение к базе данных установлено: %s", cfg.Path)
	return database, nil
}

// createTables создает необходимые таблицы
func (d *Database) createTables() error {
	queries := []string{
		`CREATE TABLE IF NOT EXISTS clients (
			id TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			uuid TEXT UNIQUE NOT NULL,
			config TEXT NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			status TEXT DEFAULT 'active'
		)`,
		`CREATE TABLE IF NOT EXISTS logs (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
			level TEXT NOT NULL,
			component TEXT NOT NULL,
			message TEXT NOT NULL,
			data TEXT
		)`,
		`CREATE TABLE IF NOT EXISTS transports (
			id TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			protocol TEXT NOT NULL,
			config TEXT NOT NULL,
			priority INTEGER DEFAULT 0,
			enabled BOOLEAN DEFAULT 1,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE INDEX IF NOT EXISTS idx_clients_uuid ON clients(uuid)`,
		`CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)`,
		`CREATE INDEX IF NOT EXISTS idx_logs_component ON logs(component)`,
	}

	for _, query := range queries {
		if _, err := d.Exec(query); err != nil {
			return fmt.Errorf("ошибка выполнения запроса: %s, ошибка: %w", query, err)
		}
	}

	return nil
}

// GetClient получает клиента по UUID
func (d *Database) GetClient(uuid string) (*Client, error) {
	query := `SELECT id, name, uuid, config, created_at, updated_at, status
	          FROM clients WHERE uuid = ?`

	var client Client
	err := d.QueryRow(query, uuid).Scan(
		&client.ID,
		&client.Name,
		&client.UUID,
		&client.Config,
		&client.CreatedAt,
		&client.UpdatedAt,
		&client.Status,
	)

	if err != nil {
		return nil, fmt.Errorf("ошибка получения клиента: %w", err)
	}

	return &client, nil
}

// SaveClient сохраняет или обновляет клиента
func (d *Database) SaveClient(client *Client) error {
	query := `INSERT OR REPLACE INTO clients
	          (id, name, uuid, config, updated_at, status)
	          VALUES (?, ?, ?, ?, ?, ?)`

	_, err := d.Exec(query,
		client.ID,
		client.Name,
		client.UUID,
		client.Config,
		time.Now(),
		client.Status,
	)

	if err != nil {
		return fmt.Errorf("ошибка сохранения клиента: %w", err)
	}

	return nil
}

// Log записывает сообщение в лог
func (d *Database) Log(level, component, message string, data interface{}) error {
	var dataStr string
	if data != nil {
		dataStr = fmt.Sprintf("%v", data)
	}

	query := `INSERT INTO logs (level, component, message, data) VALUES (?, ?, ?, ?)`
	_, err := d.Exec(query, level, component, message, dataStr)

	if err != nil {
		return fmt.Errorf("ошибка записи в лог: %w", err)
	}

	return nil
}

// GetRecentLogs получает последние записи лога
func (d *Database) GetRecentLogs(limit int) ([]LogEntry, error) {
	query := `SELECT id, timestamp, level, component, message, data
	          FROM logs ORDER BY timestamp DESC LIMIT ?`

	rows, err := d.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("ошибка получения логов: %w", err)
	}
	defer rows.Close()

	var logs []LogEntry
	for rows.Next() {
		var logEntry LogEntry
		err := rows.Scan(
			&logEntry.ID,
			&logEntry.Timestamp,
			&logEntry.Level,
			&logEntry.Component,
			&logEntry.Message,
			&logEntry.Data,
		)
		if err != nil {
			return nil, fmt.Errorf("ошибка сканирования лога: %w", err)
		}
		logs = append(logs, logEntry)
	}

	return logs, nil
}

// Close закрывает подключение к базе данных
func (d *Database) Close() error {
	if d.DB != nil {
		log.Println("🔌 Закрытие подключения к базе данных")
		return d.DB.Close()
	}
	return nil
}
