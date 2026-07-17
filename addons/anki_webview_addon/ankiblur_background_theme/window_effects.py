# AnkiBlur per-OS main-window blur strategies.
#
# Replaces the old 0B_{LINUX,WINDOWS,MACOS} site-packages patches. Applied
# at add-on import time (the main window exists but is not yet shown).
#
# Every operation records its outcome into the shared `ops` dict
# ("ok" | "symbol_missing" | "failed: <msg>"); tripwire.py surfaces
# failures to the user after startup.

import os
import sys
import traceback

from aqt import mw
from aqt.qt import Qt, QTimer

# True while we expect WA_TranslucentBackground to be set on the main
# window. Cleared when a native-effect backend gives up and we deliberately
# restore an opaque window (a translucent window without a native blur
# behind it renders black / unreadable). tripwire skips its translucency
# probe when this is False - the corresponding op already reports failure.
_translucency_expected = False


def translucency_expected() -> bool:
    return _translucency_expected


def apply(ops: dict) -> None:
    if sys.platform == "win32":
        _apply_windows(ops)
    elif sys.platform == "darwin":
        _apply_macos(ops)
    else:
        # linux and other unixes
        _apply_linux(ops)


def _set_translucent(clear: bool = False) -> None:
    global _translucency_expected
    mw.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, not clear)
    _translucency_expected = not clear


