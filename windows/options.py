import tkinter as tk
from tkinter import ttk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, 
    BUTTON_BG, BUTTON_HOVER, BORDER_COLOR
)
from windows.base_window import BasePopoutWindow

class OptionsWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Options", "OptionsWindow", 300, 480)

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        # No heavy refresh needed for options unless we want to reflect changes from elsewhere
        if not force and len(self.content_container.winfo_children()) > 0: return 
        
        # Clear existing content if forcing
        if force:
            for child in self.content_container.winfo_children():
                child.destroy()

        # Transparency Slider
        tk.Label(self.content_container, text="TRANSPARENCY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 2))
        alpha_scale = tk.Scale(self.content_container, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                              bg=WINDOW_BG, fg=TEXT_PRIMARY, highlightthickness=0, troughcolor=PANEL_DARK,
                              command=self.on_alpha_change)
        alpha_scale.set(self.app.target_alpha)
        alpha_scale.pack(fill=tk.X, pady=(0, 10))

        # Checkboxes
        def add_check(text, var, cmd=None):
            cb = tk.Checkbutton(self.content_container, text=text, variable=var, bg=WINDOW_BG, fg=TEXT_PRIMARY,
                               selectcolor=PANEL_DARK, activebackground=WINDOW_BG, activeforeground=TEXT_PRIMARY,
                               font=("Segoe UI", 9), command=cmd)
            cb.pack(anchor="w", pady=2)

        add_check("DISABLE WARNINGS", self.app.disable_warnings, self.app.save_config)
        
        # Web Sync Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="WEB SYNC", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 5))
        
        add_check("ENABLE SYNC", self.app.enable_sync, self.app.save_config)
        
        tk.Label(self.content_container, text="CHARACTER NAME", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7, "bold")).pack(anchor="w")
        char_entry = tk.Entry(self.content_container, textvariable=self.app.char_name, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Segoe UI", 9))
        char_entry.pack(fill=tk.X, pady=(2, 8))
        char_entry.bind("<FocusOut>", lambda e: self.app.save_config())
        
        tk.Label(self.content_container, text="API URL", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7, "bold")).pack(anchor="w")
        api_entry = tk.Entry(self.content_container, textvariable=self.app.api_url, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Segoe UI", 9))
        api_entry.pack(fill=tk.X, pady=(2, 8))
        api_entry.bind("<FocusOut>", lambda e: self.app.save_config())

        # Combat Log Path - ensure it's visible
        tk.Label(self.content_container, text="LOG FILE", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10, 2))
        path_lbl = tk.Label(self.content_container, textvariable=self.app.file_path_var, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 7), wraplength=230, justify=tk.LEFT)
        path_lbl.pack(fill=tk.X, pady=(0, 5))

        # Buttons
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)

        def add_btn(text, cmd):
            b = tk.Label(self.content_container, text=text, bg=BUTTON_BG, fg=TEXT_PRIMARY, 
                        font=("Segoe UI", 9, "bold"), pady=8, cursor="hand2")
            b.pack(fill=tk.X, pady=4)
            b.bind("<Enter>", lambda e: b.config(bg=BUTTON_HOVER))
            b.bind("<Leave>", lambda e: b.config(bg=BUTTON_BG))
            b.bind("<Button-1>", lambda e: cmd())

        add_btn("CHANGE LOG PATH", self.app.change_log_path)
        add_btn("RESET ALL DATA", lambda: self.app.analyze_log(manual=True))
        
    def on_alpha_change(self, val):
        self.app.target_alpha = float(val)
        self.app.current_alpha = float(val) # Immediate update for better feedback
        for win in self.app._get_managed_windows():
            win.attributes("-alpha", self.app.current_alpha)
        self.app.save_config()
