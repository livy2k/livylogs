import tkinter as tk
import os
import sys
import time
import json
import threading
import subprocess
from datetime import datetime, timedelta
from configparser import ConfigParser
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk, messagebox, filedialog
import ctypes
from ctypes import wintypes

from constants import (
    WINDOW_BG, PANEL_BG, PANEL_DARK, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    ACCENT_BLUE, BORDER_COLOR, BORDER_HIGHLIGHT, BUTTON_BG, BUTTON_HOVER,
    MIN_WIDTH, MIN_HEIGHT, SNAP_THRESHOLD, user32, kernel32, winmm,
    HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE,
    SWP_SHOWWINDOW, SWP_HIDEWINDOW, ENTRY_BG, WINDOWPLACEMENT
)
from utils import is_window_minimized, apply_snapping, extract_character_id
from parser_engine import parse_combat_log, calculate_dps
from ui_base import ThemedMessagebox

# Popout Windows
from windows.skimmers import SkimmersWindow
from windows.damage_meter import DamageMeterWindow
from windows.leaderboard import LeaderboardWindow
from windows.details import DetailsWindow
from windows.options import OptionsWindow

class CombatLogApp:
    def __init__(self, root):
        print("DEBUG: Initializing CombatLogApp")
        self.root = root
        self.root.title("Combat Log Analyzer")
        self.root.geometry("260x220")
        self.root.configure(bg=WINDOW_BG)
        
        self.target_hwnd = self.find_target_window()
        
        # Font objects
        self.font_stats_obj = tkfont.Font(family="Segoe UI Variable Display", size=20, weight="bold")
        self.font_title_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_small_obj = tkfont.Font(family="Segoe UI", size=9)
        self.font_button_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Vertical.TScrollbar", background=BUTTON_BG, troughcolor=PANEL_BG, bordercolor=BORDER_COLOR, arrowcolor=TEXT_SECONDARY)

        self.config = ConfigParser()
        self.config.read("settings.ini")

        initial_log_path = self.config.get("General", "log_path", fallback="")
        initial_alpha = self.config.getfloat("General", "transparency", fallback=1.0)
        initial_width = max(MIN_WIDTH, self.config.getint("General", "width", fallback=450))
        initial_height = max(MIN_HEIGHT, self.config.getint("General", "height", fallback=80))
        initial_x = self.config.get("General", "x", fallback="50")
        initial_y = self.config.get("General", "y", fallback="50")

        self.root.geometry(f"{initial_width}x{initial_height}+{initial_x}+{initial_y}")
        self.target_alpha = initial_alpha
        self.current_alpha = 0.0
        self.root.attributes("-alpha", 0.0)
        self.root.overrideredirect(True)
        
        self._last_topmost_state = False
        self.fade_speed = 0.05
        self.fade_after_id = None
        self.file_path_var = tk.StringVar(value=initial_log_path)
        self.disable_warnings = tk.BooleanVar(value=self.config.getboolean("General", "disable_warnings", fallback=False))
        self.char_name = tk.StringVar(value=self.config.get("General", "character_name", fallback=""))
        if not self.char_name.get() and initial_log_path:
            self.char_name.set(extract_character_id(initial_log_path))
        self.api_url = tk.StringVar(value=self.config.get("General", "api_url", fallback=""))
        self.enable_sync = tk.BooleanVar(value=self.config.getboolean("General", "enable_sync", fallback=False))

        self.skimmers_win = SkimmersWindow(self)
        self.damage_meter_win = DamageMeterWindow(self)
        self.leaderboard_win = LeaderboardWindow(self)
        self.details_win = DetailsWindow(self)
        self.options_win = OptionsWindow(self)
        
        self.is_interacting = False
        self.last_interaction_time = 0
        
        # Window-specific data containers
        self.dm_damage = {}
        self.dm_taken = {}
        
        self.actual_app_start_time = datetime.now()
        self.last_reset_time = self.actual_app_start_time
        self.running = True
        self.engine_process = None
        
        threading.Thread(target=self.start_pipe_listener, daemon=True).start()
        threading.Thread(target=self.web_sync_loop, daemon=True).start()
        
        self.root.after(300, self.initial_show)
        self.root.after(800, self.check_target_window)
        self.root.after(1000, self.start_show)
        if initial_log_path:
            self.root.after(1200, lambda: self.start_c_engine(initial_log_path))
        
        self.player_data = {}
        self.leaderboard_data = {}
        self.loot_data = {}
        self.last_dm_reset = None
        self.last_lb_reset = None
        self.last_sk_reset = None
        self.last_dt_reset = None
        self.all_events = []
        self.sync_data = {} # Data from web API
        self.last_sync_time = 0
        self.last_read_offset = 0
        self.last_processed_file = ""
        self.app_start_time = None
        self.last_combat_time = 0
        self.last_log_sync_time = None
        self.last_ui_update_time = 0
        self.ui_update_delay = 0.05
        self.pulse_state = False
        self.last_pulse_time = 0
        self.time_window_details = self.config.getint("General", "time_window_details", fallback=30)
        self.time_window_leaderboard = self.config.getint("General", "time_window_leaderboard", fallback=30)
        self.time_window_skimmers = 60
        self.time_window_dm = 30
        self.always_on_top = False
        self.skimmer_search_query = tk.StringVar()
        self.skimmer_search_mode = False
        self.leaderboard_reset_time = None
        self.current_detail_player = None
        self.current_skimmer_player = None
        self.inventory_full = False
        self.inventory_full_time = None

        self.build_layout()
        self.start_ticker_loop()

    def initial_show(self):
        try:
            self.root.withdraw()
            hwnd = self.root.winfo_id()
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_HIDEWINDOW)
        except: pass

    def start_c_engine(self, log_path):
        print(f"DEBUG: Attempting to start C Engine for: {log_path}")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "log_engine.exe", "/T"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if self.engine_process: self.engine_process.terminate()
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            engine_exe = os.path.join(base_path, "log_engine.exe")
            if os.path.exists(engine_exe):
                print(f"DEBUG: Launching C Engine: {engine_exe}")
                self.engine_process = subprocess.Popen([engine_exe, log_path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                print(f"DEBUG: log_engine.exe not found at {engine_exe}")
        except Exception as e:
            print(f"DEBUG: Error starting C Engine: {e}")

    def find_target_window(self):
        target = [None]
        def cb(hwnd, lp):
            if user32.IsWindowVisible(hwnd):
                buf = ctypes.create_unicode_buffer(255)
                user32.GetWindowTextW(hwnd, buf, 255)
                if "SwgClient" in buf.value or "Star Wars Galaxies" in buf.value:
                    target[0] = hwnd; return False
            return True
        user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(cb), 0)
        return target[0]

    def is_foreground_ours(self):
        fg = user32.GetForegroundWindow()
        if not fg: return False
        fg_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(fg, ctypes.byref(fg_pid))
        if fg_pid.value == kernel32.GetCurrentProcessId(): return True
        if self.target_hwnd and user32.IsWindow(self.target_hwnd):
            if fg == self.target_hwnd: return True
            t_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(self.target_hwnd, ctypes.byref(t_pid))
            if fg_pid.value == t_pid.value: return True
        return False

    def _get_managed_windows(self):
        managed = [self.root]
        for w in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win, self.options_win]:
            if w.window and w.window.winfo_exists(): managed.append(w.window)
        return managed

    def check_target_window(self):
        try:
            if not self.target_hwnd or not user32.IsWindow(self.target_hwnd): self.target_hwnd = self.find_target_window()
            should_show = (self.is_foreground_ours() or self.always_on_top) and not is_window_minimized(self.target_hwnd)
            if should_show:
                self.start_show()
                for win in self._get_managed_windows():
                    win.attributes("-topmost", True)
                    user32.SetWindowPos(win.winfo_id(), HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                self._last_topmost_state = True
            else:
                if not hasattr(self, '_hide_grace_after_id') or self._hide_grace_after_id is None:
                    self._hide_grace_after_id = self.root.after(1000, self._perform_graceful_hide)
        except: pass
        self.root.after(250, self.check_target_window)

    def _perform_graceful_hide(self):
        self._hide_grace_after_id = None
        if not self.is_foreground_ours() and not self.always_on_top:
            self.start_hide()

    def start_show(self):
        if self.root.state() == "withdrawn": self.root.deiconify()
        for win in self._get_managed_windows():
            if win.state() == "withdrawn": win.deiconify()
        if self.current_alpha < self.target_alpha: self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.1)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.root.after(20, self.fade_in)

    def start_hide(self):
        if self.current_alpha > 0: self.fade_out()

    def fade_out(self):
        if self.current_alpha > 0:
            self.current_alpha = max(0, self.current_alpha - 0.1)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.root.after(20, self.fade_out)
        else:
            for win in self._get_managed_windows(): win.withdraw()

    def build_layout(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0, background=PANEL_DARK, darkcolor=PANEL_DARK, lightcolor=PANEL_DARK, troughcolor=WINDOW_BG, bordercolor=BORDER_COLOR, arrowcolor=TEXT_SECONDARY)
        style.map("Vertical.TScrollbar", background=[('active', ACCENT_BLUE), ('pressed', ACCENT_BLUE)])

        self.root_border = tk.Frame(self.root, bg=BORDER_COLOR, padx=1, pady=1)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        outer = tk.Frame(self.root_border, bg=WINDOW_BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        outer.bind("<Button-1>", self.click_window)
        outer.bind("<B1-Motion>", self.drag_window)
        outer.bind("<ButtonRelease-1>", self.release_window)
        self.root.bind("<Configure>", self.on_configure)

        header = tk.Frame(outer, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header.pack(fill=tk.BOTH, expand=True)
        title_bar = tk.Frame(header, bg=PANEL_DARK, height=25); title_bar.pack(fill=tk.X)
        
        exit_btn = tk.Label(title_bar, text=" ✕ ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2")
        exit_btn.pack(side=tk.RIGHT)
        exit_btn.bind("<Button-1>", lambda e: self.on_exit())

        menu_btn = tk.Label(title_bar, text=" SETTINGS ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2")
        menu_btn.pack(side=tk.RIGHT)
        menu_btn.bind("<Button-1>", lambda e: self.toggle_menu())
        self.ontop_btn = tk.Label(title_bar, text="ONTOP: OFF", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2"); self.ontop_btn.pack(side=tk.LEFT)
        self.ontop_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())

        nav = tk.Frame(header, bg=PANEL_DARK); nav.pack(fill=tk.X, padx=10, pady=(0, 5))
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
        self.lbl_loot = btn("LOOT", self.skimmers_win.show)
        self.lbl_refresh = btn("RESCAN", lambda: self.analyze_log(manual=True))
        self.lbl_version = tk.Label(nav, text="1.0", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack(side=tk.RIGHT)

        stats = tk.Frame(outer, bg=WINDOW_BG); stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.lbl_damage_val = self.create_stat_box(stats, "DAMAGE", "0").value_label
        self.lbl_dps_val = self.create_stat_box(stats, "DPS", "0.00").value_label
        self.lbl_time_val = self.create_stat_box(stats, "DURATION", "0s").value_label
        
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
        pipe_path = r'\\.\pipe\LivyLogsPipe'
        print(f"DEBUG: Starting Pipe Listener on {pipe_path}")
        while self.running:
            if not kernel32.WaitNamedPipeW(pipe_path, 1000):
                time.sleep(1); continue
            print("DEBUG: Pipe available, connecting...")
            h = kernel32.CreateFileW(pipe_path, 0x80000000, 0, None, 3, 0x80, None)
            if h == -1:
                print(f"DEBUG: Pipe connection failed: {kernel32.GetLastError()}")
                time.sleep(1); continue
            print("DEBUG: Connected to C Engine Pipe")
            buf = ctypes.create_string_buffer(65536); bytes_read = wintypes.DWORD(); leftover = ""
            while self.running:
                if kernel32.ReadFile(h, buf, 65536, ctypes.byref(bytes_read), None) and bytes_read.value > 0:
                    lines = (leftover + buf.raw[:bytes_read.value].decode('utf-8', 'ignore')).split('\n')
                    leftover = lines.pop()
                    for i, line in enumerate(lines):
                        if line.strip():
                            try:
                                data = json.loads(line); data["timestamp"] = datetime.now()
                                self.process_external_event(data, is_last=(i == len(lines)-1))
                            except Exception as e:
                                print(f"DEBUG: JSON parse error: {e}")
                else:
                    print(f"DEBUG: Pipe read failed or closed. Last error: {kernel32.GetLastError()}")
                    break
            kernel32.CloseHandle(h)
            print("DEBUG: Pipe closed, retrying...")

    def process_external_event(self, event, is_last=False):
        # Implementation of event processing
        event_type = event.get("type"); source = event.get("source", "Unknown"); damage = event.get("damage", 0)
        item = event.get("item", ""); timestamp = event.get("timestamp"); target = event.get("target", "Target")
        
        if source.lower() == "you": event_type = "dealt"
        elif target.lower() == "you": event_type = "taken"
        elif event_type == "damage": event_type = "dealt"
        
        is_damage = damage > 0 or event_type in ["dealt", "taken", "damage"]
        internal_event = {"timestamp": timestamp, "type": event_type, "source": source, "target": target, "damage": damage, "healing": 0, "item": item}

        if self.app_start_time is None and is_damage:
            self.app_start_time = timestamp; self.last_log_sync_time = timestamp; self.last_combat_time = time.time()
            max_hist = 65; history_limit = datetime.now() - timedelta(minutes=max_hist)
            self.all_events = [e for e in self.all_events if (e["timestamp"] and e["timestamp"] >= self.app_start_time) or (e["timestamp"] and e["timestamp"] >= history_limit)]

        self.all_events.append(internal_event)
        if len(self.all_events) > 5000: self.all_events = self.all_events[-5000:]

        now = time.time()
        if self.app_start_time and (now - self.last_combat_time > self.time_window_dm):
            self.app_start_time = None; self.last_log_sync_time = None; self.leaderboard_data = {}; self.player_data = {}

        if is_damage:
            self.last_combat_time = now; self.last_log_sync_time = timestamp
            if self.app_start_time is None: self.app_start_time = timestamp

        if is_last or (now - self.last_ui_update_time > self.ui_update_delay):
            if self.running:
                try:
                    self.root.after_idle(lambda: self.refresh_ui_only(force=is_last))
                    self.last_ui_update_time = now
                except: pass

    def analyze_log(self, manual=False):
        if manual: 
            self.all_events = []; self.last_read_offset = -1; self.app_start_time = None; 
            self.last_combat_time = 0; self.player_data = {}; self.loot_data = {}; self.leaderboard_data = {}
            self.last_log_mtime = 0; self.last_log_size = 0
            print("DEBUG: Manual reset triggered")
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path): return
        
        try:
            st = os.stat(path); mtime, size = st.st_mtime, st.st_size
            if not manual and hasattr(self, 'last_log_mtime') and mtime <= self.last_log_mtime and size <= self.last_log_size:
                if time.time() - getattr(self, 'last_forced_read_time', 0) < 0.2: return
            self.last_log_mtime, self.last_log_size = mtime, size
            self.last_forced_read_time = time.time()
        except: pass

        if os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.txt', '.log'))]
            if not files: return
            path = max(files, key=os.path.getmtime)

        if path != self.last_processed_file:
            self.last_read_offset = -1 if not self.last_processed_file or manual else 0
            self.all_events = []; self.last_processed_file = path; self.app_start_time = None; self.last_combat_time = 0

        new_events, new_offset = parse_combat_log(path, self.last_read_offset)
        if new_events:
            existing = set((e.get("timestamp"), e.get("type"), e.get("source"), e.get("target"), e.get("damage")) for e in self.all_events[-1000:])
            self.all_events.extend([e for e in new_events if (e.get("timestamp"), e.get("type"), e.get("source"), e.get("target"), e.get("damage")) not in existing])
        self.last_read_offset = new_offset
        
        self.process_events_for_ui(self.all_events, manual=manual)
        self.refresh_ui_only(force=True)

    def start_ticker_loop(self):
        if self.running:
            self.analyze_log()
            # ticker updates are never forced to maintain high FPS performance
            self.refresh_ui_only(force=False)
            self.root.after(100, self.start_ticker_loop)

    def refresh_ui_only(self, force=False):
        if not hasattr(self, 'lbl_damage_val'): return
        
        # Pause UI refreshes during interaction to prevent flickering
        if self.is_interacting and not force:
            if time.time() - self.last_interaction_time < 2.0: # 2s safety timeout
                return
            else:
                self.is_interacting = False
        
        now_ts = time.time()
        if now_ts - self.last_pulse_time > 0.3:
            self.pulse_state = not self.pulse_state; self.last_pulse_time = now_ts

        if not self.app_start_time:
            self.lbl_damage_val.config(text="0"); self.lbl_dps_val.config(text="0.00"); self.lbl_time_val.config(text="0s", fg="cyan")
        else:
            events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
            dmg_dealt, dmg_taken, dps, dur, miss, hit, avoid, taken = calculate_dps(events)
            is_paused = self.last_combat_time > 0 and (time.time() - self.last_combat_time) > self.time_window_dm
            
            if not is_paused and self.last_combat_time > 0:
                anchor = getattr(self, 'last_log_sync_time', self.app_start_time)
                dur = (anchor + timedelta(seconds=time.time() - self.last_combat_time) - self.app_start_time).total_seconds()
                if dur > 0: dps = dmg_dealt / dur
                else: dps = 0
            
            dur_color = "cyan" if is_paused else TEXT_PRIMARY
            if dur > 0 and self.last_combat_time == 0: dur_color = "cyan" if self.pulse_state else "#AAAAAA"

            self.lbl_damage_val.config(text=f"{dmg_dealt:.0f}")
            self.lbl_dps_val.config(text=f"{dps:.2f}")
            self.lbl_time_val.config(text=f"{dur:.0f}s", fg=dur_color)

        # Refresh popout windows
        self.damage_meter_win.refresh(force=force)
        self.leaderboard_win.refresh(force=force)
        self.skimmers_win.refresh(force=force)
        self.details_win.refresh(force=force)
        self.options_win.refresh(force=force)

    def process_events_for_ui(self, all_events, manual=False):
        now_dt = datetime.now()
        sk_limit = now_dt - timedelta(minutes=self.time_window_skimmers)
        dt_limit = now_dt - timedelta(minutes=self.time_window_details)
        
        # We'll use local dictionaries to build the state and then assign them
        # This prevents flickering if the loop is interrupted
        new_player_data = {}
        new_loot_data = {}
        new_inventory_full = False
        
        active_ids = set(id(e) for e in all_events if self.app_start_time and e["timestamp"] and e["timestamp"] >= self.app_start_time)

        for e in all_events:
            ts = e["timestamp"]
            if not ts: continue
            
            src = e["source"].capitalize(); src = "You" if src.lower() == "you" else src
            tgt_raw = e["target"].capitalize(); tgt_raw = "You" if tgt_raw.lower() == "you" else tgt_raw
            is_npc = " (" in src or src.lower().startswith(("a ", "an ", "your target"))
            
            if e["type"] == "loot":
                # Check skimmer reset
                if ts >= sk_limit and (not self.last_sk_reset or ts >= self.last_sk_reset):
                    if src not in new_loot_data: new_loot_data[src] = []
                    new_loot_data[src].append({"item": e["item"], "target": e["target"], "timestamp": ts})
                
                # Also track for leaderboard if not reset there
                if not self.last_lb_reset or ts >= self.last_lb_reset:
                    if "lb_loot" not in new_player_data.get(src, {}):
                        if src not in new_player_data: new_player_data[src] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0}
                        else: new_player_data[src]["lb_loot"] = 0
                    new_player_data[src]["lb_loot"] += 1
                continue
            
            if e["type"] == "inventory_full":
                if ts >= sk_limit and (not self.last_sk_reset or ts >= self.last_sk_reset): 
                    new_inventory_full = True
                continue

            # Filtering for Player Data (Damage/Healing)
            # DM uses app_start_time (current combat) + dm_reset
            # DT uses dt_limit + dt_reset
            # LB uses all data (potentially filtered by lb_reset)
            
            # For simplicity, we populate a unified player_data but we'll filter it inside windows if needed,
            # OR we populate it with everything relevant to ANY window.
            
            if not is_npc:
                if src not in new_player_data: new_player_data[src] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0}
                
                # Global/Details log
                if ts >= dt_limit and (not self.last_dt_reset or ts >= self.last_dt_reset):
                    if e["damage"] > 0:
                        ts_str = ts.strftime("%H:%M:%S")
                        new_player_data[src]["logs"].append({"text": f"[{ts_str}] Dealt {e['damage']:.0f} to {tgt_raw}", "timestamp": ts})
                    elif e["healing"] > 0:
                        ts_str = ts.strftime("%H:%M:%S")
                        new_player_data[src]["logs"].append({"text": f"[{ts_str}] Healed {e['healing']:.0f} on {tgt_raw}", "timestamp": ts})

                # Damage Meter stats
                if id(e) in active_ids and (not self.last_dm_reset or ts >= self.last_dm_reset):
                    new_player_data[src]["dm_damage"] += e["damage"]
                    new_player_data[src]["dm_healing"] += e["healing"]
                    if e["type"] == "dealt":
                        if e.get("is_mitigated"):
                            new_player_data[src]["dm_misses"] = new_player_data[src].get("dm_misses", 0) + 1
                        elif e["damage"] > 0:
                            new_player_data[src]["dm_hits"] = new_player_data[src].get("dm_hits", 0) + 1
                
                # Leaderboard stats (Damage/Healing)
                if not self.last_lb_reset or ts >= self.last_lb_reset:
                    new_player_data[src]["damage"] += e["damage"]
                    new_player_data[src]["healing"] += e["healing"]
            
            tgt = tgt_raw
            if e["damage"] > 0 and not (" (" in tgt or tgt.lower().startswith(("a ", "an "))):
                if tgt not in new_player_data: new_player_data[tgt] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0}
                if ts >= dt_limit and (not self.last_dt_reset or ts >= self.last_dt_reset):
                    ts_str = ts.strftime("%H:%M:%S")
                    new_player_data[tgt]["logs"].append({"text": f"[{ts_str}] Taken {e['damage']:.0f} from {src}", "timestamp": ts})
                
                # Track taken for Damage Meter
                if id(e) in active_ids and (not self.last_dm_reset or ts >= self.last_dm_reset):
                    new_player_data[tgt]["dm_taken"] = new_player_data[tgt].get("dm_taken", 0) + e["damage"]
                    if e.get("is_mitigated"):
                        new_player_data[tgt]["dm_avoided"] = new_player_data[tgt].get("dm_avoided", 0) + 1
                    elif e["damage"] > 0:
                        new_player_data[tgt]["dm_taken_hits"] = new_player_data[tgt].get("dm_taken_hits", 0) + 1

        self.player_data = new_player_data
        self.loot_data = new_loot_data
        self.inventory_full = new_inventory_full

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
                    local_dmg = self.leaderboard_data.get("damage", {}).copy()
                    local_heal = self.leaderboard_data.get("healing", {}).copy()
                    local_loot = {}
                    for p, items in self.loot_data.items():
                        # loot_data is {player: [{"item": name, "timestamp": ts}, ...]}
                        # For sync we might just want to send counts or some representation
                        # Let's send the list of looted items
                        local_loot[p] = items

                    if "You" in local_dmg:
                        local_dmg[self.char_name.get()] = local_dmg.pop("You")
                    if "You" in local_heal:
                        local_heal[self.char_name.get()] = local_heal.pop("You")
                    if "You" in local_loot:
                        local_loot[self.char_name.get()] = local_loot.pop("You")

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
                pass # Silent fail for now to avoid spamming
            
            time.sleep(10) # Sync every 10 seconds

    def on_exit(self):
        self.running = False
        if self.engine_process: 
            self.engine_process.terminate()
        self.save_config()
        self.root.destroy()

    def save_config(self):
        if "General" not in self.config: self.config["General"] = {}
        self.config["General"].update({
            "log_path": self.file_path_var.get(),
            "transparency": str(self.target_alpha),
            "width": str(self.root.winfo_width()),
            "height": str(self.root.winfo_height()),
            "x": str(self.root.winfo_x()),
            "y": str(self.root.winfo_y()),
            "disable_warnings": str(self.disable_warnings.get())
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

    def toggle_menu(self):
        self.options_win.show()

    def change_log_path(self):
        p = filedialog.askopenfilename()
        if p: 
            self.file_path_var.set(p)
            if not self.char_name.get():
                self.char_name.set(extract_character_id(p))
            self.save_config()
            self.start_c_engine(p)
            self.analyze_log(manual=True)

    def reset_damage_meter_manual(self):
        self.last_dm_reset = datetime.now()
        # Reprocess current events to update UI immediately
        self.process_events_for_ui(self.all_events)
        self.refresh_ui_only()

    def reset_leaderboard_manual(self):
        self.last_lb_reset = datetime.now()
        self.process_events_for_ui(self.all_events)
        self.refresh_ui_only()

    def reset_skimmers_manual(self):
        self.last_sk_reset = datetime.now()
        self.inventory_full = False
        self.process_events_for_ui(self.all_events)
        self.refresh_ui_only()

    def reset_details_manual(self):
        self.last_dt_reset = datetime.now()
        self.process_events_for_ui(self.all_events)
        self.refresh_ui_only()

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
