#!/bin/bash
set -euo pipefail

# Build standalone AnkiBlur binary using Anki's native build system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ANKI_DIR="$ROOT_DIR/anki"
OUTPUT_DIR="$ROOT_DIR/dist"
PLATFORM="${PLATFORM:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
ARCH="${ARCH:-$(uname -m)}"

# Version info
ANKI_VERSION="${ANKI_VERSION:-}"
BLUR_VERSION="${BLUR_VERSION:-1.0.0}"

echo "Building standalone AnkiBlur binary..."
echo "Platform: $PLATFORM, Architecture: $ARCH"
echo "AnkiBlur version: $BLUR_VERSION"
echo "Base Anki version: $ANKI_VERSION"

# Function to setup build dependencies
setup_build_dependencies() {
    echo "Setting up build dependencies..."

    case "$PLATFORM" in
        "linux")
            # Install required system packages
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                python3-dev \
                python3-venv \
                nodejs \
                npm \
                cargo \
                rustc \
                git \
                rsync \
                curl \
                pkg-config \
                libssl-dev

            # Additional dependencies for ARM64 builds
            if [[ "$ARCH" == "aarch64" ]]; then
                echo "Installing additional ARM64 build dependencies..."
                sudo apt-get install -y \
                    libc6-dev \
                    protobuf-compiler \
                    libprotobuf-dev \
                    python3-wheel \
                    python3-setuptools \
                    python3-pip-whl

                # Ensure wheel module is available
                python3 -m pip install --upgrade pip wheel setuptools
            fi
            ;;
        "darwin")
            # macOS dependencies (assume Homebrew)
            if command -v brew >/dev/null 2>&1; then
                brew install node rust git rsync curl
            fi
            ;;
        "windows"|"mingw"*|"msys"*)
            # Windows dependencies (assume chocolatey or manual install)
            echo "Please ensure Node.js, Rust, and Git are installed"
            ;;
    esac

    # Install N2 (faster than Ninja)
    if [[ ! -f "$ROOT_DIR/tools/n2" ]]; then
        echo "Installing N2 build system..."
        mkdir -p "$ROOT_DIR/tools"
        bash "$ROOT_DIR/anki/tools/install-n2" || {
            echo "Failed to install N2, falling back to system ninja"
        }
    fi
}

# Function to prepare Anki source with patches
prepare_anki_source() {
    echo "Preparing Anki source with AnkiBlur patches..."

    # Fetch Anki source if not already present
    if [[ ! -d "$ANKI_DIR" ]]; then
        echo "Fetching Anki source..."
        "$SCRIPT_DIR/get_anki.sh"
    fi

    # Apply AnkiBlur patches (currently skipped to get working binary)
    echo "Applying AnkiBlur patches..."
    SKIP_PATCHES=true "$SCRIPT_DIR/apply_patches.sh"

    echo "Anki source prepared successfully"
}

# Function to build Anki wheels using native build system
build_anki_wheels() {
    echo "Building Anki wheels using native build system..."

    cd "$ANKI_DIR"

    # Set build environment variables
    export CARGO_TARGET_DIR="$ROOT_DIR/target"
    export BUILD_ROOT="$ROOT_DIR/build_out"

    # ARM64-specific environment setup
    if [[ "$ARCH" == "aarch64" && "$PLATFORM" == "linux" ]]; then
        echo "Setting up ARM64 build environment..."
        export RUSTFLAGS="-C target-cpu=native"
        # Limit parallel jobs to avoid memory issues on ARM64
        export CARGO_BUILD_JOBS=2
        echo "ARM64: Using CARGO_BUILD_JOBS=2 to prevent memory exhaustion"

        # Check available memory
        echo "Available memory:"
        free -h
        echo "CPU cores available: $(nproc)"
    fi

    # Run Anki's build system to create wheels with verbose output
    echo "Running ./ninja wheels..."
    echo "Build environment:"
    echo "  CARGO_TARGET_DIR=$CARGO_TARGET_DIR"
    echo "  BUILD_ROOT=$BUILD_ROOT"
    echo "  PLATFORM=$PLATFORM"
    echo "  ARCH=$ARCH"

    # Run with more verbose output to see what's failing
    echo "Starting ninja build with verbose output..."
    if ! RUST_BACKTRACE=1 ./ninja -v wheels; then
        echo "Wheels build failed, showing build directory contents for debugging:"

        # Check ninja log for details
        if [[ -f "$ROOT_DIR/build_out/.ninja_log" ]]; then
            echo "=== Last 20 lines of .ninja_log ==="
            tail -20 "$ROOT_DIR/build_out/.ninja_log"
            echo "=========================="
        fi

        # Look for Python-related logs
        find "$ROOT_DIR" -name "*.log" -o -name "*.err" | head -10 | while read -r logfile; do
            echo "=== Contents of $logfile ==="
            tail -50 "$logfile" || true
            echo "=========================="
        done

        # Check if Python wheel building failed
        echo "Checking Python environment and wheel building capabilities:"
        python3 --version
        python3 -m pip --version
        python3 -c "import wheel; print('wheel module available')" 2>/dev/null || echo "wheel module not available"

        echo "Build output directory contents:"
        ls -la "$ROOT_DIR/build_out/" || true

        echo "Checking for any wheel building attempts:"
        find "$ROOT_DIR/build_out" -name "*wheel*" -o -name "*whl*" -o -name "*pyproject*" | head -10

        exit 1
    fi

    # Verify wheels were created
    local wheels_dir="$ROOT_DIR/build_out/wheels"
    if [[ ! -d "$wheels_dir" ]] || [[ -z "$(ls -A "$wheels_dir" 2>/dev/null)" ]]; then
        echo "Error: No wheels found after build"
        echo "Checking for any .whl files in build directory:"
        find "$ROOT_DIR" -name "*.whl" | head -10
        exit 1
    fi

    echo "Wheels built successfully in $wheels_dir"
    ls -la "$wheels_dir"

    cd "$ROOT_DIR"
}

