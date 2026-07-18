import tkinter as tk
from windows.base_window import BasePopoutWindow
import requests
import os
import time
import threading
from constants import WINDOW_BG, PANEL_DARK, ACCENT_BLUE, ACCENT_RED, CENTRAL_BOT_API_URL

class DiscordViewerWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Discord Relay", "DiscordViewerWindow", 400, 300, centered=True)
        self.is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
        self.relay_token = self.app.config.get("DiscordRelay", "relay_token", fallback="")
        self.verification_code = tk.StringVar()
        self.app_id = getattr(self.app, 'app_id', None)
        if not self.app_id:
            import uuid
            self.app_id = str(uuid.uuid4()) # Fallback for absolute safety during init

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window:
            return

        if not self.content_container.winfo_children():
            self._build_ui()

    def _build_ui(self):
        self._last_built_verified = self.is_verified
        for widget in self.content_container.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        if not self.is_verified:
            # Verification UI
            tk.Label(main_frame, text="LINK DISCORD RELAY", bg=WINDOW_BG, fg=ACCENT_RED, font=("Lilita One", 14)).pack(pady=(0, 10))
            
            instructions = (
                "1. Invite our Bot to your Discord server.\n"
                "2. Go to your target channel.\n"
                "3. Type `/verify` in that channel.\n"
                "4. Enter the 6-digit code below:"
            )
            tk.Label(main_frame, text=instructions, bg=WINDOW_BG, fg="white", font=("Segoe UI", 9), justify=tk.LEFT).pack(pady=10)

            # Container for entry and status to keep them together during updates
            self.input_container = tk.Frame(main_frame, bg=WINDOW_BG)
            self.input_container.pack(pady=10)

            self.code_entry = tk.Entry(self.input_container, textvariable=self.verification_code, bg="#1a1a1a", fg=ACCENT_BLUE, 
                                     font=("Consolas", 18, "bold"), justify="center", insertbackground="white", width=10)
            self.code_entry.pack()
            
            # Clear any previous value to ensure fresh entry
            self.verification_code.set("")
            self.code_entry.focus_set()
            
            self.code_entry.bind("<Return>", lambda e: self.perform_verification())
            
            # Add copy-paste support
            self._setup_entry_bindings(self.code_entry)

            self.verify_btn = tk.Button(main_frame, text="VERIFY & LINK", command=self.perform_verification, 
                                      bg=ACCENT_RED, fg="white", font=("Lilita One", 10), padx=20, pady=5)
            self.verify_btn.pack(pady=10)

            self.status_label = tk.Label(main_frame, text="", bg=WINDOW_BG, fg="white", font=("Segoe UI", 8))
            self.status_label.pack()
        else:
            # Linked UI
            tk.Label(main_frame, text="RELAY ACTIVE", bg=WINDOW_BG, fg="#43B581", font=("Lilita One", 14)).pack(pady=(0, 10))
            
            tk.Label(main_frame, text="Your app is successfully linked to Discord.\nCombat pulses are being sent to your channel.", 
                     bg=WINDOW_BG, fg="white", font=("Segoe UI", 9), justify=tk.CENTER).pack(pady=20)

            tk.Button(main_frame, text="UNLINK ACCOUNT", command=self.unlink_account, 
                      bg="#444", fg="white", font=("Segoe UI", 8)).pack(side=tk.BOTTOM, pady=10)

    def _setup_entry_bindings(self, entry):
        def show_menu(event):
            menu = tk.Menu(self.window, tearoff=0, bg=PANEL_DARK, fg="white", activebackground=ACCENT_BLUE)
            menu.add_command(label="Paste", command=lambda: entry.event_generate("<<Paste>>"))
            menu.add_command(label="Copy", command=lambda: entry.event_generate("<<Copy>>"))
            menu.add_command(label="Select All", command=lambda: [entry.focus_set(), entry.selection_range(0, tk.END)])
            menu.post(event.x_root, event.y_root)

        entry.bind("<Button-3>", show_menu)
        # Standard Tkinter usually handles Ctrl+V / Ctrl+C, but let's ensure focus
        entry.bind("<Control-v>", lambda e: entry.event_generate("<<Paste>>"))
        entry.bind("<Control-c>", lambda e: entry.event_generate("<<Copy>>"))
        entry.bind("<Control-a>", lambda e: [entry.selection_range(0, tk.END), "break"])

    def perform_verification(self):
        # Prevent multiple simultaneous verification attempts
        if getattr(self, '_verifying', False):
            return
            
        # Refresh app_id if it was missing during init
        if not getattr(self.app, 'app_id', None):
            self.app_id = getattr(self.app, 'app_id', self.app_id)
        else:
            self.app_id = self.app.app_id

        code = self.verification_code.get().strip().upper()
        if len(code) != 6:
            self.status_label.config(text="Code must be 6 characters.", fg="red")
            return

        self._verifying = True
        self.verify_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Verifying...", fg="white")
        
        def _bg_verify():
            try:
                # Use configured relay URL
                base_url = getattr(self.app, 'discord_relay_url', None)
                if base_url:
                    base_url = base_url.get().rstrip('/')
                else:
                    base_url = CENTRAL_BOT_API_URL.rstrip('/')
                
                url = f"{base_url}/verify"
                resp = requests.post(url, json={"code": code, "app_id": self.app_id}, timeout=10)
                
                def _finalize_ui():
                    self._verifying = False
                    if self.window and self.window.winfo_exists():
                        self.verify_btn.config(state=tk.NORMAL)

                if resp.status_code == 200:
                    payload = resp.json()
                    self.relay_token = payload.get("relay_token", "")
                    self.is_verified = True
                    self.app.config.set("DiscordRelay", "is_verified", "True")
                    self.app.config.set("DiscordRelay", "relay_token", self.relay_token)
                    
                    # Also enable the relay automatically upon verification
                    if hasattr(self.app, 'discord_relay_enabled'):
                        self.app.discord_relay_enabled.set(True)
                        self.app.config.set("Discord", "relay_enabled", "True")
                        
                    self.app.save_config()
                    # Rebuild to show the Linked UI
                    self.window.after(0, lambda: [self._finalize_ui_state(), self._build_ui()])
                else:
                    try:
                        msg = resp.json().get("message", "Invalid code.")
                    except:
                        msg = f"Error: {resp.status_code}"
                    self.window.after(0, lambda m=msg: [self._finalize_ui_state(), self.status_label.config(text=m, fg="red")])
            except Exception as e:
                # Improve error message for connection issues
                err_msg = str(e)
                if "ConnectionRefusedError" in err_msg or "Failed to establish a new connection" in err_msg:
                    err_msg = "Relay Server offline or URL incorrect. Check Options."
                self.window.after(0, lambda err=err_msg: [self._finalize_ui_state(), self.status_label.config(text=f"Connection Error: {err}", fg="red")])

        threading.Thread(target=_bg_verify, daemon=True).start()

    def _finalize_ui_state(self):
        self._verifying = False
        if self.window and self.window.winfo_exists():
            try:
                self.verify_btn.config(state=tk.NORMAL)
            except: pass

    def unlink_account(self):
        self.is_verified = False
        self.relay_token = ""
        self.app.config.set("DiscordRelay", "is_verified", "False")
        self.app.config.set("DiscordRelay", "relay_token", "")
        self.app.save_config()
        self._build_ui()

    def send_pulse(self, msg):
        """Send a summarized combat pulse to the central relay bot."""
        if not self.is_verified:
            return
            
        # Ensure app_id is current
        relay_app_id = getattr(self.app, 'app_id', self.app_id)

        def _bg_send():
            try:
                # Use configured relay URL
                base_url = getattr(self.app, 'discord_relay_url', None)
                if base_url:
                    base_url = base_url.get().rstrip('/')
                else:
                    base_url = CENTRAL_BOT_API_URL.rstrip('/')
                
                url = f"{base_url}/relay"
                requests.post(
                    url,
                    json={"app_id": relay_app_id, "message": msg, "relay_token": self.relay_token},
                    timeout=5
                )
            except:
                pass

        threading.Thread(target=_bg_send, daemon=True).start()

    def refresh(self, force=True):
        if self.window and self.window.winfo_exists():
            # Only rebuild if verified state changed or explicitly forced and UI empty
            if getattr(self, '_last_built_verified', None) != self.is_verified or not self.content_container.winfo_children():
                self._build_ui()

    def save_config(self):
        super().save_config()
