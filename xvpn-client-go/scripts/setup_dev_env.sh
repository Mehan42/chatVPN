#!/bin/bash
# Скрипт для подготовки окружения разработки XVPN клиента на Go

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

# Функция для проверки и установки Go
check_and_install_go() {
    log_info "Проверка наличия Go..."
    
    if command -v go &> /dev/null; then
        local go_version=$(go version | awk '{print $3}' | sed 's/go//')
        log_success "Go уже установлен: версия $go_version"
        return 0
    fi
    
    log_info "Go не найден, устанавливаем..."
    
    # Определяем архитектуру
    local arch=$(uname -m)
    case "$arch" in
        x86_64)
            arch="amd64"
            ;;
        aarch64)
            arch="arm64"
            ;;
        *)
            log_error "Неподдерживаемая архитектура: $arch"
            exit 1
            ;;
    esac
    
    # Определяем ОС
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    case "$os" in
        linux)
            os="linux"
            ;;
        darwin)
            os="darwin"
            ;;
        *)
            log_error "Неподдерживаемая ОС: $os"
            exit 1
            ;;
    esac
    
    # Скачиваем и устанавливаем Go
    local go_version="1.21.0"
    local go_tarball="go$go_version.$os-$arch.tar.gz"
    local go_url="https://go.dev/dl/$go_tarball"
    
    log_info "Скачивание Go $go_version для $os/$arch..."
    wget -q "$go_url" -O "/tmp/$go_tarball"
    
    log_info "Установка Go..."
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "/tmp/$go_tarball"
    
    # Добавляем Go в PATH
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
    
    log_success "Go $go_version успешно установлен"
}

# Функция для настройки рабочего окружения
setup_workspace() {
    log_info "Настройка рабочего окружения..."
    
    # Создаем структуру проекта
    mkdir -p ~/go/src/github.com/Mehan42
    mkdir -p ~/go/bin
    mkdir -p ~/go/pkg
    
    # Добавляем GOPATH в .bashrc если его нет
    if ! grep -q "GOPATH" ~/.bashrc; then
        echo 'export GOPATH=$HOME/go' >> ~/.bashrc
        echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
    fi
    
    # Устанавливаем переменные окружения
    export GOPATH=$HOME/go
    export PATH=$PATH:$GOPATH/bin:/usr/local/go/bin
    
    log_success "Рабочее окружение настроено"
}

# Функция для клонирования репозитория
clone_repository() {
    local repo_url="https://github.com/Mehan42/chatVPN.git"
    local target_dir="$GOPATH/src/github.com/Mehan42/chatVPN"
    
    log_info "Клонирование репозитория $repo_url..."
    
    if [ -d "$target_dir" ]; then
        log_warning "Репозиторий уже существует, обновляем..."
        cd "$target_dir"
        git pull
    else
        mkdir -p "$(dirname "$target_dir")"
        cd "$(dirname "$target_dir")"
        git clone "$repo_url"
    fi
    
    log_success "Репозиторий клонирован в $target_dir"
}

# Функция для установки зависимостей
install_dependencies() {
    local project_dir="$GOPATH/src/github.com/Mehan42/chatVPN"
    
    log_info "Установка зависимостей..."
    
    cd "$project_dir"
    
    # Инициализируем модули Go
    go mod init xvpn-client-go
    
    # Устанавливаем зависимости
    go get -u github.com/gin-gonic/gin
    go get -u github.com/go-resty/resty/v2
    go get -u github.com/sirupsen/logrus
    go get -u github.com/spf13/viper
    go get -u github.com/fsnotify/fsnotify
    go get -u github.com/gorilla/websocket
    go get -u github.com/robfig/cron/v3
    go get -u github.com/shirou/gopsutil/v3
    go get -u github.com/google/uuid
    go get -u github.com/json-iterator/go
    go get -u github.com/mitchellh/mapstructure
    go get -u github.com/pkg/errors
    go get -u github.com/stretchr/testify
    go get -u golang.org/x/crypto
    go get -u golang.org/x/net
    go get -u golang.org/x/sys
    
    log_success "Зависимости установлены"
}

