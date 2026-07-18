# AnkiBlur background theme add-on.
#
# Entry point. Everything the AnkiBlur launcher used to text-patch into
# aqt's site-packages now happens here, at add-on import time, through
# stable aqt APIs (gui_hooks, anki.hooks.wrap, direct Qt calls on mw).
#
# aqt runs setupAddons() after the QMainWindow and the three main webviews
# (toolbarWeb, web, bottomWeb) have been constructed, but before the window
# is shown, so the Qt attributes we set here behave identically to the old
# source patches (no native-window recreation).
#
# Nothing in this module may fail silently: every operation records its
# outcome into a shared `ops` dict, and tripwire.py verifies after startup
# that the blur actually engaged, showing a one-time non-blocking warning
# if it did not.

import sys
import traceback

try:
    from aqt import mw, gui_hooks
    from aqt.qt import *  # noqa: F403
    from aqt.utils import showInfo
    from aqt.overview import Overview
    from aqt.theme import theme_manager
    from anki.hooks import wrap

    from . import tripwire
    from . import webview_transparency
    from . import window_effects
    from .config_dialog import ColorConfigDialog

    def _build_main_window_contexts():
        """Content contexts belonging to the three main-window webviews.

        Built defensively: each class is optional so that upstream renames
        degrade to "no injection for that context" instead of a crash.
        Unknown contexts (editor, previewer, dialogs...) never get the
        overlay - they must stay opaque.
        """
        classes = []
        for module_name, attr in (
            ("aqt.deckbrowser", "DeckBrowser"),
            # The bottom bar's web_context is a per-state class, not
            # aqt.toolbar.BottomToolbar: deckbrowser.py passes
            # DeckBrowserBottomBar and overview.py passes OverviewBottomBar
            # (BottomToolbar is only Toolbar's never-used fallback default).
            ("aqt.deckbrowser", "DeckBrowserBottomBar"),
            ("aqt.overview", "Overview"),
            ("aqt.overview", "OverviewBottomBar"),
            ("aqt.reviewer", "Reviewer"),
            ("aqt.reviewer", "ReviewerBottomBar"),
            ("aqt.toolbar", "TopToolbar"),
            ("aqt.toolbar", "BottomToolbar"),
        ):
            try:
                module = __import__(module_name, fromlist=[attr])
                classes.append(getattr(module, attr))
            except (ImportError, AttributeError):
                print(f"[AnkiBlur] context class unavailable: {module_name}.{attr}")
        return tuple(classes)

    class TransparentOverlay:
        def __init__(self):
            self.config = mw.addonManager.getConfig(__name__)
            self.main_window_contexts = _build_main_window_contexts()
            self.migrate_config_if_needed()
            self.setup_hooks()
            self.wrap_finished_screen()
            self.setup_theme_change_hook()

        def migrate_config_if_needed(self):
            """Migrate old single-theme config to new dual-theme format"""
            if self.config is None:
                self.config = {
                    "light_theme": {"color": "#ffffff", "alpha": 15},
                    "dark_theme": {"color": "#000000", "alpha": 30}
                }
                return

            # Check if this is old format (has 'color' and 'alpha' directly)
            if "color" in self.config and "alpha" in self.config:
                old_color = self.config.get("color", "#000000")
                old_alpha = self.config.get("alpha", 30)

                self.config = {
                    "light_theme": {"color": "#ffffff", "alpha": old_alpha},
                    "dark_theme": {"color": old_color, "alpha": old_alpha}
                }

                # Save migrated config
                mw.addonManager.writeConfig(__name__, self.config)
                showInfo("Transparent Overlay: Updated to support separate Dark/Light theme colors!\n\n"
                        "Your previous settings have been preserved for Dark theme.\n"
                        "You can now configure different colors for Light theme in the addon settings.")

        def setup_hooks(self):
            """Setup hooks to inject HTML/CSS overlay"""
            gui_hooks.webview_will_set_content.append(self.inject_overlay)

        def setup_theme_change_hook(self):
            """Setup hook to respond to theme changes"""
            gui_hooks.theme_did_change.append(self.on_theme_change)

        def on_theme_change(self):
            """Called when Anki theme changes - reapply overlay with new theme colors"""
            # Refresh all three main-window webviews (not just mw.web) so the
            # toolbar and bottom bar don't keep the previous theme's tint.
            for attr in ("web", "toolbarWeb", "bottomWeb"):
                webview = getattr(mw, attr, None)
                if webview:
                    self.inject_current_theme_style(webview)

        def get_current_theme_config(self):
            """Get color config for current theme (dark/light)"""
            is_dark = theme_manager.night_mode
            theme_key = "dark_theme" if is_dark else "light_theme"

            # Fallback if theme config missing
            fallback = {
                "color": "#000000" if is_dark else "#ffffff",
                "alpha": 30 if is_dark else 15
            }

            return self.config.get(theme_key, fallback)

        def inject_current_theme_style(self, webview):
            """Inject current theme overlay style into a main-window webview"""
            theme_config = self.get_current_theme_config()
            color = theme_config.get("color", "#000000")
            alpha = theme_config.get("alpha", 30)

            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            js_code = f"""
            // Remove existing theme overlay styles
            const existingStyle = document.getElementById('transparent-overlay-theme-style');
            if (existingStyle) {{
                existingStyle.remove();
            }}

            // Add new theme overlay style
            const style = document.createElement('style');
            style.id = 'transparent-overlay-theme-style';
            style.textContent = `
                html {{
                    background-color: rgba({r}, {g}, {b}, {alpha/100}) !important;
                }}
                body {{
                    background-color: transparent !important;
                }}
            `;
            document.head.appendChild(style);
            """

            webview.eval(js_code)

        def wrap_finished_screen(self):
            """Wrap the finished screen to inject our styles"""
            Overview._show_finished_screen = wrap(
                Overview._show_finished_screen, self.inject_finished_screen_style, "after"
            )

        def inject_finished_screen_style(self, overview):
            """Inject styles into the finished/congratulations screen"""
            theme_config = self.get_current_theme_config()
            color = theme_config.get("color", "#000000")
            alpha = theme_config.get("alpha", 30)

            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            js_code = f"""
            const style = document.createElement('style');
            style.textContent = `
                html {{
                    background-color: rgba({r}, {g}, {b}, {alpha/100}) !important;
                }}
                body {{
                    background-color: transparent !important;
                }}
            `;
            document.head.appendChild(style);
            """

            mw.web.eval(js_code)

        def inject_overlay(self, web_content, context):
            """Inject the tint overlay into main-window webviews only.

            Dialog webviews (editor, previewer, deck options...) are left
            untouched: they are opaque by design, and stripping their
            backgrounds made them unreadable.
            """
            if not isinstance(context, self.main_window_contexts):
                return

            theme_config = self.get_current_theme_config()
            color = theme_config.get("color", "#000000")
            alpha = theme_config.get("alpha", 30)

            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            # Apply background color directly to body
            background_css = f"""
            <style>
            html {{
                background-color: rgba({r}, {g}, {b}, {alpha/100}) !important;
            }}

            body {{
                background-color: transparent !important;
            }}

            /* Main web view - force background on all potential containers */
            #outer, #main, .main-webview {{
                background-color: transparent !important;
            }}

            /* Make card backgrounds transparent to show through */
            .card {{
                background-color: transparent !important;
            }}

            /* Congratulations screen - target all possible selectors */
            .congrats-container, .congrats, div[id*="congrat"], div[class*="congrat"] {{
                background-color: transparent !important;
            }}

            /* Overview screen */
            .overview, div[class*="overview"] {{
                background-color: transparent !important;
            }}
            </style>
            """

            web_content.head += background_css

    def on_config():
        dialog = ColorConfigDialog(mw)
        if dialog.exec():
            # Merge the dialog's themes over the existing config so keys the
            # dialog does not manage (e.g. linux_frameless) are preserved
            # instead of being wiped from meta.json.
            merged = dict(mw.addonManager.getConfig(__name__) or {})
            merged.update(dialog.get_config())
            overlay.config = merged
            mw.addonManager.writeConfig(__name__, overlay.config)
            showInfo("Color overlay settings updated! Restart Anki to see the changes.")

    # op_id -> "ok" | "ok: <detail>" | "symbol_missing" | "failed: <msg>".
    # Shared with the async retry loops in window_effects; tripwire reads it
    # after startup.
    ops = {}

    overlay = TransparentOverlay()
    window_effects.apply(ops)
    webview_transparency.apply(ops)
    tripwire.arm(ops)

    mw.addonManager.setConfigAction(__name__, on_config)

except Exception as exc:  # noqa: BLE001 - never fail silently, never crash Anki
    # stdout, not stderr: aqt's ErrorHandler intercepts stderr and would pop
    # Anki's generic add-on-crash dialog on top of our own report_fatal one.
    traceback.print_exc(file=sys.stdout)
    try:
        from . import tripwire
        tripwire.report_fatal(exc)
    except Exception:
        # Even the reporter is broken; the traceback above is all we have.
        traceback.print_exc(file=sys.stdout)
