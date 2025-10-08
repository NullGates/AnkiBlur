#!/bin/bash
set -euo pipefail

# Create GitHub release for AnkiBlur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
REPO="${GITHUB_REPOSITORY:-}"
TOKEN="${GITHUB_TOKEN:-}"
BLUR_VERSION="${BLUR_VERSION:-}"
ANKI_VERSION="${ANKI_VERSION:-}"
RELEASE_DIR="$ROOT_DIR/release-assets"

# Function to generate release notes
generate_release_notes() {
    local blur_version="$1"
    local anki_version="$2"

    cat << EOF
# AnkiBlur $blur_version

This release is based on Anki $anki_version with additional transparency and blur effects.

## Features
- 🎨 **Transparency Effects**: Semi-transparent main window and dialogs
- ✨ **Blur Effects**: Background blur for a modern look
- 📱 **Native Performance**: All the power of Anki with enhanced visuals
- 🔄 **Full Compatibility**: Works with existing Anki decks and add-ons

## Changes in this version
- Based on Anki $anki_version
- Applied AnkiBlur transparency patches
- Updated branding and version information

## Downloads
Choose the appropriate package for your operating system:

### Linux
- **AppImage**: Portable application for most Linux distributions
- **tar.gz**: Extract and run manually
- **deb**: Debian/Ubuntu package

### Windows
- **exe**: Windows installer
- **zip**: Portable Windows application

### macOS
- **dmg**: macOS disk image
- **tar.gz**: Manual installation

## Installation
1. Download the appropriate package for your system
2. Install/extract as usual for your platform
3. Launch AnkiBlur just like regular Anki

## Support
For issues specific to AnkiBlur transparency features, please open an issue on our repository.
For general Anki functionality, refer to the official Anki documentation.

---
*Built automatically from Anki $anki_version*
EOF
}

# Function to create the release
create_release() {
    echo "Creating GitHub release for AnkiBlur $BLUR_VERSION..."

    if [[ -z "$REPO" || -z "$TOKEN" || -z "$BLUR_VERSION" ]]; then
        echo "Error: Missing required environment variables"
        echo "  GITHUB_REPOSITORY: $REPO"
        echo "  GITHUB_TOKEN: [set]"
        echo "  BLUR_VERSION: $BLUR_VERSION"
        exit 1
    fi

    # Generate release notes
    local release_notes=$(generate_release_notes "$BLUR_VERSION" "$ANKI_VERSION")

    # Create release using GitHub API
    local response=$(curl -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/releases" \
        -d "{
            \"tag_name\": \"$BLUR_VERSION\",
            \"target_commitish\": \"master\",
            \"name\": \"AnkiBlur $BLUR_VERSION\",
            \"body\": $(echo "$release_notes" | jq -Rs .),
            \"draft\": false,
            \"prerelease\": false
        }")

    # Extract upload URL from response
    local upload_url=$(echo "$response" | jq -r '.upload_url' | sed 's/{?name,label}//')

    if [[ "$upload_url" == "null" || -z "$upload_url" ]]; then
        echo "Error creating release:"
        echo "$response" | jq .
        exit 1
    fi

    echo "Release created successfully"
    echo "Upload URL: $upload_url"

    # Upload assets
    upload_assets "$upload_url"
}

# Function to upload release assets
upload_assets() {
    local upload_url="$1"

    if [[ ! -d "$RELEASE_DIR" ]]; then
        echo "No release assets found at $RELEASE_DIR"
        return
    fi

    echo "Uploading release assets..."

    find "$RELEASE_DIR" -type f \( -name "*.tar.gz" -o -name "*.zip" -o -name "*.deb" -o -name "*.AppImage" -o -name "*.dmg" -o -name "*.exe" \) | while read -r asset_path; do
        local asset_name=$(basename "$asset_path")
        local content_type=$(get_content_type "$asset_name")

        echo "Uploading: $asset_name"

        local upload_response=$(curl -s -X POST \
            -H "Authorization: token $TOKEN" \
            -H "Content-Type: $content_type" \
            --data-binary "@$asset_path" \
            "$upload_url?name=$asset_name")

        # Check if upload was successful
        local download_url=$(echo "$upload_response" | jq -r '.browser_download_url')
        if [[ "$download_url" != "null" && -n "$download_url" ]]; then
            echo "  ✓ Uploaded: $download_url"
        else
            echo "  ✗ Failed to upload $asset_name"
            echo "$upload_response" | jq .
        fi
    done
}

# Function to determine content type for assets
get_content_type() {
    local filename="$1"

    case "$filename" in
        *.tar.gz) echo "application/gzip" ;;
        *.zip) echo "application/zip" ;;
        *.deb) echo "application/vnd.debian.binary-package" ;;
        *.AppImage) echo "application/x-executable" ;;
        *.dmg) echo "application/x-apple-diskimage" ;;
        *.exe) echo "application/x-msdownload" ;;
        *.msi) echo "application/x-msi" ;;
        *) echo "application/octet-stream" ;;
    esac
}

# Function to check if release already exists
release_exists() {
    local version="$1"

    local response=$(curl -s \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/releases/tags/$version")

    local id=$(echo "$response" | jq -r '.id')
    [[ "$id" != "null" ]]
}

# Main function
main() {
    echo "Creating GitHub release..."

    # Check if required tools are available
    if ! command -v jq >/dev/null 2>&1; then
        echo "Error: jq is required but not installed"
        exit 1
    fi

    if ! command -v curl >/dev/null 2>&1; then
        echo "Error: curl is required but not installed"
        exit 1
    fi

    # Check if release already exists
    if release_exists "$BLUR_VERSION"; then
        echo "Release $BLUR_VERSION already exists, skipping creation"
        return
    fi

    # Create the release
    create_release

    echo "GitHub release creation complete"
}

main "$@"