def _get_config() -> dict:
    try:
        return mw.addonManager.getConfig(__name__) or {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Linux
# ---------------------------------------------------------------------------

def _apply_linux(ops: dict) -> None:
    # Per-pixel transparency: WA_TranslucentBackground plus the transparent
    # webview canvases (webview_transparency.py) is all that is needed.
    #
    # Note there is deliberately NO setWindowOpacity(0.0) here: on a
    # compositing X11 session it makes the entire app invisible
    # (_NET_WM_WINDOW_OPACITY applies to the whole window), and on Wayland
    # it is a no-op. There is no configuration in which it helps.
    try:
        _set_translucent()
        ops["linux_translucent"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["linux_translucent"] = f"failed: {e}"

    try:
        mw.form.centralwidget.setAutoFillBackground(False)
        ops["linux_autofill"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["linux_autofill"] = f"failed: {e}"

    # Frameless is opt-in: floating desktop environments lose the titlebar,
    # close button and resizing with FramelessWindowHint, while tiling WMs
    # decorate/tile the window themselves and don't need it.
    try:
        config = _get_config()
        frameless = bool(config.get("linux_frameless")) or (
            os.environ.get("ANKIBLUR_FRAMELESS") == "1"
        )
        if frameless:
            mw.setWindowFlags(mw.windowFlags() | Qt.WindowType.FramelessWindowHint)
            ops["linux_frameless"] = "ok"
    except Exception as e:
        traceback.print_exc()
        ops["linux_frameless"] = f"failed: {e}"


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

def _is_dark_theme() -> bool:
    """Best-effort detection of Anki's current night mode, for the immersive
    dark titlebar. Falls back to False (light) if anything is unavailable."""
    try:
        if mw is not None and getattr(mw, "pm", None) is not None:
            return bool(mw.pm.night_mode())
    except Exception:
        pass
    try:
        from aqt.theme import theme_manager
        return bool(theme_manager.night_mode)
    except Exception:
        return False


def _apply_windows(ops: dict) -> None:
    """Apply native Windows blur (acrylic/mica) to the main window.

    Strategy (works around the Qt6 + QWebEngineView issues on Windows):
      * CSS backdrop-filter blur is unusable in QtWebEngine on Windows -- it
        flickers badly (Anki upstream issue #4470, closed not-planned), so the
        blur is applied natively to the top-level window via the DWM compositor
        using pywinstyles (acrylic by default; mica/aero selectable).
      * The Qt content view and the webviews are made translucent so the
        DWM-blurred desktop shows through.
      * The native HWND is only stable after Anki finishes its own .show(), so
        we retry on a QTimer.
      * Keeps the native titlebar (no FramelessWindowHint, no
        setWindowOpacity) -- DWM needs a normal, non-zero-opacity window.
    """
    try:
        import pywinstyles
    except Exception:
        # Do NOT set WA_TranslucentBackground without the acrylic behind it:
        # that leaves an unreadable, hole-punched window. Fall back to fully
        # stock rendering and let the tripwire show a visible warning.
        ops["pywinstyles_import"] = "symbol_missing"
        ops["win_acrylic"] = (
            "failed: pywinstyles is missing - blur disabled; "
            "reinstall via the AnkiBlur launcher"
        )
        print("[AnkiBlur] pywinstyles is missing - blur disabled; "
              "reinstall via the AnkiBlur launcher")
        return
    ops["pywinstyles_import"] = "ok"

    try:
        _set_translucent()
        if hasattr(mw.form, "centralwidget"):
            mw.form.centralwidget.setAutoFillBackground(False)
    except Exception as e:
        traceback.print_exc()
        ops["win_acrylic"] = f"failed: {e}"
        return

    ops["win_acrylic"] = "failed: not applied yet"
    state = {"tries": 0}

    def configure_blur() -> None:
        """Env-var-controlled tuning of the Windows native blur.

        Env vars (all optional, read at startup):

            ANKIBLUR_BACKDROP   str   acrylic (default) | mica | aero |
                                      transparent | auto. Selects the DWM
                                      material applied via pywinstyles.
            ANKIBLUR_DARK       1/0   Force the immersive dark titlebar on/off.
                                      When unset, follows Anki's night mode.
            ANKIBLUR_TINT       hex   #RRGGBB or #RRGGBBAA title-bar tint, best
                                      effort via pywinstyles.change_header_color.
        """
        dark_env = os.environ.get("ANKIBLUR_DARK")
        if dark_env is not None:
            dark = dark_env.strip().lower() in ("1", "true", "yes", "on")
        else:
            dark = _is_dark_theme()
        try:
            pywinstyles.apply_style(mw, "dark" if dark else "light")
            print(f"[AnkiBlur] titlebar {'dark' if dark else 'light'}")
        except Exception as e:
            print(f"[AnkiBlur] titlebar theme failed: {e}")
        if (v := os.environ.get("ANKIBLUR_TINT")) is not None:
            try:
                pywinstyles.change_header_color(mw, v)
                print(f"[AnkiBlur] change_header_color({v})")
            except Exception as e:
                print(f"[AnkiBlur] change_header_color failed: {e}")

    def attempt() -> None:
        try:
            hwnd = int(mw.winId())
            if not hwnd:
                raise RuntimeError("winId() not ready (0)")
            backdrop = os.environ.get(
                "ANKIBLUR_BACKDROP", "acrylic"
            ).strip().lower()
            style_map = {
                "acrylic": "acrylic",
                "mica": "mica",
                "aero": "aero",
                "transparent": "transparent",
                "auto": "acrylic",
            }
            style = style_map.get(backdrop, "acrylic")
            # Titlebar theme / tint first, then the backdrop material last so
            # the immersive-dark-mode call cannot clobber the blur.
            configure_blur()
            pywinstyles.apply_style(mw, style)
            ops["win_acrylic"] = "ok"
            print(
                f"[AnkiBlur] native Windows blur applied "
                f"({backdrop} -> {style})"
            )
            return
        except Exception as e:
            print(f"[AnkiBlur] blur apply failed: {e}")
            traceback.print_exc()
        state["tries"] += 1
        if state["tries"] < 15:
            QTimer.singleShot(100, attempt)
        else:
            # Give up cleanly: a translucent window without acrylic behind it
            # is a see-through hole, so restore an opaque window.
            print("[AnkiBlur] giving up after 15 retries")
            ops["win_acrylic"] = "failed: gave up after 15 retries"
            try:
                _set_translucent(clear=True)
                mw.update()
            except Exception:
                traceback.print_exc()

    # 150ms lets Anki finish its own .show() before we touch the HWND.
    QTimer.singleShot(150, attempt)


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------

def _apply_macos(ops: dict) -> None:
    """Apply macOS Liquid Glass to the main window.

    Strategy (works around the Qt6 + QWebEngineView translucent compositor
    bug on macOS):
      * pyqt-liquidglass injects an NSGlassEffectView (macOS 26+) or an
        NSVisualEffectView fallback as a sibling BEHIND the Qt root view
        in the NSThemeFrame. This avoids "Compositor returned null
        texture" that plagues every approach that goes through Qt's
        own translucent compositing path on QWebEngineView children.
      * On macOS 26+, additional NSGlassEffectView properties (style,
        scrim, tint, appearance, etc.) are controllable via env vars
        listed in configure_glass below.
    """
    try:
        import pyqt_liquidglass
    except Exception:
        ops["liquidglass_import"] = "symbol_missing"
        ops["mac_glass"] = (
            "failed: pyqt-liquidglass is missing - glass effect disabled; "
            "reinstall via the AnkiBlur launcher"
        )
        print("[AnkiBlur] pyqt-liquidglass is missing - glass effect disabled; "
              "reinstall via the AnkiBlur launcher")
        return
    ops["liquidglass_import"] = "ok"

    try:
        # The Qt content view must be translucent so the NSVisualEffectView /
        # NSGlassEffectView under it (in the NSThemeFrame) shows through. The
        # lib also sets this internally inside prepare_window_for_glass; we
        # set it early as defense in depth.
        _set_translucent()
        if hasattr(mw.form, "centralwidget"):
            mw.form.centralwidget.setAutoFillBackground(False)
    except Exception as e:
        traceback.print_exc()
        ops["mac_glass"] = f"failed: {e}"
        return

    ops["mac_glass"] = "failed: not applied yet"
    state = {"tries": 0}

    def configure_glass() -> None:
        """Env-var-controlled tuning of the NSGlassEffectView.

        Env vars (all optional, all live across restarts of Anki):

            ANKIBLUR_STYLE        int   0=Regular 1=Clear 2=Frosted 3=Chromatic
                                        (macOS 26+ NSGlassEffectView)
            ANKIBLUR_SUBVARIANT   int   private subvariant fine-tune
            ANKIBLUR_SCRIM        int   0=Off 1=Subdued 2=Normal
            ANKIBLUR_LENSING      1/0   content-lensing effect
            ANKIBLUR_TINT         hex   tint color, e.g. #80808026 (gray @ 15%
                                        alpha), accepts #RRGGBB or #RRGGBBAA
            ANKIBLUR_APPEARANCE   str   NSAppearanceNameAqua to force light
                                        glass even when the system is in dark
                                        mode (mitigates Apple's dark-mode
                                        saturation boost which is otherwise
                                        unreachable on NSGlassEffectView)
        """
        try:
            gv = mw._glass_view
            if (v := os.environ.get("ANKIBLUR_STYLE")) is not None:
                try:
                    gv.setStyle_(int(v))
                    print(f"[AnkiBlur] setStyle_({v})")
                except Exception as e:
                    print(f"[AnkiBlur] setStyle_ failed: {e}")
            if (v := os.environ.get("ANKIBLUR_SUBVARIANT")) is not None:
                try:
                    gv.set_subvariant_(int(v))
                    print(f"[AnkiBlur] set_subvariant_({v})")
                except Exception as e:
                    print(f"[AnkiBlur] set_subvariant_ failed: {e}")
            if (v := os.environ.get("ANKIBLUR_SCRIM")) is not None:
                try:
                    gv.set_scrimState_(int(v))
                    print(f"[AnkiBlur] set_scrimState_({v})")
                except Exception as e:
                    print(f"[AnkiBlur] set_scrimState_ failed: {e}")
            if (v := os.environ.get("ANKIBLUR_LENSING")) is not None:
                try:
                    gv.set_contentLensing_(bool(int(v)))
                    print(f"[AnkiBlur] set_contentLensing_({bool(int(v))})")
                except Exception as e:
                    print(f"[AnkiBlur] set_contentLensing_ failed: {e}")
            if (v := os.environ.get("ANKIBLUR_APPEARANCE")) is not None:
                try:
                    from AppKit import NSAppearance
                    na = NSAppearance.appearanceNamed_(v)
                    if na is not None:
                        gv.setAppearance_(na)
                        print(f"[AnkiBlur] setAppearance_({v})")
                except Exception as e:
                    print(f"[AnkiBlur] setAppearance_ failed: {e}")
            if (v := os.environ.get("ANKIBLUR_TINT")) is not None:
                try:
                    from AppKit import NSColor
                    h = v.lstrip("#")
                    if len(h) == 6:
                        h += "ff"
                    r, g, b, a = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4, 6))
                    gv.setTintColor_(
                        NSColor.colorWithRed_green_blue_alpha_(r, g, b, a)
                    )
                    print(f"[AnkiBlur] setTintColor_({v})")
                except Exception as e:
                    print(f"[AnkiBlur] setTintColor_ failed: {e}")
        except Exception as e:
            print(f"[AnkiBlur] glass configure failed: {e}")
            traceback.print_exc()

    def attempt() -> None:
        try:
            # Use the WindowBackground material for the NSVisualEffectView
            # fallback (older macOS). On macOS 26+ NSGlassEffectView is used
            # and material is ignored; tune via setStyle_ env var instead.
            try:
                from pyqt_liquidglass import GlassMaterial, GlassOptions
                opts = GlassOptions(material=GlassMaterial.WINDOW_BACKGROUND)
            except Exception:
                opts = None
            effect_id = pyqt_liquidglass.apply_glass_to_window(mw, opts)
            if effect_id is not None:
                ops["mac_glass"] = "ok"
                print(f"[AnkiBlur] liquid glass applied (id={effect_id})")
                configure_glass()
                return
            else:
                print("[AnkiBlur] glass apply returned None")
        except Exception as e:
            print(f"[AnkiBlur] glass apply failed: {e}")
            traceback.print_exc()
        state["tries"] += 1
        if state["tries"] < 15:
            QTimer.singleShot(100, attempt)
        else:
            # Give up cleanly: a translucent window without the effect view
            # behind it renders black, so restore an opaque window.
            print("[AnkiBlur] giving up after 15 retries")
            ops["mac_glass"] = "failed: gave up after 15 retries"
            try:
                _set_translucent(clear=True)
                mw.update()
            except Exception:
                traceback.print_exc()

    # 150ms lets Anki finish its own .show() before we touch the NSWindow.
    QTimer.singleShot(150, attempt)
