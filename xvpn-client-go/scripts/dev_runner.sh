#!/bin/bash
# Скрипт для запуска XVPN клиента в режиме разработки

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для проверки зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверка Go
    if ! command -v go &> /dev/null; then
        log_error "Go не установлен"
        exit 1
    fi
    
    # Проверка версии Go
    local go_version=$(go version | awk '{print $3}' | sed 's/go//')
    log_info "Версия Go: $go_version"
    
    # Проверка наличия необходимых пакетов
    log_info "Проверка необходимых пакетов..."
    
    # Если есть зависимости в go.mod, проверяем их
    if [ -f "go.mod" ]; then
        log_info "Проверка зависимостей из go.mod..."
        go mod tidy
    fi
    
    log_success "Все зависимости проверены"
}

# Функция для запуска клиента
run_client() {
    local client_uuid="${1:-test-client-uuid}"
    local server_url="${2:-http://localhost:8443}"
    
    log_info "Запуск XVPN клиента..."
    log_info "  UUID клиента: $client_uuid"
    log_info "  URL сервера: $server_url"
    
    # Устанавливаем переменные окружения
    export XVPN_CLIENT_UUID="$client_uuid"
    export XVPN_SERVER_URL="$server_url"
    export XVPN_DEBUG="true"
    
    # Запускаем клиент
    go run cmd/xvpn-client/main.go "$@"
}

# Функция для запуска тестов
run_tests() {
    log_info "Запуск тестов..."
    
    # Запускаем unit-тесты
    go test -v ./...
    
    log_success "Тесты завершены"
}

# Функция для сборки клиента
build_client() {
    local output_name="${1:-xvpn-client}"
    local target_os="${2:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
    local target_arch="${3:-$(uname -m)}"
    
    log_info "Сборка клиента..."
    log_info "  Выходной файл: $output_name"
    log_info "  Целевая ОС: $target_os"
    log_info "  Целевая архитектура: $target_arch"
    
    # Устанавливаем переменные окружения для кросс-компиляции
    case "$target_os" in
        linux)
            export GOOS=linux
            ;;
        darwin)
            export GOOS=darwin
            ;;
        windows)
            export GOOS=windows
            output_name="${output_name}.exe"
            ;;
        *)
            export GOOS="$target_os"
            ;;
    esac
    
    case "$target_arch" in
        x86_64|amd64)
            export GOARCH=amd64
            ;;
        aarch64|arm64)
            export GOARCH=arm64
            ;;
        i386|i686)
            export GOARCH=386
            ;;
        *)
            export GOARCH="$target_arch"
            ;;
    esac
    
    # Сборка
    go build -o "$output_name" -ldflags="-s -w -X main.version=dev" ./cmd/xvpn-client
    
    # Проверка успешности сборки
    if [ $? -eq 0 ]; then
        log_success "Клиент успешно собран: $output_name"
        ls -lh "$output_name"
    else
        log_error "Ошибка сборки клиента"
        exit 1
    fi
}

# Функция для запуска в режиме отладки
run_debug() {
    local client_uuid="${1:-test-client-uuid}"
    local server_url="${2:-http://localhost:8443}"
    
    log_info "Запуск XVPN клиента в режиме отладки..."
    
    # Устанавливаем переменные окружения для отладки
    export XVPN_CLIENT_UUID="$client_uuid"
    export XVPN_SERVER_URL="$server_url"
    export XVPN_DEBUG="true"
    export XVPN_LOG_LEVEL="debug"
    
    # Запускаем клиент с отладкой
    go run -gcflags="all=-N -l" cmd/xvpn-client/main.go "$@"
}

# Функция для запуска профилирования
run_profile() {
    local client_uuid="${1:-test-client-uuid}"
    local server_url="${2:-http://localhost:8443}"
    
    log_info "Запуск XVPN клиента с профилированием..."
    
    # Устанавливаем переменные окружения
    export XVPN_CLIENT_UUID="$client_uuid"
    export XVPN_SERVER_URL="$server_url"
    export XVPN_PROFILE="true"
    
    # Запускаем клиент с профилированием
    go run cmd/xvpn-client/main.go "$@"
}

# Функция для запуска тестирования производительности
run_benchmark() {
    log_info "Запуск тестирования производительности..."
    
    # Запускаем benchmark тесты
    go test -bench=. -benchmem ./...
    
    log_success "Тестирование производительности завершено"
}

# Основная функция
main() {
    local command="${1:-run}"
    
    log_info "XVPN Client Development Runner"
    log_info "============================="
    
    # Проверка зависимостей
    check_dependencies
    
    # Получаем путь к проекту
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    
    log_info "Каталог проекта: $PROJECT_DIR"
    
    # Переходим в каталог проекта
    cd "$PROJECT_DIR"
    
    # Выполняем команду
    case "$command" in
        run)
            shift
            run_client "$@"
            ;;
        test)
            shift
            run_tests "$@"
            ;;
        build)
            shift
            build_client "$@"
            ;;
        debug)
            shift
            run_debug "$@"
            ;;
        profile)
            shift
            run_profile "$@"
            ;;
        bench)
            shift
            run_benchmark "$@"
            ;;
        help)
            echo "Использование: $0 [команда] [параметры]"
            echo ""
            echo "Команды:"
            echo "  run     - Запустить клиент (по умолчанию)"
            echo "  test    - Запустить тесты"
            echo "  build   - Собрать клиент"
            echo "  debug   - Запустить клиент в режиме отладки"
            echo "  profile - Запустить клиент с профилированием"
            echo "  bench   - Запустить тестирование производительности"
            echo "  help    - Показать помощь"
            echo ""
            echo "Примеры:"
            echo "  $0 run"
            echo "  $0 run custom-uuid https://api.example.com"
            echo "  $0 test"
            echo "  $0 build xvpn-client-linux-amd64 linux amd64"
            echo "  $0 debug"
            echo "  $0 profile"
            echo "  $0 bench"
            ;;
        *)
            log_error "Неизвестная команда: $command"
            log_info "Используйте '$0 help' для получения справки"
            exit 1
            ;;
    esac
}

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi