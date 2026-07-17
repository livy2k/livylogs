"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
import os
import time
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, 
    BUTTON_BG, BUTTON_HOVER, BORDER_COLOR, ACCENT_RED
)
from windows.base_window import BasePopoutWindow

class OptionsWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Options", "OptionsWindow", 300, 600, centered=True, fixed_size=True)
        self._is_broken = False

    def refresh(self, force=False):
        if self._is_broken:
            return
        if not self.window or self.window.state() == "withdrawn": return
        
        # Only rebuild the entire UI if it doesn't exist yet
        if len(self.content_container.winfo_children()) == 0:
            self.build_ui()
        
        # Update dynamic elements
        self.update_status_indicator()

    def build_ui(self):
        # Update window height to accommodate new fields
        if self.window:
            self.window.geometry("300x700")

        # Clear existing content just in case
        for child in self.content_container.winfo_children():
            child.destroy()

        # Transparency Slider
        tk.Label(self.content_container, text="TRANSPARENCY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(5, 2))
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

        # State Duration Slider
        tk.Label(self.content_container, text="STATE DURATION (SEC)", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(5, 2))
        duration_scale = tk.Scale(self.content_container, from_=5, to=60, resolution=1, orient=tk.HORIZONTAL,
                                bg=WINDOW_BG, fg=TEXT_PRIMARY, highlightthickness=0, troughcolor=PANEL_DARK,
                                command=lambda val: [setattr(self.app, 'state_duration', int(val)), self.app.save_config()])
        duration_scale.set(self.app.state_duration)
        duration_scale.pack(fill=tk.X, pady=(0, 10))
        duration_scale.bind("<Button-1>", stop_drag_propagation, add="+")
        duration_scale.bind("<ButtonRelease-1>", lambda e: self.app.__setattr__('is_interacting', False), add="+")

        tk.Label(self.content_container, text="UNCLE RECON INTEL", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(5, 2))
        ai_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
        ai_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(ai_frame, text="CLOUD SOURCE: GOOGLE GEMINI", bg=PANEL_DARK, fg=ACCENT_RED, font=("Lilita One", 9)).pack(anchor="w")
        tk.Label(ai_frame, text="Status: ZERO-COST PERMANENT FREE TIER", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w", pady=(0, 10))

        tk.Label(ai_frame, text="GEMINI API KEY:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        
        key_frame = tk.Frame(ai_frame, bg=PANEL_DARK)
        key_frame.pack(fill=tk.X, pady=2)
        
        # Help link
        key_link = tk.Label(ai_frame, text="Get a free key at AI Studio (Click)", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 7, "underline"), cursor="hand2")
        key_link.pack(anchor="w", pady=(0, 5))
        import webbrowser
        key_link.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        # We need a way to edit the key
        from constants import AI_API_KEY
        self._temp_ai_key = tk.StringVar(value=AI_API_KEY)
        
        key_entry = tk.Entry(key_frame, textvariable=self._temp_ai_key, bg=WINDOW_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Consolas", 9), show="*")
        key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def save_key():
            new_key = self._temp_ai_key.get().strip()
            # Update constants (in memory for now, ideally persist to settings.ini)
            import constants
            constants.AI_API_KEY = new_key
            # Persist to settings.ini
            self.app.config["General"]["ai_api_key"] = new_key
            self.app.save_config()
            self.refresh(force=True)

        save_btn = tk.Label(key_frame, text=" SAVE ", bg=ACCENT_RED, fg=TEXT_PRIMARY, font=("Lilita One", 8), cursor="hand2")
        save_btn.pack(side=tk.RIGHT)
        save_btn.bind("<Button-1>", lambda e: save_key())

        # --- ADVANCED BOT SETUP (1-CODE) ---
        tk.Label(self.content_container, text="ADVANCED BOT SETUP", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(10, 2))
        adv_bot_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
        adv_bot_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(adv_bot_frame, text="Type /123 in your Discord channel", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w")
        
        setup_code_frame = tk.Frame(adv_bot_frame, bg=PANEL_DARK)
        setup_code_frame.pack(fill=tk.X, pady=2)

        self._adv_setup_code = tk.StringVar()
        code_entry = tk.Entry(setup_code_frame, textvariable=self._adv_setup_code, bg=WINDOW_BG, fg=ACCENT_BLUE, 
                              insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Consolas", 10, "bold"), justify="center")
        code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def run_adv_setup():
            code = self._adv_setup_code.get().strip()
            if len(code) != 6:
                status_lbl.config(text="CODE MUST BE 6 DIGITS", fg=ACCENT_RED)
                return
            
            status_lbl.config(text="CONNECTING...", fg=ACCENT_BLUE)
            
            def _bg_setup():
                try:
                    import requests
                    import hashlib
                    import base64
                    from cryptography.fernet import Fernet
                    
                    # Call the Advanced Bot's Web API
                    # Note: Using localhost 8081 as defined in discord_bot_advanced.py
                    url = "http://localhost:8081/adv_verify"
                    payload = {"code": code}
                    
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        user = data.get("user")
                        enc_token = data.get("token")
                        channel = data.get("channel")
                        
                        # Decrypt token to verify and store
                        key_src = code.encode() + b"LivyLogsSalt"
                        key = base64.urlsafe_b64encode(hashlib.sha256(key_src).digest())
                        f_dec = Fernet(key)
                        token = f_dec.decrypt(enc_token.encode()).decode()
                        
                        # Save to config
                        self.app.config["Discord"]["bot_token"] = token
                        self.app.config["Discord"]["channel_id"] = channel
                        self.app.config["Discord"]["relay_enabled"] = "True"
                        self.app.save_config()
                        
                        self.window.after(0, lambda: status_lbl.config(text=f"LINKED: {user}", fg="#43B581"))
                    else:
                        msg = resp.json().get("message", "INVALID CODE")
                        self.window.after(0, lambda: status_lbl.config(text=msg.upper(), fg=ACCENT_RED))
                    
                except Exception as e:
                    self.window.after(0, lambda: status_lbl.config(text=f"ERROR: {str(e)[:20]}", fg=ACCENT_RED))

            import threading
            threading.Thread(target=_bg_setup, daemon=True).start()

        setup_btn = tk.Label(setup_code_frame, text=" LINK ", bg=ACCENT_BLUE, fg=TEXT_PRIMARY, font=("Lilita One", 8), cursor="hand2")
        setup_btn.pack(side=tk.RIGHT)
        setup_btn.bind("<Button-1>", lambda e: run_adv_setup())
        
        status_lbl = tk.Label(adv_bot_frame, text="READY FOR SETUP", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 7))
        status_lbl.pack(anchor="w")

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
        add_check("CLASS COLORS", self.app.show_class_colors, lambda: [self.app.save_config(), self.app.refresh_ui_only(force=True)])
        add_check("ENABLE DISCORD RELAY (10s)", self.app.discord_relay_enabled, self.app.save_config)
        
        # Discord Settings Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="DISCORD RELAY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(0, 5))
        
        def open_discord_verify():
            self.app.open_discord_viewer()

        verify_btn = tk.Label(self.content_container, text="LINK DISCORD ACCOUNT", bg=ACCENT_RED, fg=TEXT_PRIMARY, 
                            font=("Lilita One", 9), pady=10, cursor="hand2")
        verify_btn.pack(fill=tk.X, pady=4)
        verify_btn.bind("<Button-1>", lambda e: open_discord_verify())

        tk.Label(self.content_container, text="Character Relay ID:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w")
        id_label = tk.Label(self.content_container, text=getattr(self.app, 'app_id', 'N/A'), bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Consolas", 8), pady=5)
        id_label.pack(fill=tk.X, pady=(0, 5))

        # Web Sync Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="WEB SYNC", bg=WINDOW_BG, fg="#888888", font=("Lilita One", 8)).pack(anchor="w", pady=(0, 5))
        
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

        set_btn = tk.Label(char_frame, text=" SET ", bg=ACCENT_RED, fg=TEXT_PRIMARY, font=("Lilita One", 8), cursor="hand2")
        set_btn.pack(side=tk.RIGHT)
        set_btn.bind("<Button-1>", lambda e: set_name_from_log())
        
        def on_name_change(e):
            self.app.save_config()
            # Force refresh to update any UI elements that depend on character name
            self.refresh(force=True)

        # Bind context menu
        self.window.bind("<Button-3>", self.show_context_menu)
        self.content_container.bind("<Button-3>", self.show_context_menu)
        char_entry.bind("<Button-3>", lambda e: "break") # Let entry handle its own or use ours? Actually entries have default.
        # But for consistency:
        char_entry.bind("<Button-3>", self.show_context_menu)

        char_entry.bind("<FocusOut>", on_name_change)
        char_entry.bind("<Return>", on_name_change)

        # Combat Log Path - simplified status
        tk.Label(self.content_container, text="LOG FILE STATUS", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(10, 2))
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

        add_btn("BROWSE ALL LOGS", self.app.change_log_path)
        add_btn("RESET ALL DATA", self.app.reset_all_data_manual)

        # Test Mode Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="TESTING", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(0, 5))
        
        test_btn = tk.Label(self.content_container, text="HOLD TO TEST DATA", bg=BUTTON_BG, fg=TEXT_PRIMARY, 
                           font=("Segoe UI", 9, "bold"), pady=12, cursor="hand2")
        test_btn.pack(fill=tk.X, pady=4)

        def on_press(e):
            test_btn.config(bg=ACCENT_BLUE, text="TESTING DATA...")
            self.app.toggle_test_mode(True)
            self.refresh()

        def on_release(e):
            test_btn.config(bg=BUTTON_BG, text="HOLD TO TEST DATA")
            self.app.toggle_test_mode(False)
            self.refresh()

        test_btn.bind("<Button-1>", on_press)
        test_btn.bind("<ButtonRelease-1>", on_release)
        test_btn.bind("<Enter>", lambda e: test_btn.config(bg=BUTTON_HOVER) if not self.app.test_mode.get() else None)
        test_btn.bind("<Leave>", lambda e: test_btn.config(bg=BUTTON_BG) if not self.app.test_mode.get() else None)
        
        tk.Label(self.content_container, text="Hold this button to temporarily switch to test log and simulate activity.", 
                 bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7), wraplength=250, justify="left").pack(anchor="w", pady=(2, 5))

    def save_config(self):
        """Save window position/size to app config. Safe to call even if window is not open."""
        # Sync Relay Enabled state to config
        if not self.app.config.has_section("Discord"):
            self.app.config.add_section("Discord")
        self.app.config.set("Discord", "relay_enabled", str(self.app.discord_relay_enabled.get()))
        
        if not self.window or not self.window.winfo_exists():
            return
        try:
            if self.config_key not in self.app.config:
                self.app.config[self.config_key] = {}
            self.app.config[self.config_key].update({
                "width": str(self.window.winfo_width()),
                "height": str(self.window.winfo_height()),
                "x": str(self.window.winfo_x()),
                "y": str(self.window.winfo_y())
            })
        except:
            pass

    def close(self):
        self._is_broken = False
        super().close()
        self.app.on_options_closed()

    def update_status_indicator(self):
        if not hasattr(self, 'status_lbl'): return
        path_exists = bool(self.app.file_path_var.get() and os.path.exists(self.app.file_path_var.get()))
        status_text = "SELECTED" if path_exists else "NOT SELECTED"
        status_color = ACCENT_RED if path_exists else "#FF5555"
        self.status_lbl.config(text=status_text, fg=status_color)

    def copy_to_clipboard(self):
        # Allow copying the current character name or log path
        name = self.app.char_name.get()
        path = self.app.file_path_var.get()
        text = f"Character: {name}\nLog Path: {path}"
        self.window.clipboard_clear()
        self.window.clipboard_append(text)

    def on_alpha_change(self, val):
        self.app.target_alpha = float(val)
        self.app.current_alpha = float(val) # Immediate update for better feedback
        for win in self.app._get_managed_windows():
            win.attributes("-alpha", self.app.current_alpha)
        self.app.save_config()
