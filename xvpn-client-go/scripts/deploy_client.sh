#!/bin/bash
# Скрипт развертывания XVPN клиента на Go

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

# Проверка наличия необходимых инструментов
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверка Go
    if ! command -v go &> /dev/null; then
        log_error "Go не установлен"
        exit 1
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        log_error "Git не установлен"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Клонирование репозитория
clone_repository() {
    local repo_url="$1"
    local target_dir="$2"
    
    log_info "Клонирование репозитория $repo_url в $target_dir..."
    
    if [ -d "$target_dir" ]; then
        log_warning "Директория $target_dir уже существует, обновляем..."
        cd "$target_dir"
        git pull
    else
        git clone "$repo_url" "$target_dir"
    fi
    
    cd "$target_dir"
    log_success "Репозиторий клонирован"
}

# Сборка клиента
build_client() {
    local target_platform="$1"
    local output_dir="$2"
    
    log_info "Сборка клиента для платформы $target_platform..."
    
    # Создаем директорию для вывода
    mkdir -p "$output_dir"
    
    # Определяем переменные окружения для сборки
    case "$target_platform" in
        "linux-amd64")
            export GOOS=linux
            export GOARCH=amd64
            output_name="xvpn-client-linux-amd64"
            ;;
        "linux-arm64")
            export GOOS=linux
            export GOARCH=arm64
            output_name="xvpn-client-linux-arm64"
            ;;
        "darwin-amd64")
            export GOOS=darwin
            export GOARCH=amd64
            output_name="xvpn-client-darwin-amd64"
            ;;
        "darwin-arm64")
            export GOOS=darwin
            export GOARCH=arm64
            output_name="xvpn-client-darwin-arm64"
            ;;
        "windows-amd64")
            export GOOS=windows
            export GOARCH=amd64
            output_name="xvpn-client-windows-amd64.exe"
            ;;
        "windows-386")
            export GOOS=windows
            export GOARCH=386
            output_name="xvpn-client-windows-386.exe"
            ;;
        *)
            log_error "Неизвестная платформа: $target_platform"
            exit 1
            ;;
    esac
    
    # Сборка
    go build -o "$output_dir/$output_name" -ldflags="-s -w -X main.version=1.0.0" ./cmd/xvpn-client
    
    # Проверка успешности сборки
    if [ $? -eq 0 ]; then
        log_success "Клиент успешно собран: $output_dir/$output_name"
        ls -lh "$output_dir/$output_name"
    else
        log_error "Ошибка сборки клиента"
        exit 1
    fi
}

# Сборка для всех платформ
build_all_platforms() {
    local output_dir="$1"
    
    log_info "Сборка клиента для всех платформ..."
    
    # Список платформ
    platforms=("linux-amd64" "linux-arm64" "darwin-amd64" "darwin-arm64" "windows-amd64" "windows-386")
    
    for platform in "${platforms[@]}"; do
        build_client "$platform" "$output_dir"
    done
    
    log_success "Сборка для всех платформ завершена"
}

# Создание установщиков
create_installers() {
    local output_dir="$1"
    
    log_info "Создание установщиков..."
    
    # Для Linux создаем .deb пакет
    create_deb_installer "$output_dir"
    
    # Для macOS создаем .pkg пакет
    create_pkg_installer "$output_dir"
    
    # Для Windows создаем .exe инсталлятор
    create_exe_installer "$output_dir"
    
    log_success "Установщики созданы"
}

