# AnkiBlur

This repo take the official [Anki](https://github.com/ankitects/anki) and applies patches on top for window blur effect. Automatically tracks and builds on each new Anki releases.

## Downloads

| Platform | Downloads | Transparency Support |
|----------|-----------|---------------------|
| <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" />| [AppImage](../../releases/latest/download/AnkiBlur-latest-x86_64.AppImage) • [.deb](../../releases/latest) | Requires compositor (KWin, Mutter, etc.) |
| <img src="https://img.shields.io/badge/windows-%230078D6.svg?&style=for-the-badge&logo=windows&logoColor=white" /> | [Installer](../../releases/latest) | Native blur support (Windows 8+) |
| <img src="https://img.shields.io/badge/mac%20os-000000?style=for-the-badge&logo=apple&logoColor=white" />| [.dmg](../../releases/latest) | Native blur support |

> **Note**: Visual blur effects depend on your system's compositor. Without compositor support, you'll see transparency without blur.

## Features

- **Window Transparency**: Semi-transparent windows with compositor-dependent blur
- **Full Compatibility**: Works with existing Anki decks and add-ons
- **Automated Builds**: Daily checks for new Anki releases


## Manual Build

```bash
export ANKI_VERSION="v23.12.1"
export BLUR_VERSION="23.12.1.1"

./scripts/get_anki.sh && ./scripts/apply_patches.sh && ./scripts/build.sh
```

## How It Works

AnkiBlur applies patches to Anki source code:
1. **Branding**: Changes "Anki" to "AnkiBlur" (I'm not allowed to post as "Anki", altough all credits goes to the ankitechts !)
2. **Transparency**: Adds `setWindowOpacity(0.95)` and CSS `backdrop-filter: blur(10px)`
3. **Version**: Updates metadata

GitHub Actions automatically builds new versions when Anki releases are detected.


## License

AGPL-3.0 (same as Anki)