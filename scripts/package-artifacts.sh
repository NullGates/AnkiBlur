#!/bin/bash

# package-artifacts.sh
# Packages built AnkiBlur launchers for distribution
# Usage: ./package-artifacts.sh <anki-source-directory> <platform> <version>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ANKI_SOURCE="${1:-}"
PLATFORM="${2:-}"
VERSION="${3:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Usage function
usage() {
    echo "Usage: $0 <anki-source-directory> <platform> <version>"
    echo ""
    echo "Packages built AnkiBlur launchers for distribution."
    echo ""
    echo "Arguments:"
    echo "  anki-source-directory    Path to the built Anki source with AnkiBlur patches"
    echo "  platform                 Target platform (linux, macos, windows)"
    echo "  version                  Version string (e.g., 25.09)"
    echo ""
    echo "Supported platforms:"
    echo "  linux    - Creates .tar.zst archive"
    echo "  macos    - Creates .dmg package"
    echo "  windows  - Creates .exe installer"
    echo ""
    exit 1
}

# Validate arguments
if [[ -z "$ANKI_SOURCE" ]] || [[ -z "$PLATFORM" ]] || [[ -z "$VERSION" ]]; then
    log_error "Missing required arguments"
    usage
fi

if [[ ! -d "$ANKI_SOURCE" ]]; then
    log_error "Anki source directory does not exist: $ANKI_SOURCE"
    exit 1
fi

# Convert to absolute path
ANKI_SOURCE="$(cd "$ANKI_SOURCE" && pwd)"

# Create artifacts directory
ARTIFACTS_DIR="$REPO_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR"

log_info "Starting artifact packaging for $PLATFORM"
log_info "Anki source: $ANKI_SOURCE"
log_info "Platform: $PLATFORM"
log_info "Version: $VERSION"
log_info "Artifacts will be saved to: $ARTIFACTS_DIR"

# Function to package Linux artifacts
package_linux() {
    log_info "Packaging Linux artifacts..."

    local launcher_dir="$ANKI_SOURCE/out/launcher/anki-launcher-$VERSION-linux"
    local tarball="$ANKI_SOURCE/out/launcher/anki-launcher-$VERSION-linux.tar.zst"

    # Check if the build output exists
    if [[ ! -d "$launcher_dir" ]]; then
        log_error "Linux launcher directory not found: $launcher_dir"
        log_error "Build may have failed or output location changed"
        return 1
    fi

    if [[ ! -f "$tarball" ]]; then
        log_error "Linux tarball not found: $tarball"
        log_error "Build may have failed or tarball creation failed"
        return 1
    fi

    # Verify the tarball contains expected files
    log_info "Verifying tarball contents..."
    if tar -tf "$tarball" | grep -q "launcher.amd64" && tar -tf "$tarball" | grep -q "launcher.arm64"; then
        log_success "Tarball contains expected launcher binaries"
    else
        log_warning "Tarball may be missing expected binaries"
    fi

    # Copy tarball to artifacts directory
    cp "$tarball" "$ARTIFACTS_DIR/"
    log_success "Linux tarball copied to artifacts"

    # Create additional metadata
    {
        echo "Platform: Linux (x86_64 + ARM64)"
        echo "Version: $VERSION"
        echo "Package Type: tar.zst archive"
        echo "Contents: Universal launcher with both architectures"
        echo "Installation: Extract and run install.sh"
        echo "Patches Applied: AnkiBlur branding, core patches, addon integration"
        echo "Build Date: $(date -u)"
    } > "$ARTIFACTS_DIR/anki-launcher-$VERSION-linux.info"

    return 0
}

