<p align="center">
  <img src="./docs/screenshots.png" alt="AnkiBlur screenshot showing window blur effect" width="100%">
</p>

<p align="center">
  This repo takes the official <a href="https://github.com/ankitects/anki">Anki</a> app and applies custom patches on top to achieve a window blur effect.
</p>

<p align="center">
  <a href="#download">Download</a>
  ·
  <a href="#installation">Installation</a>
  ·
  <a href="#faq">FAQ</a>
  ·
  <a href="#how-it-works">How It Works</a>
</p>


<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-download-dark.svg">
    <img src="./docs/icon-download-light.svg" height="40" align="center" alt="">
  </picture>
  Download
</h2>

<table>
  <thead>
    <tr>
      <th width="200" align="left">Platform</th>
      <th width="240" align="left">Supported Architecture</th>
      <th width="300" align="left">Download Latest</th>
      <th width="260" align="left">Blur Support</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="200" valign="middle"><img height="40" src="https://img.shields.io/badge/%20-MacOS-b1cc10?style=for-the-badge&logo=apple&logoColor=white&labelColor=2e2e2e" /></td>
      <td width="240" valign="middle"><img height="28" alt="apple_intel" src="https://custom-icon-badges.demolab.com/badge/%20-Intel-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e"> <img height="28" alt="apple_silicon" src="https://custom-icon-badges.demolab.com/badge/%20-silicon-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e"></td>
      <td width="300" valign="middle"><a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_dmg" src="https://custom-icon-badges.demolab.com/badge/Download%20-.dmg-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e"></a></td>
      <td width="260" valign="middle">Native blur support (macOS 10.15+)</td>
    </tr>
    <tr>
      <td width="200" valign="middle"><img height="40" src="https://custom-icon-badges.demolab.com/badge/%20-windows-b1cc10?style=for-the-badge&logo=windowsz&logoColor=white&labelColor=2e2e2e" /></td>
      <td width="240" valign="middle"><img height="28" alt="windows_x64" src="https://custom-icon-badges.demolab.com/badge/%20-%C3%9764-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e"> <br><img height="28" alt="windows_arm64" src="https://custom-icon-badges.demolab.com/badge/%20-ARM64-e35007?style=for-the-badge&logoSource=feather&logo=x&logoColor=white&labelColor=2e2e2e"></td>
      <td width="300" valign="middle"><a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_exe" src="https://custom-icon-badges.demolab.com/badge/Download%20-.exe-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e"></a></td>
      <td width="260" valign="middle">Native blur support (Windows 10 1803+)<br>Installer is unsigned — SmartScreen will warn</td>
    </tr>
    <tr>
      <td width="200" valign="middle"><img height="40" src="https://img.shields.io/badge/%20-Linux-b1cc10?style=for-the-badge&logo=linux&logoColor=white&labelColor=2e2e2e" /></td>
      <td width="240" valign="middle"><img height="28" alt="linux_x86" src="https://custom-icon-badges.demolab.com/badge/%20-%C3%9786-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e"> <img height="28" alt="linux_aarch64" src="https://custom-icon-badges.demolab.com/badge/%20-aarch64-59b300?style=for-the-badge&logoSource=feather&logo=check&logoColor=white&labelColor=2e2e2e"></td>
      <td width="300" valign="middle"><a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_AppImage" src="https://custom-icon-badges.demolab.com/badge/Download%20-AppImage-blue?style=for-the-badge&logoSource=feather&logo=download&logoColor=white&labelColor=2e2e2e"></a> <a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_deb" src="https://custom-icon-badges.demolab.com/badge/Download%20-.deb-blue?style=for-the-badge&logoSource=simple-icons&logo=debian&logoColor=white&labelColor=2e2e2e"></a><br> <a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_rpm" src="https://custom-icon-badges.demolab.com/badge/Download%20-.rpm-blue?style=for-the-badge&logoSource=simple-icons&logo=fedora&logoColor=white&labelColor=2e2e2e"></a> <a href="https://github.com/NullGates/AnkiBlur/releases/latest"><img height="22" alt="download_tarzst" src="https://custom-icon-badges.demolab.com/badge/Download%20-.tar.zst-blue?style=for-the-badge&logoSource=feather&logo=package&logoColor=white&labelColor=2e2e2e"></a><br> <a href="https://github.com/NullGates/AnkiBlur"><img height="22" alt="nixos_flake" src="https://custom-icon-badges.demolab.com/badge/I'm%20working%20on%20it...%20-flake-8a8a8a?style=for-the-badge&logoSource=simple-icons&logo=nixos&logoColor=white&labelColor=2e2e2e"></a> <a href="https://github.com/NullGates/AnkiBlur"><img height="22" alt="nixos_stable" src="https://custom-icon-badges.demolab.com/badge/also%20working%20on%20it%20%3A3%20-Nix%20stable%20pkgs-8a8a8a?style=for-the-badge&logoSource=simple-icons&logo=nixos&logoColor=white&labelColor=2e2e2e"></a></td>
      <td width="260" valign="middle">Requires a compositor implementing blur<br>Needs glibc 2.36 or newer</td>
    </tr>
  </tbody>
