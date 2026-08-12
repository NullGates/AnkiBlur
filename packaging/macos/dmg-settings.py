# dmgbuild settings for the AnkiBlur DMG.
#
# Rendered headlessly on the CI runner (no Finder/AppleScript):
#   python3 -m dmgbuild -s dmg-settings.py \
#     -D app=... -D license=... -D notice=... -D background=... -D size=... \
#     "AnkiBlur" AnkiBlur-<version>.dmg
#
# The geometry below is what packaging/macos/dmg-background.png was drawn
# for (660x480 pt window, 128 pt icons) -- keep them in sync. See README.md.

import os.path

app = defines.get("app", "out/launcher/AnkiBlur.app")  # noqa: F821
license_file = defines.get("license", "LICENSE")  # noqa: F821
notice_file = defines.get("notice", "NOTICE")  # noqa: F821

files = [app, license_file, notice_file]
symlinks = {"Applications": "/Applications"}

# Icon centers, in points, matching the arrow/glow artwork.
icon_locations = {
    "AnkiBlur.app": (165, 180),
    "Applications": (495, 180),
    "LICENSE": (240, 368),
    "NOTICE": (420, 368),
}

background = defines.get(  # noqa: F821
    "background", os.path.join(os.path.dirname(__file__), "dmg-background.png")
)

format = defines.get("format", "UDZO")  # noqa: F821
# Explicit size: hdiutil auto-sizing has produced ENOSPC inside the mounted
# intermediate volume before (see build-macos.yml). The workflow computes it.
size = defines.get("size", None)  # noqa: F821

window_rect = ((200, 120), (660, 480))
default_view = "icon-view"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False

icon_size = 128
text_size = 12
label_pos = "bottom"
arrange_by = None
show_icon_preview = False
scroll_position = (0, 0)
