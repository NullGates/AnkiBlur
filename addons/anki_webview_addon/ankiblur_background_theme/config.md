# AnkiBlur Background Theme - configuration

## Config keys

- `light_theme` / `dark_theme`: tint overlay applied over the blurred
  desktop for Anki's light and dark themes.
  - `color`: `#RRGGBB` hex color of the tint.
  - `alpha`: `0`-`100` opacity of the tint (0 = fully transparent).
- `linux_frameless` (Linux only, default `false`): remove the window
  titlebar/decorations (`FramelessWindowHint`). Leave off on floating
  desktop environments (you would lose the titlebar, close button and
  mouse resizing); tiling window managers generally don't need it.
- `windows` (Windows only): knobs for the native blur + frameless window.
  Each key maps to the `ANKIBLUR_*` environment variable of the same
  meaning below; a set environment variable always wins over the config.
  `""` / `"auto"` mean "use the built-in default".
  - `backend` (default `"auto"`): force a single blur backend:
    `accent-acrylic` | `accent-blur` | `dwm` | `mica1029` | `none`.
    `auto` picks `accent-acrylic` on Win10 1803+/Win11 with `accent-blur`
    as fallback. `dwm` (the documented Win11 backdrop API) does NOT render
    behind Anki's translucent window and is never chosen automatically.
  - `backdrop` (default `"acrylic"`): requested material when `backend`
    is `auto`: `acrylic` | `aero` | `mica`/`tabbed` (best effort) | `none`.
  - `accent_tint` (default `""` = follow Anki's theme): `#RRGGBB` tint the
    accent backends blend over the blur (theme default: `#101010` dark /
    `#F9F9F9` light).
  - `accent_alpha` (default `153`): `0`-`255` opacity of that tint
    (clamped to >= 1; alpha 0 would disable the blur entirely).
  - `border` (default `"none"`): `none` removes the 1px Win11 window
    border hairline; `default` keeps it; `#RRGGBB` colors it.
  - `corners` (default `"round"`): Win11 corner style:
    `round` | `small` | `square`.
  - `drag_fix` (default `true`): swap acrylic to plain blur while the
    window is being moved/resized (works around Win10 acrylic drag lag).
  - `legacy_grips` (default `false`): disable the native frame/filter and
    use the old Qt edge grips instead (debug fallback; breaks Aero Snap).

Restart Anki after changing settings.

## Environment variables (all optional)

Read at Anki startup. On Windows they override the `windows` config keys.

### All platforms
- `ANKIBLUR_FRAMELESS=1` (Linux): same as `linux_frameless: true`.

### Windows (native blur via ctypes - see docs/WINDOWS_IMPLEMENTATION.md)
- `ANKIBLUR_BACKEND`: force a backend: `accent-acrylic` | `accent-blur` |
  `dwm` | `mica1029` | `none` (skips auto-detection).
- `ANKIBLUR_BACKDROP`: `acrylic` (default) | `aero` | `mica`/`tabbed`
  (best effort) | `none` - the requested material.
- `ANKIBLUR_ACCENT_TINT`: `#RRGGBB` tint of the accent blur backends.
- `ANKIBLUR_ACCENT_ALPHA`: `0`-`255` tint opacity (default `153`).
- `ANKIBLUR_BORDER`: `none` (default) | `default` | `#RRGGBB` - Win11
  window border.
- `ANKIBLUR_CORNERS`: `round` (default) | `small` | `square`.
- `ANKIBLUR_DRAG_FIX`: `1` (default) / `0` - Win10 acrylic drag-lag swap.
- `ANKIBLUR_DARK`: `1`/`0` - force the immersive dark titlebar on/off.
  When unset, follows Anki's night mode.
- `ANKIBLUR_TINT`: `#RRGGBB` DWM caption color (best effort).
- `ANKIBLUR_FRAME_MODE`: `thick` (default) | `none` (debug: no
  WS_THICKFRAME - kills Aero Snap).
- `ANKIBLUR_LEGACY_GRIPS=1`: same as `legacy_grips: true`.
- `ANKIBLUR_NC_LOG=<path>`: debug: append every non-client mouse message
  + hit-test classification to a file.

### macOS (Liquid Glass via pyqt-liquidglass)
- `ANKIBLUR_STYLE`: int, `0`=Regular `1`=Clear `2`=Frosted `3`=Chromatic
  (macOS 26+ NSGlassEffectView).
- `ANKIBLUR_SUBVARIANT`: int, private subvariant fine-tune.
- `ANKIBLUR_SCRIM`: int, `0`=Off `1`=Subdued `2`=Normal.
- `ANKIBLUR_LENSING`: `1`/`0`, content-lensing effect.
- `ANKIBLUR_TINT`: `#RRGGBB` or `#RRGGBBAA` glass tint color.
- `ANKIBLUR_APPEARANCE`: e.g. `NSAppearanceNameAqua` to force light glass
  even when the system is in dark mode.

## Self-check

Shortly after startup the add-on verifies the blur actually engaged. On
Windows it also records WHICH blur backend engaged (e.g.
`win_blur: ok: backend=accent-acrylic`) and warns only when none did. If
anything failed, a one-time non-blocking warning is shown (once per Anki
version and failure set) and details are printed to the console. State is
kept in `user_files/ankiblur-state.json`, which survives updates.
