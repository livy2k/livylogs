import tkinter as tk
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT,
    TITLE_GRADIENT_START, TITLE_GRADIENT_END
)
from utils import apply_snapping

class BasePopoutWindow:
    def __init__(self, app, title, config_key, default_w, default_h, centered=False, fixed_size=False):
        self.app = app
        self.title = title
        self.config_key = config_key
        self.default_w = default_w
        self.default_h = default_h
        self.centered = centered
        self.fixed_size = fixed_size
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

        if self.centered:
            sw = self.window.winfo_screenwidth()
            sh = self.window.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
        else:
            saved_x = self.app.config.get(self.config_key, "x", fallback=None)
            saved_y = self.app.config.get(self.config_key, "y", fallback=None)
            x = int(saved_x) if saved_x else 100
            y = int(saved_y) if saved_y else 100
        
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.configure(bg=WINDOW_BG)
        self.window.overrideredirect(True)
        self.window.attributes("-alpha", self.app.current_alpha)
        
        if not self.fixed_size:
            self.window.bind("<Button-1>", self.click_window)
            self.window.bind("<B1-Motion>", self.drag_window)
            self.window.bind("<ButtonRelease-1>", self.release_window)
            self.window.bind("<Configure>", self.on_configure)
        
        border = tk.Frame(self.window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(border, bg=WINDOW_BG)
        self.inner.pack(fill=tk.BOTH, expand=True)

        # Gradient Title Bar
        self.title_bar = tk.Canvas(self.inner, bg=TITLE_GRADIENT_END, height=32, highlightthickness=0)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.bind("<Button-1>", self.click_window)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
        self.title_bar.bind("<ButtonRelease-1>", self.release_window)
        
        # Draw subtle gradient
        self.title_bar.bind("<Configure>", self._draw_title_gradient)
        
        self.title_label = tk.Label(self.title_bar, text=self.title.upper(), bg=TITLE_GRADIENT_START, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"))
        # We'll place the label after the gradient is drawn or use transparent-like placement
        self.title_bar.create_window(10, 16, window=self.title_label, anchor="w")
        
        self.title_label.bind("<Button-1>", self.click_window)
        self.title_label.bind("<B1-Motion>", self.drag_window)
        self.title_label.bind("<ButtonRelease-1>", self.release_window)
        
        close_btn = tk.Label(self.title_bar, text="✕", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=("Segoe UI", 11), cursor="hand2", padx=10)
        self.title_bar.create_window(self.default_w - 5, 16, window=close_btn, anchor="e", tags="close_btn")
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))
        
        self.content_container = tk.Frame(self.inner, bg=WINDOW_BG, padx=8, pady=8)
        self.content_container.pack(fill=tk.BOTH, expand=True)

        if not self.fixed_size:
            self.resize_handle = tk.Label(self.inner, text="◢", bg=WINDOW_BG, fg=BORDER_COLOR, font=("Segoe UI", 8), cursor="size_nw_se")
            self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
            self.resize_handle.bind("<Button-1>", self.on_resize_start)
            self.resize_handle.bind("<B1-Motion>", self.on_resize_drag)
            self.resize_handle.bind("<ButtonRelease-1>", self.on_resize_end)
        
        self.refresh(force=True)

    def on_resize_start(self, e):
        self.app.is_interacting = True
        self.app.last_interaction_time = __import__("time").time()
        self._is_resizing = True
        self.app.init_resize_popout(e, self.window, self.default_w, self.default_h)

    def on_resize_drag(self, e):
        self.app.is_interacting = True
        self.app.last_interaction_time = __import__("time").time()
        self._is_resizing = True
        self.app.do_resize_popout(e, self.window, self.default_w, self.default_h)

    def on_resize_end(self, e):
        self.app.is_interacting = False
        self._is_resizing = False
        self.app.save_size(e)
        self.app.refresh_ui_only(force=True)

    def on_configure(self, event):
        # Only suppress if we are explicitly resizing/interacting
        if getattr(self, "app", None) and self.app.is_interacting:
            self.app.last_interaction_time = __import__("time").time()

    def close(self):
        if self.window:
            self.window.destroy()
            self.window = None

    def click_window(self, event):
        self.app.is_interacting = True
        self.app.last_interaction_time = tk.time.time() if hasattr(tk, "time") else __import__("time").time()
        self._offsetx = event.x
        self._offsety = event.y

    def drag_window(self, event):
        if not self.window: return
        self.app.is_interacting = True
        self.app.last_interaction_time = __import__("time").time()
        x = self.window.winfo_pointerx() - self._offsetx
        y = self.window.winfo_pointery() - self._offsety
        x, y = apply_snapping(self.window, x, y)
        self.window.geometry(f"+{x}+{y}")

    def release_window(self, event=None):
        self.app.is_interacting = False
        self.app.refresh_ui_only(force=True)

    def refresh(self, force=False):
        pass

    def _draw_title_gradient(self, event=None):
        if not self.title_bar: return
        w = self.title_bar.winfo_width()
        h = self.title_bar.winfo_height()
        self.title_bar.delete("gradient")
        
        # Simple vertical gradient
        for i in range(h):
            # Calculate color interpolation
            r1, g1, b1 = self.app.root.winfo_rgb(TITLE_GRADIENT_START)
            r2, g2, b2 = self.app.root.winfo_rgb(TITLE_GRADIENT_END)
            r = int(r1 + (r2 - r1) * (i / h)) // 256
            g = int(g1 + (g2 - g1) * (i / h)) // 256
            b = int(b1 + (b2 - b1) * (i / h)) // 256
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.title_bar.create_line(0, i, w, i, fill=color, tags="gradient")
        
        self.title_bar.tag_lower("gradient")
        
        # Reposition close button
        self.title_bar.coords("close_btn", w - 5, h // 2)
        # Update label background to match gradient start
        self.title_label.config(bg=TITLE_GRADIENT_START)
