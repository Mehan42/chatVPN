// Package tunnelverifier provides enhanced logging functionality
package tunnelverifier

import (
	"log"
	"os"
	"fmt"
	"time"
	"strings"
	"encoding/json"
)

// LogLevel defines the level of logging
type LogLevel int

const (
	Debug LogLevel = iota
	Info
	Warn
	Error
)

// String returns the string representation of a LogLevel
func (l LogLevel) String() string {
	switch l {
	case Debug:
		return "DEBUG"
	case Info:
		return "INFO"
	case Warn:
		return "WARN"
	case Error:
		return "ERROR"
	default:
		return "UNKNOWN"
	}
}

// Logger provides enhanced logging functionality
type Logger struct {
	level      LogLevel
	logWriter  *log.Logger
	enableJSON bool
}

// NewLogger creates a new enhanced logger
func NewLogger(level LogLevel, enableJSON bool) *Logger {
	return &Logger{
		level:      level,
		logWriter:  log.New(os.Stdout, "", log.LstdFlags|log.Lshortfile),
		enableJSON: enableJSON,
	}
}

// SetLevel sets the logging level
func (l *Logger) SetLevel(level LogLevel) {
	l.level = level
}

// Log logs a message at the specified level
func (l *Logger) Log(level LogLevel, msg string, fields map[string]interface{}) {
	if level < l.level {
		return
	}
	
	if l.enableJSON {
		l.logJSON(level, msg, fields)
	} else {
		l.logText(level, msg, fields)
	}
}

// logText logs a message in text format
func (l *Logger) logText(level LogLevel, msg string, fields map[string]interface{}) {
	var fieldStr string
	if len(fields) > 0 {
		var parts []string
		for k, v := range fields {
			parts = append(parts, fmt.Sprintf("%s=%v", k, v))
		}
		fieldStr = " [" + strings.Join(parts, " ") + "]"
	}
	
	l.logWriter.Printf("[%s] %s%s", level.String(), msg, fieldStr)
}

// logJSON logs a message in JSON format
func (l *Logger) logJSON(level LogLevel, msg string, fields map[string]interface{}) {
	logEntry := map[string]interface{}{
		"timestamp": time.Now().Format(time.RFC3339),
		"level":     level.String(),
		"message":   msg,
	}
	
	for k, v := range fields {
		logEntry[k] = v
	}
	
	jsonBytes, err := json.Marshal(logEntry)
	if err != nil {
		l.logWriter.Printf("[%s] Error marshaling log entry: %v", Error.String(), err)
		return
	}
	
	l.logWriter.Printf("%s", string(jsonBytes))
}

// Debug logs a debug message
func (l *Logger) Debug(msg string, fields map[string]interface{}) {
	l.Log(Debug, msg, fields)
}

// Info logs an info message
func (l *Logger) Info(msg string, fields map[string]interface{}) {
	l.Log(Info, msg, fields)
}

// Warn logs a warning message
func (l *Logger) Warn(msg string, fields map[string]interface{}) {
	l.Log(Warn, msg, fields)
}

// Error logs an error message
func (l *Logger) Error(msg string, fields map[string]interface{}) {
	l.Log(Error, msg, fields)
}