package gui

import (
	"fmt"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
	"fyne.io/fyne/v2/data/binding"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/layout"
	"xvpn-client-go/internal/state"
	"xvpn-client-go/internal/geoip"
)

// AppGUI представляет основной GUI приложения
type AppGUI struct {
	app           app.App
	window        interface{} // Это будет fyne.Window, но мы используем interface{} чтобы избежать прямой зависимости
	stateMachine  *state.VPNStateMachine
	trafficRouter *geoip.TrafficRouter
	
	// Виджеты интерфейса
	statusLabel     *widget.Label
	ipLabel         *widget.Label
	securityLabel   *widget.Label
	securityValue   *widget.Label
	securityBar     *widget.Entry
	speedLabel      *widget.Label
	toggleButton    *widget.Button
	fetchButton     *widget.Button
	uuidButton      *widget.Button
	routingInfo     *widget.RichText
	transportInfo   *widget.List
	config          binding.String
}

// NewAppGUI создает новый экземпляр GUI приложения
func NewAppGUI(sm *state.VPNStateMachine, tr *geoip.TrafficRouter) *AppGUI {
	myApp := app.New()
	myWindow := myApp.NewWindow("XVPN Client")
	myWindow.Resize(fyne.NewSize(500, 450))

	gui := &AppGUI{
		app:            myApp,
		window:         myWindow,
		stateMachine:   sm,
		trafficRouter:  tr,
	}

	// Создаем виджеты интерфейса
	gui.createWidgets()
	
	// Создаем макет
	content := gui.createLayout()
	
	// Устанавливаем контент окна
	myWindow.SetContent(content)

	return gui
}

// createWidgets создает все виджеты интерфейса
func (g *AppGUI) createWidgets() {
	g.statusLabel = widget.NewLabel("Статус: OFF")
	g.ipLabel = widget.NewLabel("IP: -")
	g.securityLabel = widget.NewLabel("Безопасность:")
	g.securityValue = widget.NewLabel("Оценка: -")
	g.securityBar = widget.NewEntry()
	g.securityBar.Disable()
	g.speedLabel = widget.NewLabel("Скорость: 0 ↓ / 0 ↑ КБ/с")
	g.toggleButton = widget.NewButton("Включить VPN", func() {
		g.onToggle()
	})
	g.fetchButton = widget.NewButton("Запросить конфиг", func() {
		g.onFetchConfig()
	})
	g.uuidButton = widget.NewButton("Сменить UUID", func() {
		g.onChangeUUID()
	})
	
	// Текст с информацией о маршрутизации
	g.routingInfo = widget.NewRichTextFromMarkdown("")
	g.routingInfo.Wrapping = true
	
	// Список транспортов
	g.transportInfo = widget.NewList(
		func() int {
			// Возвращаем количество транспортов
			return len(g.stateMachine.GetStateInfo()["fallback_transports"].([]state.Transport))
		},
		func() fyne.CanvasObject {
			return container.NewHBox(
				widget.NewLabel("Transport"),
				widget.NewLabel("Status"),
			)
		},
		func(id widget.ListItemID, obj fyne.CanvasObject) {
			// Здесь будет обновление элемента списка
		},
	)
}

// createLayout создает макет интерфейса
func (g *AppGUI) createLayout() fyne.CanvasObject {
	// Информационная панель
	infoGrid := container.NewGridWithColumns(2,
		g.statusLabel,
		g.ipLabel,
		g.securityLabel,
		container.NewHBox(g.securityValue, g.securityBar),
		g.speedLabel,
		widget.NewLabel(""), // пустая ячейка для выравнивания
	)
	
	// Кнопки управления
	buttonGrid := container.NewGridWithColumns(3,
		g.toggleButton,
		g.fetchButton,
		g.uuidButton,
	)
	
	// Информация о маршрутизации
	routingBox := container.NewVBox(
		widget.NewLabel("Информация о маршрутизации:"),
		g.routingInfo,
	)
	
	// Список транспортов
	transportBox := container.NewVBox(
		widget.NewLabel("Доступные транспорты:"),
		g.transportInfo,
	)
	
	// Верхняя часть: информация и кнопки
	topSection := container.NewVBox(
		infoGrid,
		buttonGrid,
		routingBox,
		transportBox,
	)
	
	// Используем разделитель для лучшего восприятия
	return container.NewBorder(
		nil, // верх
		nil, // низ
		nil, // лево
		nil, // право
		topSection,
	)
}

