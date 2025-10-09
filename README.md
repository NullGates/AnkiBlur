# AnkiBlur

This repo take the official [Anki](https://github.com/ankitects/anki) and applies patches on top for window blur effect. Automatically tracks and builds on each new Anki releases.

## Downloads

| Platform | Download (latest) | Transparency Support |
|----------|-----------|---------------------|
| <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Apple</title><path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg> | [AppImage](../../releases/latest/download/AnkiBlur-latest-x86_64.AppImage) • [.deb](../../releases/latest) | Requires compositor (KWin, Mutter, etc.) |
| <svg role="img" viewBox="0 0 10 11" width="24" height="24" xmlns="http://www.w3.org/2000/svg"><title>Windows</title><g transform="matrix(.947 0 0 .949 -.19 .354)"><path fill="white" d="m10.7 5.95v4.85l-5.57-0.87v-3.99z"/><path fill="white" d="m5.13 1.13 5.57-0.804v4.774h-5.57z"/><path fill="white" d="m4.39 5.91v3.95l-4.126-0.57v-3.4z"/><path fill="white" d="m0.261 1.77 4.129-0.57v3.95h-4.127z"/></g></svg> Windows | [.exe](../../releases/latest) | Native blur support (Windows 8+) |
| <svg role="img" viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg"><title>Apple</title><path fill="white" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg> macOS | [.dmg](../../releases/latest) | Native blur support |

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
