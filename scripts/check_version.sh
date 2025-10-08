#!/bin/bash
set -euo pipefail

# Check for new Anki versions and determine if we should build
# This script sets environment variables for the GitHub workflow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ANKI_REPO="ankitects/anki"
CONFIG_FILE="$ROOT_DIR/configs/build-config.json"
VERSION_FILE="$ROOT_DIR/configs/version-mapping.json"

# Default values
SHOULD_BUILD="no"
SHOULD_DEPLOY="no"

# Function to get latest Anki release
get_latest_anki_release() {
    if [[ -n "${ANKI_VERSION_INPUT:-}" ]]; then
        echo "$ANKI_VERSION_INPUT"
        return
    fi

    # Get latest release from GitHub API
    curl -s "https://api.github.com/repos/$ANKI_REPO/releases/latest" | \
        jq -r '.tag_name'
}

# Function to get commit hash for a tag
get_commit_for_tag() {
    local tag="$1"
    curl -s "https://api.github.com/repos/$ANKI_REPO/git/refs/tags/$tag" | \
        jq -r '.object.sha'
}

# Function to check if we already built this version
version_already_built() {
    local anki_version="$1"

    if [[ ! -f "$VERSION_FILE" ]]; then
        return 1
    fi

    # Check if this Anki version is already in our mapping
    if jq -e --arg version "$anki_version" '.[$version]' "$VERSION_FILE" > /dev/null; then
        return 0
    fi

    return 1
}

# Function to generate AnkiBlur version
generate_blur_version() {
    local anki_version="$1"
    # Remove 'v' prefix if present
    anki_version="${anki_version#v}"

    # Check if this is a patch/rebuild
    local patch_number="1"
    if [[ -f "$VERSION_FILE" ]]; then
        # Get the highest patch number for this Anki version
        local existing=$(jq -r --arg version "v$anki_version" 'to_entries[] | select(.value.anki_version == $version) | .key' "$VERSION_FILE" 2>/dev/null || echo "")
        if [[ -n "$existing" ]]; then
            # Extract patch number and increment
            local last_patch=$(echo "$existing" | grep -o '\.[0-9]*$' | tr -d '.' || echo "0")
            patch_number=$((last_patch + 1))
        fi
    fi

    echo "${anki_version}.${patch_number}"
}

# Main logic
main() {
    echo "Checking for Anki updates..."

    # Get latest Anki version
    ANKI_VERSION=$(get_latest_anki_release)
    echo "Latest Anki version: $ANKI_VERSION"

    if [[ -z "$ANKI_VERSION" || "$ANKI_VERSION" == "null" ]]; then
        echo "Error: Could not fetch Anki version"
        exit 1
    fi

    # Get commit hash
    ANKI_COMMIT=$(get_commit_for_tag "$ANKI_VERSION")
    echo "Anki commit: $ANKI_COMMIT"

    # Generate AnkiBlur version
    BLUR_VERSION=$(generate_blur_version "$ANKI_VERSION")
    echo "AnkiBlur version: $BLUR_VERSION"

    # Check if we should build
    if [[ "${FORCE_VERSION:-false}" == "true" ]]; then
        echo "Force version enabled, will build"
        SHOULD_BUILD="yes"
        SHOULD_DEPLOY="yes"
    elif ! version_already_built "$ANKI_VERSION"; then
        echo "New Anki version detected, will build"
        SHOULD_BUILD="yes"
        SHOULD_DEPLOY="yes"
    else
        echo "Anki version already built"
        SHOULD_BUILD="no"
        SHOULD_DEPLOY="no"
    fi

    # Export environment variables for GitHub Actions
    {
        echo "ANKI_VERSION=$ANKI_VERSION"
        echo "ANKI_COMMIT=$ANKI_COMMIT"
        echo "BLUR_VERSION=$BLUR_VERSION"
        echo "SHOULD_BUILD=$SHOULD_BUILD"
        echo "SHOULD_DEPLOY=$SHOULD_DEPLOY"
    } >> "$GITHUB_ENV"

    echo "Version check complete:"
    echo "  Anki: $ANKI_VERSION"
    echo "  AnkiBlur: $BLUR_VERSION"
    echo "  Should build: $SHOULD_BUILD"
    echo "  Should deploy: $SHOULD_DEPLOY"
}

main "$@"