"""Ground truth: does the snap flyout appear over Notepad's max button with
the same SetCursorPos injection, and what window class hosts it?"""
import ctypes
import subprocess
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))


def find(title_sub):
    res = []
    EP = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(h, l):
        if user32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, b, 256)
            if title_sub in b.value:
                res.append(int(h))
        return True

    user32.EnumWindows(EP(cb), 0)
    return res[0] if res else None


def dump_all():
    """Every top-level window: (class, visible, cloaked)."""
    out = []
    EP = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    dwmapi = ctypes.windll.dwmapi

    def cb(hh, l):
        cn = ctypes.create_unicode_buffer(96)
        user32.GetClassNameW(hh, cn, 96)
        vis = bool(user32.IsWindowVisible(hh))
        cloaked = ctypes.c_int(0)
        dwmapi.DwmGetWindowAttribute(wintypes.HWND(hh), 14,
                                     ctypes.byref(cloaked), 4)
        out.append((int(hh), cn.value, vis, cloaked.value))
        return True

    user32.EnumWindows(EP(cb), 0)
    return out


proc = subprocess.Popen(["notepad.exe"])
time.sleep(3.0)
np = find("Notepad")
print("notepad hwnd:", hex(np or 0))
if not np:
    raise SystemExit(1)
user32.SetWindowPos(wintypes.HWND(np), None, 300, 200, 900, 600, 0x0004)
user32.SetForegroundWindow(wintypes.HWND(np))
time.sleep(0.8)

r = wintypes.RECT()
user32.GetWindowRect(wintypes.HWND(np), ctypes.byref(r))
# notepad11 caption buttons: max is 2nd from right, each ~46px wide (physical ~51)
mx, my = r.right - 51 - 51 - 25, r.top + 25

# scan for the exact HTMAXBUTTON spot
user32.SendMessageW.restype = ctypes.c_longlong
user32.SendMessageW.argtypes = [wintypes.HWND, ctypes.c_uint,
                                ctypes.c_ulonglong, ctypes.c_longlong]


def htest(x, y):
    return user32.SendMessageW(
        wintypes.HWND(np), 0x0084, 0,
        (ctypes.c_longlong(y).value << 16) | (x & 0xFFFF))


found = None
for dy in (25, 20, 30, 16):
    for dx in range(60, 200, 8):
        if htest(r.right - dx, r.top + dy) == 9:
            found = (r.right - dx, r.top + dy)
            break
    if found:
        break
print("HTMAXBUTTON spot:", found)
if found:
    mx, my = found

before = {(h, c) for h, c, v, cl in dump_all() if v and not cl}
user32.SetCursorPos(int(mx), int(my))
# wiggle: hover tracking wants real WM_MOUSEMOVE traffic
for i in range(6):
    user32.mouse_event(0x0001, 1 if i % 2 else -1, 0, 0, 0)  # MOVE relative
    time.sleep(0.1)
time.sleep(1.8)
after = dump_all()
new_vis = [(hex(h), c) for h, c, v, cl in after
           if v and not cl and (h, c) not in before]
print("NEW visible windows during Notepad max hover:", new_vis)
# also anything newly visible-but-cloaked with interesting class
xaml = [(hex(h), c, v, cl) for h, c, v, cl in after
        if any(k in c for k in ("Xaml", "Island", "Popup", "Snap"))]
print("Xaml-ish windows (h, class, vis, cloaked):", xaml)

# hover check: what does hit-test say at that point
user32.SendMessageW.restype = ctypes.c_longlong
user32.SendMessageW.argtypes = [wintypes.HWND, ctypes.c_uint,
                                ctypes.c_ulonglong, ctypes.c_longlong]
ht = user32.SendMessageW(wintypes.HWND(np), 0x0084, 0,
                         (ctypes.c_longlong(my).value << 16) | (mx & 0xFFFF))
print("notepad hittest at hover point:", ht)

proc.terminate()
