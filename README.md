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


<a id="download"></a>
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



<a id="installation"></a>
<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-hash-dark.svg">
    <img src="./docs/icon-hash-light.svg" height="40" align="center" alt="">
  </picture>
  Installation
</h2>

> *"Wait — why is it opening a command line? Am I being hacked? I don't remember
> this happening when I installed Anki back in the day."*
>
> You're not being hacked, and you're not misremembering. Anki switched to a
> launcher-based install: instead of shipping one big bundle, a small launcher
> downloads Anki and its Python/Qt runtime on first run. That's the terminal you
> see. The decision was made upstream by Anki's maintainer to cut release overhead
> and get something close to auto-updates — see discussion
> [ankitects/anki#4556](https://github.com/ankitects/anki/issues/4556).

<details>
<summary><big><big><b>macOS</b></big></big></summary>

<br>

1. Download the `.dmg` from the [latest release](https://github.com/NullGates/AnkiBlur/releases/latest).
2. Open it and drag **AnkiBlur.app** to your `Applications` folder.
3. Launch it from Applications or Spotlight. The first run opens a terminal with
   the **AnkiBlur Launcher** menu — press <kbd>Enter</kbd> to take the latest version.
   It downloads Anki, the Qt runtime and the blur add-on, then tells you the
   window can be closed.

Later launches skip the menu and start AnkiBlur directly.

> **Note:** the DMG is signed and notarized, so Gatekeeper lets it open normally.
> That runs on my own Apple Developer account ($99/year, out of pocket) — donations
> toward it are very welcome.

</details>

<details>
<summary><big><big><b>Windows</b></big></big></summary>

<br>

1. Download the `.exe` from the [latest release](https://github.com/NullGates/AnkiBlur/releases/latest).
2. Run it. SmartScreen will warn that the publisher is unknown — click **More info** → **Run anyway**.
3. Launch **AnkiBlur** from the Start menu. The first run opens a console with the
   **AnkiBlur Launcher** menu — press <kbd>Enter</kbd> to take the latest version. It
   downloads Anki, the Qt runtime and the blur add-on, then tells you the window
   can be closed.

Later launches skip the menu and start AnkiBlur directly.

> **Note:** the installer is unsigned (AnkiBlur has no code-signing certificate),
> so that warning is expected on every install. It installs per-user to
> `%LOCALAPPDATA%\Programs\AnkiBlur` and needs no admin rights.

</details>

<details>
<summary><big><big><b>Linux</b></big></big></summary>

<br>

Pick the format that matches your distro — all are on the
[latest release](https://github.com/NullGates/AnkiBlur/releases/latest) page.

**Debian / Ubuntu / Mint / Pop!_OS**
```bash
sudo apt install ./ankiblur_*.deb
ankiblur
```

**Fedora / RHEL / openSUSE**
```bash
sudo dnf install ./ankiblur-*.rpm   # openSUSE: sudo zypper install ./ankiblur-*.rpm
ankiblur
```

**Any distro (portable)**
```bash
chmod +x AnkiBlur-*.AppImage
./AnkiBlur-*.AppImage
```

**NixOS** — *to be arriving*

The first run opens the **AnkiBlur Launcher** menu in your terminal — press
<kbd>Enter</kbd> to take the latest version. It downloads Anki, the Qt runtime and the
blur add-on, then prompts you to press <kbd>Enter</kbd> again to start. Later launches skip the
menu and start AnkiBlur directly.

The `.deb` and `.rpm` install the command as `ankiblur` and add a menu entry, so
they sit alongside stock Anki without conflict. The `.tar.zst` is the plain
launcher payload for distros that match neither family — extract it and run
`./anki`.

Requires **glibc 2.36 or newer**.

</details>

### Installation Issues

<details>
<summary><big><big><b>macOS</b></big></big></summary>

<br>

**macOS says "AnkiBlur.app is damaged"**

> Right-click the app, select "Open", then click "Open" in the security dialog.

</details>

<details>
<summary><big><big><b>Windows</b></big></big></summary>

<br>

**Windows Defender blocks the installer**

> AnkiBlur's Windows releases aren't code-signed, so Windows has no publisher to
> verify and raises the alarm on every install. That's expected, not a sign
> something is wrong. Click **More info** → **Run anyway** to continue.

</details>

<details>
<summary><big><big><b>Linux</b></big></big></summary>

<br>

**Getting "Qt platform plugin" errors**

> Qt itself ships inside the bundled PyQt6 wheels; what's usually missing are the system xcb runtime libraries it loads:
> - **Ubuntu/Debian**: `sudo apt install libxcb-cursor0 libxcb-xinerama0`

**The blur effect isn't working**

> Blur effects require a compositor. Install one of these:
> - **Wayland**: Sway, Hyprland, or GNOME (Mutter)
> - **X11**: KWin (KDE), Compiz, or Picom

**AppImage won't run - "Permission denied"**

> Make it executable: `chmod +x AnkiBlur-*.AppImage`

</details>


<a id="faq"></a>
<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-help-circle-dark.svg">
    <img src="./docs/icon-help-circle-light.svg" height="40" align="center" alt="">
  </picture>
  FAQ
</h2>

### General Questions

**What's the difference between AnkiBlur and regular Anki?**

> AnkiBlur is identical to Anki but with window transparency and blur effects. All Anki features work exactly the same.

**Will my existing Anki data work, and can I run both Anki and AnkiBlur?**

> Anki and AnkiBlur share the same data directory (where your cards and decks are).
> Don't run both at the same time, as they aren't used to this setup.

### Why is the blur not showing !!! >:[

If these questions don't handle your case, please
[open a GitHub issue](https://github.com/NullGates/AnkiBlur/issues/new) and I'll try
to help you :)

**I installed AnkiBlur and the window is transparent, but there's no blur**

> AnkiBlur makes the window transparent and asks your OS to blur what's behind it —
> it can't draw the blur itself. On **Linux** that means you need a compositor that
> implements blur (KWin, Hyprland, Picom with blur enabled…); without one you get
> transparency and nothing else. **macOS** should work fine out of the box.
> **Windows** blur is freaking complicated — open an issue about your Windows
> version and I'll take a look at it.

**The blur worked, then a theming add-on made it disappear**

> Some theming add-ons paint an opaque background over the transparent canvas.
> Toggle your theming add-ons off one at a time to find the culprit, then set its
> background colour to none/transparent in its config.

### Addons and making Anki all pwetty :3

**Does AnkiBlur support add-ons?**

> Yes, all Anki add-ons are fully compatible — but AnkiBlur is new, and some
> theming add-ons paint an opaque background over the transparent canvas, which
> hides the blur. If that happens, toggle your theming add-ons off one at a time to
> find the culprit, then set its background color to none/transparent in its config.

**Can I adjust the transparency level?**

> You can change the tint color and alpha per theme in Anki under Tools → Add-ons → AnkiBlur Background Theme → Config (defaults: light `#ffffff` at alpha 15, dark `#1a1a2e` at alpha 25).
>
> This is very platform specific, this section will need more love.

**How can I make the background more [insert colour] while keeping the blur?**

> That's what the bundled **AnkiBlur Background Theme** add-on is for — it tints the
> transparent canvas with a colour and an alpha (opacity), so the blur still shows
> through. If you installed AnkiBlur you already have it: go to
> **Tools → Add-ons → AnkiBlur Background Theme → Config** and set `color` (hex) and
> `alpha` (0–255) for the light and dark themes independently.

### Updating and Uninstalling

**How do I completely uninstall AnkiBlur?**

> - **Linux**: `sudo apt remove ankiblur` (for the .deb) or delete the AppImage
> - **macOS**: Drag the app to Trash
> - **Windows**: Use "Add/Remove Programs" or run the uninstaller
> - **Launcher runtime**: delete `~/.local/share/AnkiBlurProgramFiles/` (Linux; equivalent data dir on other platforms)
> - **User data**: lives in the shared `~/.local/share/Anki2/` — do NOT delete as it holds your cards and profiles

<a id="how-it-works"></a>
<h2>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./docs/icon-layers-dark.svg">
    <img src="./docs/icon-layers-light.svg" height="40" align="center" alt="">
  </picture>
  How It Works
</h2>

<p align="center">
  I will be updating this section on a day where I have something very stressful to
  do and suddenly all the boring chores become interesting — the inner workings of
  AnkiBlur are freaking complicated, and maintaining it is even more a pain (thank
  goodness we have Claude!).
</p>

<p align="center">
  Licensed under AGPL-3.0-or-later — see <a href="LICENSE">LICENSE</a> and <a href="NOTICE">NOTICE</a>.
</p>
