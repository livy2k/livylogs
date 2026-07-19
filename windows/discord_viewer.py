import tkinter as tk
from windows.base_window import BasePopoutWindow
import requests
import os
import time
import threading
from constants import WINDOW_BG, PANEL_DARK, ACCENT_BLUE, ACCENT_RED, CENTRAL_BOT_API_URL

class DiscordViewerWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Discord Relay", "DiscordViewerWindow", 500, 400, centered=True)
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
        
        # Ensure chat entry is focused when window is shown
        if self.window and self.window.winfo_exists():
            self.window.after(200, self._force_focus)

    def _build_ui(self):
        # Save old log content if it exists
        old_content = None
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            old_content = self.log_text.get("1.0", tk.END).strip()

        # Force refresh verification status from config
        self.is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
        self.relay_token = self.app.config.get("DiscordRelay", "relay_token", fallback="")
        self._last_built_verified = self.is_verified

        for widget in self.content_container.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        if not self.is_verified:
            # Simple prompt when not linked
            tk.Label(main_frame, text="DISCORD NOT LINKED", bg=WINDOW_BG, fg=ACCENT_RED, font=("Lilita One", 14)).pack(pady=(0, 10))
            
            msg = "Go to the Options window to link your Discord account."
            tk.Label(main_frame, text=msg, bg=WINDOW_BG, fg="white", font=("Segoe UI", 10)).pack(pady=20)

            tk.Button(main_frame, text="OPEN OPTIONS", command=self.app.open_options, 
                      bg=ACCENT_RED, fg="white", font=("Lilita One", 10), padx=20, pady=5).pack()
        else:
            # Refresh session-based tokens
            self.relay_token = self.app.config.get("DiscordRelay", "relay_token", fallback="")
            self.app_id = self.app.app_id
            
            # Linked UI
            header_frame = tk.Frame(main_frame, bg=WINDOW_BG)
            header_frame.pack(fill=tk.X)
            
            tk.Label(header_frame, text="RELAY ACTIVE", bg=WINDOW_BG, fg="#43B581", font=("Lilita One", 14)).pack(side=tk.LEFT)

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

            if old_content:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, old_content + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
                
                # Start polling immediately to catch up
                # and clear old content first if we want a fresh view
                self._last_msg_ts = 0 # Reset to fetch history
                self._start_polling()
            else:
                self._append_log("System", "Discord Relay connection active.")
                self._append_log("System", "Pulses will appear here as they are sent.")
                # Polling will start via _append_log logic

            # Chat Input Area
            input_frame = tk.Frame(main_frame, bg=WINDOW_BG)
            input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

            self.chat_entry = tk.Entry(input_frame, textvariable=self.chat_message, bg="#1a1a1a", fg="white",
                                      insertbackground="white", font=("Segoe UI", 9), borderwidth=1, relief=tk.FLAT)
            self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
            self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())
            self.chat_entry.bind("<Control-v>", lambda e: self._handle_paste())
            
            # Ensure it can get focus even in overrideredirect window
            self.chat_entry.bind("<Button-1>", self._force_focus)
            self.log_text.bind("<Button-1>", self._force_focus)
            main_frame.bind("<Button-1>", self._force_focus)
            self.content_container.bind("<Button-1>", self._force_focus)

            # Image attachment button
            self.img_btn = tk.Button(input_frame, text="📎", command=self._handle_paste,
                                   bg="#333", fg="white", font=("Segoe UI", 10), borderwidth=0, padx=5)
            self.img_btn.pack(side=tk.RIGHT, padx=(0, 5))
            
            # Add tooltip or help text if possible, but keep it simple
            # self.img_btn.bind("<Enter>", lambda e: ...) 

            send_btn = tk.Button(input_frame, text="SEND", command=self.send_chat_message,
                                bg=ACCENT_BLUE, fg="white", font=("Lilita One", 8), padx=10)
            send_btn.pack(side=tk.RIGHT)

            # Start message polling
            self._start_polling()

    def _force_focus(self, event=None):
        """Force focus to the window and chat entry."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            # On Windows, overrideredirect windows can be tricky with focus.
            # We use after to ensure it happens after the click event processes.
            def _set_entry_focus():
                if self.is_verified and hasattr(self, 'chat_entry'):
                    self.chat_entry.focus_set()
                elif not self.is_verified and hasattr(self, 'code_entry'):
                    self.code_entry.focus_set()
            self.window.after(10, _set_entry_focus)

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

    def _handle_paste(self, event=None):
        """Handle clipboard paste, checking for images."""
        from PIL import ImageGrab, Image
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                # It's an image!
                self._send_image(img)
                return "break" # Prevent default paste
        except Exception as e:
            print(f"Paste error: {e}")
        
        # Fallback to global text paste
        return self._on_global_paste(event)

    def _select_and_send_image(self):
        """Open file dialog to select and send an image."""
        from tkinter import filedialog
        from PIL import Image
        
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                self._send_image(img)
            except Exception as e:
                self._append_log("System", f"Error opening image: {e}")

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
                
                # Attribution
                author_name = self.app.char_name.get() or "Unknown"

                url = f"{base_url}/relay"
                requests.post(url, json={
                    "app_id": self.app_id, 
                    "image_data": img_str, 
                    "relay_token": self.relay_token,
                    "author_name": author_name
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
        try:
            resp = requests.get(url, params=params, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    messages = data.get("messages", [])
                    # Group messages by timestamp to keep chronological order
                    # and process content/attachments together.
                    grouped_messages = []
                    for msg in messages:
                        ts = msg.get("timestamp", 0)
                        if ts > self._last_msg_ts:
                            author = msg.get("author")
                            content = msg.get("content")
                            attachments = msg.get("attachments", [])
                            
                            # Log the receipt of attachments for debugging
                            if attachments:
                                print(f"[DiscordViewer] Found {len(attachments)} attachments in message from {author}")

                            # Pack all components of a single message to ensure they stay together
                            grouped_messages.append({
                                "ts": ts,
                                "author": author,
                                "content": content,
                                "attachments": attachments
                            })
                            
                    # Sort by timestamp (Discord API should return chronological, but safety first)
                    grouped_messages.sort(key=lambda x: x["ts"])
                    
                    for m in grouped_messages:
                        # Process attachments first, then content? 
                        # Actually, Discord usually shows content THEN attachments.
                        if m["content"]:
                            self.window.after(0, lambda a=m["author"], c=m["content"], t=m["ts"]: self._append_log(a, c, timestamp=t))
                        
                        if m["attachments"]:
                            for att in m["attachments"]:
                                self.window.after(0, lambda a=m["author"], u=att, t=m["ts"]: self._fetch_and_display_image(a, u, t))
                        
                        self._last_msg_ts = m["ts"]
            elif resp.status_code == 403:
                if not getattr(self, '_auth_error_shown', False):
                    self.window.after(0, lambda: self._append_log("System", "Error 403: Discord link is invalid or expired. Please relink in Options."))
                    self._auth_error_shown = True
                print(f"[DiscordViewer] Message fetch failed: 403 (Forbidden)")
                # Force refresh state from config in case it was unlinked elsewhere
                self.relay_token = self.app.config.get("DiscordRelay", "relay_token", fallback="")
                self.is_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
            else:
                if resp.status_code != 404: # Ignore not found errors if no messages yet
                    print(f"[DiscordViewer] Message fetch failed: {resp.status_code}")
        except Exception as e:
            print(f"[DiscordViewer] Error fetching messages: {e}")

    def _fetch_and_display_image(self, author, url, timestamp=None):
        """Fetch image from URL and display in log."""
        from PIL import Image, ImageTk
        import io
        import requests

        def _bg_fetch():
            try:
                # Add headers to mimic a browser, some CDNs block simple requests
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    img_data = io.BytesIO(resp.content)
                    img = Image.open(img_data)
                    
                    # Resize for display
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    self._image_cache.append(photo)
                    
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: self._append_log(author, "[Image]", image=photo, timestamp=timestamp))
                else:
                    print(f"[DiscordViewer] Failed to fetch image: {resp.status_code} for {url}")
            except Exception as e:
                print(f"[DiscordViewer] Error fetching image: {e}")

        threading.Thread(target=_bg_fetch, daemon=True).start()

    def send_chat_message(self):
        msg = self.chat_message.get().strip()
        if not msg: return
        
        self.chat_message.set("")
        
        # Check for command triggers
        if msg == "d911":
            self.app.d911_active = not self.app.d911_active
            status = "ENABLED" if self.app.d911_active else "DISABLED"
            self._append_log("System", f"Discord PvP Pulse {status} via command.")
            return
        if msg == "d999":
            self.app.generate_report_from_combatlog(is_test=False)
            return
        if msg == "dg001":
            self.app.generate_report_from_combatlog(is_test=True)
            return

        # Add to local log immediately
        self._append_log("You", msg)
        
        # Send to relay (reusing send_pulse logic but without the PULSE prefix)
        self._send_to_relay(msg)

    def _send_to_relay(self, msg):
        relay_app_id = getattr(self.app, 'app_id', self.app_id)
        author_name = self.app.char_name.get() or "Unknown"
        def _bg_send():
            try:
                base_url = getattr(self.app, 'discord_relay_url', None)
                if base_url: base_url = base_url.get().rstrip('/')
                else: base_url = CENTRAL_BOT_API_URL.rstrip('/')
                
                url = f"{base_url}/relay"
                requests.post(url, json={
                    "app_id": relay_app_id, 
                    "message": msg, 
                    "relay_token": self.relay_token,
                    "author_name": author_name
                }, timeout=10)
            except: pass
        threading.Thread(target=_bg_send, daemon=True).start()

    def _append_log(self, sender, message, image=None, timestamp=None):
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            return
            
        self.log_text.config(state=tk.NORMAL)
        
        # Determine timestamp string
        if timestamp:
            # If it's a float/int (from Discord), format it. If it's already a string, use it.
            if isinstance(timestamp, (int, float)):
                ts_str = time.strftime("[%m/%d %H:%M:%S] ", time.localtime(timestamp))
            else:
                ts_str = f"{timestamp} "
        else:
            ts_str = time.strftime("[%H:%M:%S] ")
            
        self.log_text.insert(tk.END, ts_str, "timestamp")
        
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

    def send_pulse(self, msg):
        """Send a summarized combat pulse to the central relay bot."""
        if not self.is_verified:
            return
            
        # UI Feedback
        self._append_log("App", msg)
            
        # Ensure app_id is current
        relay_app_id = getattr(self.app, 'app_id', self.app_id)
        author_name = self.app.char_name.get() or "Unknown"

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
                    json={
                        "app_id": relay_app_id, 
                        "message": msg, 
                        "relay_token": self.relay_token,
                        "author_name": author_name
                    },
                    timeout=5
                )
            except:
                pass

        threading.Thread(target=_bg_send, daemon=True).start()

    def refresh(self, force=True):
        if self.window and self.window.winfo_exists():
            # If we are currently resizing or dragging, don't rebuild the whole UI as it's destructive
            if getattr(self, "_is_resizing", False) or getattr(self, "_is_dragging", False):
                return

            # Check if verified status changed since last build
            current_verified = self.app.config.getboolean("DiscordRelay", "is_verified", fallback=False)
            
            # Smart Refresh: Only rebuild if verified status changed OR UI is empty
            # If force is True but verified status is the same, we DON'T rebuild the whole UI to avoid data loss
            # Subclasses of widgets will handle their own internal updates
            needs_rebuild = (getattr(self, '_last_built_verified', None) != current_verified) or not self.content_container.winfo_children()
            
            if needs_rebuild:
                self.is_verified = current_verified
                self._build_ui()
            elif force:
                # If forced but no rebuild needed, just ensure focus or other minor updates
                if self.is_verified:
                    self._force_focus()

    def save_config(self):
        super().save_config()
