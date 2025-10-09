#!/bin/bash
set -euo pipefail

# Build AnkiBlur Rust launcher for multiple architectures

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
LAUNCHER_DIR="$ROOT_DIR/qt/launcher"
OUTPUT_DIR="$ROOT_DIR/out/launcher"
TARGET_DIR="${CARGO_TARGET_DIR:-$ROOT_DIR/target}"

# Version info
BLUR_VERSION="${BLUR_VERSION:-1.0.0}"

echo "Building AnkiBlur launcher for version $BLUR_VERSION"

# Function to setup Rust toolchain
setup_rust() {
    echo "Setting up Rust toolchain..."

    # Ensure rustup is available
    if ! command -v rustup >/dev/null 2>&1; then
        echo "Error: rustup not found. Please install Rust: https://rustup.rs/"
        exit 1
    fi

    # Add cross-compilation targets
    echo "Adding cross-compilation targets..."
    rustup target add x86_64-unknown-linux-gnu
    rustup target add aarch64-unknown-linux-gnu
}

# Function to setup cross-compilation dependencies
setup_cross_compilation() {
    echo "Setting up cross-compilation dependencies..."

    # Platform-specific setup
    case "$(uname -s)" in
        Linux)
            # Install cross-compilation toolchain for ARM64
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update
                sudo apt-get install -y gcc-aarch64-linux-gnu
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y gcc-aarch64-linux-gnu
            else
                echo "Warning: Could not install ARM64 cross-compilation toolchain automatically"
                echo "Please install gcc-aarch64-linux-gnu manually"
            fi
            ;;
        *)
            echo "Note: Cross-compilation setup may need manual configuration on this platform"
            ;;
    esac
}

# Function to download uv binaries
download_uv_binaries() {
    echo "Downloading uv binaries..."

    local uv_version="0.5.8"  # Update this to match Anki's version
    local uv_dir="$OUTPUT_DIR/uv-binaries"

    mkdir -p "$uv_dir"

    # Download uv for x86_64
    echo "Downloading uv for x86_64..."
    curl -L "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-gnu.tar.gz" \
        -o "$uv_dir/uv-x86_64.tar.gz"

    # Download uv for aarch64
    echo "Downloading uv for aarch64..."
    curl -L "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-aarch64-unknown-linux-gnu.tar.gz" \
        -o "$uv_dir/uv-aarch64.tar.gz"

    # Extract binaries
    cd "$uv_dir"
    tar -xzf uv-x86_64.tar.gz
    tar -xzf uv-aarch64.tar.gz

    # Rename for consistency
    mv uv-x86_64-unknown-linux-gnu/uv uv.amd64
    mv uv-aarch64-unknown-linux-gnu/uv uv.arm64

    # Clean up
    rm -rf uv-*.tar.gz uv-*-unknown-linux-gnu/

    echo "UV binaries downloaded to $uv_dir"
    cd "$ROOT_DIR"
}

# Function to setup launcher in Anki workspace
setup_launcher_in_anki_workspace() {
    local anki_dir="$ROOT_DIR/anki"
    local anki_launcher_dir="$anki_dir/qt/launcher"

    if [[ ! -d "$anki_dir" ]]; then
        echo "Error: Anki source not found at $anki_dir. Please run get_anki.sh first."
        exit 1
    fi

    echo "Setting up AnkiBlur launcher in Anki workspace..."

    # Backup original Anki launcher if it exists
    if [[ -d "$anki_launcher_dir" ]]; then
        mv "$anki_launcher_dir" "$anki_launcher_dir.backup"
    fi

    # Copy our AnkiBlur launcher to Anki workspace
    cp -r "$LAUNCHER_DIR" "$anki_launcher_dir"

    # Copy the .python-version file from Anki root to launcher directory
    if [[ -f "$anki_dir/.python-version" ]]; then
        cp "$anki_dir/.python-version" "$anki_launcher_dir/"
        echo "Copied .python-version from Anki: $(cat "$anki_dir/.python-version")"
    else
        echo "Warning: .python-version not found in Anki repo"
    fi

    # Update LAUNCHER_DIR to point to workspace location
    LAUNCHER_DIR="$anki_launcher_dir"

    # Update TARGET_DIR to point to Anki workspace target
    TARGET_DIR="${CARGO_TARGET_DIR:-$anki_dir/target}"
}

