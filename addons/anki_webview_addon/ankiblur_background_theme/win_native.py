# AnkiBlur Windows-native blur + zero-strip native frame (add-on port).
#
# Faithful transplant of the verified-working Windows implementation that was
# developed inline in aqt/main.py on a live Windows machine (July 2026, Anki
# 25.09.4, Python 3.13.5, Qt/PyQt 6.9.1, Windows 11 23H2 build 22631) and
# handed off in docs/WINDOWS_IMPLEMENTATION.md. Every name keeps its
# `_ankiblur_` / `_AnkiBlur` prefix from the handoff so a future rebase can
# diff this module against the handoff directly.
#
# READ docs/WINDOWS_IMPLEMENTATION.md ("Verified findings") BEFORE CHANGING
# ANYTHING HERE -- each finding cost hours of experimentation and several are
# deeply counter-intuitive.
#
# Backend note (finding 1): the legacy accent-policy path
# (SetWindowCompositionAttribute WCA_ACCENT_POLICY, acrylic state 4) is the
# DEFAULT on every build incl. Win11: it is the only blur API that composites
# behind a layered (WS_EX_LAYERED) surface, and Qt6 makes every
# WA_TranslucentBackground top-level a layered window. The documented Win11
# DWM systembackdrop API (DwmSetWindowAttribute attr 38) returns hr=0 but
# draws NOTHING behind layered windows (verified with a screen-sampling probe
# on 22631) -- it must never be the default.
#
# Add-on context: aqt runs setupAddons() after the QMainWindow and the three
# main webviews exist but BEFORE the first show(), so install_window_chrome()
# (called at add-on import time from window_effects._apply_windows) flips the
# frameless flag and translucency attributes pre-show, exactly like the
# handoff's inline AnkiQt.__init__ hook. The HWND-derived setup (styles,
# accent, border, native filter) is (re)applied by the retry loop in
# window_effects, for which _ankiblur_apply_backdrop and
# _ankiblur_install_native_frame are idempotent.

import os
import sys
import traceback
import sys as _ankiblur_sys

from aqt.qt import *  # noqa: F401,F403

_HAS_WIN_BLUR = _ankiblur_sys.platform == "win32"


def _ankiblur_is_dark_theme():
    """Best-effort detection of Anki's current night mode, for the immersive
    dark titlebar. Falls back to False (light) if anything is unavailable."""
    try:
        from aqt import mw
        if mw is not None and getattr(mw, "pm", None) is not None:
            return bool(mw.pm.night_mode())
    except Exception:
        pass
    try:
        from aqt.theme import theme_manager
        return bool(theme_manager.night_mode)
    except Exception:
        return False


# DWM constants (dwmapi.h)
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWA_CAPTION_COLOR = 35
_DWMWA_SYSTEMBACKDROP_TYPE = 38
# DWM_WINDOW_CORNER_PREFERENCE values
_DWMWCP = {"default": 0, "square": 1, "none": 1, "round": 2, "small": 3}
# DWM_SYSTEMBACKDROP_TYPE enum values
_DWMSBT = {
    "auto": 0,        # DWMSBT_AUTO          -- DWM decides
    "none": 1,        # DWMSBT_NONE          -- no backdrop
    "mica": 2,        # DWMSBT_MAINWINDOW    -- Mica (static, wallpaper-tinted)
    "acrylic": 3,     # DWMSBT_TRANSIENTWINDOW -- Acrylic (real-time blur)
    "tabbed": 4,      # DWMSBT_TABBEDWINDOW  -- Mica Alt
}
# Friendly aliases for ANKIBLUR_BACKDROP
_DWMSBT_ALIASES = {
    "transient": 3, "transparent": 3, "blur": 3,
    "mainwindow": 2,
    "mica-alt": 4, "mica_alt": 4, "micaalt": 4,
    "disable": 1,
}

# --- AnkiBlur native frame (qframelesswindow recipe, ctypes port) -----------
# Re-add the native Win32 frame to the Qt-frameless window so Windows handles
# the drop shadow / Aero Snap / native edge-resize / min-max animations, while
# Qt still believes it is frameless (which is what gives us the layered alpha
# surface the acrylic needs). Caption is hidden via the WM_NCCALCSIZE handler.
_GWL_STYLE = -16
_WS_CAPTION = 0x00C00000
_WS_THICKFRAME = 0x00040000
_WS_MINIMIZEBOX = 0x00020000
_WS_MAXIMIZEBOX = 0x00010000
_WS_SYSMENU = 0x00080000
_WM_STYLECHANGING = 0x007C
_WM_STYLECHANGED = 0x007D
_WM_NCCALCSIZE = 0x0083
_WM_NCHITTEST = 0x0084
_WM_NCPAINT = 0x0085
_WM_NCACTIVATE = 0x0086
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17
_HTCLIENT = 1
_HTCAPTION = 2
_HTMINBUTTON = 8
_HTMAXBUTTON = 9
_HTCLOSE = 20
_DWMWA_CAPTION_BUTTON_BOUNDS = 29
_WVR_REDRAW = 0x0400
_SM_CXSIZEFRAME = 32
_SM_CYSIZEFRAME = 33
_SM_CXPADDEDBORDER = 92
_SW_SHOWMAXIMIZED = 3
_ABM_GETSTATE = 0x4
_ABM_GETTASKBARPOS = 0x5
_ABS_AUTOHIDE = 0x1
_ABE_LEFT = 0
_ABE_TOP = 1
_ABE_RIGHT = 2
_ABE_BOTTOM = 3
_WM_NCMOUSEMOVE = 0x00A0
_WM_NCLBUTTONDOWN = 0x00A1
_WM_NCLBUTTONUP = 0x00A2
_WM_NCLBUTTONDBLCLK = 0x00A3
_WM_NCRBUTTONUP = 0x00A5
_WM_NCMOUSELEAVE = 0x02A2
# debug: append every NC mouse message to this file (empty/unset = off)
_ANKIBLUR_NC_LOG = os.environ.get("ANKIBLUR_NC_LOG", "")
_WM_ENTERSIZEMOVE = 0x0231
_WM_EXITSIZEMOVE = 0x0232
_WM_SYSCOMMAND = 0x0112
_SC_SIZE = 0xF000
_SC_MOVE = 0xF010
_SC_MINIMIZE = 0xF020
_SC_MAXIMIZE = 0xF030
_SC_RESTORE = 0xF120
_SC_CLOSE = 0xF060
_TPM_RIGHTBUTTON = 0x0002
_TPM_RETURNCMD = 0x0100
_MF_ENABLED = 0x0000
_MF_GRAYED = 0x0003


