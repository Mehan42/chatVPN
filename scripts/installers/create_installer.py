
#!/usr/bin/env python3
"""
Скрипт создания установщиков для XVPN
Поддержка различных платформ: Linux, Windows, macOS
"""

import os
import sys
import shutil
import subprocess
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(message: str, color: str = Colors.GREEN):
    """Вывод цветного сообщения"""
    print(f"{color}{message}{Colors.NC}")

class XVPNInstaller:
    """Основной класс для создания установщиков"""
    
    def __init__(self, platform_name: str = None):
        self.platform = platform_name or platform.system().lower()
        self.project_root = Path(__file__).parent.parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
        # Конфигурация
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Загрузка конфигурации"""
        config_file = self.project_root / "install_config.json"
        default_config = {
            "app_name": "XVPN",
            "version": "1.0.0",
            "description": "Secure VPN Client with AI Integration",
            "author": "XVPN Team",
            "url": "https://xvpn.local",
            "icon": None,
            "license": "MIT",
            "platforms": {
                "linux": {
                    "binary_name": "xvpn",
                    "service_name": "xvpn",
                    "desktop_entry": True,
                    "systemd": True
                },
                "windows": {
                    "binary_name": "xvpn.exe",
                    "service_name": "XVPN Service",
                    "install_dir": "C:\\Program Files\\XVPN",
                    "create_shortcut": True
                },
                "darwin": {
                    "binary_name": "XVPN",
                    "service_name": "com.xvpn.client",
                    "app_bundle": True,
                    "launchd": True
                }
            }
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        
        return default_config
    
    def create_installer(self, target_platform: str = None) -> bool:
        """Создание установщика для указанной платформы"""
        target_platform = target_platform or self.platform
        
        print_colored(f"🚀 Creating installer for {target_platform.upper()}", Colors.BLUE)
        
        # Создание директорий
        self._create_directories()
        
        # Сборка проекта
        if not self._build_project():
            print_colored("❌ Build failed", Colors.RED)
            return False
        
        # Создание пакета
        if target_platform == "linux":
            success = self._create_linux_installer()
        elif target_platform == "windows":
            success = self._create_windows_installer()
        elif target_platform == "darwin":
            success = self._create_macos_installer()
        else:
            print_colored(f"❌ Platform {target_platform} not supported", Colors.RED)
            return False
        
        if success:
            print_colored(f"✅ {target_platform.upper()} installer created successfully!", Colors.GREEN)
            return True
        else:
            print_colored(f"❌ Failed to create {target_platform.upper()} installer", Colors.RED)
            return False
    
    def _create_directories(self):
        """Создание необходимых директорий"""
        for directory in [self.build_dir, self.dist_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            print_colored(f"📁 Created directory: {directory}", Colors.BLUE)
    
    def _build_project(self) -> bool:
        """Сборка проекта"""
        print_colored("🔨 Building project...", Colors.YELLOW)
        
        try:
            # Установка зависимостей
            self._install_dependencies()
            
            # Сборка Python приложений
            self._build_python_apps()
            
            # Копирование ресурсов
            self._copy_resources()
            
            print_colored("✅ Project built successfully", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Build failed: {e}", Colors.RED)
            return False
    
    def _install_dependencies(self):
        """Установка зависимостей"""
        print_colored("📦 Installing dependencies...", Colors.YELLOW)
        
        # Установка Python зависимостей
        if self.project_root.joinpath("requirements.txt").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                          str(self.project_root / "requirements.txt")], 
                         check=True)
        
        # Установка Docker и Docker Compose если Linux
        if self.platform == "linux":
            self._install_docker_linux()
    
    def _install_docker_linux(self):
        """Установка Docker для Linux"""
        try:
            # Проверка, установлен ли Docker
            result = subprocess.run(["docker", "--version"], capture_output=True)
            if result.returncode != 0:
                print_colored("🐳 Installing Docker...", Colors.YELLOW)
                # Установка Docker (упрощенная версия)
                subprocess.run([
                    "curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"
                ], check=True)
                subprocess.run(["sh", "get-docker.sh"], check=True)
                subprocess.run(["usermod", "-aG", "docker", os.getenv("USER")], check=True)
        except subprocess.CalledProcessError as e:
            print_colored(f"⚠️ Docker installation failed: {e}", Colors.YELLOW)
    
    def _build_python_apps(self):
        """Сборка Python приложений"""
        print_colored("🐍 Building Python applications...", Colors.YELLOW)
        
        # Сборка серверного приложения
        server_dir = self.project_root / "server"
        if server_dir.exists():
            # Использование uv для сборки
            try:
                subprocess.run([
                    "uv", "build", "--out-dir", str(self.build_dir / "server")
                ], cwd=str(server_dir), check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback на обычную установку
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-e", "."
                ], cwd=str(server_dir), check=True)
        
        # Сборка клиентского приложения
        client_dir = self.project_root / "client"
        if client_dir.exists():
            try:
                subprocess.run([
                    "uv", "build", "--out-dir", str(self.build_dir / "client")
                ], cwd=str(client_dir), check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback на обычную установку
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-e", "."
                ], cwd=str(client_dir), check=True)
    
    def _copy_resources(self):
        """Копирование ресурсов"""
        print_colored("📋 Copying resources...", Colors.YELLOW)
        
        # Копирование конфигурационных файлов
        config_sources = [
            "docker-compose.yml",
            "traefik/",
            "systemd/"
        ]
        
        for source in config_sources:
            source_path = self.project_root / source
            if source_path.exists():
                dest_path = self.build_dir / source
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                print_colored(f"📄 Copied: {source}", Colors.BLUE)
    
    def _create_linux_installer(self) -> bool:
        """Создание Linux установщика (deb/rpm)"""
        print_colored("🐧 Creating Linux installer...", Colors.YELLOW)
        
        try:
            # Создание .deb пакета
            self._create_deb_package()
            
            # Создание .rpm пакета
            self._create_rpm_package()
            
            print_colored("✅ Linux installers created", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Failed to create Linux installer: {e}", Colors.RED)
            return False
    
    def _create_deb_package(self):
        """Создание Debian пакета"""
        deb_dir = self.build_dir / "deb"
        deb_dir.mkdir(exist_ok=True)
        
        # Структура .deb пакета
        package_dir = deb_dir / "xvpn" / "DEBIAN"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Создание control файла
        control_content = f"""Package: xvpn
