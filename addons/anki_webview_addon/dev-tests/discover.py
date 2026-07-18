"""Isolated checks: snap-flyout class discovery, dbl-click, max-button click.
Move mouse to neutral spot between gestures; generous settle times."""
import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
DPR = 1.1041666666666667


def find():
    res = []
    EP = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(h, l):
        if user32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, b, 256)
            if b.value.endswith("- Anki"):
                res.append(int(h))
        return True

    user32.EnumWindows(EP(cb), 0)
    return res[0] if res else None


h = find()
if not h:
    print("NO ANKI")
    sys.exit(1)
user32.SetWindowPos(wintypes.HWND(h), None, 400, 300, 1000, 700, 0x0004)
user32.SetForegroundWindow(wintypes.HWND(h))
time.sleep(1.0)


def rect():
    r = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r))
    return r


def is_max():
    class WP(ctypes.Structure):
        _fields_ = [("l", wintypes.UINT), ("f", wintypes.UINT),
                    ("s", wintypes.UINT), ("a", wintypes.POINT),
                    ("b", wintypes.POINT), ("rc", wintypes.RECT)]
    wp = WP()
    wp.l = ctypes.sizeof(wp)
    user32.GetWindowPlacement(wintypes.HWND(h), ctypes.byref(wp))
    return wp.s == 3


def maxbtn():
    r = rect()
    bw = round(46 * DPR)
    return (r.right - bw - bw // 2, r.top + round(16 * DPR))


def caption():
    r = rect()
    return (r.left + round(300 * DPR), r.top + round(16 * DPR))


def neutral():
    r = rect()
    user32.SetCursorPos((r.left + r.right) // 2, (r.top + r.bottom) // 2)
    time.sleep(0.3)


def click(x, y, dbl=False):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    if dbl:
        time.sleep(0.05)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(1.2)


# --- snap flyout discovery ---
print("== all popup/tool windows BEFORE hover ==")


def dump():
    out = []
    EP = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hh, l):
        if user32.IsWindowVisible(hh):
            cn = ctypes.create_unicode_buffer(96)
            user32.GetClassNameW(hh, cn, 96)
            ex = user32.GetWindowLongW(hh, -20)
            if (ex & 0x00000080) or "Popup" in cn.value or "Xaml" in cn.value \
                    or "Island" in cn.value or "Drop" in cn.value:
                out.append(cn.value)
        return True

    user32.EnumWindows(EP(cb), 0)
    return out


before = set(dump())
neutral()
user32.SetCursorPos(*maxbtn())
time.sleep(1.8)
after = dump()
new = [c for c in after if c not in before]
print("NEW popup classes during max hover:", new)
print("ALL popup classes during hover:", after)
neutral()

# --- dbl-click caption -> maximize ---
print("\n== double-click caption ==")
print("before is_max:", is_max())
click(*caption(), dbl=True)
print("after dbl-click is_max:", is_max())
if is_max():
    neutral()
    click(*caption(), dbl=True)
    print("after 2nd dbl-click is_max:", is_max())
user32.SetWindowPos(wintypes.HWND(h), None, 400, 300, 1000, 700, 0x0004)
time.sleep(0.6)

# --- max button single click ---
print("\n== max button click ==")
neutral()
print("before is_max:", is_max())
click(*maxbtn())
print("after max-btn click is_max:", is_max())
if is_max():
    neutral()
    click(*maxbtn())
    print("after 2nd max-btn click is_max:", is_max())
user32.SetWindowPos(wintypes.HWND(h), None, 400, 300, 1000, 700, 0x0004)