# Функция для настройки IDE
setup_ide() {
    log_info "Настройка IDE..."
    
    # Создаем конфигурацию VS Code если она существует
    if [ -d ~/.vscode ]; then
        mkdir -p .vscode
        
        # Создаем tasks.json
        cat > .vscode/tasks.json << EOF
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "build",
            "type": "shell",
            "command": "go build -o bin/xvpn-client cmd/xvpn-client/main.go",
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "\${workspaceFolder}"
            }
        },
        {
            "label": "run",
            "type": "shell",
            "command": "go run cmd/xvpn-client/main.go",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "\${workspaceFolder}"
            }
        },
        {
            "label": "test",
            "type": "shell",
            "command": "go test ./...",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "\${workspaceFolder}"
            }
        }
    ]
}
EOF
        
        # Создаем launch.json
        cat > .vscode/launch.json << EOF
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch XVPN Client",
            "type": "go",
            "request": "launch",
            "mode": "debug",
            "program": "\${workspaceFolder}/cmd/xvpn-client/main.go",
            "env": {
                "XVPN_CLIENT_UUID": "test-client-uuid",
                "XVPN_SERVER_URL": "http://localhost:8443"
            },
            "args": []
        }
    ]
}
EOF
        
        log_success "Конфигурация VS Code создана"
    fi
}

# Функция для создания алиасов
create_aliases() {
    log_info "Создание алиасов..."
    
    # Добавляем алиасы в .bashrc
    local aliases_added=false
    
    if ! grep -q "# XVPN Aliases" ~/.bashrc; then
        cat >> ~/.bashrc << 'EOF'

# XVPN Aliases
alias xvpn-dev='cd $GOPATH/src/github.com/Mehan42/chatVPN && ./scripts/dev_runner.sh'
alias xvpn-test='cd $GOPATH/src/github.com/Mehan42/chatVPN && ./scripts/run_integration_tests.sh'
alias xvpn-build='cd $GOPATH/src/github.com/Mehan42/chatVPN && make build'
alias xvpn-run='cd $GOPATH/src/github.com/Mehan42/chatVPN && make dev'
alias xvpn-deploy='cd $GOPATH/src/github.com/Mehan42/chatVPN && ./scripts/deploy_client.sh'
EOF
        
        aliases_added=true
    fi
    
    if [ "$aliases_added" = true ]; then
        log_success "Алиасы добавлены в .bashrc"
        log_info "Для применения алиасов выполните: source ~/.bashrc"
    else
        log_info "Алиасы уже существуют"
    fi
}

# Функция для тестирования установки
test_installation() {
    local project_dir="$GOPATH/src/github.com/Mehan42/chatVPN"
    
    log_info "Тестирование установки..."
    
    cd "$project_dir"
    
    # Проверяем, что проект собирается
    if go build -o /tmp/xvpn-client-test cmd/xvpn-client/main.go; then
        log_success "Проект успешно собирается"
        rm /tmp/xvpn-client-test
    else
        log_error "Ошибка сборки проекта"
        exit 1
    fi
    
    # Проверяем, что тесты проходят
    if go test ./... -short; then
        log_success "Тесты проходят успешно"
    else
        log_warning "Некоторые тесты не прошли"
    fi
    
    log_success "Установка протестирована"
}

# Основная функция
main() {
    log_info "Подготовка окружения разработки XVPN клиента на Go"
    log_info "=================================================="
    
    # Проверяем и устанавливаем Go
    check_and_install_go
    
    # Настраиваем рабочее окружение
    setup_workspace
    
    # Клонируем репозиторий
    clone_repository
    
    # Устанавливаем зависимости
    install_dependencies
    
    # Настраиваем IDE
    setup_ide
    
    # Создаем алиасы
    create_aliases
    
    # Тестируем установку
    test_installation
    
    log_success "Окружение разработки успешно настроено!"
    log_info "Для начала работы выполните:"
    log_info "  source ~/.bashrc"
    log_info "  cd \$GOPATH/src/github.com/Mehan42/chatVPN"
    log_info "  make dev"
}

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi