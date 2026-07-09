import tkinter as tk
import os
import time
from tkinter import ttk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, 
    BUTTON_BG, BUTTON_HOVER, BORDER_COLOR
)
from windows.base_window import BasePopoutWindow

class OptionsWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Options", "OptionsWindow", 300, 480, centered=True, fixed_size=True)

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        # Only rebuild the entire UI if it doesn't exist yet
        if len(self.content_container.winfo_children()) == 0:
            self.build_ui()
        
        # Update dynamic elements
        self.update_status_indicator()

    def build_ui(self):
        # Clear existing content just in case
        for child in self.content_container.winfo_children():
            child.destroy()

        # Transparency Slider
        tk.Label(self.content_container, text="TRANSPARENCY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 2))
        alpha_scale = tk.Scale(self.content_container, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                              bg=WINDOW_BG, fg=TEXT_PRIMARY, highlightthickness=0, troughcolor=PANEL_DARK,
                              command=self.on_alpha_change)
        alpha_scale.set(self.app.target_alpha)
        alpha_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Prevent window dragging when interacting with the slider
        def stop_drag_propagation(e):
            self.app.is_interacting = True
            self.app.last_interaction_time = time.time()
            return # Let the scale handle its own event
            
        alpha_scale.bind("<Button-1>", stop_drag_propagation, add="+")
        alpha_scale.bind("<ButtonRelease-1>", lambda e: self.app.__setattr__('is_interacting', False), add="+")

        # Checkboxes
        def add_check(text, var, cmd=None):
            def combined_cmd():
                if cmd: cmd()
                self.refresh() # Update status if needed
            cb = tk.Checkbutton(self.content_container, text=text, variable=var, bg=WINDOW_BG, fg=TEXT_PRIMARY,
                               selectcolor=PANEL_DARK, activebackground=WINDOW_BG, activeforeground=TEXT_PRIMARY,
                               font=("Segoe UI", 9), command=combined_cmd)
            cb.pack(anchor="w", pady=2)

        add_check("DISABLE WARNINGS", self.app.disable_warnings, self.app.save_config)
        
        # Web Sync Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="WEB SYNC (not implemented currently)", bg=WINDOW_BG, fg="#888888", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 5))
        
        sync_cb = tk.Checkbutton(self.content_container, text="ENABLE SYNC", variable=self.app.enable_sync, bg=WINDOW_BG, fg="#888888",
                               selectcolor=PANEL_DARK, activebackground=WINDOW_BG, activeforeground="#888888",
                               font=("Segoe UI", 9), state=tk.DISABLED)
        sync_cb.pack(anchor="w", pady=2)
        
        tk.Label(self.content_container, text="CHARACTER NAME", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7, "bold")).pack(anchor="w")
        
        char_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        char_frame.pack(fill=tk.X, pady=(2, 8))
        
        char_entry = tk.Entry(char_frame, textvariable=self.app.char_name, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Segoe UI", 9))
        char_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def set_name_from_log():
            from utils import extract_character_id
            log_path = self.app.file_path_var.get()
            if log_path:
                detected_name = extract_character_id(log_path)
                if detected_name:
                    self.app.char_name.set(detected_name)
                    self.app.save_config()
                    self.refresh(force=True)

        set_btn = tk.Label(char_frame, text=" SET ", bg=ACCENT_BLUE, fg=TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), cursor="hand2")
        set_btn.pack(side=tk.RIGHT)
        set_btn.bind("<Button-1>", lambda e: set_name_from_log())
        
        def on_name_change(e):
            self.app.save_config()
            # Force refresh to update any UI elements that depend on character name
            self.refresh(force=True)

        char_entry.bind("<FocusOut>", on_name_change)
        char_entry.bind("<Return>", on_name_change)

        # Combat Log Path - simplified status
        tk.Label(self.content_container, text="LOG FILE STATUS", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10, 2))
        self.status_lbl = tk.Label(self.content_container, text="CHECKING...", bg=PANEL_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"), pady=5)
        self.status_lbl.pack(fill=tk.X, pady=(0, 5))
        self.update_status_indicator()

        # Buttons
        def add_btn(text, cmd):
            b = tk.Label(self.content_container, text=text, bg=BUTTON_BG, fg=TEXT_PRIMARY, 
                        font=("Segoe UI", 9, "bold"), pady=8, cursor="hand2")
            b.pack(fill=tk.X, pady=4)
            b.bind("<Enter>", lambda e: b.config(bg=BUTTON_HOVER))
            b.bind("<Leave>", lambda e: b.config(bg=BUTTON_BG))
            b.bind("<Button-1>", lambda e: [cmd(), self.refresh()])

        add_btn("SELECT LOG (MATCHING CHAR)", self.app.select_log_filtered)
        add_btn("BROWSE ALL LOGS", self.app.change_log_path)
        add_btn("RESET ALL DATA", lambda: self.app.analyze_log(manual=True))

    def close(self):
        super().close()
        self.app.on_options_closed()

    def update_status_indicator(self):
        if not hasattr(self, 'status_lbl'): return
        path_exists = bool(self.app.file_path_var.get() and os.path.exists(self.app.file_path_var.get()))
        status_text = "SELECTED" if path_exists else "NOT SELECTED"
        status_color = ACCENT_BLUE if path_exists else "#FF5555"
        self.status_lbl.config(text=status_text, fg=status_color)
        
    def on_alpha_change(self, val):
        self.app.target_alpha = float(val)
        self.app.current_alpha = float(val) # Immediate update for better feedback
        for win in self.app._get_managed_windows():
            win.attributes("-alpha", self.app.current_alpha)
        self.app.save_config()
