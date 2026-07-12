"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
import os
import sys
import time
import json
import threading
import subprocess
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageTk
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
from utils import is_window_minimized, apply_snapping, extract_character_id, get_resource_path, normalize_name, is_probable_player
from ui_base import ThemedMessagebox

# Popout Windows
from windows.skimmers import SkimmersWindow
from windows.damage_meter import DamageMeterWindow
from windows.leaderboard import LeaderboardWindow
from windows.details import DetailsWindow
from windows.options import OptionsWindow
from windows.alexa import AlexaWindow
from windows.equalizer import EqualizerWindow
from windows.livius import LiviusWindow
from radio_manager import RadioManager, SAFE_RAP_STATIONS
from killstreak_manager import KillstreakManager


class CombatLogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Combat Log Analyzer")
        self.root.geometry("400x50")
        self.root.configure(bg=WINDOW_BG)
        
        # Font objects
        self.font_stats_obj = tkfont.Font(family="Segoe UI Variable Display", size=20, weight="bold")
        self.font_title_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_small_obj = tkfont.Font(family="Segoe UI", size=9)
        self.font_button_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Load Lilita One font if available
        self.lilita_font_path = r"C:\Users\LivyC\Documents\UImaker\assets\fonts\LilitaOne\LilitaOne.ttf"
        self.lilita_family = "Lilita One"
        if os.path.exists(self.lilita_font_path):
            try:
                # Attempt to load font on Windows using ctypes
                # gdi32.AddFontResourceExW
                FR_PRIVATE = 0x10
                res = ctypes.windll.gdi32.AddFontResourceExW(self.lilita_font_path, FR_PRIVATE, 0)
                if res > 0:
                     print(f"[DEBUG] Loaded custom font: {self.lilita_family} from {self.lilita_font_path}")
                     # Refresh font list
                     # ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
                else:
                     print(f"[DEBUG] Failed to load font resource: {self.lilita_font_path}")
            except Exception as e:
                print(f"[DEBUG] Error loading font: {e}")
        
        self.config = ConfigParser()
        self.config.read("settings.ini")

        initial_log_path = self.config.get("General", "log_path", fallback="")
        initial_alpha = self.config.getfloat("General", "transparency", fallback=1.0)
        initial_width = max(MIN_WIDTH, self.config.getint("General", "width", fallback=400))
        initial_height = max(MIN_HEIGHT, self.config.getint("General", "height", fallback=50))
        initial_x = self.config.get("General", "x", fallback="971")
        initial_y = self.config.get("General", "y", fallback="92")

        self.root.geometry(f"{initial_width}x{initial_height}+{initial_x}+{initial_y}")
        
        # Override geometry if it doesn't match the design 700x400
        # The user said the app "isn't close" so I'm ensuring it starts at 700x400
        if initial_width != 700 or initial_height != 400:
             self.root.geometry(f"700x400+{initial_x}+{initial_y}")
        
        # Set window icon
        try:
            from PIL import Image, ImageTk
            icon_path = get_resource_path("iconbell.jpg")
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                # Resize for icon (typically 32x32 or 16x16)
                icon_photo = ImageTk.PhotoImage(icon_img.resize((32, 32), Image.Resampling.LANCZOS))
                self.root.iconphoto(True, icon_photo)
                # Keep a reference to prevent garbage collection
                self._icon_photo = icon_photo
        except Exception as e:
            print(f"[DEBUG] Error loading icon: {e}")

        if initial_alpha < 0.01: initial_alpha = 1.0
        self.target_alpha = initial_alpha
        self.current_alpha = initial_alpha
        self.root.attributes("-alpha", initial_alpha)
        self.root.overrideredirect(True)
        
        # Enable basic copy/select all globally for the main window
        self.root.bind("<Control-c>", self._on_global_copy)
        self.root.bind("<Control-a>", self._on_global_select_all)
        self.root.bind("<Button-3>", self.show_context_menu)
        
        # Ensure it doesn't show in taskbar by setting it as a tool window
        try:
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            
            # Map the window to ensure winfo_id is valid
            self.root.update() 
            wid = self.root.winfo_id()
            
            if wid > 0:
                hwnd = ctypes.windll.user32.GetParent(wid)
                if hwnd > 0:
                    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW)
        except Exception as e:
            print(f"[DEBUG] Error setting toolwindow style: {e}")
        
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

        try:
            self.skimmers_win = SkimmersWindow(self)
            self.damage_meter_win = DamageMeterWindow(self)
            self.leaderboard_win = LeaderboardWindow(self)
            self.details_win = DetailsWindow(self)
            self.options_win = OptionsWindow(self)
            self.alexa_win = AlexaWindow(self)
            self.eq_win = EqualizerWindow(self)
            self.livius_win = LiviusWindow(self)
        except Exception as e:
            print(f"[DEBUG] Error creating subwindows: {e}")
            # Ensure defaults exist
            if not hasattr(self, 'skimmers_win'): self.skimmers_win = None
            if not hasattr(self, 'damage_meter_win'): self.damage_meter_win = None
            if not hasattr(self, 'leaderboard_win'): self.leaderboard_win = None
            if not hasattr(self, 'details_win'): self.details_win = None
            if not hasattr(self, 'options_win'): self.options_win = None
            if not hasattr(self, 'alexa_win'): self.alexa_win = None
            if not hasattr(self, 'livius_win'): self.livius_win = None

        self.calc_win = None
        self.armor_win = None
        self.hitmiss_win = None
        self.resists_win = None
        
        # UI State
        self.details_tab = "all"
        self.skimmer_tab = "loot"
        self.always_on_top = True
        
        self._managed_windows = [
            self.skimmers_win, self.damage_meter_win, self.leaderboard_win, 
            self.details_win, self.options_win, self.alexa_win, self.livius_win, None, None # placeholders for calc_win, armor_win
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
        self.leaderboard_data = {}
        self.known_npcs = set()
        self.known_players = set()
        self.friendly_players = set()
        self.enemy_players = set()
        self.player_arrival_order = [] # List to track order of first appearance
        self.status_cooldowns = {} # {player_name: {status_type: timestamp}}
        self.damage_history = {} # {player_name: [(timestamp, damage)]}
        self.damage_taken_history = {} # {player_name: [(timestamp, damage_taken)]}
        self.healing_history = {} # {player_name: [(timestamp, healing)]}
        self.top_dps_durations = {} # {player_name: total_seconds_at_top}
        self.top_tank_durations = {} # {player_name: total_seconds_at_top_tank}
        self.top_healing_durations = {} # {player_name: total_seconds_at_top_healing}
        self.current_top_dps = {'friendly': None, 'enemy': None}
        self.current_top_tank = {'friendly': None, 'enemy': None}
        self.current_top_healing = {'friendly': None, 'enemy': None}
        self.current_focus_target = {'friendly': None, 'enemy': None}
        self.last_top_stats_check = time.time()
        self.permanent_drops = {} # { "item_name": ["dropper1", "dropper2"] }
        self.load_permanent_drops()
        
        self.load_bosses()
        self.load_filters()
        self.load_class_configs()

        # Radio Manager
        try:
            self.radio_mgr = RadioManager(status_callback=self._update_radio_ui)
        except Exception as e:
            print(f"[DEBUG] Error initializing RadioManager: {e}")
            self.radio_mgr = None

        try:
            self.killstreak_mgr = KillstreakManager(sfx_dir=os.path.join(os.getcwd(), "sfx"))
        except Exception as e:
            print(f"[DEBUG] Error initializing KillstreakManager: {e}")
            self.killstreak_mgr = None

        try:
            self.build_layout()
        except Exception as e:
            print(f"[DEBUG] Error building layout: {e}")
        
        self.pulse_state = False
        self.last_pulse_time = 0
        self.last_ui_update_time = 0
        self.last_combat_time = 0
        self.app_start_time = None
        self._encounter_start_stats = {}
        self.session_start_time = datetime.now()
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
        self.skimmer_search_query = tk.StringVar()
        self.always_on_top = True
        self.is_dialog_open = False
        self.target_game_hwnd = None

        # self.radio_mgr = RadioManager(status_callback=self._update_radio_ui) # Moved up

        self.initial_show()
        threading.Thread(target=self.start_pipe_listener, daemon=True).start()
        threading.Thread(target=self.web_sync_loop, daemon=True).start()
        self.setup_tray_icon()
        self.start_ticker_loop()
        self.root.after(500, self.check_target_window)
        if initial_log_path:
            # Check if it's the test log in testing dir
            test_path = os.path.join(os.getcwd(), "testing", "test_chatlog.txt")
            if initial_log_path == "test_chatlog.txt" or initial_log_path == test_path:
                initial_log_path = test_path
            self.root.after(1000, lambda: self.start_c_engine(initial_log_path))

    def load_permanent_drops(self):
        try:
            path = get_resource_path("drops.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.permanent_drops = json.load(f)
        except Exception as e:
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"Error loading permanent drops: {e}\n")
            except: pass

    def save_permanent_drops(self):
        try:
            # Sort the data for cleaner JSON
            sorted_drops = {k: sorted(v) for k, v in sorted(self.permanent_drops.items())}
            # For simplicity, save to current directory
            with open("drops.json", "w") as f:
                json.dump(sorted_drops, f, indent=4)
        except Exception as e:
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"Error saving permanent drops: {e}\n")
            except: pass

    def load_bosses(self):
        self.bosses = []
        try:
            path = get_resource_path(os.path.join("filters", "bosses.txt"))
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        name = line.strip()
                        if name and not name.startswith("#"):
                            self.bosses.append(name.lower())
        except Exception as e:
            pass # Suppress log loading errors for clean UI experience

    def load_filters(self):
        self.filters = []
        try:
            path = get_resource_path(os.path.join("filters", "filters.txt"))
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        phrase = line.rstrip("\n").rstrip("\r")
                        if phrase and not phrase.startswith("#"):
                            self.filters.append(phrase.lower())
        except Exception as e:
            pass # Suppress for clean UI experience

    def load_class_configs(self):
        self.class_configs = {}
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
                                    if not color.startswith("#"): color = "#" + color
                                    start_idx = 1
                                else:
                                    start_idx = 0
                                
                                for line in lines[start_idx:]:
                                    ability = line.strip()
                                    if ability and not ability.startswith("#"):
                                        abilities.add(ability.lower())
                        self.class_configs[class_name] = {"color": color, "abilities": abilities}
        except Exception as e:
            pass # Suppress for clean UI experience

    def initial_show(self):
        try:
            # self.current_alpha = 0.0
            # self.root.attributes("-alpha", 0.0)
            self.root.overrideredirect(True)
            self.root.deiconify()
            if self.always_on_top:
                self.root.attributes("-topmost", True)
        except: pass

    def _get_managed_windows(self):
        managed = [self.root]
        for w in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win, self.options_win, self.alexa_win, self.calc_win, self.livius_win]:
            if w and w.window and w.window.winfo_exists(): managed.append(w.window)
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
                is_game_title = any(s in fg_title for s in ["swgclient", "star wars galaxies"])
                
                # Lock onto the first opened SWG client
                if is_game_title:
                    if self.target_game_hwnd is None:
                        # First time seeing a game window, lock onto it
                        self.target_game_hwnd = fg_hwnd
                    elif self.target_game_hwnd != fg_hwnd:
                        # Verify if the target window still exists
                        if not user32.IsWindow(self.target_game_hwnd):
                            # Target window closed, lock onto this new one
                            self.target_game_hwnd = fg_hwnd
                
                is_game = (is_game_title and self.target_game_hwnd == fg_hwnd)
                
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
                
                # If we are already in game/safe mode, and the current window being checked is part of our app,
                # we don't want to flip the state to 'hidden' just because it's not the game.
                # The fg_pid check above handles this globally for the process.

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
                        # Only hide if we aren't always_on_top
                        if not self.always_on_top:
                            self.root.attributes("-topmost", False)
                            for win in self._get_managed_windows():
                                if win != self.root:
                                    if win.state() != "withdrawn":
                                        win.withdraw()
                else:
                    # Even if state is same, ensure topmost is maintained if in game
                    if target_state == "game":
                        try:
                            if not self.root.attributes("-topmost") and self.root.state() != "withdrawn":
                                self.root.attributes("-topmost", True)
                        except: pass
                        
                        for win in self._get_managed_windows():
                            if win != self.root:
                                try:
                                    if not win.attributes("-topmost") and win.state() != "withdrawn":
                                        win.attributes("-topmost", True)
                                except: pass
            
        except Exception as e:
            pass
            
        self.root.after(500, self.check_target_window)

    def start_show(self):
        self._minimized_to_tray = False
        if self.root.state() == "withdrawn":
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.root.lift()
        
        for win in self._get_managed_windows():
            try:
                if win.state() == "withdrawn":
                    win.deiconify()
                    win.lift()
                win.attributes("-topmost", True)
            except: pass
        
        if self.current_alpha < self.target_alpha:
            self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.05)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.root.after(5, self.fade_in)

    def start_hide(self, minimize=True):
        self.fade_out(minimize=minimize)
        if minimize:
            self._minimized_to_tray = True
            # When we hide, we also hide managed windows
            for win in self._get_managed_windows():
                try: win.withdraw()
                except: pass

    def fade_out(self, minimize=True):
        if self.current_alpha > 0:
            self.current_alpha = max(0, self.current_alpha - 0.05)
            for win in self._get_managed_windows(): 
                try: win.attributes("-alpha", self.current_alpha)
                except: pass
            self.root.after(5, lambda: self.fade_out(minimize=minimize))
        else:
            if minimize:
                for win in self._get_managed_windows():
                    try:
                        if win.state() != "withdrawn":
                            win.withdraw()
                    except: pass

    def start_c_engine(self, log_path):
        def _bg_start():
            # Terminate any existing engine processes first
            try:
                import subprocess
                # Use absolute path of the script directory
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Use taskkill to clean up any orphaned engines
                # We wrap individual calls to handle Access Denied errors more gracefully
                for proc_name in ['parser.exe']:
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
                    res = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq parser.exe'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if "parser.exe" not in res.stdout:
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
            
            # Try to start the engine
            # Note: Some versions might show 'Access is denied' if they are being updated or blocked
            possible_exes = ["parser.exe"]
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
                    log_file_path = os.path.join(base_dir, "testing", "engine_debug.txt")
                    if not os.path.exists(os.path.dirname(log_file_path)):
                        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                    with open(log_file_path, "a") as debug_file:
                        debug_file.write(f"--- LAUNCHING ENGINE {datetime.now()} ---\nPath: {exe_path}\nLog: {log_path}\n")
                    
                    # We use a very simple Popen call
                    # Using CREATE_NO_WINDOW and ensuring we don't redirect to pipes that might clog
                    # We also add DETACHED_PROCESS to help it live independently of the UI thread if needed
                    DETACHED_PROCESS = 0x00000008
                    print(f"[DEBUG] Engine starting: {exe_path}")
                    print(f"[DEBUG] Target log: {log_path}")
                    
                    proc = subprocess.Popen([exe_path, log_path], 
                                     cwd=base_dir,
                                     shell=False,
                                     stdin=subprocess.DEVNULL,
                                     stdout=None, # Allow output to console for PyCharm visibility
                                     stderr=None,
                                     creationflags=subprocess.CREATE_NO_WINDOW | DETACHED_PROCESS)
                    
                    print(f"[DEBUG] Engine process created. PID: {proc.pid}")
                    
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

    def _load_dynamic_labels(self):
        self.dynamic_labels = {}
        labels_file = "ui_labels_map.txt"
        if os.path.exists(labels_file):
            try:
                with open(labels_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        # Format: Name, X, Y, [FG], [Shape], [W], [H], [Font], [Size]
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            name = parts[0]
                            try:
                                x = float(parts[1])
                                y = float(parts[2])
                                fg = parts[3] if len(parts) > 3 else None
                                w = float(parts[5]) if len(parts) > 5 else 0
                                h = float(parts[6]) if len(parts) > 6 else 0
                                font_fam = parts[7] if len(parts) > 7 else None
                                font_size = int(parts[8]) if len(parts) > 8 else None
                                
                                self.dynamic_labels[name.upper()] = {
                                    "x": x, "y": y, "fg": fg, "w": w, "h": h,
                                    "font": font_fam, "size": font_size
                                }
                            except ValueError: continue
            except Exception as e:
                print(f"Error loading dynamic labels: {e}")

    def build_layout(self):
        self._load_dynamic_labels()
        
        # Clean up existing layout if it exists
        if hasattr(self, 'main_canvas') and self.main_canvas.winfo_exists():
            self.main_canvas.destroy()
            
        # Load the radio base image
        try:
            self.bg_image_raw = Image.open(get_resource_path("uimaker_bg.jpg"))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image_raw)
        except Exception as e:
            # Try documents path if not in current dir
            try:
                self.bg_image_raw = Image.open(r"C:\Users\LivyC\Documents\UImaker\assets\images\8c032fb61d.jpg")
                self.bg_photo = ImageTk.PhotoImage(self.bg_image_raw)
            except:
                print(f"Error loading background image: {e}")
                self.bg_photo = None

        # Set window size to match UImaker design exactly (700x400)
        img_w, img_h = 700, 400
        self.root.geometry(f"{img_w}x{img_h}")
        self.root.resizable(False, False)
        
        # Transparent background for "smoke" effect
        try:
            # We use a color that is unlikely to be used in the UI for transparency
            # Windows allows a transparent color key. 
            # Or we can use -alpha for overall transparency.
            # User said "smoke", which often means semi-transparent black.
            # But "still not smoke" might mean they want the window background itself
            # to be completely transparent where the image isn't.
            TRANS_COLOR = '#000001'
            self.root.config(bg=TRANS_COLOR)
            self.root.wm_attributes("-transparentcolor", TRANS_COLOR)
            self.root.wm_attributes("-alpha", self.target_alpha)
        except: pass
        
        # Remove title bar for a clean UI look
        try:
            self.root.overrideredirect(True)
        except: pass
        
        self.main_canvas = tk.Canvas(self.root, width=img_w, height=img_h, 
                                     bg=TRANS_COLOR, highlightthickness=0)
        self.main_canvas.pack(fill=tk.BOTH, expand=True)
        
        if self.bg_photo:
            # Match window size to background image size (typically 638x154)
            bg_w, bg_h = self.bg_image_raw.size
            if bg_w > 0 and bg_h > 0:
                img_w, img_h = bg_w, bg_h
                self.root.geometry(f"{img_w}x{img_h}")
                self.main_canvas.config(width=img_w, height=img_h)
                # Position image at (0, 0)
                self.main_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_image")
                
                # UImaker design notes:
                # The original design used a 700x400 canvas.
                # The background image (638x154) was placed at (178, 107) with scale=0.5.
                # This means it appeared as 319x77 in the design tool.
                # Coordinates for labels were absolute to the 700x400 canvas.
                # To achieve 1:1 parity on a full-sized 638x154 background:
                # 1. We calculate position relative to the design image start (178, 107).
                # 2. We scale that relative offset by 2x (since 638 / 319 = 2).
                
                self.coord_offset_x = 0 # Not used directly anymore, but kept for safety
                self.coord_offset_y = 0
            else:
                self.main_canvas.create_image(178, 107, image=self.bg_photo, anchor="nw", tags="bg_image")
                self.coord_offset_x = 0
                self.coord_offset_y = 0
        else:
            self.coord_offset_x = 0
            self.coord_offset_y = 0
            
        # Bind dragging to the entire canvas
        self.main_canvas.bind("<Button-1>", self.click_window)
        self.main_canvas.bind("<B1-Motion>", self.drag_window)
        self.main_canvas.bind("<ButtonRelease-1>", self.release_window)
        self.root.bind("<Configure>", self.on_configure)

        def create_ui_label(name, x, y, cmd=None, fg=TEXT_SECONDARY, font_obj=None, tags=None, anchor="nw"):
            if font_obj is None:
                font_obj = self.font_small_obj
            
            # Use canvas text for "transparency"
            text_id = self.main_canvas.create_text(x, y, text=name, fill=fg, font=font_obj, anchor=anchor, tags=tags)
            
            if cmd:
                # Handle both types of callbacks: those that expect 'e' and those that don't
                def safe_call(e):
                    try:
                        cmd(e)
                    except TypeError:
                        try: cmd()
                        except Exception as ex:
                            try:
                                with open("crash_log.txt", "a") as f:
                                    f.write(f"Label Command Error ({name}): {ex}\n")
                            except: pass
                self.main_canvas.tag_bind(text_id, "<Button-1>", safe_call)
                
                # Hover effects
                def on_enter(e, tid=text_id, color=TEXT_ACCENT):
                    self.main_canvas.itemconfig(tid, fill=color)
                    self.main_canvas.config(cursor="hand2")
                def on_leave(e, tid=text_id, color=fg):
                    self.main_canvas.itemconfig(tid, fill=color)
                    self.main_canvas.config(cursor="")
                
                self.main_canvas.tag_bind(text_id, "<Enter>", on_enter)
                self.main_canvas.tag_bind(text_id, "<Leave>", on_leave)
            
            return text_id

        # Place labels based on UImaker coordinates
        def get_pos(name, default_x, default_y, default_fg=TEXT_SECONDARY, default_size=9):
            data = self.dynamic_labels.get(name.upper(), {})
            raw_x = data.get("x", default_x) if data else default_x
            raw_y = data.get("y", default_y) if data else default_y
            fg = data.get("fg", default_fg) if data else default_fg
            size = data.get("size", default_size) if data else default_size
            
            # The file now uses 1:1 coordinates relative to the 638x154 window.
            # No transformation is needed.
            
            return raw_x, raw_y, fg, size
        
        self.build_layout_get_pos = get_pos

        # In UImaker design, the background is 638x154 and placed at (178, 107).
        # However, the window is 700x400.
        # The user says "background isnt fitting our window size".
        # Let's ensure the canvas is exactly 700x400 and background is centered if desired,
        # but the design specifies absolute (178, 107).
        # Actually, if the background image itself should be the window size (or vice versa), 
        # but the user provided assets that are 638x154.
        
        # Setup: 240, 129
        sx, sy, sfg, ssz = get_pos("SETUP", 129, 49, "#d21a17", 7)
        if "SETTINGS" in self.dynamic_labels: 
             sx, sy, sfg, ssz = get_pos("SETTINGS", sx, sy, sfg, ssz)
        self.btn_setup = create_ui_label("SETUP", sx, sy, self.toggle_menu, fg=sfg, 
                                         font_obj=tkfont.Font(family="Lilita One", size=ssz))

        # Alexa: 236, 151
        ax, ay, afg, asz = get_pos("ALEXA", 121, 98, "#d21a18", 7)
        self.btn_alexa = create_ui_label("ALEXA", ax, ay, self.alexa_win.show, fg=afg,
                                         font_obj=tkfont.Font(family="Lilita One", size=asz))
        
        # DMG METER: 292, 163
        dx, dy, dfg, dsz = get_pos("DMG METER", 233, 123, "#d31a18", 5)
        self.lbl_dmg = create_ui_label("DMG METER", dx, dy, self.damage_meter_win.show, fg=dfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=dsz))
        
        # Details: 342, 164
        tx, ty, tfg, tsz = get_pos("DETAILS", 333, 123, "#d31a18", 5)
        self.lbl_det = create_ui_label("DETAILS", tx, ty, self.details_win.show, fg=tfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=tsz))
        
        # Skimmers: 381, 162
        kx, ky, kfg, ksz = get_pos("SKIMMERS", 411, 124, "#d31a18", 5)
        self.lbl_skm = create_ui_label("SKIMMERS", kx, ky, self.skimmers_win.show, fg=kfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=ksz))

        # Livius: 226, 164
        lx, ly, lfg, lsz = get_pos("LIVIUS", 101, 124, "#bbbbbb", 7)
        self.lbl_livius = create_ui_label("LIVIUS", lx, ly, self.livius_win.show, fg=lfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=lsz))

        # JOG
        jx, jy, jfg, jsz = get_pos("JOG", 595, -74, "#ececec", 5)
        self.lbl_jog = create_ui_label("JOG", jx, jy, None, fg=jfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=jsz))

        # ON - Replaced with Connectivity Status Dot
        onx, ony, onfg, onsz = get_pos("ON", 26, 33, "#d31a18", 5)
        # We create a circle (oval) instead of text for the ON label.
        # onsz is used here as a proxy for radius/diameter.
        self.status_id = self.main_canvas.create_oval(onx, ony, onx + 10, ony + 10, fill="#ff4444", outline="", tags="status_dot")

        # Gharv
        gx, gy, gfg, gsz = get_pos("GHARV", 139, 76, "#d21a18", 6)
        self.lbl_gharv = create_ui_label("GHARV", gx, gy, None, fg=gfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=gsz))

        
        # Text_6: Clock (411, 114) - design uses 'Clock' as header
        # We'll skip the 'CLOCK' header label to avoid clutter, as the time value is displayed here.
        # self.lbl_clock_header = create_ui_label("CLOCK", 411, 114, None, fg="#60fc17", 
        #                                        font_obj=tkfont.Font(family="Lilita One", size=7))

        # Item Link: 419, 165
        ix, iy, ifg, isz = get_pos("ITEM LINK", 487, 124, "#d31a18", 5)
        self.lbl_itemlink = create_ui_label("ITEM LINK", ix, iy, None, fg=ifg,
                                         font_obj=tkfont.Font(family="Lilita One", size=isz))

        # Bass Boost: Bottom Left
        bbx, bby, bbfg, bbsz = get_pos("BASS BOOST", 25, 129, "#d21a17", 5)
        self.lbl_bassboost = create_ui_label("BASS\nBOOST", bbx, bby, self.open_equalizer, fg=bbfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=bbsz))

        # Reset: 261, 163
        rx, ry, rfg, rsz = get_pos("RESET", 171, 122, "#d31a18", 4)
        self.btn_reset = create_ui_label("RESET", rx, ry, self.reset_session_data, fg=rfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=rsz))

        # XP: 272, 117
        xx, xy, xfg, xsz = get_pos("XP", 200, 23, "#60fc17", 10)
        self.lbl_xp = create_ui_label("XP", xx, xy, None, fg=xfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=xsz))

        # XP/H: 364, 117
        xhx, xhy, xhfg, xhsz = get_pos("XP/H", 380, 23, "#60fc17", 10)
        self.lbl_xph = create_ui_label("XP/H", xhx, xhy, None, fg=xhfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=xhsz))

        # Damage: 218, 117
        dmx, dmy, dmfg, dmsz = get_pos("DAMAGE", 80, 23, "#d31a17", 10)
        self.lbl_damage_header = create_ui_label("DAMAGE", dmx, dmy, None, fg=dmfg,
                                         font_obj=tkfont.Font(family="Lilita One", size=dmsz))

        # XP Labels - values aligned horizontally to the right of headers
        self.lbl_damage = create_ui_label("0", dmx + 60, dmy, None, fg="#ffffff", font_obj=tkfont.Font(family="Lilita One", size=10))
        xpx, xpy, _, _ = get_pos("XP", 200, 23)
        xphx, xphy, _, _ = get_pos("XP/H", 380, 23)
        self.lbl_xp_val = create_ui_label("0", xpx + 40, xpy, None, fg="#ffffff", font_obj=tkfont.Font(family="Lilita One", size=10))
        self.lbl_xph_val = create_ui_label("0", xphx + 50, xphy, None, fg="#ffffff", font_obj=tkfont.Font(family="Lilita One", size=10))

        # Text_6: Clock (411, 114) - design uses 'Clock' as header
        clx, cly, clfg, clsz = get_pos("CLOCK", 471, 9, "#60fc17", 7)
        # Clock value remains 14px below the header position as per previous layout
        self.clock_id = self.main_canvas.create_text(clx, cly + 14, text="00:00:00", fill=clfg, 
                                                     font=tkfont.Font(family="Lilita One", size=10), anchor="nw")
        self.update_clock()

        # AUX Label - positioned right of Clock
        ax, ay, afg, asz = get_pos("AUX", 573.5, 17, "#bbbbbb", 10)
        self.lbl_aux = create_ui_label("AUX", ax, ay, self.open_aux_mode, fg=afg, 
                                       font_obj=tkfont.Font(family="Lilita One", size=asz), anchor="center")

        px, py, pfg, psz = get_pos("PLAY", 551, 30, "#d31a18", 10)
        self.lbl_play = create_ui_label("▶", px, py, lambda e: self.radio_mgr.pause() if self.radio_mgr else None, fg=pfg,
                                        font_obj=tkfont.Font(family="Lilita One", size=psz))
        
        pax, pay, pafg, pasz = get_pos("PAUSE", 566, 30, "#d31a18", 10)
        self.lbl_pause = create_ui_label("||", pax, pay, lambda e: self.radio_mgr.pause() if self.radio_mgr else None, fg=pafg,
                                         font_obj=tkfont.Font(family="Lilita One", size=pasz))
        
        stx, sty, stfg, stsz = get_pos("STOP", 581, 30, "#d31a18", 10)
        self.lbl_stop = create_ui_label("■", stx, sty, lambda e: self.radio_mgr.stop() if self.radio_mgr else None, fg=stfg,
                                        font_obj=tkfont.Font(family="Lilita One", size=stsz))
        
        skx, sky, skfg, sksz = get_pos("SKIP", 596, 30, "#d31a18", 10)
        self.lbl_skip = create_ui_label("⏭", skx, sky, lambda e: self.radio_mgr.next_track() if self.radio_mgr else None, skfg, sksz)

        # Exit 590, 100
        ex, ey, efg, esz = get_pos("EXIT", 829, -4, "#ff4444", 12)
        # Check if EXIT is already in dynamic labels, if not, add it for compatibility
        if "EXIT" not in self.dynamic_labels:
            self.dynamic_labels["EXIT"] = {"x": 829, "y": -4, "fg": "#ff4444", "size": 12}
        
        self.btn_exit = create_ui_label(" ✕ ", ex, ey, self.on_exit, fg=efg, font_obj=("Segoe UI", esz))
        
        # Volume Knob Line (Rotating Knob)
        vx, vy, vfg, vsz = get_pos("VOL_DOT", 51, 74, "#ffffff", 5)
        # The user wants a line that rotates 355 degrees around its right edge.
        # Center of rotation is the right edge (vx+10, vy+5). Line length is 20 pixels.
        self.knob_cx = vx + 10
        self.knob_cy = vy + 5
        self.knob_len = 30
        self.vol_knob_id = self.main_canvas.create_line(self.knob_cx - self.knob_len, self.knob_cy, self.knob_cx, self.knob_cy, 
                                                        fill=vfg, width=3, tags="vol_knob")
        
        # Interaction area for the knob - a larger invisible rectangle or oval
        self.knob_area_id = self.main_canvas.create_oval(self.knob_cx - 40, self.knob_cy - 40, self.knob_cx + 40, self.knob_cy + 40,
                                                        fill="", outline="", tags="vol_knob_area")

        self._last_knob_angle = getattr(self, '_last_knob_angle', 90)
        self.update_knob_visual(self._last_knob_angle)

        def on_knob_drag(e):
            if not self.radio_mgr: return "break"
            import math
            # Mark that we are interacting to prevent refresh_ui_only from overriding
            self.is_interacting = True
            self.last_interaction_time = time.time()

            # Initialize _last_adj_angle if not present
            if not hasattr(self, '_last_adj_angle'):
                if hasattr(self, 'radio_mgr'):
                    vol_stage = int((self.radio_mgr.volume / 100.0) * 11)
                    self._last_adj_angle = vol_stage * 30.0
                else:
                    self._last_adj_angle = 0

            # Calculate angle relative to knob center (right edge)
            dx = e.x - self.knob_cx
            dy = e.y - self.knob_cy
            
            # atan2 returns radians between -pi and pi. 
            angle_rad = math.atan2(dy, dx)
            # Convert to degrees (0 is right, 180 is left, 270 is up, 90 is down)
            angle_deg = math.degrees(angle_rad) % 360
            
            # Map angle to volume based on a clock face starting at 6 o'clock (down)
            # 6 o'clock (down) = 90 deg
            # 9 o'clock (left) = 180 deg
            # 12 o'clock (up) = 270 deg
            # 3 o'clock (right) = 0/360 deg
            # 5 o'clock = 60 deg (30 deg past 4 o'clock, which is 30 deg)
            
            # Adjust angle so that 6 o'clock (90 deg) is the start (0)
            adj_angle = (angle_deg - 90) % 360
            
            # Rotation is 30 degrees per volume unit (0-11)
            # Total range: 11 * 30 = 330 degrees
            # Dead zone: 330 to 360 (30 degrees)
            
            # Implementation of strict deadzone/stop:
            # We want to prevent jumping between Volume 0 (adj_angle=0) and Volume 11 (adj_angle=330)
            # if the mouse moves into the deadzone (330-360).
            
            # Get the previous adjusted angle to detect direction and cross-over
            prev_adj = getattr(self, '_last_adj_angle', 0)
            
            if 330 < adj_angle < 360:
                # User moved into the deadzone. Snap to the nearest limit based on previous position.
                if prev_adj < 165: # Closer to 0
                    adj_angle = 0
                else: # Closer to 330
                    adj_angle = 330
            
            # Save the current adj_angle for the next drag event
            self._last_adj_angle = adj_angle
            
            new_vol_stage = int(round(adj_angle / 30.0))
            if new_vol_stage > 11: new_vol_stage = 11
            
            # Update volume dynamically
            # We use a power curve for more natural volume steps (logarithmic human hearing)
            # stage 11 is still 100%, but the steps leading to it are more gradual
            # ratio = new_vol_stage / 11.0
            # target_vol = int((ratio ** 2) * 100)
            # However, user says 11 jumps 15db, which suggests the previous linear 100% was already high.
            # In VLC, 100 is 100%. If it jumps at 11, maybe stage 10 was too low or 11 is interpreted differently.
            # Let's try a slightly smoother linear-to-log mapping.
            if new_vol_stage == 11:
                target_vol = 100
            else:
                target_vol = int((new_vol_stage / 11.0) * 90) # Cap stage 10 at 90% to make the jump to 100 smaller
            
            # ONLY update if stage changed to reduce erratic behavior
            if getattr(self, '_last_vol_stage', -1) != new_vol_stage:
                self.radio_mgr.set_volume(target_vol)
                self._last_vol_stage = new_vol_stage
            
            self._last_knob_angle = (new_vol_stage * 30 + 90) % 360
            
            # Immediate visual feedback
            self.update_knob_visual(self._last_knob_angle)
            
            return "break"

        self.main_canvas.tag_bind("vol_knob", "<B1-Motion>", on_knob_drag)
        self.main_canvas.tag_bind("vol_knob", "<Button-1>", on_knob_drag)
        self.main_canvas.tag_bind("vol_knob", "<ButtonRelease-1>", lambda e: setattr(self, 'last_interaction_time', time.time()))
        self.main_canvas.tag_bind("vol_knob_area", "<B1-Motion>", on_knob_drag)
        self.main_canvas.tag_bind("vol_knob_area", "<Button-1>", on_knob_drag)
        self.main_canvas.tag_bind("vol_knob_area", "<ButtonRelease-1>", lambda e: setattr(self, 'last_interaction_time', time.time()))

        # Radio 292, 130
        rax, ray, rafg, rasz = get_pos("RADIO", 233, 51, "#d31a18", 5)
        radio_text = "OFF".center(26)
        # For the radio text which is centered in design, we use center anchor
        # UImaker width=155 in design. At 2x scale, it's 310.
        # User wants to extend 40px either side -> total width 310 + 80 = 390.
        # Centering remains at the same X coordinate relative to rax.
        self.radio_toggle_id = self.main_canvas.create_text(rax + 155, ray + 30, text=radio_text, fill=rafg, 
                                                         font=("Lilita One", 14, "bold"), anchor="center", tags="radio_toggle")
        self.main_canvas.tag_bind(self.radio_toggle_id, "<Button-1>", lambda e: self.toggle_radio())
        self.main_canvas.tag_bind(self.radio_toggle_id, "<Enter>", lambda e: self.main_canvas.config(cursor="hand2"))
        self.main_canvas.tag_bind(self.radio_toggle_id, "<Leave>", lambda e: self.main_canvas.config(cursor=""))
        self.main_canvas.tag_bind(self.radio_toggle_id, "<Button-3>", self.show_radio_context_menu)


        self.version_id = self.main_canvas.create_text(img_w - 18, img_h - 14, text="1.0", fill=TEXT_SECONDARY, font=("Segoe UI", 8), anchor="center")

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
            # Use a slightly longer timeout for the standard check
            if kernel32.WaitNamedPipeW(pipe_path, 200):
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
                        # Use cmd /c tasklist to avoid PowerShell/subprocess interpretation issues on some systems
                        check = subprocess.run(['cmd', '/c', 'tasklist /FI ""PID eq ' + pid_str + '""'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        if pid_str in check.stdout:
                            # If process exists, we wait a bit more for the pipe to appear
                            if kernel32.WaitNamedPipeW(pipe_path, 2000):
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
            if hasattr(self, 'status_id'):
                self.main_canvas.itemconfig(self.status_id, fill="#ffaa00")
            
            # Use discovery logic
            current_pipe = find_active_pipe()
            
            if not current_pipe:
                # Wait longer for the pipe to appear
                # Increase wait time for the initial connection
                if kernel32.WaitNamedPipeW(pipe_path, 2000):
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
            
            if hasattr(self, 'status_id'):
                self.main_canvas.itemconfig(self.status_id, fill="#00ff88")
            
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
        import json
        # First-pass normalization for specific keys
        for key in ["name", "source", "target"]:
            val = event.get(key)
            if val:
                # SPECIAL CASE: Recognize and strip [group] prefix for looters
                if key == "source" and val.lower().startswith("[group] "):
                    val = val[8:].strip()
                    self.known_players.add(normalize_name(val).lower())
                    event[key] = val
                
                v_norm = normalize_name(event.get(key, ""))
                event[key] = v_norm
                
                # TRACK ARRIVAL ORDER
                if v_norm and v_norm != "Unknown":
                    if v_norm not in self.player_arrival_order:
                        self.player_arrival_order.append(v_norm)
                        try:
                            with open("livius_debug.log", "a") as f:
                                f.write(f"[{time.strftime('%H:%M:%S')}] ARRIVAL: {v_norm} (via {key})\n")
                        except: pass
        
        event_type = event.get("type")

        # LIVIUS DEBUG LOGGING
        if event_type in ["chat", "poison", "incapacitated", "status_removed", "cooldown", "death", "kill"]:
             try:
                 with open("livius_debug.log", "a") as f:
                     f.write(f"[{time.strftime('%H:%M:%S')}] EVENT: {json.dumps(event)}\n")
             except: pass

        if event_type == "chat":
            channel = event.get("channel")
            source = event.get("source")
            message = event.get("message", "")
            if channel == "Groupchat" and source:
                source = normalize_name(source)
                msg_clean = message.strip()
                if msg_clean == "123":
                    self.friendly_players.add(source)
                    self.known_players.add(source.lower())
                    # ENSURE IN ARRIVAL ORDER
                    if source not in self.player_arrival_order:
                        self.player_arrival_order.append(source)
                
                    try:
                        with open("livius_debug.log", "a") as f:
                            f.write(f"[{time.strftime('%H:%M:%S')}] FRIEND ADDED: {source} (Chat 123). Order: {self.player_arrival_order}\n")
                    except: pass
                
                    if source in self.enemy_players:
                        self.enemy_players.remove(source)
                    # Force a data init for the friendly player
                    if source not in self.player_data:
                        self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0, "kill_count": 0}
                    else:
                        if "poison_hits" not in self.player_data[source]: self.player_data[source]["poison_hits"] = 0
                        if "incapacitated_count" not in self.player_data[source]: self.player_data[source]["incapacitated_count"] = 0
                        if "kill_count" not in self.player_data[source]: self.player_data[source]["kill_count"] = 0
                    
                    # Force a UI refresh to show the new friend immediately
                    if hasattr(self, 'livius_win') and self.livius_win:
                        self.livius_win.refresh(force=True)
            return

        if event_type == "stats":
            name = event.get("name")
            if not name: return
            
            # Filter out NPCs from persistent data if they aren't probable players
            if not is_probable_player(name, self.bosses, self.known_npcs):
                # We still keep them in locally_seen for a short while, but maybe not in player_data forever
                pass
            
            # p should be keyed by the normalized name
            if name not in self.player_data:
                self.player_data[name] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0, "kill_count": 0}
            
            p = self.player_data[name]
            
            # If they did something, mark them as definitely a player locally (to bypass NPC filters if needed)
            if event.get("damage", 0) > 0 or event.get("healing", 0) > 0 or event.get("taken", 0) > 0:
                self.known_players.add(name.lower())
                # Mark as enemy if not already friendly and is a player (not NPC)
                if name != "You" and name not in self.friendly_players:
                    # Check if it's a known player or passes the probable player test
                    if name.lower() in self.known_players or is_probable_player(name, self.bosses, self.known_npcs, self.known_players):
                        if name not in self.enemy_players:
                            self.enemy_players.add(name)
                            # ENSURE IN ARRIVAL ORDER
                            if name not in self.player_arrival_order:
                                self.player_arrival_order.append(name)
                            try:
                                with open("livius_debug.log", "a") as f:
                                    f.write(f"[{time.strftime('%H:%M:%S')}] ENEMY ADDED: {name} (Combat Action). Order: {self.player_arrival_order}\n")
                            except: pass
                
                # Ensure player data has fields for LIVIUS UI
                if name not in self.player_data:
                    self.player_data[name] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0, "kill_count": 0}
                else:
                    if "poison_hits" not in self.player_data[name]: self.player_data[name]["poison_hits"] = 0
                    if "incapacitated_count" not in self.player_data[name]: self.player_data[name]["incapacitated_count"] = 0
                    if "kill_count" not in self.player_data[name]: self.player_data[name]["kill_count"] = 0

            # Track knockdowns
            if event_type == "stats":
                # stats events don't usually have ability, check dealing/taken events
                pass
            
            # Reset status cooldowns if a player dies or is defeated
            if event.get("died", False) or event.get("defeated", False):
                if name in self.status_cooldowns:
                    del self.status_cooldowns[name]

            # Ensure cumulative session stats only increase
            p["damage"] = max(p.get("damage", 0), event.get("damage", 0))
            p["healing"] = max(p.get("healing", 0), event.get("healing", 0))
            
            # DM stats should only be updated if we are in an active combat encounter
            # and only if the incoming value is higher than what we currently have for this encounter.
            # If the engine sends session totals, we need to subtract the session total at encounter start.
            if self.app_start_time:
                if not hasattr(self, '_encounter_start_stats'): self._encounter_start_stats = {}
                if name not in self._encounter_start_stats:
                    # Capture the base session stats when this player first appears in this encounter
                    # We use event values as the baseline for this encounter
                    self._encounter_start_stats[name] = {"damage": event.get("damage", 0), "healing": event.get("healing", 0)}
                
                # dm_damage is the growth since encounter start
                encounter_damage = event.get("damage", 0) - self._encounter_start_stats[name]["damage"]
                encounter_healing = event.get("healing", 0) - self._encounter_start_stats[name]["healing"]
                p["dm_damage"] = encounter_damage
                p["dm_healing"] = encounter_healing
            else:
                # Outside combat, dm stats stay 0
                p["dm_damage"] = 0
                p["dm_healing"] = 0

            p["dm_taken"] = max(p.get("dm_taken", 0), event.get("taken", 0))
            p["dm_hits"] = max(p.get("dm_hits", 0), event.get("hits", 0))
            p["dm_misses"] = max(p.get("dm_misses", 0), event.get("misses", 0))
            p["dm_avoided"] = max(p.get("dm_avoided", 0), event.get("avoided", 0))
            p["aoe_hits"] = max(p.get("aoe_hits", 0), event.get("aoe", 0))
            
            p["lb_loot"] = max(p.get("lb_loot", 0), event.get("loot", 0))
            p["lb_mobs"] = max(p.get("lb_mobs", 0), event.get("mobs", 0))
            p["lb_xp"] = max(p.get("lb_xp", 0), event.get("xp", 0))

            self.locally_seen_players[name] = time.time()

            # Ensure secondary windows see this data
            self.leaderboard_data[name] = p["damage"]
            
            # Refresh will be handled by centralized timing at the end of process_external_event
            # self.refresh_ui_only(force=True) -> REMOVED

            # Update last_combat_time and app_start_time
            if (p["dm_damage"] > 0 or p["dm_healing"] > 0 or p["dm_taken"] > 0 or 
                p["dm_hits"] > 0 or p["dm_misses"] > 0 or p["dm_avoided"] > 0 or
                p["lb_loot"] > 0 or p["lb_mobs"] > 0 or p["lb_xp"] > 0):
                self.last_combat_time = time.time()
                if self.app_start_time is None:
                    self.app_start_time = datetime.now()
                self.last_log_sync_time = self.app_start_time
            return

        now = datetime.now()
        source = event.get("source", "Unknown")
        damage = event.get("damage", 0)
        healing = event.get("healing", 0)
        item = event.get("item", "")
        timestamp = event.get("timestamp")
        if timestamp is None: timestamp = now
        target = event.get("target", "Unknown")
        ability = event.get("ability", "")
        is_mitigated = event.get("is_mitigated", False)

        # Track statuses (knockdown, posture change, intimidate)
        if ability:
            low_ability = ability.lower()
            status_type = None
            if "knockdown" in low_ability: status_type = "knockdown"
            elif "posture" in low_ability: status_type = "posture"
            elif "intimidate" in low_ability: status_type = "intimidate"
            
            if status_type and target and target != "Unknown":
                cur_time = time.time()
                # DEBUG STATUS
                try:
                    with open("livius_debug.log", "a") as dbf:
                        dbf.write(f"[{time.strftime('%H:%M:%S')}] STATUS DETECTED: {status_type} on {target}\n")
                except: pass
                
                if target not in self.status_cooldowns:
                    self.status_cooldowns[target] = {}
                
                last_time = self.status_cooldowns[target].get(status_type, 0)
                if cur_time - last_time > 30:
                    self.status_cooldowns[target][status_type] = cur_time
                else:
                    try:
                        with open("livius_debug.log", "a") as dbf:
                            dbf.write(f"  (Ignored: {cur_time - last_time:.1f}s since last)\n")
                    except: pass

        # Early status removal (e.g., "no longer intimidated")
        if event_type == "status_removed":
            status_type = event.get("status")
            if target and target != "Unknown" and target in self.status_cooldowns:
                if status_type in self.status_cooldowns[target]:
                    del self.status_cooldowns[target][status_type]

        # Incapacitated tracking
        if event_type == "incapacitated":
            if target not in self.player_data:
                self.player_data[target] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0}
            
            # Ensure field exists
            if "poison_hits" not in self.player_data[target]:
                 self.player_data[target]["poison_hits"] = 0
            if "incapacitated_count" not in self.player_data[target]:
                 self.player_data[target]["incapacitated_count"] = 0

            self.player_data[target]["incapacitated_count"] = self.player_data[target].get("incapacitated_count", 0) + 1
            self.player_data[target]["logs"].append({"msg": "Incapacitated!", "time": timestamp, "type": "incapacitated"})

        # Poison tracking
        if event_type == "poison":
            if source not in self.player_data:
                self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0}
            
            # Ensure field exists
            if "poison_hits" not in self.player_data[source]:
                 self.player_data[source]["poison_hits"] = 0
            if "incapacitated_count" not in self.player_data[source]:
                 self.player_data[source]["incapacitated_count"] = 0

            self.player_data[source]["poison_hits"] = self.player_data[source].get("poison_hits", 0) + 1
            self.player_data[source]["logs"].append({"msg": f"Applied poison to {target}", "time": timestamp, "type": "poison"})
            if len(self.player_data[source]["logs"]) > 200: self.player_data[source]["logs"].pop(0)

        if event_type == "poison_resist":
            # Just log it for now
            if "You" not in self.player_data:
                self.player_data["You"] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0}
            self.player_data["You"]["logs"].append({"msg": f"{target} resisted your poison", "time": timestamp, "type": "poison_resist"})
            if len(self.player_data["You"]["logs"]) > 200: self.player_data["You"]["logs"].pop(0)

        # Death/Defeated trigger
        if event_type in ["death", "kill"]:
            if target and target != "Unknown":
                if target in self.status_cooldowns:
                    del self.status_cooldowns[target]
                if target not in self.player_data:
                    self.player_data[target] = {"damage": 0, "healing": 0, "logs": [], "died": True, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0, "kill_count": 0}
                else:
                    self.player_data[target]["died"] = True
                    # Ensure fields exist for the UI even if player already existed
                    if "poison_hits" not in self.player_data[target]:
                        self.player_data[target]["poison_hits"] = 0
                    if "incapacitated_count" not in self.player_data[target]:
                        self.player_data[target]["incapacitated_count"] = 0
                    if "kill_count" not in self.player_data[target]:
                        self.player_data[target]["kill_count"] = 0
            
            # Increment kill count for the source if it was a kill event
            # FILTER: Only count it if the target is a probable player (PvP Kill)
            if event_type == "kill" and source and source != "Unknown":
                is_pvp = False
                if target and target != "Unknown":
                    # Check if target is a known player or passes player test
                    if target.lower() in self.known_players or is_probable_player(target, self.bosses, self.known_npcs, self.known_players):
                        is_pvp = True
                
                if is_pvp:
                    if source not in self.player_data:
                        self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0, "kill_count": 0}
                    
                    self.player_data[source]["kill_count"] = self.player_data[source].get("kill_count", 0) + 1
                    try:
                        with open("livius_debug.log", "a") as f:
                            f.write(f"[{time.strftime('%H:%M:%S')}] PVP KILL TRACKED: {source} killed {target}. Total: {self.player_data[source]['kill_count']}\n")
                    except: pass

        # Handle rolling damage for Top DPS and Top Tank
        if event_type in ["taken", "healing"]:
            attacker_name = source
            victim_name = target
            val = damage if event_type == "taken" else healing
            
            # Attacker's damage history
            if attacker_name and attacker_name != "Unknown" and val > 0:
                if event_type == "taken":
                    if attacker_name not in self.damage_history:
                        self.damage_history[attacker_name] = []
                    self.damage_history[attacker_name].append((time.time(), val))
                elif event_type == "healing":
                    if attacker_name not in self.healing_history:
                        self.healing_history[attacker_name] = []
                    self.healing_history[attacker_name].append((time.time(), val))
            
            # Victim's damage taken history
            if event_type == "taken" and victim_name and victim_name != "Unknown" and val > 0:
                if victim_name not in self.damage_taken_history:
                    self.damage_taken_history[victim_name] = []
                self.damage_taken_history[victim_name].append((time.time(), val))

        # Re-assign p for correct log attribution
        # If it's a 'taken' event, the victim is 'target'
        if event_type == "taken":
            source_for_logs = target
            attacker = source
        else:
            source_for_logs = source
            attacker = source_for_logs
        
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
            if source_for_logs not in self.player_data:
                self.player_data[source_for_logs] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0}
            
            p = self.player_data[source_for_logs]
            amount = event.get("amount", 0)
            xp_type = event.get("xp_type", "Unknown")
            p["lb_xp"] = p.get("lb_xp", 0) + amount
            
            # Killstreak trigger: PvP XP (Faction)
            if xp_type.lower() == "faction" and source_for_logs.lower() == self.char_name.get().lower():
                if self.killstreak_mgr:
                    self.killstreak_mgr.record_kill()

            if "xp_history" not in p: p["xp_history"] = []
            p["xp_history"].append({"amount": amount, "type": event.get("xp_type", "Unknown"), "time": time.time()})
            if len(p["xp_history"]) > 100: p["xp_history"].pop(0)

            # Add to logs
            p["logs"].append({"msg": f"Received {amount:,.0f} {event.get('xp_type', 'Unknown')} XP", "time": timestamp, "type": "xp"})
            if len(p["logs"]) > 200: p["logs"].pop(0)

            self.locally_seen_players[source_for_logs] = time.time()
            self.leaderboard_data[source_for_logs] = p.get("damage", 0)
            
            # SESSION START HANDLED IN LATER BLOCK
            # self.refresh_ui_only(force=True) -> REMOVED
            # FALL THROUGH to session/combat timing logic at the end of function
        
        elif (event_type == "mobs"):
            if source_for_logs not in self.player_data:
                self.player_data[source_for_logs] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 0, "incapacitated_count": 0}
            
            p = self.player_data[source_for_logs]
            p["lb_mobs"] = p.get("lb_mobs", 0) + 1
            
            self.locally_seen_players[source_for_logs] = time.time()
            self.leaderboard_data[source_for_logs] = p.get("damage", 0)
            
            # Add to logs
            norm_target = normalize_name(target)
            p["logs"].append({"msg": f"Defeated {norm_target}", "time": timestamp, "type": "kill"})
            if len(p["logs"]) > 200: p["logs"].pop(0)
            
            # Killstreak trigger: PvP Kill
            if source_for_logs.lower() == self.char_name.get().lower() and is_probable_player(target, self.bosses, self.known_npcs):
                if self.killstreak_mgr:
                    self.killstreak_mgr.record_kill()
            
            # If our character dies
            if target.lower() == self.char_name.get().lower():
                if self.killstreak_mgr:
                    self.killstreak_mgr.record_death()
            
            # self.refresh_ui_only(force=True) -> REMOVED
            # FALL THROUGH
            
        elif (event_type == "loot"):
            if source_for_logs not in self.player_data:
                self.player_data[source_for_logs] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0}
            
            p = self.player_data[source_for_logs]
            p["lb_loot"] = p.get("lb_loot", 0) + 1
            
            self.leaderboard_data[source_for_logs] = p.get("damage", 0)
            
            # New loot fields
            if "total_credits" not in p: p["total_credits"] = 0
            if "looted_items" not in p: p["looted_items"] = []
            
            credits = event.get("credits", 0)
            item = event.get("item", "Unknown")
            
            if credits > 0:
                p["total_credits"] += credits
                p["logs"].append({"msg": f"Looted {credits:,.0f}cr", "time": timestamp, "type": "loot"})
            elif item and item != "Unknown":
                p["looted_items"].append(item)
                p["logs"].append({"msg": f"Looted {item}", "time": timestamp, "type": "loot"})
                if len(p["looted_items"]) > 10000: # Limit history
                    p["looted_items"].pop(0)
                
                # Permanent drops tracking
                if target and target != "Unknown":
                    norm_item = item.strip()
                    norm_target = normalize_name(target)
                    if norm_item not in self.permanent_drops:
                        self.permanent_drops[norm_item] = []
                    if norm_target not in self.permanent_drops[norm_item]:
                        self.permanent_drops[norm_item].append(norm_target)
            
            if source_for_logs not in self.loot_data: self.loot_data[source_for_logs] = []
            self.loot_data[source_for_logs].append({"item": item, "credits": credits, "target": target, "timestamp": timestamp})
            if len(self.loot_data[source_for_logs]) > 10000: self.loot_data[source_for_logs].pop(0)

            # HEURISTIC: If a name has been looted from, it is not a player
            if target and target != "Unknown":
                self.known_npcs.add(target.lower())

            self.locally_seen_players[source_for_logs] = time.time()
            # self.refresh_ui_only(force=True) -> REMOVED
            # FALL THROUGH
        
        else:
            # ORIGINAL DIRECT DAMAGE/HEALING/TAKEN LOGIC
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

            self.all_events.append(internal_event)
            if len(self.all_events) > 5000: self.all_events = self.all_events[-5000:]

            # Update per-player breakdown and logs
            if source_for_logs not in self.player_data:
                self.player_data[source_for_logs] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0}
            
            p = self.player_data[source_for_logs]
            self.locally_seen_players[source_for_logs] = time.time()
            
            # If they did something, mark them as definitely a player locally
            if damage > 0 or healing > 0 or event_type == "taken":
                self.known_players.add(source_for_logs.lower())

            log_msg = ""
            log_type = "all"
            if event_type == "dealt" or event_type == "other_dealt":
                p["damage"] = p.get("damage", 0) + damage
                if self.app_start_time:
                    p["dm_damage"] = p.get("dm_damage", 0) + damage
                else:
                    p["dm_damage"] = 0
                if target not in p["targets"]: p["targets"][target] = 0
                p["targets"][target] += damage
                # Simplified format: "damage ability target"
                norm_target = normalize_name(target)
                log_msg = f"{damage:,.0f} {ability} {norm_target}"
                log_type = "dealt"
                
                if p["damage"] < p["dm_damage"]: p["damage"] = p["dm_damage"]
                self.leaderboard_data[source] = p["damage"]

                if is_probable_player(target, self.bosses, self.known_npcs):
                    if target not in self.player_data:
                        self.player_data[target] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0}
                    tp = self.player_data[target]
                    if self.app_start_time:
                        tp["dm_taken"] = tp.get("dm_taken", 0) + damage
                    else:
                        tp["dm_taken"] = 0
                    # Already simplified format for taken
                    norm_source = normalize_name(source)
                    tp["logs"].append({"msg": f"{damage:,.0f} {norm_source}", "time": timestamp, "type": "taken"})
                    if len(tp["logs"]) > 200: tp["logs"].pop(0)
                    
                    if hasattr(self, 'details_win') and getattr(self.details_win, 'is_drilldown', False) and getattr(self.details_win, 'selected_player', None) == target:
                        # Throttle will handle this
                        pass
            elif event_type == "taken":
                if self.app_start_time:
                    p["dm_taken"] = p.get("dm_taken", 0) + damage
                else:
                    p["dm_taken"] = 0
                norm_attacker = normalize_name(attacker)
                log_msg = f"{damage:,.0f} {norm_attacker}"
                log_type = "taken"
            elif event_type == "healing":
                p["healing"] = p.get("healing", 0) + healing
                if self.app_start_time:
                    p["dm_healing"] = p.get("dm_healing", 0) + healing
                else:
                    p["dm_healing"] = 0
                if target not in p["targets"]: p["targets"][target] = 0
                p["targets"][target] += healing
                norm_target = normalize_name(target)
                log_msg = f"{healing:,.0f} {ability} {norm_target}"
                log_type = "healing"
                
                if p["healing"] < p["dm_healing"]: p["healing"] = p["dm_healing"]
            
            if log_msg:
                p["logs"].append({"msg": log_msg, "time": timestamp, "type": log_type})
                if len(p["logs"]) > 200: p["logs"].pop(0)
                
                if hasattr(self, 'leaderboard_win') and getattr(self.leaderboard_win, 'is_drilldown', False) and getattr(self.leaderboard_win, 'selected_player', None) == source_for_logs:
                    self.leaderboard_win.last_full_refresh = 0
                if hasattr(self, 'details_win') and getattr(self.details_win, 'is_drilldown', False) and getattr(self.details_win, 'selected_player', None) == source_for_logs:
                    self.details_win.last_full_refresh = 0
                if hasattr(self, 'skimmers_win') and getattr(self.skimmers_win, 'is_drilldown', False) and getattr(self.skimmers_win, 'selected_player', None) == source_for_logs:
                    self.skimmers_win.last_full_refresh = 0

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

        # --- CENTRALIZED SESSION & COMBAT TIMING ---
        now_f = time.time()
        is_damage = (damage > 0 and event_type in ["dealt", "taken", "other_dealt"])
        is_healing = (healing > 0 and event_type == "healing")
        is_activity = is_damage or is_healing or event_type in ["mobs", "xp", "loot"]

        # 1. COMBAT TIMEOUT & SESSION RESET
        if self.app_start_time and (now_f - self.last_combat_time > self.time_window_dm):
            self.last_log_sync_time = None 
            self.app_start_time = None
            if hasattr(self, '_encounter_start_stats'): self._encounter_start_stats = {}
            for p_name in list(self.player_data.keys()):
                self.player_data[p_name]["dm_damage"] = 0
                self.player_data[p_name]["dm_healing"] = 0
                self.player_data[p_name]["dm_taken"] = 0
                self.player_data[p_name]["dm_hits"] = 0
                self.player_data[p_name]["dm_misses"] = 0
                self.player_data[p_name]["dm_avoided"] = 0
            self.last_ui_update_time = 0 # Force immediate update on timeout
            is_last = True # Force UI refresh on reset
            
        # 2. RE-ENABLE COMBAT START
        if is_activity:
            if self.app_start_time is None:
                self.app_start_time = timestamp
                # Reset DM baselines for all players when new encounter starts
                if not hasattr(self, '_encounter_start_stats'):
                    self._encounter_start_stats = {}
                else:
                    self._encounter_start_stats.clear()
                
                for p_name in self.player_data:
                    self.player_data[p_name]["dm_damage"] = 0
                    self.player_data[p_name]["dm_healing"] = 0
                    self.player_data[p_name]["dm_taken"] = 0
                    self.player_data[p_name]["dm_hits"] = 0
                    self.player_data[p_name]["dm_misses"] = 0
                    self.player_data[p_name]["dm_avoided"] = 0
            
            self.last_combat_time = now_f
            self.last_log_sync_time = timestamp
            
            # If we just started combat, we might need to apply this event to dm_damage immediately
            # because the activity block is AFTER the damage update.
            p = self.player_data.get(source_for_logs)
            if p and p["dm_damage"] == 0 and damage > 0 and (event_type == "dealt" or event_type == "other_dealt"):
                p["dm_damage"] = damage
            if p and p["dm_healing"] == 0 and healing > 0 and event_type == "healing":
                p["dm_healing"] = healing
            if p and p["dm_taken"] == 0 and damage > 0 and event_type == "taken":
                p["dm_taken"] = damage

        # 3. HISTORY LIMIT (General)
        history_limit = datetime.now() - timedelta(hours=1)
        self.all_events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= history_limit]

        # 4. UI UPDATE THROTTLE
        if is_last or (now_f - self.last_ui_update_time > 0.3):
            if self.running:
                try:
                    # Use a more robust check for pending updates to avoid flooding the UI thread
                    if not getattr(self, '_ui_update_pending', False) or is_last:
                        self._ui_update_pending = True
                        def do_update(f=is_last):
                            self._ui_update_pending = False
                            self.refresh_ui_only(force=f)
                        self.root.after(0, do_update)
                        self.last_ui_update_time = now_f
                except: pass

    def update_knob_visual(self, angle_deg):
        import math
        self._last_knob_angle = angle_deg
        rad = math.radians(angle_deg)
        ex = self.knob_cx + self.knob_len * math.cos(rad)
        ey = self.knob_cy + self.knob_len * math.sin(rad)
        if hasattr(self, 'vol_knob_id'):
            self.main_canvas.coords(self.vol_knob_id, self.knob_cx, self.knob_cy, ex, ey)

    def update_clock(self):
        try:
            # Format: 3:16PM
            now = datetime.now().strftime("%I:%M%p").lstrip("0")
            if hasattr(self, 'clock_id'):
                if self.main_canvas.itemcget(self.clock_id, "text") != now:
                    self.main_canvas.itemconfig(self.clock_id, text=now)
            self.root.after(10000, self.update_clock) # Update every 10 seconds is enough for this format
        except: pass

    def _update_top_stats(self):
        """Calculates rolling 10s damage/tanking/healing and updates top status/focus for each team."""
        now = time.time()
        if now - self.last_top_stats_check < 0.5:
            return
            
        elapsed = now - self.last_top_stats_check
        self.last_top_stats_check = now
        
        # 1. Update Top DPS
        rolling_dps = {}
        for player, history in list(self.damage_history.items()):
            self.damage_history[player] = [(ts, dmg) for ts, dmg in history if now - ts <= 10]
            total = sum(dmg for ts, dmg in self.damage_history[player])
            if total > 0:
                rolling_dps[player] = total
        
        # 2. Update Top Tank (Damage Taken)
        rolling_tank = {}
        for player, history in list(self.damage_taken_history.items()):
            self.damage_taken_history[player] = [(ts, dmg) for ts, dmg in history if now - ts <= 10]
            total = sum(dmg for ts, dmg in self.damage_taken_history[player])
            if total > 0:
                rolling_tank[player] = total
                
        # 3. Update Top Healing
        rolling_healing = {}
        for player, history in list(self.healing_history.items()):
            self.healing_history[player] = [(ts, heal) for ts, heal in history if now - ts <= 10]
            total = sum(heal for ts, heal in self.healing_history[player])
            if total > 0:
                rolling_healing[player] = total
        
        new_tops = {'friendly': None, 'enemy': None}
        new_tanks = {'friendly': None, 'enemy': None}
        new_heals = {'friendly': None, 'enemy': None}
        new_focus = {'friendly': None, 'enemy': None}
        
        # Find Friendly Top DPS / Tank / Healer / Focus
        f_players = [p for p in rolling_dps if p in self.friendly_players or p == "You"]
        if f_players:
            new_tops['friendly'] = max(f_players, key=lambda p: rolling_dps[p])
        
        f_tank_players = [p for p in rolling_tank if p in self.friendly_players or p == "You"]
        if f_tank_players:
            # Most damage taken is the Top Tank, but also the Focus Target
            new_tanks['friendly'] = max(f_tank_players, key=lambda p: rolling_tank[p])
            new_focus['friendly'] = new_tanks['friendly']
            
        f_heal_players = [p for p in rolling_healing if p in self.friendly_players or p == "You"]
        if f_heal_players:
            new_heals['friendly'] = max(f_heal_players, key=lambda p: rolling_healing[p])
            
        # Find Enemy Top DPS / Tank / Healer / Focus
        e_dps_players = [p for p in rolling_dps if p in self.enemy_players]
        if e_dps_players:
            new_tops['enemy'] = max(e_dps_players, key=lambda p: rolling_dps[p])

        e_tank_players = [p for p in rolling_tank if p in self.enemy_players]
        if e_tank_players:
            new_tanks['enemy'] = max(e_tank_players, key=lambda p: rolling_tank[p])
            new_focus['enemy'] = new_tanks['enemy']
            
        e_heal_players = [p for p in rolling_healing if p in self.enemy_players]
        if e_heal_players:
            new_heals['enemy'] = max(e_heal_players, key=lambda p: rolling_healing[p])
            
        # Update Top DPS durations
        for team in ['friendly', 'enemy']:
            top_p = new_tops[team]
            old_top_p = self.current_top_dps[team]
            if top_p and top_p == old_top_p:
                self.top_dps_durations[top_p] = self.top_dps_durations.get(top_p, 0) + elapsed
            self.current_top_dps[team] = top_p
            
        # Update Top Tank durations
        for team in ['friendly', 'enemy']:
            tank_p = new_tanks[team]
            old_tank_p = self.current_top_tank[team]
            if tank_p and tank_p == old_tank_p:
                self.top_tank_durations[tank_p] = self.top_tank_durations.get(tank_p, 0) + elapsed
            self.current_top_tank[team] = tank_p
            
        # Update Top Healing durations
        for team in ['friendly', 'enemy']:
            heal_p = new_heals[team]
            old_heal_p = self.current_top_healing[team]
            if heal_p and heal_p == old_heal_p:
                self.top_healing_durations[heal_p] = self.top_healing_durations.get(heal_p, 0) + elapsed
            self.current_top_healing[team] = heal_p
            
        # Update Focus Target
        for team in ['friendly', 'enemy']:
            self.current_focus_target[team] = new_focus[team]

    def start_ticker_loop(self):
        if self.running:
            self._update_top_stats()
            self.refresh_ui_only(force=False)
            self.root.after(500, self.start_ticker_loop) # Restore 500ms ticker for smoother marquee

    def refresh_ui_only(self, force=False):
        if force:
            # Instead of full build_layout which causes flashing,
            # we just reload positions and update items if they exist.
            self._load_dynamic_labels()
            # If the canvas doesn't exist, we must build it.
            if not hasattr(self, 'main_canvas') or not self.main_canvas.winfo_exists():
                self.build_layout()
                return
            
            # Optimization: Try to just move existing items instead of destroying canvas
            # This significantly reduces flashing.
            img_w, img_h = self.root.winfo_width(), self.root.winfo_height()
            
            # Reposition labels based on new mapping
            def update_pos(name, item_attr):
                if hasattr(self, item_attr):
                    item = getattr(self, item_attr)
                    data = self.dynamic_labels.get(name.upper())
                    if data:
                        self.main_canvas.coords(item, data['x'], data['y'])
                        if 'fg' in data: self.main_canvas.itemconfig(item, fill=data['fg'])

            # List of standard labels to update
            label_map = {
                "SETUP": "lbl_setup", "ALEXA": "lbl_alexa", "DMG METER": "lbl_dmm",
                "DETAILS": "lbl_det", "SKIMMERS": "lbl_skm", "CLOCK": "lbl_clock_header",
                "AUX": "lbl_aux", "PLAY": "lbl_play", "PAUSE": "lbl_pause", 
                "STOP": "lbl_stop", "SKIP": "lbl_skip",
                "DAMAGE": "lbl_damage_header", "XP": "lbl_xp", "XP/H": "lbl_xph",
                "GHARV": "lbl_gharv", "LIVIUS": "lbl_livius", "RESET": "lbl_reset",
                "EXIT": "btn_exit", "ITEM LINK": "lbl_itemlink"
            }
            for name, attr in label_map.items():
                update_pos(name, attr)

            if hasattr(self, 'lbl_bassboost'):
                bbx, bby, bbfg, bbsz = self.build_layout_get_pos("BASS BOOST", 25, 129, "#d21a17", 5)
                self.main_canvas.coords(self.lbl_bassboost, bbx, bby)
            
            # Special cases
            if hasattr(self, 'clock_id'):
                clx, cly, _, _ = self.build_layout_get_pos("CLOCK", 471, 9)
                self.main_canvas.coords(self.clock_id, clx, cly + 14)
            
            if hasattr(self, 'lbl_damage'):
                dmx, dmy, _, _ = self.build_layout_get_pos("DAMAGE", 80, 23)
                self.main_canvas.coords(self.lbl_damage, dmx + 60, dmy)
            
            if hasattr(self, 'lbl_xp_val'):
                xpx, xpy, _, _ = self.build_layout_get_pos("XP", 200, 23)
                self.main_canvas.coords(self.lbl_xp_val, xpx + 40, xpy)
            
            if hasattr(self, 'lbl_xph_val'):
                xphx, xphy, _, _ = self.build_layout_get_pos("XP/H", 380, 23)
                self.main_canvas.coords(self.lbl_xph_val, xphx + 50, xphy)

            # Background image
            if hasattr(self, 'bg_photo') and self.bg_photo:
                bg_items = self.main_canvas.find_withtag("bg_image")
                if bg_items:
                    self.main_canvas.coords(bg_items[0], 0, 0)
                    self.main_canvas.itemconfig(bg_items[0], image=self.bg_photo)
                
            # Volume knob
            vx, vy, vfg, vsz = self.build_layout_get_pos("VOL_DOT", 51, 74, "#ffffff", 5)
            self.knob_cx = vx + 10
            self.knob_cy = vy + 5
            if hasattr(self, 'knob_area_id'):
                self.main_canvas.coords(self.knob_area_id, self.knob_cx - 40, self.knob_cy - 40, self.knob_cx + 40, self.knob_cy + 40)
            
            # Reposition the volume line start/end if it's being forced
            if hasattr(self, 'vol_knob_id'):
                self.update_knob_visual(getattr(self, '_last_knob_angle', 90))
            
            # Radio
            rax, ray, rafg, rasz = self.build_layout_get_pos("RADIO", 233, 51, "#d31a18", 5)
            if hasattr(self, 'radio_toggle_id'):
                self.main_canvas.coords(self.radio_toggle_id, rax + 155, ray + 30)
            
            return
        
        # Update Combat Stats
        try:
            you = self.player_data.get("You", {})
            dmg = you.get("damage", 0)
            xp = sum(item.get("amount", 0) for item in you.get("xp_history", []))
            
            # Calculate XP/H
            xph = 0
            if "xp_history" in you and you["xp_history"]:
                first_ts = you["xp_history"][0].get("time", time.time())
                elapsed_hours = (time.time() - first_ts) / 3600.0
                if elapsed_hours > 0:
                    xph = int(xp / elapsed_hours)

            def format_val(val):
                if val >= 1000000:
                    return f"{val/1000000:.1f}mil"
                elif val >= 1000:
                    return f"{val/1000:.1f}k"
                return str(val)

            new_dmg_text = format_val(dmg)
            new_xp_text = format_val(xp)
            new_xph_text = format_val(xph)

            if hasattr(self, 'lbl_damage'):
                if self.main_canvas.itemcget(self.lbl_damage, "text") != new_dmg_text:
                    self.main_canvas.itemconfig(self.lbl_damage, text=new_dmg_text)
            if hasattr(self, 'lbl_xp_val'):
                if self.main_canvas.itemcget(self.lbl_xp_val, "text") != new_xp_text:
                    self.main_canvas.itemconfig(self.lbl_xp_val, text=new_xp_text)
            if hasattr(self, 'lbl_xph_val'):
                if self.main_canvas.itemcget(self.lbl_xph_val, "text") != new_xph_text:
                    self.main_canvas.itemconfig(self.lbl_xph_val, text=new_xph_text)

            # Update Volume Knob visual
            if hasattr(self, 'radio_mgr') and self.radio_mgr:
                # If user is currently dragging the knob, don't override the position from manager
                # to prevent "snapping" due to integer volume rounding or network delay
                now_t = time.time()
                is_interacting = (now_t - getattr(self, 'last_interaction_time', 0) < 3.0)
                if not is_interacting:
                    # Map volume 0-100 back to 0-11 stages, then to 0-330 degrees relative to 90
                    # Use float for more precision during mapping back
                    vol_stage = int((self.radio_mgr.volume / 100.0) * 11)
                    angle = (vol_stage * 30.0) + 90
                    self.update_knob_visual(angle)
                    self._last_knob_angle = angle
                    self._last_vol_stage = vol_stage
                    self._last_adj_angle = vol_stage * 30.0
        except: pass

        # Update radio scrolling text if playing
        try:
            now_ts = time.time()
            is_adjusting_vol = (now_ts - getattr(self, 'last_interaction_time', 0) < 1.5)
                
            if is_adjusting_vol:
                # Show LED volume bar: VOL [|||||     ] 11
                # Use the latest interaction volume stage, but ensure it's not None
                vol_stage = getattr(self, '_last_vol_stage', None)
                if vol_stage is None and hasattr(self, 'radio_mgr'):
                    vol_stage = int((self.radio_mgr.volume / 100.0) * 11)
                
                vol_stage = vol_stage if vol_stage is not None else 0
                bar = "|" * vol_stage + " " * (11 - vol_stage)
                vol_display = f"VOL [{bar}] {vol_stage:02d}"
                
                # Check current display to avoid redundant updates
                current_text = self.main_canvas.itemcget(self.radio_toggle_id, "text")
                expected_text = vol_display.center(26)
                if current_text != expected_text:
                    self.main_canvas.itemconfig(self.radio_toggle_id, text=expected_text, fill="#00FF00")
            elif hasattr(self, 'radio_mgr') and self.radio_mgr and self.radio_mgr.is_playing:
                if not hasattr(self, '_radio_scroll_pos'): self._radio_scroll_pos = 0
                if not hasattr(self, '_radio_scroll_last_tick'): self._radio_scroll_last_tick = 0
                if not hasattr(self, '_radio_station_cycle_start'): self._radio_station_cycle_start = now_ts
                
                # Scroll every 0.3 seconds for smooth LED look
                if now_ts - self._radio_scroll_last_tick > 0.3:
                    self._radio_scroll_last_tick = now_ts
                    
                    # Cycle: 20 seconds song info, 5 seconds station name
                    cycle_time = (now_ts - self._radio_station_cycle_start) % 25
                    show_station = cycle_time >= 20
                    
                    if hasattr(self.radio_mgr, 'is_interrupting') and self.radio_mgr.is_interrupting:
                        text = "INTERRUPT: " + (os.path.splitext(self.radio_mgr.last_played_mp3)[0].upper() if self.radio_mgr.last_played_mp3 else "UNKNOWN")
                    elif self.radio_mgr.current_station in ["LOCAL AUX", "LOCAL PLAYLIST"]:
                        if getattr(self.radio_mgr, 'current_song_name', None):
                            text = self.radio_mgr.current_song_name.upper()
                        else:
                            text = self.radio_mgr.current_station.upper()
                    elif show_station:
                        text = self.radio_mgr.current_station.upper() if self.radio_mgr.current_station else "RNS 420AM"
                    elif getattr(self.radio_mgr, 'current_song_name', None):
                        text = self.radio_mgr.current_song_name.upper()
                    else:
                        text = self.radio_mgr.current_station.upper() if self.radio_mgr.current_station else "PLAYING"
                    
                    # If text changed, reset scroll pos
                    last_text = getattr(self, '_last_radio_text', "")
                    if text != last_text:
                        self._radio_scroll_pos = 0
                        self._last_radio_text = text
                    
                    # Add padding for scroll loop
                    display_text = text + "   ***   "
                    visible_len = 26 # LED display width in characters (increased by ~6 for 80px extra width)
                    
                    if len(text) > visible_len:
                        self._radio_scroll_pos = (self._radio_scroll_pos + 1) % len(display_text)
                        start = self._radio_scroll_pos
                        marquee = (display_text * 2)[start:start+visible_len]
                        
                        if getattr(self.radio_mgr, 'is_interrupting', False):
                            fg = "#ffcc00"
                        elif self.radio_mgr.current_station == "X MINUS ONE":
                            fg = "#FFFFFF"
                        else:
                            fg = "#CD853F"
                        self.main_canvas.itemconfig(self.radio_toggle_id, text=marquee, fill=fg)
                    else:
                        # No scroll needed
                        self._radio_scroll_pos = 0
                        if getattr(self.radio_mgr, 'is_interrupting', False):
                            fg = "#ffcc00"
                        elif self.radio_mgr.current_station == "X MINUS ONE":
                            fg = "#FFFFFF"
                        else:
                            fg = "#CD853F"
                        self.main_canvas.itemconfig(self.radio_toggle_id, text=text.center(visible_len), fill=fg)
            else:
                if hasattr(self, 'radio_toggle_id'):
                    self.main_canvas.itemconfig(self.radio_toggle_id, text="OFF".center(26), fill="#ff4444")
        except: pass

        try:
            # Damage meter is highest priority for real-time feel
            if hasattr(self, 'damage_meter_win') and self.damage_meter_win:
                self.damage_meter_win.refresh(force=force)

            # Heavy windows (Details, Leaderboard, Skimmers)
            # We refresh them at most once per second, UNLESS they are in drill-down mode,
            # in which case we want faster updates for the active log.
            now_heavy = now_ts - getattr(self, 'last_heavy_refresh', 0)
            if now_heavy >= 1.0 or force:
                refresh_details = True
                refresh_lb = True
                refresh_skimmers = True
                self.last_heavy_refresh = now_ts
            else:
                # Check if we should override for active drill-down
                refresh_details = hasattr(self, 'details_win') and self.details_win and getattr(self.details_win, 'is_drilldown', False)
                refresh_lb = hasattr(self, 'leaderboard_win') and self.leaderboard_win and getattr(self.leaderboard_win, 'is_drilldown', False)
                refresh_skimmers = False # Skimmers doesn't have drill-down

            if refresh_details and hasattr(self, 'details_win') and self.details_win:
                self.details_win.refresh(force=force)
            if refresh_lb and hasattr(self, 'leaderboard_win') and self.leaderboard_win:
                self.leaderboard_win.refresh(force=force)
            if refresh_skimmers and hasattr(self, 'skimmers_win') and self.skimmers_win:
                self.skimmers_win.refresh(force=force)
            if hasattr(self, 'livius_win') and self.livius_win:
                self.livius_win.refresh(force=force)

            if hasattr(self, 'armor_win') and self.armor_win:
                self.armor_win.refresh(force=force)

            if hasattr(self, 'hitmiss_win') and self.hitmiss_win:
                self.hitmiss_win.refresh(force=force)

            # Other windows (less frequent)
            if now_heavy >= 1.0:
                if hasattr(self, 'alexa_win') and self.alexa_win: self.alexa_win.refresh(force=False)
                if hasattr(self, 'options_win') and self.options_win: self.options_win.refresh(force=False)
                if hasattr(self, 'calc_win') and self.calc_win: self.calc_win.refresh(force=False)
        except: pass

    def process_events_for_ui(self, all_events, manual=False):
        pass

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        text = "ONTOP: ON" if self.always_on_top else "ONTOP: OFF"
        fg = ACCENT_BLUE if self.always_on_top else TEXT_SECONDARY
        self.main_canvas.itemconfig(self.btn_ontop, text=text, fill=fg)
        self.root.attributes("-topmost", self.always_on_top)

    def cycle_volume(self):
        # Cycles volume: 100 -> 75 -> 50 -> 25 -> 0 -> 100
        if not self.radio_mgr:
            return
        current_vol = self.radio_mgr.volume
        if current_vol > 75: new_vol = 75
        elif current_vol > 50: new_vol = 50
        elif current_vol > 25: new_vol = 25
        elif current_vol > 0: new_vol = 0
        else: new_vol = 100
        
        self.radio_mgr.set_volume(new_vol)
        self._last_vol_stage = int((new_vol / 100.0) * 11)
        self._last_adj_angle = self._last_vol_stage * 30.0
        self.last_interaction_time = time.time()
        
        if hasattr(self, 'lbl_vol'):
            self.main_canvas.itemconfig(self.lbl_vol, text=f"VOL: {new_vol}%")

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
                    
                    # Also include logs in payload for sync if needed (though current server might not use it)
                    local_logs = {p: d.get("logs", []) for p, d in self.player_data.items() if d.get("logs")}

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
                pass
            
            # Wait 30 seconds between syncs
            for _ in range(600): # Sync every 60 seconds
                if not self.running: break
                time.sleep(0.1)

    def setup_tray_icon(self):
        try:
            with open("crash_log.txt", "a") as f:
                f.write(f"--- ENTERING SETUP_TRAY_ICON {datetime.now()} ---\n")

            icon_path = get_resource_path("iconbell.jpg")
            png_path = get_resource_path("livylogs.png")
            ico_path = get_resource_path("livylogs.ico")
            
            with open("crash_log.txt", "a") as f:
                f.write(f"--- PATHS: icon={icon_path}, png={png_path}, ico={ico_path} ---\n")

            # Always try to create a fresh image to be safe
            try:
                if os.path.exists(icon_path):
                    image = Image.open(icon_path)
                    image.load()
                elif os.path.exists(png_path):
                    image = Image.open(png_path)
                    image.load() # Force load
                elif os.path.exists(ico_path):
                    image = Image.open(ico_path)
                    image.load()
                else:
                    image = Image.new('RGBA', (64, 64), color=(0, 160, 255, 255))
            except Exception as img_err:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- IMAGE LOAD ERROR {datetime.now()} ---\n{img_err}\n")
                image = Image.new('RGBA', (64, 64), color=(0, 160, 255, 255))
            
            import webbrowser
            import pystray
            
            # Explicitly force-reload pystray or ensure it's fresh
            # Some environments have issues with pystray initialization in threads
            
            with open("crash_log.txt", "a") as f:
                f.write(f"--- CREATING MENU {datetime.now()} ---\n")

            menu = (
                item('Show/Hide', self.toggle_visibility, default=True),
                item('About', lambda: webbrowser.open("https://github.com/livy2k/livylogs#readme")),
                pystray.Menu.SEPARATOR,
                item('Exit', self.on_exit)
            )
            
            with open("crash_log.txt", "a") as f:
                f.write(f"--- INITIALIZING ICON {datetime.now()} ---\n")

            # Simplify icon creation
            self.tray_icon = pystray.Icon(
                "LivyLogs",
                image,
                "LivyLogs",
                menu=menu
            )
            
            # Explicitly set visible before run
            self.tray_icon.visible = True
            
            # Forcing a small delay
            time.sleep(0.2)
            
            # Double click tray icon to show/hide
            self.tray_icon.on_activate = lambda icon: self.root.after(0, self.toggle_visibility)
            
            def run_tray():
                try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- TRAY RUN START {datetime.now()} ---\n")
                    self.tray_icon.run()
                except Exception as e:
                    try:
                        import traceback
                        with open("crash_log.txt", "a") as f:
                            f.write(f"--- TRAY RUN ERROR {datetime.now()} ---\n{traceback.format_exc()}\n")
                    except: pass
                finally:
                    try:
                        with open("crash_log.txt", "a") as f:
                            f.write(f"--- TRAY STOPPED {datetime.now()} ---\n")
                    except: pass

            self.tray_icon.visible = True
            # Double click tray icon to show/hide
            self.tray_icon.on_activate = lambda icon: self.root.after(0, self.toggle_visibility)
            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
            
            with open("crash_log.txt", "a") as f:
                f.write(f"--- TRAY THREAD STARTED {datetime.now()} ---\n")
        except Exception as e:
            try:
                import traceback
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- TRAY SETUP ERROR {datetime.now()} ---\n{traceback.format_exc()}\n")
            except: pass
            
    def on_exit(self, icon=None, item=None):
        try:
            # Save all window positions
            for win_attr in ['skimmers_win', 'damage_meter_win', 'leaderboard_win', 
                            'details_win', 'options_win', 'alexa_win', 'eq_win', 'livius_win']:
                win = getattr(self, win_attr, None)
                if win: win.save_config()
        except: pass
        if hasattr(self, '_exiting') and self._exiting:
            return
        self._exiting = True
        
        # Immediate UI hiding to make it feel responsive
        try:
            self.save_permanent_drops()
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
                # List of all known engine executables to clean up
                engine_exes = [
                    'LivyLogs_Engine_New.exe', 
                    'LivyLogsEngine_v2.exe', 
                    'parser_v2.exe', 
                    'LivyLogsEngine.exe', 
                    'parser.exe', 
                    'LL_Engine.exe', 
                    'p_final.exe'
                ]
                
                for proc_name in engine_exes:
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', proc_name, '/T'], 
                                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    except: pass
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
        for win in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win, self.options_win, self.alexa_win, self.calc_win, self.armor_win, self.hitmiss_win, self.resists_win]:
            if win and win.window and win.window.winfo_exists():
                if win.config_key not in self.config: self.config[win.config_key] = {}
                self.config[win.config_key].update({
                    "width": str(win.window.winfo_width()),
                    "height": str(win.window.winfo_height()),
                    "x": str(win.window.winfo_x()),
                    "y": str(win.window.winfo_y())
                })
            elif win and hasattr(win, 'config_key'):
                # Also save from config if window is not currently open, to preserve last known position
                pass 

        self.config.set("General", "character_name", self.char_name.get())
        self.config.set("General", "api_url", self.api_url.get())
        self.config.set("General", "enable_sync", str(self.enable_sync.get()))
        with open("settings.ini", "w") as f: self.config.write(f)

    def _on_global_copy(self, event=None):
        focused = self.root.focus_get()
        if isinstance(focused, (tk.Text, tk.Entry)):
            try:
                content = ""
                if isinstance(focused, tk.Text):
                    if focused.tag_ranges("sel"):
                        content = focused.get("sel.first", "sel.last")
                elif isinstance(focused, tk.Entry):
                    if focused.selection_present():
                        content = focused.selection_get()
                
                if content:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(content)
                    return "break"
            except: pass
        return "break"

    def _on_global_select_all(self, event=None):
        focused = self.root.focus_get()
        if isinstance(focused, (tk.Text, tk.Entry)):
            if isinstance(focused, tk.Text):
                focused.tag_add("sel", "1.0", "end")
            elif isinstance(focused, tk.Entry):
                focused.selection_range(0, tk.END)
            return "break"
        return "break"

    def show_context_menu(self, event):
        if not hasattr(self, 'context_menu'):
            from constants import PANEL_DARK, TEXT_PRIMARY, ACCENT_BLUE
            self.context_menu = tk.Menu(self.root, tearoff=0, bg=PANEL_DARK, fg=TEXT_PRIMARY, activebackground=ACCENT_BLUE, borderwidth=1)
            self.context_menu.add_command(label="Copy", command=self._on_global_copy, accelerator="Ctrl+C")
            self.context_menu.add_command(label="Select All", command=self._on_global_select_all, accelerator="Ctrl+A")
            self.context_menu.add_separator()
            self.context_menu.add_command(label="LIVIUS", command=lambda: self.livius_win.show())
        
        self.context_menu.unpost()
        self.context_menu.post(event.x_root, event.y_root)

        # Win32 call to force menu to the very top
        def force_top():
            try:
                from constants import HWND_TOPMOST, SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW, user32
                hwnd = self.context_menu.winfo_id()
                if hwnd:
                    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            except: pass
            try:
                self.context_menu.focus_set()
            except: pass

        self.root.after(1, force_top)
        self.root.after(50, force_top)

    def drag_window(self, event):
        if not getattr(self, "_dragging_allowed", False):
            return
        self.is_interacting = True
        self.last_interaction_time = time.time()
        x, y = apply_snapping(self.root, self.root.winfo_pointerx() - self._offsetx, self.root.winfo_pointery() - self._offsety)
        self.root.geometry(f"+{x}+{y}")

    def click_window(self, event):
        # Only allow dragging if clicking near the borders
        # Or if clicking an empty area of the canvas
        margin = 10
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        # If it's a border click, allow it
        is_border = (event.x < margin or event.x > w - margin or 
                     event.y < margin or event.y > h - margin)
        
        # Also check if we clicked an actual object on the canvas
        # If we clicked "nothing" (background), we can allow drag too,
        # but the user said "only let the borders drag".
        if is_border:
            self._dragging_allowed = True
            self.is_interacting = True
            self.last_interaction_time = time.time()
            self._offsetx = event.x_root - self.root.winfo_x(); self._offsety = event.y_root - self.root.winfo_y()
        else:
            self._dragging_allowed = False

    def release_window(self, event=None):
        self._dragging_allowed = False
        self.is_interacting = False
        self.last_interaction_time = time.time()
        try:
            self.save_config()
        except: pass
        self.refresh_ui_only(force=True)

    def toggle_radio(self):
        if self.radio_mgr:
            self.radio_mgr.toggle()

    def next_radio_station(self):
        if self.radio_mgr:
            self.radio_mgr.next_station()

    def prev_radio_station(self):
        if self.radio_mgr:
            self.radio_mgr.prev_station()

    def show_radio_context_menu(self, event):
        if not self.radio_mgr:
            return
        
        # Reload stations from file before showing menu
        self.radio_mgr.load_stations()
        
        menu = tk.Menu(self.root, tearoff=0, bg=PANEL_DARK, fg=TEXT_PRIMARY, 
                       activebackground=ACCENT_BLUE, activeforeground=TEXT_PRIMARY, font=("Segoe UI", 9))
        
        # Get all stations from radio_mgr which includes custom ones
        for station in self.radio_mgr.stations.keys():
            menu.add_command(label=station, command=lambda s=station: self.radio_mgr.play(s))
            
        menu.post(event.x_root, event.y_root)

    def _update_radio_ui(self, is_playing):
        if not self.radio_mgr:
            self.main_canvas.itemconfig(self.radio_toggle_id, text="NO AUDIO".center(30), fill="#ff4444")
            return
        if is_playing:
            st = self.radio_mgr.current_station if self.radio_mgr.current_station else "PLAYING"
            self.main_canvas.itemconfig(self.radio_toggle_id, text=st.center(30), fill="#00ff00")
        else:
            self.main_canvas.itemconfig(self.radio_toggle_id, text="OFF".center(30), fill="#ff4444")

    def on_configure(self, event):
        if hasattr(self, "is_interacting") and self.is_interacting:
            self.last_interaction_time = time.time()

    def toggle_visibility(self, icon=None, item=None):
        try:
            if self.root.state() == "withdrawn" or getattr(self, "_minimized_to_tray", False):
                self._minimized_to_tray = False
                self.root.after(0, self.start_show)
            else:
                self._minimized_to_tray = True
                self.root.after(0, lambda: self.start_hide(minimize=True))
        except Exception as e:
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- TOGGLE ERROR {datetime.now()} ---\n{e}\n")
            except: pass


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
                self.reset_session_data()
                self.start_c_engine(p)
                # User clicked YES and finished - close options window
                if hasattr(self, 'options_win') and self.options_win and self.options_win.window and self.options_win.window.winfo_exists():
                    self.options_win.close()
                self.refresh_ui_only(force=True)

            if skip_prompt or (not self.char_name.get() and self.disable_warnings.get()):
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
        self.reset_session_data()
        self.reset_damage_meter_manual()
        self.reset_leaderboard_manual()
        self.reset_skimmers_manual()
        self.reset_details_manual()
        self.refresh_ui_only(force=True)

    def open_equalizer(self):
        if hasattr(self, 'eq_win') and self.eq_win:
            self.eq_win.show()

    def open_aux_mode(self, event=None):
        """Allows users to select and play local audio files/playlists."""
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="Select Local Audio Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("All Files", "*.*")]
        )
        if files:
            if not self.radio_mgr:
                from tkinter import messagebox
                messagebox.showerror("Error", "Radio Manager is not initialized.")
                return

            # Check if it's a single file or multiple
            if len(files) == 1:
                # Play single file
                self.radio_mgr.play_local_file(files[0])
            else:
                # Play multiple files (playlist)
                self.radio_mgr.play_local_playlist(list(files))

    def reset_session_data(self):
        self.player_data = {}
        self.loot_data = {}
        self.all_events = []
        self.locally_seen_players = {}
        self.leaderboard_data = {}
        self.known_npcs = set()
        self.known_players = set()
        self.friendly_players = set()
        self.enemy_players = set()
        self.player_arrival_order = []
        self.status_cooldowns = {}
        self.damage_history = {}
        self.damage_taken_history = {}
        self.healing_history = {}
        self.top_dps_durations = {}
        self.top_tank_durations = {}
        self.top_healing_durations = {}
        self.current_top_dps = {'friendly': None, 'enemy': None}
        self.current_top_tank = {'friendly': None, 'enemy': None}
        self.current_top_healing = {'friendly': None, 'enemy': None}
        self.current_focus_target = {'friendly': None, 'enemy': None}
        # Reset player counts
        for p in self.player_data.values():
            p["poison_hits"] = 0
            p["incapacitated_count"] = 0
            p["kill_count"] = 0
            p["died"] = False
        self.app_start_time = None
        self._encounter_start_stats = {}
        self.session_start_time = datetime.now()
        self.last_combat_time = 0
        self.last_log_sync_time = None
        
        # Reset Damage Meter baseline
        self.last_dm_reset = datetime.now()
        
        # Clear drill-down states and internal row-tracking to ensure windows return to primary lists smoothly
        if hasattr(self, 'details_win'): 
            self.details_win.is_drilldown = False
            self.details_win.selected_player = None
            self.details_win._row_frames = {}
            self.details_win._row_widgets = {}
            self.details_win._last_log_key = None
            self.details_win._last_list_key = None
            self.details_win._last_players = []
            if hasattr(self.details_win, 'list_container'):
                for w in self.details_win.list_container.winfo_children(): w.destroy()
        if hasattr(self, 'leaderboard_win'): 
            self.leaderboard_win.is_drilldown = False
            self.leaderboard_win.selected_player = None
            self.leaderboard_win._row_frames = {}
            self.leaderboard_win._row_widgets = {}
            self.leaderboard_win._last_log_key = None
            self.leaderboard_win._last_order = []
            if hasattr(self.leaderboard_win, 'list_container'):
                for w in self.leaderboard_win.list_container.winfo_children(): w.destroy()
        if hasattr(self, 'skimmers_win'): 
            self.skimmers_win.is_drilldown = False
            self.skimmers_win.selected_player = None
            self.skimmers_win.drill_down_player = None
            self.skimmers_win._row_frames = {}
            self.skimmers_win._row_widgets = {}
            self.skimmers_win._last_players = []
            if hasattr(self.skimmers_win, 'list_container'):
                for w in self.skimmers_win.list_container.winfo_children(): w.destroy()
        if hasattr(self, 'damage_meter_win'):
            # Clear Damage Meter labels immediately
            for lbl in ['lbl_dmg', 'lbl_dps', 'lbl_dur', 'lbl_hit', 'lbl_taken', 'lbl_miss', 'lbl_xp', 'lbl_xph']:
                if hasattr(self.damage_meter_win, lbl):
                    try:
                        widget = getattr(self.damage_meter_win, lbl)
                        if widget.winfo_exists():
                            default_val = "0.0%" if "pct" in lbl or "hit" in lbl or "miss" in lbl else "0"
                            if "dps" in lbl: default_val = "0.0"
                            if "dur" in lbl: default_val = "0s"
                            widget.config(text=default_val)
                    except: pass

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
                    
                    test_log = os.path.join(os.getcwd(), "testing", "test_chatlog.txt")
                    if not os.path.exists(os.path.dirname(test_log)):
                        os.makedirs(os.path.dirname(test_log), exist_ok=True)
                    if not os.path.exists(test_log):
                        with open(test_log, "w") as f:
                            f.write("[Spatial]  00:00:00 [GROUP] System: Welcome to the test log.\n")
                    
                    # Switch to test log
                    self.root.after(0, lambda: self.file_path_var.set(test_log))
                    
                    # RESET DATA FOR NEW SESSION
                    self.root.after(0, self.reset_session_data)
                    
                    # Force a refresh after a small delay to ensure lists are clear
                    self.root.after(500, lambda: self.refresh_ui_only(force=True))
                    
                    # RESTART ENGINE for test log
                    self.start_c_engine(test_log)
                    
                    # Log state for debugging
                    try:
                        with open("livius_debug.log", "a") as f:
                            f.write(f"[{time.strftime('%H:%M:%S')}] TEST SESSION RESTARTED. File: {test_log}\n")
                    except: pass
                    
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
                        
                        # RESET DATA FOR NEW SESSION
                        self.root.after(0, self.reset_session_data)
                        
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
        
        # Wait until we are CONNECTED before starting to generate data
        # Also wait for reset_session_data to finish (it's queued via root.after)
        time.sleep(1.0) 

        players = ["You", "Turd", "Leloglo", "Rehote", "Ma-o", "Fikiosa", "Eliemau"]
        enemies = ["Dark Jedi", "Rebel Scum", "Imp Trooper", "Bounty Hunter", "Sith Lord"]
        
        # Manually inject some players into friendlies/enemies and player_data to bypass log delay
        for p in players:
             norm_p = normalize_name(p)
             self.known_players.add(norm_p.lower())
             if norm_p not in self.player_arrival_order:
                 self.player_arrival_order.append(norm_p)
             self.friendly_players.add(norm_p)
             if norm_p not in self.player_data:
                 self.player_data[norm_p] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 10, "incapacitated_count": 2, "kill_count": 3}
             
             # Also inject some initial statuses for immediate visual feedback
             self.status_cooldowns[norm_p] = {"knockdown": time.time(), "intimidate": time.time() - 5}
             
        for e in enemies:
             norm_e = normalize_name(e)
             self.known_players.add(norm_e.lower())
             if norm_e not in self.player_arrival_order:
                 self.player_arrival_order.append(norm_e)
             self.enemy_players.add(norm_e)
             if norm_e not in self.player_data:
                 self.player_data[norm_e] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "lb_mobs": 0, "lb_xp": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0, "xp_history": [], "looted_items": [], "total_credits": 0, "poison_hits": 5, "incapacitated_count": 1, "kill_count": 0}

        try:
            with open("livius_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] TEST DATA START: Friendlies={len(self.friendly_players)}, Enemies={len(self.enemy_players)}\n")
                f.write(f"  FRIENDLIES: {list(self.friendly_players)}\n")
                f.write(f"  ENEMIES: {list(self.enemy_players)}\n")
                f.write(f"  ARRIVAL ORDER: {self.player_arrival_order}\n")
        except: pass

        items = ["Work light", "Broken Electrobinoculars", "A Damaged Datapad", "CDEF Pistol", "Stun Baton", "Heavy Two-Handed Sword", "Enhanced DH-17 Carbine", "T-21 Rifle"]
        xp_types = ["Combat", "Weapon", "General", "Medicine", "Scout", "Surveying"]
        abilities = ["Power Shot", "Fire Knockdown", "Posture Change", "Intimidate", "Health Shot II", "Bleeding Shot", "Stun", "Melee Hit", "Force Choke", "Mind Blast", "Scatter Shot"]
        targets = ["a SpecForce marine", "a senior SpecForce infiltrator", "a Rebel Colonel", "a Rebel Major General", "an Imperial Stormtrooper", "a Krayt Dragon", "a Rancor"]
        damage_types = ["energy", "kinetic", "elemental", "stun"]
        
        log_path = os.path.join(os.getcwd(), "testing", "test_chatlog.txt")
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Initial 123 messages to mark friendlies
        with open(log_path, "a") as f:
            for p in players:
                ts = datetime.now().strftime("%H:%M:%S")
                f.write(f"[Groupchat]  {ts} {p}: 123\n")
                norm_p = normalize_name(p)
                if norm_p not in self.player_arrival_order:
                    self.player_arrival_order.append(norm_p)
                self.friendly_players.add(norm_p)
            f.flush()

        # Wait until we are CONNECTED before starting to generate data
        while self.running and self.test_mode.get():
            if hasattr(self, 'status_id'):
                # In the dot mode, connected is #00ff88
                if self.main_canvas.itemcget(self.status_id, "fill") == "#00ff88":
                    time.sleep(1.0)
                    break
            time.sleep(0.5)

        while self.running and self.test_mode.get():
            try:
                # Force refresh UI frequently during test mode to show icons
                if hasattr(self, 'livius_win'):
                    self.root.after(0, lambda: self.livius_win.refresh(force=True))

                with open(log_path, "a") as f:
                    ts = datetime.now().strftime("%H:%M:%S")
                    event_type = random.random()
                    
                    # Force statuses frequently for all players/enemies in test mode
                    if random.random() < 0.6: # High frequency for testing
                        p_target = random.choice(players + enemies)
                        st_type = random.choice(["Fire Knockdown", "Posture Change", "Intimidate"])
                        # Inject directly into state using normalized name
                        norm_target = normalize_name(p_target)
                        status_key = st_type.lower().split()[-1]
                        if norm_target not in self.status_cooldowns: self.status_cooldowns[norm_target] = {}
                        self.status_cooldowns[norm_target][status_key] = time.time()
                        
                        line = f"[Combat]  {ts} A_Giant_Spider {st_type} {p_target} for 0 points of damage.\n"
                        f.write(line)

                    if random.random() < 0.3: # Focused damage burst
                        target = random.choice(players + enemies)
                        for _ in range(3):
                            p1 = random.choice(players + enemies)
                            dmg = random.randint(500, 2000)
                            line = f"[Combat]  {ts} {p1} hits {target} for {dmg} points of damage.\n"
                            f.write(line)
                        f.flush()

                    if event_type < 0.2: # Simple Hits
                        p1 = random.choice(players + enemies)
                        target = random.choice(targets + players + enemies)
                        dmg = random.randint(150, 1200)
                        line = f"[Combat]  {ts} {p1} hits {target} for {dmg} points of damage.\n"
                        f.write(line)
                    elif event_type < 0.4: # Ability Hits & Statuses
                        p1 = random.choice(players + enemies)
                        target = random.choice(targets + players + enemies)
                        dmg = random.randint(300, 1500)
                        ability = random.choice(abilities)
                        
                        # Simulate some high healing for testing
                        if "Health" in ability:
                            heal_val = random.randint(500, 2000)
                            if p1 not in self.healing_history: self.healing_history[p1] = []
                            self.healing_history[p1].append((time.time(), heal_val))

                        line = f"[Combat]  {ts} {p1} {ability} {target} for {dmg} points of damage.\n"
                        f.write(line)
                        
                        # Occasionally remove intimidate
                        if ability == "Intimidate" and random.random() < 0.3:
                            time.sleep(0.5)
                            f.write(f"[Combat]  {ts} {target} no longer intimidated.\n")
                    elif event_type < 0.5: # Healing
                        p1 = random.choice(players)
                        p2 = random.choice(players)
                        heal = random.randint(100, 800)
                        line = f"[Combat]  {ts} {p1} heals {p2} for {heal} points of damage.\n"
                        f.write(line)
                    elif event_type < 0.6: # Loot credits
                        p = random.choice(players)
                        target = random.choice(targets)
                        credits = random.randint(80, 500)
                        line = f"[Combat]  {ts} {p} looted {credits} credits from {target}.\n"
                        f.write(line)
                    elif event_type < 0.7: # Loot item
                        p = random.choice(players)
                        target = random.choice(targets)
                        item = random.choice(items)
                        line = f"[Combat]  {ts} {p} looted {item} from {target}.\n"
                        f.write(line)
                    elif event_type < 0.8: # Mobs (Defeated)
                        p = random.choice(players)
                        target = random.choice(targets)
                        line = f"[Combat]  {ts} {p} has defeated {target}.\n"
                        f.write(line)
                    elif event_type < 0.85: # Poison
                        p1 = random.choice(players)
                        target = random.choice(enemies)
                        # More poison hits
                        line = f"[Combat]  {ts} You apply poison to {target}.\n" if p1 == "You" else f"[Combat]  {ts} {p1} applies poison to {target}.\n"
                        f.write(line)
                    elif event_type < 0.9: # Incapacitated
                        target = random.choice(players + enemies)
                        line = f"[Combat]  {ts} {target} has been incapacitated by something.\n"
                        f.write(line)
                        p1 = random.choice(players + enemies)
                        target = random.choice(players + enemies)
                        if target == "You":
                            line = f"[Combat]  {ts} You have been incapacitated by {p1}.\n"
                        else:
                            line = f"[Combat]  {ts} {target} has been incapacitated by {p1}.\n"
                        f.write(line)
                    elif event_type < 0.95: # XP
                        xp = random.randint(250, 5000)
                        xt = random.choice(xp_types)
                        line = f"[Combat]  {ts} You receive {xp} points of {xt} experience.\n"
                        f.write(line)
                    elif event_type < 0.98: # Death / Kill
                        p = random.choice(players + enemies)
                        line = f"[Combat]  {ts} {p} has died.\n"
                        f.write(line)
                        
                        # Occasionally simulate a PvP Kill by another player
                        if random.random() < 0.5:
                            killer = random.choice(players)
                            victim = random.choice(enemies)
                            f.write(f"[Combat]  {ts} {killer} has defeated {victim}.\n")
                    else: # Mitigation (Dodge/Parry)
                        p1 = random.choice(players)
                        target = random.choice(targets)
                        mit = random.choice(["dodges", "parries", "evades"])
                        line = f"[Combat]  {ts} {target} {mit} {p1}'s attack!\n"
                        f.write(line)
                    
                    # INJECT SOME ROLLING DAMAGE for Top DPS/Tank testing
                    if random.random() < 0.3:
                        p_dmg = random.choice(players + enemies)
                        d_val = random.randint(500, 2000)
                        victim = random.choice(players + enemies)
                        f.write(f"[Combat]  {ts} {p_dmg} hits {victim} for {d_val} damage.\n")
                        # Also add a heavy hitter to see growth (Turd is injected as Friendly)
                        f.write(f"[Combat]  {ts} Turd hits target for 5000 damage.\n")
                        # Add someone taking a lot of damage to see Sheep icon (Bob is usually a target)
                        f.write(f"[Combat]  {ts} Someone hits Bob for 10000 damage.\n")
                    
                    f.flush()
            except Exception as e:
                try:
                    with open("crash_log.txt", "a") as cf:
                        cf.write(f"--- TEST GENERATOR ERROR {datetime.now()} ---\n{e}\n")
                except: pass
            
            time.sleep(random.uniform(0.1, 0.5))

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
    def init_resize_popout(self, e, w, dw, dh): 
        self._rs_x = e.x_root
        self._rs_y = e.y_root
        self._rs_w = w.winfo_width()
        self._rs_h = w.winfo_height()

    def do_resize_popout(self, e, w, dw, dh): 
        nw = max(200, self._rs_w + e.x_root - self._rs_x)
        nh = max(200, self._rs_h + e.y_root - self._rs_y)
        w.geometry(f"{nw}x{nh}")

    def save_size(self, e): 
        self.save_config()
    
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
