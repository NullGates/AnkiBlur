# AnkiBlur window-title branding.
#
# aqt hardcodes "Anki" in the main-window title in two places
# (qt/aqt/main.py: `setWindowTitle(f"{pm.name} - Anki")` on profile load,
# `setWindowTitle("Anki")` in updateTitleBar). Both run AFTER add-on setup
# (setupAddons happens before the profile loads), so rebinding
# mw.setWindowTitle here intercepts every future title; the current title
# is rewritten immediately as well in case one was already set.

import re
import traceback

from aqt import mw

# Rewrite only a trailing standalone "Anki" ("User 1 - Anki", "Anki").
# Deliberately not every occurrence: a profile literally named "Anki"
# ("Anki - Anki") must keep its name. \b keeps "MyAnki" untouched.
_TITLE_RE = re.compile(r"\bAnki$")


def _rebrand(title: str) -> str:
    return _TITLE_RE.sub("AnkiBlur", title)


def apply(ops: dict) -> None:
    """Rebind mw.setWindowTitle so titles show AnkiBlur instead of Anki."""
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
