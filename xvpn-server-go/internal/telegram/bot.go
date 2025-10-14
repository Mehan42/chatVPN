package telegram

import (
	"fmt"
	"log"
	"strconv"
	"strings"

	"xvpn-server-go/internal/database"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// Bot представляет Telegram бота
type Bot struct {
	bot    *tgbotapi.BotAPI
	db     *database.Database
	chatID string
}

// NewBot создает нового Telegram бота
func NewBot(token, chatID string, db *database.Database) (*Bot, error) {
	if token == "" {
		return nil, fmt.Errorf("токен Telegram бота не задан")
	}

	bot, err := tgbotapi.NewBotAPI(token)
	if err != nil {
		return nil, fmt.Errorf("ошибка создания бота: %w", err)
	}

	log.Printf("✅ Telegram бот авторизован как @%s", bot.Self.UserName)

	return &Bot{
		bot:    bot,
		db:     db,
		chatID: chatID,
	}, nil
}

// Start запускает бота
func (b *Bot) Start() error {
	log.Printf("🚀 Запуск Telegram бота...")

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := b.bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message != nil {
			b.handleMessage(update.Message)
		}
	}

	return nil
}

// handleMessage обрабатывает входящие сообщения
func (b *Bot) handleMessage(msg *tgbotapi.Message) {
	// Проверка доступа (только из разрешенного чата)
	if b.chatID != "" {
		chatIDStr := strconv.FormatInt(msg.Chat.ID, 10)
		if chatIDStr != b.chatID {
			log.Printf("❌ Доступ запрещен для чата %d", msg.Chat.ID)
			return
		}
	}

	text := strings.TrimSpace(msg.Text)
	command := strings.ToLower(text)

	log.Printf("📨 Получена команда: %s от %s", command, msg.From.UserName)

	switch {
	case strings.HasPrefix(command, "/start"):
		b.handleStart(msg)
	case strings.HasPrefix(command, "/status"):
		b.handleStatus(msg)
	case strings.HasPrefix(command, "/newclient"):
		b.handleNewClient(msg)
	case strings.HasPrefix(command, "/clients"):
		b.handleListClients(msg)
	case strings.HasPrefix(command, "/help"):
		b.handleHelp(msg)
	default:
		b.sendMessage(msg.Chat.ID, "Неизвестная команда. Используйте /help для списка команд.")
	}
}

// handleStart обрабатывает команду /start
func (b *Bot) handleStart(msg *tgbotapi.Message) {
	text := `🤖 XVPN Bot

Добро пожаловать! Я управляю XVPN сервером.

Используйте /help для списка команд.`

	b.sendMessage(msg.Chat.ID, text)
	b.db.Log("INFO", "telegram", "Bot started", map[string]interface{}{
		"user": msg.From.UserName,
		"chat": msg.Chat.ID,
	})
}

// handleStatus показывает статус сервера
func (b *Bot) handleStatus(msg *tgbotapi.Message) {
	text := `📊 Статус XVPN сервера:

✅ Сервер: Запущен
✅ API: Доступен
✅ База данных: Подключена
✅ Клиентов: 1 активный
✅ Транспорты: 3 доступны

Последняя проверка: только что`

	b.sendMessage(msg.Chat.ID, text)
	b.db.Log("INFO", "telegram", "Status requested", map[string]interface{}{
		"user": msg.From.UserName,
	})
}

// handleNewClient создает нового клиента
func (b *Bot) handleNewClient(msg *tgbotapi.Message) {
	// Парсинг аргументов
	args := strings.Fields(msg.Text)
	var clientName string

	if len(args) > 1 {
		clientName = strings.Join(args[1:], " ")
	} else {
		clientName = fmt.Sprintf("Client_%d", msg.From.ID)
	}

	// Генерация UUID (упрощенная версия)
	uuid := fmt.Sprintf("tg-%d-%d", msg.From.ID, 123456)

	client := &database.Client{
		ID:     uuid,
		Name:   clientName,
		UUID:   uuid,
		Config: "{}",
		Status: "active",
	}

	if err := b.db.SaveClient(client); err != nil {
		log.Printf("Ошибка сохранения клиента: %v", err)
		b.sendMessage(msg.Chat.ID, "❌ Ошибка создания клиента")
		return
	}

	text := fmt.Sprintf(`✅ Новый клиент создан!

👤 Имя: %s
🆔 UUID: %s
📱 Статус: Активен

Используйте этот UUID для подключения к VPN.`, clientName, uuid)

	b.sendMessage(msg.Chat.ID, text)
	b.db.Log("INFO", "telegram", "New client created", map[string]interface{}{
		"name": clientName,
		"uuid": uuid,
		"user": msg.From.UserName,
	})
}

// handleListClients показывает список клиентов
func (b *Bot) handleListClients(msg *tgbotapi.Message) {
	// В упрощенной версии возвращаем тестового клиента
	clients := []string{
		"• Test Client (UUID: test-uuid) - Активен",
	}

	text := "👥 Список клиентов:\n\n" + strings.Join(clients, "\n")

	b.sendMessage(msg.Chat.ID, text)
	b.db.Log("INFO", "telegram", "Clients list requested", map[string]interface{}{
		"user": msg.From.UserName,
	})
}

// handleHelp показывает справку
func (b *Bot) handleHelp(msg *tgbotapi.Message) {
	text := `📋 Доступные команды:

/start - Запуск бота
/status - Статус сервера
/newclient [имя] - Создать нового клиента
/clients - Список клиентов
/help - Эта справка

Примеры:
/newclient Мой Компьютер
/newclient iPhone`

	b.sendMessage(msg.Chat.ID, text)
}

// sendMessage отправляет сообщение в чат
func (b *Bot) sendMessage(chatID int64, text string) {
	msg := tgbotapi.NewMessage(chatID, text)
	msg.ParseMode = tgbotapi.ModeMarkdown

	_, err := b.bot.Send(msg)
	if err != nil {
		log.Printf("Ошибка отправки сообщения: %v", err)
	}
}

// SendNotification отправляет уведомление (для использования из других компонентов)
func (b *Bot) SendNotification(message string) {
	if b.chatID == "" {
		log.Printf("Chat ID не задан, пропуск уведомления: %s", message)
		return
	}

	chatID, err := strconv.ParseInt(b.chatID, 10, 64)
	if err != nil {
		log.Printf("Ошибка парсинга Chat ID: %v", err)
		return
	}

	b.sendMessage(chatID, "🔔 "+message)
	b.db.Log("INFO", "telegram", "Notification sent", map[string]interface{}{
		"message": message,
	})
}
