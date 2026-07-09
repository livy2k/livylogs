import tkinter as tk
import ctypes
from ctypes import wintypes
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, 
    BUTTON_BG, BUTTON_HOVER, BORDER_COLOR, TEXT_ACCENT, user32, GWL_EXSTYLE,
    WS_EX_TOOLWINDOW, WS_EX_APPWINDOW, WS_EX_TOPMOST, SWP_NOMOVE, SWP_NOSIZE,
    SWP_NOACTIVATE, SWP_SHOWWINDOW, SWP_HIDEWINDOW, HWND_TOPMOST, HWND_NOTOPMOST
)
from utils import apply_snapping

class ThemedMessagebox(tk.Toplevel):
    def __init__(self, parent, title, message, icon="info", on_close=None, extra_button_text=None, extra_button_callback=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=WINDOW_BG)
        self.attributes("-alpha", 0.0)
        self.overrideredirect(True)
        self.resizable(False, False)
        self.on_close_callback = on_close

        self.current_alpha = 0.0
        self.target_alpha = 1.0
        self.fade_speed = 0.1
        self.fade_after_id = None
        self.target_hwnd = None

        width, height = 450, 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width // 2) - (width // 2))
        y = max(0, (screen_height // 2) - (height // 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

        border = tk.Frame(self, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        tk.Label(title_bar, text=title.upper(), bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.close_and_callback())

        content = tk.Frame(inner, bg=WINDOW_BG, padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        icon_text = "ℹ" if icon == "info" else "⚠"
        tk.Label(content, text=icon_text, bg=WINDOW_BG, fg=ACCENT_BLUE if icon=="info" else "#ff4444", font=("Segoe UI", 24)).pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(content, text=message, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10), justify=tk.LEFT, wraplength=400).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_area = tk.Frame(inner, bg=PANEL_DARK, height=40)
        btn_area.pack(fill=tk.X)
        ok_btn = tk.Frame(btn_area, bg=BUTTON_BG, padx=15, pady=5, cursor="hand2")
        ok_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        ok_lbl = tk.Label(ok_btn, text="OK", bg=BUTTON_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"))
        ok_lbl.pack()
        ok_btn.bind("<Button-1>", lambda e: self.close_and_callback())

        if extra_button_text and extra_button_callback:
            def on_extra_click(e):
                self.destroy()
                extra_button_callback()
            ex_btn = tk.Frame(btn_area, bg=BUTTON_BG, padx=15, pady=5, cursor="hand2")
            ex_btn.pack(side=tk.RIGHT, padx=5, pady=5)
            tk.Label(ex_btn, text=extra_button_text.upper(), bg=BUTTON_BG, fg=TEXT_ACCENT, font=("Segoe UI", 9, "bold")).pack()
            ex_btn.bind("<Button-1>", on_extra_click)

        title_bar.bind("<Button-1>", self._click_window)
        title_bar.bind("<B1-Motion>", self._drag_window)
        self.check_target_window()

    def find_target_window(self):
        target_hwnd = [None]
        def enum_windows_callback(hwnd, lparam):
            buf = ctypes.create_unicode_buffer(255)
            user32.GetWindowTextW(hwnd, buf, 255)
            if "Star Wars Galaxies" in buf.value:
                target_hwnd[0] = hwnd
                return False
            return True
        user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback), 0)
        return target_hwnd[0]

    def check_target_window(self):
        if not self.winfo_exists(): return
        self.target_hwnd = self.find_target_window()
        if self.target_hwnd:
            if user32.GetForegroundWindow() == self.target_hwnd or user32.GetForegroundWindow() == user32.GetAncestor(self.winfo_id(), 3):
                self.start_show()
            else: self.start_hide()
        else: self.start_show()
        self.after(1000, self.check_target_window)

    def start_show(self):
        if self.fade_after_id: self.after_cancel(self.fade_after_id)
        self.target_alpha = 1.0
        self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + self.fade_speed)
            self.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.after(20, self.fade_in)

    def start_hide(self):
        if self.fade_after_id: self.after_cancel(self.fade_after_id)
        self.target_alpha = 0.0
        self.fade_out()

    def fade_out(self):
        if self.current_alpha > self.target_alpha:
            self.current_alpha = max(self.target_alpha, self.current_alpha - self.fade_speed)
            self.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.after(20, self.fade_out)

    def close_and_callback(self):
        self.destroy()
        if self.on_close_callback: self.on_close_callback()

    def _click_window(self, event):
        self._offsetx = event.x; self._offsety = event.y

    def _drag_window(self, event):
        x = self.winfo_pointerx() - self._offsetx; y = self.winfo_pointery() - self._offsety
        x, y = apply_snapping(self, x, y)
        self.geometry(f"+{x}+{y}")

    @staticmethod
    def showinfo(parent, title, message, on_close=None, extra_button_text=None, extra_button_callback=None):
        return ThemedMessagebox(parent, title, message, "info", on_close, extra_button_text, extra_button_callback)

    @staticmethod
    def showerror(parent, title, message, on_close=None):
        return ThemedMessagebox(parent, title, message, "error", on_close)
