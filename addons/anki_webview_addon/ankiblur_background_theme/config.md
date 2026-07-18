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

Restart Anki after changing settings.

## Environment variables (all optional)

Read at Anki startup.

### All platforms
- `ANKIBLUR_FRAMELESS=1` (Linux): same as `linux_frameless: true`.

### Windows (native DWM blur via pywinstyles)
- `ANKIBLUR_BACKDROP`: `acrylic` (default) | `mica` | `aero` |
  `transparent` | `auto` - the DWM material.
- `ANKIBLUR_DARK`: `1`/`0` - force the immersive dark titlebar on/off.
  When unset, follows Anki's night mode.
- `ANKIBLUR_TINT`: `#RRGGBB` or `#RRGGBBAA` title-bar tint.

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

Shortly after startup the add-on verifies the blur actually engaged. If
anything failed, a one-time non-blocking warning is shown (once per Anki
version and failure set) and details are printed to the console. State is
kept in `user_files/ankiblur-state.json`, which survives updates.
