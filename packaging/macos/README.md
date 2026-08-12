# macOS DMG assets

## dmg-background.png

Drag-to-Applications background for the AnkiBlur DMG window.

- 1320x960 px @ 144 dpi (pHYs chunk set), so Finder renders it as a
  **660x480 pt** Retina background.
- Derived from `dmg-background-source.png` (846x528, cover-scaled to fill),
  with a white drag arrow between the two icon slots and soft light glows
  under each label position. The glows are load-bearing: when a DMG window
  has a background picture, Finder ALWAYS draws icon labels in black (even
  in dark mode), and half of this artwork is near-black.

## dmg-settings.py

[dmgbuild](https://dmgbuild.readthedocs.io/) settings consumed by the
`Create DMG` step in `.github/workflows/build-macos.yml`. dmgbuild writes
the `.DS_Store` (window geometry, icon coordinates, background alias)
headlessly — no Finder/AppleScript — and also creates the `/Applications`
symlink and packs `LICENSE`/`NOTICE` (AGPL conveyance).

### Layout (must stay in sync with the artwork)

Coordinates in points; icon positions are icon centers:

| Item                    | Position     |
|-------------------------|--------------|
| Window content size     | 660 x 480    |
| Icon size / text size   | 128 / 12     |
| `AnkiBlur.app`          | (165, 180)   |
| `Applications` symlink  | (495, 180)   |
| `LICENSE` (bottom row)  | (240, 368)   |
| `NOTICE` (bottom row)   | (420, 368)   |

If you move an icon in `dmg-settings.py`, regenerate the background so the
arrow and label glows land in the right places.
