#!/bin/bash
set -euo pipefail

# Check existing AnkiBlur releases to avoid duplicates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
REPO="${GITHUB_REPOSITORY:-}"
TOKEN="${GITHUB_TOKEN:-}"
VERSION_FILE="$ROOT_DIR/configs/version-mapping.json"

# Function to get existing releases from GitHub
get_existing_releases() {
    if [[ -z "$REPO" || -z "$TOKEN" ]]; then
        echo "Warning: Cannot check existing releases (missing repo or token)"
        return
    fi

    echo "Checking existing releases on GitHub..."

    curl -s \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/releases" | \
        jq -r '.[].tag_name' 2>/dev/null || echo ""
}

# Function to check if a version exists
version_exists() {
    local version="$1"
    local existing_releases="$2"

    echo "$existing_releases" | grep -q "^$version$"
}

# Function to update version mapping with existing releases
update_version_mapping() {
    local existing_releases="$1"

    if [[ ! -f "$VERSION_FILE" ]]; then
        echo "{}" > "$VERSION_FILE"
    fi

    echo "Updating version mapping with existing releases..."

    # For each existing release, add to version mapping if not present
    while IFS= read -r version; do
        if [[ -n "$version" ]]; then
            # Check if version is already in mapping
            if ! jq -e --arg v "$version" '.[$v]' "$VERSION_FILE" >/dev/null 2>&1; then
                echo "Adding existing release to mapping: $version"

                # Get release info from GitHub
                local release_info=$(curl -s \
                    -H "Authorization: token $TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    "https://api.github.com/repos/$REPO/releases/tags/$version" 2>/dev/null)

                if [[ -n "$release_info" ]]; then
                    local created_date=$(echo "$release_info" | jq -r '.created_at // "unknown"')
                    local body=$(echo "$release_info" | jq -r '.body // ""')

                    # Try to extract Anki version from release body
                    local anki_version=$(echo "$body" | grep -o "Anki [v0-9][0-9.]*" | head -1 | cut -d' ' -f2 || echo "unknown")

                    # Update version mapping
                    local temp_file=$(mktemp)
                    jq --arg version "$version" \
                       --arg anki_version "$anki_version" \
                       --arg build_date "$created_date" \
                       '.[$version] = {
                           "anki_version": $anki_version,
                           "anki_commit": "unknown",
                           "build_date": $build_date,
                           "patches_applied": ["branding", "transparency", "version"],
                           "release_notes": "Imported from existing release"
                       }' "$VERSION_FILE" > "$temp_file"

                    mv "$temp_file" "$VERSION_FILE"
                fi
            fi
        fi
    done <<< "$existing_releases"
}

# Function to validate current build version
validate_build_version() {
    local blur_version="${BLUR_VERSION:-}"
    local anki_version="${ANKI_VERSION:-}"

    if [[ -z "$blur_version" ]]; then
        echo "Warning: BLUR_VERSION not set"
        return
    fi

    echo "Validating build version: $blur_version"

    # Get existing releases
    local existing_releases=$(get_existing_releases)

    # Check if this version already exists
    if version_exists "$blur_version" "$existing_releases"; then
        echo "Version $blur_version already exists!"
        echo "Existing releases:"
        echo "$existing_releases" | head -10

        # Set environment variable to indicate we shouldn't deploy
        if [[ -n "${GITHUB_ENV:-}" ]]; then
            echo "SHOULD_DEPLOY=no" >> "$GITHUB_ENV"
        fi

        return 1
    else
        echo "Version $blur_version is new, proceeding with build"

        # Update version mapping
        update_version_mapping "$existing_releases"

        return 0
    fi
}

# Function to suggest next version if current exists
suggest_next_version() {
    local blur_version="${BLUR_VERSION:-}"
    local anki_version="${ANKI_VERSION:-}"

    if [[ -z "$blur_version" || -z "$anki_version" ]]; then
        return
    fi

    echo "Suggesting next version for Anki $anki_version..."

    # Extract base version (remove any .patch_number suffix)
    local base_version=$(echo "$blur_version" | sed 's/\.[0-9]*$//')

    # Find highest patch number for this base version
    local existing_releases=$(get_existing_releases)
    local highest_patch=0

    while IFS= read -r version; do
        if [[ "$version" =~ ^${base_version}\.([0-9]+)$ ]]; then
            local patch_num="${BASH_REMATCH[1]}"
            if [[ $patch_num -gt $highest_patch ]]; then
                highest_patch=$patch_num
            fi
        fi
    done <<< "$existing_releases"

    local next_version="${base_version}.$((highest_patch + 1))"
    echo "Suggested next version: $next_version"

    # Set environment variable with suggested version
    if [[ -n "${GITHUB_ENV:-}" ]]; then
        echo "SUGGESTED_VERSION=$next_version" >> "$GITHUB_ENV"
    fi
}

# Main function
main() {
    echo "Checking existing AnkiBlur releases..."

    # Validate current build version
    if ! validate_build_version; then
        echo "Version validation failed"
        suggest_next_version
        exit 1
    fi

    echo "Release check complete"
}

main "$@"