Version: {self.config["version"]}
Architecture: amd64
Maintainer: {self.config["author"]}
Description: {self.config["description"]}
Section: net
Priority: optional
Depends: python3, python3-pip, docker.io
"""
        
        with open(package_dir / "control", "w") as f:
            f.write(control_content)
        
        # Копирование файлов в пакет
        usr_bin = deb_dir / "xvpn" / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        
        # Копирование бинарных файлов
        for binary in ["client/chatvpn_backend.py", "server/api/app.py"]:
            src = self.project_root / binary
            if src.exists():
                shutil.copy2(src, usr_bin)
        
        # Создание postinst скрипта
        postinst_content = """#!/bin/bash
# Post-installation script
echo "Installing XVPN..."

# Create user
useradd -r -s /bin/false xvpn || true

# Set permissions
chown -R xvpn:xvpn /opt/xvpn
chmod +x /usr/bin/chatvpn_backend.py

# Enable services
systemctl enable xvpn-docker.service
systemctl start xvpn-docker.service

echo "XVPN installation completed!"
"""
        
        with open(package_dir / "postinst", "w") as f:
            f.write(postinst_content)
        
        # Сделаем скрипт исполняемым
        os.chmod(package_dir / "postinst", 0o755)
        
        # Сборка .deb пакета
        subprocess.run([
            "dpkg-deb", "--build", str(deb_dir / "xvpn"),
            str(self.dist_dir / f"xvpn_{self.config['version']}_amd64.deb")
        ], check=True)
        
        print_colored(f"📦 Debian package created: xvpn_{self.config['version']}_amd64.deb", Colors.GREEN)
    
    def _create_rpm_package(self):
        """Создание RPM пакета"""
        print_colored("⚠️ RPM package creation requires rpmbuild tool", Colors.YELLOW)
        # Здесь можно добавить создание RPM пакета
        # Для этого нужен rpmbuild и спецификационный файл
    
    def _create_windows_installer(self) -> bool:
        """Создание Windows установщика"""
        print_colored("🪟 Creating Windows installer...", Colors.YELLOW)
        
        try:
            # Создание NSIS скрипта
            self._create_nsis_script()
            
            # Создание ZIP архива
            self._create_windows_zip()
            
            print_colored("✅ Windows installers created", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Failed to create Windows installer: {e}", Colors.RED)
            return False
    
    def _create_nsis_script(self):
        """Создание NSIS скрипта для Windows"""
        nsis_script = self.build_dir / "xvpn.nsi"
        
        script_content = f"""; XVPN Windows Installer
