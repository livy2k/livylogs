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
        self.chat_message = tk.StringVar()
        self._last_msg_ts = 0
        self._image_cache = [] # Keep references to PhotoImage objects
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

        # Force refresh verification status from config just in case it changed elsewhere
        self.is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
        self.relay_token = self.app.config.get("DiscordRelay", "relay_token", fallback="")

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
            header_frame = tk.Frame(main_frame, bg=WINDOW_BG)
            header_frame.pack(fill=tk.X)
            
            tk.Label(header_frame, text="RELAY ACTIVE", bg=WINDOW_BG, fg="#43B581", font=("Lilita One", 14)).pack(side=tk.LEFT)
            
            tk.Button(header_frame, text="UNLINK", command=self.unlink_account, 
                      bg="#444", fg="white", font=("Segoe UI", 8), padx=10).pack(side=tk.RIGHT)

            # Chat / Pulse Log View
            log_frame = tk.Frame(main_frame, bg=PANEL_DARK, highlightbackground="#333", highlightthickness=1)
            log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            self.log_text = tk.Text(log_frame, bg="#121212", fg="#dcddde", font=("Consolas", 9), 
                                  padx=10, pady=10, borderwidth=0, highlightthickness=0, state=tk.DISABLED)
            self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg=PANEL_DARK)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.log_text.config(yscrollcommand=scrollbar.set)
            
            # Add tags for coloring
            self.log_text.tag_configure("timestamp", foreground="#72767d")
            self.log_text.tag_configure("system", foreground=ACCENT_BLUE)
            self.log_text.tag_configure("pulse", foreground="#ffffff")

            self._append_log("System", "Discord Relay connection active.")
            self._append_log("System", "Pulses will appear here as they are sent.")

            # Chat Input Area
            input_frame = tk.Frame(main_frame, bg=WINDOW_BG)
            input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

            self.chat_entry = tk.Entry(input_frame, textvariable=self.chat_message, bg="#1a1a1a", fg="white",
                                      insertbackground="white", font=("Segoe UI", 9), borderwidth=1, relief=tk.FLAT)
            self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
            self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())
            self.chat_entry.bind("<Control-v>", lambda e: self._handle_paste())

            send_btn = tk.Button(input_frame, text="SEND", command=self.send_chat_message,
                                bg=ACCENT_BLUE, fg="white", font=("Lilita One", 8), padx=10)
            send_btn.pack(side=tk.RIGHT)

            # Start message polling
            self._start_polling()

    def _start_polling(self):
        if not self.is_verified or getattr(self, '_polling_started', False):
            return
            
        self._polling_started = True
        def _poll_loop():
            while self.window and self.window.winfo_exists() and self.is_verified:
                try:
                    self._fetch_messages()
                except: pass
                time.sleep(5) # Poll every 5 seconds
            self._polling_started = False

        threading.Thread(target=_poll_loop, daemon=True).start()

    def _handle_paste(self):
        """Handle clipboard paste, checking for images."""
        from PIL import ImageGrab, Image, ImageTk
        import io
        import base64

        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                # It's an image!
                self._send_image(img)
                return "break" # Prevent default paste
        except Exception as e:
            print(f"Paste error: {e}")
        
        return None # Continue with default paste

    def _send_image(self, img):
        """Resize, display and send image to relay."""
        from PIL import Image, ImageTk
        import io
        import base64
        import threading

        # Resize for display
        display_img = img.copy()
        max_size = (300, 300)
        display_img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(display_img)
        self._image_cache.append(photo) # Prevent GC
        
        # Display in log
        self._append_log("You", "[Image]", image=photo)
        
        # Prepare for sending
        def _bg_send():
            try:
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                base_url = getattr(self.app, 'discord_relay_url', None)
                if base_url: base_url = base_url.get().rstrip('/')
                else: base_url = CENTRAL_BOT_API_URL.rstrip('/')
                
                url = f"{base_url}/relay"
                requests.post(url, json={
                    "app_id": self.app_id, 
                    "image_data": img_str, 
                    "relay_token": self.relay_token
                }, timeout=10)
            except Exception as e:
                self.window.after(0, lambda: self._append_log("System", f"Image send error: {e}"))

        threading.Thread(target=_bg_send, daemon=True).start()

    def _fetch_messages(self):
        if not self.is_verified: return
        
        base_url = getattr(self.app, 'discord_relay_url', None)
        if base_url: base_url = base_url.get().rstrip('/')
        else: base_url = CENTRAL_BOT_API_URL.rstrip('/')
        
        url = f"{base_url}/messages"
        params = {"app_id": self.app_id, "relay_token": self.relay_token}
        resp = requests.get(url, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                messages = data.get("messages", [])
                for msg in messages:
                    ts = msg.get("timestamp", 0)
                    if ts > self._last_msg_ts:
                        author = msg.get("author")
                        content = msg.get("content")
                        attachments = msg.get("attachments", [])
                        
                        if attachments:
                            for att in attachments:
                                self.window.after(0, lambda a=author, u=att: self._fetch_and_display_image(a, u))
                        
                        if content:
                            self.window.after(0, lambda a=author, c=content: self._append_log(a, c))
                        
                        self._last_msg_ts = ts

    def _fetch_and_display_image(self, author, url):
        """Fetch image from URL and display in log."""
        from PIL import Image, ImageTk
        import io
        import requests

        def _bg_fetch():
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    
                    # Resize for display
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    self._image_cache.append(photo)
                    
                    self.window.after(0, lambda: self._append_log(author, "[Image]", image=photo))
            except: pass

        threading.Thread(target=_bg_fetch, daemon=True).start()

    def send_chat_message(self):
        msg = self.chat_message.get().strip()
        if not msg: return
        
        self.chat_message.set("")
        # Add to local log immediately
        self._append_log("You", msg)
        
        # Send to relay (reusing send_pulse logic but without the PULSE prefix)
        self._send_to_relay(msg)

    def _send_to_relay(self, msg):
        relay_app_id = getattr(self.app, 'app_id', self.app_id)
        def _bg_send():
            try:
                base_url = getattr(self.app, 'discord_relay_url', None)
                if base_url: base_url = base_url.get().rstrip('/')
                else: base_url = CENTRAL_BOT_API_URL.rstrip('/')
                
                url = f"{base_url}/relay"
                requests.post(url, json={"app_id": relay_app_id, "message": msg, "relay_token": self.relay_token}, timeout=5)
            except: pass
        threading.Thread(target=_bg_send, daemon=True).start()

    def _append_log(self, sender, message, image=None):
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            return
            
        self.log_text.config(state=tk.NORMAL)
        ts = time.strftime("[%H:%M:%S] ")
        self.log_text.insert(tk.END, ts, "timestamp")
        
        if sender == "System":
            self.log_text.insert(tk.END, f"{message}\n", "system")
        elif sender == "App" or sender == "You":
            self.log_text.insert(tk.END, f"{sender}: ", "pulse")
            if image:
                self.log_text.image_create(tk.END, image=image)
                self.log_text.insert(tk.END, "\n")
            else:
                self.log_text.insert(tk.END, f"{message}\n", "pulse")
        else:
            # Discord message
            self.log_text.insert(tk.END, f"{sender}: ", "system")
            if image:
                self.log_text.image_create(tk.END, image=image)
                self.log_text.insert(tk.END, "\n")
            elif message == "[Image]":
                 # Fallback if text message is just "[Image]" and we have no image object
                 self.log_text.insert(tk.END, "[Image loading...]\n", "pulse")
            else:
                self.log_text.insert(tk.END, f"{message}\n", "pulse")
            
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Force message polling to start if it hasn't already (and we are verified)
        if self.is_verified and not getattr(self, '_polling_started', False):
            self._start_polling()

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
                        # Explicitly set last_discord_pulse_time to 0 to trigger a pulse soon
                        self.app.last_discord_pulse_time = 0
                        
                    self.app.save_config()
                    # Rebuild to show the Linked UI
                    self.window.after(0, lambda: [
                        self._finalize_ui_state(), 
                        self.refresh(force=True),
                        self.chat_entry.focus_set() if hasattr(self, 'chat_entry') else None
                    ])
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
            
        # UI Feedback
        self._append_log("App", msg)
            
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
            # Check if verified status changed since last build
            current_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
            if force or getattr(self, '_last_built_verified', None) != current_verified or not self.content_container.winfo_children():
                self.is_verified = current_verified
                self._build_ui()

    def save_config(self):
        super().save_config()
