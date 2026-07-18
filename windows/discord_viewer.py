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

            self.code_entry = tk.Entry(main_frame, textvariable=self.verification_code, bg="#1a1a1a", fg=ACCENT_BLUE, 
                                     font=("Consolas", 18, "bold"), justify="center", insertbackground="white", width=10)
            self.code_entry.pack(pady=10)
            self.code_entry.bind("<Return>", lambda e: self.perform_verification())

            self.verify_btn = tk.Button(main_frame, text="VERIFY & LINK", command=self.perform_verification, 
                                      bg=ACCENT_RED, fg="white", font=("Lilita One", 10), padx=20, pady=5)
            self.verify_btn.pack(pady=20)

            self.status_label = tk.Label(main_frame, text="", bg=WINDOW_BG, fg="white", font=("Segoe UI", 8))
            self.status_label.pack()
        else:
            # Linked UI
            tk.Label(main_frame, text="RELAY ACTIVE", bg=WINDOW_BG, fg="#43B581", font=("Lilita One", 14)).pack(pady=(0, 10))
            
            tk.Label(main_frame, text="Your app is successfully linked to Discord.\nCombat pulses are being sent to your channel.", 
                     bg=WINDOW_BG, fg="white", font=("Segoe UI", 9), justify=tk.CENTER).pack(pady=20)

            tk.Button(main_frame, text="UNLINK ACCOUNT", command=self.unlink_account, 
                      bg="#444", fg="white", font=("Segoe UI", 8)).pack(side=tk.BOTTOM, pady=10)

    def perform_verification(self):
        # Refresh app_id if it was missing during init
        if not getattr(self.app, 'app_id', None):
            self.app_id = getattr(self.app, 'app_id', self.app_id)
        else:
            self.app_id = self.app.app_id

        code = self.verification_code.get().strip().upper()
        if len(code) != 6:
            self.status_label.config(text="Code must be 6 characters.", fg="red")
            return

        self.status_label.config(text="Verifying...", fg="white")
        
        def _bg_verify():
            try:
                url = f"{CENTRAL_BOT_API_URL}/verify"
                resp = requests.post(url, json={"code": code, "app_id": self.app_id}, timeout=10)
                if resp.status_code == 200:
                    payload = resp.json()
                    self.relay_token = payload.get("relay_token", "")
                    self.is_verified = True
                    self.app.config.set("DiscordRelay", "is_verified", "True")
                    self.app.config.set("DiscordRelay", "relay_token", self.relay_token)
                    self.app.save_config()
                    self.window.after(0, self._build_ui)
                else:
                    msg = resp.json().get("message", "Invalid code.")
                    self.window.after(0, lambda: self.status_label.config(text=msg, fg="red"))
            except Exception as e:
                self.window.after(0, lambda: self.status_label.config(text=f"Connection Error: {e}", fg="red"))

        threading.Thread(target=_bg_verify, daemon=True).start()

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
                url = f"{CENTRAL_BOT_API_URL}/relay"
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
            self._build_ui()

    def save_config(self):
        super().save_config()