def _ankiblur_win32():
    """Lazily build (once) a cached table of ctypes handles with 64-bit-safe
    argtypes/restypes for the Win32 calls the native frame needs.

    Finding 8 is law: every `_ankiblur_*` helper must use this cached dict
    (`w["ctypes"]`, `w["u"]`, `w["wintypes"]`, `w["WINDOWPLACEMENT"]`...) --
    a bare `ctypes` NameError here crashes the setup retry loop mid-way,
    leaving the window half-configured. GetWindowPlacement.argtypes is bound
    to THIS WINDOWPLACEMENT; defining a second struct raises a ctypes
    TypeError."""
    cache = getattr(_ankiblur_win32, "_cache", None)
    if cache is not None:
        return cache
    if not _HAS_WIN_BLUR:
        return None
    import ctypes
    from ctypes import wintypes

    u = ctypes.windll.user32

    class APPBARDATA(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
            ("uCallbackMessage", wintypes.UINT), ("uEdge", wintypes.UINT),
            ("rc", wintypes.RECT), ("lParam", wintypes.LPARAM),
        ]

    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT), ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT), ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT), ("rcNormalPosition", wintypes.RECT),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD),
        ]

    getlp = getattr(u, "GetWindowLongPtrW", None) or u.GetWindowLongW
    setlp = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
    getlp.restype = ctypes.c_longlong
    getlp.argtypes = [wintypes.HWND, ctypes.c_int]
    setlp.restype = ctypes.c_longlong
    setlp.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]
    u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.GetWindowRect.restype = wintypes.BOOL
    u.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWPLACEMENT)]
    u.GetWindowPlacement.restype = wintypes.BOOL
    u.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    u.MonitorFromWindow.restype = ctypes.c_void_p
    u.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFO)]
    u.GetMonitorInfoW.restype = wintypes.BOOL
    u.PostMessageW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    ]
    u.PostMessageW.restype = wintypes.BOOL
    u.GetSystemMenu.argtypes = [wintypes.HWND, wintypes.BOOL]
    u.GetSystemMenu.restype = ctypes.c_void_p
    u.TrackPopupMenu.argtypes = [
        ctypes.c_void_p, wintypes.UINT, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, wintypes.HWND, ctypes.c_void_p
    ]
    u.TrackPopupMenu.restype = ctypes.c_int
    u.EnableMenuItem.argtypes = [ctypes.c_void_p, wintypes.UINT, wintypes.UINT]
    u.EnableMenuItem.restype = wintypes.BOOL
    u.DefWindowProcW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    ]
    u.DefWindowProcW.restype = ctypes.c_longlong

    gsmfd = getattr(u, "GetSystemMetricsForDpi", None)
    if gsmfd is not None:
        gsmfd.argtypes = [ctypes.c_int, wintypes.UINT]
        gsmfd.restype = ctypes.c_int
    gdfw = getattr(u, "GetDpiForWindow", None)
    if gdfw is not None:
        gdfw.argtypes = [wintypes.HWND]
        gdfw.restype = wintypes.UINT

    shell32 = ctypes.windll.shell32
    shell32.SHAppBarMessage.argtypes = [wintypes.DWORD, ctypes.POINTER(APPBARDATA)]
    shell32.SHAppBarMessage.restype = ctypes.c_void_p

    dwm = ctypes.windll.dwmapi
    dwm.DwmGetWindowAttribute.argtypes = [
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
    ]
    dwm.DwmGetWindowAttribute.restype = ctypes.c_long

    cache = {
        "ctypes": ctypes, "wintypes": wintypes, "u": u, "shell32": shell32,
        "dwm": dwm,
        "getlp": getlp, "setlp": setlp, "gsmfd": gsmfd, "gdfw": gdfw,
        "APPBARDATA": APPBARDATA, "WINDOWPLACEMENT": WINDOWPLACEMENT,
        "MONITORINFO": MONITORINFO,
    }
    _ankiblur_win32._cache = cache
    return cache


def _ankiblur_dpi_for(hwnd):
    w = _ankiblur_win32()
    if w and w["gdfw"] is not None:
        try:
            d = w["gdfw"](w["wintypes"].HWND(hwnd))
            if d:
                return int(d)
        except Exception:
            pass
    return 96


def _ankiblur_is_maximized(hwnd):
    w = _ankiblur_win32()
    if not w:
        return False
    try:
        wp = w["WINDOWPLACEMENT"]()
        wp.length = w["ctypes"].sizeof(wp)
        if w["u"].GetWindowPlacement(w["wintypes"].HWND(hwnd), w["ctypes"].byref(wp)):
            return wp.showCmd == _SW_SHOWMAXIMIZED
    except Exception:
        pass
    return False


def _ankiblur_rect_is_maximized(hwnd, rect):
    """True when the proposed WM_NCCALCSIZE rect reaches/overflows the monitor
    work area on all edges -- i.e. the window is genuinely maximized for THIS
    layout pass. Uses the proposed rect, which (unlike WINDOWPLACEMENT.showCmd)
    is never stale during a maximize<->restore transition, so the maximized
    resize-border inset is never wrongly left on the restored window (the white
    inner-border bug).

    NOTE: currently unreferenced -- its logic is inlined in
    _AnkiBlurNativeFilter._on_nccalcsize. Kept deliberately for parity with
    the handoff (it is on WINDOWS_IMPLEMENTATION.md's transplant list)."""
    w = _ankiblur_win32()
    if not w:
        return False
    try:
        ct, wt, u = w["ctypes"], w["wintypes"], w["u"]
        mon = u.MonitorFromWindow(wt.HWND(hwnd), 2)  # MONITOR_DEFAULTTONEAREST
        mi = w["MONITORINFO"]()
        mi.cbSize = ct.sizeof(mi)
        if not u.GetMonitorInfoW(mon, ct.byref(mi)):
            return False
        wk = mi.rcWork
        return (rect.left <= wk.left and rect.top <= wk.top
                and rect.right >= wk.right and rect.bottom >= wk.bottom)
    except Exception:
        return False


def _ankiblur_is_fullscreen(hwnd):
    w = _ankiblur_win32()
    if not w:
        return False
    try:
        ct, wt, u = w["ctypes"], w["wintypes"], w["u"]
        rc = wt.RECT()
        if not u.GetWindowRect(wt.HWND(hwnd), ct.byref(rc)):
            return False
        mon = u.MonitorFromWindow(wt.HWND(hwnd), 2)  # MONITOR_DEFAULTTONEAREST
        mi = w["MONITORINFO"]()
        mi.cbSize = ct.sizeof(mi)
        if not u.GetMonitorInfoW(mon, ct.byref(mi)):
            return False
        m = mi.rcMonitor
        return (rc.left == m.left and rc.top == m.top
                and rc.right == m.right and rc.bottom == m.bottom)
    except Exception:
        return False


def _ankiblur_resize_border(hwnd, horizontal, dpr=1.0):
    w = _ankiblur_win32()
    if w and w["gsmfd"] is not None:
        try:
            dpi = _ankiblur_dpi_for(hwnd)
            idx = _SM_CXSIZEFRAME if horizontal else _SM_CYSIZEFRAME
            total = w["gsmfd"](idx, dpi) + w["gsmfd"](_SM_CXPADDEDBORDER, dpi)
            if total > 0:
                return total
        except Exception:
            pass
    return round(8 * dpr)


def _ankiblur_taskbar_autohide_edge(hwnd):
    w = _ankiblur_win32()
    if not w:
        return None
    try:
        ct, shell32 = w["ctypes"], w["shell32"]
        abd = w["APPBARDATA"]()
        abd.cbSize = ct.sizeof(abd)
        state = shell32.SHAppBarMessage(_ABM_GETSTATE, ct.byref(abd))
        if not ((int(state) if state else 0) & _ABS_AUTOHIDE):
            return None
        abd2 = w["APPBARDATA"]()
        abd2.cbSize = ct.sizeof(abd2)
        if not shell32.SHAppBarMessage(_ABM_GETTASKBARPOS, ct.byref(abd2)):
            return _ABE_BOTTOM
        rc = abd2.rc
        if rc.right - rc.left > rc.bottom - rc.top:
            return _ABE_TOP if rc.top <= 0 else _ABE_BOTTOM
        return _ABE_LEFT if rc.left <= 0 else _ABE_RIGHT
    except Exception:
        return None


# --- AnkiBlur multi-version blur backends -----------------------------------
# Windows changed its compositor blur API three times, so the right call
# depends on the build we are running on:
#   accent-acrylic  SetWindowCompositionAttribute(WCA_ACCENT_POLICY) with
#                   ACCENT_ENABLE_ACRYLICBLURBEHIND=4. Win10 1803+ (build
#                   17134) AND Win11 (verified working on 22631). This is the
#                   DEFAULT everywhere: it is the only blur API that composites
#                   behind a layered (WS_EX_LAYERED) surface, and Qt6 makes
#                   every WA_TranslucentBackground top-level a layered window.
#                   Known quirk: laggy window drag on Win10 -- worked around by
#                   switching to plain blur during the native move/size loop
#                   (WM_ENTER/EXITSIZEMOVE).
#   accent-blur     Same accent API with ACCENT_ENABLE_BLURBEHIND=3 -- the old
#                   "aero" gaussian blur. Works from early Win10 builds and is
#                   the terminal fallback.
#   dwm             DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE=38), the
#                   documented Win11 22H2+ API (attribute exists since insider
#                   22523). NOT the default: DWM system backdrop materials do
#                   not render behind layered windows -- on a Qt translucent
#                   window the call "succeeds" (hr=0) but draws nothing, which
#                   Anki's webviews then composite as black (verified with a
#                   screen-sampling probe on 22631). Only used when mica is
#                   explicitly requested, or forced via ANKIBLUR_BACKEND=dwm.
#   mica1029        DwmSetWindowAttribute(1029) -- the undocumented Mica bool
#                   of Win11 21H2 (builds 22000-22522), removed in 22H2+
#                   (silent no-op there). Only tried for mica requests on
#                   21H2 builds.
_WCA_ACCENT_POLICY = 19
_ACCENT_DISABLED = 0
_ACCENT_ENABLE_BLURBEHIND = 3
_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
_DWMWA_MICA_EFFECT_LEGACY = 1029
_ANKIBLUR_BACKENDS = ("dwm", "mica1029", "accent-acrylic", "accent-blur", "none")


