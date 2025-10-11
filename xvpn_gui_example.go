package main

import (
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/data/binding"
	"fmt"
	"time"
)

// GUIApp представляет основное GUI приложение
type GUIApp struct {
	app           app.App
	window        fyne.Window
	stateMachine  *VPNStateMachine
	statusLabel   *widget.Label
	ipLabel       *widget.Label
	securityLabel *widget.Label
	securityValue *widget.Label
	toggleButton  *widget.Button
	fetchButton   *widget.Button
	uuidButton    *widget.Button
	speedLabel    *widget.Label
	securityGauge *widget.Entry // Используем Entry для отображения цветного индикатора
}

// NewGUIApp создает новое GUI приложение
func NewGUIApp(stateMachine *VPNStateMachine) *GUIApp {
	myApp := app.New()
	myWindow := myApp.NewWindow("XVPN Client")
	myWindow.Resize(fyne.NewSize(400, 300))

	gui := &GUIApp{
		app:          myApp,
		window:       myWindow,
		stateMachine: stateMachine,
	}

	// Создаем виджеты
	gui.statusLabel = widget.NewLabel("Статус: OFF")
	gui.ipLabel = widget.NewLabel("IP: -")
	gui.securityLabel = widget.NewLabel("Безопасность:")
	gui.securityValue = widget.NewLabel("Оценка: -")
	gui.securityGauge = widget.NewEntry()
	gui.securityGauge.Disable()
	gui.speedLabel = widget.NewLabel("Скорость: 0 ↓ / 0 ↑ КБ/с")
	gui.toggleButton = widget.NewButton("Включить VPN", func() {
		gui.onToggle()
	})
	gui.fetchButton = widget.NewButton("Запросить конфиг", func() {
		gui.onFetchConfig()
	})
	gui.uuidButton = widget.NewButton("Сменить UUID", func() {
		gui.onChangeUUID()
	})

	// Макет интерфейса
	content := container.NewVBox(
		gui.statusLabel,
		gui.ipLabel,
		container.NewHBox(
			gui.securityLabel,
			gui.securityValue,
			gui.securityGauge,
		),
		gui.speedLabel,
		gui.toggleButton,
		gui.fetchButton,
		gui.uuidButton,
	)

	myWindow.SetContent(content)

	// Запускаем обновление статуса
	go gui.refreshStatusLoop()

	return gui
}

// onToggle обрабатывает нажатие кнопки переключения VPN
func (gui *GUIApp) onToggle() {
	if gui.stateMachine.context.CurrentState == StateRunning {
		gui.stateMachine.TriggerEvent(EventStopRequested)
		dialog.ShowInformation("XVPN", "VPN останавливается...", gui.window)
	} else {
		gui.stateMachine.TriggerEvent(EventStartRequested)
		dialog.ShowInformation("XVPN", "VPN запускается...", gui.window)
	}
}

// onFetchConfig обрабатывает нажатие кнопки получения конфига
func (gui *GUIApp) onFetchConfig() {
	gui.stateMachine.TriggerEvent(EventStartRequested)
	dialog.ShowInformation("XVPN", "Конфигурация обновляется...", gui.window)
}

// onChangeUUID обрабатывает смену UUID
func (gui *GUIApp) onChangeUUID() {
	// В реальном приложении здесь будет диалог ввода
	newUUID := "new-test-uuid-12345"
	dialog.ShowInformation("XVPN", fmt.Sprintf("UUID изменён на:\n%s", newUUID), gui.window)
}

// updateSecurityGauge обновляет индикатор безопасности
func (gui *GUIApp) updateSecurityGauge(healthScore int) {
	// Устанавливаем цвет индикатора в зависимости от оценки
	var color string
	var statusText string
	
	switch {
	case healthScore >= 4:
		color = "green"
		statusText = "Отлично"
	case healthScore >= 3:
		color = "yellow"
		statusText = "Хорошо"
	case healthScore >= 1:
		color = "orange"
		statusText = "Внимание"
	default:
		color = "red"
		statusText = "Критично"
	}
	
	gui.securityGauge.Text = fmt.Sprintf("●") // Символ для индикатора
	gui.securityGauge.PlaceHolder = statusText
	gui.securityValue.SetText(fmt.Sprintf("Оценка: %d/5 (%s)", healthScore, statusText))
	
	// В реальном приложении здесь нужно установить цвет текста
}

// refreshStatus обновляет статус на основе состояния машины
func (gui *GUIApp) refreshStatus() {
	stateInfo := gui.stateMachine.GetStateInfo()
	
	// Обновляем статус
	if stateInfo["current_state"] == StateRunning {
		gui.statusLabel.SetText("Статус: ON")
		gui.toggleButton.SetText("Выключить VPN")
	} else {
		gui.statusLabel.SetText("Статус: OFF")
		gui.toggleButton.SetText("Включить VPN")
	}
	
	// Обновляем IP (в реальном приложении будет реальный IP)
	gui.ipLabel.SetText("IP: 203.0.113.10")
	
	// Обновляем оценку безопасности
	if healthScore, ok := stateInfo["health_score"].(int); ok {
		gui.updateSecurityGauge(healthScore)
	}
	
	// Обновляем скорость (в реальном приложении будет реальная скорость)
	gui.speedLabel.SetText("Скорость: 15.2 ↓ / 8.7 ↑ МБ/с")
}

// refreshStatusLoop циклически обновляет статус
func (gui *GUIApp) refreshStatusLoop() {
	for {
		time.Sleep(5 * time.Second)
		// Обновляем в главной горутине GUI
		gui.window.Canvas().SetOnTypedKey(func(key *fyne.KeyEvent) {
			// Обновляем статус
			gui.refreshStatus()
		})
		
		// Вызываем обновление статуса
		gui.window.Canvas().Content().Refresh()
		gui.refreshStatus()
	}
}

// Run запускает GUI приложение
func (gui *GUIApp) Run() {
	gui.window.ShowAndRun()
}

// main функция для запуска GUI приложения
func main() {
	// Создаем машину состояний
	clientUUID := "test-gui-client-uuid"
	stateMachine := NewVPNStateMachine(clientUUID)
	
	// Запускаем машину состояний
	stateMachine.Start()
	
	// Создаем и запускаем GUI
	guiApp := NewGUIApp(stateMachine)
	
	// Запускаем GUI
	guiApp.Run()
	
	// При закрытии останавливаем машину состояний
	stateMachine.Stop()
}