# AnkiBlur

AnkiBlur is a modified version of [Anki](https://github.com/ankitects/anki) that adds transparency and blur effects to the user interface, creating a more modern and visually appealing experience while maintaining full compatibility with Anki's functionality.

## Features

- 🎨 **Transparency Effects**: Semi-transparent main window and dialogs
- ✨ **Blur Effects**: Background blur for a modern look
- 📱 **Native Performance**: All the power of Anki with enhanced visuals
- 🔄 **Full Compatibility**: Works with existing Anki decks and add-ons
- 🤖 **Automated Builds**: Automatically tracks Anki releases and builds AnkiBlur

## Architecture

AnkiBlur follows the same automated patching approach as VSCodium:

1. **Automated Monitoring**: Daily checks for new Anki releases
2. **Patch Application**: Applies transparency, branding, and version patches
3. **Multi-Platform Builds**: Automatically builds for Linux, Windows, and macOS
4. **Release Management**: Creates GitHub releases with proper versioning

## Directory Structure

```
ankiblur/
├── .github/workflows/     # GitHub Actions workflows
│   ├── build-ankiblur.yml # Main build workflow
│   └── check-anki-updates.yml # Daily update checker
├── configs/               # Configuration files
│   ├── build-config.json # Build settings
│   └── version-mapping.json # Version tracking
├── patches/               # Patch files
│   ├── branding/         # AnkiBlur branding patches
│   ├── transparency/     # UI transparency patches
│   └── version/          # Version string patches
└── scripts/               # Build and utility scripts
    ├── check_version.sh   # Version checking
    ├── get_anki.sh       # Download Anki source
    ├── apply_patches.sh  # Apply patches
    ├── build.sh          # Build AnkiBlur
    ├── package.sh        # Create distribution packages
    └── create_release.sh # Create GitHub releases
```

## How It Works

### 1. Automatic Updates
- GitHub Actions runs daily to check for new Anki releases
- When a new release is detected, it triggers the build workflow
- Version mapping tracks which Anki versions have been built

### 2. Patching Process
The build system applies patches in this order:
1. **Branding**: Changes "Anki" to "AnkiBlur" in UI and about dialogs
2. **Transparency**: Adds window transparency and blur effects
3. **Version**: Updates version strings and metadata

### 3. Build Process
- Downloads Anki source code for the target version
- Applies all patches sequentially
- Builds AnkiBlur for multiple platforms (Linux, Windows, macOS)
- Creates distribution packages (AppImage, .deb, .exe, .dmg, etc.)

### 4. Release Management
- Automatically creates GitHub releases
- Uploads all platform packages
- Generates release notes
- Updates version tracking

## Manual Build

To build AnkiBlur manually:

```bash
# Set environment variables
export ANKI_VERSION="v23.12.1"  # Target Anki version
export BLUR_VERSION="23.12.1.1" # AnkiBlur version

# Run the build process
./scripts/check_version.sh
./scripts/get_anki.sh
./scripts/apply_patches.sh
./scripts/build.sh
./scripts/package.sh
```

## Configuration

### Build Configuration (`configs/build-config.json`)
- Platform-specific build settings
- Package formats for each platform
- Dependency requirements
- Patch application order

### Version Mapping (`configs/version-mapping.json`)
- Tracks which Anki versions have been built
- Maps AnkiBlur versions to Anki versions
- Stores build metadata and patch information

## Patches

### Branding Patches
- `01-app-name.patch`: Changes app name from "Anki" to "AnkiBlur"
- `02-about-dialog.patch`: Updates about dialog with AnkiBlur information
- `03-window-title.patch`: Changes window titles to show "AnkiBlur"

### Transparency Patches
- `01-main-window-transparency.patch`: Adds transparency to main window
- `02-dialog-transparency.patch`: Makes dialogs semi-transparent
- `03-webview-transparency.patch`: Applies transparency to web content

### Version Patches
- `01-pyproject-version.patch`: Updates project metadata and URLs

## GitHub Actions Workflows

### Main Build Workflow (`build-ankiblur.yml`)
- Triggered by new Anki releases, manual dispatch, or code changes
- Builds for multiple platforms and architectures
- Creates and uploads release packages
- Updates version tracking

### Update Checker (`check-anki-updates.yml`)
- Runs daily to check for new Anki releases
- Triggers builds automatically for significant releases
- Creates issues for manual review when needed

## Contributing

1. **Adding New Patches**: Place patch files in the appropriate `patches/` subdirectory
2. **Modifying Build Process**: Update scripts in `scripts/` directory
3. **Platform Support**: Modify build configuration and platform-specific scripts

## Platform Support

- **Linux**: x64, ARM64 (AppImage, .deb, .tar.gz)
- **Windows**: x64 (.exe installer, .zip)
- **macOS**: x64, ARM64 (.dmg, .tar.gz)

## License

AnkiBlur is licensed under the same AGPL-3.0 license as Anki. See the original Anki repository for license details.

## Acknowledgments

- Based on [Anki](https://github.com/ankitects/anki) by Damien Elmes
- Inspired by the [VSCodium](https://github.com/VSCodium/vscodium) project's approach to automated patching
- Built with GitHub Actions for continuous integration