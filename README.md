# AnkiBlur

This repo takes the official [Anki](https://github.com/ankitects/anki) and applies patches on top for window blur effect. Automatically tracks and builds on each new Anki releases.

## Downloads

| Platform | Supported Architecture | Download Latest | Blur Support |
|---|---|---|---|
| <img width="150" src="https://img.shields.io/badge/%20-Linux-b1cc10?style=for-the-badge&logo=linux&logoColor=white&labelColor=2e2e2e" />| ![linux_x86](https://custom-icon-badges.demolab.com/badge/%20-%C3%9786-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e) ![linux_aarch64](https://custom-icon-badges.demolab.com/badge/%20-aarch64-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e) | ![download_AppImage](https://custom-icon-badges.demolab.com/badge/Download%20-AppImage-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e) ![download_Flatpack](https://custom-icon-badges.demolab.com/badge/Download%20-Flatpack-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e) ![download_Deb](https://custom-icon-badges.demolab.com/badge/Download%20-.Deb-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e) | Requires compositor (Hyprland, Sway, KWin, Mutter, etc.) |
|  <img width="150" src="https://img.shields.io/badge/%20-MacOS-b1cc10?style=for-the-badge&logo=apple&logoColor=white&labelColor=2e2e2e" /> | ![apple_intel](https://custom-icon-badges.demolab.com/badge/%20-Intel-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e) ![apple_silicon](https://custom-icon-badges.demolab.com/badge/%20-silicon-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e) | ![download_dmg](https://custom-icon-badges.demolab.com/badge/Download%20-.dmg-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e)| Native blur support |
| <img width="400" src="https://custom-icon-badges.demolab.com/badge/%20-windows-b1cc10?style=for-the-badge&logo=windowsz&logoColor=white&labelColor=2e2e2e" /> | ![windows_x64](https://custom-icon-badges.demolab.com/badge/%20-%C3%9764-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e) ![windows_arm64](https://custom-icon-badges.demolab.com/badge/%20-ARM64-e35007?style=for-the-badge&logoSource=feather&logo=x&logoColor=white&labelColor=2e2e2e)| ![download_exe](https://custom-icon-badges.demolab.com/badge/Download%20-.exe-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e) | Native blur support (Windows 8+) |


<div style="display: flex; align-items: center; border-left: 4px solid #ffffffff; padding: 0.5em 1em; background-color: #2e2e2e70; border-radius: 4px; margin: 8px 0;">

<img src="https://tender-wash.surge.sh/white-alert-triangle.svg" alt="alert-triangle" style="width: 20px; height: 20px; margin-right: 10px;">
  <div>
    <strong>Note:</strong> Visual blur effects depend on your system's compositor. Without compositor support, you'll see transparency without blur.
  </div>
</div>

><img src="https://tender-wash.surge.sh/white-alert-triangle.svg" alt="alert-triangle" style="width: 20px; height: 20px; margin-right: 10px;">
><strong>Note:</strong> Visual blur effects depend on your system's compositor. Without compositor support, you'll see transparency without blur.





## Screenshot

[screenshot to be added]

## Installation

### Linux

#### Option 1: AppImage (Recommended)
```bash
# Download the AppImage
wget https://github.com/your-repo/ankiblur/releases/latest/download/ankiblur-linux-x86_64.AppImage

# Make it executable
chmod +x ankiblur-linux-x86_64.AppImage

# Run directly
./ankiblur-linux-x86_64.AppImage

# Optional: Integrate with system
./ankiblur-linux-x86_64.AppImage --appimage-extract
sudo mv squashfs-root /opt/ankiblur
sudo ln -s /opt/ankiblur/AppRun /usr/local/bin/ankiblur
```

#### Option 2: Debian Package (.deb)
```bash
# Download and install
wget https://github.com/your-repo/ankiblur/releases/latest/download/ankiblur-linux-x86_64.deb
sudo apt install ./ankiblur-linux-x86_64.deb

# Or with dpkg
sudo dpkg -i ankiblur-linux-x86_64.deb
sudo apt install -f  # Fix dependencies if needed
```

#### Option 3: Flatpak
```bash
# Install from Flathub (coming soon)
flatpak install flathub net.ankiblur.AnkiBlur

# Run
flatpak run net.ankiblur.AnkiBlur
```

#### Option 4: NixOS
```bash
# Using nix run (requires flakes)
nix run github:your-repo/ankiblur

# Or build locally
nix-build ankiblur-patchelf.nix
./result/bin/ankiblur
```

### macOS

#### Download and Install
```bash
# Download DMG
wget https://github.com/your-repo/ankiblur/releases/latest/download/ankiblur-macos-universal.dmg

# Mount and install
open ankiblur-macos-universal.dmg
# Drag AnkiBlur.app to Applications folder
```

#### Command Line (Homebrew - coming soon)
```bash
brew install --cask ankiblur
```

### Windows

#### Option 1: Installer (Recommended)
1. Download `ankiblur-windows-x64.exe` from [releases](https://github.com/your-repo/ankiblur/releases/latest)
2. Run the installer as Administrator
3. Follow installation wizard
4. Launch from Start Menu or Desktop shortcut

#### Option 2: Portable
1. Download `ankiblur-windows-x64-portable.zip`
2. Extract to desired folder
3. Run `ankiblur.exe` directly

#### Option 3: Package Managers
```powershell
# Chocolatey (coming soon)
choco install ankiblur

# Winget (coming soon)
winget install AnkiBlur
```

## FAQ

### General Questions

**Q: What's the difference between AnkiBlur and regular Anki?**
A: AnkiBlur is identical to Anki but with window transparency and blur effects. All Anki features work exactly the same.

**Q: Will my existing Anki data work with AnkiBlur?**
A: Yes! AnkiBlur uses the same data format and profile system as Anki. Your cards, decks, and settings are fully compatible.

**Q: Can I run both Anki and AnkiBlur on the same system?**
A: Yes, they can coexist. They use separate profile directories by default.

**Q: How do I sync my data between devices?**
A: Use AnkiWeb sync exactly like regular Anki. Your AnkiWeb account works with both.

### Installation Issues

**Q: The blur effect isn't working on Linux**
A: Blur effects require a compositor. Install one of these:
- **Wayland**: Sway, Hyprland, or GNOME (Mutter)
- **X11**: KWin (KDE), Compiz, or Picom

**Q: Getting "libEGL.so.1 not found" error on NixOS**
A: Use the NixOS-specific installation method or run with `nixGL`.

**Q: AppImage won't run - "Permission denied"**
A: Make it executable: `chmod +x ankiblur-*.AppImage`

**Q: macOS says "AnkiBlur.app is damaged"**
A: Right-click the app, select "Open", then click "Open" in the security dialog.

**Q: Windows Defender blocks the installer**
A: This is a false positive. Click "More info" → "Run anyway" or temporarily disable real-time protection.

### Performance & Features

**Q: Does AnkiBlur affect performance?**
A: Minimal impact. The blur effect uses hardware acceleration when available.

**Q: Can I adjust the transparency level?**
A: Currently fixed at 95% opacity. Customization options coming in future versions.

**Q: Does AnkiBlur support add-ons?**
A: Yes! All Anki add-ons are fully compatible.

**Q: How do I update AnkiBlur?**
A: Download and install the latest version. Your data and settings are preserved.

### Troubleshooting

**Q: AnkiBlur crashes on startup**
A: Try these solutions:
1. Update your graphics drivers
2. Disable hardware acceleration: `ankiblur --disable-gpu`
3. Reset preferences: Delete `~/.local/share/ankiblur/prefs21.db`

**Q: Sync isn't working**
A: Check your internet connection and AnkiWeb credentials. Sync works identically to regular Anki.

**Q: Getting "Qt platform plugin" errors**
A: Install required Qt libraries:
- **Ubuntu/Debian**: `sudo apt install qt6-base-dev`
- **Fedora**: `sudo dnf install qt6-qtbase-devel`

**Q: How do I completely uninstall AnkiBlur?**
A:
- **Linux**: `sudo apt remove ankiblur` or delete AppImage
- **macOS**: Drag AnkiBlur.app to Trash
- **Windows**: Use "Add/Remove Programs" or run uninstaller
- **Data**: Delete `~/.local/share/ankiblur/` (Linux) or equivalent on other platforms

## How It Works

AnkiBlur applies patches to Anki source code:
1. **Branding**: Changes "Anki" to "AnkiBlur" (I'm not allowed to post as "Anki", altough all credits goes to the ankitechts !)
2. **Transparency**: Adds `setWindowOpacity(0.95)` and CSS `backdrop-filter: blur(10px)`
3. **Version**: Updates metadata

GitHub Actions automatically builds new versions when Anki releases are detected.


## License

AGPL-3.0 (same as Anki)
