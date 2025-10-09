# AnkiBlur

A modified version of [Anki](https://github.com/ankitects/anki) with window transparency effects. Automatically tracks and builds against new Anki releases.

## Downloads

| Platform | Downloads | Transparency Support |
|----------|-----------|---------------------|
| 🐧 **Linux** | [AppImage](../../releases/latest/download/AnkiBlur-latest-x86_64.AppImage) • [.deb](../../releases/latest) | Requires compositor (KWin, Mutter, etc.) |
| 🪟 **Windows** | [Installer](../../releases/latest) | Native blur support (Windows 8+) |
| 🍎 **macOS** | [.dmg](../../releases/latest) | Native blur support |

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
1. **Branding**: Changes "Anki" to "AnkiBlur"
2. **Transparency**: Adds `setWindowOpacity(0.95)` and CSS `backdrop-filter: blur(10px)`
3. **Version**: Updates metadata

GitHub Actions automatically builds new versions when Anki releases are detected.


## License

AGPL-3.0 (same as Anki)