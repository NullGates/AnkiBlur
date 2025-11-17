#!/bin/bash

# validate-and-apply-patches.sh
# Validates and applies AnkiBlur patches to Anki source code
# Usage: ./validate-and-apply-patches.sh <anki-source-directory>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ANKI_SOURCE="${1:-}"

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
    echo "Usage: $0 <anki-source-directory>"
    echo ""
    echo "This script validates and applies AnkiBlur patches to the Anki source code."
    echo ""
    echo "Arguments:"
    echo "  anki-source-directory    Path to the extracted Anki source code"
    echo ""
    echo "Patch Application Order:"
    echo "  1. launcher_branding     - Changes Anki branding to AnkiBlur"
    echo "  2. launcher_anki_patches - Core Anki functionality patches"
    echo "  3. launcher_anki_addon   - AnkiBlur addon integration patches"
    echo ""
    exit 1
}

# Validate arguments
if [[ -z "$ANKI_SOURCE" ]]; then
    log_error "Anki source directory not specified"
    usage
fi

if [[ ! -d "$ANKI_SOURCE" ]]; then
    log_error "Anki source directory does not exist: $ANKI_SOURCE"
    exit 1
fi

# Convert to absolute path
ANKI_SOURCE="$(cd "$ANKI_SOURCE" && pwd)"

log_info "Starting patch validation and application process"
log_info "Anki source directory: $ANKI_SOURCE"
log_info "AnkiBlur repository: $REPO_ROOT"

# Define patch directories in application order
PATCH_DIRS=(
    "launcher_branding"
    "launcher_apply_anki_patches"
    "launcher_apply_anki_addon"
)

# Function to validate patch can be applied
validate_patch() {
    local patch_file="$1"
    local patch_name="$(basename "$patch_file")"

    log_info "Validating patch: $patch_name"

    # Check if patch file exists and is readable
    if [[ ! -r "$patch_file" ]]; then
        log_error "Patch file is not readable: $patch_file"
        return 1
    fi

    # Test patch application with dry-run
    if patch --dry-run -p1 -d "$ANKI_SOURCE" < "$patch_file" >/dev/null 2>&1; then
        log_success "Patch validation passed: $patch_name"
        return 0
    else
        log_error "Patch validation failed: $patch_name"

        # Show detailed error for debugging
        log_info "Detailed patch validation output:"
        patch --dry-run -p1 -d "$ANKI_SOURCE" < "$patch_file" || true

        return 1
    fi
}

# Function to apply a single patch
apply_patch() {
    local patch_file="$1"
    local patch_name="$(basename "$patch_file")"

    log_info "Applying patch: $patch_name"

    if patch -p1 -d "$ANKI_SOURCE" < "$patch_file"; then
        log_success "Patch applied successfully: $patch_name"
        return 0
    else
        log_error "Failed to apply patch: $patch_name"
        return 1
    fi
}

