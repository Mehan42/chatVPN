# Makefile для сборки XVPN клиента на Go

.PHONY: build build-linux build-macos build-windows build-all clean test vet fmt install \
	dev dev-run dev-debug dev-profile dev-bench \
	test-run test-extended test-integration test-api \
	deploy deploy-client deploy-server \
	setup setup-dev setup-env \
	doc docs document \
	help

# Имя бинарного файла
BINARY_NAME=xvpn-client
GATEWAY_BINARY_NAME=xvpn-gateway
# Версия
VERSION=$(shell git describe --tags --always 2>/dev/null || echo "v0.1.0")

# Платформы для сборки
PLATFORMS_LINUX=linux-amd64 linux-arm64
PLATFORMS_MACOS=darwin-amd64 darwin-arm64
PLATFORMS_WINDOWS=windows-amd64 windows-386
PLATFORMS_ALL=$(PLATFORMS_LINUX) $(PLATFORMS_MACOS) $(PLATFORMS_WINDOWS)

# Директории
BUILD_DIR=builds
DIST_DIR=dist
DOCS_DIR=docs
SCRIPTS_DIR=scripts

# Сборка для всех платформ
build-all: $(addprefix build-,$(PLATFORMS_ALL))

# Сборка для Linux
build-linux: $(addprefix build-,$(PLATFORMS_LINUX))

# Сборка для macOS
build-macos: $(addprefix build-,$(PLATFORMS_MACOS))

# Сборка для Windows
build-windows: $(addprefix build-,$(PLATFORMS_WINDOWS))

# Правила сборки для каждой платформы
build-linux-amd64:
	@echo "Сборка для Linux/amd64..."
	@mkdir -p $(BUILD_DIR)/linux/amd64
	GOOS=linux GOARCH=amd64 go build -o $(BUILD_DIR)/linux/amd64/$(BINARY_NAME)-linux-amd64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=linux GOARCH=amd64 go build -o $(BUILD_DIR)/linux/amd64/$(GATEWAY_BINARY_NAME)-linux-amd64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для Linux/amd64 завершена"

build-linux-arm64:
	@echo "Сборка для Linux/arm64..."
	@mkdir -p $(BUILD_DIR)/linux/arm64
	GOOS=linux GOARCH=arm64 go build -o $(BUILD_DIR)/linux/arm64/$(BINARY_NAME)-linux-arm64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=linux GOARCH=arm64 go build -o $(BUILD_DIR)/linux/arm64/$(GATEWAY_BINARY_NAME)-linux-arm64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для Linux/arm64 завершена"

build-darwin-amd64:
	@echo "Сборка для macOS/amd64..."
	@mkdir -p $(BUILD_DIR)/darwin/amd64
	GOOS=darwin GOARCH=amd64 go build -o $(BUILD_DIR)/darwin/amd64/$(BINARY_NAME)-darwin-amd64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=darwin GOARCH=amd64 go build -o $(BUILD_DIR)/darwin/amd64/$(GATEWAY_BINARY_NAME)-darwin-amd64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для macOS/amd64 завершена"

build-darwin-arm64:
	@echo "Сборка для macOS/arm64..."
	@mkdir -p $(BUILD_DIR)/darwin/arm64
	GOOS=darwin GOARCH=arm64 go build -o $(BUILD_DIR)/darwin/arm64/$(BINARY_NAME)-darwin-arm64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=darwin GOARCH=arm64 go build -o $(BUILD_DIR)/darwin/arm64/$(GATEWAY_BINARY_NAME)-darwin-arm64 -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для macOS/arm64 завершена"

build-windows-amd64:
	@echo "Сборка для Windows/amd64..."
	@mkdir -p $(BUILD_DIR)/windows/amd64
	GOOS=windows GOARCH=amd64 go build -o $(BUILD_DIR)/windows/amd64/$(BINARY_NAME)-windows-amd64.exe -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=windows GOARCH=amd64 go build -o $(BUILD_DIR)/windows/amd64/$(GATEWAY_BINARY_NAME)-windows-amd64.exe -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для Windows/amd64 завершена"

build-windows-386:
	@echo "Сборка для Windows/386..."
	@mkdir -p $(BUILD_DIR)/windows/386
	GOOS=windows GOARCH=386 go build -o $(BUILD_DIR)/windows/386/$(BINARY_NAME)-windows-386.exe -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	GOOS=windows GOARCH=386 go build -o $(BUILD_DIR)/windows/386/$(GATEWAY_BINARY_NAME)-windows-386.exe -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway
	@echo "Сборка для Windows/386 завершена"

# Сборка для текущей платформы
build:
	@echo "Сборка для текущей платформы..."
	go build -o $(BINARY_NAME) -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client
	go build -o $(GATEWAY_BINARY_NAME) -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway

# Сборка только основного клиента
build-client:
	@echo "Сборка основного клиента..."
	go build -o $(BINARY_NAME) -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-client

