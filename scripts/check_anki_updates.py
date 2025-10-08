#!/usr/bin/env python3
"""
Check for new Anki releases and determine if AnkiBlur should be built.
This script is used by the GitHub Actions workflow.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
ANKI_REPO = "ankitects/anki"
BLUR_REPO = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# File paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
VERSION_FILE = ROOT_DIR / "configs" / "version-mapping.json"
CHECK_FILE = ROOT_DIR / ".last-check"

def get_github_headers():
    """Get headers for GitHub API requests."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

def get_latest_anki_release():
    """Get the latest Anki release from GitHub."""
    url = f"https://api.github.com/repos/{ANKI_REPO}/releases/latest"
    response = requests.get(url, headers=get_github_headers())
    response.raise_for_status()
    return response.json()

def get_anki_releases():
    """Get all Anki releases from GitHub."""
    url = f"https://api.github.com/repos/{ANKI_REPO}/releases"
    response = requests.get(url, headers=get_github_headers())
    response.raise_for_status()
    return response.json()

def load_version_mapping():
    """Load the version mapping file."""
    if not VERSION_FILE.exists():
        return {}

    try:
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_version_mapping(mapping):
    """Save the version mapping file."""
    VERSION_FILE.parent.mkdir(exist_ok=True)
    with open(VERSION_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)

def was_recently_checked():
    """Check if we've recently checked for updates."""
    if not CHECK_FILE.exists():
        return False

    try:
        with open(CHECK_FILE, 'r') as f:
            last_check = datetime.fromisoformat(f.read().strip())

        # Consider "recent" as within the last 2 hours
        return datetime.now() - last_check < timedelta(hours=2)
    except (ValueError, IOError):
        return False

def mark_checked():
    """Mark that we've checked for updates."""
    with open(CHECK_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def version_already_built(anki_version, version_mapping):
    """Check if we've already built this Anki version."""
    anki_version = anki_version.lstrip('v')

    for blur_version, info in version_mapping.items():
        if info.get('anki_version', '').lstrip('v') == anki_version:
            return True

    return False

def is_significant_release(release):
    """Determine if this is a significant release worth building."""
    tag = release['tag_name']
    name = release['name'] or tag
    body = release['body'] or ""

    # Skip pre-releases unless forced
    if release['prerelease']:
        return False

    # Skip if it's a minor patch (like 2.1.66.1)
    if tag.count('.') > 2:
        return False

    # Look for keywords that indicate major changes
    significant_keywords = [
        'major', 'breaking', 'new feature', 'ui change', 'interface',
        'rework', 'rewrite', 'overhaul'
    ]

    text_to_check = (name + " " + body).lower()
    for keyword in significant_keywords:
        if keyword in text_to_check:
            return True

    # Default to building all releases
    return True

def get_existing_ankiblur_releases():
    """Get existing AnkiBlur releases."""
    if not BLUR_REPO:
        return []

    url = f"https://api.github.com/repos/{BLUR_REPO}/releases"
    try:
        response = requests.get(url, headers=get_github_headers())
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

def set_github_output(name, value):
    """Set GitHub Actions output."""
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
    print(f"::set-output name={name}::{value}")

def main():
    print("Checking for Anki updates...")

    # Check if we should skip due to recent check
    force_check = os.environ.get('FORCE_CHECK', 'false').lower() == 'true'
    if not force_check and was_recently_checked():
        print("Recently checked for updates, skipping")
        set_github_output('new_release', 'false')
        set_github_output('needs_review', 'false')
        return

    try:
        # Get latest Anki release
        latest_release = get_latest_anki_release()
        anki_version = latest_release['tag_name']

        print(f"Latest Anki release: {anki_version}")

        # Load our version mapping
        version_mapping = load_version_mapping()

        # Check if we've already built this version
        if version_already_built(anki_version, version_mapping):
            print(f"Already built AnkiBlur for Anki {anki_version}")
            set_github_output('new_release', 'false')
            set_github_output('needs_review', 'false')
            mark_checked()
            return

        print(f"New Anki release detected: {anki_version}")

        # Determine if this is a significant release
        if is_significant_release(latest_release):
            print("Release appears significant, triggering automatic build")
            set_github_output('new_release', 'true')
            set_github_output('needs_review', 'false')
            set_github_output('anki_version', anki_version)
            set_github_output('changes_url', latest_release['html_url'])
        else:
            print("Release appears minor, creating issue for manual review")
            set_github_output('new_release', 'false')
            set_github_output('needs_review', 'true')
            set_github_output('anki_version', anki_version)
            set_github_output('changes_url', latest_release['html_url'])

        mark_checked()

    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()