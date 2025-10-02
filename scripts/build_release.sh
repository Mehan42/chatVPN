#!/bin/bash

# Скрипт автоматической сборки и публикации релиза XVPN
# Автоматическая генерация установщиков для всех платформ

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 XVPN Release Builder${NC}"
echo "================================"

# Проверка прав
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен быть запущен с правами root${NC}"
   exit 1
fi

# Путь к проекту
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Директории
BUILD_DIR="$PROJECT_DIR/build"
DIST_DIR="$PROJECT_DIR/dist"
INSTALLER_SCRIPT="$PROJECT_DIR/scripts/installers/create_installer.py"

# Цвета для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не установлен"
        exit 1
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        print_error "Git не установлен"
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker не установлен, будет пропущена сборка Docker образов"
    fi
    
    # Проверка dpkg-deb для Linux
    if ! command -v dpkg-deb &> /dev/null; then
        print_warning "dpkg-deb не установлен, будет пропущена сборка .deb пакетов"
    fi
    
    # Проверка NSIS для Windows
    if ! command -v makensis &> /dev/null; then
        print_warning "NSIS не установлен, будет пропущена сборка .exe установщиков"
    fi
    
    print_success "Зависимости проверены"
}

# Очистка перед сборкой
clean_build() {
    print_info "Очистка перед сборкой..."
    
    if [[ -d "$BUILD_DIR" ]]; then
        rm -rf "$BUILD_DIR"
    fi
    
    if [[ -d "$DIST_DIR" ]]; then
        rm -rf "$DIST_DIR"
    fi
    
    mkdir -p "$BUILD_DIR" "$DIST_DIR"
    print_success "Очистка завершена"
}

# Сборка проекта
build_project() {
    print_info "Сборка проекта..."
    
    cd "$PROJECT_DIR"
    
    # Установка Python зависимостей
    if [[ -f "requirements.txt" ]]; then
        print_info "Установка Python зависимостей..."
        pip3 install -r requirements.txt
    fi
    
    # Установка uv если установлен
    if ! command -v uv &> /dev/null; then
        print_info "Установка uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Сборка Python приложений
    if [[ -d "server" ]]; then
        print_info "Сборка серверного приложения..."
        cd server
        if command -v uv &> /dev/null; then
            uv build --out-dir "$BUILD_DIR/server"
        else
            pip3 install -e .
        fi
        cd ..
    fi
    
    if [[ -d "client" ]]; then
        print_info "Сборка клиентского приложения..."
        cd client
        if command -v uv &> /dev/null; then
            uv build --out-dir "$BUILD_DIR/client"
        else
            pip3 install -e .
        fi
        cd ..
    fi
    
    print_success "Проект собран"
}

# Создание установщиков
create_installers() {
    print_info "Создание установщиков..."
    
    if [[ ! -f "$INSTALLER_SCRIPT" ]]; then
        print_error "Скрипт установщика не найден: $INSTALLER_SCRIPT"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Linux установщики
    if command -v dpkg-deb &> /dev/null; then
        print_info "Создание Linux .deb пакета..."
        python3 "$INSTALLER_SCRIPT" --platform linux
    else
        print_warning "Пропускаем создание .deb пакета"
    fi
    
    # Windows установщики
    if command -v makensis &> /dev/null; then
        print_info "Создание Windows установщика..."
        python3 "$INSTALLER_SCRIPT" --platform windows
    else
        print_warning "Пропускаем создание .exe установщика"
    fi
    
    # macOS установщики
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Создание macOS установщиков..."
        python3 "$INSTALLER_SCRIPT" --platform darwin
    else
        print_warning "Пропускаем создание macOS установщиков"
    fi
    
    print_success "Установщики созданы"
}

# Тестирование установщиков
test_installers() {
    print_info "Тестирование установщиков..."
    
    if [[ ! -d "$DIST_DIR" ]]; then
        print_warning "Директория с установщиками не найдена"
        return
    fi
    
    # Проверка созданных файлов
    cd "$DIST_DIR"
    
    for file in *.deb *.exe *.dmg *.pkg *.zip; do
        if [[ -f "$file" ]]; then
            file_size=$(du -h "$file" | cut -f1)
            print_success "Найден установщик: $file ($file_size)"
        fi
    done
    
    print_success "Тестирование завершено"
}

# Создание архива релиза
create_release_archive() {
    print_info "Создание архива релиза..."
    
    cd "$PROJECT_DIR"
    
    # Определение версии
    if [[ -f "install_config.json" ]]; then
        VERSION=$(grep -o '"version": "[^"]*"' install_config.json | cut -d'"' -f4)
    else
        VERSION="1.0.0"
    fi
    
    ARCHIVE_NAME="xvpn_${VERSION}_release"
    ARCHIVE_FILE="${ARCHIVE_NAME}.tar.gz"
    
    # Создание архива
    tar -czf "$ARCHIVE_FILE" \
        --exclude="build" \
        --exclude="dist" \
        --exclude=".git" \
        --exclude="*.pyc" \
        --exclude="__pycache__" \
        .
    
    if [[ -f "$ARCHIVE_FILE" ]]; then
        archive_size=$(du -h "$ARCHIVE_FILE" | cut -f1)
        print_success "Архив создан: $ARCHIVE_FILE ($archive_size)"
    else
        print_error "Ошибка создания архива"
        exit 1
    fi
    
    print_success "Архив релиза создан"
}

# Вывод информации
show_release_info() {
    print_info "Информация о релизе:"
    echo "================================"
    
    if [[ -d "$DIST_DIR" ]]; then
        echo "Установители:"
        ls -la "$DIST_DIR" | grep -E "\.(deb|exe|dmg|pkg|zip)$" || true
    fi
    
    if [[ -f "$PROJECT_DIR/$ARCHIVE_FILE" ]]; then
        echo ""
        echo "Архив релиза:"
        ls -lh "$PROJECT_DIR/$ARCHIVE_FILE"
    fi
    
    echo ""
    print_success "Релиз готов к публикации!"
}

# Основная функция
main() {
    print_info "Начало процесса сборки релиза XVPN"
    
    check_dependencies
    clean_build
    build_project
    create_installers
    test_installers
    create_release_archive
    show_release_info
    
    print_success "✅ Релиз XVPN успешно создан!"
    print_info "Проверьте директорию $DIST_DIR для готовых установщиков"
    print_info "Архив релиза находится в $PROJECT_DIR/"
}

# Запуск основной функции
main "$@"