#!/bin/bash
set -euo pipefail

# Create AnkiBlur package definitions for the launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
OUTPUT_DIR="$ROOT_DIR/out/launcher"
PACKAGE_DIR="$OUTPUT_DIR/ankiblur-launcher-${BLUR_VERSION:-1.0.0}-linux"

# Version info
BLUR_VERSION="${BLUR_VERSION:-1.0.0}"
ANKI_VERSION="${ANKI_VERSION:-25.09.2}"

echo "Creating AnkiBlur package definitions for version $BLUR_VERSION"

# Function to create AnkiBlur pyproject.toml
create_ankiblur_pyproject() {
    echo "Creating AnkiBlur pyproject.toml..."

    local pyproject_path="$PACKAGE_DIR/pyproject.toml"

    cat > "$pyproject_path" << EOF
[project]
name = "ankiblur-release"
version = "$BLUR_VERSION"
description = "AnkiBlur - Anki with transparency and blur effects"
requires-python = ">=3.9"
dependencies = [
  # AnkiBlur launcher manages Anki installation dynamically
  # No need to pin specific Anki versions as dependencies
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# hatch throws an error if nothing is included
[tool.hatch.build.targets.wheel]
include = ["no-such-file"]

[tool.ankiblur]
# AnkiBlur-specific configuration
base_anki_version = "$ANKI_VERSION"
patches_applied = []
# Future: patches_applied = ["branding", "transparency", "version"]
transparency_enabled = false
blur_enabled = false
EOF

    echo "Created AnkiBlur pyproject.toml at: $pyproject_path"
}

# Function to create version tracking file
create_version_info() {
    echo "Creating version information..."

    local version_info_path="$PACKAGE_DIR/ankiblur-version.json"

    cat > "$version_info_path" << EOF
{
  "ankiblur_version": "$BLUR_VERSION",
  "base_anki_version": "$ANKI_VERSION",
  "anki_commit": "${ANKI_COMMIT:-unknown}",
  "build_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "patches_applied": [],
  "features": {
    "transparency": false,
    "blur_effects": false,
    "universal_binary": true
  },
  "architecture_support": ["x86_64", "aarch64"],
  "launcher_version": "1.0.0"
}
EOF

    echo "Created version info at: $version_info_path"
}

# Function to create installation script
create_install_script() {
    echo "Creating installation script..."

    local install_path="$PACKAGE_DIR/install.sh"

    cat > "$install_path" << 'EOF'
#!/bin/bash
set -e

# AnkiBlur installation script

INSTALL_DIR="${INSTALL_DIR:-/opt/ankiblur}"
DESKTOP_DIR="${HOME}/.local/share/applications"
BIN_DIR="${HOME}/.local/bin"

echo "Installing AnkiBlur..."

# Create directories
mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR" "$BIN_DIR"

# Copy all files
cp -r * "$INSTALL_DIR/"

# Create symlink in user's bin directory
ln -sf "$INSTALL_DIR/ankiblur" "$BIN_DIR/ankiblur"

# Install desktop file
cp "$INSTALL_DIR/ankiblur.desktop" "$DESKTOP_DIR/"

# Update desktop file path
sed -i "s|Exec=ankiblur|Exec=$INSTALL_DIR/ankiblur|g" "$DESKTOP_DIR/ankiblur.desktop"
sed -i "s|Icon=ankiblur|Icon=$INSTALL_DIR/anki.png|g" "$DESKTOP_DIR/ankiblur.desktop"

echo "AnkiBlur installed successfully!"
echo "Installation directory: $INSTALL_DIR"
echo "You can now run 'ankiblur' from the command line"
echo "Or find AnkiBlur in your applications menu"
EOF

    chmod +x "$install_path"
    echo "Created installation script at: $install_path"
}

# Function to create uninstall script
create_uninstall_script() {
    echo "Creating uninstall script..."

    local uninstall_path="$PACKAGE_DIR/uninstall.sh"

    cat > "$uninstall_path" << 'EOF'
#!/bin/bash
set -e

# AnkiBlur uninstall script

INSTALL_DIR="${INSTALL_DIR:-/opt/ankiblur}"
DESKTOP_FILE="${HOME}/.local/share/applications/ankiblur.desktop"
BIN_LINK="${HOME}/.local/bin/ankiblur"

echo "Uninstalling AnkiBlur..."

# Remove installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo "Removed installation directory: $INSTALL_DIR"
fi

# Remove desktop file
if [[ -f "$DESKTOP_FILE" ]]; then
    rm -f "$DESKTOP_FILE"
    echo "Removed desktop file"
fi

# Remove binary symlink
if [[ -L "$BIN_LINK" ]]; then
    rm -f "$BIN_LINK"
    echo "Removed command line shortcut"
fi

echo "AnkiBlur uninstalled successfully"
echo "Note: User data and profiles are preserved"
EOF

    chmod +x "$uninstall_path"
    echo "Created uninstall script at: $uninstall_path"
}

# Function to create README
create_readme() {
    echo "Creating README..."

    local readme_path="$PACKAGE_DIR/README.md"

    cat > "$readme_path" << EOF
# AnkiBlur $BLUR_VERSION

AnkiBlur is a modified version of Anki with transparency and blur effects for modern interfaces.

## What's Included

This is a **universal binary package** that works on both x86_64 and ARM64 Linux systems.

- **Universal launcher**: Automatically detects your system architecture
- **Self-contained**: No system dependencies required beyond base Linux
- **Anki compatibility**: Based on Anki $ANKI_VERSION

## Quick Start

### Option 1: Direct Launch
```bash
./ankiblur
```

### Option 2: System Installation
```bash
# Install to system (creates shortcuts and menu entries)
./install.sh

# Then run from anywhere
ankiblur
```

## Features

- ✅ **Universal binary** - works on x86_64 and ARM64
- ✅ **No dependencies** - everything bundled
- ✅ **Automatic updates** - built-in update mechanism
- ⏳ **Transparency effects** - coming in future versions
- ⏳ **Blur effects** - coming in future versions

## Current Status

This version is based on vanilla Anki $ANKI_VERSION. Transparency and blur effects will be added in future releases.

## How It Works

The AnkiBlur launcher:
1. Detects your system architecture (x86_64 or ARM64)
2. Downloads and manages Python environments automatically
3. Installs Anki and dependencies via the bundled package manager
4. Launches AnkiBlur with the same interface as regular Anki

## Uninstall

To remove AnkiBlur:
```bash
./uninstall.sh
```

## Troubleshooting

### Launcher Won't Start
- Ensure the package is extracted completely
- Check that the launcher binary has execute permissions: \`chmod +x ankiblur\`

### Architecture Issues
- The launcher will automatically select the correct binary for your system
- Supported: x86_64 (Intel/AMD), aarch64 (ARM64)

### Updates
- The launcher includes an update mechanism
- Check for updates through the launcher interface

## Version Information

- **AnkiBlur Version**: $BLUR_VERSION
- **Based on Anki**: $ANKI_VERSION
- **Build Date**: $(date -u +"%Y-%m-%d")
- **Architecture Support**: Universal (x86_64 + ARM64)

## Support

- For AnkiBlur-specific issues: [GitHub Issues](https://github.com/your-username/ankiblur/issues)
- For general Anki questions: [Anki Manual](https://docs.ankiweb.net/)

---
*AnkiBlur is not affiliated with AnkiWeb or Damien Elmes*
EOF

    echo "Created README at: $readme_path"
}

# Function to verify package structure
verify_package() {
    echo "Verifying package structure..."

    if [[ ! -d "$PACKAGE_DIR" ]]; then
        echo "Error: Package directory not found: $PACKAGE_DIR"
        exit 1
    fi

    # Check required files
    local required_files=(
        "ankiblur"
        "launcher.amd64"
        "launcher.arm64"
        "uv.amd64"
        "uv.arm64"
        "pyproject.toml"
        ".python-version"
        "versions.py"
        "ankiblur-version.json"
        "install.sh"
        "uninstall.sh"
        "README.md"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$PACKAGE_DIR/$file" ]]; then
            echo "Warning: Missing file: $file"
        fi
    done

    echo "Package verification complete"
}

# Main function
main() {
    echo "Creating AnkiBlur package definitions..."

    # Verify the launcher package was built
    if [[ ! -d "$PACKAGE_DIR" ]]; then
        echo "Error: Launcher package not found at $PACKAGE_DIR"
        echo "Run build_launcher.sh first"
        exit 1
    fi

    # Create package definition files
    create_ankiblur_pyproject
    create_version_info
    create_install_script
    create_uninstall_script
    create_readme

    # Verify final package
    verify_package

    echo "AnkiBlur package definitions created successfully!"
    echo "Package ready at: $PACKAGE_DIR"
}

main "$@"