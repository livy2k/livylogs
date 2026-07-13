"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT,
    TITLE_GRADIENT_START, TITLE_GRADIENT_END
)
from utils import apply_snapping

class BasePopoutWindow:
    def __init__(self, app, title, config_key, default_w, default_h, centered=False, fixed_size=False, show_title=True):
        self.app = app
        self.title = title
        self.config_key = config_key
        self.default_w = default_w
        self.default_h = default_h
        self.centered = centered
        self.fixed_size = fixed_size
        self.show_title = show_title
        self.window = None

    def update_if_changed(self, label, new_value):
        try:
            if label.cget("text") != str(new_value):
                label.config(text=str(new_value))
        except: pass

    def show(self, force_open=False):
        if self.window and self.window.winfo_exists():
            if self.window.state() == "withdrawn":
                self.window.deiconify()
                if self.window.attributes("-alpha") != self.app.current_alpha:
                    self.window.attributes("-alpha", self.app.current_alpha)
                self.window.lift()
                return
            if force_open:
                self.window.lift()
                return
            self.close()
            return

        # Use a hidden dummy parent to hide from taskbar
        if not hasattr(self.app, '_taskbar_dummy'):
            self.app._taskbar_dummy = tk.Toplevel(self.app.root)
            self.app._taskbar_dummy.withdraw()
            self.app._taskbar_dummy.overrideredirect(True)

        self.window = tk.Toplevel(self.app._taskbar_dummy)
        self.window.title(self.title)
        
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
        
        # Set window icon (should be inherited from root, but explicit for safety)
        try:
            if hasattr(self.app, '_icon_photo'):
                self.window.iconphoto(False, self.app._icon_photo)
        except: pass

        # Explicitly hide from taskbar using ToolWindow style if parent trick didn't suffice
        try:
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = self.window.winfo_id()
            if hwnd:
                import ctypes
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW)
        except: pass
        
        self.window.attributes("-alpha", self.app.current_alpha)
        if self.app.always_on_top:
            self.window.attributes("-topmost", True)
        
        if not self.fixed_size:
            self.window.bind("<Configure>", self.on_configure)
        
        # Enable basic copy/select all globally for the window
        self.window.bind("<Control-c>", self._on_global_copy)
        self.window.bind("<Control-a>", self._on_global_select_all)
        
        border = tk.Frame(self.window, bg=BORDER_COLOR, padx=0, pady=0)
        border.pack(fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(border, bg=WINDOW_BG)
        self.inner.pack(fill=tk.BOTH, expand=True)

        # Content container
        # Reduced padding to 0,0 for maximum space
        self.content_container = tk.Frame(self.inner, bg=WINDOW_BG, padx=0, pady=0)
        self.content_container.pack(fill=tk.BOTH, expand=True)

        # Gradient Title Bar
        if self.show_title:
            self.title_bar = tk.Canvas(self.inner, bg=TITLE_GRADIENT_END, height=20, highlightthickness=0)
            self.title_bar.pack(side=tk.TOP, fill=tk.X, before=self.content_container)
            self.title_bar.bind("<Button-1>", self.click_window)
            self.title_bar.bind("<B1-Motion>", self.drag_window)
            self.title_bar.bind("<ButtonRelease-1>", self.release_window)
            
            # Draw subtle gradient
            self.title_bar.bind("<Configure>", self._draw_title_gradient)
            
            # Close Button on the far right
            close_btn = tk.Label(self.title_bar, text="✕", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=8)
            self.title_bar.create_window(self.window.winfo_width() - 5 if self.window else self.default_w - 5, 10, window=close_btn, anchor="e", tags="close_btn")
            close_btn.bind("<Button-1>", lambda e: self.close())
            close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
            close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))
            
            # If title is empty or not provided, we just have the bar
            if self.title and self.title != "LIVIUS":
                self.title_label = tk.Label(self.title_bar, text=self.title.upper(), bg=TITLE_GRADIENT_START, fg=TEXT_PRIMARY, font=("Segoe UI", 8, "bold"))
                self.title_bar.create_window(10, 10, window=self.title_label, anchor="w", tags="title_label")
                self.title_label.bind("<Button-1>", self.click_window)
                self.title_label.bind("<B1-Motion>", self.drag_window)
                self.title_label.bind("<ButtonRelease-1>", self.release_window)
        else:
            # If no title bar, make the content container draggable
            self.content_container.bind("<Button-1>", self.click_window)
            self.content_container.bind("<B1-Motion>", self.drag_window)
            self.content_container.bind("<ButtonRelease-1>", self.release_window)
        

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
        # Update textures or layout if needed immediately
        self.refresh(force=True)

    def on_resize_end(self, e):
        self.app.is_interacting = False
        self._is_resizing = False
        self.app.save_size(e)
        try:
            self.app.save_config()
        except: pass
        self.app.refresh_ui_only(force=True)

    def on_configure(self, event):
        # Only suppress if we are explicitly resizing/interacting
        if getattr(self, "app", None) and self.app.is_interacting:
            self.app.last_interaction_time = __import__("time").time()

    def close(self):
        if self.window:
            try:
                self.app.save_config()
            except: pass
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
        try:
            self.app.save_config()
        except: pass
        self.app.refresh_ui_only(force=True)

    def refresh(self, force=False):
        pass

    def _on_global_copy(self, event=None):
        # Default behavior: try to copy from focused widget if it's a Text/Entry
        focused = self.window.focus_get()
        if isinstance(focused, (tk.Text, tk.Entry)):
            # Tkinter handles Ctrl-C for these by default, but we can force it
            try:
                content = ""
                if isinstance(focused, tk.Text):
                    if focused.tag_ranges("sel"):
                        content = focused.get("sel.first", "sel.last")
                elif isinstance(focused, tk.Entry):
                    if focused.selection_present():
                        content = focused.selection_get()
                
                if content:
                    self.window.clipboard_clear()
                    self.window.clipboard_append(content)
                    return "break"
            except: pass
        
        # If nothing specific is focused/selected, call window-specific copy
        self.copy_to_clipboard()
        return "break"

    def _on_global_select_all(self, event=None):
        focused = self.window.focus_get()
        if isinstance(focused, (tk.Text, tk.Entry)):
            if isinstance(focused, tk.Text):
                focused.tag_add("sel", "1.0", "end")
            elif isinstance(focused, tk.Entry):
                focused.selection_range(0, tk.END)
            return "break"
        return "break"

    def copy_to_clipboard(self):
        # To be overridden by subclasses
        pass

    def show_context_menu(self, event):
        if not hasattr(self, 'context_menu'):
            from constants import PANEL_DARK, TEXT_PRIMARY, ACCENT_BLUE
            self.context_menu = tk.Menu(self.window, tearoff=0, bg=PANEL_DARK, fg=TEXT_PRIMARY, activebackground=ACCENT_BLUE, borderwidth=1)
            self.context_menu.add_command(label="Copy", command=self._on_global_copy, accelerator="Ctrl+C")
            self.context_menu.add_command(label="Select All", command=self._on_global_select_all, accelerator="Ctrl+A")
        
        # Unmap previous instances if any
        self.context_menu.unpost()
        
        # Position and post the menu
        self.context_menu.post(event.x_root, event.y_root)
        
        # Win32 call to force menu to the very top. 
        # Using a slight delay to ensure the menu window is fully created and visible.
        def force_top():
            try:
                from constants import HWND_TOPMOST, SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW, user32
                import ctypes
                
                def enum_callback(hwnd, lparam):
                    class_name = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_name, 256)
                    if class_name.value == "#32768":
                        if user32.IsWindowVisible(hwnd):
                            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                                               SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                    return True

                enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_callback)
                user32.EnumWindows(enum_proc, 0)
            except: pass
            
            # Also ensure focus
            try:
                self.context_menu.focus_set()
            except: pass

        self.window.after(1, force_top)
        self.window.after(50, force_top)
        self.window.after(100, force_top)

    def _draw_title_gradient(self, event=None):
        if not self.title_bar: return
        w = self.title_bar.winfo_width()
        h = self.title_bar.winfo_height()
        if h == 0: h = 24
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
        # Reposition title label
        if hasattr(self, "title_label"):
            try:
                self.title_bar.coords(self.title_bar.find_withtag("title_label"), 10, h // 2)
            except:
                # If finding by tag fails, try using the widget itself or its window item
                pass
        
        # Update label background to match gradient start
        self.title_label.config(bg=TITLE_GRADIENT_START)
