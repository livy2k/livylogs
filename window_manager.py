"""
WindowManager - handles creation, lifecycle, and refresh of popout windows.
"""

import tkinter as tk
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT,
    TITLE_GRADIENT_START, TITLE_GRADIENT_END
)
from utils import apply_snapping

class WindowManager:
    def __init__(self, app):
        self.app = app
        self._windows = {}  # name -> window instance
        self._order = []    # list of names in registration order

    def register(self, name, window):
        """Register a popout window with a unique name."""
        if name in self._windows:
            raise ValueError(f"Window '{name}' already registered")
        self._windows[name] = window
        self._order.append(name)

    def get(self, name):
        return self._windows.get(name)

    def show(self, name, force_open=False):
        win = self._windows.get(name)
        if win:
            win.show(force_open=force_open)

    def close(self, name):
        win = self._windows.get(name)
        if win:
            win.close()

    def refresh_all(self, force=False):
        for name in self._order:
            win = self._windows.get(name)
            if win:
                try:
                    win.refresh(force=force)
                except Exception as e:
                    # Log but don't crash
                    try:
                        with open("crash_log.txt", "a") as f:
                            f.write(f"WindowManager: refresh error for {name}: {e}\n")
                    except:
                        pass

    def get_open_windows(self):
        """Return list of tkinter windows that are currently open."""
        result = []
        for name in self._order:
            win = self._windows.get(name)
            if win and win.window and win.window.winfo_exists():
                result.append(win.window)
        return result

    def save_all_configs(self):
        for name in self._order:
            win = self._windows.get(name)
            if win:
                try:
                    win.save_config()
                except:
                    pass

    def close_all(self):
        for name in self._order:
            win = self._windows.get(name)
            if win:
                try:
                    win.close()
                except:
                    pass