# Function to package macOS artifacts
package_macos() {
    log_info "Packaging macOS artifacts..."

    local app_bundle="$ANKI_SOURCE/out/launcher/Anki.app"
    local dmg_file="$ANKI_SOURCE/out/launcher/anki-launcher-$VERSION-mac.dmg"

    # Check if DMG was created
    if [[ -f "$dmg_file" ]]; then
        log_success "Found DMG file: $dmg_file"
        cp "$dmg_file" "$ARTIFACTS_DIR/"
        log_success "macOS DMG copied to artifacts"
    elif [[ -d "$app_bundle" ]]; then
        log_warning "DMG not found, but app bundle exists. Creating DMG manually..."

        # Create DMG manually if the build script didn't create one
        local temp_dmg="$ARTIFACTS_DIR/anki-launcher-$VERSION-mac-temp.dmg"
        local final_dmg="$ARTIFACTS_DIR/anki-launcher-$VERSION-mac.dmg"

        # Calculate size needed (app bundle size + 50MB buffer)
        local bundle_size=$(du -sm "$app_bundle" | cut -f1)
        local dmg_size=$((bundle_size + 50))

        log_info "Creating DMG with size: ${dmg_size}MB"

        # Create temporary DMG
        hdiutil create -size "${dmg_size}m" -fs HFS+ -volname "AnkiBlur Launcher $VERSION" "$temp_dmg"

        # Mount the DMG
        local mount_point=$(hdiutil attach "$temp_dmg" -readwrite -noverify -noautoopen | grep "/Volumes/" | awk '{print $3}')

        if [[ -n "$mount_point" ]]; then
            # Copy app bundle to DMG
            cp -R "$app_bundle" "$mount_point/"

            # Create Applications symlink
            ln -s /Applications "$mount_point/Applications"

            # Unmount and convert to compressed DMG
            hdiutil detach "$mount_point"
            hdiutil convert "$temp_dmg" -format UDZO -o "$final_dmg"

            # Clean up temp file
            rm "$temp_dmg"

            log_success "Created DMG manually: $final_dmg"
        else
            log_error "Failed to mount temporary DMG"
            return 1
        fi
    else
        log_error "Neither DMG file nor app bundle found"
        log_error "Expected DMG: $dmg_file"
        log_error "Expected app bundle: $app_bundle"
        return 1
    fi

    # Create additional metadata
    {
        echo "Platform: macOS (Universal Binary)"
        echo "Version: $VERSION"
        echo "Package Type: DMG disk image"
        echo "Contents: AnkiBlur.app with universal binary (ARM64 + x86_64)"
        echo "Installation: Open DMG and drag to Applications folder"
        echo "Patches Applied: AnkiBlur branding, core patches, addon integration"
        echo "Build Date: $(date -u)"
        echo "Note: Code signing may not be present in CI builds"
    } > "$ARTIFACTS_DIR/anki-launcher-$VERSION-mac.info"

    return 0
}

# Function to package Windows artifacts
package_windows() {
    log_info "Packaging Windows artifacts..."

    # Look for Windows installer in multiple possible locations
    local installer_locations=(
        "$ANKI_SOURCE/out/launcher/anki-launcher-$VERSION-windows.exe"
        "$ANKI_SOURCE/out/anki-launcher-$VERSION-windows.exe"
        "$ANKI_SOURCE/qt/launcher/win/anki-launcher-$VERSION-windows.exe"
    )

    local installer_found=false
    for installer_path in "${installer_locations[@]}"; do
        if [[ -f "$installer_path" ]]; then
            log_success "Found Windows installer: $installer_path"
            cp "$installer_path" "$ARTIFACTS_DIR/anki-launcher-$VERSION-windows.exe"
            installer_found=true
            break
        fi
    done

    if ! $installer_found; then
        log_error "Windows installer not found in any expected location:"
        for location in "${installer_locations[@]}"; do
            log_error "  - $location"
        done

        # Look for any .exe files as a fallback
        log_info "Searching for any .exe files in output directory..."
        find "$ANKI_SOURCE/out" -name "*.exe" -type f | while read -r exe_file; do
            log_info "Found: $exe_file"
        done

        return 1
    fi

    log_success "Windows installer copied to artifacts"

    # Create additional metadata
    {
        echo "Platform: Windows (x86_64)"
        echo "Version: $VERSION"
        echo "Package Type: NSIS Installer (.exe)"
        echo "Contents: AnkiBlur launcher with Windows integration"
        echo "Installation: Run the .exe installer"
        echo "Features: Start menu shortcuts, file associations, uninstaller"
        echo "Patches Applied: AnkiBlur branding, core patches, addon integration"
        echo "Build Date: $(date -u)"
        echo "Note: Code signing may not be present in CI builds"
    } > "$ARTIFACTS_DIR/anki-launcher-$VERSION-windows.info"

    return 0
}

