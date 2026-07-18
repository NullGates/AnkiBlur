"""Automated native-frame behavior suite for the AnkiBlur window.

Simulates real user input (SetCursorPos + mouse_event + keybd_event) and
verifies each behavior a normal Windows app has:

  1.  WM_NCHITTEST map: caption / max button / min button / menubar / client
  2.  double-click title bar -> maximize; again -> restore
  3.  click custom max button (NC path) -> maximize; again -> restore
  4.  right-click title bar -> system menu opens (#32768), Esc closes
  5.  hover max button -> Win11 snap-layouts flyout appears
  6.  drag title bar -> window moves (native move loop)
  7.  drag title bar down while maximized -> restores (drag-to-restore)
  8.  Win+Left -> snap left half ; restore
  9.  minimize via taskbar-equivalent (SC_MINIMIZE) -> iconic; restore
  10. maximized: client == work area
"""

import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

HTCLIENT, HTCAPTION, HTMAXBUTTON = 1, 2, 9
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}: {name} {detail}")


def find_anki():
    res = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                         wintypes.LPARAM)

    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value.endswith("- Anki"):
                res.append(int(hwnd))
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return res[0] if res else None


hwnd = find_anki()
if not hwnd:
    print("NO ANKI WINDOW")
    sys.exit(1)

# deterministic start geometry
X, Y, W, H = 400, 300, 1000, 700
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
user32.SetForegroundWindow(wintypes.HWND(hwnd))
time.sleep(1.0)

DPR = 1.1041666666666667  # physical/logical (from earlier probes)


def rect():
    r = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(r))
    return r


def is_max():
    class WP(ctypes.Structure):
        _fields_ = [("length", wintypes.UINT), ("flags", wintypes.UINT),
                    ("showCmd", wintypes.UINT), ("a", wintypes.POINT),
                    ("b", wintypes.POINT), ("rc", wintypes.RECT)]
    wp = WP()
    wp.length = ctypes.sizeof(wp)
    user32.GetWindowPlacement(wintypes.HWND(hwnd), ctypes.byref(wp))
    return wp.showCmd == 3