def _ankiblur_win_build():
    try:
        return int(_ankiblur_sys.getwindowsversion().build)
    except Exception:
        return 0


def _ankiblur_backend_plan():
    """Ordered list of blur backends to try for this Windows build (first that
    applies cleanly wins). ANKIBLUR_BACKEND forces a single backend:
    dwm | mica1029 | accent-acrylic | accent-blur | none."""
    import os

    force = os.environ.get("ANKIBLUR_BACKEND", "").strip().lower()
    aliases = {
        "dwm38": "dwm", "systembackdrop": "dwm", "backdrop": "dwm",
        "acrylic-accent": "accent-acrylic", "accent4": "accent-acrylic",
        "accent": "accent-acrylic",
        "blur-accent": "accent-blur", "accent3": "accent-blur",
        "aero": "accent-blur",
        "mica-legacy": "mica1029", "1029": "mica1029",
        "off": "none", "disable": "none",
    }
    force = aliases.get(force, force)
    if force in _ANKIBLUR_BACKENDS:
        return [force]

    backdrop = os.environ.get("ANKIBLUR_BACKDROP", "acrylic").strip().lower()
    wants_mica = backdrop in (
        "mica", "tabbed", "mainwindow", "mica-alt", "mica_alt", "micaalt")
    build = _ankiblur_win_build()
    plan = []
    if backdrop in ("none", "disable", "off"):
        return ["none"]
    if wants_mica:
        # Mica is a DWM-only material with no accent equivalent; best effort
        # (see the backend notes above: it may render as plain transparency on
        # a layered Qt window), then fall through to the accent chain.
        if build >= 22523:
            plan.append("dwm")
        elif build >= 22000:
            plan.append("mica1029")
    if backdrop == "aero":
        # Explicit request for the old gaussian aero blur.
        plan.append("accent-blur")
        return plan
    if build >= 17134:
        plan.append("accent-acrylic")
    plan.append("accent-blur")
    return plan


def _ankiblur_accent_gradient(dark):
    """ABGR gradient color for the accent backends (they blend this tint over
    the blur; alpha 0 disables the blur entirely, so it is clamped to >= 1).

    ANKIBLUR_ACCENT_TINT   #RRGGBB tint (default follows the Anki theme).
    ANKIBLUR_ACCENT_ALPHA  0-255 tint opacity (default 153)."""
    import os

    r, g, b = (16, 16, 16) if dark else (249, 249, 249)
    tint = os.environ.get("ANKIBLUR_ACCENT_TINT", "").lstrip("#")
    if len(tint) >= 6:
        try:
            r, g, b = int(tint[0:2], 16), int(tint[2:4], 16), int(tint[4:6], 16)
        except Exception:
            pass
    try:
        a = int(os.environ.get("ANKIBLUR_ACCENT_ALPHA", "153"))
    except Exception:
        a = 153
    a = min(255, max(1, a))
    return (a << 24) | (b << 16) | (g << 8) | r


def _ankiblur_apply_accent(hwnd, state, gradient):
    """Apply a WCA_ACCENT_POLICY accent state (blur/acrylic/off) to the HWND
    via the undocumented-but-stable user32 SetWindowCompositionAttribute."""
    import ctypes
    from ctypes import wintypes

    class ACCENT_POLICY(ctypes.Structure):
        _fields_ = [
            ("AccentState", wintypes.DWORD),
            ("AccentFlags", wintypes.DWORD),
            ("GradientColor", wintypes.DWORD),
            ("AnimationId", wintypes.DWORD),
        ]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        _fields_ = [
            ("Attribute", wintypes.DWORD),
            ("Data", ctypes.c_void_p),
            ("SizeOfData", ctypes.c_ulong),
        ]

    user32 = ctypes.windll.user32
    swca = getattr(user32, "SetWindowCompositionAttribute", None)
    if swca is None:
        raise RuntimeError("SetWindowCompositionAttribute unavailable")
    swca.argtypes = [wintypes.HWND, ctypes.c_void_p]
    swca.restype = wintypes.BOOL

    accent = ACCENT_POLICY()
    accent.AccentState = state
    accent.AccentFlags = 0
    accent.GradientColor = gradient & 0xFFFFFFFF
    accent.AnimationId = 0
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = _WCA_ACCENT_POLICY
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
    data.SizeOfData = ctypes.sizeof(accent)
    if not swca(wintypes.HWND(hwnd), ctypes.byref(data)):
        raise RuntimeError(
            f"SetWindowCompositionAttribute(state={state}) returned FALSE")