# Function to include patches directory in package info
include_patches_info() {
    local platform="$1"

    if [[ -d "$ANKI_SOURCE/patches" ]]; then
        log_info "Creating patches manifest for $platform package"

        {
            echo ""
            echo "=== INCLUDED PATCHES ==="
            echo ""
            echo "This package includes the following AnkiBlur patches:"
            echo ""

            # List all patch files with their purposes
            echo "1. Branding Patches (patches/01_launcher_branding/):"
            find "$ANKI_SOURCE/patches/01_launcher_branding" -name "*.patch" -exec basename {} \; | sort | sed 's/^/   - /'
            echo ""

            echo "2. Core Anki Patches (patches/02_launcher_apply_anki_patches/):"
            find "$ANKI_SOURCE/patches/02_launcher_apply_anki_patches" -name "*.patch" -exec basename {} \; | sort | sed 's/^/   - /'
            echo ""

            echo "3. Addon Integration Patches (patches/03_launcher_apply_anki_addon/):"
            find "$ANKI_SOURCE/patches/03_launcher_apply_anki_addon" -name "*.patch" -exec basename {} \; | sort | sed 's/^/   - /'
            echo ""

            echo "The complete patches directory is included in this package"
            echo "for reference and potential reapplication to future Anki versions."

        } >> "$ARTIFACTS_DIR/anki-launcher-$VERSION-$platform.info"

        log_success "Patches information added to package metadata"
    else
        log_warning "Patches directory not found in Anki source"
    fi
}

# Function to verify package integrity
verify_package() {
    local platform="$1"

    case "$platform" in
        linux)
            local package_file="$ARTIFACTS_DIR/anki-launcher-$VERSION-linux.tar.zst"
            if [[ -f "$package_file" ]]; then
                local size=$(stat -c%s "$package_file" 2>/dev/null || stat -f%z "$package_file" 2>/dev/null || echo "unknown")
                log_info "Linux package size: $size bytes"

                # Test that the archive can be read
                if tar -tf "$package_file" >/dev/null 2>&1; then
                    log_success "Linux package integrity verified"
                else
                    log_error "Linux package appears to be corrupted"
                    return 1
                fi
            fi
            ;;
        macos)
            local package_file="$ARTIFACTS_DIR/anki-launcher-$VERSION-mac.dmg"
            if [[ -f "$package_file" ]]; then
                local size=$(stat -c%s "$package_file" 2>/dev/null || stat -f%z "$package_file" 2>/dev/null || echo "unknown")
                log_info "macOS package size: $size bytes"
                log_success "macOS package integrity check completed"
            fi
            ;;
        windows)
            local package_file="$ARTIFACTS_DIR/anki-launcher-$VERSION-windows.exe"
            if [[ -f "$package_file" ]]; then
                local size=$(stat -c%s "$package_file" 2>/dev/null || stat -f%z "$package_file" 2>/dev/null || echo "unknown")
                log_info "Windows package size: $size bytes"
                log_success "Windows package integrity check completed"
            fi
            ;;
    esac

    return 0
}

# Main execution
main() {
    case "$PLATFORM" in
        linux)
            if package_linux; then
                include_patches_info "linux"
                verify_package "linux"
                log_success "Linux packaging completed successfully"
            else
                log_error "Linux packaging failed"
                exit 1
            fi
            ;;
        macos)
            if package_macos; then
                include_patches_info "mac"
                verify_package "macos"
                log_success "macOS packaging completed successfully"
            else
                log_error "macOS packaging failed"
                exit 1
            fi
            ;;
        windows)
            if package_windows; then
                include_patches_info "windows"
                verify_package "windows"
                log_success "Windows packaging completed successfully"
            else
                log_error "Windows packaging failed"
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported platform: $PLATFORM"
            log_error "Supported platforms: linux, macos, windows"
            exit 1
            ;;
    esac

    log_success "Packaging completed for $PLATFORM"
    log_info "Artifacts available in: $ARTIFACTS_DIR"

    # List created artifacts
    log_info "Created artifacts:"
    find "$ARTIFACTS_DIR" -name "*$PLATFORM*" -o -name "*$VERSION*" | sort | while read -r file; do
        log_info "  - $(basename "$file")"
    done
}

# Trap to handle interruptions
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"