def pts():
    """Interesting points (screen physical) based on current rect."""
    r = rect()
    btn_w = round(46 * DPR)
    btn_y = r.top + round(16 * DPR)
    return {
        "caption": (r.left + round(300 * DPR), r.top + round(16 * DPR)),
        "close": (r.right - btn_w // 2, btn_y),
        "max": (r.right - btn_w - btn_w // 2, btn_y),
        "min": (r.right - 2 * btn_w - btn_w // 2, btn_y),
        "menubar_gap": (r.left + round(400 * DPR), r.top + round(44 * DPR)),
        "menu_file": (r.left + round(20 * DPR), r.top + round(44 * DPR)),
        "client": ((r.left + r.right) // 2, (r.top + r.bottom) // 2),
    }


def ht(x, y):
    user32.SendMessageW.restype = ctypes.c_longlong
    user32.SendMessageW.argtypes = [wintypes.HWND, ctypes.c_uint,
                                    ctypes.c_ulonglong, ctypes.c_longlong]
    return user32.SendMessageW(wintypes.HWND(hwnd), 0x0084, 0,
                               (ctypes.c_longlong(y).value << 16)
                               | (x & 0xFFFF))


# --- 1. hit-test map ---------------------------------------------------------
p = pts()
check("hittest caption", ht(*p["caption"]) == HTCAPTION, f"={ht(*p['caption'])}")
check("hittest max button", ht(*p["max"]) == HTMAXBUTTON, f"={ht(*p['max'])}")
check("hittest min button is client", ht(*p["min"]) == HTCLIENT,
      f"={ht(*p['min'])}")
check("hittest close is client", ht(*p["close"]) == HTCLIENT,
      f"={ht(*p['close'])}")
check("hittest menubar gap is caption", ht(*p["menubar_gap"]) == HTCAPTION,
      f"={ht(*p['menubar_gap'])}")
check("hittest File menu is client", ht(*p["menu_file"]) == HTCLIENT,
      f"={ht(*p['menu_file'])}")
check("hittest client", ht(*p["client"]) == HTCLIENT, f"={ht(*p['client'])}")


def move_to(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)


def click(x, y, right=False, dbl=False):
    move_to(x, y)
    down = 0x0008 if right else 0x0002
    up = 0x0010 if right else 0x0004
    user32.mouse_event(down, 0, 0, 0, 0)
    user32.mouse_event(up, 0, 0, 0, 0)
    if dbl:
        time.sleep(0.08)
        user32.mouse_event(down, 0, 0, 0, 0)
        user32.mouse_event(up, 0, 0, 0, 0)
    time.sleep(0.15)


def key(vk, up=False):
    user32.keybd_event(vk, 0, 2 if up else 0, 0)


# --- 2. double-click caption -> maximize / restore ---------------------------
click(*p["caption"], dbl=True)
time.sleep(1.0)
check("dbl-click caption maximizes", is_max())
p2 = pts()
click(*p2["caption"], dbl=True)
time.sleep(1.0)
check("dbl-click again restores", not is_max())
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
time.sleep(0.5)

# --- 3. max button click (non-client path) -----------------------------------
p = pts()
click(*p["max"])
time.sleep(1.0)
check("max button click maximizes", is_max())
# 10. maximized client == work area
class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


mon = user32.MonitorFromWindow(wintypes.HWND(hwnd), 2)
mi = MONITORINFO()
mi.cbSize = ctypes.sizeof(mi)
user32.GetMonitorInfoW(mon, ctypes.byref(mi))
wk = mi.rcWork
cr = wintypes.RECT()
user32.GetClientRect(wintypes.HWND(hwnd), ctypes.byref(cr))
org = wintypes.POINT(0, 0)
user32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(org))
check("maximized client fits work area",
      abs(org.x - wk.left) <= 2 and abs(org.y - wk.top) <= 2
      and abs(cr.right - (wk.right - wk.left)) <= 4
      and abs(cr.bottom - (wk.bottom - wk.top)) <= 4,
      f"client={cr.right}x{cr.bottom}@{org.x},{org.y}")

p3 = pts()
click(*p3["max"])
time.sleep(1.0)
check("max button click restores", not is_max())
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
time.sleep(0.5)

# --- 4. right-click caption -> system menu -----------------------------------
p = pts()
click(*p["caption"], right=True)
time.sleep(0.7)
menu_hwnd = user32.FindWindowW("#32768", None)
menu_visible = bool(menu_hwnd) and user32.IsWindowVisible(menu_hwnd)
check("right-click caption opens system menu", menu_visible,
      f"menu_hwnd=0x{menu_hwnd or 0:X}")
key(0x1B)
key(0x1B, True)
time.sleep(0.4)

# --- 5. snap layouts flyout on max-button hover ------------------------------
p = pts()
move_to(*p["max"])
time.sleep(1.6)
flyouts = []
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                     wintypes.LPARAM)


def cb2(h, lp):
    if user32.IsWindowVisible(h):
        buf = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(h, buf, 64)
        if buf.value in ("Xaml_WindowedPopupClass", "XamlExplorerHostIslandWindow"):
            flyouts.append((int(h), buf.value))
    return True


user32.EnumWindows(EnumWindowsProc(cb2), 0)
check("snap-layouts flyout appears on hover", len(flyouts) > 0,
      f"popups={flyouts}")
move_to(p["client"][0], p["client"][1])
time.sleep(0.5)

# --- 6. drag caption moves the window ---------------------------------------
r_before = rect()
cx, cy = pts()["caption"]
move_to(cx, cy)
user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
time.sleep(0.15)
for i in range(20):
    move_to(cx + (i + 1) * 8, cy + (i + 1) * 4)
    time.sleep(0.02)
user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
time.sleep(0.6)
r_after = rect()
check("caption drag moves window",
      abs(r_after.left - r_before.left) > 100
      and abs(r_after.top - r_before.top) > 40,
      f"moved {r_after.left - r_before.left},{r_after.top - r_before.top}")
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
time.sleep(0.5)

# --- 7. drag-to-restore from maximized ---------------------------------------
user32.ShowWindow(wintypes.HWND(hwnd), 3)
time.sleep(1.0)
p = pts()
cx, cy = p["caption"]
move_to(cx, cy)
user32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(0.15)
for i in range(15):
    move_to(cx, cy + (i + 1) * 12)
    time.sleep(0.02)
user32.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(0.8)
check("drag-to-restore from maximized", not is_max(),
      f"is_max={is_max()}")
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
time.sleep(0.5)

# --- 8. Win+Left snap ---------------------------------------------------------
user32.SetForegroundWindow(wintypes.HWND(hwnd))
time.sleep(0.3)
key(0x5B)
key(0x25)
key(0x25, True)
key(0x5B, True)
time.sleep(1.2)
key(0x1B)
key(0x1B, True)
time.sleep(0.4)
r = rect()
half = (wk.right - wk.left) // 2
check("Win+Left snaps to left half",
      abs(r.left - wk.left) <= 12 and abs((r.right - r.left) - half) <= 24,
      f"rect=({r.left},{r.top},{r.right},{r.bottom})")
user32.SetWindowPos(wintypes.HWND(hwnd), None, X, Y, W, H, 0x0004)
time.sleep(0.5)

# --- 9. minimize / restore ----------------------------------------------------
user32.PostMessageW(wintypes.HWND(hwnd), 0x0112, 0xF020, 0)  # SC_MINIMIZE
time.sleep(1.0)
check("SC_MINIMIZE iconifies", bool(user32.IsIconic(wintypes.HWND(hwnd))))
user32.ShowWindow(wintypes.HWND(hwnd), 9)
time.sleep(1.0)
check("restore from minimized", not user32.IsIconic(wintypes.HWND(hwnd)))

print(f"{'ALL PASS' if all(results) else 'SOME FAILED'}"
      f" ({sum(1 for r in results if r)}/{len(results)})")
