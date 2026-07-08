# VERSION: 1.0 - FINALIZED FOR RELEASE
import re
import tkinter as tk
import os
import sys
from tkinter import font as tkfont
from tkinter import ttk
from tkinter import messagebox, filedialog
from configparser import ConfigParser
from pathlib import Path
from datetime import datetime, timedelta
import ctypes
import time
from ctypes import wintypes
import json
import threading

# Win32 Constants
SW_HIDE = 0
SW_SHOW = 5
SW_RESTORE = 9
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOPMOST = 0x00000008

winmm = ctypes.WinDLL('winmm')

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# Win32 Constants for SetWindowPos
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080

# Define WINDOWPLACEMENT if missing from wintypes
if not hasattr(wintypes, "WINDOWPLACEMENT"):
    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]
    wintypes.WINDOWPLACEMENT = WINDOWPLACEMENT

def is_window_minimized(hwnd):
    """Checks if a window is minimized using Win32 API."""
    placement = wintypes.WINDOWPLACEMENT()
    placement.length = ctypes.sizeof(wintypes.WINDOWPLACEMENT)
    if user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
        return placement.showCmd == 2 # SW_SHOWMINIMIZED
    return False

MIN_WIDTH = 450
MIN_HEIGHT = 60


WINDOW_BG = "#0a0b0d"
PANEL_BG = "#14171c"
PANEL_DARK = "#0d0f12"
ACCENT_BLUE = "#00a2ff"
ACCENT_GLOW = "#005a8e"
BORDER_COLOR = "#2a2e35"
BORDER_HIGHLIGHT = "#3f444d"
TEXT_PRIMARY = "#e1e4e8"
TEXT_SECONDARY = "#8b949e"
TEXT_ACCENT = "#00a2ff"
BUTTON_BG = "#1f242d"
BUTTON_HOVER = "#2a2e35"
ENTRY_BG = "#090a0c"
SNAP_THRESHOLD = 20