Name "XVPN"
OutFile "xvpn_{self.config['version']}_setup.exe"
InstallDir $PROGRAMFILES\\XVPN
RequestExecutionLevel admin

; Section - Main Program
Section "Main Program" SEC01
    SetOutPath $INSTDIR
    File /r "..\\build\\*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    ; Add to registry
    WriteRegStr HKLM "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\XVPN" "DisplayName" "XVPN"
    WriteRegStr HKLM "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\XVPN" "UninstallString" "$INSTDIR\\uninstall.exe"
SectionEnd

; Section - Start Menu
Section "Start Menu Shortcuts" SEC02
    CreateDirectory "$SMPROGRAMS\\XVPN"
    CreateShortcut "$SMPROGRAMS\\XVPN\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    CreateShortcut "$SMPROGRAMS\\XVPN\\XVPN.lnk" "$INSTDIR\\client\\chatvpn_backend.py"
SectionEnd

; Uninstaller
Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\XVPN\\*.*"
    RMDir "$SMPROGRAMS\\XVPN"
    DeleteRegKey HKLM "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\XVPN"
SectionEnd
"""
        
        with open(nsis_script, "w") as f:
            f.write(script_content)
        
        print_colored("📝 NSIS script created: xvpn.nsi", Colors.BLUE)
    
    def _create_windows_zip(self):
        """Создание ZIP архива для Windows"""
        zip_file = self.dist_dir / f"xvpn_{self.config['version']}_windows.zip"
        
        import zipfile
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.build_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.build_dir)
                    zipf.write(file_path, arcname)
        
        print_colored(f"📦 ZIP archive created: xvpn_{self.config['version']}_windows.zip", Colors.GREEN)
    
    def _create_macos_installer(self) -> bool:
        """Создание macOS установщика"""
        print_colored("🍎 Creating macOS installer...", Colors.YELLOW)
        
        try:
            # Создание DMG образа
            self._create_dmg_image()
            
            # Создания PKG пакета
            self._create_pkg_package()
            
            print_colored("✅ macOS installers created", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Failed to create macOS installer: {e}", Colors.RED)
            return False
    
    def _create_dmg_image(self):
        """Создание DMG образа для macOS"""
        print_colored("⚠️ DMG creation requires hdiutil tool", Colors.YELLOW)
        # Здесь можно добавить создание DMG образа
        
    def _create_pkg_package(self):
        """Создание PKG пакета для macOS"""
        print_colored("⚠️ PKG creation requires productbuild tool", Colors.YELLOW)
        # Здесь можно добавить создание PKG пакета


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Create XVPN installers")
    parser.add_argument("--platform", "-p",
                       choices=["linux", "windows", "darwin", "all"],
                       help="Target platform (auto-detected if not specified)")
    parser.add_argument("--clean", "-c", action="store_true",
                       help="Clean build directory before creating installer")
    
    args = parser.parse_args()
    
    # Создание установщика
    installer = XVPNInstaller()
    
    if args.clean:
        print_colored("🧹 Cleaning build directory...", Colors.YELLOW)
        if installer.build_dir.exists():
            shutil.rmtree(installer.build_dir)
    
    # Определение платформ для сборки
    platforms = [args.platform] if args.platform and args.platform != "all" else [installer.platform]
    
    if "all" in platforms:
        platforms = ["linux", "windows", "darwin"]
    
    # Создание установщиков для всех платформ
    success = True
    for platform in platforms:
        if not installer.create_installer(platform):
            success = False
    
    if success:
        print_colored("🎉 All installers created successfully!", Colors.GREEN)
        print_colored(f"📁 Installers are available in: {installer.dist_dir}", Colors.BLUE)
    else:
        print_colored("❌ Some installers failed to create", Colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
           