# Создание .deb пакета для Linux
create_deb_installer() {
    local output_dir="$1"
    
    log_info "Создание .deb пакета для Linux..."
    
    # Создаем структуру пакета
    mkdir -p "$output_dir/deb/xvpn-client/DEBIAN"
    mkdir -p "$output_dir/deb/xvpn-client/usr/bin"
    mkdir -p "$output_dir/deb/xvpn-client/usr/share/applications"
    mkdir -p "$output_dir/deb/xvpn-client/usr/share/icons/hicolor/128x128/apps"
    
    # Копируем бинарный файл
    cp "$output_dir/xvpn-client-linux-amd64" "$output_dir/deb/xvpn-client/usr/bin/xvpn-client"
    
    # Создаем control файл
    cat > "$output_dir/deb/xvpn-client/DEBIAN/control" << EOF
Package: xvpn-client
Version: 1.0.0
Section: net
Priority: optional
Architecture: amd64
Maintainer: XVPN Team <support@xvpn.local>
Homepage: https://xvpn.local
Description: XVPN Client - intelligent VPN with AI agents and proxy integration
 Intelligent VPN system that uses AI agents to automatically manage transport
 protocols, monitor connection health, and provide self-healing capabilities.
 Unlike traditional VPN solutions, XVPN continuously adapts to network conditions
 and automatically switches between transports to maintain optimal performance
 and security.
EOF
    
    # Создаем desktop файл
    cat > "$output_dir/deb/xvpn-client/usr/share/applications/xvpn-client.desktop" << EOF
[Desktop Entry]
Name=XVPN Client
Comment=Intelligent VPN with AI agents and proxy integration
Exec=/usr/bin/xvpn-client
Icon=xvpn-client
Terminal=false
Type=Application
Categories=Network;VPN;
Keywords=VPN;Security;Privacy;Proxy;
EOF
    
    # Создаем скрипт postinst
    cat > "$output_dir/deb/xvpn-client/DEBIAN/postinst" << EOF
#!/bin/bash
chmod +x /usr/bin/xvpn-client
echo "XVPN Client успешно установлен"
EOF
    
    chmod +x "$output_dir/deb/xvpn-client/DEBIAN/postinst"
    
    # Создаем .deb пакет
    dpkg-deb --build "$output_dir/deb/xvpn-client" "$output_dir/xvpn-client_1.0.0_amd64.deb"
    
    log_success ".deb пакет создан: $output_dir/xvpn-client_1.0.0_amd64.deb"
}

# Создание .pkg пакета для macOS
create_pkg_installer() {
    local output_dir="$1"
    
    log_info "Создание .pkg пакета для macOS..."
    
    # Создаем структуру пакета
    mkdir -p "$output_dir/pkg/root/usr/local/bin"
    mkdir -p "$output_dir/pkg/scripts"
    
    # Копируем бинарный файл
    cp "$output_dir/xvpn-client-darwin-amd64" "$output_dir/pkg/root/usr/local/bin/xvpn-client"
    
    # Создаем preinstall скрипт
    cat > "$output_dir/pkg/scripts/preinstall" << EOF
#!/bin/bash
echo "Подготовка к установке XVPN Client..."
EOF
    
    # Создаем postinstall скрипт
    cat > "$output_dir/pkg/scripts/postinstall" << EOF
#!/bin/bash
chmod +x /usr/local/bin/xvpn-client
echo "XVPN Client успешно установлен"
EOF
    
    chmod +x "$output_dir/pkg/scripts/preinstall"
    chmod +x "$output_dir/pkg/scripts/postinstall"
    
    # Создаем .pkg пакет (если доступен pkgbuild)
    if command -v pkgbuild &> /dev/null; then
        pkgbuild --root "$output_dir/pkg/root" \
                 --scripts "$output_dir/pkg/scripts" \
                 --identifier com.xvpn.client \
                 --version 1.0.0 \
                 "$output_dir/xvpn-client-1.0.0.pkg"
        
        log_success ".pkg пакет создан: $output_dir/xvpn-client-1.0.0.pkg"
    else
        log_warning "pkgbuild не найден, пропускаем создание .pkg пакета"
    fi
}

# Создание .exe инсталлятора для Windows
create_exe_installer() {
    local output_dir="$1"
    
    log_info "Создание .exe инсталлятора для Windows..."
    
    # Создаем структуру инсталлятора
    mkdir -p "$output_dir/exe"
    
    # Копируем бинарный файл
    cp "$output_dir/xvpn-client-windows-amd64.exe" "$output_dir/exe/xvpn-client.exe"
    
    # Создаем NSIS скрипт (если доступен makensis)
    if command -v makensis &> /dev/null; then
        cat > "$output_dir/exe/installer.nsi" << EOF
; XVPN Client Installer Script
!define APPNAME "XVPN Client"
!define COMPANYNAME "XVPN"
!define DESCRIPTION "Intelligent VPN with AI agents and proxy integration"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://xvpn.local/help"
!define UPDATEURL "https://xvpn.local/update"
!define ABOUTURL "https://xvpn.local/about"

; Main Install Settings
Name "\${APPNAME}"
InstallDir "\$PROGRAMFILES\\\${COMPANYNAME}\\\${APPNAME}"
InstallDirRegKey HKCU "Software\\\${COMPANYNAME}\\\${APPNAME}" ""
OutFile "\${APPNAME}-installer.exe"

; Modern interface settings
!include "MUI2.nsh"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set languages
!insertmacro MUI_LANGUAGE "English"

; The stuff to install
Section "\${APPNAME}" SectionMain
  ; Set output path to the installation directory
  SetOutPath \$INSTDIR
  
  ; Put file there
  File "xvpn-client.exe"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKCU "Software\\\${COMPANYNAME}\\\${APPNAME}" "" \$INSTDIR
  WriteUninstaller "\$INSTDIR\Uninstall.exe"
  
  ; Write shortcuts
  CreateShortCut "\$DESKTOP\\\${APPNAME}.lnk" "\$INSTDIR\xvpn-client.exe"
  CreateShortCut "\$SMPROGRAMS\\\${APPNAME}.lnk" "\$INSTDIR\xvpn-client.exe"
SectionEnd

; Uninstaller
Section "Uninstall"
  ; Remove registry keys
  DeleteRegKey HKCU "Software\\\${COMPANYNAME}\\\${APPNAME}"
  
  ; Remove files
  Delete \$INSTDIR\xvpn-client.exe
  Delete \$INSTDIR\Uninstall.exe
  
  ; Remove shortcuts
  Delete "\$DESKTOP\\\${APPNAME}.lnk"
  Delete "\$SMPROGRAMS\\\${APPNAME}.lnk"
  
  ; Remove directories
  RMDir "\$INSTDIR"
SectionEnd
EOF
        
        # Создаем .exe инсталлятор
        makensis "$output_dir/exe/installer.nsi"
        
        log_success ".exe инсталлятор создан: $output_dir/exe/\${APPNAME}-installer.exe"
    else
        log_warning "makensis не найден, пропускаем создание .exe инсталлятора"
    fi
}

