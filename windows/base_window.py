import tkinter as tk
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)
from utils import apply_snapping

class BasePopoutWindow:
    def __init__(self, app, title, config_key, default_w, default_h):
        self.app = app
        self.title = title
        self.config_key = config_key
        self.default_w = default_w
        self.default_h = default_h
        self.window = None

    def show(self, force_open=False):
        if self.window and self.window.winfo_exists():
            if self.window.state() == "withdrawn":
                self.window.deiconify()
                self.window.attributes("-alpha", self.app.current_alpha)
                self.window.lift()
                self.refresh(force=True) # Immediate update on show
                return
            if force_open:
                self.window.lift()
                self.refresh(force=True) # Immediate update on show
                return
            self.close()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(self.title)
        
        saved_x = self.app.config.get(self.config_key, "x", fallback=None)
        saved_y = self.app.config.get(self.config_key, "y", fallback=None)
        w = self.app.config.getint(self.config_key, "width", fallback=self.default_w)
        h = self.app.config.getint(self.config_key, "height", fallback=self.default_h)

        x = int(saved_x) if saved_x else 100
        y = int(saved_y) if saved_y else 100
        
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.configure(bg=WINDOW_BG)
        self.window.overrideredirect(True)
        self.window.attributes("-alpha", self.app.current_alpha)
        
        self.window.bind("<Button-1>", self.click_window)
        self.window.bind("<B1-Motion>", self.drag_window)
        
        border = tk.Frame(self.window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(border, bg=WINDOW_BG)
        self.inner.pack(fill=tk.BOTH, expand=True)

        self.title_bar = tk.Frame(self.inner, bg=PANEL_DARK, height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.bind("<Button-1>", self.click_window)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
        
        tk.Label(self.title_bar, text=self.title.upper(), bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Label(self.title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.close())
        
        self.content_container = tk.Frame(self.inner, bg=WINDOW_BG, padx=5, pady=5)
        self.content_container.pack(fill=tk.BOTH, expand=True)

        self.resize_handle = tk.Label(self.inner, text="◢", bg=WINDOW_BG, fg=BORDER_COLOR, font=("Segoe UI", 8), cursor="size_nw_se")
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<Button-1>", lambda e: self.app.init_resize_popout(e, self.window, self.default_w, self.default_h))
        self.resize_handle.bind("<B1-Motion>", lambda e: self.app.do_resize_popout(e, self.window, self.default_w, self.default_h))
        self.resize_handle.bind("<ButtonRelease-1>", lambda e: self.app.save_size(e))

    def close(self):
        if self.window:
            self.app.save_config()
            self.window.destroy()
            self.window = None

    def click_window(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def drag_window(self, event):
        if not self.window: return
        x = self.window.winfo_pointerx() - self._offsetx
        y = self.window.winfo_pointery() - self._offsety
        x, y = apply_snapping(self.window, x, y)
        self.window.geometry(f"+{x}+{y}")

    def refresh(self, force=False):
        pass
