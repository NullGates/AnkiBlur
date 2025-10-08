#!/bin/bash
set -euo pipefail

# Update version tracking after successful release

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
VERSION_FILE="$ROOT_DIR/configs/version-mapping.json"
BLUR_VERSION="${BLUR_VERSION:-}"
ANKI_VERSION="${ANKI_VERSION:-}"
ANKI_COMMIT="${ANKI_COMMIT:-}"

# Function to update version mapping
update_version_mapping() {
    local blur_version="$1"
    local anki_version="$2"
    local anki_commit="$3"

    echo "Updating version mapping for AnkiBlur $blur_version..."

    # Ensure version file exists
    if [[ ! -f "$VERSION_FILE" ]]; then
        echo "{}" > "$VERSION_FILE"
    fi

    # Create build info
    local build_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local patches_applied='["branding", "transparency", "version"]'

    # Generate release notes
    local release_notes="AnkiBlur $blur_version based on Anki $anki_version with transparency and blur effects"

    # Update the version mapping file
    local temp_file=$(mktemp)
    jq --arg blur_version "$blur_version" \
       --arg anki_version "$anki_version" \
       --arg anki_commit "$anki_commit" \
       --arg build_date "$build_date" \
       --arg release_notes "$release_notes" \
       --argjson patches_applied "$patches_applied" \
       '.[$blur_version] = {
           "anki_version": $anki_version,
           "anki_commit": $anki_commit,
           "build_date": $build_date,
           "patches_applied": $patches_applied,
           "release_notes": $release_notes
       }' "$VERSION_FILE" > "$temp_file"

    mv "$temp_file" "$VERSION_FILE"

    echo "Version mapping updated successfully"
}

# Function to commit version tracking updates
commit_version_update() {
    echo "Committing version tracking updates..."

    cd "$ROOT_DIR"

    # Check if we're in a git repository and have changes
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "Not in a git repository, skipping commit"
        return
    fi

    # Check if version file has changes
    if ! git diff --quiet "$VERSION_FILE" 2>/dev/null; then
        echo "Version mapping has changes, committing..."

        # Configure git if in CI environment
        if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
        fi

        # Add and commit the version file
        git add "$VERSION_FILE"
        git commit -m "Update version mapping for AnkiBlur $BLUR_VERSION

Based on Anki $ANKI_VERSION ($ANKI_COMMIT)
Built: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"

        # Push if we have the right permissions
        if [[ -n "${GITHUB_TOKEN:-}" ]] && [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
            echo "Pushing version tracking updates..."
            git push origin HEAD
        else
            echo "No push permissions, version update committed locally"
        fi
    else
        echo "No changes in version mapping, skipping commit"
    fi
}

# Function to create a summary for GitHub Actions
create_build_summary() {
    echo "Creating build summary..."

    local summary_file="${GITHUB_STEP_SUMMARY:-/dev/null}"

    cat >> "$summary_file" << EOF
# AnkiBlur Build Summary

## Build Information
- **AnkiBlur Version**: $BLUR_VERSION
- **Based on Anki**: $ANKI_VERSION
- **Anki Commit**: $ANKI_COMMIT
- **Build Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Patches Applied
- ✅ Branding (AnkiBlur name and about dialog)
- ✅ Transparency (window and dialog transparency)
- ✅ Version (updated version strings and metadata)

## Release Status
- ✅ Built successfully
- ✅ Packaged for all platforms
- ✅ Released to GitHub
- ✅ Version tracking updated

## Downloads
The release is available at: https://github.com/${GITHUB_REPOSITORY:-}/releases/tag/$BLUR_VERSION
EOF

    echo "Build summary created"
}

# Function to notify about the release
notify_release() {
    echo "Release notification for AnkiBlur $BLUR_VERSION"

    # Log release information
    echo "=== RELEASE COMPLETE ==="
    echo "AnkiBlur Version: $BLUR_VERSION"
    echo "Anki Version: $ANKI_VERSION"
    echo "Anki Commit: $ANKI_COMMIT"
    echo "Release URL: https://github.com/${GITHUB_REPOSITORY:-}/releases/tag/$BLUR_VERSION"
    echo "========================="

    # Create GitHub Actions annotation if available
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
        echo "::notice title=Release Complete::AnkiBlur $BLUR_VERSION has been released successfully"
    fi
}

# Function to clean up temporary files
cleanup() {
    echo "Cleaning up temporary files..."

    # Remove any temporary build artifacts older than 1 day
    find "$ROOT_DIR" -name "*.tmp" -o -name "*.temp" -mtime +1 -type f -delete 2>/dev/null || true

    # Clean up old logs
    find "$ROOT_DIR" -name "*.log" -mtime +7 -type f -delete 2>/dev/null || true

    echo "Cleanup complete"
}

# Main function
main() {
    echo "Updating version tracking after release..."

    if [[ -z "$BLUR_VERSION" || -z "$ANKI_VERSION" ]]; then
        echo "Error: Missing required version information"
        echo "  BLUR_VERSION: $BLUR_VERSION"
        echo "  ANKI_VERSION: $ANKI_VERSION"
        exit 1
    fi

    # Update version mapping
    update_version_mapping "$BLUR_VERSION" "$ANKI_VERSION" "$ANKI_COMMIT"

    # Commit version updates
    commit_version_update

    # Create build summary
    create_build_summary

    # Notify about release
    notify_release

    # Clean up
    cleanup

    echo "Version tracking update complete"
}

main "$@"