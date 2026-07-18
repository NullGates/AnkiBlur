# AnkiBlur — Windows Implementation

**Status: WORKING** (verified July 2026, Anki 25.09.4, Python 3.13.5, Qt/PyQt 6.9.1,
Windows 11 23H2 build 22631). 18/19 automated behavior checks pass; the 19th
(snap-layouts flyout) passes with a real mouse and was confirmed by the user.

> **RELEASE GATE — the transplant itself is NOT yet Windows-verified.** The
> "WORKING" verification above applies to the original *inline* `aqt/main.py`
> implementation on the original machine. The transplanted add-on version in
> this tree (`win_native.py` + the new adaptation layer: `install_window_chrome`,
> `seed_env_from_config`, the `_apply_windows` orchestration) has **never been
> executed on a real Windows machine**. Before including it in any release, a
> human MUST run `addons/anki_webview_addon/dev-tests/native_test.py` against a
> live AnkiBlur on real Windows and get >= 18/19 (the snap-layouts flyout check
> requires a real mouse — finding 9).

> **Where the code lives now.** This document was written as the handoff for
> an implementation developed *inline* in the installed `aqt/main.py` on a
> live Windows machine. That implementation has since been transplanted,
> faithfully and with the same `_ankiblur_` / `_AnkiBlur` names, into the
> bundled add-on:
> `addons/anki_webview_addon/ankiblur_background_theme/win_native.py`
> (orchestrated by `window_effects.py::_apply_windows` in the same package,
> which owns the setup retry loop, the `ops` bookkeeping and the tripwire
> give-up path). The add-on loads at `setupAddons()` time — after the main
> window and webviews exist but **before the first `show()`** — which is what
> lets it set the frameless flag and translucency attributes as early as the
> old inline `AnkiQt.__init__` hook did. The inline `AnkiQt` method hooks
> (`resizeEvent` → repaint debounce, title-bar insertion) became an
> eventFilter + dynamic attributes on `mw`; everything else is verbatim.
> Section references to `main.py` below describe the original inline
> anchors; the same blocks exist 1:1 in `win_native.py`.

This document exists so that a future AI (or human) can troubleshoot or re-port
this work after an upstream Anki update **without rediscovering everything the
hard way**. Read the "Verified findings" section before changing ANYTHING — every
item there was established experimentally and several are deeply
counter-intuitive.

---

## 1. What this is

AnkiBlur is a CI/CD repo that fetches upstream Anki and applies patches to give
the main window a glassmorphism / transparent-acrylic-blur look. Linux and macOS
were already done; this is the **finished Windows work**:

- a frameless, translucent Qt window with real Windows acrylic blur behind it,
- a custom QWidget title bar (min/max/close) that behaves **exactly** like a
  native one: Aero Snap, snap-layouts flyout, double-click-to-maximize,
  drag-to-move/restore, right-click system menu, Alt+Space, native
  maximize animation, edge resize — all verified by
  `addons/anki_webview_addon/dev-tests/native_test.py`.

### Where the pieces are in this repo

| File | What it is |
|---|---|
| `addons/anki_webview_addon/ankiblur_background_theme/win_native.py` | **The working code.** The full transplanted implementation: constants, `_ankiblur_win32()` cache, blur backends, native frame, `_AnkiBlurNativeFilter`, `_AnkiBlurTitleBar`, repaint helpers, plus the add-on adaptation layer (`install_window_chrome`, `seed_env_from_config`). |
| `addons/anki_webview_addon/ankiblur_background_theme/window_effects.py` | `_apply_windows`: seeds env vars from the add-on config, sets translucency + chrome pre-show, runs the backdrop retry loop (150 ms + 15 × 100 ms), records `ops` for the tripwire, restores an opaque natively-framed window on give-up. |
| `addons/anki_webview_addon/ankiblur_background_theme/tripwire.py` | Post-startup self-check; reports which blur backend engaged and warns only when none did. |
| `addons/anki_webview_addon/dev-tests/native_test.py` | 19-check automated behavior suite (hit-tests, maximize paths, system menu, snap, minimize…). Run it against a live Anki on Windows to verify a port. |
| `addons/anki_webview_addon/dev-tests/{close_anki,discover,dbl_probe,flyout_truth}.py` | Helper probes used during debugging (close window, isolated gesture probes, snap-flyout ground truth). |

All AnkiBlur code is marked: search for `ankiblur` (case-insensitive).
Everything is prefixed `_ankiblur_` / `_AnkiBlur`, so a future rebase is
"diff `win_native.py` against upstream behavior and re-verify the marked
blocks".

---

## 2. Architecture overview

Three cooperating pieces, all in `win_native.py`:

### 2.1 Tiered blur backends — `_ankiblur_backend_plan` / `_ankiblur_apply_backdrop`