def _ankiblur_apply_backdrop(window):
    """Apply the best native Windows blur available on this build (AnkiBlur).

    Tries the backends from _ankiblur_backend_plan() in order and stops at the
    first that applies cleanly -- accent acrylic on Win10 1803+ AND Win11 (the
    only blur that composites behind Qt's layered windows), aero blur on older
    builds, DWM mica only on explicit request.

    Env vars (all optional, read at startup; the add-on config's "windows"
    section seeds any that are unset -- see seed_env_from_config):

        ANKIBLUR_BACKEND    Force a backend: dwm | mica1029 | accent-acrylic |
                            accent-blur | none (skips auto-detection).
        ANKIBLUR_BACKDROP   acrylic (default) = real-time accent blur;
                            aero = old gaussian blur; mica/tabbed = DWM Mica,
                            best effort (may render as plain transparency on a
                            Qt window); none = no blur.
        ANKIBLUR_DARK       1/0  Force the immersive dark titlebar on/off.
                            When unset, follows Anki's night mode.
        ANKIBLUR_TINT       #RRGGBB title-bar caption color (DWMWA_CAPTION_COLOR).
        ANKIBLUR_ACCENT_TINT / ANKIBLUR_ACCENT_ALPHA
                            Tint of the accent backends (see above).
        ANKIBLUR_DRAG_FIX   1 (default) swaps accent acrylic to plain blur
                            while the window is being moved/resized (Win10
                            acrylic drag lag); 0 disables the swap.
    """
    import os
    import ctypes
    from ctypes import wintypes

    backdrop = os.environ.get("ANKIBLUR_BACKDROP", "acrylic").strip().lower()
    sbt = _DWMSBT.get(backdrop, _DWMSBT_ALIASES.get(backdrop, 3))

    dark_env = os.environ.get("ANKIBLUR_DARK")
    if dark_env is not None:
        dark = dark_env.strip().lower() in ("1", "true", "yes", "on")
    else:
        dark = _ankiblur_is_dark_theme()

    hwnd = int(window.winId())
    if not hwnd:
        raise RuntimeError("winId() not ready (0)")

    dwm = ctypes.windll.dwmapi
    # Type the args so the 64-bit HWND isn't silently truncated to 32 bits.
    dwm.DwmSetWindowAttribute.argtypes = [
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
    ]
    dwm.DwmSetWindowAttribute.restype = ctypes.c_long

    class MARGINS(ctypes.Structure):
        _fields_ = [
            ("cxLeftWidth", ctypes.c_int),
            ("cxRightWidth", ctypes.c_int),
            ("cyTopHeight", ctypes.c_int),
            ("cyBottomHeight", ctypes.c_int),
        ]

    dwm.DwmExtendFrameIntoClientArea.argtypes = [
        wintypes.HWND, ctypes.POINTER(MARGINS)
    ]
    dwm.DwmExtendFrameIntoClientArea.restype = ctypes.c_long

    hwnd_c = wintypes.HWND(hwnd)

    def _set_attr(attr, value):
        v = ctypes.c_int(value)
        return dwm.DwmSetWindowAttribute(
            hwnd_c, attr, ctypes.byref(v), ctypes.sizeof(v)
        )

    # (1) Immersive dark/light titlebar. Attr 20 is 1903+; pre-1903 Win10
    #     used 19 for the same bool.
    if _set_attr(_DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0) != 0:
        _set_attr(_DWMWA_USE_IMMERSIVE_DARK_MODE - 1, 1 if dark else 0)

    # (2) No DwmExtendFrameIntoClientArea at all: the accent backends need no
    #     frame extension, DWM drop shadows don't manifest on this layered
    #     window anyway, and the extension paints a faint 1px line at the top.
    #     (MARGINS kept defined for the dwm backend's potential future use.)

    # (3) The actual blur material -- first backend in the plan that applies
    #     cleanly wins; the rest of the chain is the fallback for older builds.
    gradient = _ankiblur_accent_gradient(dark)
    plan = _ankiblur_backend_plan()
    applied = None
    for backend in plan:
        try:
            if backend == "none":
                applied = backend
                break
            if backend == "dwm":
                hr = _set_attr(_DWMWA_SYSTEMBACKDROP_TYPE, sbt)
                if hr != 0:
                    raise RuntimeError(
                        f"DwmSetWindowAttribute(SYSTEMBACKDROP_TYPE)"
                        f" hr=0x{hr & 0xffffffff:08x}"
                    )
            elif backend == "mica1029":
                hr = _set_attr(_DWMWA_MICA_EFFECT_LEGACY, 1)
                if hr != 0:
                    raise RuntimeError(
                        f"DwmSetWindowAttribute(1029) hr=0x{hr & 0xffffffff:08x}"
                    )
            elif backend == "accent-acrylic":
                _ankiblur_apply_accent(
                    hwnd, _ACCENT_ENABLE_ACRYLICBLURBEHIND, gradient)
            elif backend == "accent-blur":
                _ankiblur_apply_accent(
                    hwnd, _ACCENT_ENABLE_BLURBEHIND, gradient)
            applied = backend
            break
        except Exception as e:
            print(f"[AnkiBlur] backend {backend} failed: {e}")
    if applied is None:
        raise RuntimeError(f"no blur backend applied (tried: {', '.join(plan)})")
    # Remembered for the WM_ENTER/EXITSIZEMOVE acrylic drag fix.
    window._ankiblur_backend = applied
    window._ankiblur_accent_tint = gradient

    # (4) Windows 11 rounded corners (ANKIBLUR_CORNERS: round|small|square).
    corners = os.environ.get("ANKIBLUR_CORNERS", "round").strip().lower()
    _set_attr(_DWMWA_WINDOW_CORNER_PREFERENCE, _DWMWCP.get(corners, 2))

    # (4b) Remove the Win11 window border -- the 1px grey/white hairline DWM
    #      draws across the top of the window (verified live: killing the
    #      border removes the line instantly). ANKIBLUR_BORDER: none (default)
    #      | default (keep system border) | #RRGGBB custom color.
    #      Attr 34 is Win11-only; the call fails harmlessly on Win10.
    border = os.environ.get("ANKIBLUR_BORDER", "none").strip().lower()
    _DWMWA_BORDER_COLOR = 34
    if border == "none":
        v = ctypes.c_uint(0xFFFFFFFE)  # DWMWA_COLOR_NONE
        dwm.DwmSetWindowAttribute(
            hwnd_c, _DWMWA_BORDER_COLOR, ctypes.byref(v), ctypes.sizeof(v))
    elif border.startswith("#"):
        try:
            h = border.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            _set_attr(_DWMWA_BORDER_COLOR, (b << 16) | (g << 8) | r)
        except Exception as e:
            print(f"[AnkiBlur] border color failed: {e}")

    # (5) Optional caption tint. DWM wants a COLORREF (0x00BBGGRR).
    tint = os.environ.get("ANKIBLUR_TINT")
    if tint:
        try:
            h = tint.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            _set_attr(_DWMWA_CAPTION_COLOR, (b << 16) | (g << 8) | r)
            print(f"[AnkiBlur] caption color #{h[:6]}")
        except Exception as e:
            print(f"[AnkiBlur] tint failed: {e}")

    # The core "opaque white until resized" cause: Windows paints the window
    # CLASS background brush (white) before Qt composites, and only freshly
    # invalidated (resized) regions escape it. Replace that brush with a NULL
    # brush so Windows stops drawing white behind the translucent window.
    # (Qt forum 69867: SetClassLongPtr(hwnd, GCLP_HBRBACKGROUND, NULL_BRUSH).)
    GCLP_HBRBACKGROUND = -10
    NULL_BRUSH = 5
    gdi32 = ctypes.windll.gdi32
    gdi32.GetStockObject.restype = ctypes.c_void_p
    gdi32.GetStockObject.argtypes = [ctypes.c_int]
    user32 = ctypes.windll.user32
    _set_class = getattr(user32, "SetClassLongPtrW", None) or user32.SetClassLongW
    _set_class.restype = ctypes.c_void_p
    _set_class.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    _set_class(hwnd_c, GCLP_HBRBACKGROUND, gdi32.GetStockObject(NULL_BRUSH))

    # Re-add the native frame + install the native event filter BEFORE the
    # FRAMECHANGED below, so the first WM_NCCALCSIZE (which strips the caption to
    # fill the client) is handled on this pass. No-op if ANKIBLUR_LEGACY_GRIPS=1.
    _ankiblur_install_native_frame(window)

    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020
    user32.SetWindowPos(
        hwnd_c, None, 0, 0, 0, 0,
        SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED,
    )
    RDW_INVALIDATE = 0x0001
    RDW_ERASE = 0x0004
    RDW_FRAME = 0x0400
    RDW_ALLCHILDREN = 0x0080
    RDW_UPDATENOW = 0x0100
    user32.RedrawWindow(
        hwnd_c, None, None,
        RDW_INVALIDATE | RDW_ERASE | RDW_FRAME | RDW_ALLCHILDREN | RDW_UPDATENOW,
    )
    window.update()

    name = next((k for k, v in _DWMSBT.items() if v == sbt), str(sbt))
    detail = (
        f"DWMSBT_{name.upper()}={sbt}" if applied == "dwm"
        else f"tint=0x{gradient:08x}" if applied.startswith("accent")
        else applied
    )
    print(
        f"[AnkiBlur] blur applied via backend '{applied}' "
        f"(build={_ankiblur_win_build()}, backdrop={backdrop}, {detail}, "
        f"dark={dark})"
    )


