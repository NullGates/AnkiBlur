# AnkiBlur window-title branding.
#
# aqt hardcodes "Anki" in the main-window title in two places
# (qt/aqt/main.py: `setWindowTitle(f"{pm.name} - Anki")` on profile load,
# `setWindowTitle("Anki")` in updateTitleBar). Both run AFTER add-on setup
# (setupAddons happens before the profile loads), so rebinding
# mw.setWindowTitle here intercepts every future title; the current title
# is rewritten immediately as well in case one was already set.

import os
import re
import traceback

from aqt import mw

# Rewrite only a trailing standalone "Anki" ("User 1 - Anki", "Anki").
# Deliberately not every occurrence: a profile literally named "Anki"
# ("Anki - Anki") must keep its name. \b keeps "MyAnki" untouched.
_TITLE_RE = re.compile(r"\bAnki$")


def _rebrand(title: str) -> str:
    return _TITLE_RE.sub("AnkiBlur", title)


def _apply_window_icon(ops: dict) -> None:
    """Swap the running app's window/taskbar icon for the AnkiBlur logo.

    The launcher exe/.desktop entries already carry the AnkiBlur icon, but
    the window Anki itself opens uses aqt's bundled Anki icon — on Windows
    and Linux that is what the taskbar shows while the app runs. On macOS
    the Dock uses the .app bundle's Assets.car instead, and a Qt window
    icon would only add a title-bar proxy icon, so it is skipped there.
    """
    try:
        from aqt.qt import QApplication, QIcon
        from aqt.utils import is_mac

        if is_mac:
            ops["icon_brand"] = "ok: skipped on macOS (bundle icon)"
            return
        icon = QIcon(os.path.join(os.path.dirname(__file__), "ankiblur_icon.png"))
        if icon.isNull():
            ops["icon_brand"] = "failed: ankiblur_icon.png missing/unreadable"
            return
        # App-wide first so future dialogs inherit it, then the already
        # created main window explicitly.
        QApplication.setWindowIcon(icon)
        mw.setWindowIcon(icon)
        ops["icon_brand"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["icon_brand"] = f"failed: {e}"


def apply(ops: dict) -> None:
    """Rebind mw.setWindowTitle so titles show AnkiBlur instead of Anki."""
    _apply_window_icon(ops)
    try:
        original = mw.setWindowTitle

        def branded_set_window_title(title: str) -> None:
            try:
                title = _rebrand(title)
            except Exception:
                # Never let branding break a title update.
                traceback.print_exc()
            original(title)

        # Instance attribute shadows the Qt method; aqt only ever calls
        # mw.setWindowTitle(...), so every caller goes through the rewrite.
        mw.setWindowTitle = branded_set_window_title
        mw.setWindowTitle(mw.windowTitle())
        ops["title_brand"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["title_brand"] = f"failed: {e}"