The window is created with `FramelessWindowHint` + `WA_TranslucentBackground`
(+ `WA_NoSystemBackground`). Qt 6 makes such top-levels **`WS_EX_LAYERED`**,
which dictates everything below.

Backends, tried in order until one applies cleanly:

| Backend | API | Windows builds | Notes |
|---|---|---|---|
| `accent-acrylic` (**default**) | `SetWindowCompositionAttribute(WCA_ACCENT_POLICY=19)`, `ACCENT_ENABLE_ACRYLICBLURBEHIND=4` | ≥17134 (Win10 1803), incl. all Win11 | The only *acrylic* that composites behind layered Qt windows. Gradient color alpha must be ≥1. |
| `accent-blur` (fallback / `aero`) | same, `ACCENT_ENABLE_BLURBEHIND=3` | universal | Softer gaussian blur, always works. |
| `mica1029` | `DwmSetWindowAttribute(1029)` undocumented | 22000–22522 **only** (Win11 21H2) | Removed/no-op in 22H2+. Only tried for explicit mica requests. |
| `dwm` | `DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE=38)` | ≥22523 | **Broken for this window** (see findings). Never default; only when forced. |

Env vars: `ANKIBLUR_BACKEND`, `ANKIBLUR_BACKDROP`, `ANKIBLUR_ACCENT_TINT`,
`ANKIBLUR_ACCENT_ALPHA` (defaults: dark `#101010` / light `#F9F9F9`, alpha 153),
`ANKIBLUR_BORDER` (`none` by default → kills the Win11 1px border, see below),
`ANKIBLUR_DRAG_FIX` (Win10: swap acrylic→blur during drags to fix lag).
The add-on config's `windows` section seeds any of these that are unset
(`win_native.seed_env_from_config`); a real env var always wins.

### 2.2 Zero-strip native frame — `_ankiblur_install_native_frame` + `_AnkiBlurNativeFilter`

Windows features (Aero Snap, snap layouts, native resize/maximize) are gated on
**window styles** the frameless Qt window doesn't have. We add them behind Qt's
back and then *hide the fact from Qt*:

1. `SetWindowLongPtr(GWL_STYLE, style | WS_THICKFRAME | WS_MAXIMIZEBOX |
   WS_MINIMIZEBOX | WS_SYSMENU)`
   - `WS_THICKFRAME`: required for Aero Snap and native edge-resize (verified:
     Win+Left literally no-ops without it).
   - `WS_MAXIMIZEBOX` (+`MINIMIZEBOX`/`SYSMENU`): **no visuals** without
     `WS_CAPTION`, but Windows gates the snap-layouts flyout and
     DefWindowProc's SC_MAXIMIZE handling on them.
   - `WS_CAPTION` is deliberately NOT added — on Win11 it makes DWM draw its own
     (non-functional here) caption buttons on top of ours.
2. The app-level `QAbstractNativeEventFilter` (`_AnkiBlurNativeFilter`,
   installed once, strong ref kept on the window — Qt does NOT take ownership)
   **eats `WM_STYLECHANGING`/`WM_STYLECHANGED`** → Qt keeps its cached
   frameless margins at 0 and never fights the styles.
3. `WM_NCCALCSIZE` answers "client == full window" (0 insets); when maximized
   it clamps the client to the monitor work area (+2px reservation for
   auto-hide taskbars).
4. `CS_DBLCLKS` is set on the window class (`SetClassLongPtr(GCL_STYLE)`).

Result: zero visible non-client strip, but Windows believes it's a normal
resizable, maximizable window.

`ANKIBLUR_FRAME_MODE=none` disables all of this (debug only — breaks snap).

### 2.3 Custom caption via non-client messages — the message table

`WM_NCHITTEST` (`_on_nchittest` → `_caption_hittest`) classifies points:
edge zones → HT resize codes (skipped when maximized/fullscreen); the custom
title bar → `HTCAPTION`; our maximize button → `HTMAXBUTTON` (9); interactive
Qt children (min/close buttons, menu entries) → `HTCLIENT`; menubar empty
space → `HTCAPTION`. Coordinates: physical→logical via
`windowHandle().devicePixelRatio()` then `QWidget.childAt`.

Returning `HTMAXBUTTON` is what makes Win11 show the snap-layouts flyout — but
it also **reroutes all mouse traffic over that button into non-client messages
that Qt never converts to widget events**, so hover/press/click are
re-implemented in the filter:

