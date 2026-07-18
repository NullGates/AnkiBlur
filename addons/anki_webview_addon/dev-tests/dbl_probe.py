"""Focused: dbl-click caption -> maximize, with HT logging in nc.log."""
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
time.sleep(0.8)


def is_max():
    class WP(ctypes.Structure):
        _fields_ = [("l", wintypes.UINT), ("f", wintypes.UINT),
                    ("s", wintypes.UINT), ("a", wintypes.POINT),
                    ("b", wintypes.POINT), ("rc", wintypes.RECT)]
    wp = WP()
    wp.l = ctypes.sizeof(wp)
    user32.GetWindowPlacement(wintypes.HWND(h), ctypes.byref(wp))
    return wp.s == 3


r = wintypes.RECT()
user32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r))
cx, cy = r.left + round(300 * DPR), r.top + round(16 * DPR)

# what does the wndproc hit-test say right now at that point?
user32.SendMessageW.restype = ctypes.c_longlong
user32.SendMessageW.argtypes = [wintypes.HWND, ctypes.c_uint,
                                ctypes.c_ulonglong, ctypes.c_longlong]
ht = user32.SendMessageW(wintypes.HWND(h), 0x0084, 0,
                         (ctypes.c_longlong(cy).value << 16) | (cx & 0xFFFF))
print(f"hittest at ({cx},{cy}) = {ht}")

print("before is_max:", is_max())
user32.SetCursorPos(cx, cy)
time.sleep(0.3)


def whotop(x, y):
    hh = user32.WindowFromPoint(wintypes.POINT(x, y))
    root = user32.GetAncestor(hh, 2)  # GA_ROOT
    cn = ctypes.create_unicode_buffer(96)
    user32.GetClassNameW(root, cn, 96)
    tb = ctypes.create_unicode_buffer(128)
    user32.GetWindowTextW(root, tb, 128)
    fg = user32.GetForegroundWindow()
    return (f"underpoint root=0x{int(root) & 0xFFFFFFFF:X} cls={cn.value!r} "
            f"title={tb.value!r} anki=0x{h:X} fg=0x{int(fg) & 0xFFFFFFFF:X}")


print(whotop(cx, cy))
for _ in range(2):
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.06)
time.sleep(1.5)
print("after dbl-click is_max:", is_max())
if is_max():
    r2 = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r2))
    cx2, cy2 = r2.left + round(300 * DPR), r2.top + round(16 * DPR)
    user32.SetCursorPos(cx2, cy2)
    time.sleep(0.3)
    for _ in range(2):
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.06)
    time.sleep(1.5)
    print("after 2nd dbl-click is_max:", is_max())
user32.SetWindowPos(wintypes.HWND(h), None, 400, 300, 1000, 700, 0x0004)