# Сборка только Gateway модуля
build-gateway:
	@echo "Сборка Gateway модуля..."
	go build -o $(GATEWAY_BINARY_NAME) -ldflags="-s -w -X main.version=$(VERSION)" ./cmd/xvpn-gateway

# Установка зависимостей
deps:
	@echo "Обновление зависимостей..."
	go mod tidy

# Тестирование
test:
	@echo "Запуск тестов..."
	go test -v ./...

# Проверка кода
vet:
	@echo "Проверка кода с помощью go vet..."
	go vet ./...

# Форматирование
fmt:
	@echo "Форматирование кода..."
	gofmt -s -w .

# Запуск в режиме разработки
dev:
	@echo "Запуск в режиме разработки..."
	./$(SCRIPTS_DIR)/dev_runner.sh run

# Запуск с параметрами
dev-run:
	@echo "Запуск с параметрами..."
	./$(SCRIPTS_DIR)/dev_runner.sh run $(ARGS)

# Запуск в режиме отладки
dev-debug:
	@echo "Запуск в режиме отладки..."
	./$(SCRIPTS_DIR)/dev_runner.sh debug

# Запуск с профилированием
dev-profile:
	@echo "Запуск с профилированием..."
	./$(SCRIPTS_DIR)/dev_runner.sh profile

# Запуск тестирования производительности
dev-bench:
	@echo "Запуск тестирования производительности..."
	./$(SCRIPTS_DIR)/dev_runner.sh bench

# Запуск тестов
test-run:
	@echo "Запуск тестов..."
	./$(SCRIPTS_DIR)/run_integration_tests.sh

# Расширенное тестирование
test-extended:
	@echo "Запуск расширенного тестирования..."
	go run ./cmd/extended_test/main.go

# Интеграционное тестирование
test-integration:
	@echo "Запуск интеграционного тестирования..."
	go run ./cmd/test/main.go

# API тестирование
test-api:
	@echo "Запуск API тестирования..."
	go run ./cmd/api_integration_test/main.go

# Тестирование обновлений
test-updates:
	@echo "Запуск тестирования обновлений..."
	go run ./cmd/update_test/main.go

# Очистка
clean:
	@echo "Очистка..."
	rm -rf $(BUILD_DIR)/
	rm -rf $(DIST_DIR)/
	rm -f $(BINARY_NAME) $(BINARY_NAME).exe
	find . -name "*.test" -delete

# Установка
install:
	@echo "Установка..."
	go install ./cmd/xvpn-client

# Создание архивов
package: build-all
	@echo "Создание архивов..."
	@mkdir -p $(DIST_DIR)
	
	# Linux
	cd $(BUILD_DIR)/linux/amd64 && tar -czf ../../$(DIST_DIR)/$(BINARY_NAME)-linux-amd64.tar.gz $(BINARY_NAME)-linux-amd64
	cd $(BUILD_DIR)/linux/amd64 && tar -czf ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-linux-amd64.tar.gz $(GATEWAY_BINARY_NAME)-linux-amd64
	cd $(BUILD_DIR)/linux/arm64 && tar -czf ../../$(DIST_DIR)/$(BINARY_NAME)-linux-arm64.tar.gz $(BINARY_NAME)-linux-arm64
	cd $(BUILD_DIR)/linux/arm64 && tar -czf ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-linux-arm64.tar.gz $(GATEWAY_BINARY_NAME)-linux-arm64
	
	# macOS
	cd $(BUILD_DIR)/darwin/amd64 && tar -czf ../../$(DIST_DIR)/$(BINARY_NAME)-darwin-amd64.tar.gz $(BINARY_NAME)-darwin-amd64
	cd $(BUILD_DIR)/darwin/amd64 && tar -czf ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-darwin-amd64.tar.gz $(GATEWAY_BINARY_NAME)-darwin-amd64
	cd $(BUILD_DIR)/darwin/arm64 && tar -czf ../../$(DIST_DIR)/$(BINARY_NAME)-darwin-arm64.tar.gz $(BINARY_NAME)-darwin-arm64
	cd $(BUILD_DIR)/darwin/arm64 && tar -czf ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-darwin-arm64.tar.gz $(GATEWAY_BINARY_NAME)-darwin-arm64
	
	# Windows
	cd $(BUILD_DIR)/windows/amd64 && zip ../../$(DIST_DIR)/$(BINARY_NAME)-windows-amd64.zip $(BINARY_NAME)-windows-amd64.exe
	cd $(BUILD_DIR)/windows/amd64 && zip ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-windows-amd64.zip $(GATEWAY_BINARY_NAME)-windows-amd64.exe
	cd $(BUILD_DIR)/windows/386 && zip ../../$(DIST_DIR)/$(BINARY_NAME)-windows-386.zip $(BINARY_NAME)-windows-386.exe
	cd $(BUILD_DIR)/windows/386 && zip ../../$(DIST_DIR)/$(GATEWAY_BINARY_NAME)-windows-386.zip $(GATEWAY_BINARY_NAME)-windows-386.exe
	
	@echo "Архивы созданы в $(DIST_DIR)/"

