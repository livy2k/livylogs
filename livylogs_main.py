import tkinter as tk
import os
import sys
import time
import json
import threading
import subprocess
import pystray
from pystray import MenuItem as item
from PIL import Image
from datetime import datetime, timedelta
from configparser import ConfigParser
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, filedialog
import ctypes
from ctypes import wintypes

from constants import (
    WINDOW_BG, PANEL_BG, PANEL_DARK, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    ACCENT_BLUE, BORDER_COLOR, BORDER_HIGHLIGHT, BUTTON_BG, BUTTON_HOVER,
    MIN_WIDTH, MIN_HEIGHT, SNAP_THRESHOLD, user32, kernel32, winmm,
    HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE,
    SWP_SHOWWINDOW, SWP_HIDEWINDOW, ENTRY_BG, WINDOWPLACEMENT,
    TITLE_GRADIENT_START, TITLE_GRADIENT_END
)
from utils import is_window_minimized, apply_snapping, extract_character_id, get_resource_path
from ui_base import ThemedMessagebox

# Popout Windows
from windows.skimmers import SkimmersWindow
from windows.damage_meter import DamageMeterWindow
from windows.leaderboard import LeaderboardWindow
from windows.details import DetailsWindow
from windows.options import OptionsWindow
from windows.alexa import AlexaWindow


class CombatLogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Combat Log Analyzer")
        self.root.geometry("260x50")
        self.root.configure(bg=WINDOW_BG)
        
        # Font objects
        self.font_stats_obj = tkfont.Font(family="Segoe UI Variable Display", size=20, weight="bold")
        self.font_title_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_small_obj = tkfont.Font(family="Segoe UI", size=9)
        self.font_button_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # self.style = ttk.Style()
        # self.style.theme_use('clam')
        # self.style.configure("Vertical.TScrollbar", background=BUTTON_BG, troughcolor=PANEL_BG, bordercolor=BORDER_COLOR, arrowcolor=TEXT_SECONDARY)

        self.config = ConfigParser()
        self.config.read("settings.ini")

        initial_log_path = self.config.get("General", "log_path", fallback="")
        initial_alpha = self.config.getfloat("General", "transparency", fallback=1.0)
        initial_width = max(MIN_WIDTH, self.config.getint("General", "width", fallback=260))
        initial_height = max(MIN_HEIGHT, self.config.getint("General", "height", fallback=50))
        initial_x = self.config.get("General", "x", fallback="50")
        initial_y = self.config.get("General", "y", fallback="50")

        self.root.geometry(f"{initial_width}x{initial_height}+{initial_x}+{initial_y}")
        if initial_alpha < 0.01: initial_alpha = 1.0
        self.target_alpha = initial_alpha
        self.current_alpha = initial_alpha
        self.root.attributes("-alpha", initial_alpha)
        self.root.overrideredirect(True)
        # Ensure it doesn't show in taskbar by setting it as a tool window
        try:
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW)
        except: pass
        
        self.file_path_var = tk.StringVar(value=initial_log_path)
        self.disable_warnings = tk.BooleanVar(value=self.config.getboolean("General", "disable_warnings", fallback=False))
        self.show_class_colors = tk.BooleanVar(value=self.config.getboolean("General", "show_class_colors", fallback=True))
        self.char_name = tk.StringVar(value=self.config.get("General", "character_name", fallback=""))
        if not self.char_name.get() and initial_log_path:
            self.char_name.set(extract_character_id(initial_log_path))
        self.api_url = tk.StringVar(value=self.config.get("General", "api_url", fallback="https://livy.logs/sync"))
        self.enable_sync = tk.BooleanVar(value=self.config.getboolean("General", "enable_sync", fallback=False))
        self.test_mode = tk.BooleanVar(value=False)
        self.test_thread = None
        self._last_test_toggle = 0

        self.skimmers_win = SkimmersWindow(self)
        self.damage_meter_win = DamageMeterWindow(self)
        self.leaderboard_win = LeaderboardWindow(self)
        self.details_win = DetailsWindow(self)
        self.options_win = OptionsWindow(self)
        self.alexa_win = AlexaWindow(self)
        
        self._managed_windows = [
            self.skimmers_win, self.damage_meter_win, self.leaderboard_win, 
            self.details_win, self.options_win, self.alexa_win
        ]
        
        self.is_interacting = False
        self.last_interaction_time = 0
        
        self.actual_app_start_time = datetime.now()
        self.last_reset_time = self.actual_app_start_time
        self.running = True
        
        # Combat State
        self.player_data = {}
        self.loot_data = {}
        self.player_classes = {}
        self.all_events = []
        self.locally_seen_players = {}
        
        self.load_bosses()
        self.load_filters()
        self.load_class_configs()
        self.build_layout()
        
        self.pulse_state = False
        self.last_pulse_time = 0
        self.last_ui_update_time = 0
        self.last_combat_time = 0
        self.app_start_time = None
        self.last_log_sync_time = None
        
        self.last_dm_reset = None
        self.last_lb_reset = None
        self.last_sk_reset = None
        self.last_dt_reset = None
        
        self.engine_process = None
        self.time_window_dm = 5
        self.time_window_skimmers = 60
        self.time_window_details = 60
        self.inventory_full = False
        self.skimmer_search_mode = False
        self.always_on_top = True
        self.is_dialog_open = False

        self.initial_show()
        threading.Thread(target=self.start_pipe_listener, daemon=True).start()
        threading.Thread(target=self.web_sync_loop, daemon=True).start()
        self.setup_tray_icon()
        self.start_ticker_loop()
        self.root.after(500, self.check_target_window)
        if initial_log_path:
            self.root.after(1000, lambda: self.start_c_engine(initial_log_path))

    def load_bosses(self):
        boss_list = []
        try:
            path = get_resource_path(os.path.join("filters", "bosses.txt"))
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        name = line.strip()
                        if name and not name.startswith("#"):
                            boss_list.append(name.lower())
        except Exception as e:
            pass # Suppress log loading errors for clean UI experience
        return boss_list

    def load_filters(self):
        filter_list = []
        try:
            path = get_resource_path(os.path.join("filters", "filters.txt"))
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        phrase = line.rstrip("\n").rstrip("\r")
                        if phrase and not phrase.startswith("#"):
                            filter_list.append(phrase.lower())
        except Exception as e:
            pass # Suppress for clean UI experience
        return filter_list

    def load_class_configs(self):
        configs = {}
        try:
            filters_dir = get_resource_path("filters")
            if os.path.exists(filters_dir):
                for filename in os.listdir(filters_dir):
                    if filename.endswith(".txt") and filename not in ["bosses.txt", "filters.txt"]:
                        class_name = filename[:-4]
                        path = os.path.join(filters_dir, filename)
                        color = "#00a2ff" # Default
                        abilities = set()
                        with open(path, "r", encoding="utf-8-sig") as f:
                            lines = f.readlines()
                            if lines:
                                first_line = lines[0].strip()
                                if first_line.startswith("#"):
                                    color = first_line.lstrip("#").strip()
                                    start_idx = 1
                                else:
                                    start_idx = 0
                                
                                for line in lines[start_idx:]:
                                    ability = line.strip()
                                    if ability and not ability.startswith("#"):
                                        abilities.add(ability.lower())
                        configs[class_name] = {"color": color, "abilities": abilities}
        except Exception as e:
            pass # Suppress for clean UI experience
        return configs

    def initial_show(self):
        try:
            # self.current_alpha = 0.0
            # self.root.attributes("-alpha", 0.0)
            self.root.overrideredirect(True)
            self.root.withdraw()
        except: pass

    def _get_managed_windows(self):
        managed = [self.root]
        for w in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win, self.options_win, self.alexa_win]:
            if w.window and w.window.winfo_exists(): managed.append(w.window)
        return managed

    def check_target_window(self):
        if not self.running: return
        
        # 1. Ensure main window is always visible
        if self.root.state() == "withdrawn" and not getattr(self, "_minimized_to_tray", False):
            self.root.deiconify()
            if self.root.attributes("-alpha") != self.current_alpha:
                self.root.attributes("-alpha", self.current_alpha)
            
        # 2. Window Management Logic (Reverted from C)
        try:
            import ctypes
            user32 = ctypes.windll.user32
            
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd:
                # Get Foreground Title
                length = user32.GetWindowTextLengthW(fg_hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(fg_hwnd, buff, length + 1)
                fg_title = buff.value.lower()
                
                # Get Foreground Class
                class_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(fg_hwnd, class_buff, 256)
                fg_class = class_buff.value
                
                # Detect Game Window
                is_game = any(s in fg_title for s in ["swgclient", "star wars galaxies"])
                
                # Detect Safe Zone (Start Menu, Explorer, Discord, etc.)
                safe_classes = ["Shell_TrayWnd", "DV2ControlHost", "BaseBar", "Immersive", "Launcher", "NotifyIconOverflowWindow", "CabinetWClass", "TaskManagerWindow"]
                is_safe = any(sc in fg_class for sc in safe_classes) or fg_title == "" or "discord" in fg_title or "search" in fg_title
                
                # Track state to avoid redundant calls (flashing)
                target_state = "game" if is_game else ("safe" if is_safe else "hidden")
                current_state = getattr(self, "_last_win_state", None)
                
                # Check for focus on the app itself
                my_pid = os.getpid()
                fg_pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(fg_pid))
                if fg_pid.value == my_pid:
                    target_state = "game" # Treat focus on app like focus on game

                if target_state != current_state:
                    self._last_win_state = target_state
                    
                    if target_state == "game":
                        if not self.root.attributes("-topmost"):
                            self.root.attributes("-topmost", True)
                        for win in self._get_managed_windows():
                            if win != self.root:
                                if win.state() == "withdrawn":
                                    win.deiconify()
                                    win.lift()
                                if not win.attributes("-topmost"):
                                    win.attributes("-topmost", True)
                                if win.attributes("-alpha") != self.current_alpha:
                                    win.attributes("-alpha", self.current_alpha)
                    elif target_state == "safe":
                        if self.root.attributes("-topmost"):
                            self.root.attributes("-topmost", False)
                        for win in self._get_managed_windows():
                            if win != self.root:
                                if win.state() == "withdrawn":
                                    win.deiconify()
                                    win.lift()
                                if win.attributes("-topmost"):
                                    win.attributes("-topmost", False)
                                if win.attributes("-alpha") != self.current_alpha:
                                    win.attributes("-alpha", self.current_alpha)
                    else:
                        self.root.attributes("-topmost", False)
                        for win in self._get_managed_windows():
                            if win != self.root:
                                if win.state() != "withdrawn":
                                    win.withdraw()
                else:
                    # Even if state is same, ensure topmost is maintained if in game
                    if target_state == "game":
                        # Be less aggressive to prevent flashing
                        try:
                            # Only set if NOT topmost, but check if we are actually allowed to (not minimized)
                            if not self.root.attributes("-topmost") and self.root.state() != "withdrawn":
                                self.root.attributes("-topmost", True)
                        except: pass
                        
                        for win in self._get_managed_windows():
                            if win != self.root:
                                try:
                                    # ONLY re-apply topmost if it somehow lost it
                                    if not win.attributes("-topmost") and win.state() != "withdrawn":
                                        win.attributes("-topmost", True)
                                except: pass
            
        except Exception as e:
            pass
            
        self.root.after(500, self.check_target_window)

    def start_show(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.root.lift()
        
        for win in self._get_managed_windows():
            if win.state() == "withdrawn":
                win.deiconify()
                win.lift()
        
        if self.current_alpha < self.target_alpha:
            self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.05)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.root.after(5, self.fade_in)

    def start_hide(self, minimize=True):
        self.fade_out(minimize=minimize)

    def fade_out(self, minimize=True):
        if self.current_alpha > 0:
            self.current_alpha = max(0, self.current_alpha - 0.05)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.root.after(5, lambda: self.fade_out(minimize=minimize))
        else:
            if minimize:
                for win in self._get_managed_windows():
                    if win.state() != "withdrawn":
                        win.withdraw()

    def start_c_engine(self, log_path):
        def _bg_start():
            # Terminate any existing engine processes first
            try:
                import subprocess
                # Use absolute path of the script directory
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Use taskkill to clean up any orphaned engines
                # We wrap individual calls to handle Access Denied errors more gracefully
                for proc_name in ['LivyLogsEngine_v2.exe', 'parser_v2.exe', 'LivyLogs_Engine_New.exe', 'LivyLogsEngine.exe', 'parser.exe', 'LL_Engine.exe']:
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', proc_name, '/T'], 
                                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception as e:
                        try:
                            with open("crash_log.txt", "a") as f:
                                f.write(f"--- CLEANUP WARNING {datetime.now()} --- Could not kill {proc_name}: {e}\n")
                        except: pass
                
                # Additional check to ensure processes are GONE
                import time
                max_wait = 1.0
                start_wait = time.time()
                while time.time() - start_wait < max_wait:
                    res = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq LivyLogsEngine_v2.exe'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if "LivyLogsEngine_v2.exe" not in res.stdout:
                        break
                    time.sleep(0.2)

                # Clean up stale tmp files in the script directory
                if os.path.exists(base_dir):
                    for f in os.listdir(base_dir):
                        if f.startswith("engine_pid_") and f.endswith(".tmp"):
                            try: os.remove(os.path.join(base_dir, f))
                            except: pass
            except Exception as e:
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- CLEANUP ERROR {datetime.now()} ---\n{e}\n")
                except: pass
            
            # Small delay to ensure OS releases resources
            time.sleep(0.3)
            
            # Try multiple possible engine names to be robust
            possible_exes = ["LivyLogs_Engine_New.exe", "LivyLogsEngine_v2.exe", "parser_v2.exe", "LivyLogsEngine.exe", "parser.exe", "LL_Engine.exe"]
            exe_path = None
            for name in possible_exes:
                p = os.path.join(base_dir, name)
                if os.path.exists(p):
                    exe_path = p
                    break

            if exe_path:
                try:
                    import subprocess
                    # Start the engine in the background and capture output for debugging
                    log_file_path = os.path.join(base_dir, "engine_debug.txt")
                    with open(log_file_path, "a") as debug_file:
                        debug_file.write(f"--- LAUNCHING ENGINE {datetime.now()} ---\nPath: {exe_path}\nLog: {log_path}\n")
                    
                    # We use a very simple Popen call without redirecting stdout/stderr to a closed file
                    proc = subprocess.Popen([exe_path, log_path], 
                                     cwd=base_dir,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    with open(log_file_path, "a") as debug_file:
                        debug_file.write(f"  Launched PID: {proc.pid}\n")
                        
                    try:
                        with open("crash_log.txt", "a") as f:
                            f.write(f"--- ENGINE STARTED {datetime.now()} ---\nPath: {exe_path}\nLog: {log_path}\n")
                    except: pass
                except Exception as e:
                    try:
                        with open("crash_log.txt", "a") as f:
                            f.write(f"--- ENGINE START ERROR {datetime.now()} ---\n{e}\n")
                    except: pass
            else:
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- ENGINE MISSING {datetime.now()} --- Tried: {possible_exes} in {base_dir}\n")
                except: pass

        # Run the startup sequence in a thread to avoid blocking UI
        t = threading.Thread(target=_bg_start, daemon=True)
        t.start()

    def build_layout(self):
        # style = ttk.Style()
        # style.theme_use('clam')
        # style.configure("Vertical.TScrollbar", gripcount=0, background=PANEL_DARK, darkcolor=PANEL_DARK, lightcolor=PANEL_DARK, troughcolor=WINDOW_BG, bordercolor=BORDER_COLOR, arrowcolor=TEXT_SECONDARY)
        # style.map("Vertical.TScrollbar", background=[('active', ACCENT_BLUE), ('pressed', ACCENT_BLUE)])

        self.root_border = tk.Frame(self.root, bg=BORDER_COLOR, padx=1, pady=1)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        outer = tk.Frame(self.root_border, bg=WINDOW_BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        outer.bind("<Button-1>", self.click_window)
        outer.bind("<B1-Motion>", self.drag_window)
        outer.bind("<ButtonRelease-1>", self.release_window)
        self.root.bind("<Configure>", self.on_configure)

        header = tk.Frame(outer, bg=WINDOW_BG)
        header.pack(fill=tk.X)
        
        # Sophisticated Main Title Bar
        self.main_title_bar = tk.Canvas(header, bg=TITLE_GRADIENT_END, height=35, highlightthickness=0)
        self.main_title_bar.pack(fill=tk.X)
        self.main_title_bar.bind("<Button-1>", self.click_window)
        self.main_title_bar.bind("<B1-Motion>", self.drag_window)
        self.main_title_bar.bind("<ButtonRelease-1>", self.release_window)
        
        def draw_main_gradient(e=None):
            w = self.main_title_bar.winfo_width()
            h = self.main_title_bar.winfo_height()
            self.main_title_bar.delete("gradient")
            for i in range(h):
                r1, g1, b1 = self.root.winfo_rgb(TITLE_GRADIENT_START)
                r2, g2, b2 = self.root.winfo_rgb(TITLE_GRADIENT_END)
                r = int(r1 + (r2 - r1) * (i / h)) // 256
                g = int(g1 + (g2 - g1) * (i / h)) // 256
                b = int(b1 + (b2 - b1) * (i / h)) // 256
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.main_title_bar.create_line(0, i, w, i, fill=color, tags="gradient")
            self.main_title_bar.tag_lower("gradient")
            self.main_title_bar.coords("exit_btn", w - 5, h // 2)
            self.main_title_bar.coords("alexa_btn", w - 35, h // 2)
            self.main_title_bar.coords("menu_btn", w - 100, h // 2)
            title_lbl.config(bg=TITLE_GRADIENT_START)

        self.main_title_bar.bind("<Configure>", draw_main_gradient)
        
        exit_btn = tk.Label(self.main_title_bar, text=" ✕ ", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2")
        self.main_title_bar.create_window(300, 17, window=exit_btn, anchor="e", tags="exit_btn")
        exit_btn.bind("<Button-1>", lambda e: self.on_exit())
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(fg="#ff4444"))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(fg=TEXT_SECONDARY))

        alexa_btn = tk.Label(self.main_title_bar, text=" ALEXA ", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2")
        self.main_title_bar.create_window(270, 17, window=alexa_btn, anchor="e", tags="alexa_btn")
        alexa_btn.bind("<Button-1>", lambda e: self.alexa_win.show())
        alexa_btn.bind("<Enter>", lambda e: alexa_btn.config(fg=TEXT_ACCENT))
        alexa_btn.bind("<Leave>", lambda e: alexa_btn.config(fg=TEXT_SECONDARY))

        menu_btn = tk.Label(self.main_title_bar, text=" SETTINGS ", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2")
        self.main_title_bar.create_window(200, 17, window=menu_btn, anchor="e", tags="menu_btn")
        menu_btn.bind("<Button-1>", lambda e: self.toggle_menu())
        menu_btn.bind("<Enter>", lambda e: menu_btn.config(fg=TEXT_ACCENT))
        menu_btn.bind("<Leave>", lambda e: menu_btn.config(fg=TEXT_SECONDARY))

        self.ontop_btn = tk.Label(self.main_title_bar, text="ONTOP: OFF", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2")
        self.main_title_bar.create_window(10, 17, window=self.ontop_btn, anchor="w")
        self.ontop_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())

        title_lbl = tk.Label(self.main_title_bar, text="LIVYLOGS", bg=TITLE_GRADIENT_START, fg=TEXT_ACCENT, font=self.font_title_obj)
        self.main_title_bar.create_window(85, 17, window=title_lbl, anchor="w")
        title_lbl.bind("<Button-1>", self.click_window)
        title_lbl.bind("<B1-Motion>", self.drag_window)
        title_lbl.bind("<ButtonRelease-1>", self.release_window)

        nav = tk.Frame(header, bg=PANEL_DARK, pady=2)
        nav.pack(fill=tk.X)
        nav.bind("<Button-1>", self.click_window)
        nav.bind("<B1-Motion>", self.drag_window)
        nav.bind("<ButtonRelease-1>", self.release_window)

        def btn(t, cmd): 
            l = tk.Label(nav, text=t, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2", padx=5)
            l.pack(side=tk.LEFT); l.bind("<Button-1>", lambda e: cmd())
            return l
        self.lbl_dmg = btn("DMG METER", self.damage_meter_win.show)
        self.lbl_det = btn("DETAILS", self.details_win.show)
        self.lbl_skm = btn("SKIMMERS", self.skimmers_win.show)
        self.lbl_ldb = btn("LEADERBOARD", self.leaderboard_win.show)
        
        self.lbl_status = tk.Label(nav, text="DISCONNECTED", bg=PANEL_DARK, fg="#ff4444", font=("Segoe UI", 7, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=5)
        
        self.lbl_version = tk.Label(nav, text="1.0", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8))
        self.lbl_version.pack(side=tk.RIGHT)

        # Spacer to keep minimal height
        tk.Frame(outer, bg=WINDOW_BG, height=2).pack()
        
        # Add resize handle for main window
        self.resize_handle = tk.Label(outer, text="◢", bg=WINDOW_BG, fg=BORDER_COLOR, font=("Segoe UI", 8), cursor="size_nw_se")
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<Button-1>", self.init_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)
        self.resize_handle.bind("<ButtonRelease-1>", self.release_window)

    def create_stat_box(self, parent, title, value):
        f = tk.Frame(parent, bg=BORDER_COLOR, padx=1, pady=1); f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        b = tk.Frame(f, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_HIGHLIGHT); b.pack(fill=tk.BOTH, expand=True)
        tk.Label(b, text=title, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(anchor="w", padx=5)
        v = tk.Label(b, text=value, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=self.font_stats_obj); v.pack(anchor="w", padx=5)
        f.value_label = v; return f

    def start_pipe_listener(self):
        retry_count = 0
        pipe_path = r"\\.\pipe\LivyLogsPipe"

        def find_active_pipe():
            # 1. Standard name check
            if kernel32.WaitNamedPipeW(pipe_path, 1):
                return pipe_path

            # 2. Look for the .tmp files we created
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                tmp_files = [f for f in os.listdir(base_dir) if f.startswith("engine_pid_") and f.endswith(".tmp")]
                if tmp_files:
                    # Sort by modification time to get the newest one
                    tmp_files.sort(key=lambda x: os.path.getmtime(os.path.join(base_dir, x)))
                    for newest_file in reversed(tmp_files):
                        file_full_path = os.path.join(base_dir, newest_file)
                        if os.path.getsize(file_full_path) == 0:
                            continue

                        with open(file_full_path, "r") as f:
                            pid_str = f.read().strip()
                        
                        if not pid_str:
                            continue
                            
                        pid = int(pid_str)
                        
                        # Verify the process is still running
                        import subprocess
                        check = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        if pid_str in check.stdout:
                            # If process exists, we wait a bit more for the pipe to appear
                            if kernel32.WaitNamedPipeW(pipe_path, 100):
                                return pipe_path
                        else:
                            try: os.remove(file_full_path)
                            except: pass
            except Exception as e:
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- DISCOVERY ERROR {datetime.now()} ---\n{e}\n")
                except: pass
            return None

        while self.running:
            if hasattr(self, 'lbl_status'):
                self.lbl_status.config(text="RECONNECTING...", fg="#ffaa00")
            
            # Use discovery logic
            current_pipe = find_active_pipe()
            
            if not current_pipe:
                # Wait longer for the pipe to appear
                if kernel32.WaitNamedPipeW(pipe_path, 10000):
                    current_pipe = pipe_path
            
            if not current_pipe:
                if retry_count % 10 == 0:
                    try:
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        with open("crash_log.txt", "a") as f:
                            f.write(f"--- PIPE WAIT ATTEMPT {datetime.now()} (retry {retry_count}) ---\n")
                            # List .tmp files just in case
                            tmps = [tf for tf in os.listdir(base_dir) if tf.startswith("engine_pid_")]
                            f.write(f"  Existing signals: {tmps}\n")
                    except: pass
                if retry_count > 1200: # 10 minutes
                    self.root.after(0, self.on_exit)
                    break
                time.sleep(0.5); continue
            
            retry_count = 0
            
            h = kernel32.CreateFileW(pipe_path, 0x80000000, 0x00000003, None, 3, 0, None)
            if h == -1 or h == 0xFFFFFFFF:
                err = kernel32.GetLastError()
                # 231 is ERROR_PIPE_BUSY
                if err == 231:
                    # Wait for the pipe to become available
                    if kernel32.WaitNamedPipeW(pipe_path, 10000):
                        # Retry immediately
                        continue
                
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- PIPE CONNECT ERROR {datetime.now()} --- Error: {err}\n")
                except: pass
                
                if err == 5: # ACCESS_DENIED
                    time.sleep(0.5)
                else:
                    time.sleep(1)
                continue
            
            if hasattr(self, 'lbl_status'):
                self.lbl_status.config(text="CONNECTED", fg="#00ff88")
            
            buf = ctypes.create_string_buffer(65536); bytes_read = wintypes.DWORD(); leftover = ""
            while self.running:
                # Use a peek-like check or just rely on ReadFile failing
                if kernel32.ReadFile(h, buf, 65536, ctypes.byref(bytes_read), None) and bytes_read.value > 0:
                    try:
                        decoded = buf.raw[:bytes_read.value].decode('utf-8', 'ignore')
                        
                        # Filter out the \x01 dummy health check byte
                        if decoded == "\x01":
                            continue
                            
                        # If the dummy byte is part of a larger buffer, strip it out
                        if "\x01" in decoded:
                            decoded = decoded.replace("\x01", "")
                            if not decoded:
                                continue
                        
                        # DEBUG: Print to a file to see what we are getting
                        # with open("pipe_debug.txt", "a") as f:
                        #     f.write(f"RECEIVED: {repr(decoded)}\n")

                        lines = (leftover + decoded).split('\n')
                        leftover = lines.pop()
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if line:
                                try:
                                    # Handle cases where multiple JSON objects might be mashed together without newlines
                                    # (though splitting by \n usually handles this)
                                    if line.count('}{') > 0:
                                        line = line.replace('}{', '}\n{')
                                        sublines = line.split('\n')
                                        for subline in sublines:
                                            subline = subline.strip()
                                            if subline:
                                                data = json.loads(subline); data["timestamp"] = datetime.now()
                                                self.process_external_event(data, is_last=(i == len(lines)-1))
                                    else:
                                        data = json.loads(line); data["timestamp"] = datetime.now()
                                        self.process_external_event(data, is_last=(i == len(lines)-1))
                                except Exception as e:
                                    # Ignore tiny strings that might be remnants of dummy writes
                                    if len(line) > 5:
                                        try:
                                            with open("crash_log.txt", "a") as f:
                                                f.write(f"--- JSON ERROR {datetime.now()} ---\nLine: {line}\nError: {e}\n")
                                        except: pass
                    except Exception as e:
                        try:
                            with open("crash_log.txt", "a") as f:
                                f.write(f"--- PIPE READ ERROR {datetime.now()} ---\n{e}\n")
                        except: pass
                else:
                    # Pipe probably closed or error
                    err = kernel32.GetLastError()
                    if err != 0:
                        try:
                            with open("crash_log.txt", "a") as f:
                                f.write(f"--- PIPE DISCONNECT {datetime.now()} (Error: {err}) ---\n")
                        except: pass
                    break
            kernel32.CloseHandle(h)
            time.sleep(1) # Wait before reconnecting to avoid tight loop on failure

    def process_external_event(self, event, is_last=False):
        event_type = event.get("type")
        
        if event_type == "stats":
            name = event.get("name")
            if not name: return
            if name not in self.player_data:
                self.player_data[name] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0}
            
            p = self.player_data[name]
            p["damage"] = event.get("damage", 0)
            p["healing"] = event.get("healing", 0)
            p["dm_taken"] = event.get("taken", 0)
            p["dm_hits"] = event.get("hits", 0)
            p["dm_misses"] = event.get("misses", 0)
            p["dm_avoided"] = event.get("avoided", 0)
            p["aoe_hits"] = event.get("aoe", 0)
            p["lb_loot"] = event.get("loot", 0)
            p["lb_mobs"] = event.get("mobs", 0)
            p["lb_xp"] = event.get("xp", 0)

            self.locally_seen_players[name] = time.time()

            # Map total stats to real-time dm_ stats if combat just started
            if self.app_start_time and (time.time() - self.last_combat_time) <= self.time_window_dm:
                if p.get("dm_damage", 0) == 0: p["dm_damage"] = p["damage"]
                if p.get("dm_healing", 0) == 0: p["dm_healing"] = p["healing"]
                if p.get("dm_taken", 0) == 0: p["dm_taken"] = p["dm_taken"] # Already mapped above, but for clarity

            # Update last_combat_time if there is actual activity in these stats
            if p["damage"] > 0 or p["healing"] > 0 or p["dm_taken"] > 0:
                self.last_combat_time = time.time()
                if self.app_start_time is None:
                    # Look for the earliest event in memory if we have any, 
                    # otherwise use now.
                    if self.all_events:
                        self.app_start_time = self.all_events[0]["timestamp"]
                    else:
                        self.app_start_time = datetime.now()
            return

        source = event.get("source", "Unknown")
        damage = event.get("damage", 0)
        healing = event.get("healing", 0)
        item = event.get("item", "")
        timestamp = event.get("timestamp")
        target = event.get("target", "Unknown")
        ability = event.get("ability", "")
        is_mitigated = event.get("is_mitigated", False)
        
        # Handle armor reduction
        if event_type == "armor_reduction":
            if self.all_events:
                # Look back for the last 'taken' event to apply reduction
                for e in reversed(self.all_events):
                    if e["type"] == "taken" and e["damage"] > 0:
                        e["damage"] = max(0, e["damage"] - damage)
                        break
            return

        if (event_type == "xp"):
            if source not in self.player_data:
                self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0}
            
            p = self.player_data[source]
            amount = event.get("amount", 0)
            p["lb_xp"] = p.get("lb_xp", 0) + amount
            
            if "xp_history" not in p: p["xp_history"] = []
            p["xp_history"].append({"amount": amount, "type": event.get("xp_type", "Unknown"), "time": time.time()})
            if len(p["xp_history"]) > 100: p["xp_history"].pop(0)

            # Keep activity alive
            self.last_combat_time = time.time()
            if self.app_start_time is None:
                self.app_start_time = datetime.now()

            self.locally_seen_players[source] = time.time()
            return

        if (event_type == "loot"):
            if source not in self.player_data:
                self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0}
            
            p = self.player_data[source]
            p["lb_loot"] = p.get("lb_loot", 0) + 1
            
            # New loot fields
            if "total_credits" not in p: p["total_credits"] = 0
            if "looted_items" not in p: p["looted_items"] = []
            
            credits = event.get("credits", 0)
            item = event.get("item", "Unknown")
            
            if credits > 0:
                p["total_credits"] += credits
            elif item and item != "Unknown":
                p["looted_items"].append(item)
                if len(p["looted_items"]) > 100: # Limit history
                    p["looted_items"].pop(0)
            
            self.locally_seen_players[source] = time.time()
            return
            
        is_damage = damage > 0 or event_type in ["dealt", "taken", "other_dealt"]
        is_healing = healing > 0 or event_type == "healing"
        
        internal_event = {
            "timestamp": timestamp, 
            "type": event_type, 
            "source": source, 
            "target": target, 
            "damage": damage, 
            "healing": healing, 
            "item": item,
            "ability": ability,
            "is_mitigated": is_mitigated
        }

        if self.app_start_time is None and is_damage:
            self.app_start_time = timestamp; self.last_log_sync_time = timestamp; self.last_combat_time = time.time()
            max_hist = 65; history_limit = datetime.now() - timedelta(minutes=max_hist)
            self.all_events = [e for e in self.all_events if (e["timestamp"] and e["timestamp"] >= self.app_start_time) or (e["timestamp"] and e["timestamp"] >= history_limit)]

        self.all_events.append(internal_event)
        if len(self.all_events) > 5000: self.all_events = self.all_events[-5000:]

        if event_type == "command" and item.startswith("log"):
            try:
                mins = int(item[3:])
                if 1 <= mins <= 60:
                    from utils import save_log_segment
                    path = self.file_path_var.get().strip()
                    if path:
                        saved_to = save_log_segment(path, mins)
                        if saved_to:
                            print(f"DEBUG: Saved {mins} minutes of log to {saved_to}")
            except Exception as e:
                print(f"DEBUG: Failed to process log command: {e}")

        now = time.time()
        # Ensure we keep some history for windows that need it (skimmers/details usually 5-60 mins)
        history_limit = datetime.now() - timedelta(hours=1)
        if self.app_start_time and (now - self.last_combat_time > self.time_window_dm):
            # If we were in combat but it timed out, only reset real-time DM stats
            self.last_log_sync_time = None; self.leaderboard_data = {}; 
            for p in self.player_data:
                self.player_data[p]["dm_damage"] = 0
                self.player_data[p]["dm_healing"] = 0
                if "dm_taken" in self.player_data[p]: self.player_data[p]["dm_taken"] = 0
            
            # Reset app_start_time if we've been idle for too long, but be less aggressive
            if now - self.last_combat_time > 1800: # 30 minutes absolute idle
                self.app_start_time = None
            
            self.all_events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= history_limit]

        if is_damage:
            self.last_combat_time = now; self.last_log_sync_time = timestamp
            if self.app_start_time is None: self.app_start_time = timestamp

        if is_last or (now - self.last_ui_update_time > 0.02):
            if self.running:
                try:
                    self.root.after(0, lambda: self.refresh_ui_only(force=is_last))
                    self.last_ui_update_time = now
                except: pass

    def start_ticker_loop(self):
        if self.running:
            self.refresh_ui_only(force=False)
            self.root.after(100, self.start_ticker_loop)

    def refresh_ui_only(self, force=False):
        try:
            now_ts = time.time()
            if now_ts - self.last_pulse_time > 0.3:
                self.pulse_state = not self.pulse_state; self.last_pulse_time = now_ts
    
            # Update Managed Windows list first to ensure all windows are processed
            managed_wins = self._get_managed_windows()

            # Damage meter is highest priority for real-time feel
            self.damage_meter_win.refresh(force=force)
    
            # Alexa window doesn't need to refresh every tick, but keep it in loop for consistency
            if force or (now_ts - getattr(self, 'last_heavy_refresh', 0) >= 0.2):
                self.leaderboard_win.refresh(force=force)
                self.skimmers_win.refresh(force=force)
                self.details_win.refresh(force=force)
                self.alexa_win.refresh(force=force)
                self.last_heavy_refresh = now_ts
            
            # Options window doesn't need to refresh every tick, only when forced
            if force:
                self.options_win.refresh(force=True)
        except: pass

    def process_events_for_ui(self, all_events, manual=False):
        pass

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.ontop_btn.config(text="ONTOP: ON" if self.always_on_top else "ONTOP: OFF", fg=ACCENT_BLUE if self.always_on_top else TEXT_SECONDARY)

    def web_sync_loop(self):
        import urllib.request
        import json
        while self.running:
            try:
                if self.enable_sync.get() and self.api_url.get() and self.char_name.get():
                    # Prepare local data to send
                    # We send current session leaderboard data
                    # Only send data where "You" has been replaced by the actual character name
                    local_dmg = {p: d.get("damage", 0) for p, d in self.player_data.items() if d.get("damage", 0) > 0}
                    local_heal = {p: d.get("healing", 0) for p, d in self.player_data.items() if d.get("healing", 0) > 0}
                    local_loot = self.loot_data.copy()

                    if "You" in local_dmg:
                        local_dmg[self.char_name.get()] = local_dmg.pop("You")
                    if "You" in local_heal:
                        local_heal[self.char_name.get()] = local_heal.pop("You")
                    if "You" in local_loot:
                        local_loot[self.char_name.get()] = local_loot.pop("You")

                    # Filter local_dmg/heal to only include players we've seen locally
                    seen_recently = set(self.locally_seen_players.keys())
                    local_dmg = {p: v for p, v in local_dmg.items() if p in seen_recently or p == self.char_name.get()}
                    local_heal = {p: v for p, v in local_heal.items() if p in seen_recently or p == self.char_name.get()}

                    payload = {
                        "character": self.char_name.get(),
                        "timestamp": time.time(),
                        "data": {
                            "damage": local_dmg,
                            "healing": local_heal,
                            "loot": local_loot,
                        }
                    }
                    
                    data = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(self.api_url.get(), data=data, method='POST')
                    req.add_header('Content-Type', 'application/json')
                    
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            remote_data = json.loads(response.read().decode('utf-8'))
                            self.sync_data = remote_data
                            self.last_sync_time = time.time()
                
            except Exception as e:
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- SYNC ERROR {datetime.now()} ---\n{e}\n")
                except: pass
            
            time.sleep(10) # Sync every 10 seconds

    def setup_tray_icon(self):
        try:
            png_path = get_resource_path("livylogs.png")
            ico_path = get_resource_path("livylogs.ico")
            if os.path.exists(png_path):
                image = Image.open(png_path)
            elif os.path.exists(ico_path):
                image = Image.open(ico_path)
            else:
                image = Image.new('RGBA', (64, 64), color=(0, 160, 255, 255)) # Brighter blue square
            
            import webbrowser
            menu = (
                item('Show/Hide', self.toggle_visibility),
                item('About', lambda: webbrowser.open("https://github.com/livy2k/livylogs#readme")),
                item('Exit', self.on_exit)
            )
            self.tray_icon = pystray.Icon("LivyLogs", image, "LivyLogs", menu)
            self.tray_icon.visible = True
            # Double click tray icon to show/hide
            self.tray_icon.on_activate = lambda: self.root.after(0, self.toggle_visibility)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- TRAY ERROR {datetime.now()} ---\n{e}\n")
            except: pass
            
    def on_exit(self, icon=None, item=None):
        if hasattr(self, '_exiting') and self._exiting:
            return
        self._exiting = True
        
        # Immediate UI hiding to make it feel responsive
        try:
            self.root.withdraw()
            for win in self._get_managed_windows():
                try: win.withdraw()
                except: pass
        except: pass

        # Add a watchdog timer to force exit if cleanup hangs
        def force_kill():
            time.sleep(3)
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- WATCHDOG FORCE EXIT {datetime.now()} ---\n")
            except: pass
            os._exit(1)
        threading.Thread(target=force_kill, daemon=True).start()

        def background_cleanup():
            self.running = False
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- ON_EXIT CALLED {datetime.now()} ---\n")
            except: pass

            if hasattr(self, 'tray_icon'):
                try:
                    self.tray_icon.stop()
                except: pass
            
            # Kill any engine processes that might be running
            try:
                import subprocess
                subprocess.run(['taskkill', '/F', '/IM', 'LivyLogsEngine.exe', '/IM', 'parser.exe', '/IM', 'LL_Engine.exe', '/T'], 
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except: pass

            try:
                self.save_config()
            except: pass

            # Force exit to ensure the process actually terminates
            os._exit(0)

        # Run cleanup in a separate thread
        threading.Thread(target=background_cleanup, daemon=True).start()

    def save_config(self):
        if "General" not in self.config: self.config["General"] = {}
        self.config["General"].update({
            "log_path": self.file_path_var.get(),
            "transparency": str(self.target_alpha),
            "width": str(self.root.winfo_width()),
            "height": str(self.root.winfo_height()),
            "x": str(self.root.winfo_x()),
            "y": str(self.root.winfo_y()),
            "disable_warnings": str(self.disable_warnings.get()),
            "show_class_colors": str(self.show_class_colors.get())
        })
        
        # Save popout positions/sizes
        for win in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win, self.options_win]:
            if win.window and win.window.winfo_exists():
                if win.config_key not in self.config: self.config[win.config_key] = {}
                self.config[win.config_key].update({
                    "width": str(win.window.winfo_width()),
                    "height": str(win.window.winfo_height()),
                    "x": str(win.window.winfo_x()),
                    "y": str(win.window.winfo_y())
                })

        self.config.set("General", "character_name", self.char_name.get())
        self.config.set("General", "api_url", self.api_url.get())
        self.config.set("General", "enable_sync", str(self.enable_sync.get()))
        with open("settings.ini", "w") as f: self.config.write(f)

    def drag_window(self, event):
        self.is_interacting = True
        self.last_interaction_time = time.time()
        x, y = apply_snapping(self.root, self.root.winfo_pointerx() - self._offsetx, self.root.winfo_pointery() - self._offsety)
        self.root.geometry(f"+{x}+{y}")

    def click_window(self, event):
        self.is_interacting = True
        self.last_interaction_time = time.time()
        self._offsetx = event.x_root - self.root.winfo_x(); self._offsety = event.y_root - self.root.winfo_y()

    def release_window(self, event=None):
        self.is_interacting = False
        self.refresh_ui_only(force=True)

    def on_configure(self, event):
        if hasattr(self, "is_interacting") and self.is_interacting:
            self.last_interaction_time = time.time()

    def toggle_visibility(self, icon=None, item=None):
        if self.root.state() == "withdrawn":
            self._minimized_to_tray = False
            self.root.after(0, self.start_show)
        else:
            self._minimized_to_tray = True
            self.root.after(0, lambda: self.start_hide(minimize=True))


    def toggle_menu(self):
        self.is_dialog_open = True
        self.options_win.show()

    def on_options_closed(self):
        self.is_dialog_open = False
        # Re-set topmost state for all managed windows after a short delay
        # to ensure they come back on top of the game client correctly
        self.root.after(100, lambda: [
            user32.SetWindowPos(win.winfo_id(), HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            for win in self._get_managed_windows()
        ])
        # Force a refresh to catch up if we missed any updates while open
        self.refresh_ui_only(force=True)

    def select_log_filtered(self):
        from ui_base import ThemedListDialog
        from utils import extract_character_id
        import os
        import glob
        
        current_path = self.file_path_var.get()
        char_id = extract_character_id(current_path)
        
        # Try to find matching logs automatically
        if char_id:
            initial_dir = os.path.dirname(current_path) if current_path and os.path.exists(current_path) else os.getcwd()
            pattern = os.path.join(initial_dir, f"{char_id}_chatlog.txt")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                self.is_dialog_open = True
                def on_file_selected(p):
                    if p:
                        self.proceed_with_log(p, skip_prompt=True)
                
                ThemedListDialog(self.root, "Select Log File", matching_files, on_select=on_file_selected)
                return

        # If no char_id or no matching files found, fallback to standard
        self.change_log_path()

    def change_log_path(self):
        from tkinter import filedialog
        import os
        
        current_path = self.file_path_var.get()
        initial_dir = os.path.dirname(current_path) if current_path and os.path.exists(current_path) else None
        
        self.is_dialog_open = True
        p = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("SWG Chat Logs", "*_chatlog.txt"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        self.is_dialog_open = False
        if p:
            self.proceed_with_log(p)

    def proceed_with_log(self, p, skip_prompt=False):
        from utils import extract_character_id
        from ui_base import ThemedInputDialog, ThemedMessagebox
        
        current_path = self.file_path_var.get()
        char_id = extract_character_id(current_path)
        # If we had a char_id, verify the new one matches
        new_char_id = extract_character_id(p)
        
        def finalize(accepted=True):
            if not accepted:
                # User clicked NO - return to opening log selection
                self.root.after(100, self.change_log_path)
                return
            
            self.file_path_var.set(p)
            detected_name = extract_character_id(p)
            
            def apply_settings(new_name):
                if new_name:
                    self.char_name.set(new_name)
                elif not self.char_name.get():
                    self.char_name.set(detected_name)
                
                self.save_config()
                self.start_c_engine(p)
                # User clicked YES and finished - close options window
                if hasattr(self, 'options_win') and self.options_win and self.options_win.window and self.options_win.window.winfo_exists():
                    self.options_win.close()
                self.refresh_ui_only(force=True)

            if skip_prompt:
                apply_settings(None)
            else:
                self.is_dialog_open = True
                ThemedInputDialog(self.root, "Character Name", "Enter your Character Name for synchronization:", 
                                  initial_value=detected_name, on_submit=apply_settings)

        if char_id and new_char_id and new_char_id != char_id:
            self.is_dialog_open = True
            ThemedMessagebox.askyesno(self.root, "Character Mismatch", 
                                      f"The selected log ({new_char_id}) does not match your current character ({char_id}).\n\nAre you sure you want to switch?",
                                      on_close=finalize)
        else:
            finalize(True)

    def reset_all_data_manual(self):
        self.reset_damage_meter_manual()
        self.reset_leaderboard_manual()
        self.reset_skimmers_manual()
        self.reset_details_manual()
        self.refresh_ui_only(force=True)

    def toggle_test_mode(self, active=None):
        if active is not None:
            if self.test_mode.get() == active:
                return # No change
            self.test_mode.set(active)
            
        # Debounce/Lock
        now = time.time()
        if now - self._last_test_toggle < 0.5:
            return
        self._last_test_toggle = now

        if self.test_mode.get():
            # Reset generator flag
            if hasattr(self, '_generator_started'):
                del self._generator_started

            # Ensure any previous test thread is dead
            if self.test_thread and self.test_thread.is_alive():
                # We just let it exit via test_mode check
                pass

            # Start generator thread
            self.test_thread = threading.Thread(target=self.test_data_generator_loop, daemon=True)
            self.test_thread.start()
            
            def _bg_start_test():
                try:
                    if not hasattr(self, 'original_log_path') or not self.original_log_path:
                        self.original_log_path = self.file_path_var.get()
                    
                    test_log = os.path.join(os.getcwd(), "test_chatlog.txt")
                    if not os.path.exists(test_log):
                        with open(test_log, "w") as f:
                            f.write("[Spatial]  00:00:00 [GROUP] System: Welcome to the test log.\n")
                    
                    # Switch to test log
                    self.root.after(0, lambda: self.file_path_var.set(test_log))
                    
                    # RESTART ENGINE for test log
                    self.start_c_engine(test_log)
                    
                    # Immediate refresh to show connection status
                    self.root.after(0, lambda: self.refresh_ui_only(force=True))
                except Exception as e:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- TEST MODE START ERROR {datetime.now()} ---\n{e}\n")

            threading.Thread(target=_bg_start_test, daemon=True).start()
        else:
            def _bg_stop_test():
                try:
                    if hasattr(self, 'original_log_path') and self.original_log_path:
                        orig = self.original_log_path
                        self.original_log_path = None
                        self.root.after(0, lambda: self.file_path_var.set(orig))
                        if os.path.exists(orig):
                            self.start_c_engine(orig)
                    self.root.after(0, lambda: self.refresh_ui_only(force=True))
                except Exception as e:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- TEST MODE STOP ERROR {datetime.now()} ---\n{e}\n")

            threading.Thread(target=_bg_stop_test, daemon=True).start()

    def test_data_generator_loop(self):
        import random
        import time
        from datetime import datetime
        
        players = ["You", "Turd", "Leloglo", "Rehote", "Ma-o", "Fikiosa", "Eliemau"]
        items = ["Work light", "Broken Electrobinoculars", "A Damaged Datapad", "CDEF Pistol", "Stun Baton"]
        xp_types = ["Combat", "Weapon", "General", "Medicine"]
        
        log_path = os.path.join(os.getcwd(), "test_chatlog.txt")
        
        # Wait until we are CONNECTED before starting to generate data
        while self.running and self.test_mode.get():
            if hasattr(self, 'lbl_status') and self.lbl_status.cget("text") == "CONNECTED":
                time.sleep(1.5)
                break
            time.sleep(0.5)

        while self.running and self.test_mode.get():
            try:
                with open(log_path, "a") as f:
                    ts = datetime.now().strftime("%H:%M:%S")
                    event_type = random.random()
                    
                    if event_type < 0.6: # Damage/Combat
                        p1 = random.choice(players)
                        p2 = random.choice(players)
                        while p1 == p2: p2 = random.choice(players)
                        dmg = random.randint(50, 500)
                        line = f"[Spatial]  {ts} [GROUP] {p1} hits {p2} for {dmg} points of damage.\n"
                        f.write(line)
                    elif event_type < 0.7: # Loot credits
                        p = random.choice(players)
                        credits = random.randint(80, 150)
                        line = f"[Spatial]  {ts} [GROUP] {p} looted {credits} credits from a fallen foe.\n"
                        f.write(line)
                    elif event_type < 0.8: # Loot item
                        p = random.choice(players)
                        item = random.choice(items)
                        line = f"[Spatial]  {ts} [GROUP] {p} looted {item} from a fallen foe.\n"
                        f.write(line)
                    elif event_type < 0.9: # Mobs
                        p = random.choice(players)
                        line = f"[Spatial]  {ts} [GROUP] {p} has defeated a SpecForce marine.\n"
                        f.write(line)
                    else: # XP
                        xp = random.randint(100, 1000)
                        xt = random.choice(xp_types)
                        line = f"[Spatial]  {ts} [GROUP] You receive {xp} points of {xt} experience.\n"
                        f.write(line)
                    
                    f.flush()
            except Exception as e:
                try:
                    with open("crash_log.txt", "a") as cf:
                        cf.write(f"--- TEST GENERATOR ERROR {datetime.now()} ---\n{e}\n")
                except: pass
            
            time.sleep(random.uniform(0.5, 2.0))

    def reset_damage_meter_manual(self):
        self.last_dm_reset = datetime.now()
        self.refresh_ui_only(force=True)

    def reset_leaderboard_manual(self):
        self.last_lb_reset = datetime.now()
        self.leaderboard_win.drill_down_player = None
        self.refresh_ui_only(force=True)

    def reset_skimmers_manual(self):
        self.last_sk_reset = datetime.now()
        self.inventory_full = False
        self.skimmers_win.drill_down_player = None
        self.refresh_ui_only(force=True)

    def reset_details_manual(self):
        self.last_dt_reset = datetime.now()
        self.details_win.drill_down_player = None
        self.refresh_ui_only(force=True)

    def toggle_skimmer_search(self):
        self.skimmer_search_mode = not self.skimmer_search_mode
        self.skimmers_win.show(force_open=True)

    # Required for popout window resizing
    def init_resize_popout(self, e, w, dw, dh): self._rs_x = e.x_root; self._rs_y = e.y_root; self._rs_w = w.winfo_width(); self._rs_h = w.winfo_height()
    def do_resize_popout(self, e, w, dw, dh): w.geometry(f"{max(dw//3, self._rs_w + e.x_root - self._rs_x)}x{max(dh//3, self._rs_h + e.y_root - self._rs_y)}")
    def save_size(self, e): self.save_config()
    
    # Required for main window resizing
    def init_resize(self, e): 
        self.is_interacting = True
        self.last_interaction_time = time.time()
        self._rs_x = e.x_root; self._rs_y = e.y_root; self._rs_w = self.root.winfo_width(); self._rs_h = self.root.winfo_height()

    def do_resize(self, e): 
        self.is_interacting = True
        self.last_interaction_time = time.time()
        nw, nh = max(MIN_WIDTH, self._rs_w + e.x_root - self._rs_x), max(MIN_HEIGHT, self._rs_h + e.y_root - self._rs_y)
        self.root.geometry(f"{nw}x{nh}")