</table>


[comment]: <> (<img src="https://tender-wash.surge.sh/white-alert-triangle.svg" alt="alert-triangle" style="width: 20px; height: 20px; margin-right: 10px;">) 
><strong>Note:</strong> AnkiBlur makes the window transparent and nudges your OS to draw blur. Only your operating system knows what's behind the window (like your wallpaper or other apps) and can therefore apply the blur effect to that background content. If you only see transparency without blur, im sorry :(



<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-hash-dark.svg">
    <img src="./docs/icon-hash-light.svg" height="40" align="center" alt="">
  </picture>
  Installation
</h2>

Every method ships only the launcher. On first run it downloads Anki and the Qt
runtime into `AnkiBlurProgramFiles`, so the first launch needs a network connection.

<details>
<summary><h3>macOS</h3></summary>

<br>

1. Download the `.dmg` from the [latest release](https://github.com/NullGates/AnkiBlur/releases/latest).
2. Open it and drag **Anki.app** to your `Applications` folder.
3. Launch it from Applications or Spotlight.

The DMG is signed and notarized, so Gatekeeper lets it open normally.

> **Note:** the bundle is named `Anki.app`, so it will overwrite stock Anki if you
> have it installed. Rename one of them if you want to keep both.

Requires macOS 10.15 or newer. To uninstall, drag the app to the Trash.

</details>

<details>
<summary><h3>Windows</h3></summary>

<br>

1. Download the `.exe` from the [latest release](https://github.com/NullGates/AnkiBlur/releases/latest).
2. Run it. SmartScreen will warn that the publisher is unknown — click **More info** → **Run anyway**.
3. Launch **AnkiBlur** from the Start menu.

The installer is unsigned (AnkiBlur has no code-signing certificate), so that
warning is expected on every install. It installs per-user to
`%LOCALAPPDATA%\Programs\AnkiBlur` and needs no admin rights.

Requires Windows 10 1803 or newer for the blur effect. To uninstall, use
**Add/Remove Programs**.

</details>

<details>
<summary><h3>Linux</h3></summary>

<br>

Pick the format that matches your distro — all are on the
[latest release](https://github.com/NullGates/AnkiBlur/releases/latest) page.

**Debian / Ubuntu / Mint / Pop!_OS**
```bash
sudo apt install ./ankiblur_*_amd64.deb
ankiblur
```

**Fedora / RHEL / openSUSE**
```bash
sudo dnf install ./ankiblur-*.x86_64.rpm   # openSUSE: sudo zypper install ./ankiblur-*.rpm
ankiblur
```

**Any distro (portable)**
```bash
chmod +x AnkiBlur-*.AppImage
./AnkiBlur-*.AppImage
```

The `.deb` and `.rpm` install the command as `ankiblur` and add a menu entry, so
they sit alongside stock Anki without conflict. The `.tar.zst` is the plain
launcher payload for distros that match neither family — extract it and run
`./anki`.

Requires **glibc 2.36 or newer** (Ubuntu 24.04+, Debian 12+, Fedora 37+) and a
compositor that implements blur. To uninstall: `sudo apt remove ankiblur`,
`sudo dnf remove ankiblur`, or delete the AppImage.

</details>

<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-help-circle-dark.svg">
    <img src="./docs/icon-help-circle-light.svg" height="40" align="center" alt="">
  </picture>
  FAQ
</h2>

### General Questions

**Q: What's the difference between AnkiBlur and regular Anki?**
A: AnkiBlur is identical to Anki but with window transparency and blur effects. All Anki features work exactly the same.

**Q: Will my existing Anki data work with AnkiBlur?**
A: Yes! AnkiBlur uses the same data format and profile system as Anki. Your cards, decks, and settings are fully compatible.

**Q: Can I run both Anki and AnkiBlur on the same system?**
A: Yes, they can be installed side by side. Be aware that they share the same Anki data directory and profiles (`~/.local/share/Anki2` on Linux, and the platform equivalents) — your decks, settings and add-ons are common to both. Only the launcher runtime lives separately (in `AnkiBlurProgramFiles` instead of `AnkiProgramFiles`). Don't run both at the same time.

**Q: How do I sync my data between devices?**
A: Use AnkiWeb sync exactly like regular Anki. Your AnkiWeb account works with both.

### Installation Issues

**Q: The blur effect isn't working on Linux**
A: Blur effects require a compositor. Install one of these:
- **Wayland**: Sway, Hyprland, or GNOME (Mutter)
- **X11**: KWin (KDE), Compiz, or Picom

**Q: Getting "libEGL.so.1 not found" error on NixOS**
A: The bundled binaries expect a conventional filesystem layout. Run AnkiBlur through `nixGL` (e.g. `nixGL ./anki`) or `steam-run`.

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
A: The window canvas is fully transparent; what you see is a configurable tint drawn by the bundled AnkiBlur addon. Change the tint color and alpha per theme in Anki under Tools → Add-ons → AnkiBlur Background Theme → Config (defaults: light `#ffffff` at alpha 15, dark `#1a1a2e` at alpha 25).

**Q: Does AnkiBlur support add-ons?**
A: Yes! All Anki add-ons are fully compatible.

**Q: How do I update AnkiBlur?**
A: Download and install the latest version. Your data and settings are preserved.

### Troubleshooting

**Q: AnkiBlur crashes on startup**
A: Try these solutions:
1. Update your graphics drivers
2. Reset preferences: delete `~/.local/share/Anki2/prefs21.db` — note this file is shared with stock Anki, so back it up first

**Q: Sync isn't working**
A: Check your internet connection and AnkiWeb credentials. Sync works identically to regular Anki.

**Q: Getting "Qt platform plugin" errors**
A: Qt itself ships inside the bundled PyQt6 wheels; what's usually missing are the system xcb runtime libraries it loads:
- **Ubuntu/Debian**: `sudo apt install libxcb-cursor0 libxcb-xinerama0`

**Q: How do I completely uninstall AnkiBlur?**
A:
- **Linux**: `sudo apt remove ankiblur` (for the .deb) or delete the AppImage
- **macOS**: Drag the app to Trash
- **Windows**: Use "Add/Remove Programs" or run the uninstaller
- **Launcher runtime**: delete `~/.local/share/AnkiBlurProgramFiles/` (Linux; equivalent data dir on other platforms)
- **User data**: lives in the shared `~/.local/share/Anki2/` — do NOT delete it if you also use stock Anki, it holds your cards and profiles for both

<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-layers-dark.svg">
    <img src="./docs/icon-layers-light.svg" height="40" align="center" alt="">
  </picture>
  How It Works
</h2>

AnkiBlur is the official Anki launcher plus a bundled add-on — no Anki source
files are modified on your machine:

1. **Branding (build time)**: the launcher source is patched so the app
   presents itself as "AnkiBlur" and installs alongside stock Anki (I'm not
   allowed to post as "Anki", altough all credits goes to the ankitechts !).
2. **Bundled add-on (runtime)**: the entire blur/transparency payload ships as
   a regular Anki add-on (`ankiblur_background_theme`) embedded in the
   launcher binary and installed into your `addons21/` folder. At load time it
   uses only stable, supported Anki APIs (`gui_hooks`, `anki.hooks.wrap`,
   direct Qt calls) to:
   - make the main window translucent and ask the OS for native blur
     (macOS glass, Windows acrylic, your compositor's blur rules on Linux),
   - render the main webviews (card area, toolbars) on a transparent canvas
     with a configurable tint overlay.
3. **Self-check**: after startup the add-on verifies the effects actually
   applied and shows a warning inside Anki (once per Anki version) if an
   upstream change ever breaks them — nothing fails silently.

Because nothing is text-patched at runtime, AnkiBlur keeps working across Anki
point releases; a weekly CI probe additionally checks each new aqt release for
the handful of symbols the add-on relies on.

<p align="center">
  Licensed under AGPL-3.0-or-later — see <a href="LICENSE">LICENSE</a> and <a href="NOTICE">NOTICE</a>.
</p>
