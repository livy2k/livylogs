"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import ctypes
from ctypes import wintypes

# Version Info
VERSION = "1.0"

# Win32 Constants
SW_HIDE = 0
SW_SHOW = 5
SW_RESTORE = 9
SW_SHOWMINIMIZED = 2
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOPMOST = 0x00000008

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080

# UI Colors and Styling
WINDOW_BG = "#0a0b0d"
PANEL_BG = "#14171c"
PANEL_DARK = "#0d0f12"
ACCENT_BLUE = "#00a2ff"
ACCENT_GLOW = "#005a8e"
BORDER_COLOR = "#2a2e35"
BORDER_HIGHLIGHT = "#3f444d"
TEXT_PRIMARY = "#e1e4e8"
TEXT_SECONDARY = "#8b949e"
TEXT_ACCENT = "#00a2ff"
TEXT_DISABLED = "#555555"
BUTTON_BG = "#1f242d"
BUTTON_HOVER = "#2a2e35"
ENTRY_BG = "#090a0c"
COLOR_DEFAULT_CLASS = "#00a2ff" # Default blue for unidentified classes

# New Sophisticated Graphics Constants
TITLE_GRADIENT_START = "#1a1d23"
TITLE_GRADIENT_END = "#0d0f12"
CORNER_RADIUS = 10
WINDOW_SHADOW_COLOR = "#000000"

# Layout Constants
MIN_WIDTH = 400
MIN_HEIGHT = 40
SNAP_THRESHOLD = 20

# DLLs
winmm = ctypes.WinDLL('winmm')
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# Win32 Structures
if not hasattr(wintypes, "WINDOWPLACEMENT"):
    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]
    wintypes.WINDOWPLACEMENT = WINDOWPLACEMENT
else:
    WINDOWPLACEMENT = wintypes.WINDOWPLACEMENT
