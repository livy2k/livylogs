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
        self.target_alpha = initial_alpha
        self.current_alpha = initial_alpha
        self.root.attributes("-alpha", initial_alpha)
        self.root.overrideredirect(True)
        
        self.file_path_var = tk.StringVar(value=initial_log_path)
        self.disable_warnings = tk.BooleanVar(value=self.config.getboolean("General", "disable_warnings", fallback=False))
        self.show_class_colors = tk.BooleanVar(value=self.config.getboolean("General", "show_class_colors", fallback=True))
        self.char_name = tk.StringVar(value=self.config.get("General", "character_name", fallback=""))
        if not self.char_name.get() and initial_log_path:
            self.char_name.set(extract_character_id(initial_log_path))
        self.api_url = tk.StringVar(value=self.config.get("General", "api_url", fallback="https://livy.logs/sync"))
        self.enable_sync = tk.BooleanVar(value=self.config.getboolean("General", "enable_sync", fallback=False))

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
            print(f"DEBUG: Error loading bosses.txt: {e}")
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
            print(f"DEBUG: Error loading filters.txt: {e}")
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
            print(f"DEBUG: Error loading class configs: {e}")
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
        # Since we want the main window to stay visible always, we restore
        # this loop to ensure it stays deiconified if it's not in the tray.
        if self.root.state() == "withdrawn" and not getattr(self, "_minimized_to_tray", False):
            self.start_show()
        
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
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.1)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.root.after(20, self.fade_in)

    def start_hide(self, minimize=True):
        self.fade_out(minimize=minimize)

    def fade_out(self, minimize=True):
        if self.current_alpha > 0:
            self.current_alpha = max(0, self.current_alpha - 0.1)
            for win in self._get_managed_windows(): win.attributes("-alpha", self.current_alpha)
            self.root.after(20, lambda: self.fade_out(minimize=minimize))
        else:
            if minimize:
                for win in self._get_managed_windows():
                    if win.state() != "withdrawn":
                        win.withdraw()

    def start_c_engine(self, log_path):
        # C Engine now starts Python
        pass

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
        exit_btn.bind("<Button-1>", lambda e: self.start_hide(minimize=True))
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
        self.lbl_version = tk.Label(nav, text="1.0", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack(side=tk.RIGHT)

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
        event_type = event.get("type")
        
        if event_type == "stats":
            name = event.get("name")
            if not name: return
            if name not in self.player_data:
                self.player_data[name] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "targets": {}, "aoe_hits": 0, "dm_hits": 0, "dm_misses": 0, "dm_taken": 0, "dm_taken_hits": 0, "dm_avoided": 0}
            
            p = self.player_data[name]
            p["damage"] = event.get("damage", 0)
            p["healing"] = event.get("healing", 0)
            p["dm_taken"] = event.get("taken", 0)
            p["dm_hits"] = event.get("hits", 0)
            p["dm_misses"] = event.get("misses", 0)
            p["dm_avoided"] = event.get("avoided", 0)
            p["aoe_hits"] = event.get("aoe", 0)
            p["lb_loot"] = event.get("loot", 0)
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
            self.app_start_time = None; self.last_log_sync_time = None; self.leaderboard_data = {}; 
            # We don't want to completely clear player_data here because Leaderboard might need it
            # But we reset the DM relevant stats for 'You' and others
            for p in self.player_data:
                self.player_data[p]["dm_damage"] = 0
                self.player_data[p]["dm_healing"] = 0
                if "dm_taken" in self.player_data[p]: self.player_data[p]["dm_taken"] = 0
            
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
        now_ts = time.time()
        if now_ts - self.last_pulse_time > 0.3:
            self.pulse_state = not self.pulse_state; self.last_pulse_time = now_ts

        # Damage meter is highest priority for real-time feel
        self.damage_meter_win.refresh(force=force)

        # Other windows are lower priority
        if force or (now_ts - getattr(self, 'last_heavy_refresh', 0) >= 0.2):
            self.leaderboard_win.refresh(force=force)
            self.skimmers_win.refresh(force=force)
            self.details_win.refresh(force=force)
            self.last_heavy_refresh = now_ts
        
        # Options window doesn't need to refresh every tick, only when forced
        if force:
            self.options_win.refresh(force=True)

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
                pass # Silent fail for now to avoid spamming
            
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
            print(f"DEBUG: Failed to setup tray icon: {e}")


    def on_exit(self, icon=None, item=None):
        self.running = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        if self.engine_process: 
            self.engine_process.terminate()
        self.save_config()
        self.root.after(0, self.root.destroy)

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
            if not accepted: return
            
            self.file_path_var.set(p)
            detected_name = extract_character_id(p)
            
            def apply_settings(new_name):
                if new_name:
                    self.char_name.set(new_name)
                elif not self.char_name.get():
                    self.char_name.set(detected_name)
                
                self.save_config()
                self.start_c_engine(p)
                self.options_win.refresh(force=True)

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