# Создание AppImage для Linux
create_appimage() {
    local output_dir="$1"
    
    log_info "Создание AppImage для Linux..."
    
    # Создаем структуру AppImage
    mkdir -p "$output_dir/AppImage/usr/bin"
    mkdir -p "$output_dir/AppImage/usr/share/applications"
    mkdir -p "$output_dir/AppImage/usr/share/icons/hicolor/128x128/apps"
    
    # Копируем бинарный файл
    cp "$output_dir/xvpn-client-linux-amd64" "$output_dir/AppImage/usr/bin/xvpn-client"
    
    # Создаем desktop файл
    cat > "$output_dir/AppImage/usr/share/applications/xvpn-client.desktop" << EOF
[Desktop Entry]
Name=XVPN Client
Comment=Intelligent VPN with AI agents and proxy integration
Exec=xvpn-client
Icon=xvpn-client
Terminal=false
Type=Application
Categories=Network;VPN;
Keywords=VPN;Security;Privacy;Proxy;
EOF
    
    # Если доступен appimagetool, создаем AppImage
    if command -v appimagetool &> /dev/null; then
        appimagetool "$output_dir/AppImage" "$output_dir/XVPN_Client-x86_64.AppImage"
        log_success "AppImage создан: $output_dir/XVPN_Client-x86_64.AppImage"
    else
        log_warning "appimagetool не найден, пропускаем создание AppImage"
    fi
}

# Архивирование бинарных файлов
archive_binaries() {
    local output_dir="$1"
    
    log_info "Архивирование бинарных файлов..."
    
    # Создаем архивы для каждой платформы
    cd "$output_dir"
    
    # Linux
    tar -czf xvpn-client-linux-amd64.tar.gz xvpn-client-linux-amd64
    tar -czf xvpn-client-linux-arm64.tar.gz xvpn-client-linux-arm64
    
    # macOS
    tar -czf xvpn-client-darwin-amd64.tar.gz xvpn-client-darwin-amd64
    tar -czf xvpn-client-darwin-arm64.tar.gz xvpn-client-darwin-arm64
    
    # Windows
    zip xvpn-client-windows-amd64.zip xvpn-client-windows-amd64.exe
    zip xvpn-client-windows-386.zip xvpn-client-windows-386.exe
    
    log_success "Бинарные файлы заархивированы"
}

# Основная функция
main() {
    local repo_url="https://github.com/Mehan42/chatVPN.git"
    local target_dir="/tmp/xvpn-client-go"
    local output_dir="/tmp/xvpn-client-builds"
    
    log_info "Начало развертывания XVPN клиента на Go"
    
    # Проверка зависимостей
    check_dependencies
    
    # Клонирование репозитория
    clone_repository "$repo_url" "$target_dir"
    
    # Переход в директорию клиента
    cd "$target_dir/xvpn-client-go"
    
    # Сборка для всех платформ
    build_all_platforms "$output_dir"
    
    # Создание установщиков
    create_installers "$output_dir"
    
    # Создание AppImage
    create_appimage "$output_dir"
    
    # Архивирование бинарных файлов
    archive_binaries "$output_dir"
    
    log_success "Развертывание завершено успешно!"
    log_info "Бинарные файлы находятся в: $output_dir"
    
    # Вывод информации о созданных файлах
    echo
    echo "Созданные файлы:"
    ls -lh "$output_dir"
    echo
}

# Запуск основной функции
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi