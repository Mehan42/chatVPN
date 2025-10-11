package alerts

import (
	"fmt"
	"log"
	"time"
)

// AlertType тип алерта
type AlertType string

const (
	AlertInfo    AlertType = "info"
	AlertWarning AlertType = "warning"
	AlertError   AlertType = "error"
	AlertCritical AlertType = "critical"
)

// AlertSeverity уровень важности алерта
type AlertSeverity int

const (
	SeverityLow    AlertSeverity = iota // Низкая
	SeverityMedium                      // Средняя
	SeverityHigh                        // Высокая
	SeverityCritical                    // Критическая
)

// Alert представляет собой уведомление
type Alert struct {
	ID          string        `json:"id"`
	Type        AlertType     `json:"type"`
	Title       string        `json:"title"`
	Message     string        `json:"message"`
	Severity    AlertSeverity `json:"severity"`
	Timestamp   time.Time     `json:"timestamp"`
	Dismissed   bool          `json:"dismissed"`
	AutoDismiss bool          `json:"auto_dismiss"`
	Duration    time.Duration `json:"duration"` // Длительность отображения
	Actions     []AlertAction `json:"actions"`  // Возможные действия
}

// AlertAction действие, которое можно выполнить при алерте
type AlertAction struct {
	Label   string `json:"label"`
	Command string `json:"command"`
}

// NotificationManager управляет уведомлениями
type NotificationManager struct {
	alerts        []Alert
	maxAlerts     int
	autoDismiss   bool
	showInTray    bool
	showInDesktop bool
	logger        *log.Logger
}

// NewNotificationManager создает новый менеджер уведомлений
func NewNotificationManager() *NotificationManager {
	return &NotificationManager{
		alerts:        make([]Alert, 0, 100), // Максимум 100 алертов в памяти
		maxAlerts:     100,
		autoDismiss:   true,
		showInTray:    true,
		showInDesktop: true,
		logger:        log.Default(),
	}
}

// ShowAlert показывает уведомление
func (nm *NotificationManager) ShowAlert(alertType AlertType, title, message string, severity AlertSeverity) string {
	alert := Alert{
		ID:          fmt.Sprintf("alert_%d", time.Now().UnixNano()),
		Type:        alertType,
		Title:       title,
		Message:     message,
		Severity:    severity,
		Timestamp:   time.Now(),
		Dismissed:   false,
		AutoDismiss: nm.autoDismiss,
		Duration:    nm.getDefaultDuration(severity),
		Actions:     make([]AlertAction, 0),
	}
	
	// Добавляем алерт в список
	nm.alerts = append(nm.alerts, alert)
	
	// Ограничиваем количество алертов
	if len(nm.alerts) > nm.maxAlerts {
		// Удаляем самый старый алерт
		nm.alerts = nm.alerts[1:]
	}
	
	// Отображаем уведомление
	nm.displayAlert(&alert)
	
	// Запускаем автоматическое закрытие, если включено
	if alert.AutoDismiss && alert.Duration > 0 {
		go nm.scheduleAutoDismiss(alert.ID, alert.Duration)
	}
	
	nm.logger.Printf("Показан алерт: %s - %s", title, message)
	return alert.ID
}

// getDefaultDuration возвращает длительность отображения по умолчанию
func (nm *NotificationManager) getDefaultDuration(severity AlertSeverity) time.Duration {
	switch severity {
	case SeverityLow:
		return 3 * time.Second
	case SeverityMedium:
		return 5 * time.Second
	case SeverityHigh:
		return 10 * time.Second
	case SeverityCritical:
		return 30 * time.Second
	default:
		return 5 * time.Second
	}
}

// displayAlert отображает алерт в зависимости от настроек
func (nm *NotificationManager) displayAlert(alert *Alert) {
	// В реальной реализации здесь будет отображение в GUI
	// Для имитации просто логируем
	
	log.Printf("ALERT [%s]: %s - %s", alert.Type, alert.Title, alert.Message)
	
	// Если включено отображение в трее
	if nm.showInTray {
		nm.showTrayNotification(alert)
	}
	
	// Если включено отображение на рабочем столе
	if nm.showInDesktop {
		nm.showDesktopNotification(alert)
	}
}

// showTrayNotification показывает уведомление в трее
func (nm *NotificationManager) showTrayNotification(alert *Alert) {
	// В реальной реализации здесь будет интеграция с системным треем
	log.Printf("Tray notification: %s - %s", alert.Title, alert.Message)
}

// showDesktopNotification показывает уведомление на рабочем столе
func (nm *NotificationManager) showDesktopNotification(alert *Alert) {
	// В реальной реализации здесь будет интеграция с системными уведомлениями
	log.Printf("Desktop notification: %s - %s", alert.Title, alert.Message)
}

// scheduleAutoDismiss планирует автоматическое закрытие алерта
func (nm *NotificationManager) scheduleAutoDismiss(alertID string, duration time.Duration) {
	time.Sleep(duration)
	nm.DismissAlert(alertID)
}

// DismissAlert закрывает (скрывает) алерт
func (nm *NotificationManager) DismissAlert(alertID string) bool {
	for i := range nm.alerts {
		if nm.alerts[i].ID == alertID && !nm.alerts[i].Dismissed {
			nm.alerts[i].Dismissed = true
			nm.logger.Printf("Алерт %s закрыт", alertID)
			return true
		}
	}
	return false
}

// DismissAllAlerts закрывает все алерты
func (nm *NotificationManager) DismissAllAlerts() int {
	count := 0
	for i := range nm.alerts {
		if !nm.alerts[i].Dismissed {
			nm.alerts[i].Dismissed = true
			count++
		}
	}
	nm.logger.Printf("Закрыто %d алертов", count)
	return count
}

// GetActiveAlerts возвращает все активные (не закрытые) алерты
func (nm *NotificationManager) GetActiveAlerts() []Alert {
	activeAlerts := make([]Alert, 0)
	for _, alert := range nm.alerts {
		if !alert.Dismissed {
			activeAlerts = append(activeAlerts, alert)
		}
	}
	return activeAlerts
}

// GetAlertByID возвращает алерт по ID
func (nm *NotificationManager) GetAlertByID(alertID string) (*Alert, bool) {
	for _, alert := range nm.alerts {
		if alert.ID == alertID {
			return &alert, true
		}
	}
	return nil, false
}

// AddAction добавляет действие к алерту
func (nm *NotificationManager) AddAction(alertID string, action AlertAction) bool {
	for i := range nm.alerts {
		if nm.alerts[i].ID == alertID {
			nm.alerts[i].Actions = append(nm.alerts[i].Actions, action)
			return true
		}
	}
	return false
}

// ShowCriticalAlert показывает критическое уведомление с подтверждением
func (nm *NotificationManager) ShowCriticalAlert(title, message string) bool {
	// В реальной реализации здесь будет диалог с подтверждением
	log.Printf("CRITICAL ALERT: %s - %s", title, message)
	
	// Имитация подтверждения пользователя (всегда true для демонстрации)
	return true
}

// ShowWarningAlert показывает предупреждение с возможными действиями
func (nm *NotificationManager) ShowWarningAlert(title, message string, actions []AlertAction) string {
	// В реальной реализации здесь будет диалог с выбором действий
	log.Printf("WARNING ALERT: %s - %s", title, message)
	
	// Имитация выбора действия (всегда первое действие для демонстрации)
	if len(actions) > 0 {
		return actions[0].Command
	}
	
	return ""
}

// ShowInfoNotification показывает информационное уведомление
func (nm *NotificationManager) ShowInfoNotification(title, message string) {
	nm.ShowAlert(AlertInfo, title, message, SeverityLow)
}

// ShowErrorNotification показывает уведомление об ошибке
func (nm *NotificationManager) ShowErrorNotification(title, message string) {
	nm.ShowAlert(AlertError, title, message, SeverityHigh)
}

// ShowConnectionAlert показывает уведомление о состоянии соединения
func (nm *NotificationManager) ShowConnectionAlert(connected bool, server string) {
	if connected {
		nm.ShowAlert(AlertInfo, "VPN Подключен", fmt.Sprintf("VPN подключен к серверу %s", server), SeverityLow)
	} else {
		nm.ShowAlert(AlertWarning, "VPN Отключен", "VPN соединение потеряно", SeverityHigh)
	}
}

// ShowHealthAlert показывает уведомление о состоянии здоровья
func (nm *NotificationManager) ShowHealthAlert(score int) {
	if score >= 4 {
		nm.ShowAlert(AlertInfo, "Отличное состояние", "VPN в отличном состоянии", SeverityLow)
	} else if score >= 3 {
		nm.ShowAlert(AlertInfo, "Хорошее состояние", "VPN в хорошем состоянии", SeverityLow)
	} else if score >= 2 {
		nm.ShowAlert(AlertWarning, "Среднее состояние", "VPN в среднем состоянии, рекомендуется проверка", SeverityMedium)
	} else {
		nm.ShowAlert(AlertError, "Плохое состояние", "VPN в плохом состоянии, требуется немедленное внимание", SeverityHigh)
	}
}

// ShowTransportSwitchAlert показывает уведомление о переключении транспорта
func (nm *NotificationManager) ShowTransportSwitchAlert(oldTransport, newTransport string) {
	message := fmt.Sprintf("Переключение с %s на %s", oldTransport, newTransport)
	nm.ShowAlert(AlertInfo, "Переключение транспорта", message, SeverityLow)
}

// ShowSecurityAlert показывает уведомление о проблемах безопасности
func (nm *NotificationManager) ShowSecurityAlert(issue string) {
	nm.ShowAlert(AlertCritical, "Проблема безопасности", fmt.Sprintf("Обнаружена проблема безопасности: %s", issue), SeverityCritical)
}

// ShowUpdateAvailableAlert показывает уведомление о доступном обновлении
func (nm *NotificationManager) ShowUpdateAvailableAlert(version string) {
	message := fmt.Sprintf("Доступно обновление до версии %s", version)
	action := AlertAction{
		Label:   "Обновить",
		Command: "update_client",
	}
	
	alertID := nm.ShowAlert(AlertInfo, "Обновление доступно", message, SeverityMedium)
	nm.AddAction(alertID, action)
}

// CleanOldAlerts очищает старые алерты
func (nm *NotificationManager) CleanOldAlerts(maxAge time.Duration) int {
	now := time.Now()
	count := 0
	
	// Помечаем старые алерты как закрытые
	for i := range nm.alerts {
		if !nm.alerts[i].Dismissed && now.Sub(nm.alerts[i].Timestamp) > maxAge {
			nm.alerts[i].Dismissed = true
			count++
		}
	}
	
	// Удаляем слишком старые алерты из памяти
	cutoffTime := now.Add(-24 * time.Hour) // Удаляем алерты старше 24 часов
	filteredAlerts := make([]Alert, 0)
	
	for _, alert := range nm.alerts {
		if alert.Timestamp.After(cutoffTime) {
			filteredAlerts = append(filteredAlerts, alert)
		}
	}
	
	removed := len(nm.alerts) - len(filteredAlerts)
	nm.alerts = filteredAlerts
	
	if removed > 0 {
		nm.logger.Printf("Удалено %d старых алертов", removed)
	}
	
	return count
}

// SetAutoDismiss устанавливает автоматическое закрытие алертов
func (nm *NotificationManager) SetAutoDismiss(enabled bool) {
	nm.autoDismiss = enabled
}

// SetShowInTray устанавливает отображение алертов в трее
func (nm *NotificationManager) SetShowInTray(enabled bool) {
	nm.showInTray = enabled
}

// SetShowInDesktop устанавливает отображение алертов на рабочем столе
func (nm *NotificationManager) SetShowInDesktop(enabled bool) {
	nm.showInDesktop = enabled
}