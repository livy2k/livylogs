"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import os
import time
import threading
import ctypes
import psutil

# Native Windows API via ctypes to avoid pywin32 import issues in some environments
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)

class GharvWindow(BasePopoutWindow):
    def __init__(self, app):
        # Large window for browser embedding, show_title=False to remove Tkinter title bar
        super().__init__(app, "Galaxy Harvester", "GharvWindow", 900, 650, fixed_size=False, show_title=False)
        self.url = "https://galaxyharvester.net/ghHome.py?"
        self.browser_proc = None
        self.browser_hwnd = None
        self.embedding_active = False

    def show(self, force_open=False):
        if self.window and self.window.winfo_exists():
            if self.window.state() == "withdrawn":
                self.window.deiconify()
                if self.window.attributes("-alpha") != self.app.current_alpha:
                    self.window.attributes("-alpha", self.app.current_alpha)
                self.window.lift()
                # If we have a browser HWND but it's not showing, try to show it
                if self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
                    user32.ShowWindow(self.browser_hwnd, 4) # SW_SHOWNOACTIVATE
                return
            if force_open:
                self.window.lift()
                return
            self.close()
            return

        super().show(force_open)
        if self.window:
            self.build_ui()
            # Start embedding process in a thread to avoid freezing UI
            if not self.embedding_active:
                # Check if we already have a healthy process/window
                if self.browser_proc and self.browser_proc.poll() is None and self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
                    self.window.after(100, self.embed_window)
                else:
                    # Clean up any stale state
                    if self.browser_proc:
                        try: self.browser_proc.terminate()
                        except: pass
                        self.browser_proc = None
                    self.browser_hwnd = None
                    threading.Thread(target=self.start_browser_embedding, daemon=True).start()

    def build_ui(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Main Panel
        self.main_panel = tk.Frame(self.content_container, bg=WINDOW_BG)
        self.main_panel.pack(fill=tk.BOTH, expand=True)

        # Container for the browser window - Ensure it's packed first so it can expand
        # into the space below the title bar
        self.browser_container = tk.Frame(self.main_panel, bg="black", highlightthickness=1, highlightbackground=BORDER_COLOR)
        
        # Add a custom title bar for the browser window since we hid the base one
        self.custom_title = tk.Frame(self.main_panel, bg=PANEL_DARK, height=25)
        self.custom_title.pack(side=tk.TOP, fill=tk.X)
        self.custom_title.pack_propagate(False)

        # Now pack the container to fill the rest of the space
        self.browser_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Loading message
        self.loading_lbl = tk.Label(self.browser_container, text="LOADING INTEGRATED BROWSER (CHROME)...", 
                                   bg="black", fg=TEXT_ACCENT, font=("Lilita One", 12))
        self.loading_lbl.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.custom_title, text="GALAXY HARVESTER BROWSER", bg=PANEL_DARK, fg=TEXT_ACCENT, 
                 font=("Lilita One", 10)).pack(side=tk.LEFT, padx=10)
        
        # Right side buttons: Close, Maximize, Minimize
        close_btn = tk.Label(self.custom_title, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                            font=("Segoe UI", 10, "bold"), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.close() or "break")
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        self.max_btn = tk.Label(self.custom_title, text="▢", bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                            font=("Segoe UI", 10), cursor="hand2", padx=10)
        self.max_btn.pack(side=tk.RIGHT)
        self.max_btn.bind("<Button-1>", lambda e: self.toggle_maximize())
        self.max_btn.bind("<Enter>", lambda e: self.max_btn.config(fg=TEXT_ACCENT))
        self.max_btn.bind("<Leave>", lambda e: self.max_btn.config(fg=TEXT_SECONDARY))

        min_btn = tk.Label(self.custom_title, text="—", bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                            font=("Segoe UI", 10), cursor="hand2", padx=10)
        min_btn.pack(side=tk.RIGHT)
        min_btn.bind("<Button-1>", lambda e: self.minimize())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=TEXT_ACCENT))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=TEXT_SECONDARY))

        # Make custom title draggable
        self.custom_title.bind("<Button-1>", self.click_window)
        self.custom_title.bind("<B1-Motion>", self.drag_window)
        self.custom_title.bind("<ButtonRelease-1>", self.release_window)
        
        # Bind resize for container
        self.browser_container.bind("<Configure>", self.on_container_resize)

    def start_browser_embedding(self):
        self.embedding_active = True
        try:
            # Try to launch Chrome in App mode
            # Use --no-first-run and --no-default-browser-check to prevent popups
            # Use --window-position and --window-size to match our initial window
            # Use --no-activate if possible (though it's not a standard chrome flag, some chromium versions support it)
            # Use --user-data-dir to isolate the profile and prevent joining existing sessions
            profile_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "LivyLogsBrowser")
            # Clear profile lock if it exists from a crash
            lock_file = os.path.join(profile_dir, "SingletonLock")
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except: pass

            browser_args = [
                f"--app={self.url}",
                "--new-window",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=900,650",
                "--window-position=-10000,-10000",
                f"--user-data-dir=\"{profile_dir}\"",
                "--bwsi", # Browsing Without Signing In
                "--no-service-autorun",
                "--disable-features=Translate,OptimizationHints,MediaRouter,DialMediaRouteProvider",
                "--disable-extensions",
                "--disable-component-update",
                "--no-proxy-server",
                "--disable-sync",
                "--disable-default-apps",
                "--silent-debugger-extension-api",
                "--no-pings",
                "--disable-session-crashed-bubble",
                "--disable-infobars",
                "--disable-breakpad",
                "--no-errdialogs",
                "--force-app-mode",
                "--disable-notifications",
                "--disable-popup-blocking"
            ]
            
            # Try to find chrome.exe path if not in PATH
            potential_paths = [
                os.environ.get("PROGRAMFILES", "C:\\Program Files") + "\\Google\\Chrome\\Application\\chrome.exe",
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)") + "\\Google\\Chrome\\Application\\chrome.exe",
                os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            chrome_path = "chrome.exe"
            for p in potential_paths:
                if os.path.exists(p):
                    chrome_path = f'"{p}"'
                    break

            # Use shell=False if possible for better PID tracking, but shell=True might be needed for space in paths
            if chrome_path.startswith('"'):
                # It's a full path with quotes, subprocess handles it better as a list if shell=False
                # but if we use shell=True, we need the whole string
                pass
                
            cmd = f'{chrome_path} {" ".join(browser_args)}'
            # Launch without shell to get more accurate PID if possible
            # Use CREATE_NO_WINDOW if possible to hide the initial window/flash
            self.browser_proc = subprocess.Popen(cmd, shell=True, creationflags=0x08000000) # CREATE_NO_WINDOW
            
            # Wait a bit for process to start
            time.sleep(1)
            
            # Get the actual children PIDs because shell=True might wrap it
            target_pids = [self.browser_proc.pid]
            try:
                import psutil
                parent = psutil.Process(self.browser_proc.pid)
                for child in parent.children(recursive=True):
                    target_pids.append(child.pid)
            except: pass

            # Explicitly define argtypes/restype for EnumWindows/GetWindowText
            user32.EnumWindows.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            user32.EnumWindows.restype = ctypes.c_bool
            user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
            user32.GetWindowTextW.restype = ctypes.c_int
            user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
            user32.GetWindowTextLengthW.restype = ctypes.c_int
            user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
            user32.IsWindowVisible.restype = ctypes.c_bool
            user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
            user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
            user32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
            user32.GetClassNameW.restype = ctypes.c_int
            
            # Wait for the window to appear and find it by title AND PID
            start_time = time.time()
            found_hwnd = None
            
            # Explicitly define more user32 functions for focus management
            user32.GetForegroundWindow.restype = ctypes.c_void_p
            user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
            user32.SetForegroundWindow.restype = ctypes.c_bool
            user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
            user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
            user32.IsWindow.argtypes = [ctypes.c_void_p]
            user32.IsWindow.restype = ctypes.c_bool

            # Capture the current foreground window (SWG client)
            prev_foreground = user32.GetForegroundWindow()
            
            # Start browser in a loop that checks for focus steals more aggressively
            def focus_guard(stop_event, target_hwnd):
                while not stop_event.is_set():
                    curr = user32.GetForegroundWindow()
                    # If target_hwnd is not yet valid, don't worry about it
                    if curr and curr != prev_foreground:
                        # Check if curr belongs to our browser process
                        curr_pid = ctypes.c_ulong(0)
                        user32.GetWindowThreadProcessId(curr, ctypes.byref(curr_pid))
                        if curr_pid.value in target_pids:
                            # Browser stole focus, give it back to SWG
                            user32.SetForegroundWindow(prev_foreground)
                    time.sleep(0.1)

            stop_focus_guard = threading.Event()
            threading.Thread(target=focus_guard, args=(stop_focus_guard, self.window.winfo_id()), daemon=True).start()

            while time.time() - start_time < 12: # 12 second timeout
                if not self.window or not self.window.winfo_exists():
                    break
                
                # Enum windows via ctypes
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                
                def enum_cb(hwnd, lparam):
                    if not user32.IsWindowVisible(hwnd):
                        return True
                        
                    pid = ctypes.c_ulong(0)
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    
                    if pid.value in target_pids:
                        # Only grab the window if it's the main browser window
                        # Chromium usually has many windows (gpu process, etc)
                        # We want the one with a title or specific class
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buff, length + 1)
                            title = buff.value.upper()
                            
                            # Log titles for debugging if needed (but user won't see it)
                            # print(f"[DEBUG] Checking window: {title}")
                            
                            # Be broad with title match but ensure it's browser-like
                            if "GALAXY HARVESTER" in title or "GHHOME" in title or "GOOGLE CHROME" in title or "CHROME" in title:
                                # Double check class name to ensure it's the main frame
                                class_buff = ctypes.create_unicode_buffer(256)
                                user32.GetClassNameW(hwnd, class_buff, 256)
                                class_name = class_buff.value
                                if "Chrome_WidgetWin_1" in class_name:
                                    ctypes.cast(lparam, ctypes.POINTER(ctypes.c_void_p))[0] = hwnd
                                    return False # Stop enumeration
                    return True
                
                res_hwnd = ctypes.c_void_p(0)
                user32.EnumWindows(WNDENUMPROC(enum_cb), ctypes.addressof(res_hwnd))
                
                if res_hwnd.value:
                    found_hwnd = res_hwnd.value
                    
                    # Force the browser to stay hidden and off-screen
                    SWP_NOMOVE = 0x0002
                    SWP_NOSIZE = 0x0001
                    SWP_NOACTIVATE = 0x0010
                    SWP_HIDEWINDOW = 0x0080
                    user32.SetWindowPos(found_hwnd, 0, -10000, -10000, 0, 0, SWP_NOACTIVATE | SWP_HIDEWINDOW | SWP_NOSIZE)
                    
                    SW_HIDE = 0
                    user32.ShowWindow(found_hwnd, SW_HIDE)
                    
                    # Try to strip title bar before reparenting
                    GWL_STYLE = -16
                    WS_CAPTION = 0x00C00000
                    style = user32.GetWindowLongW(found_hwnd, GWL_STYLE)
                    user32.SetWindowLongW(found_hwnd, GWL_STYLE, style & ~WS_CAPTION)

                    # Stop the focus guard now that we found it
                    stop_focus_guard.set()
                    # Restore focus to previous foreground window one last time
                    if prev_foreground:
                        user32.SetForegroundWindow(prev_foreground)
                        
                    break
                
                time.sleep(0.5)

            # Ensure focus guard stops if timeout reached
            stop_focus_guard.set()

            if found_hwnd:
                self.browser_hwnd = found_hwnd
                
                # Start monitoring for tab closure (process death)
                def monitor_browser_exit():
                    try:
                        # Wait a bit for initial setup
                        time.sleep(2)
                        while self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
                            time.sleep(1)
                        # Window gone, close the parent
                        if self.window and self.window.winfo_exists():
                            self.window.after(0, self.close)
                    except: pass
                
                threading.Thread(target=monitor_browser_exit, daemon=True).start()
                
                self.window.after(100, self.embed_window)
            else:
                self.loading_lbl.config(text="COULD NOT EMBED BROWSER.\nPLEASE ENSURE CHROME IS INSTALLED.")
                
        except Exception as e:
            print(f"[DEBUG] Browser embedding error: {e}")
            if self.window:
                self.window.after(0, lambda: self.loading_lbl.config(text=f"ERROR: {str(e)}"))
        finally:
            self.embedding_active = False

    def embed_window(self):
        if not self.window or not self.window.winfo_exists() or not self.browser_hwnd:
            return
            
        try:
            # Set argtypes for user32 functions to prevent OverflowError on 64-bit
            user32.SetParent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            user32.SetParent.restype = ctypes.c_void_p
            user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.GetWindowLongW.restype = ctypes.c_long
            user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
            user32.SetWindowLongW.restype = ctypes.c_long
            user32.SetLayeredWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_byte, ctypes.c_long]
            user32.SetLayeredWindowAttributes.restype = ctypes.c_bool
            user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.SetWindowPos.restype = ctypes.c_bool
            user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.ShowWindow.restype = ctypes.c_bool

            # Get our container HWND
            container_hwnd = self.browser_container.winfo_id()
            
            # Hide the browser window before reparenting to minimize flickering and focus stealing
            SW_HIDE = 0
            user32.ShowWindow(self.browser_hwnd, SW_HIDE)
            
            # Reparent via user32
            user32.SetParent(self.browser_hwnd, container_hwnd)
            
            # Constants for styles
            GWL_STYLE = -16
            GWL_EXSTYLE = -20
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_SYSMENU = 0x00080000
            WS_POPUP = 0x80000000
            WS_CHILD = 0x40000000
            WS_CLIPCHILDREN = 0x02000000
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_LAYERED = 0x00080000
            
            # Remove title bar and borders
            style = user32.GetWindowLongW(self.browser_hwnd, GWL_STYLE)
            # Remove caption, borders, sysmenu, minimize/maximize buttons, and the system menu
            # WS_DLGFRAME (0x00400000) and WS_BORDER (0x00800000) combine to WS_CAPTION
            style = style & ~WS_CAPTION
            style = style & ~WS_THICKFRAME
            style = style & ~WS_SYSMENU
            style = style & ~0x00020000 # WS_MINIMIZEBOX
            style = style & ~0x00010000 # WS_MAXIMIZEBOX
            style = style & ~0x00400000 # WS_DLGFRAME
            style = style & ~0x00800000 # WS_BORDER
            
            # Ensure the window is not minimized or maximized
            style = style & ~0x20000000 # WS_MINIMIZE
            style = style & ~0x01000000 # WS_MAXIMIZE
            
            # Set to WS_CHILD and ClipChildren
            # WS_CHILD | WS_CLIPCHILDREN ensures it is restricted to the parent container
            # We explicitly remove WS_POPUP and WS_CAPTION to prevent it being dragged out
            style = (style | WS_CHILD | WS_CLIPCHILDREN) & ~(WS_POPUP | WS_CAPTION | WS_THICKFRAME)
            user32.SetWindowLongW(self.browser_hwnd, GWL_STYLE, style)

            # Set extended styles: NoActivate + Layered (for transparency support)
            ex_style = user32.GetWindowLongW(self.browser_hwnd, GWL_EXSTYLE)
            # WS_EX_TOOLWINDOW hides from taskbar
            # WS_EX_NOACTIVATE prevents focus steal
            # WS_EX_LAYERED for transparency
            # WS_EX_CONTROLPARENT helps with tab order but also keeps child status firm
            WS_EX_CONTROLPARENT = 0x00010000
            ex_style = (ex_style | WS_EX_NOACTIVATE | WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_CONTROLPARENT) & ~0x00000200 & ~0x00020000
            user32.SetWindowLongW(self.browser_hwnd, GWL_EXSTYLE, ex_style)
            
            # Ensure SetParent is truly applied one more time to be absolutely sure
            user32.SetParent(self.browser_hwnd, container_hwnd)
            
            # Reposition to match container exactly
            self.on_container_resize()
            
            # Start a thread to monitor and fix browser popups
            self.stop_popup_monitor = threading.Event()
            threading.Thread(target=self._monitor_popups, daemon=True).start()
            
            # Set transparency key for the browser too if it helps
            # Some Chromium versions need the specific transparent color key of the parent
            # to be recognized as transparent in layered mode.
            LWA_COLORKEY = 0x00000001
            LWA_ALPHA = 0x00000002
            user32.SetLayeredWindowAttributes(self.browser_hwnd, 0x000001, 255, LWA_COLORKEY | LWA_ALPHA)
            
            # Hide the loading label when browser embedded
            if self.loading_lbl.winfo_exists():
                self.loading_lbl.place_forget()
                
            # Ensure it is moved to origin 0,0 of the child container and shown
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            user32.SetWindowPos(self.browser_hwnd, 0, 0, 0, 900, 650, SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            
            # Force ShowWindow to apply styles and ensure visibility without activation
            SW_SHOWNOACTIVATE = 4
            user32.ShowWindow(self.browser_hwnd, SW_SHOWNOACTIVATE)

            # Also ensure parent window clips children to prevent flickering
            parent_hwnd = self.window.winfo_id()
            p_style = user32.GetWindowLongW(parent_hwnd, GWL_STYLE)
            user32.SetWindowLongW(parent_hwnd, GWL_STYLE, p_style | WS_CLIPCHILDREN)
            
            # Reposition to match container exactly
            self.on_container_resize()
            
            # Sync transparency immediately
            self.sync_transparency()
            
            # Hide loading label safely
            if self.window and self.loading_lbl.winfo_exists():
                self.loading_lbl.place_forget()
            
        except Exception as e:
            print(f"[DEBUG] Embedding failed: {e}")

    def toggle_maximize(self):
        """Toggles between maximized and normal state without stealing focus."""
        if not self.window or not self.window.winfo_exists():
            return

        # Use win32 focus-safe flags
        user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
        user32.GetForegroundWindow.restype = ctypes.c_void_p
        prev_foreground = user32.GetForegroundWindow()

        # Is it already maximized?
        # Check if window geometry matches screen
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        curr_w = self.window.winfo_width()
        curr_h = self.window.winfo_height()

        if curr_w >= screen_w - 20 and curr_h >= screen_h - 60:
            # Restore
            self.window.geometry(f"{self.default_w}x{self.default_h}")
            self.max_btn.config(text="▢")
        else:
            # Maximize
            # Fill entire screen
            self.window.geometry(f"{screen_w}x{screen_h}+0+0")
            self.max_btn.config(text="❐")

        # Force update
        self.window.update_idletasks()
        
        # If browser exists, ensure it is restored from any independent state
        if self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
            GWL_STYLE = -16
            WS_CHILD = 0x40000000
            WS_MINIMIZE = 0x20000000
            WS_MAXIMIZE = 0x01000000
            SW_RESTORE = 9
            
            style = user32.GetWindowLongW(self.browser_hwnd, GWL_STYLE)
            if (style & WS_MINIMIZE) or (style & WS_MAXIMIZE):
                user32.ShowWindow(self.browser_hwnd, SW_RESTORE)
            
            # Re-verify child style
            # Get style again after potential restore
            style = user32.GetWindowLongW(self.browser_hwnd, GWL_STYLE)
            if not (style & WS_CHILD):
                user32.SetWindowLongW(self.browser_hwnd, GWL_STYLE, style | WS_CHILD)
                user32.SetParent(self.browser_hwnd, self.browser_container.winfo_id())

        # Call resize handler to position correctly
        self.on_container_resize()

        # Restore focus to SWG if it moved
        if prev_foreground:
            user32.SetForegroundWindow(prev_foreground)
        
        return "break"

    def minimize(self):
        """Hides the window to the tray."""
        if self.window:
            # First ensure browser is hidden to avoid visual artifacts
            if self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
                # We use SW_HIDE, but also ensure it doesn't try to restore itself
                SW_HIDE = 0
                user32.ShowWindow(self.browser_hwnd, SW_HIDE)
            
            self.window.withdraw()
        return "break"

    def on_configure(self, event):
        # Override to handle resizing of the embedded browser
        super().on_configure(event)
        self.on_container_resize()
        # Also sync transparency on movement
        self.sync_transparency()

    def on_container_resize(self, event=None):
        if self.browser_hwnd and self.browser_container.winfo_exists():
            # Trigger popup re-sync on resize/move as well
            if hasattr(self, "stop_popup_monitor") and not self.stop_popup_monitor.is_set():
                self._fix_popups()
            
            # We need to use the actual pixel dimensions
            self.window.update_idletasks()
            w = self.browser_container.winfo_width()
            h = self.browser_container.winfo_height()
            if w > 1 and h > 1:
                # Ensure the window is always at 0,0 relative to the container
                # and hasn't been dragged out or lost its CHILD status
                GWL_STYLE = -16
                WS_CHILD = 0x40000000
                WS_MINIMIZE = 0x20000000
                WS_MAXIMIZE = 0x01000000
                SW_RESTORE = 9
                
                style = user32.GetWindowLongW(self.browser_hwnd, GWL_STYLE)
                
                # If the window is minimized or maximized independently, restore it
                if (style & WS_MINIMIZE) or (style & WS_MAXIMIZE):
                    user32.ShowWindow(self.browser_hwnd, SW_RESTORE)
                    # Get style again after restore
                    style = user32.GetWindowLongW(self.browser_hwnd, GWL_STYLE)

                if not (style & WS_CHILD):
                    # Restore and enforce child style
                    new_style = (style | WS_CHILD) & ~(WS_MINIMIZE | WS_MAXIMIZE)
                    user32.SetWindowLongW(self.browser_hwnd, GWL_STYLE, new_style)
                    user32.SetParent(self.browser_hwnd, self.browser_container.winfo_id())

                SWP_NOZORDER = 0x0004
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                user32.SetWindowPos(self.browser_hwnd, 0, 0, 0, w, h, SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                
                # Explicitly show it again if it was hidden by minimize
                SW_SHOWNOACTIVATE = 4
                user32.ShowWindow(self.browser_hwnd, SW_SHOWNOACTIVATE)
        
        # Also sync transparency on resize/move to ensure it matches
        self.sync_transparency()

    def sync_transparency(self):
        """Matches the embedded browser's transparency to the parent window."""
        if not self.browser_hwnd or not self.window or not self.window.winfo_exists():
            return
            
        try:
            # Set argtypes here too as it might be called separately
            user32.SetLayeredWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_byte, ctypes.c_long]
            user32.SetLayeredWindowAttributes.restype = ctypes.c_bool

            alpha = self.window.attributes("-alpha")
            LWA_COLORKEY = 0x00000001
            LWA_ALPHA = 0x00000002
            
            # SetLayeredWindowAttributes takes 0-255
            byte_alpha = int(alpha * 255)
            
            # Ensure browser window is still layered
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.GetWindowLongW.restype = ctypes.c_long
            user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
            user32.SetWindowLongW.restype = ctypes.c_long
            
            ex_style = user32.GetWindowLongW(self.browser_hwnd, GWL_EXSTYLE)
            if not (ex_style & WS_EX_LAYERED):
                user32.SetWindowLongW(self.browser_hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
            
            # Apply both alpha and the colorkey used by the main app for transparency
            # The #000001 color is what we use as transparency key in the main app
            user32.SetLayeredWindowAttributes(self.browser_hwnd, 0x000001, byte_alpha, LWA_COLORKEY | LWA_ALPHA)
        except:
            pass

    def refresh(self, force=False):
        """Part of the standard refresh cycle."""
        super().refresh(force)
        # Ensure browser alpha is synced during main app fade in/out
        self.sync_transparency()

    def close(self):
        # Stop popup monitor
        if hasattr(self, "stop_popup_monitor"):
            self.stop_popup_monitor.set()
            
        # Kill browser process when closing
        if self.browser_proc:
            try:
                # Get children too
                children = []
                try:
                    p = psutil.Process(self.browser_proc.pid)
                    children = p.children(recursive=True)
                except: pass

                # If we have the HWND, try to close it nicely first
                if self.browser_hwnd and user32.IsWindow(self.browser_hwnd):
                    WM_CLOSE = 0x0010
                    user32.PostMessageW(self.browser_hwnd, WM_CLOSE, 0, 0)
                
                # Give it a moment then terminate if still alive
                def kill_proc(proc, kids):
                    time.sleep(1.5)
                    try: 
                        for kid in kids:
                            try: kid.terminate()
                            except: pass
                        proc.terminate()
                    except: pass
                
                threading.Thread(target=kill_proc, args=(self.browser_proc, children), daemon=True).start()
            except:
                pass
        self.browser_hwnd = None
        super().close()

    def _monitor_popups(self):
        """Monitors for Chromium popup windows (dropdowns, etc.) and ensures they are on top."""
        while hasattr(self, "stop_popup_monitor") and not self.stop_popup_monitor.is_set():
            if self.window and self.window.winfo_exists() and self.browser_hwnd:
                self._fix_popups()
            time.sleep(0.5) # Check every 500ms

    def _fix_popups(self):
        """Finds browser popups and forces them to be topmost or correctly parented."""
        try:
            # We look for windows with class 'Chrome_WidgetWin_1' that are NOT our main browser_hwnd
            # and ensure they are forced to the top.
            # Dropdowns are often 'Chrome_WidgetWin_1' or 'Chrome_WidgetWin_2'
            
            from constants import HWND_TOPMOST, SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW, user32
            import ctypes
            
            target_pids = [self.browser_proc.pid]
            try:
                import psutil
                parent = psutil.Process(self.browser_proc.pid)
                for child in parent.children(recursive=True):
                    target_pids.append(child.pid)
            except: pass

            def enum_cb(hwnd, lparam):
                if hwnd == self.browser_hwnd:
                    return True
                if not user32.IsWindowVisible(hwnd):
                    return True
                
                pid = ctypes.c_ulong(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                if pid.value in target_pids:
                    class_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_buff, 256)
                    c_name = class_buff.value
                    
                    # Chrome dropdowns and popups are usually these classes
                    if "Chrome_WidgetWin" in c_name:
                        # Force to topmost so it shows over the app
                        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                                           SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        except:
            pass