# Function to build launcher for specific target
build_launcher_target() {
    local target="$1"
    local arch_suffix="$2"

    echo "Building launcher for $target..."

    # Ensure target is installed
    rustup target add "$target"

    cd "$LAUNCHER_DIR"

    case "$target" in
        "x86_64-unknown-linux-gnu")
            # Use musl for static linking
            rustup target add x86_64-unknown-linux-musl
            cargo build --release --target x86_64-unknown-linux-musl
            # Copy the musl binary with the original target name for compatibility
            mkdir -p "$TARGET_DIR/$target/release"
            cp "$TARGET_DIR/x86_64-unknown-linux-musl/release/launcher" "$TARGET_DIR/$target/release/launcher"
            ;;
        "aarch64-unknown-linux-gnu")
            # Use musl for static linking with proper cross-compilation setup
            rustup target add aarch64-unknown-linux-musl

            # Set environment for static musl linking
            export CC_aarch64_unknown_linux_musl=aarch64-linux-gnu-gcc
            export CXX_aarch64_unknown_linux_musl=aarch64-linux-gnu-g++
            export AR_aarch64_unknown_linux_musl=aarch64-linux-gnu-ar
            export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER=aarch64-linux-gnu-gcc
            export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_RUSTFLAGS="-C target-feature=+crt-static"

            echo "Building static ARM64 binary with musl..."
            if cargo build --release --target aarch64-unknown-linux-musl; then
                echo "ARM64 musl build successful"
                mkdir -p "$TARGET_DIR/$target/release"
                cp "$TARGET_DIR/aarch64-unknown-linux-musl/release/launcher" "$TARGET_DIR/$target/release/launcher"
            else
                echo "ARM64 musl build failed, falling back to glibc build"
                cargo build --release --target "$target"
            fi
            ;;
        *)
            echo "Error: Unsupported target $target"
            exit 1
            ;;
    esac

    # Copy built binary to output directory
    mkdir -p "$OUTPUT_DIR"
    cp "$TARGET_DIR/$target/release/launcher" "$OUTPUT_DIR/launcher.$arch_suffix"

    echo "Launcher built for $target -> launcher.$arch_suffix"
    cd "$ROOT_DIR"
}

