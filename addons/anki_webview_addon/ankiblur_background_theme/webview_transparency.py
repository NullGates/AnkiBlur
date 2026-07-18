# AnkiBlur webview canvas transparency.
#
# Replaces the old 0C site-packages patch to aqt/webview.py. Instead of
# rewriting upstream source lines, we fix up the already-constructed main
# webviews and wrap the AnkiWebView methods with anki.hooks.wrap so future
# instances / theme changes stay transparent.
#
# All transparency is scoped to the three main-window webview kinds -
# dialogs, the editor and the previewer stay opaque.

import traceback

import anki.hooks
from aqt import mw
from aqt.qt import Qt, QColor

# Populated by apply(); empty means apply() failed before scoping was set up,
# in which case the wrappers below all no-op.
MAIN_KINDS = frozenset()

_TRANSPARENT = "transparent"

# Appended to upstream's standard_css() output for main-window webviews.
# Appending (instead of string-replacing upstream's exact bytes) wins via
# the CSS cascade, is robust to upstream drift, and is idempotent when the
# venv was already text-patched by an old AnkiBlur launcher.
_CSS_APPENDIX = """
/* AnkiBlur */
body { background-color: transparent !important; }
:root, :root[class*=night-mode] { --canvas: transparent; }
"""


def _is_main_kind(view) -> bool:
    return getattr(view, "_kind", None) in MAIN_KINDS


def _make_transparent(view) -> None:
    view.page().setBackgroundColor(QColor(0, 0, 0, 0))
    view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def apply(ops: dict) -> None:
    global MAIN_KINDS

    try:
        from aqt.webview import AnkiWebView, AnkiWebViewKind
        MAIN_KINDS = frozenset({
            AnkiWebViewKind.MAIN,
            AnkiWebViewKind.TOP_TOOLBAR,
            AnkiWebViewKind.BOTTOM_TOOLBAR,
        })
    except Exception as e:
        traceback.print_exc()
        ops["webview_symbols"] = "symbol_missing"
        for op in ("fixup_existing", "wrap_init", "wrap_theme", "wrap_css"):
            ops[op] = f"failed: {e}"
        return
    ops["webview_symbols"] = "ok"

    # The three main webviews already exist when add-ons are imported
    # (setupMainWindow runs before setupAddons); fix them up directly.
    try:
        for attr in ("toolbarWeb", "web", "bottomWeb"):
            view = getattr(mw, attr, None)
            if view is not None:
                _make_transparent(view)
        ops["fixup_existing"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["fixup_existing"] = f"failed: {e}"

    # Cover any future (re-)construction of a main webview.
    try:
        def after_init(self, *args, **kwargs) -> None:
            try:
                if _is_main_kind(self):
                    _make_transparent(self)
            except Exception:
                traceback.print_exc()

        AnkiWebView.__init__ = anki.hooks.wrap(
            AnkiWebView.__init__, after_init, "after"
        )
        ops["wrap_init"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["wrap_init"] = f"failed: {e}"

    # Upstream resets the page background to the theme canvas color on theme
    # change (to avoid flashes); re-clear it afterwards. Upstream's own logic
    # (including ForceDarkMode handling) runs untouched first.
    try:
        def after_theme_change(self) -> None:
            try:
                if _is_main_kind(self):
                    self.page().setBackgroundColor(QColor(0, 0, 0, 0))
            except Exception:
                traceback.print_exc()

        AnkiWebView.on_theme_did_change = anki.hooks.wrap(
            AnkiWebView.on_theme_did_change, after_theme_change, "after"
        )
        ops["wrap_theme"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["wrap_theme"] = f"failed: {e}"

    # Make the page canvas itself transparent for main webviews.
    try:
        def around_standard_css(self, _old):
            css = _old(self)
            try:
                if _is_main_kind(self) and _CSS_APPENDIX not in css:
                    css += _CSS_APPENDIX
            except Exception:
                traceback.print_exc()
            return css

        AnkiWebView.standard_css = anki.hooks.wrap(
            AnkiWebView.standard_css, around_standard_css, "around"
        )
        ops["wrap_css"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["wrap_css"] = f"failed: {e}"
