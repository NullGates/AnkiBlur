# AnkiBlur launcher icons

Binary icon assets cannot ride in the text `.patch` files, so
`scripts/validate-and-apply-patches.sh` copies this directory's contents over
the Anki source tree right after the patches apply:

| repo file                          | destination in anki-source                                  | consumer |
|------------------------------------|-------------------------------------------------------------|----------|
| `macos/AppIcon.appiconset/`        | `qt/launcher/mac/icon/Assets.xcassets/AppIcon.appiconset/`  | `icon/build.sh` (actool) regenerates `Assets.car`, copied into `AnkiBlur.app/Contents/Resources` by the mac build |
| `windows/anki-icon.ico`            | `qt/launcher/win/anki-icon.ico`                             | embedded in `anki.exe` via `anki-manifest.rc`; NSIS installer file associations |
| `linux/anki.png` (256x256)         | `qt/launcher/lin/anki.png`                                  | `scripts/package-linux.sh`: hicolor 256x256 icon in deb/rpm + AppImage icon |
| `linux/anki.xpm` (32x32)           | `qt/launcher/lin/anki.xpm`                                  | upstream tarball `install.sh` legacy icon |

The macOS `Assets.car` is NOT replaced at staging time (actool only exists on
macOS); `.github/workflows/build-macos.yml` runs `qt/launcher/mac/icon/build.sh`
after patching to recompile it from the replaced appiconset.

## Sources (`src/`)

`src/` holds the designer exports ("AnkiBlur logo Exports 2 - Pre Tahoe -
legacy", 1024x1024): `Default`, `Dark`, `ClearLight`, `ClearDark`,
`TintedLight`, `TintedDark`.

Everything shipped today is rendered from **Default**. The five other
profiles are the *legacy fallback renders* of the macOS 26 (Tahoe)
appearance variants — pre-Tahoe asset catalogs support only a single icon,
and the real variant switching needs the Icon Composer `.icon` project
(layer source), which PNG exports cannot reconstruct. They are kept here so
a future Tahoe `.icon` adoption has the reference renders.

## Regenerating

From the repo root (ImageMagick 7):

```bash
D=patches/01_launcher_branding/icons/src/ankiblur-Default-1024.png
# macOS appiconset (per Contents.json slot: 16/32/64/128/256/512/1024)
magick "$D" -resize 16x16   -depth 8 -strip .../AppIcon.appiconset/icon_16x16.png   # etc.
# Windows
magick "$D" -depth 8 -strip -define icon:auto-resize=256,128,96,64,48,32,24,16 \
    patches/01_launcher_branding/icons/windows/anki-icon.ico
# Linux
magick "$D" -resize 256x256 -depth 8 -strip patches/01_launcher_branding/icons/linux/anki.png
magick "$D" -resize 32x32 -depth 8 -colors 200 patches/01_launcher_branding/icons/linux/anki.xpm
# Add-on runtime window icon (Windows/Linux taskbar while Anki runs)
magick "$D" -resize 256x256 -depth 8 -strip \
    addons/anki_webview_addon/ankiblur_background_theme/ankiblur_icon.png
```

After touching the add-on icon, rebuild the committed zip:
`python3 scripts/build-addon-zip.py --source addons/anki_webview_addon/ankiblur_background_theme --top-dir ankiblur_background_theme --output addons/anki_webview_addon/ankiblur_background_theme.ankiaddon`