def _ankiblur_install_native_frame(window):
    """Re-add the native Win32 window styles and install the app-level native
    event filter that hands shadow / Aero Snap / resize / maximize animations to
    Windows. Idempotent (safe under the setup_blur retry loop). Disabled when
    ANKIBLUR_LEGACY_GRIPS=1 (keeps the old Qt resize grips as a fallback)."""
    import os

    if not _HAS_WIN_BLUR or os.environ.get("ANKIBLUR_LEGACY_GRIPS") == "1":
        return
    w = _ankiblur_win32()
    if not w:
        return
    hwnd = int(window.winId())
    if not hwnd:
        raise RuntimeError("winId() not ready for native frame")

    flt = getattr(window, "_ankiblur_native_filter", None)
    if flt is None:
        flt = _AnkiBlurNativeFilter(window)
        # Qt does NOT take ownership of native filters -> keep a strong ref.
        QApplication.instance().installNativeEventFilter(flt)
        window._ankiblur_native_filter = flt
    flt.set_hwnd(hwnd)

    # Alt+Space -> system menu near the window's top-left corner (the native
    # accelerator; DefWindowProc only provides it for WS_CAPTION windows).
    if getattr(window, "_ankiblur_sysmenu_shortcut", None) is None:
        def _alt_space():
            try:
                ct, wt, u = w["ctypes"], w["wintypes"], w["u"]
                rc = wt.RECT()
                u.GetWindowRect(wt.HWND(int(window.winId())), ct.byref(rc))
                window._ankiblur_native_filter._show_system_menu(
                    rc.left + 8, rc.top + 36)
            except Exception:
                pass

        window._ankiblur_sysmenu_shortcut = QShortcut(
            QKeySequence("Alt+Space"), window)
        qconnect(window._ankiblur_sysmenu_shortcut.activated, _alt_space)

    hc = w["wintypes"].HWND(hwnd)
    style = w["getlp"](hc, _GWL_STYLE)
    # ANKIBLUR_FRAME_MODE:
    #   thick (default)  re-add WS_THICKFRAME: native edge-resize + Aero Snap
    #                    (verified: snap does NOT work without it). The style
    #                    change is hidden from Qt by eating WM_STYLECHANGED in
    #                    the filter, and WM_NCCALCSIZE keeps client == window,
    #                    so there is NO visible non-client strip.
    #   none             no THICKFRAME: kills Aero Snap; kept as a debug mode.
    # We deliberately do NOT add WS_CAPTION -- on Win11 that makes DWM draw its
    # own (non-interactive, here) caption buttons duplicating our custom ones.
    mode = os.environ.get("ANKIBLUR_FRAME_MODE", "thick").strip().lower()
    if mode != "none":
        # MAXIMIZEBOX/MINIMIZEBOX/SYSMENU carry no visuals without WS_CAPTION,
        # but Windows gates behavior on them: the Win11 snap-layouts flyout is
        # only offered for windows with WS_MAXIMIZEBOX, and DefWindowProc only
        # honors SC_MAXIMIZE / caption dbl-click for maximizable windows.
        w["setlp"](hc, _GWL_STYLE,
                   style | _WS_THICKFRAME | _WS_MAXIMIZEBOX | _WS_MINIMIZEBOX
                   | _WS_SYSMENU)
    # CS_DBLCLKS on the window CLASS so a caption double-click is delivered as
    # WM_NCLBUTTONDBLCLK (dbl-click-to-maximize). Without it Windows only sends
    # two separate WM_NCLBUTTONDOWNs and the gesture never fires.
    ct = w["ctypes"]
    _GCL_STYLE = -26
    _CS_DBLCLKS = 0x0008
    getcl = getattr(w["u"], "GetClassLongPtrW", None) or w["u"].GetClassLongW
    setcl = getattr(w["u"], "SetClassLongPtrW", None) or w["u"].SetClassLongW
    getcl.restype = ct.c_longlong if hasattr(w["u"], "GetClassLongPtrW") else ct.c_ulong
    getcl.argtypes = [w["wintypes"].HWND, ct.c_int]
    setcl.restype = getcl.restype
    setcl.argtypes = [w["wintypes"].HWND, ct.c_int, getcl.restype]
    cstyle = getcl(hc, _GCL_STYLE)
    setcl(hc, _GCL_STYLE, cstyle | _CS_DBLCLKS)
    print(f"[AnkiBlur] native frame installed (mode={mode})")