# Настройка окружения разработки
setup:
	@echo "Настройка окружения разработки..."
	./$(SCRIPTS_DIR)/setup_dev_env.sh

# Настройка окружения разработки (альтернативное имя)
setup-dev:
	@echo "Настройка окружения разработки..."
	./$(SCRIPTS_DIR)/setup_dev_env.sh

# Настройка окружения (альтернативное имя)
setup-env:
	@echo "Настройка окружения разработки..."
	./$(SCRIPTS_DIR)/setup_dev_env.sh

# Развертывание клиента
deploy-client:
	@echo "Развертывание клиента..."
	./$(SCRIPTS_DIR)/deploy_client.sh

# Развертывание сервера
deploy-server:
	@echo "Развертывание сервера..."
	cd ../server && ./install_server_flexible.sh

# Полное развертывание
deploy: deploy-client deploy-server

# Создание документации
doc:
	@echo "Создание документации..."
	@mkdir -p $(DOCS_DIR)
	
	# Генерируем документацию из комментариев в коде
	go doc -all ./... > $(DOCS_DIR)/api_reference.txt
	
	@echo "Документация создана в $(DOCS_DIR)/"

# Создание документации (альтернативное имя)
docs: doc

# Создание документации (альтернативное имя)
document: doc

# Информация о сборке
info:
	@echo "Версия: $(VERSION)"
	@go version
	@echo "Текущая ОС/архитектура: $(GOOS)/$(GOARCH)"
	@echo "Каталог сборки: $(BUILD_DIR)"
	@echo "Каталог дистрибутива: $(DIST_DIR)"

# Помощь
help:
	@echo "XVPN Client Go Makefile"
	@echo "======================"
	@echo ""
	@echo "Основные команды:"
	@echo "  make build          - Сборка клиента и Gateway модуля для текущей платформы"
	@echo "  make build-client   - Сборка только основного клиента"
	@echo "  make build-gateway  - Сборка только Gateway модуля"
	@echo "  make build-all      - Сборка для всех платформ"
	@echo "  make build-linux    - Сборка для Linux"
	@echo "  make build-macos    - Сборка для macOS"
	@echo "  make build-windows  - Сборка для Windows"
	@echo ""
	@echo "Разработка:"
	@echo "  make dev            - Запуск в режиме разработки"
	@echo "  make dev-run        - Запуск с параметрами"
	@echo "  make dev-debug      - Запуск в режиме отладки"
	@echo "  make dev-profile    - Запуск с профилированием"
	@echo "  make dev-bench      - Запуск тестирования производительности"
	@echo ""
	@echo "Тестирование:"
	@echo "  make test           - Запуск всех тестов"
	@echo "  make test-run       - Запуск тестов интеграции"
	@echo "  make test-extended  - Расширенное тестирование"
	@echo "  make test-integration - Интеграционное тестирование"
	@echo "  make test-api       - API тестирование"
	@echo "  make test-updates   - Тестирование обновлений"
	@echo ""
	@echo "Управление:"
	@echo "  make clean          - Очистка"
	@echo "  make install        - Установка"
	@echo "  make package        - Создание архивов (включая Gateway модуль)"
	@echo "  make setup          - Настройка окружения разработки"
	@echo "  make deploy         - Полное развертывание"
	@echo "  make deploy-client  - Развертывание клиента"
	@echo "  make deploy-server  - Развертывание сервера"
	@echo "  make doc            - Создание документации"
	@echo "  make info           - Информация о сборке"
	@echo "  make help           - Помощь"
	@echo ""
	@echo "Примеры:"
	@echo "  make build-linux-amd64  - Сборка для Linux/amd64"
	@echo "  make dev-run ARGS='custom-uuid https://api.example.com' - Запуск с параметрами"
	@echo "  make test-run           - Запуск тестов интеграции"

# Запуск сервера в режиме разработки
dev-server:
	@echo "Запуск сервера в режиме разработки..."
	@cd /home/uss/chatvpn/server/api && python3 app.py

# Запуск клиента в режиме разработки
dev-client:
	@echo "Запуск клиента в режиме разработки..."
	@./scripts/dev_runner.sh run

# Запуск всей системы в режиме разработки
dev-system:
	@echo "Запуск всей системы в режиме разработки..."
	@./scripts/dev_system_runner.sh start

# Остановка всей системы
stop-dev-system:
	@echo "Остановка всей системы..."
	@./scripts/dev_system_runner.sh stop

# Перезапуск всей системы
restart-dev-system:
	@echo "Перезапуск всей системы..."
	@./scripts/dev_system_runner.sh restart

# Проверка состояния системы
status-dev-system:
	@echo "Проверка состояния системы..."
	@./scripts/dev_system_runner.sh status

# Запуск тестов интеграции с API
api-integration-test:
	@echo "Запуск тестов интеграции с API..."
	@./scripts/run_integration_tests.sh