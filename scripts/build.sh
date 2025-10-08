#!/bin/bash
set -euo pipefail

# Build AnkiBlur from patched Anki source

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ANKI_DIR="$ROOT_DIR/anki"
BUILD_DIR="$ROOT_DIR/build"
DIST_DIR="$ROOT_DIR/dist"
CONFIG_FILE="$ROOT_DIR/configs/build-config.json"

# Platform detection
PLATFORM="${PLATFORM:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
ARCH="${ARCH:-$(uname -m)}"

# Normalize architecture names
case "$ARCH" in
    x86_64|amd64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    armv7l) ARCH="armhf" ;;
esac

echo "Building for platform: $PLATFORM, architecture: $ARCH"

# Function to setup build environment
setup_build_env() {
    echo "Setting up build environment..."

    # Create build and dist directories
    mkdir -p "$BUILD_DIR" "$DIST_DIR"

    # Install Python dependencies
    echo "Installing Python build dependencies..."
    cd "$ANKI_DIR"

    # Install required Python packages
    pip install --upgrade pip wheel setuptools
    pip install build

    # Install Anki's dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi

    # Install from pyproject.toml
    pip install -e .

    cd "$ROOT_DIR"
}

# Function to configure build for platform
configure_build() {
    echo "Configuring build for $PLATFORM..."
    cd "$ANKI_DIR"

    case "$PLATFORM" in
        linux)
            configure_linux_build
            ;;
        windows)
            configure_windows_build
            ;;
        darwin|macos)
            configure_macos_build
            ;;
        *)
            echo "Error: Unsupported platform: $PLATFORM"
            exit 1
            ;;
    esac

    cd "$ROOT_DIR"
}

# Function to configure Linux build
configure_linux_build() {
    echo "Configuring Linux build..."

    # Install system dependencies if running on Linux
    if [[ "$PLATFORM" == "linux" && -z "${GITHUB_ACTIONS:-}" ]]; then
        echo "Installing Linux build dependencies..."
        # Note: In GitHub Actions, these should be installed in the workflow
        sudo apt-get update || true
        sudo apt-get install -y build-essential python3-dev || true
    fi

    # Set environment variables for Linux
    export PYTHONPATH="$ANKI_DIR:${PYTHONPATH:-}"
}

# Function to configure Windows build
configure_windows_build() {
    echo "Configuring Windows build..."

    # Windows-specific build configuration
    export PYTHONPATH="$ANKI_DIR;${PYTHONPATH:-}"

    # Ensure we have the right tools
    if ! command -v protoc >/dev/null 2>&1; then
        echo "Error: protoc not found. Install Protocol Buffers compiler."
        exit 1
    fi
}

# Function to configure macOS build
configure_macos_build() {
    echo "Configuring macOS build..."

    # macOS-specific build configuration
    export PYTHONPATH="$ANKI_DIR:${PYTHONPATH:-}"

    # Ensure we have the right tools
    if ! command -v protoc >/dev/null 2>&1; then
        echo "Error: protoc not found. Install with: brew install protobuf"
        exit 1
    fi
}

# Function to build Anki/AnkiBlur
build_anki() {
    echo "Building AnkiBlur..."
    cd "$ANKI_DIR"

    # Clean any previous builds
    if [[ -d "build" ]]; then
        rm -rf build
    fi

    # Run the build
    echo "Running Anki build system..."

    # Use Anki's build system
    if [[ -f "build/configure" ]]; then
        echo "Using Anki's configure script..."
        ./build/configure

        # Build using ninja or make
        if command -v ninja >/dev/null 2>&1; then
            ninja -C build
        else
            make -C build -j$(nproc 2>/dev/null || echo 4)
        fi
    else
        # Fallback to Python build
        echo "Using Python build system..."
        python -m build --wheel
    fi

    cd "$ROOT_DIR"
}

# Function to collect build artifacts
collect_artifacts() {
    echo "Collecting build artifacts..."
    cd "$ANKI_DIR"

    # Clear dist directory
    rm -rf "$DIST_DIR"/*

    # Find and copy built artifacts
    if [[ -d "dist" ]]; then
        echo "Copying Python wheel/sdist artifacts..."
        cp -r dist/* "$DIST_DIR/"
    fi

    if [[ -d "build/dist" ]]; then
        echo "Copying native build artifacts..."
        cp -r build/dist/* "$DIST_DIR/"
    fi

    # Copy any generated executables
    find . -name "anki" -type f -executable | while read -r exe; do
        echo "Found executable: $exe"
        cp "$exe" "$DIST_DIR/ankiblur-$PLATFORM-$ARCH"
    done

    # Platform-specific artifact collection
    case "$PLATFORM" in
        linux)
            collect_linux_artifacts
            ;;
        windows)
            collect_windows_artifacts
            ;;
        darwin|macos)
            collect_macos_artifacts
            ;;
    esac

    cd "$ROOT_DIR"
}

# Function to collect Linux artifacts
collect_linux_artifacts() {
    echo "Collecting Linux artifacts..."

    # Look for AppImage or binary
    find . -name "*.AppImage" -o -name "anki-*" -type f | while read -r file; do
        echo "Found Linux artifact: $file"
        cp "$file" "$DIST_DIR/"
    done
}

# Function to collect Windows artifacts
collect_windows_artifacts() {
    echo "Collecting Windows artifacts..."

    # Look for Windows executables and installers
    find . -name "*.exe" -o -name "*.msi" -type f | while read -r file; do
        echo "Found Windows artifact: $file"
        cp "$file" "$DIST_DIR/"
    done
}

# Function to collect macOS artifacts
collect_macos_artifacts() {
    echo "Collecting macOS artifacts..."

    # Look for .app bundles and .dmg files
    find . -name "*.app" -o -name "*.dmg" | while read -r file; do
        echo "Found macOS artifact: $file"
        if [[ -d "$file" ]]; then
            cp -r "$file" "$DIST_DIR/"
        else
            cp "$file" "$DIST_DIR/"
        fi
    done
}

# Function to verify build
verify_build() {
    echo "Verifying build..."

    if [[ ! -d "$DIST_DIR" || -z "$(ls -A "$DIST_DIR" 2>/dev/null)" ]]; then
        echo "Error: No build artifacts found in $DIST_DIR"
        exit 1
    fi

    echo "Build artifacts:"
    ls -la "$DIST_DIR"

    echo "Build verification complete"
}

# Main function
main() {
    echo "Building AnkiBlur from patched source..."

    # Verify Anki source exists and is patched
    if [[ ! -d "$ANKI_DIR" ]]; then
        echo "Error: Anki source directory not found at $ANKI_DIR"
        echo "Run get_anki.sh and apply_patches.sh first"
        exit 1
    fi

    # Setup build environment
    setup_build_env

    # Configure for target platform
    configure_build

    # Build AnkiBlur
    build_anki

    # Collect artifacts
    collect_artifacts

    # Verify build
    verify_build

    echo "AnkiBlur build complete for $PLATFORM-$ARCH"
    echo "Artifacts available in: $DIST_DIR"
}

main "$@"