def _ankiblur_frame_changed(window):
    """Force Windows to recompute the non-client frame (fires WM_NCCALCSIZE).
    Needed after a maximize<->restore so the restored window doesn't keep the
    maximized resize-border inset (which shows as white padding on all sides).

    NOTE: currently unreferenced -- superseded by the proposed-rect logic in
    _AnkiBlurNativeFilter._on_nccalcsize. Kept deliberately for parity with
    the handoff (it is on WINDOWS_IMPLEMENTATION.md's transplant list)."""
    if not _HAS_WIN_BLUR:
        return
    w = _ankiblur_win32()
    if not w:
        return
    try:
        hwnd = int(window.winId())
        if not hwnd:
            return
        # NOSIZE | NOMOVE | NOZORDER | FRAMECHANGED
        w["u"].SetWindowPos(
            w["wintypes"].HWND(hwnd), None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except Exception:
        pass


class _AnkiBlurTitleBar(QWidget):
    """Custom title bar (move + minimize/maximize/close) for the frameless
    AnkiBlur window. A faint fill keeps the whole strip hit-testable -- on a
    layered/translucent window, fully transparent pixels are click-through, so
    a transparent strip could not be dragged."""

    def __init__(self, win) -> None:
        super().__init__(win)
        self._win = win
        self.setObjectName("ankiblurTitleBar")
        self.setFixedHeight(32)
        self.setStyleSheet(
            "#ankiblurTitleBar{background-color: rgba(127,127,127,0.10);}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(0)
        title = QLabel("AnkiBlur", self)
        title.setStyleSheet(
            "color: palette(window-text); font-weight: 600; background: transparent;")
        lay.addWidget(title)
        lay.addStretch(1)
        # Custom caption buttons, drawn with the native Segoe caption glyphs so
        # they match Windows. (The DWM-managed caption buttons can't be wired up
        # on this custom-frame window -- DWMWA_CAPTION_BUTTON_BOUNDS returns
        # E_INVALIDARG -- so we draw + handle our own.)
        self._max_btn = None
        for kind in ("min", "max", "close"):
            lay.addWidget(self._button(kind))
        # keep the max/restore glyph right no matter HOW the state changed
        # (snap layouts, Win+arrows, dbl-click, taskbar, system menu)
        win.installEventFilter(self)

    def eventFilter(self, obj, evt):
        if obj is self._win:
            t = evt.type()
            if t == QEvent.Type.WindowStateChange:
                self.sync_max_glyph()
            elif t == QEvent.Type.Resize:
                # Add-on port of the handoff's inline AnkiQt.resizeEvent
                # override: relayout the legacy grips (if any) and debounce a
                # full repaint to wipe the white ghost slivers the webviews
                # leave on the layered surface during a live resize.
                _ankiblur_layout_grips(self._win)
                _ankiblur_schedule_repaint(self._win)
        return False

    def sync_max_glyph(self) -> None:
        if self._max_btn is not None:
            self._max_btn.setText(
                "" if self._win.isMaximized() else "")

    def set_max_nc_state(self, hover=None, pressed=None) -> None:
        """Hover/pressed visuals for the maximize button. Its mouse traffic
        arrives as NON-client messages (HTMAXBUTTON for snap layouts), which Qt
        never converts to widget events, so the native filter drives these
        dynamic properties instead of Qt's :hover."""
        b = self._max_btn
        if b is None:
            return
        changed = False
        if hover is not None and bool(b.property("ncHover")) != bool(hover):
            b.setProperty("ncHover", bool(hover))
            changed = True
        if pressed is not None and bool(b.property("ncPressed")) != bool(pressed):
            b.setProperty("ncPressed", bool(pressed))
            changed = True
        if changed:
            st = b.style()
            st.unpolish(b)
            st.polish(b)
            b.update()

    def _button(self, kind: str) -> QToolButton:
        # Segoe Fluent Icons: E921 minimize, E922 maximize, E923 restore,
        # E8BB close.
        glyphs = {"min": "", "max": "", "close": ""}
        b = QToolButton(self)
        b.setText(glyphs[kind])
        f = QFont()
        f.setFamilies(["Segoe Fluent Icons", "Segoe MDL2 Assets"])
        f.setPointSize(10)
        b.setFont(f)
        b.setFixedSize(46, 32)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close = kind == "close"
        hover = "rgba(232,17,35,0.90)" if close else "rgba(127,127,127,0.35)"
        b.setStyleSheet(
            "QToolButton{border:none;background:transparent;"
            "color:palette(window-text);}"
            "QToolButton:hover{background:%s;color:white;}"
            'QToolButton[ncHover="true"]{background:%s;color:white;}'
            'QToolButton[ncPressed="true"]{background:rgba(127,127,127,0.55);'
            "color:white;}" % (hover, hover))
        if kind == "min":
            b.clicked.connect(self._win.showMinimized)
        elif kind == "max":
            self._max_btn = b
            b.clicked.connect(self._toggle_max)
        else:
            b.clicked.connect(self._win.close)
        return b

    def _toggle_max(self) -> None:
        # Delegate to the native filter: Qt's showMaximized() no-ops on this
        # window (state desync from the eaten style messages); the filter
        # posts a native SC_MAXIMIZE/SC_RESTORE instead. The glyph syncs on
        # the resulting WindowStateChange (see eventFilter/sync_max_glyph).
        flt = getattr(self._win, "_ankiblur_native_filter", None)
        if flt is not None:
            flt._toggle_max()
            return
        if self._win.isMaximized():
            self._win.showNormal()
            if self._max_btn is not None:
                self._max_btn.setText("")
        else:
            self._win.showMaximized()
            if self._max_btn is not None:
                self._max_btn.setText("")

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            handle = self._win.windowHandle()
            if handle is not None:
                handle.startSystemMove()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._toggle_max()
            e.accept()
            return
        super().mouseDoubleClickEvent(e)


class _AnkiBlurGrip(QWidget):
    """Invisible-but-hit-testable edge/corner grip that triggers Qt's native
    startSystemResize. alpha=1 (out of 255) keeps it click-testable without
    being visible (a fully transparent grip would be click-through)."""

    def __init__(self, win, edges, cursor) -> None:
        super().__init__(win)
        self._win = win
        self._edges = edges
        self.setCursor(cursor)
        self.setStyleSheet("background-color: rgba(0,0,0,1);")

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            handle = self._win.windowHandle()
            if handle is not None:
                handle.startSystemResize(self._edges)
                e.accept()
                return
        super().mousePressEvent(e)


class _AnkiBlurNativeFilter(QAbstractNativeEventFilter):
    """App-level native event filter giving the frameless AnkiQt window native
    drop shadow / Aero Snap / min-max animations + native border resize. Scoped
    to a single HWND. We deliberately do NOT override QMainWindow.nativeEvent --
    that faults PyQt6 here; an app-level filter is stable."""

    def __init__(self, win) -> None:
        super().__init__()
        self._win = win
        self._hwnd = None
        self._max_pressed = False

    def set_hwnd(self, hwnd) -> None:
        self._hwnd = int(hwnd)

    def _is_fullscreen(self, hwnd) -> bool:
        try:
            if getattr(self._win, "fullscreen", False):
                return True
        except Exception:
            pass
        return _ankiblur_is_fullscreen(hwnd)

    def _dpr(self) -> float:
        try:
            h = self._win.windowHandle()
            if h is not None:
                return float(h.devicePixelRatio())
        except Exception:
            pass
        return 1.0

    def nativeEventFilter(self, eventType, message):
        try:
            if eventType != b"windows_generic_MSG" or self._hwnd is None:
                return (False, 0)
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
            if int(msg.hWnd or 0) != self._hwnd:
                return (False, 0)
            if msg.message in (_WM_STYLECHANGING, _WM_STYLECHANGED):
                # Hide our behind-Qt's-back WS_THICKFRAME from Qt: if Qt sees
                # the style change it recomputes its frame margins (~7px) and
                # lays the content out offset from the real client area (the
                # white/grey band bugs). Eating the notification keeps Qt's
                # cached frameless margins at 0, matching our full-window
                # client. (Verified: Qt 6.9 keeps margins 0, and Aero Snap +
                # the SC_SIZE loop still work.)
                return (True, 0)
            if msg.message == _WM_NCCALCSIZE:
                return self._on_nccalcsize(msg)
            if msg.message == _WM_NCHITTEST:
                return self._on_nchittest(msg)
            if msg.message == _WM_NCPAINT:
                # Suppress the LEGACY GDI non-client frame. DWM's modern frame
                # never applies to a layered (translucent) window, so
                # DefWindowProc falls back to painting the ancient white 3D
                # border into the reserved WS_THICKFRAME strips -- that is the
                # white line on the window edges, which live-resize then smears
                # into the nested 'ghost' outlines.
                return (True, 0)
            if msg.message == _WM_NCACTIVATE:
                # Same reason: on activation changes DefWindowProc repaints the
                # legacy NC frame. Returning TRUE keeps activation working
                # without the repaint.
                return (True, 1)
            # --- custom caption: snap layouts + native clicks --------------
            # Returning HTMAXBUTTON from WM_NCHITTEST makes Win11 show the
            # snap-layouts flyout over our custom maximize button, but it also
            # reroutes all mouse traffic there into these NON-client messages,
            # which Qt never converts to widget events -- so click + hover are
            # re-implemented here.
            if _ANKIBLUR_NC_LOG and msg.message in (
                    _WM_NCMOUSEMOVE, _WM_NCLBUTTONDOWN, _WM_NCLBUTTONUP,
                    _WM_NCLBUTTONDBLCLK, _WM_NCRBUTTONUP, _WM_NCMOUSELEAVE,
                    0x0201, 0x0202, 0x0203):  # + client L down/up/dblclk
                try:
                    with open(_ANKIBLUR_NC_LOG, "a") as f:
                        f.write(f"msg=0x{msg.message:04X} wp={int(msg.wParam)}"
                                f" pressed={self._max_pressed}\n")
                except Exception:
                    pass
            if msg.message == _WM_NCMOUSEMOVE:
                over_max = int(msg.wParam) == _HTMAXBUTTON
                self._set_max_nc(hover=over_max)
                if not over_max and self._max_pressed:
                    self._max_pressed = False
                    self._set_max_nc(pressed=False)
                return (False, 0)
            if msg.message == _WM_NCMOUSELEAVE:
                self._max_pressed = False
                self._set_max_nc(hover=False, pressed=False)
                return (False, 0)
            if msg.message == _WM_NCLBUTTONDOWN:
                if int(msg.wParam) == _HTMAXBUTTON:
                    self._max_pressed = True
                    self._set_max_nc(pressed=True)
                    return (True, 0)  # eat: default would start a move loop
                return (False, 0)  # HTCAPTION -> native drag (snap/restore)
            if msg.message == _WM_NCLBUTTONUP:
                was = self._max_pressed
                self._max_pressed = False
                self._set_max_nc(pressed=False)
                if int(msg.wParam) == _HTMAXBUTTON:
                    if was:
                        self._toggle_max()
                    return (True, 0)
                return (False, 0)
            if msg.message == _WM_NCLBUTTONDBLCLK:
                wp = int(msg.wParam)
                if wp == _HTMAXBUTTON:
                    return (True, 0)
                if wp == _HTCAPTION:
                    # no WS_CAPTION style -> DefWindowProc won't do it for us
                    self._toggle_max()
                    return (True, 0)
                return (False, 0)
            if msg.message == _WM_NCRBUTTONUP:
                if int(msg.wParam) == _HTCAPTION:
                    import ctypes
                    lp = int(msg.lParam)
                    mx = ctypes.c_short(lp & 0xFFFF).value
                    my = ctypes.c_short((lp >> 16) & 0xFFFF).value
                    self._show_system_menu(mx, my)
                    return (True, 0)
                return (False, 0)
            if msg.message == _WM_ENTERSIZEMOVE:
                self._accent_drag_swap(True)
            elif msg.message == _WM_EXITSIZEMOVE:
                self._accent_drag_swap(False)
                # wipe any webview white-flash slivers left by the drag
                sched = getattr(self._win, "_ankiblur_schedule_repaint", None)
                if sched is not None:
                    sched()
        except Exception as e:
            try:
                print(f"[AnkiBlur] nativeEventFilter error: {e}")
            except Exception:
                pass
        return (False, 0)

    def _titlebar(self):
        return getattr(self._win, "_ankiblur_titlebar", None)

    def _toggle_max(self):
        # Native toggle: Qt's showMaximized() is a silent no-op here (its
        # cached window state is desynced by the style-change messages we eat),
        # so decide from the REAL placement and let DefWindowProc do it --
        # which also gives the native maximize/restore animation.
        try:
            w = _ankiblur_win32()
            ct, wt, u = w["ctypes"], w["wintypes"], w["u"]
            wp = w["WINDOWPLACEMENT"]()
            wp.length = ct.sizeof(wp)
            u.GetWindowPlacement(wt.HWND(self._hwnd), ct.byref(wp))
            sc = _SC_RESTORE if wp.showCmd == 3 else _SC_MAXIMIZE
            u.PostMessageW(wt.HWND(self._hwnd), _WM_SYSCOMMAND, sc, 0)
        except Exception as e:
            if _ANKIBLUR_NC_LOG:
                try:
                    with open(_ANKIBLUR_NC_LOG, "a") as f:
                        f.write(f"toggle_max ERROR: {e}\n")
                except Exception:
                    pass

    def _set_max_nc(self, hover=None, pressed=None):
        tb = self._titlebar()
        if tb is not None:
            try:
                tb.set_max_nc_state(hover, pressed)
            except Exception:
                pass

    def _caption_hittest(self, x, y, rc):
        """Classify a screen-physical point over the caption area:
        _HTMAXBUTTON / _HTCAPTION / -1 (interactive Qt child -> client) /
        0 (not caption)."""
        win = self._win
        tb = self._titlebar()
        if tb is None or not tb.isVisible():
            return 0
        dpr = self._dpr()
        lx = int((x - rc.left) / dpr)
        ly = int((y - rc.top) / dpr)
        child = win.childAt(QPoint(lx, ly))
        if _ANKIBLUR_NC_LOG and ly < 60:
            try:
                with open(_ANKIBLUR_NC_LOG, "a") as f:
                    f.write(f"HT local=({lx},{ly}) child={child!r} "
                            f"tbgeo={tb.geometry()}\n")
            except Exception:
                pass
        if child is None:
            return 0
        mx = getattr(tb, "_max_btn", None)
        if mx is not None and (child is mx or mx.isAncestorOf(child)):
            return _HTMAXBUTTON
        if isinstance(child, QToolButton) and tb.isAncestorOf(child):
            return -1  # min/close buttons stay ordinary Qt buttons
        if child is tb or tb.isAncestorOf(child):
            return _HTCAPTION
        # empty space right of the menu entries doubles as caption
        mb = getattr(getattr(win, "form", None), "menubar", None)
        if mb is not None and (child is mb or mb.isAncestorOf(child)):
            try:
                if mb.actionAt(mb.mapFrom(win, QPoint(lx, ly))) is None:
                    return _HTCAPTION
            except Exception:
                pass
        return 0

    def _show_system_menu(self, x, y):
        """Right-click-titlebar system menu (Restore/Move/Size/Min/Max/Close),
        with the same enabled/greyed state logic as a native title bar."""
        w = _ankiblur_win32()
        if not w:
            return
        wt, u = w["wintypes"], w["u"]
        hwnd = self._hwnd
        menu = u.GetSystemMenu(wt.HWND(hwnd), False)
        if not menu:
            return
        maxed = _ankiblur_is_maximized(hwnd)
        for cmd, on in ((_SC_RESTORE, maxed), (_SC_MOVE, not maxed),
                        (_SC_SIZE, not maxed), (_SC_MINIMIZE, True),
                        (_SC_MAXIMIZE, not maxed), (_SC_CLOSE, True)):
            u.EnableMenuItem(menu, cmd, _MF_ENABLED if on else _MF_GRAYED)
        cmd = u.TrackPopupMenu(menu, _TPM_RETURNCMD | _TPM_RIGHTBUTTON,
                               int(x), int(y), 0, wt.HWND(hwnd), None)
        if cmd:
            u.PostMessageW(wt.HWND(hwnd), _WM_SYSCOMMAND, cmd, 0)

    def _accent_drag_swap(self, moving):
        """Win10 accent-acrylic lags badly while the window is dragged; the
        standard workaround is to drop to plain blur for the duration of the
        native move/size loop and restore acrylic when it ends."""
        import os

        win = self._win
        if getattr(win, "_ankiblur_backend", None) != "accent-acrylic":
            return
        if os.environ.get("ANKIBLUR_DRAG_FIX", "1") == "0":
            return
        try:
            tint = getattr(win, "_ankiblur_accent_tint", None)
            if tint is None:
                tint = _ankiblur_accent_gradient(_ankiblur_is_dark_theme())
            state = (_ACCENT_ENABLE_BLURBEHIND if moving
                     else _ACCENT_ENABLE_ACRYLICBLURBEHIND)
            _ankiblur_apply_accent(self._hwnd, state, tint)
        except Exception:
            pass

    def _on_nccalcsize(self, msg):
        # Client = the FULL window rect, zero non-client strips. This matches
        # Qt's belief: we eat WM_STYLECHANGED (above), so Qt keeps its cached
        # frameless margins of 0 and lays out content from y=0. Any partial
        # inset (earlier DefWindowProc variants) surfaces as a white or grey
        # band wherever the real client and Qt's margins disagree.
        # Because DefWindowProc no longer runs, the maximized adjustments are
        # done by hand: a maximized THICKFRAME window hangs its (hidden)
        # borders off-screen, so the client is inset back by the border; an
        # auto-hide taskbar needs a 2px reservation on its edge to stay
        # summonable.
        from ctypes import wintypes

        if not msg.wParam:
            return (False, 0)  # wParam == FALSE -> let default handle it
        hwnd = self._hwnd
        rect = wintypes.RECT.from_address(int(msg.lParam))
        if not self._is_fullscreen(hwnd):
            w = _ankiblur_win32()
            ct, wt, u = w["ctypes"], w["wintypes"], w["u"]
            mon = u.MonitorFromWindow(wt.HWND(hwnd), 2)  # NEAREST
            mi = w["MONITORINFO"]()
            mi.cbSize = ct.sizeof(mi)
            if u.GetMonitorInfoW(mon, ct.byref(mi)):
                wk = mi.rcWork
                if (rect.left <= wk.left and rect.top <= wk.top
                        and rect.right >= wk.right and rect.bottom >= wk.bottom):
                    # Maximized. Clamp the client to the work area: a no-op
                    # when Qt drove the placement (window == work area, since
                    # Qt believes margins are 0), and exactly the border-inset
                    # when Windows drove it (borders hang off-screen).
                    rect.left = max(rect.left, wk.left)
                    rect.top = max(rect.top, wk.top)
                    rect.right = min(rect.right, wk.right)
                    rect.bottom = min(rect.bottom, wk.bottom)
                    edge = _ankiblur_taskbar_autohide_edge(hwnd)
                    if edge == _ABE_TOP:
                        rect.top += 2
                    elif edge == _ABE_BOTTOM:
                        rect.bottom -= 2
                    elif edge == _ABE_LEFT:
                        rect.left += 2
                    elif edge == _ABE_RIGHT:
                        rect.right -= 2
        return (True, 0)

    def _on_nchittest(self, msg):
        import ctypes
        from ctypes import wintypes

        hwnd = self._hwnd
        lp = int(msg.lParam)
        x = ctypes.c_short(lp & 0xFFFF).value
        y = ctypes.c_short((lp >> 16) & 0xFFFF).value
        w = _ankiblur_win32()
        rc = wintypes.RECT()
        w["u"].GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rc))
        if self._is_fullscreen(hwnd):
            return (False, 0)
        # Edge resize -- disabled when maximized.
        if not _ankiblur_is_maximized(hwnd):
            bw = _ankiblur_resize_border(hwnd, True, self._dpr())
            left = x < rc.left + bw
            right = x >= rc.right - bw
            top = y < rc.top + bw
            bottom = y >= rc.bottom - bw
            if top and left:
                return (True, _HTTOPLEFT)
            if top and right:
                return (True, _HTTOPRIGHT)
            if bottom and left:
                return (True, _HTBOTTOMLEFT)
            if bottom and right:
                return (True, _HTBOTTOMRIGHT)
            if left:
                return (True, _HTLEFT)
            if right:
                return (True, _HTRIGHT)
            if top:
                return (True, _HTTOP)
            if bottom:
                return (True, _HTBOTTOM)
        # Caption region: native drag (Aero Snap / Shake / drag-to-restore),
        # snap-layouts flyout over the maximize button.
        try:
            ht = self._caption_hittest(x, y, rc)
        except Exception:
            ht = 0
        if ht == _HTMAXBUTTON:
            return (True, _HTMAXBUTTON)
        if ht == _HTCAPTION:
            return (True, _HTCAPTION)
        return (False, 0)  # let Qt return HTCLIENT