class ThemedMessagebox(tk.Toplevel):
    def __init__(self, parent, title, message, icon="info", on_close=None, extra_button_text=None, extra_button_callback=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=WINDOW_BG)
        self.attributes("-alpha", 0.0)
        self.overrideredirect(True)
        self.resizable(False, False)
        self.on_close_callback = on_close

        self.current_alpha = 0.0
        self.target_alpha = 1.0
        self.fade_speed = 0.1
        self.fade_after_id = None
        self.target_hwnd = None

        # Fixed dimensions
        width = 450
        height = 180
        
        # Screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Absolute center calculation
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Ensure it doesn't go off screen
        x = max(0, x)
        y = max(0, y)
        
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Border
        border = tk.Frame(self, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Title Bar
        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        
        title_lbl = tk.Label(title_bar, text=title.upper(), bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold"))
        title_lbl.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.close_and_callback())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        # Content
        content = tk.Frame(inner, bg=WINDOW_BG, padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        icon_color = ACCENT_BLUE if icon == "info" else "#ff4444"
        icon_text = "ℹ" if icon == "info" else "⚠"
        
        icon_lbl = tk.Label(content, text=icon_text, bg=WINDOW_BG, fg=icon_color, font=("Segoe UI", 24))
        icon_lbl.pack(side=tk.LEFT, padx=(0, 20))
        
        msg_label = tk.Label(content, text=message, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10), justify=tk.LEFT, wraplength=400)
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button Area
        btn_area = tk.Frame(inner, bg=PANEL_DARK, height=40)
        btn_area.pack(fill=tk.X)
        
        ok_btn = tk.Frame(btn_area, bg=BUTTON_BG, padx=15, pady=5, cursor="hand2")
        ok_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        ok_lbl = tk.Label(ok_btn, text="OK", bg=BUTTON_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"))
        ok_lbl.pack()
        
        ok_btn.bind("<Button-1>", lambda e: self.close_and_callback())
        ok_lbl.bind("<Button-1>", lambda e: self.close_and_callback())
        ok_btn.bind("<Enter>", lambda e: [ok_btn.config(bg=BUTTON_HOVER), ok_lbl.config(bg=BUTTON_HOVER)])
        ok_btn.bind("<Leave>", lambda e: [ok_btn.config(bg=BUTTON_BG), ok_lbl.config(bg=BUTTON_BG)])

        if extra_button_text and extra_button_callback:
            def on_extra_click(e):
                self.destroy() # Close notice
                extra_button_callback() # Run callback
            
            extra_btn = tk.Frame(btn_area, bg=BUTTON_BG, padx=15, pady=5, cursor="hand2")
            extra_btn.pack(side=tk.RIGHT, padx=5, pady=5)
            extra_lbl = tk.Label(extra_btn, text=extra_button_text.upper(), bg=BUTTON_BG, fg=TEXT_ACCENT, font=("Segoe UI", 9, "bold"))
            extra_lbl.pack()
            
            extra_btn.bind("<Button-1>", on_extra_click)
            extra_lbl.bind("<Button-1>", on_extra_click)
            extra_btn.bind("<Enter>", lambda e: [extra_btn.config(bg=BUTTON_HOVER), extra_lbl.config(fg=TEXT_PRIMARY)])
            extra_btn.bind("<Leave>", lambda e: [extra_btn.config(bg=BUTTON_BG), extra_lbl.config(fg=TEXT_ACCENT)])

        # Make it draggable
        title_bar.bind("<Button-1>", self._click_window)
        title_bar.bind("<B1-Motion>", self._drag_window)
        inner.bind("<Button-1>", self._click_window)
        inner.bind("<B1-Motion>", self._drag_window)
        self._offsetx = 0
        self._offsety = 0

        # Start tracking and fade in
        self.check_target_window()

    def find_target_window(self):
        """Attempts to find the Star Wars Galaxies window."""
        target_hwnd = [None]
        def enum_windows_callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            if "Star Wars Galaxies" in title:
                target_hwnd[0] = hwnd
                return False
            return True
        
        user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_windows_callback), 0)
        return target_hwnd[0]

    def is_foreground_ours(self):
        """Checks if the current foreground window belongs to this application or the game."""
        foreground_hwnd = user32.GetForegroundWindow()
        if not foreground_hwnd:
            return False
            
        # 1. Check if it's our application (matches our Process ID)
        foreground_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(foreground_hwnd, ctypes.byref(foreground_pid))
        our_pid = kernel32.GetCurrentProcessId()
        
        if foreground_pid.value == our_pid:
            return True
            
        # 2. Check if it's the game or a child/parent/sibling of the game
        if self.target_hwnd and user32.IsWindow(self.target_hwnd):
            if foreground_hwnd == self.target_hwnd:
                return True
            
            # Does the foreground window belong to the same process as the game?
            target_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(self.target_hwnd, ctypes.byref(target_pid))
            if foreground_pid.value == target_pid.value:
                return True

            # Check descendants
            temp_hwnd = foreground_hwnd
            while temp_hwnd:
                if temp_hwnd == self.target_hwnd:
                    return True
                temp_hwnd = user32.GetParent(temp_hwnd)
                
            # Check ancestors
            temp_hwnd = self.target_hwnd
            while temp_hwnd:
                if temp_hwnd == foreground_hwnd:
                    return True
                temp_hwnd = user32.GetParent(temp_hwnd)

        return False

    def check_target_window(self):
        """Periodically checks game window state and updates visibility."""
        try:
            if not self.winfo_exists():
                return
            
            # Use parent's target_hwnd if available
            parent_app = None
            if self.master and hasattr(self.master, "target_hwnd"):
                parent_app = self.master
            elif self.master and hasattr(self.master, "master") and hasattr(self.master.master, "target_hwnd"):
                parent_app = self.master.master

            if parent_app:
                # Synchronize with parent's state
                should_show = False
                if hasattr(parent_app, "root"):
                    should_show = (parent_app.root.state() != "withdrawn" and parent_app.current_alpha > 0)
                
                if should_show:
                    # Cancel any pending hide
                    if hasattr(self, '_hide_grace_after_id') and self._hide_grace_after_id:
                        self.after_cancel(self._hide_grace_after_id)
                        self._hide_grace_after_id = None
                        
                    if self.state() == "withdrawn":
                        self.start_show()
                    
                    # Sync alpha
                    if hasattr(parent_app, "current_alpha"):
                        self.attributes("-alpha", parent_app.current_alpha)
                    
                    # Sync topmost
                    is_topmost = getattr(parent_app, "_last_topmost_state", False)
                    if not hasattr(self, "_last_topmost_state") or self._last_topmost_state != is_topmost:
                        self.attributes("-topmost", is_topmost)
                        hwnd = self.winfo_id()
                        user32.SetWindowPos(hwnd, HWND_TOPMOST if is_topmost else HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                        self._last_topmost_state = is_topmost
                else:
                    if not hasattr(self, '_hide_grace_after_id') or self._hide_grace_after_id is None:
                        self._hide_grace_after_id = self.after(1000, self._perform_graceful_hide)
            else:
                # Fallback to independent behavior if no parent found
                is_valid_foreground = self.is_foreground_ours()
                should_show = is_valid_foreground
                if should_show:
                    self.start_show()
                else:
                    self.start_hide()

        except:
            pass
        
        self.after(250, self.check_target_window)

    def _perform_graceful_hide(self):
        """Actually performs the hide after the grace period if still out of focus."""
        self._hide_grace_after_id = None
        try:
            # Re-check focus and always_on_top
            is_valid_foreground = self.is_foreground_ours()
            always_on_top = False
            if self.master and hasattr(self.master, "always_on_top"):
                always_on_top = self.master.always_on_top
            elif self.master and hasattr(self.master, "master") and hasattr(self.master.master, "always_on_top"):
                always_on_top = self.master.master.always_on_top

            if not is_valid_foreground and not always_on_top:
                if self.state() != "withdrawn" and self.current_alpha > 0:
                    self.start_hide()
        except:
            pass

    def start_show(self):
        """Gradually shows the window."""
        if self.state() == "withdrawn":
            self.current_alpha = 0.0
            self.attributes("-alpha", 0.0)
            self.deiconify()
        
        if self.current_alpha < self.target_alpha:
            if hasattr(self, "fade_after_id") and self.fade_after_id:
                self.after_cancel(self.fade_after_id)
            self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.1)
            self.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.after(20, self.fade_in)
        else:
            self.fade_after_id = None

    def start_hide(self):
        """Gradually hides the window."""
        if self.state() == "withdrawn":
            return
        if self.current_alpha > 0.0:
            if hasattr(self, "fade_after_id") and self.fade_after_id:
                self.after_cancel(self.fade_after_id)
            self.fade_out()

    def fade_out(self):
        if self.current_alpha > 0.0:
            self.current_alpha = max(0.0, self.current_alpha - 0.1)
            self.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.after(20, self.fade_out)
        else:
            self.withdraw()
            self.fade_after_id = None

    def close_and_callback(self):
        """Closes the window and triggers the callback if set."""
        callback = self.on_close_callback
        parent = self.master
        self.destroy()
        if callback:
            callback()
        
        # We only want to destroy the parent if it's NOT the main application root
        # and it is a standalone Tk instance used for simple notices.
        # CombatLogApp uses a 'root' which is a tk.Tk instance.
        # Check if the parent is a tk.Tk instance but NOT the one hosting our main app.
        if parent and hasattr(parent, "destroy") and parent.__class__.__name__ == "Tk":
            # If the parent has a CombatLogApp instance associated with it, don't destroy it!
            # We can check for known attributes of CombatLogApp on the root.
            is_main_root = False
            try:
                # CombatLogApp uses a 'root' which is a tk.Tk instance.
                # If we are inside the main app, parent.winfo_children() will contain
                # the CombatLogApp instance (which is a tk.Frame or similar).
                children = parent.winfo_children()
                for child in children:
                    if child.__class__.__name__ == "CombatLogApp":
                        is_main_root = True
                        break
            except:
                pass
            
            if not is_main_root:
                try:
                    parent.destroy()
                except:
                    pass

    def _click_window(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def _drag_window(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f"+{x}+{y}")

    @staticmethod
    def showinfo(parent, title, message, on_close=None, extra_button_text=None, extra_button_callback=None):
        if parent is None:
            temp_root = tk.Tk()
            temp_root.withdraw()
            box = ThemedMessagebox(temp_root, title, message, icon="info", on_close=on_close, extra_button_text=extra_button_text, extra_button_callback=extra_button_callback)
            temp_root.mainloop()
            return box
        return ThemedMessagebox(parent, title, message, icon="info", on_close=on_close, extra_button_text=extra_button_text, extra_button_callback=extra_button_callback)

    @staticmethod
    def showerror(parent, title, message, on_close=None):
        return ThemedMessagebox(parent, title, message, icon="error", on_close=on_close)

# Default sizes for pop-out windows
DETAILS_DEFAULT_WIDTH = 400
DETAILS_DEFAULT_HEIGHT = 500
LEADERBOARD_DEFAULT_WIDTH = 300
LEADERBOARD_DEFAULT_HEIGHT = 400
SKIMMERS_DEFAULT_WIDTH = 350
SKIMMERS_DEFAULT_HEIGHT = 400
DAMAGE_METER_DEFAULT_WIDTH = 300
DAMAGE_METER_DEFAULT_HEIGHT = 220


def parse_combat_log(file_path, start_offset=0):
    """
    Parse a combat log and return damage events.

    This parser looks for lines that appear to describe damage,
    attempts to extract a timestamp and the damage amount.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Log file does not exist: {file_path}")

    if not path.is_file():
        raise ValueError(f"Selected path is not a file: {file_path}")

    # Check if file is empty or too small (logging might be off)
    file_size = path.stat().st_size
    if file_size == 0:
        return [], 0
    
            # If start_offset is -1, read the last 256KB for history
    read_offset = start_offset
    if read_offset == -1:
        if file_size > 256 * 1024:
            read_offset = file_size - 256 * 1024
        else:
            read_offset = 0

    # If start_offset is 0 but file is very large, jump to the last 256KB

    events = []

    # Regex for common combat log timestamp formats: [YYYY-MM-DD HH:MM:SS] or HH:MM:SS
    timestamp_pattern = re.compile(r"\[?(\d{4}-\d{2}-\d{2} )?(\d{2}:\d{2}:\d{2})\]?")
    # Regex for damage dealt: looks for lines where the player deals damage
    # Updated to capture player names and distinguish damage/healing
    # Example: [2024-01-01 12:00:00] You deal 100 damage to a stormtrooper.
    # Example: [2024-01-01 12:00:00] PlayerName deals 150 damage to a target.
    # Example: [2024-01-01 12:00:00] You heal PlayerName for 50 points.
    
    # Regex for SWG style logs:
    # Example: [Spatial]  22:46:16 DCLXVI uses Advanced Strafe on a Gundark for 3223 points of damage!
    # Example: [Spatial]  22:46:20 a Gundark attacks Shorts for 475 points of damage!
    # Example: You heal PlayerName for 50 points of health.
    # Group 1: Name, Group 2: Action, Group 3: Ability, Group 4: Target, Group 5: Amount, Group 6: Unit
    swg_pattern = re.compile(
        r"(?:\[\w+\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>you|.+?)\s+(?P<action>uses|use|attacks|attack|deals|deal|heals|heal|hits|hit)\b\s+(?:(?P<ability>.+?)\s+(?:on|to|for)\s+)?(?P<target>.+?)\s+for\s+(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>damage|dmg|points|health)?",
        re.IGNORECASE
    )
    
    # Pre-check keywords for SWG pattern to avoid catastrophic backtracking on non-matching lines
    swg_keywords = ["uses", "use", "attacks", "attack", "deals", "deal", "heals", "heal", "hits", "hit"]
    dealt_keywords = ["deal", "hit", "hits"]
    taken_keywords = ["deals", "hits", "hit"]
    generic_keywords = ["damage", "dmg", "hit", "hits", "points"]
    
    # Pre-compiled activity keywords for fast filtering
    pvp_kws = ["has bested"]
    msg_kws = ["says", "shouts", "whispers", "tells", "emotes", "performs", "is", "has", "does", "goes", "starts", "stops", "completes"]
    act_kws = ["is", "has", "does", "goes", "starts", "stops", "completes", "stands", "kneels", "performs", "sits", "says", "shouts", "whispers", "tells", "emotes", "tosses", "nods", "waves", "smiles", "laughs", "cheers", "misses", "evade", "dodge", "parr", "block", "counterattack", "attack", "use", "hit"]
    death_kws = ["has died"]
    loot_kws = ["looted", "you cannot loot that item"]

    # Existing fallback/specific patterns
    damage_dealt_pattern = re.compile(r"you (?:deal|hit|hits).+?(\d+(?:\.\d+)?)\s*(?:damage|dmg|points)", re.IGNORECASE)
    damage_taken_pattern = re.compile(r"(?P<attacker>.+?) (?:deals|hits|hit) you.+?(?P<amount>\d+(?:\.\d+)?)\s*(?:damage|dmg|points)", re.IGNORECASE)
    damage_generic_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:damage|dmg|hit|hits|points)", re.IGNORECASE)
    prevented_pattern = re.compile(r"armor prevented (?P<amount>\d+(?:\.\d+)?)\s*(?:damage|dmg|points)", re.IGNORECASE)

    # Comprehensive regex for player names in non-combat activity
    activity_patterns = [
        # 1. PvP Broadcasts (e.g., Winner has bested Loser in GCW combat.)
        (re.compile(r'(?:\[PvPBroadcasts\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?\[PvPBroadcasts\]\s+:\s+(?P<winner>.+?)\s+has bested\s+(?P<loser>.+?)\s+in GCW combat\.', re.IGNORECASE), pvp_kws),
        # 2. Quoted text followed by name and action (e.g., "Hello!", PlayerName says.)
        (re.compile(r'".+",\s+(?P<name>.+?)\s+(?P<action>says|shouts|whispers|tells|emotes|performs|is|has|does|goes|starts|stops|completes)\b', re.IGNORECASE), msg_kws),
        # 2. Standard Name Action (e.g., PlayerName stands up. / PlayerName is dancing.)
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>you|.+?)\s+(?P<action>is|has|does|goes|starts|stops|completes|stands|kneels|performs|sits|says|shouts|whispers|tells|emotes|tosses|nods|waves|smiles|laughs|cheers|misses|evades|evaded|dodges|parries|blocks|counterattacks|attacks|uses|hit|hits)\b', re.IGNORECASE), act_kws),
        # 3. Death events (e.g., [GROUP] Name has died.)
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?:\[GROUP\]\s+)?(?P<name>.+?) has died\.', re.IGNORECASE), death_kws),
        # 4. Looting events (e.g., [GROUP] Name looted Item from Target.)
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?:\[GROUP\]\s+)?(?P<name>.+?) looted (?P<item>.+?) from (?P<target>.+?)\.', re.IGNORECASE), loot_kws),
        # 5. Inventory Full (e.g., You cannot loot that item because your inventory is full.)
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?You cannot loot that item because your inventory is full\.', re.IGNORECASE), loot_kws)
    ]

    with path.open("r", encoding="utf-8", errors="replace") as log_file:
        if read_offset > 0:
            log_file.seek(read_offset)
            # If we jumped into the middle of the file, skip the first partial line
            log_file.readline()
        
        current_offset = log_file.tell()
        line_number = 0
        last_taken_event = None
        while True:
            line = log_file.readline()
            if not line:
                break
            
            line_number += 1
            original_line = line.strip()
            if not original_line:
                current_offset = log_file.tell()
                continue
            
            # Skip GroupChat and Instant Messages lines early
            if "[GroupChat]" in original_line or "[Instant Messages]" in original_line:
                current_offset = log_file.tell()
                continue

            # Optimization: Skip non-relevant lines immediately
            lower_line = original_line.lower()
            
            # Immediate discard for known non-combat system messages
            if any(msg in lower_line for msg in ["there is no person by the name", "you enhance your", "is not online", "is already on your ignore list", "has been added to your", "you are too full to", "your focus your thoughts on", "%tu", "target was invalid", "already focusing on defense", "out of range", "no damage to heal", "terminal", "lost sight", "you lost sight of your target", "you must be within range", "out of range for this action", "that target is out of range", "generating vehicle", "cannot gain any more of", "faction standing", "awarded", "too tired to", "points of standing", "two-hand area attack 3", "target for two-hand area attack 3", "[galaxychat]", "[groupchat]", "[guildchat]", "[citychat]", "[publicchat]", "[instant messages]", "harvested", "completely looted", "no longer stunned", "stand", "kneel", "fall down", "music", "dancing", "playing", "burst run", "run as hard as you can", "invites you to join", "joined the group", "squad leader"]):
                current_offset = log_file.tell()
                continue

            relevant = False
            # Combined list of all primary keywords for immediate discard
            for kw in ["deal", "hit", "heal", "attack", "use", "die", "loot", "say", "shout", "whisper", "tell", "emote", "is ", "stand", "kneel", "perform", "miss", "evade", "dodge", "parr", "block", "counter", "bested", "prevented"]:
                if kw in lower_line:
                    relevant = True
                    break
            
            if not relevant:
                current_offset = log_file.tell()
                continue

            # Extract timestamp
            ts_match = timestamp_pattern.search(original_line)
            timestamp = None
            if ts_match:
                ts_str = ts_match.group(0).strip("[]")
                # Handle cases like "22:46:16" (no date)
                try:
                    if "-" in ts_str:
                        timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        # Find just the time part if it's "Spatial  22:46:16" or similar
                        time_match = re.search(r"\d{2}:\d{2}:\d{2}", ts_str)
                        if time_match:
                            ts_str = time_match.group(0)
                        
                        # Use current date to avoid events being filtered out as "old"
                        now = datetime.now()
                        timestamp = datetime.strptime(ts_str, "%H:%M:%S").replace(
                            year=now.year, month=now.month, day=now.day
                        )
                except ValueError:
                    pass

            # Detect armor prevention lines FIRST (they modify previous events)
            if "prevented" in lower_line:
                prev_match = prevented_pattern.search(original_line)
                if prev_match:
                    reduction = float(prev_match.group("amount"))
                    # If we have a very recent taken event WITH damage, apply reduction
                    # Look back through recent events for a 'taken' with damage > 0
                    target_event = None
                    if last_taken_event and last_taken_event["damage"] > 0:
                        target_event = last_taken_event
                    
                    if target_event and (not timestamp or not target_event["timestamp"] or \
                       abs((timestamp - target_event["timestamp"]).total_seconds()) <= 2.0):
                        target_event["damage"] = max(0, target_event["damage"] - reduction)
                        current_offset = log_file.tell()
                        continue
                    else:
                        # If no recent taken event, record it as a potential zero damage event for taken stats
                        events.append({
                            "line_number": line_number,
                            "damage": 0,
                            "healing": 0,
                            "type": "taken",
                            "source": "Unknown",
                            "target": "you",
                            "timestamp": timestamp,
                            "raw": original_line,
                        })
                        current_offset = log_file.tell()
                        continue

            # Detect misses/evades/etc early to mark as zero-damage events
            is_mitigated = False
            mitigation_keywords = ["counterattacks", "blocks it", "misses", "evades", "evaded", "dodges", "parries"]
            if any(kw in lower_line for kw in mitigation_keywords):
                is_mitigated = True
                # Heuristic for mitigation events: "Source misses/evades Target"
                # Handle cases like: "You use Scalp Slam on a Gundark for 2573 points of damage, but he evades it."
                # Or: "Your Scalp Slam misses a Gundark."
                
                source_candidate = "Unknown"
                target_candidate = "Unknown"
                
                if lower_line.startswith("[") or re.match(r"^\d{2}:\d{2}:\d{2}", original_line):
                    # Strip channel and timestamp
                    content = re.sub(r"^(\[\w+\]\s+)?(\d{2}:\d{2}:\d{2}\s+)?", "", original_line)
                else:
                    content = original_line

                # Look for "Source Action Target but Mitigated" or "Source's Action misses Target"
                # Pattern: "X's Y misses Z" or "X misses Z"
                miss_match = re.search(r"(?P<source>.+?)(?:'s\s+(?P<ability>.+?))?\s+(?P<action>misses|evades|evaded|dodges|parries|counterattacks|blocks it)\b(?:\s+(?P<target>.+))?", content, re.IGNORECASE)
                
                if miss_match:
                    source_candidate = miss_match.group("source").strip()
                    target_candidate = miss_match.group("target").strip() if miss_match.group("target") else "Unknown"
                else:
                    # Fallback SWG style: "You use Ability on Target for X points of damage, but he evades it."
                    swg_miss_match = re.search(r"(?P<source>you|.+?)\s+(?P<action>uses|use|attacks|attack|deals|deal|heals|heal|hits|hit)\b\s+(?:(?P<ability>.+?)\s+(?:on|to|for)\s+)?(?P<target>.+?)\s+for\s+(?P<amount>\d+(?:\.\d+)?)\s*.+?,\s*but\s+(?:he|she|it|you)\s+(?P<mitigation>evades|evaded|dodges|parries|blocks it|counterattacks)", content, re.IGNORECASE)
                    if swg_miss_match:
                        source_candidate = swg_miss_match.group("source").strip()
                        target_candidate = swg_miss_match.group("target").strip()
                
                # Clean up candidates
                if source_candidate.lower().startswith("corpse of "): source_candidate = source_candidate[10:]
                if target_candidate.lower().startswith("corpse of "): target_candidate = target_candidate[10:]
                
                if source_candidate:
                    source_name = "You" if source_candidate.lower() == "you" else source_candidate
                    target_name = "You" if target_candidate.lower() == "you" else target_candidate
                    
                    etype = "dealt"
                    if source_name == "You": etype = "dealt"
                    elif target_name == "You": etype = "taken"
                    
                    event = {
                        "line_number": line_number,
                        "damage": 0,
                        "healing": 0,
                        "type": etype,
                        "source": source_name,
                        "target": target_name,
                        "timestamp": timestamp,
                        "raw": original_line,
                        "is_mitigated": True
                    }
                    events.append(event)
                    if etype == "taken": last_taken_event = event
                    current_offset = log_file.tell()
                    continue

            # Try the SWG pattern first
            swg_match = None
            if any(kw in lower_line for kw in swg_keywords):
                try:
                    swg_match = swg_pattern.search(original_line)
                except Exception:
                    swg_match = None
            
            damage = 0
            healing = 0
            event_type = None
            source_name = "Unknown"
            target_name = "Unknown"
            
            if swg_match:
                source_name = swg_match.group("name").strip()
                action = swg_match.group("action").lower()
                amount = float(swg_match.group("amount"))
                target_name = swg_match.group("target").strip()
                
                # Clean up names (e.g. corpse of)
                if source_name.lower().startswith("corpse of "):
                    source_name = source_name[10:]
                if target_name.lower().startswith("corpse of "):
                    target_name = target_name[10:]

                # Basic validation: if name is empty after strip, fallback to Unknown
                if not source_name: source_name = "Unknown"
                if not target_name: target_name = "Unknown"

                if "heal" in action and "health" in lower_line:
                    healing = amount
                    event_type = "healing"
                elif "heal" in action:
                    healing = amount
                    event_type = "healing"
                else:
                    damage = amount
                    if source_name.lower() == "you":
                        event_type = "dealt"
                    elif target_name.lower() == "you":
                        event_type = "taken"
                    else:
                        event_type = "other_dealt"
                
                # Check for "but he evades it" style mitigation in SWG lines
                if "evades" in lower_line or "counterattacks" in lower_line:
                    damage = 0
                    is_mitigated = True
            
            # Detect misses/evades/etc early to mark as zero-damage events if not already combat
            if not event_type:
                mitigation_keywords = ["counterattacks", "blocks it", "misses", "evades", "evaded", "dodges", "parries"]
                if any(kw in lower_line for kw in mitigation_keywords):
                    is_mitigated = True
                    # Look for source/target in mitigation lines
                    # Simple heuristic: "Source misses Target"
                    parts = original_line.split(" ")
                    # Filter out timestamp/Spatial parts
                    clean_parts = [p for p in parts if ":" not in p and "[" not in p and "]" not in p]
                    if len(clean_parts) >= 3:
                        source_candidate = clean_parts[0]
                        target_candidate = clean_parts[-1].rstrip(".!")
                        
                        if source_candidate.lower() == "you":
                            source_name = "you"
                            target_name = target_candidate
                            event_type = "dealt"
                        elif target_candidate.lower() == "you":
                            source_name = source_candidate
                            target_name = "you"
                            event_type = "taken"
                        elif source_candidate:
                            source_name = source_candidate
                            event_type = "other_dealt"
                        
                        if event_type:
                            damage = 0
            
            # Healing should not start combat or extend duration if we are strictly looking for damage
            # We will mark it as healing event but it won't trigger app_start_time resets later
            
            # Try specific activity patterns if no event_type yet
            if not event_type:
                for pattern, kws in activity_patterns:
                    # Optimized keyword check - avoid repeated lower() calls by using lower_line
                    is_match = False
                    for kw in kws:
                        if kw in lower_line:
                            is_match = True
                            break
                    if not is_match:
                        continue
                        
                    act_match = pattern.search(original_line)
                    if act_match:
                        # Extract name if it exists in groups, otherwise handled specifically (like pvp_kill)
                        try:
                            source_name = act_match.group("name").strip()
                        except (IndexError, AttributeError, KeyError):
                            source_name = "Unknown"
                        
                        # Clean up names
                        if source_name.lower().startswith("corpse of "):
                            source_name = source_name[10:]

                        # Filter out NPCs and non-players
                        # NPCs in SWG logs often have descriptions in parentheses
                        # Example: Bebaiso Mowi (a Rebel security guard)
                        if " (" in source_name:
                            continue

                        event_type = "activity"
                        
                        # Set target_name to the action if available
                        try:
                            # If it's a loot event, capture the item as well
                            if "looted" in pattern.pattern:
                                target_name = act_match.group("target").strip()
                                item_name = act_match.group("item").strip()
                                event_type = "loot"
                                source_name = source_name
                                target_name = target_name
                                item_name = item_name
                            elif "inventory is full" in pattern.pattern:
                                events.append({
                                    "line_number": line_number,
                                    "damage": 0,
                                    "healing": 0,
                                    "type": "inventory_full",
                                    "source": "You",
                                    "target": "Inventory",
                                    "timestamp": timestamp,
                                    "raw": original_line,
                                })
                                event_type = "processed"
                                break
                            elif "has bested" in pattern.pattern:
                                # pvp_kill
                                winner = act_match.group("winner").strip()
                                loser = act_match.group("loser").strip()
                                events.append({
                                    "line_number": line_number,
                                    "damage": 0,
                                    "healing": 0,
                                    "type": "pvp_kill",
                                    "source": winner,
                                    "target": loser,
                                    "timestamp": timestamp,
                                    "raw": original_line,
                                })
                                event_type = "processed"
                                break
                            else:
                                target_name = act_match.group("action").strip()
                        except (IndexError, AttributeError):
                            pass
                        
                        if event_type == "loot":
                            events.append(
                                {
                                    "line_number": line_number,
                                    "damage": 0,
                                    "healing": 0,
                                    "type": "loot",
                                    "source": source_name,
                                    "target": target_name,
                                    "item": item_name,
                                    "timestamp": timestamp,
                                    "raw": original_line,
                                }
                            )
                            event_type = "processed" # Mark as handled
                        
                        break

                if event_type == "processed":
                    continue

                if not event_type:
                    # Fallback to existing logic
                    dealt_match = None
                    if any(kw in lower_line for kw in dealt_keywords):
                        try:
                            dealt_match = damage_dealt_pattern.search(original_line)
                        except Exception: dealt_match = None
                    
                    taken_match = None
                    if any(kw in lower_line for kw in taken_keywords):
                        try:
                            taken_match = damage_taken_pattern.search(original_line)
                        except Exception: taken_match = None

                    if dealt_match:
                        damage = float(dealt_match.group(1))
                        event_type = "dealt"
                        source_name = "you"
                    elif taken_match:
                        damage = float(taken_match.group("amount"))
                        event_type = "taken"
                        source_name = taken_match.group("attacker")
                        target_name = "you"
                    else:
                        normalized_line = lower_line
                        damage_related = any(kw in normalized_line for kw in ["damage", "dmg", "hit", "hits", "deal", "deals", "heal", "heals"])
                        if not damage_related:
                            continue

                        line_no_ts = original_line
                        if ts_match:
                            line_no_ts = original_line[:ts_match.start()] + original_line[ts_match.end():]
                        
                        numbers = re.findall(r"\d+(?:\.\d+)?", line_no_ts)
                        if numbers:
                            val = max(float(number) for number in numbers)
                            if "heal" in normalized_line and "health" in normalized_line:
                                healing = val
                                event_type = "healing"
                            else:
                                damage = val
                                if re.search(r"\byou\b", normalized_line.split("deals")[0].split("hits")[0].split("use")[0].split("attack")[0]):
                                    event_type = "dealt"
                                    source_name = "you"
                                else:
                                    event_type = "taken"
                                    # Try to extract a name if it's "Name deals you X damage"
                                    name_match = re.search(r"^.*?\]?\s+(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>.+?)\s+(?:deals|hits|hit|uses|attacks)\b", original_line, re.IGNORECASE)
                                    if name_match:
                                        source_name = name_match.group("name").strip()
                                        if source_name.lower() == "you":
                                            source_name = "you"
                                            event_type = "dealt"
                                    else:
                                        source_name = "Unknown"
                        else:
                            continue

            if event_type:
                # Apply mitigation
                if is_mitigated:
                    damage = 0

                events.append(
                    {
                        "line_number": line_number,
                        "damage": damage,
                        "healing": healing,
                        "type": event_type,
                        "source": source_name,
                        "target": target_name,
                        "timestamp": timestamp,
                        "raw": original_line,
                    }
                )
                if event_type == "taken":
                    last_taken_event = events[-1]
            
            current_offset = log_file.tell()

    return events, current_offset


def calculate_dps(events):
    """
    Calculate total damage dealt, damage taken, and estimated DPS.

    Uses timestamps to calculate duration if available.
    """
    if not events:
        # print("DEBUG: calculate_dps called with NO events")
        return 0, 0, 0.0, 0.0, 0, 0, 0, 0

    damage_dealt = sum(event["damage"] for event in events if event["type"] == "dealt")
    damage_taken = sum(event["damage"] for event in events if event["type"] == "taken")
    
    miss_count = sum(1 for event in events if event["type"] == "dealt" and event["damage"] == 0)
    hit_count = sum(1 for event in events if event["type"] == "dealt" and event["damage"] > 0)
    
    avoided_count = sum(1 for event in events if event["type"] == "taken" and event["damage"] == 0)
    taken_count = sum(1 for event in events if event["type"] == "taken")
    
    # print(f"DEBUG: Dealt: {damage_dealt}, Taken: {damage_taken}, Hits: {hit_count}, Misses: {miss_count}, Avoided: {avoided_count}")

    # Try to use timestamps for duration (use all damage events for duration)
    valid_timestamps = [e["timestamp"] for e in events if e["timestamp"] and e["damage"] > 0]
    
    duration = 0.0
    if len(valid_timestamps) >= 2:
        start_ts = min(valid_timestamps)
        end_ts = max(valid_timestamps)
        duration = (end_ts - start_ts).total_seconds()
        
        # Avoid division by zero, and ensure minimum duration
        effective_duration = max(0.1, duration)
        dps = damage_dealt / effective_duration
    else:
        # Fallback to estimation using damage dealt events
        dealt_events = [e for e in events if e["type"] == "dealt"]
        estimated_duration_seconds = max(0.1, float(len(dealt_events)))
        dps = damage_dealt / estimated_duration_seconds
        duration = float(len(dealt_events))

    return damage_dealt, damage_taken, dps, duration, miss_count, hit_count, avoided_count, taken_count


OPTIONS_DEFAULT_WIDTH = 250
OPTIONS_DEFAULT_HEIGHT = 220

class CombatLogApp:
    def __init__(self, root):
        print("DEBUG: Initializing CombatLogApp")
        self.root = root
        self.root.title("Combat Log Analyzer")
        self.root.geometry("260x220")
        self.root.configure(bg=WINDOW_BG)
        
        # Check for SWG client
        self.target_hwnd = self.find_target_window()
        if not self.target_hwnd:
            self.root.withdraw() # Keep main window hidden
            # self.play_sound()
            # ThemedMessagebox.showinfo(
            #     None, 
            #     "Notice", 
            #     "LivyLogs requires Star Wars Galaxies to be running.\nPlease open the game client and try again.",
            #     on_close=lambda: sys.exit(0)
            # )
            sys.exit(0)
            return

        # Font configuration
        self.font_title = ("Segoe UI", 10, "bold")
        self.font_content = ("Segoe UI", 10)
        self.font_small = ("Segoe UI", 9)
        self.font_button = ("Segoe UI", 10, "bold")
        self.font_stats = ("Segoe UI Variable Display", 20, "bold")

        # Font objects for dynamic scaling
        self.font_stats_obj = tkfont.Font(family="Segoe UI Variable Display", size=20, weight="bold")
        self.font_title_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_small_obj = tkfont.Font(family="Segoe UI", size=9)
        self.font_button_obj = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # Configure themed scrollbars
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Vertical.TScrollbar", 
                        gripcount=0,
                        background=BUTTON_BG, 
                        darkcolor=BUTTON_BG, 
                        lightcolor=BUTTON_BG,
                        troughcolor=PANEL_BG, 
                        bordercolor=BORDER_COLOR, 
                        arrowcolor=TEXT_SECONDARY)
        self.style.map("Vertical.TScrollbar",
                  background=[('active', BUTTON_HOVER), ('pressed', BORDER_HIGHLIGHT)])

        self.config = ConfigParser()
        self.config.read("settings.ini")

        if "General" in self.config:
            initial_log_path = self.config["General"].get("log_path", "")
            initial_alpha = self.config["General"].getfloat("transparency", fallback=1.0)
            initial_width = self.config["General"].getint("width", fallback=450)
            initial_height = self.config["General"].getint("height", fallback=80)
            initial_x = self.config["General"].get("x", fallback=None)
            initial_y = self.config["General"].get("y", fallback=None)
        else:
            initial_log_path = ""
            initial_alpha = 1.0
            initial_width = 450
            initial_height = 80
            initial_x = None
            initial_y = None

        # Enforce minimum size
        initial_width = max(MIN_WIDTH, initial_width)
        initial_height = max(MIN_HEIGHT, initial_height)

        if initial_x is not None and initial_y is not None:
            self.root.geometry(f"{initial_width}x{initial_height}+{initial_x}+{initial_y}")
        else:
            # Default first-run position
            self.root.geometry(f"{initial_width}x{initial_height}+50+50")
        
        # Initialize transparency and state
        self.target_alpha = initial_alpha
        self.current_alpha = 0.0
        self.root.attributes("-alpha", 0.0)
        self.root.overrideredirect(True)
        
        # Initial state: not topmost until we confirm focus
        self._last_topmost_state = False
        
        self.fade_speed = 0.05
        self.fade_after_id = None
        
        self.file_path_var = tk.StringVar(value=initial_log_path)

        self.disable_warnings = tk.BooleanVar(value=False)
        if "General" in self.config:
            self.disable_warnings.set(self.config["General"].getboolean("disable_warnings", fallback=False))

        # Initialize window references to avoid tracking errors during startup
        self.damage_meter_window = None
        self.leaderboard_window = None
        self.skimmers_window = None
        self.details_window = None
        self.options_window = None

        # Staggered initialization
        self.root.after(300, self.initial_show)
        self.root.after(800, self.start_window_tracking)
        self.root.after(1000, self.start_show)
        
        # Establishing a clean real-time baseline on startup
        self.root.after(100, lambda: self.analyze_log(manual=True))
        self.root.after(500, self.start_analysis_loop)

        self.options_window = None
        self.last_ui_update_time = 0
        self.ui_update_delay = 0.05  # 50ms throttle for heavy UI updates
        
        # Pulsing effect for duration
        self.pulse_state = False
        self.last_pulse_time = 0
        
        self.target_hwnd = getattr(self, "target_hwnd", None)
        # Performance metrics tracking
        self.player_data = {}  # {name: {"damage": 0, "healing": 0, "logs": []}}
        self.leaderboard_data = {} # Persistent damage between resets
        self.loot_data = {} # {name: [{"item": item, "target": target, "time": timestamp}]}
        self.last_combat_time = 0
        self.last_log_mtime = 0
        self.details_window = None
        self.leaderboard_window = None
        self.leaderboard_reset_time = None
        self.skimmers_window = None
        self.damage_meter_window = None
        self.current_detail_player = None
        self.current_skimmer_player = None
        self.app_start_time = None # Set on first event to ensure immediate display
        self.last_combat_time = 0
        self.dm_labels_created = False
        self.time_window_details = 30
        self.time_window_leaderboard = 30
        self.time_window_skimmers = 30
        self.time_window_dm = 30 # Fixed Seconds for DM timeout
        self.always_on_top = False # Always off on startup
        self.inventory_full = False
        self.inventory_full_time = None

        # Incremental app version
        self.version = "1.0"

        if "General" in self.config:
            self.time_window_details = self.config["General"].getint("time_window_details", fallback=self.config["General"].getint("time_window", fallback=30))
            self.time_window_leaderboard = self.config["General"].getint("time_window_leaderboard", fallback=self.config["General"].getint("time_window", fallback=30))
            self.time_window_skimmers = self.config["General"].getint("time_window_skimmers", fallback=self.config["General"].getint("time_window", fallback=30))
            # self.always_on_top = self.config["General"].getboolean("always_on_top", fallback=self.config["General"].getboolean("afk_loot", fallback=False))
            self.time_window_dm = 30 # Fixed

        # Incremental parsing state
        self.last_read_offset = 0
        self.all_events = []
        self.last_processed_file = ""

        self.build_layout()
        
        # Set Window Icon

    def initial_show(self):
        """Delayed initialization to ensure window is fully created before applying attributes."""
        try:
            print("DEBUG: Initial show triggered")
            # Border removal is now handled in __init__ for immediate effect
            self.root.withdraw() # Keep it withdrawn initially
            
            # We don't force topmost here anymore, let check_target_window handle it
            
            # Ensure Z-order is prepared using Win32, but keep hidden
            hwnd = self.root.winfo_id()
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_HIDEWINDOW)
        except Exception as e:
            print(f"DEBUG: Error in initial_show: {e}")

    def play_sound(self):
        """Play notice.mp3 using MCI."""
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # If running as a bundled executable, look in the temp folder
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
            
            sound_path = os.path.join(base_path, "notice.mp3")
            
            if os.path.exists(sound_path):
                # Use MCI to play MP3 on Windows
                winmm.mciSendStringW(f'open ""{sound_path}"" type mpegvideo alias notice_sound', None, 0, None)
                winmm.mciSendStringW('play notice_sound', None, 0, None)
        except Exception as e:
            print(f"Error playing sound: {e}")

    def start_window_tracking(self):
        """Starts the periodic check for the target window."""
        self.check_target_window()
        # Ensure UI labels are responsive even if no log events
        if hasattr(self, 'lbl_time_val'):
            self.refresh_ui_only()

    def start_analysis_loop(self):
        """Starts the periodic log analysis loop."""
        # Optimization: only run analysis if we've completed the previous one
        if not hasattr(self, '_analysis_in_progress') or not self._analysis_in_progress:
            # We don't want to use a background thread for the regular periodic check
            # because analyze_log might call UI methods if it detects a timeout/reset.
            # However, for periodic checks, new_events is usually small, so it's fast.
            self._analysis_in_progress = True
            try:
                self.analyze_log(manual=False)
            finally:
                self._analysis_in_progress = False
        self.root.after(100, self.start_analysis_loop)

    def on_exit(self):
        """Saves configuration and exits the application."""
        self.save_config()
        self.root.destroy()

    def save_config(self):
        """Saves current window positions and sizes to settings.ini."""
        if "General" not in self.config:
            self.config["General"] = {}
        
        self.config["General"]["log_path"] = self.file_path_var.get()
        self.config["General"]["transparency"] = str(self.target_alpha)
        self.config["General"]["width"] = str(self.root.winfo_width())
        self.config["General"]["height"] = str(self.root.winfo_height())
        self.config["General"]["x"] = str(self.root.winfo_x())
        self.config["General"]["y"] = str(self.root.winfo_y())
        self.config["General"]["disable_warnings"] = str(self.disable_warnings.get())
        self.config["General"]["time_window_details"] = str(self.time_window_details)
        self.config["General"]["time_window_leaderboard"] = str(self.time_window_leaderboard)
        self.config["General"]["time_window_skimmers"] = str(self.time_window_skimmers)
        self.config["General"]["always_on_top"] = "False" # Don't persist ONTOP between sessions

        # Reset window visibility for next session per user request
        self.config["General"]["details_open"] = "False"
        self.config["General"]["leaderboard_open"] = "False"
        self.config["General"]["skimmers_open"] = "False"
        self.config["General"]["damage_meter_open"] = "False"
        self.config["General"]["options_open"] = "False"

        # Details Window
        if self.details_window and self.details_window.winfo_exists():
            if "DetailsWindow" not in self.config:
                self.config["DetailsWindow"] = {}
            self.config["DetailsWindow"]["width"] = str(self.details_window.winfo_width())
            self.config["DetailsWindow"]["height"] = str(self.details_window.winfo_height())
            self.config["DetailsWindow"]["x"] = str(self.details_window.winfo_x())
            self.config["DetailsWindow"]["y"] = str(self.details_window.winfo_y())

        # Leaderboard Window
        if self.leaderboard_window and self.leaderboard_window.winfo_exists():
            if "LeaderboardWindow" not in self.config:
                self.config["LeaderboardWindow"] = {}
            self.config["LeaderboardWindow"]["width"] = str(self.leaderboard_window.winfo_width())
            self.config["LeaderboardWindow"]["height"] = str(self.leaderboard_window.winfo_height())
            self.config["LeaderboardWindow"]["x"] = str(self.leaderboard_window.winfo_x())
            self.config["LeaderboardWindow"]["y"] = str(self.leaderboard_window.winfo_y())

        # Skimmers Window
        if self.skimmers_window and self.skimmers_window.winfo_exists():
            if "SkimmersWindow" not in self.config:
                self.config["SkimmersWindow"] = {}
            self.config["SkimmersWindow"]["width"] = str(self.skimmers_window.winfo_width())
            self.config["SkimmersWindow"]["height"] = str(self.skimmers_window.winfo_height())
            self.config["SkimmersWindow"]["x"] = str(self.skimmers_window.winfo_x())
            self.config["SkimmersWindow"]["y"] = str(self.skimmers_window.winfo_y())

        # Damage Meter Window
        if self.damage_meter_window and self.damage_meter_window.winfo_exists():
            if "DamageMeterWindow" not in self.config:
                self.config["DamageMeterWindow"] = {}
            self.config["DamageMeterWindow"]["width"] = str(self.damage_meter_window.winfo_width())
            self.config["DamageMeterWindow"]["height"] = str(self.damage_meter_window.winfo_height())
            self.config["DamageMeterWindow"]["x"] = str(self.damage_meter_window.winfo_x())
            self.config["DamageMeterWindow"]["y"] = str(self.damage_meter_window.winfo_y())

        # Options Window
        if self.options_window and self.options_window.winfo_exists():
            if "OptionsWindow" not in self.config:
                self.config["OptionsWindow"] = {}
            self.config["OptionsWindow"]["width"] = str(self.options_window.winfo_width())
            self.config["OptionsWindow"]["height"] = str(self.options_window.winfo_height())
            self.config["OptionsWindow"]["x"] = str(self.options_window.winfo_x())
            self.config["OptionsWindow"]["y"] = str(self.options_window.winfo_y())

        try:
            with open("settings.ini", "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error saving config: {e}")

    def find_target_window(self):
        """Finds the most recently active (topmost) window containing 'SwgClient' or 'Star Wars Galaxies'."""
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        matching_windows = []

        def enum_windows_callback(hwnd, lparam):
            # We only care about visible windows for "locking on" to the active one
            if not user32.IsWindowVisible(hwnd):
                return True
                
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
                if "SwgClient" in title or "Star Wars Galaxies" in title:
                    # EnumWindows enumerates in Z-order (top to bottom)
                    # So the first one we find is likely the most recent/active one
                    matching_windows.append(hwnd)
                    return False # Stop enumerating once we find the top one
            return True

        # Keep a reference to the callback to prevent garbage collection
        self._enum_cb = WNDENUMPROC(enum_windows_callback)
        user32.EnumWindows(self._enum_cb, 0)
        
        if not matching_windows:
            return None
            
        return matching_windows[0]

    def is_foreground_ours(self):
        """Checks if the current foreground window belongs to this application or the game."""
        foreground_hwnd = user32.GetForegroundWindow()
        if not foreground_hwnd:
            return False
            
        # 1. Check if it's our application (matches our Process ID)
        foreground_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(foreground_hwnd, ctypes.byref(foreground_pid))
        our_pid = kernel32.GetCurrentProcessId()
        
        if foreground_pid.value == our_pid:
            return True
            
        # 2. Check if it's the game or a child/parent/sibling of the game
        if self.target_hwnd and user32.IsWindow(self.target_hwnd):
            # Is foreground the game itself?
            if foreground_hwnd == self.target_hwnd:
                return True
                
            # Does the foreground window belong to the same process as the game?
            target_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(self.target_hwnd, ctypes.byref(target_pid))
            if foreground_pid.value == target_pid.value:
                return True

            # Check if foreground is a child/descendant of the game
            temp_hwnd = foreground_hwnd
            while temp_hwnd:
                if temp_hwnd == self.target_hwnd:
                    return True
                # GetParent can sometimes miss owned windows (popups)
                parent = user32.GetParent(temp_hwnd)
                owner = user32.GetWindow(temp_hwnd, 4) # GW_OWNER = 4
                
                # Try to find a valid ancestor
                next_hwnd = parent if parent else owner
                if not next_hwnd or next_hwnd == temp_hwnd: break
                temp_hwnd = next_hwnd
                
            # Is the game a child/descendant of the foreground?
            temp_hwnd = self.target_hwnd
            while temp_hwnd:
                if temp_hwnd == foreground_hwnd:
                    return True
                parent = user32.GetParent(temp_hwnd)
                owner = user32.GetWindow(temp_hwnd, 4) # GW_OWNER = 4
                
                next_hwnd = parent if parent else owner
                if not next_hwnd or next_hwnd == temp_hwnd: break
                temp_hwnd = next_hwnd

        return False

    def check_target_window(self):
        """Periodically checks if the target window exists and updates visibility logic."""
        try:
            # If no target locked, or target invalid, try to find any SWG window
            if not self.target_hwnd or not user32.IsWindow(self.target_hwnd):
                self.target_hwnd = self.find_target_window()

            # Determine if we should be topmost and if we should show
            is_valid_foreground = self.is_foreground_ours()
            
            # Check if game is minimized
            is_minimized = False
            if self.target_hwnd and user32.IsWindow(self.target_hwnd):
                placement = wintypes.WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(wintypes.WINDOWPLACEMENT)
                if user32.GetWindowPlacement(self.target_hwnd, ctypes.byref(placement)):
                    is_minimized = (placement.showCmd == 2)
            
            should_show = (is_valid_foreground or self.always_on_top) and not is_minimized
            is_topmost_needed = should_show

            if should_show:
                if self.root.state() == "withdrawn" or (not self.fade_after_id and self.current_alpha < self.target_alpha):
                    self.start_show()
                
                # List of windows to manage (root + popups)
                managed_windows = self._get_managed_windows()

                # Check if state already matches to avoid redundant SetWindowPos calls
                if not hasattr(self, '_last_topmost_state'):
                    self._last_topmost_state = None

                if is_topmost_needed:
                    if self._last_topmost_state != True:
                        for win in managed_windows:
                            try:
                                win_hwnd = win.winfo_id()
                                user32.SetWindowPos(win_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                                win.attributes("-topmost", True)
                            except:
                                pass
                        self._last_topmost_state = True
                else:
                    if self._last_topmost_state != False:
                        for win in managed_windows:
                            try:
                                win_hwnd = win.winfo_id()
                                win.attributes("-topmost", False)
                                user32.SetWindowPos(win_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                            except:
                                pass
                        self._last_topmost_state = False
            else:
                # Use a small grace period (1 second) before hiding to prevent flickering during transient focus shifts
                if (not hasattr(self, '_hide_grace_after_id') or self._hide_grace_after_id is None) and self.root.state() != "withdrawn":
                    self._hide_grace_after_id = self.root.after(1000, self._perform_graceful_hide)

        except Exception as e:
            print(f"Error in window tracking: {e}")

        # Check again in 250ms for smoother detection and transition
        self.root.after(250, self.check_target_window)

    def _perform_graceful_hide(self):
        """Actually performs the hide after the grace period if still out of focus."""
        self._hide_grace_after_id = None
        try:
            is_valid_foreground = self.is_foreground_ours()
            if not is_valid_foreground and not self.always_on_top:
                if self.root.state() != "withdrawn" and self.current_alpha > 0:
                    # Ensure windows are NOT topmost when we are hiding
                    if getattr(self, '_last_topmost_state', None) != False:
                        for win in self._get_managed_windows():
                            try:
                                win.attributes("-topmost", False)
                                win_hwnd = win.winfo_id()
                                user32.SetWindowPos(win_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                            except:
                                pass
                        self._last_topmost_state = False
                        
                    self.start_hide()
        except Exception as e:
            print(f"Error in graceful hide: {e}")

    def show_help_notice(self):
        """Shows the character log notice manually when Help is clicked."""
        # The user requested to disable the warning menu.
        pass

    def _show_initial_notice(self, notice_text):
        """Shows the initial notice and ensures it and the main window stay on top."""
        # The user requested to disable the warning menu.
        pass

    def start_show(self):
        """Immediately shows all managed windows and cancels any pending hide."""
        if hasattr(self, '_hide_grace_after_id') and self._hide_grace_after_id:
            self.root.after_cancel(self._hide_grace_after_id)
            self._hide_grace_after_id = None
            
        is_hidden = self.root.state() == "withdrawn"
        if is_hidden:
            self.current_alpha = 0.0
            for win in self._get_managed_windows():
                win.attributes("-alpha", 0.0)
                win.deiconify()
        
        if self.current_alpha < self.target_alpha:
            if self.fade_after_id:
                # If we are already fading in, don't restart it
                if getattr(self, '_fading_direction', None) == 'in':
                    return
                self.root.after_cancel(self.fade_after_id)
            
            self._fading_direction = 'in'
            self.fade_in()

    def fade_in(self):
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.target_alpha, self.current_alpha + 0.1)
            for win in self._get_managed_windows():
                win.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.root.after(20, self.fade_in)
        else:
            self.fade_after_id = None
            self._fading_direction = None

    def start_hide(self):
        """Immediately starts hiding all managed windows."""
        if self.root.state() == "withdrawn":
            return
            
        if self.current_alpha > 0.0:
            if self.fade_after_id:
                # If we are already fading out, don't restart it
                if getattr(self, '_fading_direction', None) == 'out':
                    return
                self.root.after_cancel(self.fade_after_id)
            
            self._fading_direction = 'out'
            self.fade_out()

    def fade_out(self):
        if self.current_alpha > 0.0:
            self.current_alpha = max(0.0, self.current_alpha - 0.1)
            for win in self._get_managed_windows():
                win.attributes("-alpha", self.current_alpha)
            self.fade_after_id = self.root.after(20, self.fade_out)
        else:
            for win in self._get_managed_windows():
                win.withdraw()
            self.fade_after_id = None
            self._fading_direction = None

    def _get_managed_windows(self):
        """Returns a list of all currently active managed windows."""
        managed = [self.root]
        if self.damage_meter_window and self.damage_meter_window.winfo_exists():
            managed.append(self.damage_meter_window)
        if self.leaderboard_window and self.leaderboard_window.winfo_exists():
            managed.append(self.leaderboard_window)
        if self.skimmers_window and self.skimmers_window.winfo_exists():
            managed.append(self.skimmers_window)
        if self.details_window and self.details_window.winfo_exists():
            managed.append(self.details_window)
        if self.options_window and self.options_window.winfo_exists():
            managed.append(self.options_window)
        return managed

    def build_layout(self):
        # Main border wrapper for the whole app
        self.root_border = tk.Frame(self.root, bg=BORDER_COLOR, padx=1, pady=1)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        
        outer = tk.Frame(self.root_border, bg=WINDOW_BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        outer.bind("<Button-1>", self.click_window)
        outer.bind("<B1-Motion>", self.drag_window)

        # Add resize handle in the bottom right
        self.resize_handle = tk.Canvas(
            outer, 
            bg=WINDOW_BG, 
            cursor="size_nw_se", 
            width=25, 
            height=25, 
            highlightthickness=0,
            bd=0
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        
        # Draw a larger themed triangle/grip for the resize handle
        self.resize_handle.create_line(25, 0, 0, 25, fill=BORDER_HIGHLIGHT, width=1)
        self.resize_handle.create_line(25, 5, 5, 25, fill=BORDER_HIGHLIGHT, width=1)
        self.resize_handle.create_line(25, 10, 10, 25, fill=BORDER_HIGHLIGHT, width=1)
        self.resize_handle.create_line(25, 15, 15, 25, fill=BORDER_HIGHLIGHT, width=1)
        self.resize_handle.create_line(25, 20, 20, 25, fill=ACCENT_BLUE, width=2)

        tk.Misc.lift(self.resize_handle)

        self.resize_handle.bind("<Button-1>", self.init_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)
        self.resize_handle.bind("<ButtonRelease-1>", self.save_size)

        # Container for top section (Title bar)
        header_container = tk.Frame(outer, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_container.pack(fill=tk.BOTH, expand=True)

        # Title bar with Close and Options
        title_bar = tk.Frame(header_container, bg=PANEL_DARK, height=25)
        title_bar.pack(fill=tk.X)

        title_bar.bind("<Button-1>", self.click_window)
        title_bar.bind("<B1-Motion>", self.drag_window)

        # Close Button
        self.close_btn = tk.Label(
            title_bar,
            text=" ✕ ",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 12),
            cursor="hand2",
            padx=10
        )
        self.close_btn.pack(side=tk.RIGHT)
        
        self.close_btn.bind("<Button-1>", lambda e: self.on_exit())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg=tk.RED if hasattr(tk, "RED") else "#ff4444", bg=BUTTON_BG))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg=TEXT_SECONDARY, bg=PANEL_DARK))

        # Help (?) to the left of Close
        self.lbl_help = tk.Label(
            title_bar,
            text=" Help (?) ",
            bg=PANEL_DARK,
            fg=TEXT_ACCENT,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=5
        )
        self.lbl_help.pack(side=tk.RIGHT)
        self.lbl_help.bind("<Button-1>", lambda e: self.show_help_notice())
        self.lbl_help.bind("<Enter>", lambda e: self.lbl_help.config(fg=TEXT_PRIMARY, bg=BUTTON_BG))
        self.lbl_help.bind("<Leave>", lambda e: self.lbl_help.config(fg=TEXT_ACCENT, bg=PANEL_DARK))

        # Settings to the left of Help
        self.lbl_settings = tk.Label(
            title_bar,
            text=" SETTINGS ",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=self.font_small_obj,
            cursor="hand2",
            padx=5
        )
        self.lbl_settings.pack(side=tk.RIGHT)
        self.lbl_settings.bind("<Button-1>", lambda e: self.toggle_menu())
        self.lbl_settings.bind("<Enter>", lambda e: self.lbl_settings.config(fg=TEXT_ACCENT, bg=BUTTON_BG))
        self.lbl_settings.bind("<Leave>", lambda e: self.lbl_settings.config(fg=TEXT_SECONDARY, bg=PANEL_DARK))

        # App Title Label
        self.app_title_label = tk.Label(
            title_bar,
            text="Livylogs 1.0",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=self.font_small_obj,
        )
        self.app_title_label.pack(side=tk.LEFT)
        
        self.app_title_label.bind("<Button-1>", self.click_window)
        self.app_title_label.bind("<B1-Motion>", self.drag_window)

        # ONTOP Toggle
        self.ontop_btn = tk.Label(
            title_bar,
            text="ONTOP: OFF",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=10
        )
        self.ontop_btn.pack(side=tk.LEFT)
        self.ontop_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())
        if self.always_on_top:
            self.ontop_btn.config(text="ONTOP: ON", fg=ACCENT_BLUE)
        
        # Navigation Labels Row (Leaderboard, Details, Spy) - under the title
        nav_frame = tk.Frame(header_container, bg=PANEL_DARK)
        nav_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        nav_frame.lift()

        def create_nav_label(parent, text):
            lbl = tk.Label(
                parent,
                text=text,
                bg=PANEL_DARK,
                fg=TEXT_SECONDARY,
                font=self.font_small_obj,
                padx=5,
                pady=2,
                cursor="hand2"
            )
            lbl.bind("<Enter>", lambda e: lbl.config(fg=TEXT_ACCENT, bg=BUTTON_BG))
            lbl.bind("<Leave>", lambda e: lbl.config(fg=TEXT_SECONDARY, bg=PANEL_DARK))
            return lbl

        self.lbl_dmg_meter = create_nav_label(nav_frame, "DMG METER")
        self.lbl_dmg_meter.pack(side=tk.LEFT)
        self.lbl_dmg_meter.bind("<Button-1>", lambda e: self.show_damage_meter_window())

        self.lbl_details = create_nav_label(nav_frame, "DETAILS")
        self.lbl_details.pack(side=tk.LEFT)
        self.lbl_details.bind("<Button-1>", lambda e: self.show_details_window())
            
        self.lbl_skimmers = create_nav_label(nav_frame, "SKIMMERS")
        self.lbl_skimmers.pack(side=tk.LEFT)
        self.lbl_skimmers.bind("<Button-1>", lambda e: self.show_skimmers_window())

        self.lbl_leaderboard = create_nav_label(nav_frame, "LEADERBOARD")
        self.lbl_leaderboard.pack(side=tk.LEFT)
        self.lbl_leaderboard.bind("<Button-1>", lambda e: self.show_leaderboard_window())

        self.lbl_loot = create_nav_label(nav_frame, "LOOT")
        self.lbl_loot.pack(side=tk.LEFT)
        self.lbl_loot.bind("<Button-1>", lambda e: self.show_skimmers_window())

        self.lbl_spy = create_nav_label(nav_frame, "SPY")
        self.lbl_spy.pack(side=tk.LEFT)
        self.lbl_spy.bind("<Button-1>", lambda e: self.show_details_window(force_open=True))

        self.lbl_version = tk.Label(nav_frame, text="1.0", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8))
        self.lbl_version.pack(side=tk.RIGHT, padx=5)

    def create_stat_box(self, parent, title, value, secondary_title=None, secondary_value=None):
        # Double-layered border for stat boxes
        outer_border = tk.Frame(
            parent,
            bg=BORDER_COLOR,
            padx=1,
            pady=1
        )
        
        box = tk.Frame(
            outer_border,
            bg=PANEL_DARK,
            highlightthickness=1,
            highlightbackground=BORDER_HIGHLIGHT,
        )
        box.pack(fill=tk.BOTH, expand=True)
        
        box.bind("<Button-1>", self.click_window)
        box.bind("<B1-Motion>", self.drag_window)
        outer_border.bind("<Button-1>", self.click_window)
        outer_border.bind("<B1-Motion>", self.drag_window)

        # Use grid for better control over alignment
        box.grid_columnconfigure(0, weight=1, minsize=100)
        box.grid_columnconfigure(1, weight=1, minsize=100)

        # Primary Title (Left)
        title_label = tk.Label(
            box,
            text=title,
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=self.font_small_obj,
            anchor=tk.W,
            justify=tk.LEFT
        )
        title_label.grid(row=0, column=0, padx=(8, 4), pady=(4, 0), sticky="w")
        title_label.bind("<Button-1>", self.click_window)
        title_label.bind("<B1-Motion>", self.drag_window)

        # Secondary Title (Right)
        if secondary_title:
            sec_title_label = tk.Label(
                box,
                text=secondary_title,
                bg=PANEL_DARK,
                fg=TEXT_SECONDARY,
                font=self.font_small_obj,
                anchor=tk.E,
                justify=tk.RIGHT
            )
            sec_title_label.grid(row=0, column=1, padx=(4, 8), pady=(4, 0), sticky="e")
            sec_title_label.bind("<Button-1>", self.click_window)
            sec_title_label.bind("<B1-Motion>", self.drag_window)

        # Primary Value (Left)
        value_label = tk.Label(
            box,
            text=value,
            bg=PANEL_DARK,
            fg=TEXT_PRIMARY,
            font=self.font_stats_obj,
            anchor=tk.W,
            justify=tk.LEFT
        )
        value_label.grid(row=1, column=0, padx=(8, 4), pady=(0, 4), sticky="w")
        value_label.bind("<Button-1>", self.click_window)
        value_label.bind("<B1-Motion>", self.drag_window)

        # Secondary Value (Right)
        if secondary_value:
            sec_value_label = tk.Label(
                box,
                text=secondary_value,
                bg=PANEL_DARK,
                fg=TEXT_PRIMARY,
                font=self.font_stats_obj,
                anchor=tk.E,
                justify=tk.RIGHT
            )
            sec_value_label.grid(row=1, column=1, padx=(4, 8), pady=(0, 4), sticky="e")
            sec_value_label.bind("<Button-1>", self.click_window)
            sec_value_label.bind("<B1-Motion>", self.drag_window)
            outer_border.sec_value_label = sec_value_label

        outer_border.value_label = value_label
        return outer_border

    def analyze_log(self, manual=False):
        start_time = time.time()
        if manual:
            print("DEBUG: Manual analysis triggered")
            # Clear historical data to show "real-time" on launch or manual reset
            self.all_events = []
            self.last_read_offset = -1 # Special flag to seek to end
            self.app_start_time = None
            self.last_combat_time = 0
            # Reset persistent UI data too
            self.player_data = {}
            self.loot_data = {}
            self.leaderboard_data = {}

        actual_file_path = self.file_path_var.get().strip()

        if not actual_file_path:
            return

        if not os.path.exists(actual_file_path):
            print(f"DEBUG: Log file path does not exist: {actual_file_path}")
            return

        # Optimization: only re-parse if file has changed
        try:
            mtime = os.path.getmtime(actual_file_path)
            if not manual and hasattr(self, 'last_log_mtime') and mtime <= self.last_log_mtime:
                self.refresh_ui_only()
                return
            self.last_log_mtime = mtime
        except:
            pass

        # If it's a directory, find latest file
        if os.path.isdir(actual_file_path):
            try:
                files = [os.path.join(actual_file_path, f) for f in os.listdir(actual_file_path) if f.lower().endswith(('.txt', '.log'))]
                if not files:
                    return
                actual_file_path = max(files, key=os.path.getmtime)
            except Exception as e:
                print(f"Error finding latest log in directory: {e}")
                return

        # Handle file switch or truncation
        if actual_file_path != self.last_processed_file:
            print(f"DEBUG: File switched or initial load: {actual_file_path}")
            # If this is the initial load or manual analysis, we read the last 256KB for history
            is_initial_history_load = False
            if not self.last_processed_file or manual:
                self.last_read_offset = -1
                is_initial_history_load = True
            else:
                self.last_read_offset = 0
                
            self.all_events = []
            self.last_processed_file = actual_file_path
            # Reset session timing on file switch
            self.app_start_time = None
            self.last_combat_time = 0
        else:
            is_initial_history_load = False
        
        try:
            # Check for truncation
            if os.path.getsize(actual_file_path) < self.last_read_offset:
                self.last_read_offset = 0
                self.all_events = []
                self.app_start_time = None

            new_events, new_offset = parse_combat_log(actual_file_path, self.last_read_offset)
            
            # Immediately add new events to all_events
            self.all_events.extend(new_events)
            self.last_read_offset = new_offset

            # Prune all_events early to keep memory footprint small
            now_dt = datetime.now()
            # ALWAYS prune to at least 65 minutes to support switching between 10M, 30M, and 60M without data loss
            prune_mins = 65
            prune_limit = now_dt - timedelta(minutes=prune_mins)
            self.all_events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= prune_limit]

            parse_time = time.time() - start_time
            if len(new_events) > 100 or parse_time > 0.1:
                print(f"DEBUG: parse_combat_log took {parse_time:.3f}s for {len(new_events)} events")
            
            # Update session and UI with new data
            now_ts = time.time()
            lb_window_ago = now_dt - timedelta(minutes=self.time_window_leaderboard)

            if new_events:
                # Force refresh UI immediately if we have new events
                self.last_ui_update_time = 0 
                
                print(f"DEBUG: New batch size: {len(new_events)}. Damage events in batch: {len([e for e in new_events if e['damage'] > 0])}")

                # If app_start_time is None (initial launch or after timeout),
                # try to initialize it from the FIRST damage event in the new batch.
                # If this is the initial history load, only initialize if the latest damage is recent (within 2 mins)
                if self.app_start_time is None:
                    damage_events = [e for e in new_events if e["damage"] > 0 and e["timestamp"]]
                    if damage_events:
                        latest_damage_ts = max(e["timestamp"] for e in damage_events)
                        is_recent = (datetime.now() - latest_damage_ts).total_seconds() < 120
                        
                        if not is_initial_history_load or is_recent:
                            self.app_start_time = min(e["timestamp"] for e in damage_events)
                            
                            # CRITICAL: Reset damage dealt and damage taken stats for the main UI
                            self.damage_dealt = 0
                            self.damage_taken = 0
                            
                            # CRITICAL: When starting a NEW session, synchronize the system clock anchor 
                            # to the log event's timestamp as accurately as possible. 
                            # This prevents the duration from jumping if the log was read late.
                            self.last_log_sync_time = self.app_start_time
                            self.last_combat_time = now_ts
                            # If the log event is already several seconds old when we first read it, 
                            # we must adjust our system-time anchor backwards so the 'projected' duration 
                            # matches the 'log' duration at this exact moment.
                            log_age = (now_dt - self.app_start_time).total_seconds()
                            if log_age > 0:
                                # Clamp log_age to a reasonable value (don't sync back more than 60s)
                                self.last_combat_time = now_ts - min(60.0, log_age)
                                
                            self.last_ui_update_time = 0 # Force refresh
                            
                            # CRITICAL: If we just initialized app_start_time, prune historical damage
                            # to ensure the NEW session starts clean.
                            max_history_mins = max(self.time_window_details, self.time_window_leaderboard, self.time_window_skimmers, 65)
                            history_limit = now_dt - timedelta(minutes=max_history_mins)
                            
                            old_event_count = len(self.all_events)
                            self.all_events = [
                                e for e in self.all_events 
                                if (e["timestamp"] and e["timestamp"] >= self.app_start_time) or 
                                   (e["type"] not in ["dealt", "taken", "damage"] and e["timestamp"] and e["timestamp"] >= history_limit)
                            ]
                            events_for_ui = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
                            print(f"DEBUG: Initialized app_start_time ({self.app_start_time}) and pruned {old_event_count - len(self.all_events)} old damage events.")
                        else:
                            print(f"DEBUG: Skipping app_start_time init from initial load because latest damage ({latest_damage_ts}) is not recent.")
                    else:
                        print("DEBUG: app_start_time is None and no damage events in this batch to initialize it.")

                print(f"DEBUG: Processed {len(new_events)} new events. First TS: {new_events[0]['timestamp']}, Start: {self.app_start_time}")
                
                has_combat = any(e["damage"] > 0 for e in new_events)
                if has_combat:
                    # Find latest damage event in the NEW batch
                    damage_events = [e for e in new_events if e["damage"] > 0 and e["timestamp"]]
                    latest_new_damage_ts = max(e["timestamp"] for e in damage_events)
                    
                    # If this is the initial history load, we only sync if damage is recent
                    is_recent = (datetime.now() - latest_new_damage_ts).total_seconds() < 120
                    
                    if not is_initial_history_load or is_recent:
                        # If it's been more than X seconds since the last damage, reset the meter
                        if self.last_combat_time > 0 and (now_ts - self.last_combat_time) > self.time_window_dm:
                            print(f"DEBUG: Combat timeout ({self.time_window_dm}s), resetting session. Last: {self.last_combat_time}, Now: {now_ts}")
                            self.leaderboard_data = {}
                            
                            # Reset app_start_time to the EARLIEST event of the NEW session in this batch
                            if damage_events:
                                self.app_start_time = min(e["timestamp"] for e in damage_events)
                                # CRITICAL: Also reset sync anchor when session is reset
                                self.last_log_sync_time = self.app_start_time
                                self.last_combat_time = now_ts
                                
                                # SYNC system clock to log age for clean start
                                log_age = (now_dt - self.app_start_time).total_seconds()
                                if log_age > 0:
                                    self.last_combat_time = now_ts - min(60.0, log_age)
                                    
                                print(f"DEBUG: Combat reset. New app_start_time: {self.app_start_time}")
                                
                                # Prune all_events to remove damage from the previous session
                                max_history_mins = max(self.time_window_details, self.time_window_leaderboard, self.time_window_skimmers, 65)
                                history_limit = now_dt - timedelta(minutes=max_history_mins)
                                
                                old_event_count = len(self.all_events)
                                self.all_events = [
                                    e for e in self.all_events 
                                    if (e["timestamp"] and e["timestamp"] >= self.app_start_time) or 
                                       (e["type"] not in ["dealt", "taken", "damage"] and e["timestamp"] and e["timestamp"] >= history_limit)
                                ]
                                events_for_ui = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
                                print(f"DEBUG: Combat reset. New app_start_time: {self.app_start_time}. Pruned {old_event_count - len(self.all_events)} old events.")
                            else:
                                self.app_start_time = None
                        
                        # CRITICAL: Sync last_combat_time to system time BUT anchor it to the LATEST log event we just read
                        self.last_combat_time = now_ts
                        self.last_log_sync_time = latest_new_damage_ts
                    else:
                         # Ensure anchors are clean after history load if not recent
                        self.last_combat_time = 0
                        self.last_log_sync_time = None
                elif is_initial_history_load:
                    # Ensure anchors are clean after history load
                    self.last_combat_time = 0
                    self.last_log_sync_time = None

            # Re-calculate leaderboard_data from all_events (already pruned)
            if manual or new_events:
                self.leaderboard_data = {}
                for event in self.all_events:
                    # Respect time window AND manual reset
                    if event["damage"] > 0 and event["timestamp"]:
                        if self.app_start_time and event["timestamp"] < self.app_start_time:
                            continue
                        if self.leaderboard_reset_time and event["timestamp"] < self.leaderboard_reset_time:
                            continue
                            
                        source_raw = event["source"].capitalize()
                        source = "You" if source_raw.lower() == "you" else source_raw
                        # Filter out NPCs
                        if " (" in source or source.lower().startswith("a ") or source.lower().startswith("an "):
                            continue
                        if source not in self.leaderboard_data:
                            self.leaderboard_data[source] = 0
                        self.leaderboard_data[source] += event["damage"]

            # Filter all_events for current session
            events_for_ui = self.all_events
            if self.app_start_time:
                events_for_ui = [e for e in events_for_ui if e["timestamp"] and e["timestamp"] >= self.app_start_time]
            else:
                events_for_ui = [] # No session started

            if manual or new_events:
                damage_in_ui = len([e for e in events_for_ui if e['damage'] > 0])
                print(f"DEBUG: Final events_for_ui count: {len(events_for_ui)} (Damage: {damage_in_ui}). First event type: {events_for_ui[0]['type'] if events_for_ui else 'N/A'}")

            # OPTIMIZATION: process_events_for_ui is heavy. Only run if we have new data OR if it's been a while
            # Also refresh immediately if skimmers, details or leaderboard are open
            is_any_open = (self.skimmers_window and self.skimmers_window.winfo_exists()) or \
                         (self.details_window and self.details_window.winfo_exists()) or \
                         (self.leaderboard_window and self.leaderboard_window.winfo_exists()) or \
                         (self.damage_meter_window and self.damage_meter_window.winfo_exists())
            
            if new_events or manual or is_any_open or not hasattr(self, 'last_full_ui_update') or (time.time() - self.last_full_ui_update > 1.0):
                self.root.after(0, lambda: self.process_events_for_ui(events_for_ui, manual=manual, all_events=self.all_events))
                self.last_full_ui_update = time.time()
            
            # Update Loot count on main UI label periodically
            now_time = time.time()
            if not hasattr(self, 'last_loot_label_update') or (now_time - self.last_loot_label_update > 10.0):
                loot_count = sum(len(items) for items in self.loot_data.values())
                self.lbl_loot.config(text=f"LOOT ({loot_count})")
                self.last_loot_label_update = now_time

            # Still refresh damage meter for duration ticks even if no new events
            self.root.after(0, lambda: self.refresh_damage_meter_window(events_for_ui))
            
            # Also update main UI stats if they exist
            damage_dealt, damage_taken, dps, duration, miss_count, hit_count, avoided_count, taken_count = calculate_dps(events_for_ui)
            
            # Main UI Duration (Cyan when paused/stopped)
            is_paused = self.last_combat_time > 0 and (time.time() - self.last_combat_time) > self.time_window_dm
            
            # SUPERCEED: If we have NEW combat events in this batch, we are NOT paused
            if new_events and any(e["damage"] > 0 for e in new_events):
                is_paused = False
            
            if is_paused:
                # If paused, show exact combat duration and dps from calculate_dps
                pass 
            else:
                # If active, allow live duration ticker in main UI as well
                # RELAXED CHECK: If we have damage in the current batch but app_start_time is None,
                # initialize it immediately to avoid 1-cycle delay
                if self.app_start_time is None and new_events:
                    damage_events = [e for e in new_events if e["damage"] > 0 and e["timestamp"]]
                    if damage_events:
                        latest_damage_ts = max(e["timestamp"] for e in damage_events)
                        is_recent = (datetime.now() - latest_damage_ts).total_seconds() < 120
                        
                        if not is_initial_history_load or is_recent:
                            self.app_start_time = min(e["timestamp"] for e in damage_events)
                            # Ensure anchor is also set
                            if self.last_combat_time == 0:
                                self.last_log_sync_time = self.app_start_time
                                self.last_combat_time = now_ts
                                
                                # SYNC system clock to log age
                                log_age = (now_dt - self.app_start_time).total_seconds()
                                if log_age > 0:
                                    self.last_combat_time = now_ts - min(60.0, log_age)
                            
                            # CRITICAL: If we just initialized app_start_time here, also prune all_events
                            # to remove any damage that was sitting in all_events before this batch.
                            max_history_mins = max(self.time_window_details, self.time_window_leaderboard, self.time_window_skimmers, 65)
                            history_limit = now_dt - timedelta(minutes=max_history_mins)
                            
                            old_event_count = len(self.all_events)
                            self.all_events = [
                                e for e in self.all_events 
                                if (e["timestamp"] and e["timestamp"] >= self.app_start_time) or 
                                   (e["type"] not in ["dealt", "taken", "damage"] and e["timestamp"] and e["timestamp"] >= history_limit)
                            ]
                            events_for_ui = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
                            print(f"DEBUG: Relaxed init app_start_time ({self.app_start_time}) and pruned {old_event_count - len(self.all_events)} old damage events.")

                if self.app_start_time and self.last_combat_time > 0:
                    # Determine our sync baseline
                    anchor_ts = getattr(self, 'last_log_sync_time', self.app_start_time)
                    time_since_sync = now_ts - self.last_combat_time
                    
                    # Project current time from anchor
                    projected_now = anchor_ts + timedelta(seconds=time_since_sync)
                    
                    # Safety cap: Cannot project past actual system clock
                    if projected_now > now_dt:
                        projected_now = now_dt
                    
                    live_now = projected_now
                    live_duration = (live_now - self.app_start_time).total_seconds()
                    
                    if live_duration > duration:
                        duration = live_duration
                        if duration > 0:
                            dps = damage_dealt / duration

            # Update pulsing state (300ms)
            current_time = time.time()
            if current_time - self.last_pulse_time > 0.3:
                self.pulse_state = not self.pulse_state
                self.last_pulse_time = current_time

            display_duration = f"{duration:.0f}s"
            duration_color = "cyan" if is_paused else TEXT_PRIMARY
            
            # Pulse duration if > 0 and NOT in active combat/paused
            # "No combat started" means self.last_combat_time is 0
            if duration > 0 and self.last_combat_time == 0:
                if self.pulse_state:
                    duration_color = "cyan"
                else:
                    duration_color = "#AAAAAA" # Dim gray for pulse off
            
            def update_main_labels(d_dealt=damage_dealt, dps_val=dps, disp_dur=display_duration, dur_col=duration_color):
                if hasattr(self, 'lbl_damage_val'):
                    self.lbl_damage_val.config(text=f"{d_dealt:.0f}")
                if hasattr(self, 'lbl_dps_val'):
                    self.lbl_dps_val.config(text=f"{dps_val:.2f}")
                if hasattr(self, 'lbl_time_val'):
                    self.lbl_time_val.config(text=disp_dur, fg=dur_col)

            self.root.after(0, update_main_labels)
            
            total_time = time.time() - start_time
            if total_time > 0.5:
                print(f"DEBUG: Total analyze_log took {total_time:.3f}s")

        except FileNotFoundError as error:
            if manual:
                print(f"File Not Found: {error}")
        except ValueError as error:
            if manual:
                print(f"Invalid File: {error}")
        except PermissionError:
            if manual:
                print("Permission Error: The selected file could not be opened.")
        except Exception as error:
            if manual:
                print(f"An unexpected error occurred: {error}")
            else:
                print(f"Error in background analysis: {error}")

    def refresh_ui_only(self):
        """Refreshes the UI using already parsed events."""
        if not self.app_start_time:
            # If no combat session has started, we don't show any damage/DPS data
            self.process_events_for_ui([], all_events=self.all_events)
        else:
            events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
            self.process_events_for_ui(events, all_events=self.all_events)
        
        # Update Loot count on the label
        loot_count = sum(len(items) for items in self.loot_data.values())
        self.lbl_loot.config(text=f"LOOT ({loot_count})")

    def process_events_for_ui(self, events, manual=False, all_events=None):
        """Processes events and updates all UI components."""
        if all_events is None:
            all_events = events
        
        # Individual time windows
        now_dt = datetime.now()
        sk_window_ago = now_dt - timedelta(minutes=self.time_window_skimmers)
        dt_window_ago = now_dt - timedelta(minutes=self.time_window_details)
        
        # Update player data for Details window
        # Reset player data and loot for this UI refresh
        self.player_data = {}
        self.loot_data = {}
        self.inventory_full = False
        player_activity = {} # {name: last_active_time}

        # Process ALL events for loot (window history) and Details list (window activity)
        # But only count damage/healing for events in the filtered 'events' list (current session)
        event_ids = set(id(e) for e in events)

        for event in all_events:
            source_raw = event["source"].capitalize()
            source = "You" if source_raw.lower() == "you" else source_raw
            
            # Strengthened NPC detection
            is_source_npc = (
                " (" in source or 
                source.lower().startswith("a ") or 
                source.lower().startswith("an ") or
                source.lower() in ["your target", "that target", "mission terminal"] or
                source.startswith("[")
            )

            # Track activity for window filter (use detail window setting for Spy count)
            if not is_source_npc:
                if event["damage"] > 0 or event["healing"] > 0:
                    if event["timestamp"] and event["timestamp"] >= dt_window_ago:
                        if source not in player_activity or (not player_activity[source] or event["timestamp"] > player_activity[source]):
                            player_activity[source] = event["timestamp"]

            # Handle Loot events (window history regardless of app start)
            if str(event["type"]) == "loot":
                # Skip historical loot older than window
                if event["timestamp"] and event["timestamp"] < sk_window_ago:
                    continue
                    
                item = event.get("item", "")
                if "credits" not in item.lower():
                    if source not in self.loot_data:
                        self.loot_data[source] = []
                    self.loot_data[source].append({
                        "item": item,
                        "target": event["target"],
                        "timestamp": event["timestamp"]
                    })
                continue

            # Handle Inventory Full
            if str(event["type"]) == "inventory_full":
                if event["timestamp"] and event["timestamp"] >= sk_window_ago:
                    self.inventory_full = True
                    self.inventory_full_time = event["timestamp"]
                continue

            # Handle PvP Kill events
            if str(event["type"]) == "pvp_kill":
                now = datetime.now()
                lb_window_ago = now - timedelta(minutes=self.time_window_leaderboard)
                if event["timestamp"] and event["timestamp"] < lb_window_ago: # Use LB window for PVP kills too or share?
                    continue
                
                winner_raw = event["source"].capitalize()
                winner = "You" if winner_raw.lower() == "you" else winner_raw
                loser_raw = event["target"].capitalize()
                loser = "You" if loser_raw.lower() == "you" else loser_raw
                
                # Winner processing
                if winner not in self.player_data:
                    self.player_data[winner] = {"damage": 0, "healing": 0, "logs": [], "died": False, "death_time": None, "took_damage": False, "killing_blows": 0}
                self.player_data[winner]["killing_blows"] += 1
                
                ts_str = event["timestamp"].strftime("%H:%M:%S") if event["timestamp"] else "??:??:??"
                self.player_data[winner]["logs"].append({
                    "text": f"[{ts_str}] *** HAS BESTED {loser} ***",
                    "timestamp": event["timestamp"]
                })
                
                # Loser processing
                if loser not in self.player_data:
                    self.player_data[loser] = {"damage": 0, "healing": 0, "logs": [], "died": False, "death_time": None, "took_damage": False, "killing_blows": 0}
                self.player_data[loser]["died"] = True
                self.player_data[loser]["death_time"] = event["timestamp"]
                self.player_data[loser]["logs"].append({
                    "text": f"[{ts_str}] *** WAS BESTED BY {winner} ***",
                    "timestamp": event["timestamp"]
                })
                continue

        # Filter for last window for details
            if event["timestamp"] and event["timestamp"] < dt_window_ago:
                if id(event) not in event_ids: # Don't skip if it's part of current session
                    continue
            
            if not is_source_npc:
                if source not in self.player_data:
                    self.player_data[source] = {"damage": 0, "healing": 0, "logs": [], "died": False, "death_time": None, "took_damage": False, "killing_blows": 0}
                
                # Only add damage/healing if it's in the current session events
                if id(event) in event_ids:
                    self.player_data[source]["damage"] += event["damage"]
                    self.player_data[source]["healing"] += event["healing"]
            
            target_raw = event["target"].capitalize()
            target = "You" if target_raw.lower() == "you" else target_raw
            # Strengthened NPC detection
            is_target_npc = (
                " (" in target or 
                target.lower().startswith("a ") or 
                target.lower().startswith("an ") or
                target.lower() in ["your target", "that target", "mission terminal"] or
                target.startswith("[")
            )
            
            if event["damage"] > 0:
                if not is_target_npc:
                    if target not in self.player_data:
                        self.player_data[target] = {"damage": 0, "healing": 0, "logs": [], "died": False, "death_time": None, "took_damage": False, "killing_blows": 0}
                    self.player_data[target]["took_damage"] = True
                    
                    if target not in player_activity or (event["timestamp"] and (not player_activity[target] or event["timestamp"] > player_activity[target])):
                        player_activity[target] = event["timestamp"]

                if target in self.player_data:
                    ts_str_target = event["timestamp"].strftime("%H:%M:%S") if event["timestamp"] else "??:??:??"
                    self.player_data[target]["logs"].append({
                        "text": f"[{ts_str_target}] Taken {event['damage']:.0f} from {source}",
                        "timestamp": event["timestamp"]
                    })
            
            if event["healing"] > 0:
                if not is_target_npc:
                    if target not in self.player_data:
                        self.player_data[target] = {"damage": 0, "healing": 0, "logs": [], "died": False, "death_time": None, "took_damage": False, "killing_blows": 0}
                
                if target in self.player_data:
                    ts_str_target = event["timestamp"].strftime("%H:%M:%S") if event["timestamp"] else "??:??:??"
                    self.player_data[target]["logs"].append({
                        "text": f"[{ts_str_target}] Healed {event['healing']:.0f} by {source}",
                        "timestamp": event["timestamp"]
                    })

            ts_str = event["timestamp"].strftime("%H:%M:%S") if event["timestamp"] else "??:??:??"
            if event["healing"] > 0:
                action = "Healed"
            elif str(event["type"]) == "activity":
                if "has died" in event["raw"].lower():
                    action = "DIED"
                    if source in self.player_data:
                        self.player_data[source]["died"] = True
                        self.player_data[source]["death_time"] = event["timestamp"]
                else:
                    action = "Activity"
            elif "dealt" in str(event["type"]):
                action = "Hit"
            else:
                action = "Event"
            
            amount = event["healing"] if event["healing"] > 0 else event["damage"]
            log_entry = f"[{ts_str}] {action} {event['target']} for {amount:.0f}"
            if action == "DIED":
                log_entry = f"[{ts_str}] *** {source} HAS DIED ***"
            
            if source in self.player_data:
                self.player_data[source]["logs"].append({"text": log_entry, "timestamp": event["timestamp"]})

        # Update Spy label
        active_other_players = [
            p for p in self.player_data.keys() 
            if p.lower() != "you" and (
                self.player_data[p]["damage"] > 0 
                or self.player_data[p]["healing"] > 0 
                or self.player_data[p].get("died") 
                or self.player_data[p].get("killing_blows", 0) > 0
            )
        ]
        self.lbl_spy.config(text=f"SPY ({len(active_other_players)})")

        if self.details_window and self.details_window.winfo_exists():
            self.refresh_details_window()
        if self.leaderboard_window and self.leaderboard_window.winfo_exists():
            self.refresh_leaderboard_window()
        if self.skimmers_window and self.skimmers_window.winfo_exists():
            now_time = time.time()
            if manual or not hasattr(self, 'last_skimmers_refresh') or (now_time - self.last_skimmers_refresh > 10.0):
                self.refresh_skimmers_window(manual=manual)
                self.last_skimmers_refresh = now_time
        if self.damage_meter_window and self.damage_meter_window.winfo_exists():
            # Pass pre-filtered events to avoid re-calculating
            self.refresh_damage_meter_window(events=events)

        # Update Loot count on the label - Moved to main loop for periodic update
        pass

    def apply_snapping(self, window, x, y):
        """Adjust x, y coordinates to snap to edges of other windows."""
        win_width = window.winfo_width()
        win_height = window.winfo_height()
        
        # List of candidate windows to snap to
        candidates = []
        if self.root != window:
            candidates.append(self.root)
        if self.details_window and self.details_window.winfo_exists() and self.details_window != window:
            candidates.append(self.details_window)
        if self.leaderboard_window and self.leaderboard_window.winfo_exists() and self.leaderboard_window != window:
            candidates.append(self.leaderboard_window)
        if self.skimmers_window and self.skimmers_window.winfo_exists() and self.skimmers_window != window:
            candidates.append(self.skimmers_window)
        if self.damage_meter_window and self.damage_meter_window.winfo_exists() and self.damage_meter_window != window:
            candidates.append(self.damage_meter_window)
        if self.options_window and self.options_window.winfo_exists() and self.options_window != window:
            candidates.append(self.options_window)
            
        for target in candidates:
            tx = target.winfo_rootx()
            ty = target.winfo_rooty()
            tw = target.winfo_width()
            th = target.winfo_height()
            
            # Snap X: Left to Right, Right to Left, Left to Left, Right to Right
            # Check if within vertical overlap range for horizontal snapping
            if not (y + win_height < ty or y > ty + th):
                # Our Right to their Left
                if abs((x + win_width) - tx) < SNAP_THRESHOLD:
                    x = tx - win_width
                # Our Left to their Right
                elif abs(x - (tx + tw)) < SNAP_THRESHOLD:
                    x = tx + tw
                # Our Left to their Left
                elif abs(x - tx) < SNAP_THRESHOLD:
                    x = tx
                # Our Right to their Right
                elif abs((x + win_width) - (tx + tw)) < SNAP_THRESHOLD:
                    x = tx + tw - win_width
                    
            # Snap Y: Top to Bottom, Bottom to Top, Top to Top, Bottom to Bottom
            # Check if within horizontal overlap range for vertical snapping
            if not (x + win_width < tx or x > tx + tw):
                # Our Bottom to their Top
                if abs((y + win_height) - ty) < SNAP_THRESHOLD:
                    y = ty - win_height
                # Our Top to their Bottom
                elif abs(y - (ty + th)) < SNAP_THRESHOLD:
                    y = ty + th
                # Our Top to their Top
                elif abs(y - ty) < SNAP_THRESHOLD:
                    y = ty
                # Our Bottom to their Bottom
                elif abs((y + win_height) - (ty + th)) < SNAP_THRESHOLD:
                    y = ty + th - win_height
                    
        return x, y

    def show_skimmers_window(self):
        if self.skimmers_window and self.skimmers_window.winfo_exists():
            return

        self.skimmers_window = tk.Toplevel(self.root)
        self.skimmers_window.title("Skimmers")
        
        # Default size
        dw_width = SKIMMERS_DEFAULT_WIDTH
        dw_height = SKIMMERS_DEFAULT_HEIGHT
        
        # Try to load saved position/size
        saved_x = None
        saved_y = None
        if "SkimmersWindow" in self.config:
            saved_x = self.config["SkimmersWindow"].get("x", fallback=None)
            saved_y = self.config["SkimmersWindow"].get("y", fallback=None)
            dw_width = self.config["SkimmersWindow"].getint("width", fallback=SKIMMERS_DEFAULT_WIDTH)
            dw_height = self.config["SkimmersWindow"].getint("height", fallback=SKIMMERS_DEFAULT_HEIGHT)

        if saved_x is not None and saved_y is not None:
            win_x, win_y = saved_x, saved_y
        else:
            # Default Grid Position: Row 1, Col 1
            win_x, win_y = 50 + 460, 50 + 90
        
        self.skimmers_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
        self.skimmers_window.configure(bg=WINDOW_BG)
        self.skimmers_window.overrideredirect(True)
        self.skimmers_window.attributes("-alpha", 0.0)
        
        # Immediate alpha sync
        self.skimmers_window.attributes("-alpha", self.current_alpha)
        
        self.skimmers_window.bind("<Button-1>", self.click_window_skimmers)
        self.skimmers_window.bind("<B1-Motion>", self.drag_window_skimmers)
        
        border = tk.Frame(self.skimmers_window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        
        tk.Label(title_bar, text="SKIMMERS", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(side=tk.LEFT, padx=10)

        # Time toggles
        toggle_frame = tk.Frame(title_bar, bg=PANEL_DARK)
        toggle_frame.pack(side="left", padx=5)
        for mins in [10, 30, 60]:
            color = TEXT_PRIMARY if self.time_window_skimmers == mins else TEXT_SECONDARY
            lbl = tk.Label(toggle_frame, text=f"{mins}M", bg=PANEL_DARK, fg=color, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=2)
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, m=mins: self.set_time_window_skimmers(m))
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.on_close_skimmers())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        reset_btn = tk.Label(title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.reset_skimmers_manual())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(fg=TEXT_PRIMARY))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(fg=TEXT_SECONDARY))

        self.skimmers_container = tk.Frame(inner, bg=WINDOW_BG, padx=5, pady=5)
        self.skimmers_container.pack(fill=tk.BOTH, expand=True)

        # Resize handle
        self.skimmers_resize_handle = tk.Label(
            inner, 
            text="◢", 
            bg=WINDOW_BG, 
            fg=BORDER_HIGHLIGHT, 
            font=("Segoe UI", 10), 
            cursor="size_nw_se"
        )
        self.skimmers_resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.skimmers_resize_handle.bind("<Button-1>", lambda e: self.init_resize_popout(e, self.skimmers_window, SKIMMERS_DEFAULT_WIDTH, SKIMMERS_DEFAULT_HEIGHT))
        self.skimmers_resize_handle.bind("<B1-Motion>", lambda e: self.do_resize_popout(e, self.skimmers_window, SKIMMERS_DEFAULT_WIDTH, SKIMMERS_DEFAULT_HEIGHT))

        self.refresh_skimmers_window()

    def on_close_skimmers(self):
        if self.skimmers_window:
            self.save_config()
            self.skimmers_window.destroy()
            self.skimmers_window = None
            self.save_config()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        if hasattr(self, 'ontop_btn'):
            if self.always_on_top:
                self.ontop_btn.config(text="ONTOP: ON", fg=ACCENT_BLUE)
            else:
                self.ontop_btn.config(text="ONTOP: OFF", fg=TEXT_SECONDARY)
        
        # Reset the state tracking so the loop picks up the change immediately
        self._last_topmost_state = None
        
        # If we just turned it OFF and neither game nor app is in focus, hide immediately
        if not self.always_on_top:
            foreground_hwnd = user32.GetForegroundWindow()
            is_app_foreground = self.is_foreground_ours()
            is_target_foreground = (foreground_hwnd == self.target_hwnd) if self.target_hwnd else False
            
            if not is_target_foreground and not is_app_foreground:
                self.start_hide()
        
        # Run check logic once to apply changes immediately
        self.check_target_window_once()
        self.save_config()

    def check_target_window_once(self):
        # The main check_target_window loop runs every 500ms.
        # Calling it here will apply the new ONTOP state immediately.
        # We don't want to start another timer loop, so we just run the body once.
        # Since check_target_window is already a method that calls after(), 
        # we can just wait for the next tick, but users like immediate feedback.
        # We'll just reset _last_topmost_state and let the next 500ms tick handle it,
        # OR we can manually trigger it and handle the timer carefully.
        # Given the 500ms delay, it's usually fast enough.
        # But let's actually run the logic here once WITHOUT the timer part if possible,
        # but to keep it simple, setting _last_topmost_state = None is the most important part.
        pass

    def reset_skimmers_manual(self):
        self.loot_data = {}
        self.app_start_time = None
        self.last_combat_time = 0
        self.analyze_log(manual=True)
        self.refresh_skimmers_window()

    def refresh_skimmers_window(self, manual=False):
        if not self.skimmers_window or not self.skimmers_window.winfo_exists():
            return
            
        # Double-buffering to prevent flicker
        temp_container = tk.Frame(self.skimmers_container.master, bg=WINDOW_BG, padx=10, pady=10)
        old_container = self.skimmers_container
        self.skimmers_container = temp_container

        if self.current_skimmer_player:
            self.show_skimmer_drilldown(self.current_skimmer_player)
        else:
            # Show Inventory Full warning if applicable
            if self.inventory_full:
                full_frame = tk.Frame(self.skimmers_container, bg="#440000", pady=5)
                full_frame.pack(fill=tk.X, pady=(0, 5))
                tk.Label(full_frame, text="FULL INVENTORY", bg="#440000", fg="#ff4444", font=("Segoe UI", 10, "bold")).pack()
            self.show_skimmer_list()

        # Swap frames
        old_container.pack_forget()
        self.skimmers_container.pack(fill=tk.BOTH, expand=True)
        old_container.destroy()
        if hasattr(self, "skimmers_resize_handle"):
            pass

    def show_skimmer_list(self):
        if not self.loot_data:
            tk.Label(self.skimmers_container, text="No loot items recorded\nin the last 30 minutes.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(pady=20)
            return

        canvas = tk.Canvas(self.skimmers_container, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.skimmers_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=310)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        sorted_players = sorted(self.loot_data.keys(), key=lambda p: (p.lower() != "you", p))

        for p in sorted_players:
            p_btn = tk.Label(
                scrollable_frame, 
                text=p, 
                bg=PANEL_DARK, 
                fg="cyan" if p.lower() == "you" else TEXT_ACCENT, 
                font=self.font_title_obj, 
                anchor="w",
                padx=10,
                pady=8,
                cursor="hand2"
            )
            p_btn.pack(fill=tk.X, pady=(0, 2))
            p_btn.bind("<Button-1>", lambda e, name=p: self.drilldown_to_skimmer(name))
            
    def drilldown_to_skimmer(self, name):
        self.current_skimmer_player = name
        # Force an immediate refresh of the container when drilling down
        self.refresh_skimmers_window(manual=True)

    def show_skimmer_drilldown(self, name):
        # Header with back button
        header = tk.Frame(self.skimmers_container, bg=PANEL_DARK, pady=5)
        header.pack(fill=tk.X)
        
        back_btn = tk.Label(header, text="← BACK", bg=PANEL_DARK, fg=ACCENT_BLUE, font=self.font_small_obj, cursor="hand2", padx=10)
        back_btn.pack(side=tk.LEFT)
        back_btn.bind("<Button-1>", lambda e: self.go_back_to_skimmers())
        
        tk.Label(header, text=name, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=self.font_title_obj).pack(side=tk.LEFT, padx=10)

        if name not in self.loot_data:
            tk.Label(self.skimmers_container, text="No loot data found.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(pady=20)
            return

        canvas = tk.Canvas(self.skimmers_container, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.skimmers_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=310)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for entry in reversed(self.loot_data[name]):
            ts = entry["timestamp"].strftime("%H:%M:%S") if entry["timestamp"] else "??:??:??"
            item_frame = tk.Frame(scrollable_frame, bg=PANEL_BG, pady=5)
            item_frame.pack(fill=tk.X, pady=(0, 2))
            
            tk.Label(
                item_frame, 
                text=f"[{ts}] {entry['item']}", 
                bg=PANEL_BG, 
                fg=TEXT_PRIMARY, 
                font=self.font_small_obj, 
                anchor="w",
                wraplength=280,
                justify=tk.LEFT
            ).pack(fill=tk.X, padx=5)
            
            tk.Label(
                item_frame,
                text=f"  from {entry['target']}",
                bg=PANEL_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 8),
                anchor="w"
            ).pack(fill=tk.X, padx=5)

    def go_back_to_skimmers(self):
        self.current_skimmer_player = None
        # Force an immediate refresh to show the list again
        self.refresh_skimmers_window(manual=True)

    def click_window_skimmers(self, event):
        self._sk_offsetx = event.x
        self._sk_offsety = event.y

    def drag_window_skimmers(self, event):
        if not self.skimmers_window or not self.skimmers_window.winfo_exists():
            return
        x = self.skimmers_window.winfo_pointerx() - self._sk_offsetx
        y = self.skimmers_window.winfo_pointery() - self._sk_offsety
        x, y = self.apply_snapping(self.skimmers_window, x, y)
        self.skimmers_window.geometry(f"+{x}+{y}")

    def show_damage_meter_window(self):
        if self.damage_meter_window and self.damage_meter_window.winfo_exists():
            self.on_close_damage_meter()
            return

        self.damage_meter_window = tk.Toplevel(self.root)
        self.damage_meter_window.title("Damage Meter")
        
        # Default size
        dw_width = DAMAGE_METER_DEFAULT_WIDTH
        dw_height = DAMAGE_METER_DEFAULT_HEIGHT
        
        # Try to load saved position/size
        saved_x = None
        saved_y = None
        if "DamageMeterWindow" in self.config:
            saved_x = self.config["DamageMeterWindow"].get("x", fallback=None)
            saved_y = self.config["DamageMeterWindow"].get("y", fallback=None)
            dw_width = self.config["DamageMeterWindow"].getint("width", fallback=DAMAGE_METER_DEFAULT_WIDTH)
            dw_height = self.config["DamageMeterWindow"].getint("height", fallback=DAMAGE_METER_DEFAULT_HEIGHT)

        if saved_x is not None and saved_y is not None:
            win_x, win_y = saved_x, saved_y
        else:
            # Default Grid Position: Row 0, Col 1
            win_x, win_y = 50 + 460, 50
        
        self.damage_meter_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
        self.damage_meter_window.configure(bg=WINDOW_BG)
        self.damage_meter_window.overrideredirect(True)
        self.damage_meter_window.attributes("-alpha", 0.0)
        
        # Immediate alpha sync
        self.damage_meter_window.attributes("-alpha", self.current_alpha)
        
        self.damage_meter_window.bind("<Button-1>", self.click_window_damage_meter)
        self.damage_meter_window.bind("<B1-Motion>", self.drag_window_damage_meter)
        
        border = tk.Frame(self.damage_meter_window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        title_bar.bind("<Button-1>", self.click_window_damage_meter)
        title_bar.bind("<B1-Motion>", self.drag_window_damage_meter)
        
        tk.Label(title_bar, text="DAMAGE METER", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.on_close_damage_meter())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        reset_btn = tk.Label(title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.reset_damage_meter_manual())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(fg=TEXT_PRIMARY))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(fg=TEXT_SECONDARY))

        self.dm_container = tk.Frame(inner, bg=WINDOW_BG, padx=5, pady=5)
        self.dm_container.pack(fill=tk.BOTH, expand=True)
        self.dm_container.bind("<Button-1>", self.click_window_damage_meter)
        self.dm_container.bind("<B1-Motion>", self.drag_window_damage_meter)

        # Resize handle
        self.dm_resize_handle = tk.Label(
            inner, 
            text="◢", 
            bg=WINDOW_BG, 
            fg=BORDER_HIGHLIGHT, 
            font=("Segoe UI", 10), 
            cursor="size_nw_se"
        )
        self.dm_resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.dm_resize_handle.bind("<Button-1>", lambda e: self.init_resize_popout(e, self.damage_meter_window, DAMAGE_METER_DEFAULT_WIDTH, DAMAGE_METER_DEFAULT_HEIGHT))
        self.dm_resize_handle.bind("<B1-Motion>", lambda e: self.do_resize_popout(e, self.damage_meter_window, DAMAGE_METER_DEFAULT_WIDTH, DAMAGE_METER_DEFAULT_HEIGHT))

        self.refresh_damage_meter_window()

    def on_close_damage_meter(self):
        if self.damage_meter_window:
            self.save_config()
            self.damage_meter_window.destroy()
            self.damage_meter_window = None
            # Clear references
            self.dm_labels_created = False

    def reset_damage_meter_manual(self):
        self.leaderboard_data = {}
        # Manually reset start time
        self.app_start_time = None
        self.last_combat_time = 0
        self.analyze_log(manual=True)
        self.refresh_damage_meter_window()

    def refresh_damage_meter_window(self, events=None):
        if not self.damage_meter_window or not self.damage_meter_window.winfo_exists():
            return
        
        # Use provided events or re-calculate if none provided
        if events is None:
            if not self.app_start_time:
                # If no session started, show zero stats
                damage_dealt, damage_taken, dps, duration = 0, 0, 0, 0
                miss_count, hit_count, avoided_count, taken_count = 0, 0, 0, 0
            else:
                events = [e for e in self.all_events if e["timestamp"] and e["timestamp"] >= self.app_start_time]
                damage_dealt, damage_taken, dps, duration, miss_count, hit_count, avoided_count, taken_count = calculate_dps(events)
        else:
            damage_dealt, damage_taken, dps, duration, miss_count, hit_count, avoided_count, taken_count = calculate_dps(events)

        # Real-time duration ticking
        if self.last_combat_time > 0 and (time.time() - self.last_combat_time) < self.time_window_dm:
            # Combat is active or very recent
            if self.app_start_time:
                # Use our anchor for better stability
                anchor_ts = getattr(self, 'last_log_sync_time', self.app_start_time)
                time_since_sync = time.time() - self.last_combat_time
                
                # Project current time from anchor
                projected_now = anchor_ts + timedelta(seconds=time_since_sync)
                
                # Safety cap: Cannot project past actual system clock
                if projected_now > datetime.now():
                    projected_now = datetime.now()
                    
                live_now = projected_now
                live_duration = (live_now - self.app_start_time).total_seconds()
                if live_duration > duration:
                    duration = live_duration

        # MISS% calculation
        miss_percent = 0.0
        if (hit_count + miss_count) > 0:
            miss_percent = (miss_count / (hit_count + miss_count)) * 100

        # Recalculate DPS with finalized duration
        # ONLY if not paused, to prevent DPS from dropping during the timeout window
        is_paused = self.last_combat_time > 0 and (time.time() - self.last_combat_time) > self.time_window_dm
        if not is_paused:
            if duration > 0:
                dps = damage_dealt / duration
            else:
                dps = 0.0
        else:
            # When paused (recap), we should use the exact combat duration (first hit to last hit)
            # which is what calculate_dps returns as 'duration' before our live-ticker override
            # Let's re-calculate it or use the original duration
            _, _, dps, duration, _, _, _, _ = calculate_dps(events)

        # AVOIDANCE% calculation
        avoidance_percent = 0.0
        if taken_count > 0:
            avoidance_percent = (avoided_count / taken_count) * 100

        # Create UI components if they don't exist
        if not hasattr(self, 'dm_labels_created') or not self.dm_labels_created:
            # Clear container first
            for child in self.dm_container.winfo_children():
                child.destroy()
            
            # Configure grid
            self.dm_container.grid_columnconfigure(0, weight=1, minsize=140)
            self.dm_container.grid_columnconfigure(1, weight=1, minsize=140)
            for i in range(3):
                self.dm_container.grid_rowconfigure(i, weight=1)

            def create_dm_stat(row, col, title, initial_val, align="w"):
                frame = tk.Frame(self.dm_container, bg=PANEL_DARK, highlightthickness=1, highlightbackground=BORDER_HIGHLIGHT, padx=8, pady=5)
                frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
                
                # Make frame draggable
                frame.bind("<Button-1>", self.click_window_damage_meter)
                frame.bind("<B1-Motion>", self.drag_window_damage_meter)
                
                lbl_title = tk.Label(frame, text=title, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, anchor=align)
                lbl_title.pack(fill=tk.X)
                lbl_title.bind("<Button-1>", self.click_window_damage_meter)
                lbl_title.bind("<B1-Motion>", self.drag_window_damage_meter)
                
                lbl_val = tk.Label(frame, text=initial_val, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=self.font_stats_obj, anchor=align)
                lbl_val.pack(fill=tk.X)
                lbl_val.bind("<Button-1>", self.click_window_damage_meter)
                lbl_val.bind("<B1-Motion>", self.drag_window_damage_meter)
                
                return lbl_val

            self.dm_val_damage = create_dm_stat(0, 0, "DAMAGE", "0")
            self.dm_val_duration = create_dm_stat(0, 1, "DURATION", "0s", align="e")
            
            self.dm_val_dps = create_dm_stat(1, 0, "DPS", "0.00")
            self.dm_val_miss = create_dm_stat(1, 1, "MISS%", "0.0%", align="e")
            
            self.dm_val_taken = create_dm_stat(2, 0, "TAKEN", "0")
            self.dm_val_avoid = create_dm_stat(2, 1, "AVOIDANCE%", "0.0%", align="e")
            
            self.dm_labels_created = True

        # Update values
        if self.dm_labels_created:
            # Detect pause (> time_window_dm since last hit)
            is_paused = self.last_combat_time > 0 and (time.time() - self.last_combat_time) > self.time_window_dm
            
            # SUPERCEED: If we just received new damage events, we are not paused
            if events and any(e["damage"] > 0 for e in events):
                # Only if the latest event is very recent (this batch)
                latest_ts = max(e["timestamp"] for e in events if e["damage"] > 0 and e["timestamp"])
                if (datetime.now() - latest_ts).total_seconds() < self.time_window_dm:
                    is_paused = False

            stat_color = "cyan" if is_paused else TEXT_PRIMARY
            
            # If paused, we freeze the numbers (don't update from dps/damage_dealt)
            # This makes the DM a "recap" until combat resumes
            
            if hasattr(self, 'dm_val_damage') and self.dm_val_damage.winfo_exists():
                if not is_paused:
                    self.dm_val_damage.config(text=f"{damage_dealt:.0f}", fg=stat_color)
                else:
                    self.dm_val_damage.config(fg=stat_color)

            if hasattr(self, 'dm_val_duration') and self.dm_val_duration.winfo_exists():
                # Duration always updates or shows recap value
                display_val = f"{duration:.0f}s"
                
                # Pulse duration if > 0 and NOT in active combat/paused
                current_duration_color = stat_color
                if duration > 0 and self.last_combat_time == 0:
                    current_duration_color = "cyan" if self.pulse_state else "#AAAAAA"
                
                self.dm_val_duration.config(text=display_val, fg=current_duration_color)

            if hasattr(self, 'dm_val_dps') and self.dm_val_dps.winfo_exists():
                if not is_paused:
                    self.dm_val_dps.config(text=f"{dps:.2f}", fg=stat_color)
                else:
                    self.dm_val_dps.config(fg=stat_color)

            if hasattr(self, 'dm_val_miss') and self.dm_val_miss.winfo_exists():
                if not is_paused:
                    self.dm_val_miss.config(text=f"{miss_percent:.1f}%", fg=stat_color)
                else:
                    self.dm_val_miss.config(fg=stat_color)

            if hasattr(self, 'dm_val_taken') and self.dm_val_taken.winfo_exists():
                if not is_paused:
                    self.dm_val_taken.config(text=f"{damage_taken:.0f}", fg=stat_color)
                else:
                    self.dm_val_taken.config(fg=stat_color)

            if hasattr(self, 'dm_val_avoid') and self.dm_val_avoid.winfo_exists():
                if not is_paused:
                    self.dm_val_avoid.config(text=f"{avoidance_percent:.1f}%", fg=stat_color)
                else:
                    self.dm_val_avoid.config(fg=stat_color)
            
            # Explicitly update the window to prevent display lag
            self.damage_meter_window.update_idletasks()

        # Size enforcement
        if self.damage_meter_window.winfo_viewable():
            if self.damage_meter_window.winfo_width() < 300:
                self.damage_meter_window.geometry("300x220")
        else:
            self.damage_meter_window.update_idletasks()
            if self.damage_meter_window.winfo_width() < 300:
                self.damage_meter_window.geometry("300x220")

    def click_window_damage_meter(self, event):
        self._dm_offsetx = event.x
        self._dm_offsety = event.y

    def drag_window_damage_meter(self, event):
        if not self.damage_meter_window or not self.damage_meter_window.winfo_exists():
            return
        x = self.damage_meter_window.winfo_pointerx() - self._dm_offsetx
        y = self.damage_meter_window.winfo_pointery() - self._dm_offsety
        x, y = self.apply_snapping(self.damage_meter_window, x, y)
        self.damage_meter_window.geometry(f"+{x}+{y}")

    def show_leaderboard_window(self):
        if self.leaderboard_window and self.leaderboard_window.winfo_exists():
            self.on_close_leaderboard()
            return

        self.leaderboard_window = tk.Toplevel(self.root)
        self.leaderboard_window.title("Leaderboard")
        
        # Default size
        dw_width = LEADERBOARD_DEFAULT_WIDTH
        dw_height = LEADERBOARD_DEFAULT_HEIGHT
        
        # Try to load saved position/size
        saved_x = None
        saved_y = None
        if "LeaderboardWindow" in self.config:
            saved_x = self.config["LeaderboardWindow"].get("x", fallback=None)
            saved_y = self.config["LeaderboardWindow"].get("y", fallback=None)
            dw_width = self.config["LeaderboardWindow"].getint("width", fallback=LEADERBOARD_DEFAULT_WIDTH)
            dw_height = self.config["LeaderboardWindow"].getint("height", fallback=LEADERBOARD_DEFAULT_HEIGHT)

        if saved_x is not None and saved_y is not None:
            win_x, win_y = saved_x, saved_y
        else:
            # Default Grid Position: Row 1, Col 0
            win_x, win_y = 50 + 50, 50 + 90
        
        self.leaderboard_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
        self.leaderboard_window.configure(bg=WINDOW_BG)
        self.leaderboard_window.overrideredirect(True)
        self.leaderboard_window.attributes("-alpha", 0.0)
        
        # Ensure it's not topmost initially
        self.leaderboard_window.attributes("-topmost", False)
        hwnd = self.leaderboard_window.winfo_id()
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
        
        # Immediate alpha sync
        self.leaderboard_window.attributes("-alpha", self.current_alpha)
        
        # Border
        lb_border = tk.Frame(self.leaderboard_window, bg=BORDER_COLOR, padx=1, pady=1)
        lb_border.pack(fill="both", expand=True)
        
        inner = tk.Frame(lb_border, bg=WINDOW_BG)
        inner.pack(fill="both", expand=True)
        
        # Title Bar
        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill="x")
        title_bar.bind("<Button-1>", self.click_window_leaderboard)
        title_bar.bind("<B1-Motion>", self.drag_window_leaderboard)
        
        title_label = tk.Label(title_bar, text="LEADERBOARD", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj)
        title_label.pack(side="left", padx=10)
        title_label.bind("<Button-1>", self.click_window_leaderboard)
        title_label.bind("<B1-Motion>", self.drag_window_leaderboard)

        # Time toggles
        toggle_frame = tk.Frame(title_bar, bg=PANEL_DARK)
        toggle_frame.pack(side="left", padx=5)
        for mins in [10, 30, 60]:
            color = TEXT_PRIMARY if self.time_window_leaderboard == mins else TEXT_SECONDARY
            lbl = tk.Label(toggle_frame, text=f"{mins}M", bg=PANEL_DARK, fg=color, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=2)
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, m=mins: self.set_time_window_leaderboard(m))

        reset_btn = tk.Label(title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2")
        reset_btn.pack(side="left", padx=10)
        reset_btn.bind("<Button-1>", lambda e: self.reset_leaderboard_manual())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(fg="#ff4444"))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(fg=TEXT_SECONDARY))
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj, cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self.show_leaderboard_window())
        
        # Content
        self.lb_content = tk.Frame(inner, bg=WINDOW_BG, padx=5, pady=5)
        self.lb_content.pack(fill="both", expand=True)
        self.lb_content.bind("<Button-1>", self.click_window_leaderboard)
        self.lb_content.bind("<B1-Motion>", self.drag_window_leaderboard)
        
        # Resize handle
        self.lb_resize_handle = tk.Label(
            inner, 
            text="◢", 
            bg=WINDOW_BG, 
            fg=BORDER_HIGHLIGHT, 
            font=("Segoe UI", 10), 
            cursor="size_nw_se"
        )
        self.lb_resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.lb_resize_handle.bind("<Button-1>", lambda e: self.init_resize_popout(e, self.leaderboard_window, LEADERBOARD_DEFAULT_WIDTH, LEADERBOARD_DEFAULT_HEIGHT))
        self.lb_resize_handle.bind("<B1-Motion>", lambda e: self.do_resize_popout(e, self.leaderboard_window, LEADERBOARD_DEFAULT_WIDTH, LEADERBOARD_DEFAULT_HEIGHT))
        
        self.refresh_leaderboard_window()

        close_btn.bind("<Button-1>", lambda e: self.on_close_leaderboard())

    def on_close_leaderboard(self):
        if self.leaderboard_window:
            self.save_config()
            self.leaderboard_window.destroy()
            self.leaderboard_window = None

    def reset_leaderboard_manual(self):
        self.leaderboard_reset_time = datetime.now()
        self.leaderboard_data = {}
        self.analyze_log(manual=True)
        self.refresh_leaderboard_window()

    def refresh_leaderboard_window(self):
        if not self.leaderboard_window or not self.leaderboard_window.winfo_exists():
            return
            
        # Double-buffering to prevent flicker
        temp_content = tk.Frame(self.lb_content.master, bg=WINDOW_BG, padx=10, pady=10)
        old_content = self.lb_content
        self.lb_content = temp_content

        # Sort data
        sorted_players = sorted(self.leaderboard_data.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_players:
            lbl = tk.Label(self.lb_content, text="No combat data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj)
            lbl.pack(pady=20)
        else:
            for i, (name, damage) in enumerate(sorted_players):
                row = tk.Frame(self.lb_content, bg=WINDOW_BG)
                row.pack(fill="x", pady=2)
                row.bind("<Button-1>", self.click_window_leaderboard)
                row.bind("<B1-Motion>", self.drag_window_leaderboard)
                
                color = "cyan" if name == "You" else TEXT_PRIMARY
                
                rank_lbl = tk.Label(row, text=f"{i+1}.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj, width=3, anchor="w")
                rank_lbl.pack(side="left")
                rank_lbl.bind("<Button-1>", self.click_window_leaderboard)
                rank_lbl.bind("<B1-Motion>", self.drag_window_leaderboard)
                
                name_lbl = tk.Label(row, text=name, bg=WINDOW_BG, fg=color, font=self.font_small_obj, anchor="w")
                name_lbl.pack(side="left", fill="x", expand=True)
                name_lbl.bind("<Button-1>", self.click_window_leaderboard)
                name_lbl.bind("<B1-Motion>", self.drag_window_leaderboard)
                
                dmg_lbl = tk.Label(row, text=f"{damage:.0f}", bg=WINDOW_BG, fg=color, font=self.font_small_obj, anchor="e")
                dmg_lbl.pack(side="right")
                dmg_lbl.bind("<Button-1>", self.click_window_leaderboard)
                dmg_lbl.bind("<B1-Motion>", self.drag_window_leaderboard)

        # Swap frames
        old_content.pack_forget()
        self.lb_content.pack(fill="both", expand=True)
        old_content.destroy()
        if hasattr(self, "lb_resize_handle"):
            pass

    def show_details_window(self, force_open=False):
        if self.details_window and self.details_window.winfo_exists():
            if force_open:
                self.details_window.lift()
                return
            self.on_close_details()
            return

        self.details_window = tk.Toplevel(self.root)
        self.details_window.title("Livylogs Details")
        
        # Default size for details window
        dw_width = DETAILS_DEFAULT_WIDTH
        dw_height = DETAILS_DEFAULT_HEIGHT
        
        # Try to load saved position/size
        saved_x = None
        saved_y = None
        if "DetailsWindow" in self.config:
            saved_x = self.config["DetailsWindow"].get("x", fallback=None)
            saved_y = self.config["DetailsWindow"].get("y", fallback=None)
            dw_width = self.config["DetailsWindow"].getint("width", fallback=DETAILS_DEFAULT_WIDTH)
            dw_height = self.config["DetailsWindow"].getint("height", fallback=DETAILS_DEFAULT_HEIGHT)

        if saved_x is not None and saved_y is not None:
            win_x, win_y = saved_x, saved_y
        else:
            # Default Grid Position: Row 0, Col 2
            win_x, win_y = 50 + 460 + 310, 50
        
        self.details_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
        self.details_window.configure(bg=WINDOW_BG)
        self.details_window.overrideredirect(True) # Match theme
        self.details_window.attributes("-alpha", 0.0)
        
        # Immediate alpha sync
        self.details_window.attributes("-alpha", self.current_alpha)
        
        # Make it draggable
        self.details_window.bind("<Button-1>", self.click_window_details)
        self.details_window.bind("<B1-Motion>", self.drag_window_details)

        # Custom Border
        border = tk.Frame(self.details_window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        # Title Bar
        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        
        title_lbl = tk.Label(title_bar, text="PLAYER DETAILS", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj)
        title_lbl.pack(side=tk.LEFT, padx=10)

        # Time toggles
        toggle_frame = tk.Frame(title_bar, bg=PANEL_DARK)
        toggle_frame.pack(side="left", padx=5)
        for mins in [10, 30, 60]:
            color = TEXT_PRIMARY if self.time_window_details == mins else TEXT_SECONDARY
            lbl = tk.Label(toggle_frame, text=f"{mins}M", bg=PANEL_DARK, fg=color, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=2)
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, m=mins: self.set_time_window_details(m))
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.on_close_details())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        reset_btn = tk.Label(title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.reset_details_manual())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(fg=TEXT_PRIMARY))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(fg=TEXT_SECONDARY))

        self.details_container = tk.Frame(inner, bg=WINDOW_BG, padx=5, pady=5)
        self.details_container.pack(fill=tk.BOTH, expand=True)

        # Resize handle
        self.details_resize_handle = tk.Label(
            inner, 
            text="◢", 
            bg=WINDOW_BG, 
            fg=BORDER_HIGHLIGHT, 
            font=("Segoe UI", 10), 
            cursor="size_nw_se"
        )
        self.details_resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.details_resize_handle.bind("<Button-1>", lambda e: self.init_resize_popout(e, self.details_window, DETAILS_DEFAULT_WIDTH, DETAILS_DEFAULT_HEIGHT))
        self.details_resize_handle.bind("<B1-Motion>", lambda e: self.do_resize_popout(e, self.details_window, DETAILS_DEFAULT_WIDTH, DETAILS_DEFAULT_HEIGHT))

        self.current_detail_player = None
        self.refresh_details_window()

        close_btn.bind("<Button-1>", lambda e: self.on_close_details())

    def on_close_details(self):
        if self.details_window:
            self.save_config()
            self.details_window.destroy()
            self.details_window = None

    def reset_details_manual(self):
        self.player_data = {}
        self.app_start_time = None
        self.last_combat_time = 0
        self.analyze_log(manual=True)
        self.refresh_details_window()

    def set_time_window_details(self, mins):
        self.time_window_details = mins
        self.save_config()
        self.analyze_log(manual=True)
        if self.details_window and self.details_window.winfo_exists():
            self.refresh_details_window()

    def set_time_window_leaderboard(self, mins):
        self.time_window_leaderboard = mins
        self.save_config()
        self.analyze_log(manual=True)
        if self.leaderboard_window and self.leaderboard_window.winfo_exists():
            self.refresh_leaderboard_window()

    def set_time_window_skimmers(self, mins):
        self.time_window_skimmers = mins
        self.save_config()
        self.analyze_log(manual=True)
        if self.skimmers_window and self.skimmers_window.winfo_exists():
            self.show_skimmers_window()
            self.show_skimmers_window()

    def click_window_details(self, event):
        self._dw_offsetx = event.x
        self._dw_offsety = event.y

    def drag_window_details(self, event):
        if not self.details_window or not self.details_window.winfo_exists():
            return
        x = self.details_window.winfo_pointerx() - self._dw_offsetx
        y = self.details_window.winfo_pointery() - self._dw_offsety
        x, y = self.apply_snapping(self.details_window, x, y)
        self.details_window.geometry(f"+{x}+{y}")

    def click_window_leaderboard(self, event):
        self._lb_offsetx = event.x
        self._lb_offsety = event.y

    def drag_window_leaderboard(self, event):
        if not self.leaderboard_window or not self.leaderboard_window.winfo_exists():
            return
        x = self.leaderboard_window.winfo_pointerx() - self._lb_offsetx
        y = self.leaderboard_window.winfo_pointery() - self._lb_offsety
        x, y = self.apply_snapping(self.leaderboard_window, x, y)
        self.leaderboard_window.geometry(f"+{x}+{y}")

    def refresh_details_window(self):
        if not self.details_window or not self.details_window.winfo_exists():
            return
        
        # Update player data summary to check if we actually need a full refresh
        active_players = [
            p for p in self.player_data 
            if self.player_data[p]["damage"] > 0 
            or self.player_data[p]["healing"] > 0 
            or self.player_data[p].get("died") 
            or self.player_data[p].get("killing_blows", 0) > 0
        ]
        current_data_summary = str(sorted([(p, self.player_data[p]["damage"], self.player_data[p]["healing"], self.player_data[p].get("died")) for p in active_players]))
        if hasattr(self, "_last_details_data") and self._last_details_data == current_data_summary and hasattr(self, "_last_details_view") and self._last_details_view == self.current_detail_player:
            return
        
        self._last_details_data = current_data_summary
        self._last_details_view = self.current_detail_player

        # Update current view
        if self.current_detail_player:
            if self.current_detail_player.startswith("DEATH_RECAP:"):
                player_name = self.current_detail_player.split(":", 1)[1]
                self.show_player_death_recap(player_name)
            else:
                self.show_player_drilldown(self.current_detail_player)
        else:
            self.show_player_list()

        if hasattr(self, "details_resize_handle"):
            pass

    def show_player_list(self):
        # Clear container
        for child in self.details_container.winfo_children():
            child.destroy()

        # Sort and filter players: only those with damage, healing, kills, or who died
        all_players = list(self.player_data.keys())
        players = [
            p for p in all_players 
            if self.player_data[p]["damage"] > 0 
            or self.player_data[p]["healing"] > 0 
            or self.player_data[p].get("died") 
            or self.player_data[p].get("killing_blows", 0) > 0
        ]
        players.sort(key=lambda p: (p.lower() != "you", -self.player_data[p]["damage"]))

        # Header
        header = tk.Frame(self.details_container, bg=PANEL_DARK, pady=5)
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text="PLAYER", bg=PANEL_DARK, fg=TEXT_ACCENT, font=self.font_small_obj, width=18, anchor="w").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="DAMAGE", bg=PANEL_DARK, fg=TEXT_ACCENT, font=self.font_small_obj, width=10).pack(side=tk.LEFT)
        tk.Label(header, text="HEALING", bg=PANEL_DARK, fg=TEXT_ACCENT, font=self.font_small_obj, width=10).pack(side=tk.LEFT)

        # List with scrollbar
        canvas = tk.Canvas(self.details_container, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for p in players:
            row = tk.Frame(scrollable_frame, bg=PANEL_BG, pady=2)
            row.pack(fill=tk.X, pady=1)
            
            p_lbl = tk.Label(row, text=p, bg=PANEL_BG, fg=TEXT_PRIMARY, font=self.font_small_obj, width=18, anchor="w", cursor="hand2")
            p_lbl.pack(side=tk.LEFT, padx=5)
            p_lbl.bind("<Button-1>", lambda e, name=p: self.drilldown_to_player(name))
            p_lbl.bind("<Enter>", lambda e, l=p_lbl: l.config(fg=TEXT_ACCENT))
            p_lbl.bind("<Leave>", lambda e, l=p_lbl: l.config(fg=TEXT_PRIMARY))

            # Skull icon and Killing Blow icon for qualified players
            is_active = self.player_data[p].get("took_damage") or self.player_data[p].get("damage") > 0 or self.player_data[p].get("healing") > 0
            
            if self.player_data[p].get("died") and is_active:
                skull_lbl = tk.Label(row, text="💀", bg=PANEL_BG, fg="#ff4444", font=self.font_small_obj, cursor="hand2")
                skull_lbl.pack(side=tk.LEFT)
                skull_lbl.bind("<Button-1>", lambda e, name=p: self.show_death_recap(name))
            
            if self.player_data[p].get("killing_blows", 0) > 0 and is_active:
                kb_lbl = tk.Label(row, text="⚔️", bg=PANEL_BG, fg="#ffaa00", font=self.font_small_obj)
                kb_lbl.pack(side=tk.LEFT, padx=(2, 0))

            tk.Label(row, text=f"{self.player_data[p]['damage']:.0f}", bg=PANEL_BG, fg=TEXT_SECONDARY, font=self.font_small_obj, width=10).pack(side=tk.LEFT)
            tk.Label(row, text=f"{self.player_data[p]['healing']:.0f}", bg=PANEL_BG, fg=TEXT_SECONDARY, font=self.font_small_obj, width=10).pack(side=tk.LEFT)

    def show_death_recap(self, name):
        self.current_detail_player = f"DEATH_RECAP:{name}"
        self.refresh_details_window()

    def show_player_death_recap(self, name):
        # Clear container
        for child in self.details_container.winfo_children():
            child.destroy()

        header = tk.Frame(self.details_container, bg=PANEL_DARK, pady=5)
        header.pack(fill=tk.X, pady=(0, 5))
        
        back_btn = tk.Label(header, text=" ◀ BACK ", bg=BUTTON_BG, fg=TEXT_PRIMARY, font=self.font_small_obj, cursor="hand2", padx=5)
        back_btn.pack(side=tk.LEFT, padx=5)
        back_btn.bind("<Button-1>", lambda e: self.go_back_to_list())
        
        tk.Label(header, text=f"DEATH RECAP (30s): {name}", bg=PANEL_DARK, fg="#ff4444", font=self.font_small_obj).pack(side=tk.LEFT, padx=10)

        canvas = tk.Canvas(self.details_container, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        player_info = self.player_data.get(name, {})
        logs = player_info.get("logs", [])
        death_time = player_info.get("death_time")
        
        if death_time:
            thirty_secs_before = death_time - timedelta(seconds=30)
            filtered_logs = [l for l in logs if isinstance(l, dict) and l["timestamp"] and thirty_secs_before <= l["timestamp"] <= death_time]
            
            for log in reversed(filtered_logs):
                tk.Label(scrollable_frame, text=log["text"], bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj, anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=5)
        else:
            tk.Label(scrollable_frame, text="No death timestamp found.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(padx=10, pady=10)

    def drilldown_to_player(self, name):
        self.current_detail_player = name
        self.refresh_details_window()

    def show_player_drilldown(self, name):
        # Clear container
        for child in self.details_container.winfo_children():
            child.destroy()

        # Header with Back Arrow
        header = tk.Frame(self.details_container, bg=PANEL_DARK, pady=5)
        header.pack(fill=tk.X, pady=(0, 5))
        
        back_btn = tk.Label(header, text=" ◀ BACK ", bg=BUTTON_BG, fg=TEXT_PRIMARY, font=self.font_small_obj, cursor="hand2", padx=5)
        back_btn.pack(side=tk.LEFT, padx=5)
        back_btn.bind("<Button-1>", lambda e: self.go_back_to_list())
        
        tk.Label(header, text=f"LOGS: {name}", bg=PANEL_DARK, fg=TEXT_ACCENT, font=self.font_small_obj).pack(side=tk.LEFT, padx=10)

        # Logs list
        canvas = tk.Canvas(self.details_container, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        logs = self.player_data.get(name, {}).get("logs", [])
        for log in reversed(logs): # Show newest at top
            text = log["text"] if isinstance(log, dict) else log
            tk.Label(scrollable_frame, text=text, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj, anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=5)

    def go_back_to_list(self):
        self.current_detail_player = None
        self.refresh_details_window()

    def drag_window(self, event):
        x = self.root.winfo_pointerx() - self._offsetx
        y = self.root.winfo_pointery() - self._offsety
        x, y = self.apply_snapping(self.root, x, y)
        self.root.geometry(f"+{x}+{y}")

    def click_window(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def init_resize_popout(self, event, window, def_w, def_h):
        self._start_x = window.winfo_pointerx()
        self._start_y = window.winfo_pointery()
        self._start_width = window.winfo_width()
        self._start_height = window.winfo_height()
        return "break"

    def do_resize_popout(self, event, window, def_w, def_h):
        dx = window.winfo_pointerx() - self._start_x
        dy = window.winfo_pointery() - self._start_y
        
        min_w = int(def_w * 0.3)
        min_h = int(def_h * 0.3)
        
        new_width = max(min_w, self._start_width + dx)
        new_height = max(min_h, self._start_height + dy)
        
        window.geometry(f"{new_width}x{new_height}")
        window.update()
        return "break"

    def init_resize(self, event):
        self._start_x = self.root.winfo_pointerx()
        self._start_y = self.root.winfo_pointery()
        self._start_width = self.root.winfo_width()
        self._start_height = self.root.winfo_height()
        return "break"

    def do_resize(self, event):
        dx = self.root.winfo_pointerx() - self._start_x
        dy = self.root.winfo_pointery() - self._start_y
        
        new_width = max(MIN_WIDTH, self._start_width + dx)
        new_height = max(MIN_HEIGHT, self._start_height + dy)
        
        self.root.geometry(f"{new_width}x{new_height}")
        self.root.update_idletasks()  # Force OS to update window geometry immediately
        
        # Throttle font scaling to reduce jerkiness
        current_time = time.time()
        if current_time - self.last_ui_update_time > self.ui_update_delay:
            self.update_font_scaling(new_width, new_height, refresh_menu=False)
            self.last_ui_update_time = current_time
            
        return "break"

    def update_font_scaling(self, width, height, refresh_menu=True):
        """Dynamically updates font sizes based on window dimensions."""
        # Update version label to 1.0
        self.lbl_version.config(text="1.0")
        
        # Base scale on a combination of width and height
        scale = min(width / 350, height / 300)
        self.current_scale_factor = scale
        
        # Scale fonts but keep within reasonable limits
        size_stats = int(20 * scale)
        size_stats = max(12, min(48, size_stats))
        
        size_title = int(10 * scale)
        size_title = max(8, min(16, size_title))
        
        size_small = int(9 * scale)
        size_small = max(7, min(12, size_small))

        size_button = int(10 * scale)
        size_button = max(8, min(14, size_button))
        
        self.font_stats_obj.configure(size=size_stats)
        self.font_title_obj.configure(size=size_title)
        self.font_small_obj.configure(size=size_small)
        self.font_button_obj.configure(size=size_button)

        # Refresh menu if open and requested
        if refresh_menu and hasattr(self, 'options_window') and self.options_window:
            # Efficiently update the menu without full destruction if possible
            # But since many things like padding depend on scale, a redraw is safer but slow.
            # We'll use update_idletasks to ensure it doesn't block too long
            self.root.after_idle(self._safe_refresh_menu)

    def _safe_refresh_menu(self):
        if hasattr(self, 'options_window') and self.options_window:
            self.toggle_menu()
            self.toggle_menu()

    def save_size(self, event):
        # Final update to fonts to ensure everything is perfect after resizing ends
        self.update_font_scaling(self.root.winfo_width(), self.root.winfo_height(), refresh_menu=True)
        
        if "General" not in self.config:
            self.config["General"] = {}
        self.config["General"]["width"] = str(self.root.winfo_width())
        self.config["General"]["height"] = str(self.root.winfo_height())
        try:
            with open("settings.ini", "w", encoding="utf-8") as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error saving window size: {e}")

    def toggle_menu(self):
        if self.options_window and self.options_window.winfo_exists():
            self.on_close_options()
            return

        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Settings")
        self.options_window.configure(bg=WINDOW_BG)
        self.options_window.overrideredirect(True)
        
        # Initial state: not topmost until we confirm focus
        if not hasattr(self, "_last_topmost_state"):
            self._last_topmost_state = False
        
        # Calculate position below the main window
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        width = 200
        height = 160
        
        # Center horizontally relative to main window and place below bottom border
        spawn_x = root_x + (root_width // 2) - (width // 2)
        spawn_y = root_y + root_height + 5
        
        self.options_window.geometry(f"{width}x{height}+{spawn_x}+{spawn_y}")
        
        # Border
        border = tk.Frame(self.options_window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        # Title Bar (Small)
        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=20)
        title_bar.pack(fill=tk.X)
        
        tk.Label(title_bar, text="SETTINGS", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.on_close_options())
        
        content = tk.Frame(inner, bg=WINDOW_BG, padx=10, pady=10)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Select Log Button
        btn_log = tk.Button(
            content, text="SELECT LOG FILE", 
            bg=BUTTON_BG, fg=TEXT_PRIMARY, 
            relief=tk.FLAT, font=self.font_small_obj,
            command=lambda: [self.on_close_options(), self.change_log_path()],
            activebackground=BUTTON_HOVER,
            activeforeground=TEXT_ACCENT,
            cursor="hand2"
        )
        btn_log.pack(fill=tk.X, pady=(0, 10))

        # Disable Warnings Checkbox
        def toggle_warnings():
            if "General" not in self.config:
                self.config["General"] = {}
            self.config["General"]["disable_warnings"] = str(self.disable_warnings.get())
            self.save_config()

        cb_warnings = tk.Checkbutton(
            content, text="DISABLE WARNINGS",
            variable=self.disable_warnings,
            onvalue=True, offvalue=False,
            bg=WINDOW_BG, fg=TEXT_SECONDARY,
            selectcolor=PANEL_DARK,
            activebackground=WINDOW_BG,
            activeforeground=TEXT_PRIMARY,
            font=self.font_small_obj,
            command=toggle_warnings,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        cb_warnings.pack(fill=tk.X, pady=(0, 5))

        # Opacity Slider - Custom Styled
        tk.Label(content, text="OPACITY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(pady=(5, 0))
        
        current_alpha = self.root.attributes("-alpha")
        if current_alpha is None: current_alpha = 1.0
        
        def update_alpha(v):
            alpha = float(v)/100.0
            self.target_alpha = alpha
            self.current_alpha = alpha
            self.root.attributes("-alpha", alpha)
            if "General" not in self.config:
                self.config["General"] = {}
            self.config["General"]["transparency"] = str(alpha)

        # Themed Slider Container
        slider_frame = tk.Frame(content, bg=WINDOW_BG, pady=5)
        slider_frame.pack(fill=tk.X)
        
        # Customizing the Scale to look cleaner
        slider = tk.Scale(
            slider_frame,
            from_=10, to=100,
            orient=tk.HORIZONTAL,
            bg=BORDER_HIGHLIGHT, # Brighter indicator
            fg=TEXT_SECONDARY,
            troughcolor=PANEL_DARK,
            highlightthickness=0,
            activebackground=ACCENT_BLUE,
            font=("Segoe UI", 7),
            command=update_alpha,
            showvalue=False,
            width=10, # Thickness of the slider
            length=180,
            borderwidth=0,
            relief=tk.FLAT,
            sliderlength=15,
            sliderrelief=tk.FLAT,
            highlightbackground=BORDER_COLOR
        )
        slider.set(int(current_alpha * 100))
        slider.pack(fill=tk.X)
        
        # Percentage indicator
        percent_label = tk.Label(content, text=f"{int(current_alpha * 100)}%", bg=WINDOW_BG, fg=TEXT_ACCENT, font=("Segoe UI", 8))
        percent_label.pack()
        
        # Hook into slider to update percent label
        def on_slider_move(v):
            update_alpha(v)
            percent_label.config(text=f"{int(float(v))}%")
            
        slider.config(command=on_slider_move)

    def show_options_window(self):
        if self.options_window and self.options_window.winfo_exists():
            self.options_window.focus_force()
            return

        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        
        # Default size
        dw_width = 250
        dw_height = 200
        
        # Try to load saved position/size
        saved_x = None
        saved_y = None
        if "OptionsWindow" in self.config:
            saved_x = self.config["OptionsWindow"].get("x", fallback=None)
            saved_y = self.config["OptionsWindow"].get("y", fallback=None)
            dw_width = self.config["OptionsWindow"].getint("width", fallback=250)
            dw_height = self.config["OptionsWindow"].getint("height", fallback=200)

        if saved_x is not None and saved_y is not None:
            win_x, win_y = saved_x, saved_y
        else:
            # Default Grid Position: Snap to damage meter if possible, else below Main
            if self.damage_meter_window and self.damage_meter_window.winfo_exists():
                self.damage_meter_window.update_idletasks()
                win_x = self.damage_meter_window.winfo_x()
                win_y = self.damage_meter_window.winfo_y()
                dw_width = self.damage_meter_window.winfo_width()
                dw_height = self.damage_meter_window.winfo_height()
                self.options_window.overrideredirect(True)
                self.options_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
                self.options_window.update()
            else:
                win_x, win_y = 50, 50 + 90 + 410 # Below Leaderboard
        
        self.options_window.geometry(f"{dw_width}x{dw_height}+{win_x}+{win_y}")
        self.options_window.configure(bg=WINDOW_BG)
        self.options_window.overrideredirect(True)
        self.options_window.attributes("-alpha", 0.0)
        
        # Immediate alpha sync
        self.options_window.attributes("-alpha", self.current_alpha)
        
        self.options_window.bind("<Button-1>", self.click_window_options)
        self.options_window.bind("<B1-Motion>", self.drag_window_options)
        
        # Disable automatic resizing of window to content
        self.options_window.pack_propagate(False)
        
        border = tk.Frame(self.options_window, bg=BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)
        
        inner = tk.Frame(border, bg=WINDOW_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(inner, bg=PANEL_DARK, height=30)
        title_bar.pack(fill=tk.X)
        title_bar.bind("<Button-1>", self.click_window_options)
        title_bar.bind("<B1-Motion>", self.drag_window_options)
        
        tk.Label(title_bar, text="OPTIONS", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=self.font_small_obj).pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Label(title_bar, text="✕", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12), cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.on_close_options())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_SECONDARY))

        content = tk.Frame(inner, bg=WINDOW_BG, padx=10, pady=5)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Log File Button
        btn_log = tk.Button(
            content, text="SELECT LOG FILE", 
            bg=BUTTON_BG, fg=TEXT_PRIMARY, 
            relief=tk.FLAT, font=self.font_button_obj,
            command=self.change_log_path,
            activebackground=BUTTON_HOVER,
            activeforeground=TEXT_ACCENT
        )
        btn_log.pack(fill=tk.X, pady=(0, 10))

        # Opacity Slider
        tk.Label(content, text="OPACITY", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=self.font_small_obj).pack()
        
        current_alpha = self.root.attributes("-alpha")
        if current_alpha is None: current_alpha = 1.0
        
        def update_alpha(v):
            alpha = float(v)/100.0
            self.target_alpha = alpha
            self.current_alpha = alpha
            self.root.attributes("-alpha", alpha)
            if "General" not in self.config:
                self.config["General"] = {}
            self.config["General"]["transparency"] = str(alpha)
            
        slider = tk.Scale(
            content,
            from_=10, to=100,
            orient=tk.HORIZONTAL,
            bg=WINDOW_BG,
            fg=TEXT_PRIMARY,
            troughcolor=ENTRY_BG,
            highlightthickness=0,
            activebackground=ACCENT_BLUE,
            font=self.font_small_obj,
            command=update_alpha
        )
        slider.set(int(current_alpha * 100))
        slider.pack(fill=tk.X, pady=(0, 10))

        # Reset Stats Button
        btn_reset_data = tk.Button(
            content, text="RESET DATA",
            bg=BUTTON_BG, fg="#ff4444",
            relief=tk.FLAT, font=self.font_button_obj,
            command=self.reset_data,
            activebackground=BUTTON_HOVER,
            activeforeground="#ff6666"
        )
        btn_reset_data.pack(fill=tk.X, pady=(10, 0))

        # Reset Settings Button
        btn_reset_settings = tk.Button(
            content, text="RESET SETTINGS",
            bg=BUTTON_BG, fg="#ff4444",
            relief=tk.FLAT, font=self.font_button_obj,
            command=self.reset_settings,
            activebackground=BUTTON_HOVER,
            activeforeground="#ff6666"
        )
        btn_reset_settings.pack(fill=tk.X, pady=(5, 0))

        self.options_window.focus_force()

    def reset_data(self):
        self.player_data = {}
        self.all_events = []
        self.last_read_offset = 0
        self.app_start_time = None
        self.last_combat_time = 0 # Reset anchor as well
        self.last_log_sync_time = None
        self.analyze_log(manual=True)
        if self.options_window:
            self.on_close_options()

    def reset_settings(self):
        # Reset config to empty
        self.config = ConfigParser()
        
        # Delete settings.ini if it exists
        if os.path.exists("settings.ini"):
            try:
                os.remove("settings.ini")
            except Exception as e:
                print(f"Error deleting settings.ini: {e}")
        
        # Reset local variables to defaults
        self.disable_warnings.set(False)
        self.target_alpha = 1.0
        self.current_alpha = 1.0
        self.root.attributes("-alpha", 1.0)
        
        # Refresh UI or close options
        if self.options_window:
            self.on_close_options()
        
        # Re-initialize what we can or just let the next save_config handle it
        # ThemedMessagebox.showinfo(self.root, "Settings Reset", "Settings have been reset to defaults.\nPositions will be reset on next launch.")
        print("Settings have been reset to defaults.")

    def on_close_options(self):
        if self.options_window:
            self.save_config()
            self.options_window.destroy()
            self.options_window = None

    def click_window_options(self, event):
        self._opt_offsetx = event.x
        self._opt_offsety = event.y

    def drag_window_options(self, event):
        if not self.options_window or not self.options_window.winfo_exists():
            return
        x = self.options_window.winfo_pointerx() - self._opt_offsetx
        y = self.options_window.winfo_pointery() - self._opt_offsety
        x, y = self.apply_snapping(self.options_window, x, y)
        self.options_window.geometry(f"+{x}+{y}")

    def change_log_path(self, suppress_notice=False):
        initial_dir = "."
        current_path = self.file_path_var.get()
        if current_path:
            p = Path(current_path)
            if p.is_dir() and p.exists():
                initial_dir = str(p)
            elif p.parent.exists():
                initial_dir = str(p.parent)

        file_path = filedialog.askopenfilename(
            title="Select Log File",
            initialdir=initial_dir,
            filetypes=[
                ("Text files", "*.txt"),
                ("Log files", "*.log"),
                ("All files", "*.*"),
            ],
            defaultextension=".txt"
        )

        if file_path:
            # Check if file exists before proceeding
            if not Path(file_path).exists():
                print(f"The selected file does not exist: {file_path}")
                return

            file_path = str(Path(file_path).absolute())
            self.file_path_var.set(file_path)

            if "General" not in self.config:
                self.config["General"] = {}

            self.config["General"]["log_path"] = file_path
            self.config["General"]["disable_warnings"] = str(self.disable_warnings.get())

            try:
                with open("settings.ini", "w", encoding="utf-8") as configfile:
                    self.config.write(configfile)
            except Exception as e:
                print(f"Error saving settings: {e}")
            
            # Show character log warning
            # if not self.disable_warnings.get() and not suppress_notice:
            #     self.play_sound()
            #     notice_text = "Each character has a unique log file.\nPlease ensure you select the correct one.\nThe app will only show on the first opened client"
            #     ThemedMessagebox.showinfo(self.root, "Notice", notice_text)
            
            # Automatically analyze when log changes in a background thread to prevent UI freezing
            self.app_start_time = None
            threading.Thread(target=lambda: self.analyze_log(manual=True), daemon=True).start()


if __name__ == "__main__":
    # Ensure only one instance is running
    # Create a named mutex
    kernel32 = ctypes.windll.kernel32
    mutex_name = "LivyLogs_SingleInstance_Mutex"
    
    # CreateMutexW returns a handle to the mutex
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        # Already running
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showwarning("LivyLogs", "Another instance of LivyLogs is already running.")
        temp_root.destroy()
        sys.exit(0)

    try:
        root = tk.Tk()
        app = CombatLogApp(root)
        print("DEBUG: Entering mainloop")
        root.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to standard messagebox if possible
        try:
            messagebox.showerror("LivyLogs Critical Error", f"The application encountered a critical error:\n{e}\n\nPlease check the console for details.")
        except:
            pass
    finally:
        # Release the mutex handle when the app closes
        if mutex:
            kernel32.CloseHandle(mutex)