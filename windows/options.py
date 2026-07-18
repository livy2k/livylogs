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
        super().__init__(app, "Options", "OptionsWindow", 400, 600, centered=True, fixed_size=False)
        self._is_broken = False

    def refresh(self, force=False):
        if self._is_broken:
            return
        if not self.window or self.window.state() == "withdrawn": return
        
        # Only rebuild the entire UI if it doesn't exist yet or if forced
        if force or len(self.content_container.winfo_children()) == 0:
            self.build_ui()
        
        # Update dynamic elements
        self.update_status_indicator()

    def build_ui(self):
        # Initial focus setup
        self.window.after(200, self._force_focus)
        
        # Initialize variables if needed
        if not hasattr(self, 'verification_code'):
            self.verification_code = tk.StringVar()

        # Update window height to accommodate new fields
        # if self.window:
        #     self.window.geometry("500x950")

        # Clear existing content just in case
        for child in self.content_container.winfo_children():
            child.destroy()

        # Transparency Slider
        tk.Label(self.content_container, text="TRANSPARENCY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(5, 2))
        alpha_scale = tk.Scale(self.content_container, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                              bg=WINDOW_BG, fg=TEXT_PRIMARY, highlightthickness=0, troughcolor=PANEL_DARK,
                              command=lambda val: [setattr(self.app, 'target_alpha', float(val)), 
                                                 self.app.root.attributes("-alpha", float(val)),
                                                 self.app.save_config()])
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
        # Discord Settings Section
        tk.Frame(self.content_container, height=1, bg=BORDER_COLOR).pack(fill=tk.X, pady=10)
        tk.Label(self.content_container, text="DISCORD RELAY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 8)).pack(anchor="w", pady=(0, 5))
        
        is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)

        if not is_verified:
            # Verification UI inside Options
            tk.Label(self.content_container, text="1. Run /verify in Discord\n2. Enter code below:", 
                     bg=WINDOW_BG, fg="white", font=("Segoe UI", 8), justify=tk.LEFT).pack(anchor="w", pady=2)
            
            v_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
            v_frame.pack(fill=tk.X, pady=5)

            self.code_entry = tk.Entry(v_frame, textvariable=self.verification_code, bg="#1a1a1a", fg=ACCENT_BLUE, 
                                     font=("Consolas", 14, "bold"), justify="center", insertbackground="white")
            self.code_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
            self.code_entry.bind("<Button-1>", lambda e: [self._force_focus(), self.code_entry.focus_set()])
            
            self.verify_btn = tk.Button(v_frame, text="LINK", command=self.perform_verification, 
                                      bg=ACCENT_RED, fg="white", font=("Lilita One", 9), padx=10)
            self.verify_btn.pack(side=tk.RIGHT)

            self.status_label = tk.Label(self.content_container, text="", bg=WINDOW_BG, fg="white", font=("Segoe UI", 7))
            self.status_label.pack(anchor="w")
        else:
            # Linked UI inside Options
            l_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
            l_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(l_frame, text="RELAY ACTIVE", bg=PANEL_DARK, fg="#43B581", font=("Lilita One", 10)).pack(side=tk.LEFT)
            
            tk.Button(l_frame, text="UNLINK", command=self.unlink_account, 
                      bg="#444", fg="white", font=("Segoe UI", 8), padx=10).pack(side=tk.RIGHT)

        add_check("ENABLE DISCORD RELAY (10s)", self.app.discord_relay_enabled, self.app.save_config)

        tk.Label(self.content_container, text="Character Relay ID:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w")
        id_label = tk.Label(self.content_container, text=getattr(self.app, 'app_id', 'N/A'), bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Consolas", 8), pady=5)
        id_label.pack(fill=tk.X, pady=(0, 5))

        tk.Label(self.content_container, text="Relay API URL:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w")
        self.url_entry = tk.Entry(self.content_container, textvariable=self.app.discord_relay_url, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Consolas", 8))
        self.url_entry.pack(fill=tk.X, pady=(2, 5))
        self.url_entry.bind("<Button-1>", lambda e: [self._force_focus(), self.url_entry.focus_set()])
        self.url_entry.bind("<FocusOut>", lambda e: self.app.save_config())
        self.url_entry.bind("<Return>", lambda e: self.app.save_config())

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
        self.char_entry = char_entry
        
        # Ensure focus and interactivity in borderless window
        char_entry.bind("<Button-1>", lambda e: [self._force_focus(), char_entry.focus_set()])
        
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
        
        # Also bind global paste to the entry specifically as a backup
        char_entry.bind("<Control-v>", self._on_global_paste)
        if hasattr(self, 'code_entry'):
            self.code_entry.bind("<Control-v>", self._on_global_paste)
        if hasattr(self, 'url_entry'):
            self.url_entry.bind("<Control-v>", self._on_global_paste)

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
            b.bind("<Button-1>", lambda e: [cmd(), self.refresh(force=True)])

        add_btn("SELECT COMBAT LOG", self.app.change_log_path)
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

    def _force_focus(self, event=None):
        """Force focus to the window and appropriate entry field."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            
            def _set_entry_focus():
                # Try to find which entry should get focus
                is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
                if not is_verified and hasattr(self, 'code_entry') and self.code_entry.winfo_exists():
                    self.code_entry.focus_set()
                elif is_verified:
                    # If verified, maybe focus the char name entry as a fallback
                    if hasattr(self, 'char_entry') and self.char_entry.winfo_exists():
                         # self.char_entry.focus_set() # Only if we want auto-focus on name
                         pass
            
            self.window.after(10, _set_entry_focus)

    def save_config(self):
        """Save window position/size to app config. Safe to call even if window is not open."""
        # Sync Relay Enabled state to config
        if not self.app.config.has_section("Discord"):
            self.app.config.add_section("Discord")
        self.app.config.set("Discord", "relay_enabled", str(self.app.discord_relay_enabled.get()))
        
        # Sync Relay URL to config
        if not self.app.config.has_section("DiscordRelay"):
            self.app.config.add_section("DiscordRelay")
        self.app.config.set("DiscordRelay", "relay_url", self.app.discord_relay_url.get())
        
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

    def perform_verification(self):
        # Prevent multiple simultaneous verification attempts
        if getattr(self, '_verifying', False):
            return
            
        code = self.verification_code.get().strip().upper()
        if len(code) != 6:
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Code must be 6 characters.", fg="red")
            return

        self._verifying = True
        if hasattr(self, 'verify_btn'):
            self.verify_btn.config(state=tk.DISABLED)
        if hasattr(self, 'status_label'):
            self.status_label.config(text="Verifying...", fg="white")
        
        def _bg_verify():
            import uuid
            try:
                # Use configured relay URL
                base_url = self.app.discord_relay_url.get().rstrip('/')
                app_id = getattr(self.app, 'app_id', str(uuid.uuid4()))
                
                import requests
                url = f"{base_url}/verify"
                resp = requests.post(url, json={"code": code, "app_id": app_id}, timeout=10)
                
                if resp.status_code == 200:
                    payload = resp.json()
                    relay_token = payload.get("relay_token", "")
                    
                    self.app.config.set("DiscordRelay", "is_verified", "True")
                    self.app.config.set("DiscordRelay", "relay_token", relay_token)
                    self.app.discord_relay_enabled.set(True)
                    self.app.config.set("Discord", "relay_enabled", "True")
                    self.app.save_config()
                    
                    self.window.after(0, lambda: [
                        self.status_label.config(text="Linked Successfully!", fg="#43B581"),
                        self.verify_btn.config(state=tk.NORMAL),
                        self.refresh()
                    ])
                    # Refresh viewer if open
                    if hasattr(self.app, 'discord_viewer_win') and self.app.discord_viewer_win:
                        self.window.after(500, self.app.discord_viewer_win.refresh)
                else:
                    try:
                        msg = resp.json().get("message", "Invalid code.")
                    except:
                        msg = f"Error: {resp.status_code}"
                    self.window.after(0, lambda m=msg: [self.status_label.config(text=m, fg="red"), self.verify_btn.config(state=tk.NORMAL)])
            except Exception as e:
                self.window.after(0, lambda err=str(e): [self.status_label.config(text=f"Error: {err}", fg="red"), self.verify_btn.config(state=tk.NORMAL)])
            finally:
                self._verifying = False

        import threading, uuid
        threading.Thread(target=_bg_verify, daemon=True).start()

    def unlink_account(self):
        self.app.config.set("DiscordRelay", "is_verified", "False")
        self.app.config.set("DiscordRelay", "relay_token", "")
        self.app.discord_relay_enabled.set(False)
        self.app.config.set("Discord", "relay_enabled", "False")
        self.app.save_config()
        self.refresh(force=True)
        if hasattr(self.app, 'discord_viewer_win') and self.app.discord_viewer_win:
            self.app.discord_viewer_win.refresh()