// onToggle обрабатывает нажатие кнопки переключения VPN
func (g *AppGUI) onToggle() {
	stateInfo := g.stateMachine.GetStateInfo()
	
	if stateInfo["current_state"] == state.StateRunning {
		g.stateMachine.TriggerEvent(state.EventStopRequested)
		dialog.ShowInformation("XVPN", "VPN останавливается...", g.window.(fyne.Window))
	} else {
		g.stateMachine.TriggerEvent(state.EventStartRequested)
		dialog.ShowInformation("XVPN", "VPN запускается...", g.window.(fyne.Window))
	}
	
	// Обновляем интерфейс
	g.updateUI()
}

// onFetchConfig обрабатывает нажатие кнопки получения конфига
func (g *AppGUI) onFetchConfig() {
	g.stateMachine.TriggerEvent(state.EventStartRequested)
	dialog.ShowInformation("XVPN", "Конфигурация обновляется...", g.window.(fyne.Window))
	
	// Обновляем интерфейс
	g.updateUI()
}

// onChangeUUID обрабатывает смену UUID
func (g *AppGUI) onChangeUUID() {
	// Здесь нужно использовать диалог ввода, но для простоты используем простой ввод
	dialog.ShowForm("Сменить UUID", "Сохранить", "Отмена",
		[]*widget.FormItem{
			widget.NewFormItem("Новый UUID", widget.NewEntry()),
		},
		func(result bool) {
			if result {
				// В реальном приложении здесь будет обработка нового UUID
				dialog.ShowInformation("XVPN", "UUID изменён", g.window.(fyne.Window))
			}
		},
		g.window.(fyne.Window))
}

// updateUI обновляет интерфейс на основе состояния
func (g *AppGUI) updateUI() {
	stateInfo := g.stateMachine.GetStateInfo()
	
	// Обновляем статус
	if stateInfo["current_state"] == state.StateRunning {
		g.statusLabel.SetText("Статус: ON")
		g.toggleButton.SetText("Выключить VPN")
	} else {
		g.statusLabel.SetText("Статус: OFF")
		g.toggleButton.SetText("Включить VPN")
	}
	
	// Обновляем IP (в реальном приложении будет реальный IP)
	g.ipLabel.SetText("IP: 203.0.113.10")
	
	// Обновляем оценку безопасности
	if healthScore, ok := stateInfo["health_score"].(int); ok {
		g.updateSecurityBar(healthScore)
	}
	
	// Обновляем скорость (в реальном приложении будет реальная скорость)
	g.speedLabel.SetText("Скорость: 15.2 ↓ / 8.7 ↑ МБ/с")
	
	// Обновляем информацию о маршрутизации
	g.updateRoutingInfo()
}

// updateSecurityBar обновляет индикатор безопасности
func (g *AppGUI) updateSecurityBar(healthScore int) {
	var color, statusText string
	
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
	
	g.securityBar.Text = fmt.Sprintf("●") // Символ для индикатора
	g.securityValue.SetText(fmt.Sprintf("Оценка: %d/5 (%s)", healthScore, statusText))
	
	// В примитивной реализации мы просто устанавливаем текст
	// В реальной реализации здесь будут цветовые настройки
}

// updateRoutingInfo обновляет информацию о маршрутизации
func (g *AppGUI) updateRoutingInfo() {
	// В реальном приложении здесь будет информация о текущих правилах маршрутизации
	info := `**Правила маршрутизации:**
- Российский трафик: Прямое подключение
- Международный трафик: Через VPN
- Локальные сети: Прямое подключение

**Текущая конфигурация:**
- РУ страны: RU, BY, KZ, и др.
- Проверка GeoIP: Включена
- Хаотичный пинг: 30-300 сек`
	
	g.routingInfo.ParseMarkdown(info)
}

// Run запускает GUI приложение
func (g *AppGUI) Run() {
	g.updateUI()
	
	// Запускаем обновление интерфейса в отдельной горутине
	go g.updateLoop()
	
	// Показываем и запускаем окно
	g.window.(fyne.Window).ShowAndRun()
}

// updateLoop циклически обновляет интерфейс
func (g *AppGUI) updateLoop() {
	// В реальном приложении здесь будет цикл обновления каждые N секунд
}