# Function to create universal package structure
create_universal_package() {
    echo "Creating universal package structure..."

    local package_dir="$OUTPUT_DIR/ankiblur-launcher-$BLUR_VERSION-linux"

    # Clean and create package directory
    rm -rf "$package_dir"
    mkdir -p "$package_dir"

    # Copy launcher binaries
    cp "$OUTPUT_DIR/launcher.amd64" "$package_dir/"
    cp "$OUTPUT_DIR/launcher.arm64" "$package_dir/"

    # Copy uv binaries
    cp "$OUTPUT_DIR/uv-binaries/uv.amd64" "$package_dir/"
    cp "$OUTPUT_DIR/uv-binaries/uv.arm64" "$package_dir/"

    # Copy Linux platform files
    cp "$LAUNCHER_DIR/lin/ankiblur" "$package_dir/"
    cp "$LAUNCHER_DIR/lin/ankiblur.desktop" "$package_dir/"
    cp "$LAUNCHER_DIR/lin"/*.png "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin"/*.xpm "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin"/*.xml "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin"/*.1 "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin/install.sh" "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin/uninstall.sh" "$package_dir/" 2>/dev/null || true
    cp "$LAUNCHER_DIR/lin/README.md" "$package_dir/" 2>/dev/null || true

    # Copy configuration files
    cp "$LAUNCHER_DIR/versions.py" "$package_dir/"

    # Create AnkiBlur-specific pyproject.toml (will be created in next step)
    echo "# AnkiBlur package definition - will be populated by package creation script" > "$package_dir/pyproject.toml"

    # Copy .python-version from launcher directory (copied from Anki repo)
    if [[ -f "$LAUNCHER_DIR/.python-version" ]]; then
        cp "$LAUNCHER_DIR/.python-version" "$package_dir/"
        echo "Copied .python-version: $(cat "$LAUNCHER_DIR/.python-version")"
    else
        echo "Warning: .python-version not found, creating default"
        echo "3.13.5" > "$package_dir/.python-version"
    fi

    # Set executable permissions
    chmod +x \
        "$package_dir/ankiblur" \
        "$package_dir/launcher.amd64" \
        "$package_dir/launcher.arm64" \
        "$package_dir/uv.amd64" \
        "$package_dir/uv.arm64" \
        "$package_dir/install.sh" \
        "$package_dir/uninstall.sh" 2>/dev/null || true

    echo "Universal package created at: $package_dir"
}

# Function to create distribution archive
create_distribution_archive() {
    echo "Creating distribution archive..."

    local package_dir="ankiblur-launcher-$BLUR_VERSION-linux"

    cd "$OUTPUT_DIR"

    # Create compressed archive
    if command -v zstd >/dev/null 2>&1; then
        echo "Creating zstd compressed archive..."
        tar -I "zstd -c --long -T0 -18" -cf "$package_dir.tar.zst" "$package_dir"
        echo "Created: $OUTPUT_DIR/$package_dir.tar.zst"
    else
        echo "Creating gzip compressed archive..."
        tar -czf "$package_dir.tar.gz" "$package_dir"
        echo "Created: $OUTPUT_DIR/$package_dir.tar.gz"
    fi

    cd "$ROOT_DIR"
}

# Function to verify build
verify_build() {
    echo "Verifying build..."

    local package_dir="$OUTPUT_DIR/ankiblur-launcher-$BLUR_VERSION-linux"

    # Check that all required files exist
    local required_files=(
        "launcher.amd64"
        "launcher.arm64"
        "uv.amd64"
        "uv.arm64"
        "ankiblur"
        "pyproject.toml"
        ".python-version"
        "versions.py"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$package_dir/$file" ]]; then
            echo "Error: Missing required file: $file"
            exit 1
        fi
    done

    # Check that binaries are executable
    local executables=(
        "launcher.amd64"
        "launcher.arm64"
        "uv.amd64"
        "uv.arm64"
        "ankiblur"
    )

    for exe in "${executables[@]}"; do
        if [[ ! -x "$package_dir/$exe" ]]; then
            echo "Error: File not executable: $exe"
            exit 1
        fi
    done

    # Check architecture of binaries
    echo "Verifying binary architectures..."

    if command -v file >/dev/null 2>&1; then
        file "$package_dir/launcher.amd64" | grep -q "x86-64" || {
            echo "Warning: launcher.amd64 may not be x86_64"
        }

        file "$package_dir/launcher.arm64" | grep -q "aarch64" || {
            echo "Warning: launcher.arm64 may not be aarch64"
        }
    fi

    echo "Build verification complete"
}

# Main function
main() {
    echo "Building AnkiBlur Rust launcher..."

    # Ensure we're in the right directory
    if [[ ! -f "$LAUNCHER_DIR/Cargo.toml" ]]; then
        echo "Error: Launcher Cargo.toml not found at $LAUNCHER_DIR"
        echo "Make sure the launcher code has been copied from Anki"
        exit 1
    fi

    # Setup build environment
    setup_rust
    setup_cross_compilation

    # Setup launcher in Anki workspace
    setup_launcher_in_anki_workspace

    # Re-install targets for workspace toolchain (Anki may have its own rust-toolchain.toml)
    echo "Installing targets for workspace toolchain..."
    cd "$LAUNCHER_DIR"
    rustup target add x86_64-unknown-linux-gnu
    rustup target add aarch64-unknown-linux-gnu
    rustup target add x86_64-unknown-linux-musl
    rustup target add aarch64-unknown-linux-musl
    cd "$ROOT_DIR"

    # Download dependencies
    download_uv_binaries

    # Build for all target architectures
    build_launcher_target "x86_64-unknown-linux-gnu" "amd64"
    build_launcher_target "aarch64-unknown-linux-gnu" "arm64"

    # Create universal package
    create_universal_package

    # Create distribution archive
    create_distribution_archive

    # Verify build
    verify_build

    echo "AnkiBlur launcher build complete!"
    echo "Universal package: $OUTPUT_DIR/ankiblur-launcher-$BLUR_VERSION-linux"
}

main "$@"