| Message | Handling |
|---|---|
| `WM_NCMOUSEMOVE` | sync hover state onto the Qt button (dynamic props `ncHover`/`ncPressed` + unpolish/polish) |
| `WM_NCMOUSELEAVE` | clear hover/pressed |
| `WM_NCLBUTTONDOWN` wp=HTMAXBUTTON | set pressed, **eat** (default would start a move loop) |
| `WM_NCLBUTTONDOWN` wp=HTCAPTION | pass through → native drag loop (snap, drag-to-restore all free) |
| `WM_NCLBUTTONUP` wp=HTMAXBUTTON | if was pressed → `_toggle_max()`, eat |
| `WM_NCLBUTTONDBLCLK` wp=HTCAPTION | `_toggle_max()`, eat (no WS_CAPTION → DefWindowProc won't do it) |
| `WM_NCRBUTTONUP` wp=HTCAPTION | `_show_system_menu(x, y)`, eat |
| `WM_NCPAINT` | **eat, return (True, 0)** — see findings (white ghost lines) |
| `WM_NCACTIVATE` | **eat, return (True, 1)** — keeps activation, skips legacy NC repaint |
| `WM_ENTERSIZEMOVE`/`WM_EXITSIZEMOVE` | Win10 acrylic drag-lag swap + post-drag repaint (`_ankiblur_schedule_repaint`, debounced 120 ms, wipes webview flash slivers) |

`_show_system_menu`: `GetSystemMenu` + `EnableMenuItem` (Restore/Move/Size/
Min/Max/Close greyed appropriately vs maximized state) + `TrackPopupMenu
(TPM_RETURNCMD)` + `PostMessage(WM_SYSCOMMAND)`. Alt+Space is a `QShortcut`
(DefWindowProc only provides the accelerator for WS_CAPTION windows).

`_AnkiBlurTitleBar` (QWidget): min/max/close `QToolButton`s with Segoe Fluent
glyphs (min `U+E921`, max `U+E922`, restore `U+E923`, close `U+E8BB`), glyph
synced on `WindowStateChange` via `eventFilter`/`sync_max_glyph`. The same
eventFilter also handles `QEvent.Resize` (the add-on replacement for the
inline `resizeEvent` override) → `_ankiblur_schedule_repaint`.

---

## 3. Verified findings — DO NOT re-litigate

Each of these cost hours. If a behavior regresses after an Anki/Qt update,
check these first.

1. **DWM backdrops don't render behind layered windows.**
   `DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE)` returns hr=0 ("success")
   but draws NOTHING behind a `WS_EX_LAYERED` window → webviews composite on
   black. Qt 6 translucent top-levels are always layered. This is why the
   legacy `SetWindowCompositionAttribute` accent path is the default and `dwm`
   must never be. (Same story for `DwmExtendFrameIntoClientArea`: no effect
   except a faint 1px line — it is deliberately NOT called at all.)

2. **Qt's `showMaximized()`/`showNormal()` silently NO-OP on this window.**
   Because we eat the style-change messages, Qt's cached window state desyncs
   from reality and its maximize path does nothing (no error). `_toggle_max`
   therefore reads the REAL state (`GetWindowPlacement().showCmd == 3`) and
   posts native `WM_SYSCOMMAND` `SC_MAXIMIZE`/`SC_RESTORE`. Bonus: native
   maximize animation. The title bar's Qt-side `_toggle_max` delegates to the
   filter's. **Never "simplify" this back to `showMaximized()`.**

3. **White edge lines + resize ghost trails = legacy GDI non-client frame.**
   DWM's modern frame never applies to layered windows, so DefWindowProc paints
   the ancient white 3D border into the THICKFRAME strips. Fix: eat
   `WM_NCPAINT` → `(True, 0)` and `WM_NCACTIVATE` → `(True, 1)`.

4. **The 1px grey line at the very top = Win11 DWM border**, removed with
   `DwmSetWindowAttribute(DWMWA_BORDER_COLOR=34, DWMWA_COLOR_NONE=0xFFFFFFFE)`.
   A remaining 1px wallpaper-colored gradient at the top edge is the acrylic
   blur kernel's inherent edge bleed — present on minimal probe windows too,
   not removable, normally invisible.

5. **`WM_NCCALCSIZE` + Qt margins interplay.** Qt recomputes frame margins if
   it *sees* the style change; eating `WM_STYLECHANGING/ED` keeps margins 0.
   If you ever see a ~7px white band across the top, this contract broke.

6. **Never override `QWidget.nativeEvent` in PyQt6** for this — it crashed.
   App-level `QAbstractNativeEventFilter` is the stable path. Keep a strong
   Python reference to the filter (Qt does not own it).

7. **`WS_MAXIMIZEBOX|WS_MINIMIZEBOX|WS_SYSMENU` are behavioral gates.** Without
   them: no snap-layouts flyout, and SC_MAXIMIZE paths misbehave. They draw
   nothing without WS_CAPTION, so they're free.

8. **Inside `_ankiblur_*` helpers use the cached `w = _ankiblur_win32()` dict**
   (`w["ctypes"]`, `w["u"]`, `w["wintypes"]`, `w["WINDOWPLACEMENT"]`…) — bare
   `ctypes` NameErrors here crash the setup retry loop *mid-way*, leaving the
   window half-configured (styles applied, filter handlers missing). Also
   `GetWindowPlacement.argtypes` is already bound to `w["WINDOWPLACEMENT"]` —
   defining your own struct raises a ctypes TypeError.

9. **Snap-layouts flyout cannot be verified with injected input.**
   `SetCursorPos`/`mouse_event` hover does not trigger it — not even over stock
   Notepad's maximize button (ground truth: `dev-tests/flyout_truth.py`).
   Returning `HTMAXBUTTON` is the documented contract; verify the flyout with
   a real mouse only. (It was confirmed working by a human on the original
   test machine.)

10. **Test-harness gotcha:** probes that open helper windows (Notepad…) can
    leave them covering Anki — injected clicks then silently land on the wrong
    window and "fail". `WindowFromPoint`-verify before clicking
    (`dev-tests/dbl_probe.py` shows how).

11. Machine quirk: the original test machine's clock was ~9h off, which trips
    Anki's sync clock warning — unrelated to AnkiBlur.

---

## 4. How to re-apply after an upstream Anki update

The code no longer lives in patched site-packages; it rides along in the
add-on and touches aqt only through `mw` attributes and Qt calls, so most
upstream releases need **no re-porting at all** — CI
(`.github/workflows/test-runtime-patches.yml` + `scripts/probe-aqt-symbols.py`)
detects symbol drift, and the add-on's tripwire reports runtime failures.

If something does break:

1. All Windows behavior is in
   `addons/anki_webview_addon/ankiblur_background_theme/win_native.py`; the
   orchestration (retry loop, ops, give-up) is in `window_effects.py`
   (`_apply_windows`). The transplant inventory (all `_ankiblur_`-prefixed):
   - module-level constants block (`_WS_*`, `_WM_*`, `_HT*`, `_SC_*`,
     `_ACCENT_*`, `_DWMWA_*`, `_ANKIBLUR_NC_LOG`…),
   - `_ankiblur_win32()` cache + struct definitions,
   - backend functions (`_ankiblur_backend_plan`, `_ankiblur_apply_accent`,
     `_ankiblur_accent_gradient`, `_ankiblur_apply_backdrop`, border removal),
   - `_ankiblur_install_native_frame`, `_ankiblur_frame_changed`,
   - `_AnkiBlurNativeFilter` (whole class), `_AnkiBlurTitleBar` (whole class),
   - the add-on adaptation layer (`install_window_chrome`,
     `remove_window_chrome`, `seed_env_from_config`, the repaint helpers).
   The aqt anchor points the add-on relies on: setupAddons() running after
   the window+webviews exist but before the first `show()`, `mw.form.menubar`,
   `mw.fullscreen`, `QMainWindow.setMenuWidget`. Search upstream diff for
   changes to `setWindowFlags`, `nativeEvent`, or main-window layout if
   things break.
2. `python -m py_compile win_native.py` (the add-on's `__init__` catches and
   reports failures via the tripwire instead of crashing Anki).
3. Start Anki on Windows, then run
   `addons/anki_webview_addon/dev-tests/native_test.py` (positions the window
   itself; close other windows overlapping 400,300–1400,1000 first). Expect
   ≥18/19 — the flyout check needs a human mouse.
4. Debug channel: set env `ANKIBLUR_NC_LOG=<path>` to append every NC mouse
   message + hit-test classification to a file (works even though the launcher
   may not forward env vars — if it doesn't, temporarily hardcode the default
   in `win_native.py` next to `_ANKIBLUR_NC_LOG`).
5. When green, rebuild the committed add-on zip
   (`scripts/build-addon-zip.py`, see the workflow for the exact invocation)
   and commit both the source and the zip.

## 5. Quick triage table

| Symptom | Likely cause | Where to look |
|---|---|---|
| Black window background | dwm backend got used / accent call failed | finding 1, `_ankiblur_apply_backdrop` order |
| White lines on edges / ghost outlines while resizing | NCPAINT/NCACTIVATE no longer eaten | finding 3 |
| 7px white band across the top | style change leaked to Qt (STYLECHANGED eating broke) | finding 5 |
| 1px grey top line | border color attribute not applied | finding 4 |
| Maximize button / dbl-click does nothing | Qt maximize path used instead of native SC_ | finding 2 |
| Win+Left does nothing | WS_THICKFRAME missing | §2.2 |
| No snap-layouts flyout (real mouse) | WS_MAXIMIZEBOX missing | finding 7 |
| Window half-broken, no custom behaviors at all | exception mid-`_ankiblur_install_native_frame` (check Anki error dialog) | finding 8 |
| Snap flyout "fails" in automated tests only | expected — injection can't trigger it | finding 9 |
