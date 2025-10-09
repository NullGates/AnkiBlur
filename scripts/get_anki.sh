#!/bin/bash
set -euo pipefail

# Download and extract Anki source code

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ANKI_REPO="ankitects/anki"
ANKI_DIR="$ROOT_DIR/anki"

# Clean up any existing Anki directory
if [[ -d "$ANKI_DIR" ]]; then
    echo "Removing existing Anki directory..."
    rm -rf "$ANKI_DIR"
fi

# Function to clone Anki source
download_anki() {
    local version="${ANKI_VERSION:-}"
    local commit="${ANKI_COMMIT:-}"

    if [[ -z "$version" ]]; then
        echo "Error: ANKI_VERSION environment variable not set"
        exit 1
    fi

    echo "Cloning Anki repository for $version..."

    # Clone the repository
    echo "Cloning from: https://github.com/$ANKI_REPO.git"
    git clone --recursive "https://github.com/$ANKI_REPO.git" "$ANKI_DIR"

    cd "$ANKI_DIR"

    # Checkout the specific version/tag
    echo "Checking out $version..."
    git checkout "$version"

    # Update submodules to match the tag
    echo "Updating submodules..."
    git submodule update --init --recursive

    # Verify we're on the right commit if provided
    if [[ -n "$commit" ]]; then
        local current_commit=$(git rev-parse HEAD)
        if [[ "$current_commit" != "$commit" ]]; then
            echo "Warning: Expected commit $commit, but got $current_commit"
        else
            echo "Verified commit matches: $commit"
        fi
    fi

    cd "$ROOT_DIR"
    echo "Anki repository cloned to: $ANKI_DIR"
}

# Function to verify Anki source
verify_anki() {
    if [[ ! -d "$ANKI_DIR" ]]; then
        echo "Error: Anki directory not found at $ANKI_DIR"
        exit 1
    fi

    # Check for key files that should exist in Anki source
    local required_files=(
        "pyproject.toml"
        "qt/aqt/__init__.py"
        "build/configure"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$ANKI_DIR/$file" ]]; then
            echo "Warning: Expected file not found: $file"
        fi
    done

    echo "Anki source verification complete"
}

# Function to apply any pre-patches (if needed)
apply_prepatches() {
    local prepatch_dir="$ROOT_DIR/patches/pre"

    if [[ ! -d "$prepatch_dir" ]]; then
        echo "No pre-patches directory found, skipping pre-patches"
        return
    fi

    echo "Applying pre-patches..."
    cd "$ANKI_DIR"

    # Apply any pre-patches in alphabetical order
    find "$prepatch_dir" -name "*.patch" -type f | sort | while read -r patch_file; do
        echo "Applying pre-patch: $(basename "$patch_file")"
        patch -p1 < "$patch_file" || {
            echo "Error applying pre-patch: $patch_file"
            exit 1
        }
    done

    cd "$ROOT_DIR"
    echo "Pre-patches applied successfully"
}

# Main function
main() {
    echo "Getting Anki source code..."

    download_anki
    verify_anki
    apply_prepatches

    echo "Anki source preparation complete"
}

main "$@"