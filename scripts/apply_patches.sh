#!/bin/bash
set -euo pipefail

# Apply all patches to the Anki source code

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ANKI_DIR="$ROOT_DIR/anki"
PATCHES_DIR="$ROOT_DIR/patches"

# Function to apply patches from a directory
apply_patch_directory() {
    local patch_dir="$1"
    local patch_name="$(basename "$patch_dir")"

    if [[ ! -d "$patch_dir" ]]; then
        echo "Patch directory not found: $patch_dir"
        return 1
    fi

    echo "Applying $patch_name patches..."

    # Change to Anki directory for applying patches
    cd "$ANKI_DIR"

    # Apply .patch files first (in alphabetical order)
    if find "$patch_dir" -name "*.patch" -type f | head -1 >/dev/null 2>&1; then
        find "$patch_dir" -name "*.patch" -type f | sort | while read -r patch_file; do
            echo "  Applying patch: $(basename "$patch_file")"
            if ! patch -p1 < "$patch_file"; then
                echo "Error: Failed to apply patch $patch_file"
                exit 1
            fi
        done
    fi

    # Apply shell scripts (for complex modifications)
    if find "$patch_dir" -name "*.sh" -type f | head -1 >/dev/null 2>&1; then
        find "$patch_dir" -name "*.sh" -type f | sort | while read -r script_file; do
            echo "  Running patch script: $(basename "$script_file")"
            if ! bash "$script_file"; then
                echo "Error: Failed to run patch script $script_file"
                exit 1
            fi
        done
    fi

    # Copy replacement files
    if find "$patch_dir" -name "replace_*" -type d | head -1 >/dev/null 2>&1; then
        find "$patch_dir" -name "replace_*" -type d | while read -r replace_dir; do
            local target_path="${replace_dir#*replace_}"
            target_path="${target_path//___//}"  # Convert ___ back to /

            echo "  Replacing files in: $target_path"
            if [[ -d "$target_path" ]]; then
                cp -r "$replace_dir"/* "$target_path"/
            else
                echo "    Warning: Target directory $target_path not found"
            fi
        done
    fi

    cd "$ROOT_DIR"
    echo "$patch_name patches applied successfully"
}

# Function to substitute variables in patches
substitute_variables() {
    local anki_version="${ANKI_VERSION:-unknown}"
    local blur_version="${BLUR_VERSION:-unknown}"

    echo "Substituting variables in Anki source..."
    cd "$ANKI_DIR"

    # Replace version strings in key files
    if [[ -f "qt/aqt/__init__.py" ]]; then
        # Update version in Anki's main init file
        sed -i.bak "s/appVersion = \".*\"/appVersion = \"$blur_version\"/" qt/aqt/__init__.py || true
        sed -i.bak "s/appName = \".*\"/appName = \"AnkiBlur\"/" qt/aqt/__init__.py || true
        rm -f qt/aqt/__init__.py.bak
    fi

    # Replace branding in about dialog and other UI files
    find . -name "*.py" -type f -exec grep -l "Anki" {} \; | while read -r file; do
        # Be careful to only replace specific instances
        sed -i.bak 's/\bAnki\b(?!\w)/AnkiBlur/g' "$file" 2>/dev/null || true
        rm -f "${file}.bak"
    done

    cd "$ROOT_DIR"
    echo "Variable substitution complete"
}

# Function to verify patches applied correctly
verify_patches() {
    echo "Verifying patches..."
    cd "$ANKI_DIR"

    # Check that key modifications are in place
    local errors=0

    # Check for AnkiBlur branding
    if grep -r "AnkiBlur" qt/aqt/ >/dev/null 2>&1; then
        echo "  ✓ AnkiBlur branding found"
    else
        echo "  ✗ AnkiBlur branding not found"
        errors=$((errors + 1))
    fi

    # Check that the source is still buildable (basic check)
    if [[ -f "pyproject.toml" && -f "build/configure" ]]; then
        echo "  ✓ Build files present"
    else
        echo "  ✗ Build files missing"
        errors=$((errors + 1))
    fi

    cd "$ROOT_DIR"

    if [[ $errors -eq 0 ]]; then
        echo "Patch verification passed"
    else
        echo "Patch verification failed with $errors errors"
        exit 1
    fi
}

# Main function
main() {
    echo "Applying patches to Anki source..."

    # Verify Anki source exists
    if [[ ! -d "$ANKI_DIR" ]]; then
        echo "Error: Anki source directory not found at $ANKI_DIR"
        echo "Run get_anki.sh first"
        exit 1
    fi

    # Check if patches should be skipped
    if [[ "${SKIP_PATCHES:-false}" == "true" ]]; then
        echo "SKIP_PATCHES=true, skipping all patches"
        echo "Building vanilla Anki without modifications"
        return 0
    fi

    # Define patch order (patches are applied in this order)
    local patch_order=(
        "branding"
        "transparency"
        "version"
    )

    # Apply patches in order
    for patch_type in "${patch_order[@]}"; do
        local patch_dir="$PATCHES_DIR/$patch_type"
        if [[ -d "$patch_dir" ]]; then
            apply_patch_directory "$patch_dir"
        else
            echo "Patch directory not found: $patch_dir (skipping)"
        fi
    done

    # Apply variable substitutions
    substitute_variables

    # Verify patches
    verify_patches

    echo "All patches applied successfully"
}

main "$@"