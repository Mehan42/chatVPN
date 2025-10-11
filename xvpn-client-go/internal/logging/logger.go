package logging

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

// LogEntry представляет запись лога
type LogEntry struct {
	Timestamp time.Time `json:"timestamp"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Component string    `json:"component"`
	File      string    `json:"file"`
	Line      int       `json:"line"`
	Function  string    `json:"function"`
	Data      map[string]interface{} `json:"data,omitempty"`
}

// Logger предоставляет расширенные возможности логирования
type Logger struct {
	loggers map[string]*log.Logger
	mutex   sync.RWMutex
	logDir  string
	enableFileLogging bool
	maxFileSize int64 // в байтах
	currentFileSize int64
}

// NewLogger создает новый экземпляр логгера
func NewLogger(logDir string, enableFileLogging bool) *Logger {
	logger := &Logger{
		loggers: make(map[string]*log.Logger),
		logDir:  logDir,
		enableFileLogging: enableFileLogging,
		maxFileSize: 10 * 1024 * 1024, // 10MB
	}
	
	// Создаем директорию для логов, если она не существует
	if enableFileLogging && logDir != "" {
		os.MkdirAll(logDir, 0755)
	}
	
	return logger
}

// logInternal внутренняя функция логирования
func (l *Logger) logInternal(level, component, format string, args ...interface{}) {
	// Получаем информацию о вызывающем файле и строке
	_, file, line, ok := runtime.Caller(2)
	if !ok {
		file = "unknown"
		line = 0
	}
	
	// Получаем имя функции
	pc, _, _, _ := runtime.Caller(2)
	fn := runtime.FuncForPC(pc)
	funcName := "unknown"
	if fn != nil {
		funcName = fn.Name()
		// Оставляем только имя функции без полного пути
		if lastSlash := strings.LastIndex(funcName, "/"); lastSlash >= 0 {
			funcName = funcName[lastSlash+1:]
		}
		if period := strings.Index(funcName, "."); period >= 0 {
			funcName = funcName[period+1:]
		}
	}
	
	// Создаем сообщение
	message := fmt.Sprintf(format, args...)
	
	// Создаем запись лога
	entry := &LogEntry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Component: component,
		File:      filepath.Base(file),
		Line:      line,
		Function:  funcName,
		Data:      make(map[string]interface{}),
	}
	
	// Записываем в стандартный лог
	l.logToConsole(level, entry)
	
	// Записываем в файл, если включено
	if l.enableFileLogging {
		l.logToFile(entry)
	}
}

// logToConsole записывает лог в консоль
func (l *Logger) logToConsole(level string, entry *LogEntry) {
	logMsg := fmt.Sprintf("[%s] [%s] [%s:%d] %s: %s",
		entry.Timestamp.Format("2006-01-02 15:04:05"),
		level,
		entry.File,
		entry.Line,
		entry.Component,
		entry.Message,
	)
	
	switch level {
	case "ERROR", "FATAL":
		log.SetOutput(os.Stderr)
		log.Printf("%s", logMsg)
	case "WARN":
		log.SetOutput(os.Stderr)
		log.Printf("%s", logMsg)
	default:
		log.SetOutput(os.Stdout)
		log.Printf("%s", logMsg)
	}
}

// logToFile записывает лог в файл
func (l *Logger) logToFile(entry *LogEntry) {
	if l.logDir == "" {
		return
	}
	
	// Создаем имя файла с датой
	logFile := filepath.Join(l.logDir, fmt.Sprintf("xvpn-%s.log", time.Now().Format("2006-01-02")))
	
	// Открываем файл для записи
	file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Printf("Ошибка открытия файла лога: %v", err)
		return
	}
	defer file.Close()
	
	// Преобразуем запись в JSON
	jsonData, err := json.Marshal(entry)
	if err != nil {
		log.Printf("Ошибка сериализации лога в JSON: %v", err)
		return
	}
	
	// Проверяем размер файла и при необходимости архивируем
	l.rotateLogIfNeeded(logFile)
	
	// Записываем строку JSON в файл
	_, err = file.WriteString(string(jsonData) + "\n")
	if err != nil {
		log.Printf("Ошибка записи в файл лога: %v", err)
	}
	
	// Обновляем размер файла
	if stat, err := os.Stat(logFile); err == nil {
		l.currentFileSize = stat.Size()
	}
}

// rotateLogIfNeeded проверяет размер файла и архивирует, если нужно
func (l *Logger) rotateLogIfNeeded(logFile string) {
	if stat, err := os.Stat(logFile); err == nil {
		if stat.Size() > l.maxFileSize {
			// Архивируем текущий файл
			archiveFile := logFile + "." + time.Now().Format("20060102_150405")
			os.Rename(logFile, archiveFile)
		}
	}
}

// AddData добавляет дополнительные данные к записи лога
func (l *Logger) AddData(entry *LogEntry, key string, value interface{}) {
	if entry.Data == nil {
		entry.Data = make(map[string]interface{})
	}
	entry.Data[key] = value
}

// Debug записывает отладочное сообщение
func (l *Logger) Debug(component, format string, args ...interface{}) {
	l.logInternal("DEBUG", component, format, args...)
}

// Info записывает информационное сообщение
func (l *Logger) Info(component, format string, args ...interface{}) {
	l.logInternal("INFO", component, format, args...)
}

// Warn записывает предупреждение
func (l *Logger) Warn(component, format string, args ...interface{}) {
	l.logInternal("WARN", component, format, args...)
}

// Error записывает сообщение об ошибке
func (l *Logger) Error(component, format string, args ...interface{}) {
	l.logInternal("ERROR", component, format, args...)
}

// Fatal записывает сообщение об ошибке и завершает программу
func (l *Logger) Fatal(component, format string, args ...interface{}) {
	l.logInternal("FATAL", component, format, args...)
	os.Exit(1)
}

// WithData создает временную запись лога с дополнительными данными
func (l *Logger) WithData(component string, data map[string]interface{}) *LogEntry {
	return &LogEntry{
		Timestamp: time.Now(),
		Component: component,
		Data:      data,
	}
}

// LogEntry записывает специфичную запись лога
func (l *Logger) LogEntry(entry *LogEntry) {
	// Записываем в стандартный лог
	logMsg := fmt.Sprintf("[%s] [%s] [%s:%d] %s: %s",
		entry.Timestamp.Format("2006-01-02 15:04:05"),
		entry.Level,
		entry.File,
		entry.Line,
		entry.Component,
		entry.Message,
	)
	log.Println(logMsg)
	
	// Записываем в файл, если включено
	if l.enableFileLogging {
		l.logToFile(entry)
	}
}