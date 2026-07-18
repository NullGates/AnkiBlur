"""Politely close any running Anki main window via WM_CLOSE."""
import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
WM_CLOSE = 0x0010
found = []
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def cb(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    t = buf.value
    if t.endswith("- Anki") or t == "Anki" or t.startswith("Anki -"):
        found.append((int(hwnd), t))
    return True


user32.EnumWindows(EnumWindowsProc(cb), 0)
for hwnd, t in found:
    print(f"closing hwnd=0x{hwnd:X} title={t!r}")
    user32.PostMessageW(wintypes.HWND(hwnd), WM_CLOSE, 0, 0)
if not found:
    print("no Anki window")
time.sleep(3)