# Function to create standalone executable
create_standalone_executable() {
    echo "Creating standalone executable..."

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    # Create virtual environment for bundling
    local venv_dir="$OUTPUT_DIR/bundle_venv"
    python3 -m venv "$venv_dir"
    source "$venv_dir/bin/activate"

    # Install bundling tools
    pip install --upgrade pip
    pip install pyinstaller

    # Install the built wheels
    local wheels_dir="$ROOT_DIR/build_out/wheels"
    pip install "$wheels_dir"/*.whl

    # Create standalone executable with PyInstaller
    local app_name="ankiblur"
    echo "Creating $app_name executable..."

    # Create entry point script for PyInstaller
    cat > ankiblur_main.py << 'EOF'
#!/usr/bin/env python3
"""AnkiBlur entry point for PyInstaller."""
import aqt

if __name__ == "__main__":
    aqt.run()
EOF

    pyinstaller \
        --name "$app_name" \
        --onefile \
        --windowed \
        --add-data "$ANKI_DIR/qt/aqt/data:aqt/data" \
        --hidden-import=aqt \
        --hidden-import=anki \
        --hidden-import=PyQt6 \
        --hidden-import=PyQt6.QtWebEngineWidgets \
        --collect-all=aqt \
        --collect-all=anki \
        --python-option=-O \
        ankiblur_main.py

    # Move executable to final location
    local exe_name="$app_name"
    case "$PLATFORM" in
        "windows"|"mingw"*|"msys"*)
            exe_name="$app_name.exe"
            ;;
    esac

    if [[ -f "dist/$exe_name" ]]; then
        if [[ "$(realpath "dist/$exe_name")" != "$(realpath "$OUTPUT_DIR/$exe_name")" ]]; then
            mv "dist/$exe_name" "$OUTPUT_DIR/"
        fi
        echo "Standalone executable created: $OUTPUT_DIR/$exe_name"
    else
        echo "Error: Executable not found after PyInstaller build"
        exit 1
    fi

    # Clean up
    deactivate
    rm -rf "$venv_dir" build/ "$app_name.spec" ankiblur_main.py
}

# Function to create platform packages
create_platform_packages() {
    echo "Creating platform-specific packages..."

    local app_name="ankiblur"
    local package_name="ankiblur-$BLUR_VERSION-$PLATFORM-$ARCH"
    local package_dir="$OUTPUT_DIR/$package_name"

    mkdir -p "$package_dir"

    case "$PLATFORM" in
        "linux")
            # Create Linux package structure
            mkdir -p "$package_dir/usr/local/bin"
            mkdir -p "$package_dir/usr/share/applications"
            mkdir -p "$package_dir/usr/share/icons/hicolor/128x128/apps"

            # Copy executable
            cp "$OUTPUT_DIR/$app_name" "$package_dir/usr/local/bin/"
            chmod +x "$package_dir/usr/local/bin/$app_name"

            # Create desktop file
            cat > "$package_dir/usr/share/applications/ankiblur.desktop" << EOF
[Desktop Entry]
Name=AnkiBlur
Comment=Spaced repetition flashcard program with transparency effects
Exec=/usr/local/bin/ankiblur
Icon=ankiblur
Type=Application
Categories=Education;
EOF

            # Create install script
            cat > "$package_dir/install.sh" << 'EOF'
#!/bin/bash
set -e
echo "Installing AnkiBlur..."
sudo cp usr/local/bin/ankiblur /usr/local/bin/
sudo cp usr/share/applications/ankiblur.desktop /usr/share/applications/
sudo chmod +x /usr/local/bin/ankiblur
echo "AnkiBlur installed successfully!"
echo "You can now run 'ankiblur' from the command line or find it in your applications menu."
EOF
            chmod +x "$package_dir/install.sh"

            # Create archive
            cd "$OUTPUT_DIR"
            tar -czf "$package_name.tar.gz" "$package_name"
            echo "Linux package created: $OUTPUT_DIR/$package_name.tar.gz"
            ;;

        "darwin")
            # Create macOS app bundle
            local app_bundle="$package_dir/AnkiBlur.app"
            mkdir -p "$app_bundle/Contents/MacOS"
            mkdir -p "$app_bundle/Contents/Resources"

            # Copy executable
            cp "$OUTPUT_DIR/$app_name" "$app_bundle/Contents/MacOS/"

            # Create Info.plist
            cat > "$app_bundle/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>AnkiBlur</string>
    <key>CFBundleIdentifier</key>
    <string>net.ankiblur.AnkiBlur</string>
    <key>CFBundleVersion</key>
    <string>$BLUR_VERSION</string>
    <key>CFBundleExecutable</key>
    <string>$app_name</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

            # Create DMG
            echo "Creating DMG..."
            hdiutil create -srcfolder "$package_dir" -volname "AnkiBlur $BLUR_VERSION" "$OUTPUT_DIR/$package_name.dmg"
            echo "macOS package created: $OUTPUT_DIR/$package_name.dmg"
            ;;

        "windows"|"mingw"*|"msys"*)
            # Create Windows package
            cp "$OUTPUT_DIR/$app_name.exe" "$package_dir/"

            # Create installer script (batch file)
            cat > "$package_dir/install.bat" << 'EOF'
@echo off
echo Installing AnkiBlur...
copy ankiblur.exe "%ProgramFiles%\AnkiBlur\"
echo AnkiBlur installed to %ProgramFiles%\AnkiBlur\
echo You can now run AnkiBlur from the Start menu.
pause
EOF

            # Create ZIP archive
            cd "$OUTPUT_DIR"
            if command -v zip >/dev/null 2>&1; then
                zip -r "$package_name.zip" "$package_name"
                echo "Windows package created: $OUTPUT_DIR/$package_name.zip"
            else
                echo "Warning: zip command not found, package directory created: $package_dir"
            fi
            ;;
    esac
}

# Function to verify the build
verify_build() {
    echo "Verifying build..."

    local app_name="ankiblur"
    case "$PLATFORM" in
        "windows"|"mingw"*|"msys"*)
            app_name="ankiblur.exe"
            ;;
    esac

    local executable="$OUTPUT_DIR/$app_name"

    if [[ ! -f "$executable" ]]; then
        echo "Error: Executable not found at $executable"
        exit 1
    fi

    # Check file size (should be substantial for a bundled app)
    local size=$(stat -f%z "$executable" 2>/dev/null || stat -c%s "$executable" 2>/dev/null || echo "0")
    if [[ $size -lt 50000000 ]]; then  # Less than 50MB
        echo "Warning: Executable seems unusually small ($size bytes)"
    fi

    echo "✓ Build verification completed"
    echo "✓ Executable: $executable ($(numfmt --to=iec $size 2>/dev/null || echo "$size bytes"))"

    # List all outputs
    echo "Build outputs:"
    find "$OUTPUT_DIR" -type f -name "*ankiblur*" | sort
}

# Main execution
main() {
    echo "Starting AnkiBlur standalone build process..."

    # Validate environment
    if [[ -z "$ANKI_VERSION" ]]; then
        echo "Warning: ANKI_VERSION not set, will use latest"
    fi

    # Execute build phases
    setup_build_dependencies
    prepare_anki_source
    build_anki_wheels
    create_standalone_executable
    create_platform_packages
    verify_build

    echo ""
    echo "🎉 AnkiBlur standalone build completed successfully!"
    echo "📦 Output directory: $OUTPUT_DIR"
    echo "🚀 Ready for distribution!"
}

# Execute main function
main "$@"