# Function to check if patch file contains wildcard placeholders
is_placeholder_patch() {
    local patch_file="$1"

    if grep -q "LAUNCHER_.*_WILDCARD" "$patch_file" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Function to process all patches in a directory
process_patch_directory() {
    local patch_dir_name="$1"
    local patch_dir="$REPO_ROOT/patches/$patch_dir_name"

    log_info "Processing patch directory: $patch_dir_name"

    # Check if patch directory exists
    if [[ ! -d "$patch_dir" ]]; then
        log_error "Patch directory does not exist: $patch_dir"
        return 1
    fi

    # Find all patch files in the directory
    local patch_files=()
    while IFS= read -r -d '' file; do
        patch_files+=("$file")
    done < <(find "$patch_dir" -name "*.patch" -type f -print0 | sort -z)

    if [[ ${#patch_files[@]} -eq 0 ]]; then
        log_warning "No patch files found in: $patch_dir"
        return 0
    fi

    log_info "Found ${#patch_files[@]} patch file(s) in $patch_dir_name"

    # Validate all patches first
    local failed_validations=0
    for patch_file in "${patch_files[@]}"; do
        if is_placeholder_patch "$patch_file"; then
            log_warning "Skipping placeholder patch: $(basename "$patch_file")"
            continue
        fi

        if ! validate_patch "$patch_file"; then
            ((failed_validations++))
        fi
    done

    if [[ $failed_validations -gt 0 ]]; then
        log_error "$failed_validations patch(es) failed validation in $patch_dir_name"
        return 1
    fi

    # Apply all patches
    local failed_applications=0
    for patch_file in "${patch_files[@]}"; do
        if is_placeholder_patch "$patch_file"; then
            log_warning "Skipping placeholder patch: $(basename "$patch_file")"
            continue
        fi

        if ! apply_patch "$patch_file"; then
            ((failed_applications++))
        fi
    done

    if [[ $failed_applications -gt 0 ]]; then
        log_error "$failed_applications patch(es) failed to apply in $patch_dir_name"
        return 1
    fi

    log_success "All patches applied successfully from: $patch_dir_name"
    return 0
}

# Function to create backup of original source
create_backup() {
    local backup_dir="$ANKI_SOURCE.backup.$(date +%Y%m%d_%H%M%S)"

    log_info "Creating backup of original source: $backup_dir"

    if cp -r "$ANKI_SOURCE" "$backup_dir"; then
        log_success "Backup created: $backup_dir"
        echo "$backup_dir" > "$ANKI_SOURCE.backup_location"
    else
        log_error "Failed to create backup"
        return 1
    fi
}

# Function to restore from backup
restore_from_backup() {
    local backup_location_file="$ANKI_SOURCE.backup_location"

    if [[ -f "$backup_location_file" ]]; then
        local backup_dir="$(cat "$backup_location_file")"

        if [[ -d "$backup_dir" ]]; then
            log_info "Restoring from backup: $backup_dir"

            rm -rf "$ANKI_SOURCE"
            cp -r "$backup_dir" "$ANKI_SOURCE"

            log_success "Restored from backup"
            return 0
        fi
    fi

    log_error "No backup found or backup is invalid"
    return 1
}

# Main execution
main() {
    local overall_success=true

    # Verify we're in the right directory structure
    if [[ ! -d "$REPO_ROOT/patches" ]]; then
        log_error "Patches directory not found in repository root: $REPO_ROOT/patches"
        exit 1
    fi

    # Check that Anki source looks valid
    if [[ ! -f "$ANKI_SOURCE/Cargo.toml" ]] || [[ ! -d "$ANKI_SOURCE/qt/launcher" ]]; then
        log_error "Directory doesn't appear to be Anki source code: $ANKI_SOURCE"
        log_error "Expected to find Cargo.toml and qt/launcher directory"
        exit 1
    fi

    # Create backup before starting
    if ! create_backup; then
        log_error "Failed to create backup, aborting"
        exit 1
    fi

    # Process each patch directory in order
    for patch_dir in "${PATCH_DIRS[@]}"; do
        log_info "Starting patch application for: $patch_dir"

        if ! process_patch_directory "$patch_dir"; then
            log_error "Failed to process patch directory: $patch_dir"
            overall_success=false

            log_info "Attempting to restore from backup..."
            if restore_from_backup; then
                log_error "Patch application failed, source restored to original state"
            else
                log_error "Patch application failed AND backup restore failed!"
            fi

            exit 1
        fi

        log_success "Completed patch application for: $patch_dir"
    done

    if $overall_success; then
        log_success "All patches applied successfully!"
        log_info "AnkiBlur patches have been applied to: $ANKI_SOURCE"

        # Copy patches directory to the Anki source for inclusion in final package
        log_info "Copying patches directory to Anki source for package inclusion"
        cp -r "$REPO_ROOT/patches" "$ANKI_SOURCE/"
        log_success "Patches directory copied to Anki source"

        # Clean up backup location file
        rm -f "$ANKI_SOURCE.backup_location"

        log_success "Patch application process completed successfully!"
    else
        log_error "Some patches failed to apply"
        exit 1
    fi
}

# Trap to handle interruptions
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"