#!/bin/bash
set -euo pipefail

# Package AnkiBlur for distribution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
DIST_DIR="$ROOT_DIR/dist"
PACKAGE_DIR="$ROOT_DIR/packages"
APP_NAME="AnkiBlur"
BINARY_NAME="ankiblur"

# Platform detection
PLATFORM="${PLATFORM:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
ARCH="${ARCH:-$(uname -m)}"

# Normalize architecture names
case "$ARCH" in
    x86_64|amd64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    armv7l) ARCH="armhf" ;;
esac

# Version info
BLUR_VERSION="${BLUR_VERSION:-1.0.0}"
ANKI_VERSION="${ANKI_VERSION:-unknown}"

echo "Packaging AnkiBlur $BLUR_VERSION for $PLATFORM-$ARCH"

# Function to setup packaging environment
setup_packaging() {
    echo "Setting up packaging environment..."

    # Create package directory
    mkdir -p "$PACKAGE_DIR"

    # Clean previous packages for this platform/arch
    rm -f "$PACKAGE_DIR"/*"$PLATFORM"*"$ARCH"*

    echo "Packaging environment ready"
}

# Function to create Linux packages
package_linux() {
    echo "Creating Linux packages..."

    local app_dir="$PACKAGE_DIR/AnkiBlur-linux-$ARCH"
    mkdir -p "$app_dir"

    # Copy built artifacts
    cp -r "$DIST_DIR"/* "$app_dir/"

    # Create Linux-specific files
    create_linux_desktop_file "$app_dir"
    create_linux_launcher "$app_dir"

    # Create AppImage if tools available
    if command -v appimagetool >/dev/null 2>&1; then
        create_appimage "$app_dir"
    fi

    # Create tar.gz archive
    cd "$PACKAGE_DIR"
    tar -czf "AnkiBlur-$BLUR_VERSION-linux-$ARCH.tar.gz" "AnkiBlur-linux-$ARCH"
    rm -rf "AnkiBlur-linux-$ARCH"

    # Create .deb package if tools available
    if command -v dpkg-deb >/dev/null 2>&1; then
        create_deb_package
    fi

    echo "Linux packaging complete"
}

# Function to create Linux desktop file
create_linux_desktop_file() {
    local app_dir="$1"

    cat > "$app_dir/ankiblur.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AnkiBlur
Comment=Spaced repetition flashcard program with transparency effects
Exec=ankiblur
Icon=ankiblur
Categories=Education;
StartupNotify=true
MimeType=application/x-anki-deck;
EOF
}

# Function to create Linux launcher script
create_linux_launcher() {
    local app_dir="$1"

    cat > "$app_dir/ankiblur" << 'EOF'
#!/bin/bash
# AnkiBlur launcher script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set library path for bundled libraries
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:${LD_LIBRARY_PATH:-}"

# Set Python path
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Launch AnkiBlur
exec python3 "$SCRIPT_DIR/aqt" "$@"
EOF

    chmod +x "$app_dir/ankiblur"
}

# Function to create AppImage
create_appimage() {
    local app_dir="$1"

    echo "Creating AppImage..."

    # Create AppDir structure
    local appdir="$PACKAGE_DIR/AnkiBlur.AppDir"
    mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" "$appdir/usr/share/icons/hicolor/256x256/apps"

    # Copy application files
    cp -r "$app_dir"/* "$appdir/usr/bin/"

    # Copy desktop file and icon
    cp "$app_dir/ankiblur.desktop" "$appdir/usr/share/applications/"
    # TODO: Copy icon file when available

    # Create AppRun
    cat > "$appdir/AppRun" << 'EOF'
#!/bin/bash
exec "$APPDIR/usr/bin/ankiblur" "$@"
EOF
    chmod +x "$appdir/AppRun"

    # Build AppImage
    cd "$PACKAGE_DIR"
    appimagetool "AnkiBlur.AppDir" "AnkiBlur-$BLUR_VERSION-linux-$ARCH.AppImage"
    rm -rf "AnkiBlur.AppDir"
}

# Function to create .deb package
create_deb_package() {
    echo "Creating .deb package..."

    local deb_dir="$PACKAGE_DIR/ankiblur-deb"
    local control_dir="$deb_dir/DEBIAN"
    local usr_dir="$deb_dir/usr"

    mkdir -p "$control_dir" "$usr_dir/bin" "$usr_dir/share/applications" "$usr_dir/share/doc/ankiblur"

    # Create control file
    cat > "$control_dir/control" << EOF
Package: ankiblur
Version: $BLUR_VERSION
Section: education
Priority: optional
Architecture: amd64
Depends: python3, python3-pip
Maintainer: AnkiBlur Team
Description: Spaced repetition flashcard program with transparency effects
 AnkiBlur is a modified version of Anki with additional transparency
 and visual effects for a more modern interface.
EOF

    # Copy application files
    cp -r "$DIST_DIR"/* "$usr_dir/bin/"

    # Build .deb
    cd "$PACKAGE_DIR"
    dpkg-deb --build ankiblur-deb "ankiblur_${BLUR_VERSION}_amd64.deb"
    rm -rf ankiblur-deb
}

# Function to create Windows packages
package_windows() {
    echo "Creating Windows packages..."

    local app_dir="$PACKAGE_DIR/AnkiBlur-windows-$ARCH"
    mkdir -p "$app_dir"

    # Copy built artifacts
    cp -r "$DIST_DIR"/* "$app_dir/"

    # Create Windows launcher
    create_windows_launcher "$app_dir"

    # Create ZIP archive
    cd "$PACKAGE_DIR"
    if command -v 7z >/dev/null 2>&1; then
        7z a "AnkiBlur-$BLUR_VERSION-windows-$ARCH.zip" "AnkiBlur-windows-$ARCH"
    else
        zip -r "AnkiBlur-$BLUR_VERSION-windows-$ARCH.zip" "AnkiBlur-windows-$ARCH"
    fi
    rm -rf "AnkiBlur-windows-$ARCH"

    # Create installer if NSIS available
    if command -v makensis >/dev/null 2>&1; then
        create_windows_installer
    fi

    echo "Windows packaging complete"
}

# Function to create Windows launcher
create_windows_launcher() {
    local app_dir="$1"

    cat > "$app_dir/ankiblur.bat" << 'EOF'
@echo off
setlocal

set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

python "%SCRIPT_DIR%\aqt" %*
EOF
}

# Function to create Windows installer
create_windows_installer() {
    echo "Creating Windows installer..."

    # Create NSIS script
    cat > "$PACKAGE_DIR/ankiblur-installer.nsi" << EOF
!include "MUI2.nsh"

Name "AnkiBlur"
OutFile "AnkiBlur-$BLUR_VERSION-windows-$ARCH-installer.exe"
InstallDir "\$PROGRAMFILES\\AnkiBlur"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "\$INSTDIR"
    File /r "$DIST_DIR\\*"

    CreateDirectory "\$SMPROGRAMS\\AnkiBlur"
    CreateShortCut "\$SMPROGRAMS\\AnkiBlur\\AnkiBlur.lnk" "\$INSTDIR\\ankiblur.bat"
    CreateShortCut "\$DESKTOP\\AnkiBlur.lnk" "\$INSTDIR\\ankiblur.bat"

    WriteUninstaller "\$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "\$INSTDIR\\*"
    RMDir /r "\$INSTDIR"
    Delete "\$SMPROGRAMS\\AnkiBlur\\*"
    RMDir "\$SMPROGRAMS\\AnkiBlur"
    Delete "\$DESKTOP\\AnkiBlur.lnk"
SectionEnd
EOF

    # Build installer
    cd "$PACKAGE_DIR"
    makensis ankiblur-installer.nsi
    rm ankiblur-installer.nsi
}

# Function to create macOS packages
package_macos() {
    echo "Creating macOS packages..."

    local app_dir="$PACKAGE_DIR/AnkiBlur-macos-$ARCH"
    mkdir -p "$app_dir"

    # Copy built artifacts
    cp -r "$DIST_DIR"/* "$app_dir/"

    # Create .app bundle if not already created
    if [[ ! -d "$app_dir/AnkiBlur.app" ]]; then
        create_macos_app_bundle "$app_dir"
    fi

    # Create DMG
    create_macos_dmg "$app_dir"

    echo "macOS packaging complete"
}

# Function to create macOS .app bundle
create_macos_app_bundle() {
    local app_dir="$1"
    local bundle_dir="$app_dir/AnkiBlur.app"

    mkdir -p "$bundle_dir/Contents/MacOS" "$bundle_dir/Contents/Resources"

    # Create Info.plist
    cat > "$bundle_dir/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ankiblur</string>
    <key>CFBundleIdentifier</key>
    <string>net.ankiblur.ankiblur</string>
    <key>CFBundleName</key>
    <string>AnkiBlur</string>
    <key>CFBundleVersion</key>
    <string>$BLUR_VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$BLUR_VERSION</string>
</dict>
</plist>
EOF

    # Copy application files
    cp -r "$DIST_DIR"/* "$bundle_dir/Contents/MacOS/"

    # Create launcher script
    cat > "$bundle_dir/Contents/MacOS/ankiblur" << 'EOF'
#!/bin/bash
BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$BUNDLE_DIR/Contents/MacOS:${PYTHONPATH:-}"
exec python3 "$BUNDLE_DIR/Contents/MacOS/aqt" "$@"
EOF
    chmod +x "$bundle_dir/Contents/MacOS/ankiblur"
}

# Function to create macOS DMG
create_macos_dmg() {
    local app_dir="$1"

    echo "Creating DMG..."

    cd "$PACKAGE_DIR"
    if command -v hdiutil >/dev/null 2>&1; then
        hdiutil create -srcfolder "$app_dir" -volname "AnkiBlur $BLUR_VERSION" "AnkiBlur-$BLUR_VERSION-macos-$ARCH.dmg"
    else
        # Fallback to tar.gz on non-macOS systems
        tar -czf "AnkiBlur-$BLUR_VERSION-macos-$ARCH.tar.gz" "AnkiBlur-macos-$ARCH"
    fi

    rm -rf "AnkiBlur-macos-$ARCH"
}

# Function to verify packages
verify_packages() {
    echo "Verifying packages..."

    if [[ ! -d "$PACKAGE_DIR" || -z "$(ls -A "$PACKAGE_DIR" 2>/dev/null)" ]]; then
        echo "Error: No packages created"
        exit 1
    fi

    echo "Created packages:"
    ls -la "$PACKAGE_DIR"

    echo "Package verification complete"
}

# Main function
main() {
    echo "Packaging AnkiBlur for distribution..."

    # Verify build artifacts exist
    if [[ ! -d "$DIST_DIR" || -z "$(ls -A "$DIST_DIR" 2>/dev/null)" ]]; then
        echo "Error: No build artifacts found in $DIST_DIR"
        echo "Run build.sh first"
        exit 1
    fi

    # Setup packaging environment
    setup_packaging

    # Package for target platform
    case "$PLATFORM" in
        linux)
            package_linux
            ;;
        windows)
            package_windows
            ;;
        darwin|macos)
            package_macos
            ;;
        *)
            echo "Error: Unsupported platform: $PLATFORM"
            exit 1
            ;;
    esac

    # Copy packages to dist for GitHub Actions
    cp "$PACKAGE_DIR"/* "$DIST_DIR/" 2>/dev/null || true

    # Verify packages
    verify_packages

    echo "AnkiBlur packaging complete for $PLATFORM-$ARCH"
    echo "Packages available in: $PACKAGE_DIR"
}

main "$@"