# ---------------------------------------------------------------------------
# Add-on adaptation layer.
#
# In the handoff these lived as AnkiQt methods / inline edits in aqt/main.py
# (resizeEvent override, _ankiblur_schedule_repaint/_ankiblur_full_repaint/
# _ankiblur_layout_grips methods, the __init__ window-flag block and the
# setupMainWindow title-bar insertion). Here they are module functions
# attached to / operating on the live mw. The cross-object attribute contract
# is unchanged: _ankiblur_titlebar, _ankiblur_native_filter,
# _ankiblur_sysmenu_shortcut, _ankiblur_backend, _ankiblur_accent_tint,
# _ankiblur_schedule_repaint, _ankiblur_repaint_timer live as dynamic
# attributes on the window, exactly as the filter and title bar expect.
# ---------------------------------------------------------------------------


def _ankiblur_schedule_repaint(window):
    """Debounced full repaint after a resize settles (AnkiBlur, Windows).

    On the layered (translucent) window the webviews only repaint their
    dirty region, so the white flash they draw at their OLD right/bottom
    edge during a resize step is never painted over -- it accumulates as
    the nested white 'ghost' lines seen while dragging a window edge
    (especially when growing). A single forced full-surface repaint once
    the resize settles wipes them."""
    if not _HAS_WIN_BLUR:
        return
    t = getattr(window, "_ankiblur_repaint_timer", None)
    if t is None:
        t = QTimer(window)
        t.setSingleShot(True)
        t.setInterval(120)
        qconnect(t.timeout, lambda: _ankiblur_full_repaint(window))
        window._ankiblur_repaint_timer = t
    t.start()


