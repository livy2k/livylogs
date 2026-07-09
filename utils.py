import ctypes
from ctypes import wintypes
from constants import user32, SNAP_THRESHOLD

def is_window_minimized(hwnd):
    """Checks if a window is minimized using Win32 API."""
    from constants import WINDOWPLACEMENT
    placement = WINDOWPLACEMENT()
    placement.length = ctypes.sizeof(WINDOWPLACEMENT)
    if user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
        return placement.showCmd == 2 # SW_SHOWMINIMIZED
    return False

def apply_snapping(window, x, y):
    """Applies snapping to screen edges."""
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    ww = window.winfo_width()
    wh = window.winfo_height()

    if abs(x) < SNAP_THRESHOLD: x = 0
    if abs(y) < SNAP_THRESHOLD: y = 0
    if abs(x + ww - sw) < SNAP_THRESHOLD: x = sw - ww
    if abs(y + wh - sh) < SNAP_THRESHOLD: y = sh - wh
    
    return x, y
