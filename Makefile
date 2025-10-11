# Makefile для сборки XVPN клиента под разные платформы

.PHONY: build build-linux build-macos build-windows build-android build-ios clean test install deploy

# Определение переменных
BINARY_NAME=xvpn-client
GOFILES=$(shell find . -name '*.go' -not -path './vendor/*' -not -path './third_party/*')

# Целевые платформы
LINUX_TARGETS=linux/amd64 linux/386 linux/arm64 linux/arm
MACOS_TARGETS=darwin/amd64 darwin/arm64
WINDOWS_TARGETS=windows/amd64 windows/386 windows/arm64

# Сборка для всех платформ
build: build-linux build-macos build-windows

# Сборка для Linux
build-linux:
	@echo "Сборка для Linux..."
	@mkdir -p builds/linux
	@for target in $(LINUX_TARGETS); do \
		os=$$(echo $$target | cut -d'/' -f1); \
		arch=$$(echo $$target | cut -d'/' -f2); \
		echo "Сборка для $$target..."; \
		GOOS=$$os GOARCH=$$arch go build -o builds/linux/$(BINARY_NAME)-$$os-$$arch -ldflags="-s -w" .; \
	done

# Сборка для macOS
build-macos:
	@echo "Сборка для macOS..."
	@mkdir -p builds/macos
	@for target in $(MACOS_TARGETS); do \
		os=$$(echo $$target | cut -d'/' -f1); \
		arch=$$(echo $$target | cut -d'/' -f2); \
		echo "Сборка для $$target..."; \
		GOOS=$$os GOARCH=$$arch go build -o builds/macos/$(BINARY_NAME)-$$os-$$arch -ldflags="-s -w" .; \
	done

# Сборка для Windows
build-windows:
	@echo "Сборка для Windows..."
	@mkdir -p builds/windows
	@for target in $(WINDOWS_TARGETS); do \
		os=$$(echo $$target | cut -d'/' -f1); \
		arch=$$(echo $$target | cut -d'/' -f2); \
		echo "Сборка для $$target..."; \
		GOOS=$$os GOARCH=$$arch go build -o builds/windows/$(BINARY_NAME)-$$os-$$arch.exe -ldflags="-s -w" .; \
	done

# Сборка для конкретной платформы (использование: make build-platform PLATFORM=linux/amd64)
build-platform:
	@echo "Сборка для $(PLATFORM)..."
	@mkdir -p builds
	@os=$$(echo $(PLATFORM) | cut -d'/' -f1); \
	arch=$$(echo $(PLATFORM) | cut -d'/' -f2); \
	if [ "$(PLATFORM)" = "windows/amd64" ] || [ "$(PLATFORM)" = "windows/386" ] || [ "$(PLATFORM)" = "windows/arm64" ]; then \
		GOOS=$$os GOARCH=$$arch go build -o builds/$(BINARY_NAME)-$$os-$$arch.exe -ldflags="-s -w" .; \
	else \
		GOOS=$$os GOARCH=$$arch go build -o builds/$(BINARY_NAME)-$$os-$$arch -ldflags="-s -w" .; \
	fi

# Установка зависимостей
deps:
	@echo "Установка зависимостей..."
	go mod tidy

# Тестирование
test:
	@echo "Запуск тестов..."
	go test -v ./...

# Форматирование кода
fmt:
	@echo "Форматирование кода..."
	gofmt -s -w .

# Линтинг
lint:
	@echo "Проверка кода линтером..."
	golangci-lint run

# Очистка сборок
clean:
	@echo "Очистка..."
	rm -rf builds/
	rm -f $(BINARY_NAME)*

# Установка бинарного файла (для разработки)
install:
	@echo "Установка бинарного файла..."
	go install .

# Сборка и создание архива
package: build
	@echo "Создание архивов..."
	@cd builds/linux && tar -czf ../$(BINARY_NAME)-linux-amd64.tar.gz xvpn-client-linux-amd64
	@cd builds/macos && tar -czf ../$(BINARY_NAME)-darwin-amd64.tar.gz xvpn-client-darwin-amd64
	@cd builds/windows && zip ../$(BINARY_NAME)-windows-amd64.zip xvpn-client-windows-amd64.exe

# Запуск в режиме разработки
dev:
	@echo "Запуск в режиме разработки..."
	go run .

# Отправка в репозиторий
deploy:
	@echo "Подготовка к деплою..."
	git add .
	git commit -m "Build: добавлены бинарные файлы для мультиплатформенной версии"
	git push origin main