def _ankiblur_full_repaint(window):
    try:
        w = _ankiblur_win32()
        hwnd = int(window.winId())
        if w and hwnd:
            # INVALIDATE | ERASE | ALLCHILDREN | FRAME | UPDATENOW
            w["u"].RedrawWindow(
                w["wintypes"].HWND(hwnd), None, None,
                0x0001 | 0x0004 | 0x0080 | 0x0400 | 0x0100)
    except Exception:
        pass
    for v in (getattr(window, "toolbarWeb", None), getattr(window, "web", None),
              getattr(window, "bottomWeb", None)):
        try:
            if v is not None:
                v.update()
        except Exception:
            pass
    window.update()


def _ankiblur_layout_grips(window):
    grips = getattr(window, "_ankiblur_grips", None)
    if not grips:
        return
    w, h = window.width(), window.height()
    g, c = 6, 14  # edge thickness, corner size
    geoms = {
        "left": (0, c, g, max(0, h - 2 * c)),
        "right": (w - g, c, g, max(0, h - 2 * c)),
        "top": (c, 0, max(0, w - 2 * c), g),
        "bottom": (c, h - g, max(0, w - 2 * c), g),
        "topleft": (0, 0, c, c),
        "topright": (w - c, 0, c, c),
        "bottomleft": (0, h - c, c, c),
        "bottomright": (w - c, h - c, c, c),
    }
    for name, grip in grips.items():
        x, y, gw, gh = geoms[name]
        grip.setGeometry(x, y, gw, gh)
        grip.raise_()


# Add-on config "windows" section -> ANKIBLUR_* env var seeding. The verified
# code paths above read env vars only (exactly as on the Windows machine the
# implementation was validated on); config values are translated to env vars
# at startup, and a real env var always wins over config.
_CONFIG_ENV_MAP = (
    ("backend", "ANKIBLUR_BACKEND"),
    ("backdrop", "ANKIBLUR_BACKDROP"),
    ("accent_tint", "ANKIBLUR_ACCENT_TINT"),
    ("accent_alpha", "ANKIBLUR_ACCENT_ALPHA"),
    ("border", "ANKIBLUR_BORDER"),
    ("corners", "ANKIBLUR_CORNERS"),
    ("drag_fix", "ANKIBLUR_DRAG_FIX"),
    ("legacy_grips", "ANKIBLUR_LEGACY_GRIPS"),
    ("dark", "ANKIBLUR_DARK"),
    ("tint", "ANKIBLUR_TINT"),
    ("frame_mode", "ANKIBLUR_FRAME_MODE"),
)


def seed_env_from_config(config):
    """Translate the add-on config's "windows" dict into the ANKIBLUR_* env
    vars the transplanted code reads. Env vars that are already set win;
    empty strings and "auto" mean "keep the built-in default"."""
    win_cfg = (config or {}).get("windows") or {}
    for key, env in _CONFIG_ENV_MAP:
        if env in os.environ:
            continue
        val = win_cfg.get(key)
        if val is None or val == "" or val == "auto":
            continue
        if isinstance(val, bool):
            val = "1" if val else "0"
        os.environ[env] = str(val)


def install_window_chrome(window):
    """Pre-show window setup, ported from the handoff's inline AnkiQt hooks.

    Runs at add-on import time (setupAddons: main window + webviews exist,
    first show() has not happened), so like the handoff's AnkiQt.__init__
    block the frameless flag and translucency attributes are in place before
    the window ever becomes visible. WA_TranslucentBackground itself is set
    by window_effects._set_translucent (tracked for the tripwire); the
    HWND-side work (styles, accent, filter) happens in
    _ankiblur_apply_backdrop under the retry loop, which re-derives the HWND
    after any native-window recreation the flag change causes."""
    if not _HAS_WIN_BLUR:
        return

    # main.py AnkiQt.__init__: Qt6 only composites WA_TranslucentBackground
    # with the backdrop material on a FRAMELESS window -- with the native
    # frame the client area stays opaque white (documented Qt6 regression).
    window.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

    # main.py resizeEvent/_ankiblur_schedule_repaint attribute contract: the
    # native filter resolves window._ankiblur_schedule_repaint by name on
    # WM_EXITSIZEMOVE; the title bar's eventFilter drives it on Qt resizes.
    window._ankiblur_schedule_repaint = (
        lambda: _ankiblur_schedule_repaint(window))
    window._ankiblur_full_repaint = lambda: _ankiblur_full_repaint(window)

    # main.py setupMainWindow: frameless window -> custom title bar
    # (move/min/max/close) stacked ABOVE Anki's menu bar. QMainWindow always
    # puts the menu bar at the very top, so wrap both in a menu-widget
    # container with the title bar on top. Edge-resize is handled natively by
    # the WM_NCHITTEST filter; the old Qt grips remain only as a fallback
    # (ANKIBLUR_LEGACY_GRIPS=1).
    if getattr(window, "_ankiblur_titlebar", None) is None:
        titlebar = _AnkiBlurTitleBar(window)
        window._ankiblur_titlebar = titlebar
        _menu_container = QWidget()
        _mv = QVBoxLayout(_menu_container)
        _mv.setContentsMargins(0, 0, 0, 0)
        _mv.setSpacing(0)
        _mv.addWidget(titlebar)
        _mv.addWidget(window.form.menubar)
        window.setMenuWidget(_menu_container)
        window._ankiblur_menu_container = _menu_container

    if (os.environ.get("ANKIBLUR_LEGACY_GRIPS") == "1"
            and not getattr(window, "_ankiblur_grips", None)):
        E = Qt.Edge
        C = Qt.CursorShape
        specs = {
            "left": (E.LeftEdge, C.SizeHorCursor),
            "right": (E.RightEdge, C.SizeHorCursor),
            "top": (E.TopEdge, C.SizeVerCursor),
            "bottom": (E.BottomEdge, C.SizeVerCursor),
            "topleft": (E.TopEdge | E.LeftEdge, C.SizeFDiagCursor),
            "topright": (E.TopEdge | E.RightEdge, C.SizeBDiagCursor),
            "bottomleft": (E.BottomEdge | E.LeftEdge, C.SizeBDiagCursor),
            "bottomright": (E.BottomEdge | E.RightEdge, C.SizeFDiagCursor),
        }
        window._ankiblur_grips = {
            name: _AnkiBlurGrip(window, edges, QCursor(shape))
            for name, (edges, shape) in specs.items()
        }
        _ankiblur_layout_grips(window)


def remove_window_chrome(window):
    """Best-effort undo of install_window_chrome, used only when the backdrop
    retry loop gives up: a frameless window without the native filter's
    caption/resize handling would be barely usable, so restore the native
    frame and titlebar (window_effects also clears the translucency)."""
    if not _HAS_WIN_BLUR:
        return
    try:
        flt = getattr(window, "_ankiblur_native_filter", None)
        if flt is not None:
            QApplication.instance().removeNativeEventFilter(flt)
            window._ankiblur_native_filter = None
    except Exception:
        traceback.print_exc()
    try:
        tb = getattr(window, "_ankiblur_titlebar", None)
        if tb is not None:
            # Reparent the menubar out of the container before setMenuWidget
            # deletes it (Qt owns the previous menu widget).
            window.form.menubar.setParent(window)
            window.setMenuWidget(window.form.menubar)
            window._ankiblur_titlebar = None
            window._ankiblur_menu_container = None
    except Exception:
        traceback.print_exc()
    try:
        window.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)
        if not window.isHidden():
            window.show()  # the flag change hides an already-shown window
    except Exception:
        traceback.print_exc()
