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
from utils import is_window_minimized, apply_snapping
from parser_engine import parse_combat_log, calculate_dps
from ui_base import ThemedMessagebox

# Popout Windows
from windows.skimmers import SkimmersWindow
from windows.damage_meter import DamageMeterWindow
from windows.leaderboard import LeaderboardWindow
from windows.details import DetailsWindow

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

        # Windows
        self.skimmers_win = SkimmersWindow(self)
        self.damage_meter_win = DamageMeterWindow(self)
        self.leaderboard_win = LeaderboardWindow(self)
        self.details_win = DetailsWindow(self)
        
        # Backward compatibility aliases
        self.skimmers_window = None 
        self.damage_meter_window = None
        self.leaderboard_window = None
        self.details_window = None
        self.options_window = None

        self.actual_app_start_time = datetime.now()
        self.last_reset_time = self.actual_app_start_time
        self.running = True
        self.engine_process = None
        
        threading.Thread(target=self.start_pipe_listener, daemon=True).start()
        
        self.root.after(300, self.initial_show)
        self.root.after(800, self.start_window_tracking)
        self.root.after(1000, self.start_show)
        if initial_log_path:
            self.root.after(1200, lambda: self.start_c_engine(initial_log_path))

        self.player_data = {}
        self.leaderboard_data = {}
        self.loot_data = {}
        self.all_events = []
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

    def initial_show(self):
        try:
            self.root.withdraw()
            hwnd = self.root.winfo_id()
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_HIDEWINDOW)
        except: pass

    def start_c_engine(self, log_path):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "log_engine.exe", "/T"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if self.engine_process: self.engine_process.terminate()
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            engine_exe = os.path.join(base_path, "log_engine.exe")
            if os.path.exists(engine_exe):
                self.engine_process = subprocess.Popen([engine_exe, log_path], creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

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
        for w in [self.skimmers_win, self.damage_meter_win, self.leaderboard_win, self.details_win]:
            if w.window and w.window.winfo_exists(): managed.append(w.window)
        if self.options_window and self.options_window.winfo_exists(): managed.append(self.options_window)
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
        self.root_border = tk.Frame(self.root, bg=BORDER_COLOR, padx=1, pady=1)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        outer = tk.Frame(self.root_border, bg=WINDOW_BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        outer.bind("<Button-1>", self.click_window); outer.bind("<B1-Motion>", self.drag_window)

        header = tk.Frame(outer, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header.pack(fill=tk.BOTH, expand=True)
        title_bar = tk.Frame(header, bg=PANEL_DARK, height=25); title_bar.pack(fill=tk.X)
        
        tk.Label(title_bar, text=" ✕ ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2").pack(side=tk.RIGHT).bind("<Button-1>", lambda e: self.on_exit())
        tk.Label(title_bar, text=" SETTINGS ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2").pack(side=tk.RIGHT).bind("<Button-1>", lambda e: self.toggle_menu())
        self.ontop_btn = tk.Label(title_bar, text="ONTOP: OFF", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2"); self.ontop_btn.pack(side=tk.LEFT)
        self.ontop_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())

        nav = tk.Frame(header, bg=PANEL_DARK); nav.pack(fill=tk.X, padx=10, pady=(0, 5))
        def btn(t, cmd): 
            l = tk.Label(nav, text=t, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2", padx=5)
            l.pack(side=tk.LEFT); l.bind("<Button-1>", lambda e: cmd())
            return l
        self.lbl_dmg = btn("DMG METER", self.damage_meter_win.show)
        self.lbl_det = btn("DETAILS", self.details_win.show)
        self.lbl_skm = btn("SKIMMERS", self.skimmers_win.show)
        self.lbl_ldb = btn("LEADERBOARD", self.leaderboard_win.show)
        self.lbl_loot = btn("LOOT", self.skimmers_win.show)
        self.lbl_version = tk.Label(nav, text="1.0", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack(side=tk.RIGHT)

        stats = tk.Frame(outer, bg=WINDOW_BG); stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.lbl_damage_val = self.create_stat_box(stats, "DAMAGE", "0").value_label
        self.lbl_dps_val = self.create_stat_box(stats, "DPS", "0.00").value_label
        self.lbl_time_val = self.create_stat_box(stats, "DURATION", "0s").value_label

    def create_stat_box(self, parent, title, value):
        f = tk.Frame(parent, bg=BORDER_COLOR, padx=1, pady=1); f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        b = tk.Frame(f, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_HIGHLIGHT); b.pack(fill=tk.BOTH, expand=True)
        tk.Label(b, text=title, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(anchor="w", padx=5)
        v = tk.Label(b, text=value, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=self.font_stats_obj); v.pack(anchor="w", padx=5)
        f.value_label = v; return f

    def start_pipe_listener(self):
        pipe_path = r'\\.\pipe\LivyLogsPipe'
        while self.running:
            if not kernel32.WaitNamedPipeW(pipe_path, 1000): time.sleep(1); continue
            h = kernel32.CreateFileW(pipe_path, 0x80000000, 0, None, 3, 0x80, None)
            if h == -1: time.sleep(1); continue
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
                            except: pass
                else: break
            kernel32.CloseHandle(h)

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
            self.root.after(0, self.refresh_ui_only); self.last_ui_update_time = now

    def analyze_log(self, manual=False):
        if manual: self.all_events = []; self.last_read_offset = -1; self.app_start_time = None; self.last_combat_time = 0; self.player_data = {}; self.loot_data = {}; self.leaderboard_data = {}
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path): return
        
        try:
            st = os.stat(path); mtime, size = st.st_mtime, st.st_size
            if not manual and hasattr(self, 'last_log_mtime') and mtime <= self.last_log_mtime and size <= self.last_log_size:
                if time.time() - getattr(self, 'last_forced_read_time', 0) < 0.2: self.refresh_ui_only(); return
            self.last_log_mtime, self.last_log_size = mtime, size
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
        self.refresh_ui_only()

    def start_ticker_loop(self):
        if self.running:
            self.refresh_ui_only(); self.root.after(100, self.start_ticker_loop)

    def refresh_ui_only(self):
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
            
            dur_color = "cyan" if is_paused else TEXT_PRIMARY
            if dur > 0 and self.last_combat_time == 0: dur_color = "cyan" if self.pulse_state else "#AAAAAA"

            self.lbl_damage_val.config(text=f"{dmg_dealt:.0f}")
            self.lbl_dps_val.config(text=f"{dps:.2f}")
            self.lbl_time_val.config(text=f"{dur:.0f}s", fg=dur_color)

    def process_events_for_ui(self, all_events, manual=False):
        now_dt = datetime.now()
        sk_limit = now_dt - timedelta(minutes=self.time_window_skimmers)
        dt_limit = now_dt - timedelta(minutes=self.time_window_details)
        
        self.player_data = {}; self.loot_data = {}; self.inventory_full = False
        active_ids = set(id(e) for e in all_events if self.app_start_time and e["timestamp"] and e["timestamp"] >= self.app_start_time)

        for e in all_events:
            src = e["source"].capitalize(); src = "You" if src.lower() == "you" else src
            is_npc = " (" in src or src.lower().startswith(("a ", "an ", "your target"))
            
            if e["type"] == "loot":
                if e["timestamp"] and e["timestamp"] >= sk_limit:
                    if src not in self.loot_data: self.loot_data[src] = []
                    self.loot_data[src].append({"item": e["item"], "target": e["target"], "timestamp": e["timestamp"]})
                continue
            
            if e["type"] == "inventory_full":
                if e["timestamp"] and e["timestamp"] >= sk_limit: self.inventory_full = True; continue

            if e["timestamp"] and e["timestamp"] < dt_limit and id(e) not in active_ids: continue
            
            if not is_npc:
                if src not in self.player_data: self.player_data[src] = {"damage": 0, "healing": 0, "logs": [], "died": False}
                if id(e) in active_ids:
                    self.player_data[src]["damage"] += e["damage"]; self.player_data[src]["healing"] += e["healing"]
            
            tgt = e["target"].capitalize(); tgt = "You" if tgt.lower() == "you" else tgt
            if e["damage"] > 0 and not (" (" in tgt or tgt.lower().startswith(("a ", "an "))):
                if tgt not in self.player_data: self.player_data[tgt] = {"damage": 0, "healing": 0, "logs": [], "died": False}
                ts_str = e["timestamp"].strftime("%H:%M:%S") if e["timestamp"] else "??:??:??"
                self.player_data[tgt]["logs"].append({"text": f"[{ts_str}] Taken {e['damage']:.0f} from {src}", "timestamp": e["timestamp"]})

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.ontop_btn.config(text="ONTOP: ON" if self.always_on_top else "ONTOP: OFF", fg=ACCENT_BLUE if self.always_on_top else TEXT_SECONDARY)

    def on_exit(self):
        self.running = False
        if self.engine_process: 
            self.engine_process.terminate()
        self.save_config()
        self.root.destroy()

    def save_config(self):
        if "General" not in self.config: self.config["General"] = {}
        self.config["General"].update({"log_path": self.file_path_var.get(), "transparency": str(self.target_alpha), "width": str(self.root.winfo_width()), "height": str(self.root.winfo_height()), "x": str(self.root.winfo_x()), "y": str(self.root.winfo_y())})
        with open("settings.ini", "w") as f: self.config.write(f)

    def drag_window(self, event):
        x, y = apply_snapping(self.root, self.root.winfo_pointerx() - self._offsetx, self.root.winfo_pointery() - self._offsety)
        self.root.geometry(f"+{x}+{y}")

    def click_window(self, event):
        self._offsetx = event.x_root - self.root.winfo_x(); self._offsety = event.y_root - self.root.winfo_y()

    def toggle_menu(self):
        # Mini-settings implementation omitted for brevity but placeholder for functional parity
        pass

    def change_log_path(self):
        p = filedialog.askopenfilename()
        if p: 
            self.file_path_var.set(p)
            self.save_config()
            self.start_c_engine(p)
            self.analyze_log(manual=True)

    # Required for popout window resizing
    def init_resize_popout(self, e, w, dw, dh): self._rs_x = e.x_root; self._rs_y = e.y_root; self._rs_w = w.winfo_width(); self._rs_h = w.winfo_height()
    def do_resize_popout(self, e, w, dw, dh): w.geometry(f"{max(dw//3, self._rs_w + e.x_root - self._rs_x)}x{max(dh//3, self._rs_h + e.y_root - self._rs_y)}")
    def save_size(self, e): self.save_config()
    
    # Required for main window resizing
    def init_resize(self, e): self._rs_x = e.x_root; self._rs_y = e.y_root; self._rs_w = self.root.winfo_width(); self._rs_h = self.root.winfo_height()
    def do_resize(self, e): 
        nw, nh = max(MIN_WIDTH, self._rs_w + e.x_root - self._rs_x), max(MIN_HEIGHT, self._rs_h + e.y_root - self._rs_y)
        self.root.geometry(f"{nw}x{nh}")
