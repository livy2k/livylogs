1234
import tkinter as tk
from windows.base_window import BasePopoutWindow
import pyautogui
import json
import uuid
import jsonschema
import base64
import zlib
from jsonschema import validate
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import pyperclip
import tkinter.simpledialog as simpledialog
from PIL import Image, ImageTk
import os
import re
import random
import requests
from utils import get_resource_path
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_PRIMARY, TEXT_SECONDARY, 
    ACCENT_RED, BUTTON_BG, BUTTON_HOVER, ACCENT_BLUE
)
try:
    import pytesseract
except ImportError:
    pytesseract = None

if pytesseract:
    # Prioritize bundled tesseract, then common Windows paths
    tesseract_paths = [
        # For frozen apps, the bin/ folder is at the root of the distribution
        get_resource_path(os.path.join("bin", "tesseract", "tesseract.exe")),
        get_resource_path(os.path.join("bin", "tesseract", "tesseract")),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        # In case the user placed it relative to the script in dev
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin", "tesseract", "tesseract.exe"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin", "tesseract", "tesseract")
    ]
    for p in tesseract_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "weapon_type": {"type": "string"},
        "speed": {"type": "number"},
        "range_zero": {"type": "number"},
        "range_mid": {"type": "number"},
        "range_max": {"type": "number"},
        "acc_zero": {"type": "number"},
        "acc_mid": {"type": "number"},
        "acc_max": {"type": "number"},
        "damage_min": {"type": "number"},
        "damage_max": {"type": "number"},
        "wound_chance": {"type": "number"},
        "armor_piercing": {"type": "string"},
        "damage_type": {"type": "string"},
        "health_cost": {"type": "number"},
        "action_cost": {"type": "number"},
        "mind_cost": {"type": "number"},
        "item_type": {"type": "string"},
        "component_type": {"type": "string"},
        "mod_damage_min": {"type": "number"},
        "mod_damage_max": {"type": "number"},
        "mod_speed": {"type": "number"},
        "mod_accuracy": {"type": "number"},
        "mod_effectiveness": {"type": "number"},
        "condition": {"type": "number"},
        "max_condition": {"type": "number"},
        "armor_rating": {"type": "string"},
        "effectiveness": {"type": "number"},
        "kinetic": {"type": "number"},
        "energy": {"type": "number"},
        "blast": {"type": "number"},
        "stun": {"type": "number"},
        "heat": {"type": "number"},
        "cold": {"type": "number"},
        "acid": {"type": "number"},
        "electricity": {"type": "number"},
        "environmental": {"type": "number"},
        "skill_mods": {"type": "object"},
        "use_count": {"type": "number"},
        "resource_class": {"type": "string"},
        "cold_resistance": {"type": "number"},
        "conductivity": {"type": "number"},
        "decay_resistance": {"type": "number"},
        "entangle_resistance": {"type": "number"},
        "flavor": {"type": "number"},
        "heat_resistance": {"type": "number"},
        "malleability": {"type": "number"},
        "potential_energy": {"type": "number"},
        "overall_quality": {"type": "number"},
        "shock_resistance": {"type": "number"},
        "unit_toughness": {"type": "number"},
        "is_sliced": {"type": "boolean"},
        "has_powerup": {"type": "boolean"},
        "powerup_stats": {"type": "object"}
    },
    "required": ["name", "damage_type"],
    "additionalProperties": True
}

# Key mapping for v2/v3 compact links
V2_KEY_MAP = {
    "name": "n",
    "item_type": "t",
    "weapon_type": "wt",
    "speed": "s",
    "range_zero": "r0",
    "range_mid": "r1",
    "range_max": "r2",
    "acc_zero": "a0",
    "acc_mid": "a1",
    "acc_max": "a2",
    "damage_min": "d0",
    "damage_max": "d1",
    "wound_chance": "wc",
    "armor_piercing": "ap",
    "damage_type": "dt",
    "health_cost": "hc",
    "action_cost": "ac",
    "mind_cost": "mc",
    "skill_mods": "sm",
    "overall_quality": "oq",
    "unit_toughness": "ut",
    "malleability": "ma",
    "cold_resistance": "cr",
    "decay_resistance": "dr",
    "heat_resistance": "hr",
    "conductivity": "cd",
    "entangle_resistance": "er",
    "flavor": "fl",
    "potential_energy": "pe",
    "shock_resistance": "sr",
    "mod_damage_min": "md0",
    "mod_damage_max": "md1",
    "mod_speed": "ms",
    "mod_accuracy": "mac",
    "mod_effectiveness": "me",
    "armor_rating": "ar",
    "effectiveness": "eff",
    "kinetic": "kin",
    "energy": "en",
    "blast": "bl",
    "stun": "st",
    "heat": "ht",
    "cold": "co",
    "acid": "ad",
    "electricity": "el",
    "condition": "c",
    "max_condition": "mc"
}
V2_INV_MAP = {v: k for k, v in V2_KEY_MAP.items()}

# v4 mapping for ultra-short links (Bit-packed style indices)
# We map most common items and attributes to a single byte or less.
V4_KEY_MAP = {
    "name": 0, "item_type": 1, "weapon_type": 2, "speed": 3,
    "range_zero": 4, "range_mid": 5, "range_max": 6,
    "acc_zero": 7, "acc_mid": 8, "acc_max": 9,
    "damage_min": 10, "damage_max": 11, "wound_chance": 12,
    "armor_piercing": 13, "damage_type": 14,
    "health_cost": 15, "action_cost": 16, "mind_cost": 17,
    "skill_mods": 18, "overall_quality": 19, "unit_toughness": 20,
    "malleability": 21, "cold_resistance": 22, "decay_resistance": 23,
    "heat_resistance": 24, "conductivity": 25, "entangle_resistance": 26,
    "flavor": 27, "potential_energy": 28, "shock_resistance": 29,
    "mod_damage_min": 30, "mod_damage_max": 31, "mod_speed": 32,
    "mod_accuracy": 33, "mod_effectiveness": 34,
    "armor_rating": 35, "effectiveness": 36, "kinetic": 37,
    "energy": 38, "blast": 39, "stun": 40, "heat": 41,
    "cold": 42, "acid": 43, "electricity": 44, "condition": 45,
    "max_condition": 46
}
V4_INV_MAP = {v: k for k, v in V4_KEY_MAP.items()}

# V6 Constants for ultra-compact bit-packing (16-byte block)
V6_ITEM_TYPES = {"Weapon": 0, "Armor": 1, "Resource": 2, "Component": 3}
V6_WEAPON_TYPES = {"Pistol": 0, "Rifle": 1, "Carbine": 2, "1H Sword": 3, "2H Sword": 4, "Polearm": 5, "Unarmed": 6}
V6_DAMAGE_TYPES = {"Energy": 0, "Kinetic": 1, "Blast": 2, "Stun": 3, "Heat": 4, "Cold": 5, "Acid": 6, "Electricity": 7, "None": 8}
V6_WEAPON_CATEGORIES = {"Pistol": 0, "Carbine": 1, "Rifle": 2, "1H Sword": 3, "2H Sword": 4, "Axe": 5, "Polearm": 6, "Unarmed": 7}
V6_AP_LEVELS = {"None": 0, "Light": 1, "Medium": 2, "Heavy": 3}
V6_ARMOR_RATINGS = {"None": 0, "Light": 1, "Medium": 2, "Heavy": 3}
V6_RESOURCE_TRAITS = [
    "cold_resistance", "conductivity", "decay_resistance", "entangle_resistance", 
    "flavor", "heat_resistance", "malleability", "overall_quality", 
    "potential_energy", "shock_resistance", "unit_toughness"
]
V6_RESOURCE_TRAITS_MAP = {k: i for i, k in enumerate(V6_RESOURCE_TRAITS)}

# Common values to index mapping
V4_VAL_MAP = {
    "Pistol": 0, "Rifle": 1, "Carbine": 2, "1H Sword": 3, "2H Sword": 4,
    "Polearm": 5, "Unarmed": 6, "Energy": 7, "Kinetic": 8, "Blast": 9,
    "Stun": 10, "Heat": 11, "Cold": 12, "Acid": 13, "Electricity": 14,
    "Light": 15, "Medium": 16, "Heavy": 17, "None": 18, "Resource": 19,
    "Weapon": 20, "Armor": 21, "Component": 22
}
V4_VAL_INV_MAP = {v: k for k, v in V4_VAL_MAP.items()}

# v5 Registry for ultra-short (12 chars) local references
# Maps a small integer ID to an item hash. Only works locally or if peer has seen it.
V5_REGISTRY = {}
V5_COUNTER = 0

# Chat-safe Base85 alphabet (excludes ; & < > " ' \ and others that might be tricky)
# We map standard B85 alphabet (RFC 1924) to this safe one.
# Standard (Python base64.b85): 0-9, A-Z, a-z, !, #, $, %, &, (, ), *, +, -, ;, <, =, >, ?, @, ^, _, `, {, |, }, ~
B85_STD  = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~"
# Safe: 62 Alphanum + 23 symbols = 85. 
# We use symbols that are widely accepted in SWG chat.
B85_SAFE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.-_/:,()[]+=!?$#@%*{|}~"

def b85_to_safe(s):
    # Standard has 85 chars, SAFE must have 85 chars.
    return s.translate(str.maketrans(B85_STD, B85_SAFE))

def b85_from_safe(s):
    return s.translate(str.maketrans(B85_SAFE, B85_STD))

def set_clipboard_text(text):
    """Securely set clipboard text using multiple methods to ensure SWG compatibility."""
    import pyperclip
    import ctypes
    from ctypes import wintypes
    
    # Method 1: Pyperclip (Standard)
    try:
        pyperclip.copy(text)
    except:
        pass
        
    # Method 2: Win32 API (Direct) - Ensures CF_UNICODETEXT / CF_TEXT
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        CF_UNICODETEXT = 13
        GHND = 0x0042
        
        if user32.OpenClipboard(None):
            user32.EmptyClipboard()
            
            # Unicode version
            h_mem = kernel32.GlobalAlloc(GHND, len(text.encode('utf-16-le')) + 2)
            p_mem = kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, text.encode('utf-16-le'), len(text.encode('utf-16-le')))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            
            user32.CloseClipboard()
    except Exception as e:
        print(f"Direct clipboard error: {e}")

class ItemWand:
    def __init__(self, parent_win, app):
        self.parent = parent_win
        self.app = app
        self.active = False
        self.wand_size = 150 # Size of the wand scanning area
        self.overlay = None
        self.last_pos = (0, 0)
        self.accumulated_text = ""
        self.current_data = {}
        self.cooldown = 0
        self.live_overlay = None
        
    def start(self):
        self.active = True
        self.accumulated_text = ""
        self.current_data = {"name": "Wand Scan", "damage_type": "None", "item_type": "Misc"}
        self.parent.status_label.config(text="WAND ACTIVE: MOVE OVER STATS", fg="#00FF00")
        
        # Create a transparent overlay that follows mouse
        self.overlay = tk.Toplevel(self.parent.window)
        try:
            self.overlay.attributes("-toolwindow", True)
        except: pass
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.configure(bg="green")

        # Live OCR Display Window
        self.live_overlay = tk.Toplevel(self.parent.window)
        try:
            self.live_overlay.attributes("-toolwindow", True)
        except: pass
        self.live_overlay.overrideredirect(True)
        self.live_overlay.attributes("-topmost", True)
        self.live_overlay.configure(bg="#1a1a1a")
        self.live_label = tk.Label(self.live_overlay, text="Initializing Wand...", fg="#00FF00", bg="#1a1a1a", font=("Consolas", 9))
        self.live_label.pack()
        
        # Make it "click-through" on Windows
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20
        
        hwnd_ov = ctypes.windll.user32.GetParent(self.overlay.winfo_id())
        style_ov = ctypes.windll.user32.GetWindowLongW(hwnd_ov, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd_ov, GWL_EXSTYLE, style_ov | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        
        hwnd_live = ctypes.windll.user32.GetParent(self.live_overlay.winfo_id())
        style_live = ctypes.windll.user32.GetWindowLongW(hwnd_live, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd_live, GWL_EXSTYLE, style_live | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        
        self.update_wand()
        
    def stop(self):
        self.active = False
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        if self.live_overlay:
            self.live_overlay.destroy()
            self.live_overlay = None
        
        self.parent.status_label.config(text="Wand scan complete", fg="white")
        self.parent.wand_btn.config(text="WAND SCAN", bg="#333")
        
        # Process what we found
        if self.accumulated_text:
            final_data = self.parent._identify_item_from_text(self.accumulated_text)
            if final_data:
                final_data["raw_ocr"] = self.accumulated_text
                self.parent.show_scan_preview(final_data)
        
    def update_wand(self):
        if not self.active: return
        
        # Get mouse pos
        x, y = pyautogui.position()
        self.overlay.geometry(f"{self.wand_size}x{self.wand_size}+{x - self.wand_size//2}+{y - self.wand_size//2}")
        self.live_overlay.geometry(f"+{x + self.wand_size//2 + 10}+{y - 20}")
        
        # Only scan if moved significantly or every 600ms
        import time
        now = time.time()
        if (abs(x - self.last_pos[0]) > 20 or abs(y - self.last_pos[1]) > 20) and now > self.cooldown:
            self.last_pos = (x, y)
            self.cooldown = now + 0.6 # Rate limit OCR
            self.perform_localized_scan(x, y)
            
        self.parent.window.after(50, self.update_wand)
        
    def perform_localized_scan(self, mx, my):
        # Capture a small region around the mouse
        rx = mx - self.wand_size // 2
        ry = my - self.wand_size // 2
        
        try:
            shot = pyautogui.screenshot(region=(rx, ry, self.wand_size, self.wand_size))
            
            # High-Res / Pre-processing
            from PIL import ImageEnhance
            shot = shot.resize((self.wand_size * 2, self.wand_size * 2), Image.LANCZOS)
            shot = shot.convert('L')
            shot = ImageEnhance.Contrast(shot).enhance(2.5)
            
            if pytesseract:
                text = pytesseract.image_to_string(shot, config='--psm 6')
                if text.strip():
                    self.accumulated_text += "\n" + text.strip()
                    # Update live feedback
                    display_text = text.strip().replace("\n", " | ")
                    if len(display_text) > 40: display_text = display_text[:37] + "..."
                    self.live_label.config(text=display_text)
                    
                    # Real-time identification feedback
                    partial = self.parent._identify_item_from_text(text)
                    if partial and partial.get("name") and partial["name"] != "Unknown Item":
                        self.parent.status_label.config(text=f"WAND: FOUND {partial['name'].upper()}", fg="cyan")
        except:
            pass

class ThemedInputDialog(BasePopoutWindow):
    def __init__(self, app, title, prompt, initial_value=""):
        self.prompt = prompt
        self.initial_value = initial_value
        self.result = None
        super().__init__(app, title, 400, 150)

    def build_ui(self):
        # Center the window relative to screen or parent
        self.window.update_idletasks()
        
        tk.Label(self.content_container, text=self.prompt.upper(), bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Lilita One", 10)).pack(pady=(10, 5))
        
        self.entry = tk.Entry(self.content_container, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, borderwidth=0, font=("Segoe UI", 10))
        self.entry.pack(fill=tk.X, padx=20, pady=5)
        self.entry.insert(0, self.initial_value)
        self.entry.focus_set()
        
        btn_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        btn_frame.pack(pady=10)
        
        def on_ok(e=None):
            self.result = self.entry.get()
            self.close()
            
        def on_cancel(e=None):
            self.result = None
            self.close()

        ok_btn = tk.Label(btn_frame, text="  OK  ", bg=ACCENT_RED, fg=TEXT_PRIMARY, font=("Lilita One", 10), cursor="hand2")
        ok_btn.pack(side=tk.LEFT, padx=10)
        ok_btn.bind("<Button-1>", on_ok)
        
        cancel_btn = tk.Label(btn_frame, text=" CANCEL ", bg=BUTTON_BG, fg=TEXT_PRIMARY, font=("Lilita One", 10), cursor="hand2")
        cancel_btn.pack(side=tk.LEFT, padx=10)
        cancel_btn.bind("<Button-1>", on_cancel)
        
        self.window.bind("<Return>", on_ok)
        self.window.bind("<Escape>", on_cancel)

    def get_result(self):
        self.window.wait_window()
        return self.result

class FaxWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "FAX", "FaxWindow", 320, 480, centered=True)
        self.encryption_key = self._get_obfuscated_key()
        self.custom_items = self._load_custom_items()
        self.history = self._load_history()
        self.safety_engine = self._initialize_safety()
        self.item_wand = ItemWand(self, app)

    def _get_discord_webhook_url(self):
        """Return the Discord webhook URL from config, or None."""
        if hasattr(self.app, 'config') and self.app.config:
            return self.app.config.get('Discord', 'webhook_url', fallback=None)
        return None

    def _set_discord_webhook_url(self, url):
        """Save the Discord webhook URL to config."""
        if hasattr(self.app, 'config') and self.app.config:
            self.app.config.set('Discord', 'webhook_url', url)
            self.app.save_config()

    def send_to_discord_webhook(self, message):
        """Send a message to the configured Discord webhook."""
        url = self._get_discord_webhook_url()
        if not url:
            self.status_label.config(text="No webhook URL configured! Use SET WEBHOOK.", fg="red")
            return
        try:
            payload = {"content": message}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 204 or r.status_code == 200:
                self.status_label.config(text="Sent to Discord!", fg="#00ff00")
            else:
                self.status_label.config(text=f"Discord error: {r.status_code}", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Discord send error: {e}", fg="red")

    def _initialize_safety(self):
        # High-speed safety filter for restricted letter combinations
        # Stored in an obfuscated binary format to prevent simple copying
        try:
            safety_file = get_resource_path("safety_data.bin")
            if not os.path.exists(safety_file):
                # First time: Download and transform
                url = "https://raw.githubusercontent.com/livy2k/swgstuff/unstable/MMOCoreORB/bin/scripts/managers/name/regex_words.txt"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    raw_lines = [l.strip().lower() for l in r.text.split('\n') if len(l.strip()) > 3]
                    # Filter out purely alphanumeric 4-char strings that might be too common in random base85
                    # like 'pons' (weaponry related but common in cipher)
                    filtered = []
                    for l in raw_lines:
                        if len(l) <= 4 and l.isalnum(): continue
                        filtered.append(l)
                    
                    # Shuffle to make it look different from source
                    random.shuffle(filtered)
                    # XOR obfuscation
                    with open(safety_file, "wb") as f:
                        for line in filtered:
                            b = line.encode('utf-8')
                            f.write(bytes([len(b)]))
                            f.write(bytes([x ^ 0xA5 for x in b]))
            
            patterns = []
            if os.path.exists(safety_file):
                with open(safety_file, "rb") as f:
                    while True:
                        l_byte = f.read(1)
                        if not l_byte: break
                        length = l_byte[0]
                        data = f.read(length)
                        patterns.append("".join([chr(x ^ 0xA5) for x in data]))
            
            if patterns:
                # Escape dots and build a single regex
                safe_patterns = [re.escape(p) if "\\" not in p else p for p in patterns]
                return re.compile("|".join(safe_patterns), re.IGNORECASE)
        except Exception as e:
            print(f"Safety init error: {e}")
        return None

    def is_cipher_clean(self, text):
        if not self.safety_engine: return True
        return not self.safety_engine.search(text)
        
    def _load_history(self):
        import os
        if os.path.exists("scan_history.json"):
            try:
                with open("scan_history.json", "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_history(self, item_data):
        # 1. Duplicate Handling: move to top if exists
        # We compare by name and stats (or cipher if available)
        # Using a hash of the data for comparison
        import hashlib
        def get_item_id(data):
            # Exclude metadata from ID comparison
            core = {k: v for k, v in data.items() if k not in ["timestamp", "sender", "channel", "raw_ocr", "raw_ocr_text", "chroma_proof"]}
            return hashlib.md5(str(sorted(core.items())).encode()).hexdigest()

        new_id = get_item_id(item_data)
        
        # Remove existing if it's a duplicate
        self.history = [h for h in self.history if get_item_id(h) != new_id]
        
        # 2. Insert at top
        self.history.insert(0, item_data)
        
        # 3. Prune to 50
        self.history = self.history[:50]
        
        try:
            with open("scan_history.json", "w") as f:
                json.dump(self.history, f)
        except Exception as e:
            print(f"[ERROR] Failed to save history: {e}")
        
    def _load_custom_items(self):
        items = {}
        import os
        if os.path.exists("custom_items.txt"):
            try:
                with open("custom_items.txt", "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        try:
                            data = json.loads(line)
                            if self.validate_item(data):
                                items[data["name"].upper()] = data
                        except Exception as e:
                            print(f"[ERROR] Failed to parse custom item line: {e}")
            except Exception as e:
                print(f"[ERROR] Failed to read custom_items.txt: {e}")
        return items
        
    def show(self, force_open=False):
        # BasePopoutWindow.show(self, force_open) initializes the window and content_container
        super().show(force_open)
        if not self.window: return
        
        # Increase width for two-column layout if needed
        self.window.geometry("700x480")

        # Ensure window is visible and follows app alpha
        self.window.attributes("-alpha", self.app.current_alpha)
        self.window.deiconify()
        self.window.lift()
        
        # Reset notification on open
        if hasattr(self.app, 'new_link_available'):
            self.app.new_link_available = False
        
        # Clear previous UI if any
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Two-Column Layout (similar to Livius)
        main_container = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left Panel: History
        left_panel = tk.Frame(main_container, bg=PANEL_DARK, bd=1, relief=tk.RIDGE)
        left_panel.place(relx=0.01, rely=0.01, relwidth=0.48, relheight=0.88)
        
        tk.Label(left_panel, text="ITEM HISTORY", fg="#d31a17", bg=PANEL_DARK, font=("Lilita One", 10)).pack(anchor="w", padx=5, pady=2)
        
        tree_frame = tk.Frame(left_panel, bg=WINDOW_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Fax.Treeview", background="#111111", foreground="white", fieldbackground="#111111", 
                        font=("Segoe UI", 9), borderwidth=0, rowheight=22)
        style.map("Fax.Treeview", background=[("selected", "#d31a17")])
        
        self.tree = ttk.Treeview(tree_frame, columns=("name",), show="headings", style="Fax.Treeview", height=5)
        self.tree.heading("name", text="ITEM NAME")
        self.tree.column("name", width=150, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # CoolScroll Scrollbar
        style.configure("Cool.Vertical.TScrollbar", background="#333", bordercolor="#222", arrowcolor="white", troughcolor="#111")
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, style="Cool.Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<Double-Button-1>", self._on_tree_double_click)
        self.tree.tag_configure('odd', background='#111111')
        self.tree.tag_configure('even', background='#1a1a1a')

        # Right Panel: Display Window
        right_panel = tk.Frame(main_container, bg=PANEL_DARK, bd=1, relief=tk.RIDGE)
        right_panel.place(relx=0.51, rely=0.01, relwidth=0.48, relheight=0.88)
        
        tk.Label(right_panel, text="DISPLAY", fg="#d31a17", bg=PANEL_DARK, font=("Lilita One", 10)).pack(anchor="w", padx=5, pady=2)
        self.display_frame = tk.Frame(right_panel, bg="#111", bd=1, relief=tk.SUNKEN)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.display_label = tk.Label(self.display_frame, text="Select an item\nto view details", fg="#666", bg="#111", font=("Segoe UI", 9))
        self.display_label.pack(expand=True)

        # Bottom Buttons
        btn_frame = tk.Frame(main_container, bg=WINDOW_BG)
        btn_frame.place(relx=0.01, rely=0.90, relwidth=0.98, relheight=0.09)
        
        self.v10_btn = tk.Button(btn_frame, text="COPY LINK CLIPBOARD", command=self.quick_v10_scan, bg="#333", fg="white", font=("Lilita One", 10), bd=0)
        self.v10_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(btn_frame, text="Double-click history to display", fg="#888", bg=WINDOW_BG, font=("Segoe UI", 8))
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Webhook setup button
        def set_webhook():
            dialog = ThemedInputDialog(self.app, "Discord Webhook", "Enter Discord webhook URL:", 
                                     initial_value=self._get_discord_webhook_url() or "")
            url = dialog.get_result()
            if url:
                self._set_discord_webhook_url(url.strip())
                self.status_label.config(text="Webhook URL saved!", fg="#00ff00")

        webhook_btn = tk.Button(btn_frame, text="SET WEBHOOK", command=set_webhook,
                                bg="#5865F2", fg="white", font=("Lilita One", 8), bd=0)
        webhook_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_history()

    def _on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            idx = self.tree.index(item_id)
            item_data = self.history[idx]
            self._display_item_preview(item_data)

    def _display_item_preview(self, item_data):
        for w in self.display_frame.winfo_children():
            w.destroy()
            
        # If we have a visual proof (chroma_proof), prioritize it as requested
        if "chroma_proof" in item_data:
            try:
                import io
                import zlib
                import base64
                from PIL import Image, ImageTk, ImageDraw
                
                b85_data = item_data["chroma_proof"].replace("chromalink:", "")
                compressed = base64.b85decode(b85_data)
                img_bytes = zlib.decompress(compressed)
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                
                # Create a themed reconstruction (matching ItemDetailWindow style)
                # But sized for the display_frame
                self.display_frame.update_idletasks() # Ensure dimensions are updated
                f_w = self.display_frame.winfo_width()
                f_h = self.display_frame.winfo_height()
                if f_w < 50: f_w = 340 # Fallback if not mapped yet
                if f_h < 50: f_h = 420 # Increased height fallback

                recon = Image.new('RGB', (f_w, f_h), color=(10, 10, 10))
                
                # Paste the chroma text directly - "only the proof image"
                # Center it
                self.display_frame.update_idletasks()
                f_w = self.display_frame.winfo_width()
                f_h = self.display_frame.winfo_height()
                if f_w < 50: f_w = 340
                if f_h < 50: f_h = 420
                
                # Re-create recon with final size
                recon = Image.new('RGB', (f_w, f_h), color=(10, 10, 10))
                
                img.thumbnail((f_w - 10, f_h - 10))
                ix, iy = img.size
                recon.paste(img, ((f_w - ix)//2, (f_h - iy)//2))
                
                self.preview_photo = ImageTk.PhotoImage(recon)
                lbl = tk.Label(self.display_frame, image=self.preview_photo, bg="#111", borderwidth=0)
                lbl.image = self.preview_photo
                lbl.pack(fill=tk.BOTH, expand=True)
                
                # Add a small button overlay at bottom to view full
                def open_full():
                    from windows.item_detail import ItemDetailWindow
                    detail = ItemDetailWindow(self.app, "History", item_data)
                    detail.show(force_open=True)
                
                btn = tk.Button(self.display_frame, text="FULL DETAILS", command=open_full, 
                              bg="#222", fg="#444", font=("Segoe UI", 7), bd=0, padx=2, pady=0)
                btn.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
                return
            except Exception as e:
                print(f"[DEBUG] Error rendering fax preview image: {e}")
                # Fallback to text if image fails

        container = tk.Frame(self.display_frame, bg="#111")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(container, text=item_data.get("name", "Unknown").upper(), fg="cyan", bg="#111", font=("Lilita One", 11, "bold")).pack(anchor="w")
        
        details = f"Type: {item_data.get('item_type', 'Misc')}\n"
        if item_data.get("item_type") == "Weapon":
            details += f"Dmg: {item_data.get('damage_min', 0)}-{item_data.get('damage_max', 0)}\n"
            details += f"Speed: {item_data.get('speed', 0.0)}s\n"
        elif item_data.get("item_type") == "Armor":
            details += f"Rating: {item_data.get('armor_rating', 'None')}\n"
            details += f"Kinetic: {item_data.get('kinetic', 0)}%\n"
            
        tk.Label(container, text=details, fg="white", bg="#111", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor="w", pady=5)
        
        def open_full():
            from windows.item_detail import ItemDetailWindow
            detail = ItemDetailWindow(self.app, "History", item_data)
            detail.show(force_open=True)
            
        tk.Button(container, text="VIEW FULL DETAILS", command=open_full, bg="#222", fg="#d31a17", font=("Lilita One", 9), bd=0).pack(side=tk.BOTTOM, fill=tk.X)

    def encrypt_item_v12(self, item):
        """V12 Extreme-Pack: Targets exactly 16 bytes (24 chars).
        Minimalist bit-packing for core stats, prioritizing value over names."""
        try:
            b = bytearray()
            itype = V6_ITEM_TYPES.get(item.get("item_type"), 0)
            
            # 1. Byte 0: Type(2 bits) | SubType/Flags(6 bits)
            # Use 6 bits for category/rating
            if itype == 0: # Weapon
                cat = V6_WEAPON_CATEGORIES.get(item.get("weapon_type"), 0) & 0x07
                dt = V6_DAMAGE_TYPES.get(item.get("damage_type"), 0) & 0x07
                b.append((itype << 6) | (cat << 3) | dt)
                
                # Bytes 1-2: Dmin(10), Dmax(6) - dmax is usually higher, let's see
                # Actually, 10 bits for each damage is better.
                # Bytes 1-3: Dmin(10) | Dmax(10) | AP(2) | Sliced(1) | Powerup(1) = 24 bits
                dmin = int(item.get("damage_min", 0)) & 0x3FF
                dmax = int(item.get("damage_max", 0)) & 0x3FF
                ap = V6_AP_LEVELS.get(item.get("armor_piercing"), 0) & 0x03
                flags = 0
                if item.get("is_sliced"): flags |= 0x02
                if item.get("has_powerup"): flags |= 0x01
                val = (dmin << 14) | (dmax << 4) | (ap << 2) | flags
                b.extend(val.to_bytes(3, 'big'))
                
                # Byte 4: Speed (0-6.3 -> 6 bits) | Wound (0-15 -> 4 bits? no, 2 bits?)
                # Let's do Speed(6 bits) | Wound(2 bits: 0, 5, 10, 15)
                speed = int(min(item.get("speed", 0) * 10, 63))
                wound = int(min(item.get("wound_chance", 0) // 5, 3))
                b.append((speed << 2) | wound)
                
                # Bytes 5-7: Accuracy Zero/Mid/Max (8 bits each, signed)
                b.append(int(max(-128, min(127, item.get("acc_zero", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_mid", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_max", 0)))) & 0xFF)
                
                # Bytes 8-15: Name (8 chars)
                name = item.get("name", "ITEM")[:8].upper().ljust(8)
                b.extend(name.encode('ascii', 'ignore'))

            elif itype == 1: # Armor
                rating = V6_ARMOR_RATINGS.get(item.get("armor_rating"), 0) & 0x03
                eff = int(min(item.get("effectiveness", 0), 63)) # 0-63%
                b.append((itype << 6) | (rating << 4) | (eff >> 2)) # Use some bits here
                # We have plenty of space in armor
                b.append((eff & 0x03) << 6) 
                
                # Protections: 8 stats, 5 bits each (0-31 step 3% roughly, or just 0-95 step 3)
                # 8 * 5 = 40 bits = 5 bytes
                prots = [item.get(p, 0) for p in ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]]
                p_val = 0
                for p in prots:
                    p_val = (p_val << 5) | int(min(p // 3, 31))
                b.extend(p_val.to_bytes(5, 'big'))
                
                # Bytes 7-15: Name (9 chars)
                name = item.get("name", "ARMOR")[:9].upper().ljust(9)
                b.extend(name.encode('ascii', 'ignore'))

            elif itype == 2: # Resource
                b.append((itype << 6))
                # Overall Quality(10) + 3 traits(10 bits each + 4 bits index)
                # 10 + 3*(10+4) = 10 + 42 = 52 bits = 6.5 bytes
                oq = int(item.get("overall_quality", 0)) & 0x3FF
                traits = []
                for t in V6_RESOURCE_TRAITS:
                    if item.get(t): traits.append((t, item[t]))
                traits.sort(key=lambda x: x[1], reverse=True)
                
                val = oq
                for i in range(3):
                    t_val = 0
                    t_idx = 0
                    if i < len(traits):
                        t_val = int(traits[i][1]) & 0x3FF
                        t_idx = V6_RESOURCE_TRAITS_MAP.get(traits[i][0], 0) & 0x0F
                    val = (val << 14) | (t_val << 4) | t_idx
                
                # val is 10 + 14*3 = 52 bits
                b.extend(val.to_bytes(7, 'big'))
                
                # Bytes 8-15: Name (8 chars)
                name = item.get("name", "RESO")[:8].upper().ljust(8)
                b.extend(name.encode('ascii', 'ignore'))

            else: # Component
                b.append((itype << 6))
                # Just store more name/stats
                d_mod = int(item.get("mod_damage_min", 0) * 10) & 0x3FF
                s_mod = int(item.get("mod_speed", 0) * 100) & 0x3FF
                val = (d_mod << 10) | s_mod
                b.extend(val.to_bytes(3, 'big'))
                # Bytes 4-15: Name (12 chars)
                name = item.get("name", "COMP")[:12].upper().ljust(12)
                b.extend(name.encode('ascii', 'ignore'))

            # Ensure exactly 16 bytes for 1 AES block without padding expansion
            while len(b) < 16: b.append(0)
            payload = bytes(b[:16])
            
            key = self.encryption_key.encode('utf-8').ljust(32)[:32]
            iv = b"LivyLogsShortIV1"
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(payload)
            
            return "lvs:" + b85_to_safe(base64.b85encode(encrypted).decode('utf-8'))
        except Exception as e:
            print(f"v12 encryption error: {e}")
            return self.encrypt_item_v10(item)

    def decrypt_item_v12(self, decrypted):
        try:
            itype = (decrypted[0] >> 6)
            if itype == 0: # Weapon
                cat_idx = (decrypted[0] >> 3) & 0x07
                dt_idx = decrypted[0] & 0x07
                
                val = int.from_bytes(decrypted[1:4], 'big')
                dmin = (val >> 14) & 0x3FF
                dmax = (val >> 4) & 0x3FF
                ap_idx = (val >> 2) & 0x03
                flags = val & 0x03
                
                byte4 = decrypted[4]
                speed = (byte4 >> 2) / 10.0
                wound = (byte4 & 0x03) * 5
                
                acc_zero = int.from_bytes([decrypted[5]], 'big', signed=True)
                acc_mid = int.from_bytes([decrypted[6]], 'big', signed=True)
                acc_max = int.from_bytes([decrypted[7]], 'big', signed=True)
                
                name = decrypted[8:16].decode('ascii', 'ignore').strip()
                
                return {
                    "name": name, "item_type": "Weapon",
                    "weapon_type": {v: k for k, v in V6_WEAPON_CATEGORIES.items()}.get(cat_idx, "Unknown"),
                    "damage_type": {v: k for k, v in V6_DAMAGE_TYPES.items()}.get(dt_idx, "Kinetic"),
                    "armor_piercing": {v: k for k, v in V6_AP_LEVELS.items()}.get(ap_idx, "None"),
                    "damage_min": dmin, "damage_max": dmax, "speed": speed, "wound_chance": float(wound),
                    "acc_zero": acc_zero, "acc_mid": acc_mid, "acc_max": acc_max,
                    "is_sliced": bool(flags & 0x02), "has_powerup": bool(flags & 0x01)
                }
            elif itype == 1: # Armor
                rating_idx = (decrypted[0] >> 4) & 0x03
                eff = ((decrypted[0] & 0x0F) << 2) | (decrypted[1] >> 6)
                
                p_val = int.from_bytes(decrypted[2:7], 'big')
                p_keys = ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]
                data = {"item_type": "Armor", "effectiveness": eff}
                for i in range(7, -1, -1):
                    data[p_keys[i]] = (p_val & 0x1F) * 3
                    p_val >>= 5
                data["armor_rating"] = {v: k for k, v in V6_ARMOR_RATINGS.items()}.get(rating_idx, "None")
                data["name"] = decrypted[7:16].decode('ascii', 'ignore').strip()
                return data
            elif itype == 2: # Resource
                val = int.from_bytes(decrypted[1:8], 'big')
                # val is 52 bits. traits(14*3=42) | oq(10) NO, oq is high
                # Packing was: oq(10) | T1(14) | T2(14) | T3(14) = 52 bits
                oq = (val >> 42) & 0x3FF
                data = {"item_type": "Resource", "overall_quality": oq, "name": decrypted[8:16].decode('ascii', 'ignore').strip()}
                for i in range(2, -1, -1):
                    t_val = (val >> (i * 14 + 4)) & 0x3FF
                    t_idx = (val >> (i * 14)) & 0x0F
                    if t_idx < len(V6_RESOURCE_TRAITS):
                        data[V6_RESOURCE_TRAITS[t_idx]] = t_val
                return data
            else: # Component
                val = int.from_bytes(decrypted[1:4], 'big')
                d_mod = ((val >> 10) & 0x3FF) / 10.0
                s_mod = (val & 0x3FF) / 100.0
                name = decrypted[4:16].decode('ascii', 'ignore').strip()
                return {"item_type": "Component", "name": name, "mod_damage_min": d_mod, "mod_speed": s_mod}
        except Exception as e:
            print(f"v12 decryption error: {e}")
            return None

    def encrypt_item_v10(self, item):
        """V10 Ultra-Pack: Targets exactly ~55 characters. 
        Uses bit-packing for stats and remaining space for the name."""
        try:
            b = bytearray()
            itype = V6_ITEM_TYPES.get(item.get("item_type"), 0)
            
            # 1. Header: Type(2 bits) | Presence Mask(6 bits)
            # Mask: [Name, Dmg, Speed, Wound, Acc, Flags]
            mask = 0x3F # Default most on
            b.append((itype << 6) | mask)
            
            if itype == 0: # Weapon
                # Category(3) | Dtype(3) | AP(2) = 8 bits
                b.append((V6_WEAPON_CATEGORIES.get(item.get("weapon_type"), 0) << 5) | 
                         (V6_DAMAGE_TYPES.get(item.get("damage_type"), 0) << 2) |
                         (V6_AP_LEVELS.get(item.get("armor_piercing"), 0)))
                
                # DmgMin(14) | DmgMax(14) | Speed(6) | Wound(4) | Flags(4) = 42 bits (5.25 bytes -> 6 bytes)
                dmin = int(item.get("damage_min", 0)) & 0x3FFF
                dmax = int(item.get("damage_max", 0)) & 0x3FFF
                speed = int(min(item.get("speed", 0) * 10, 63))
                wound = int(round(item.get("wound_chance", 0))) & 0x0F
                flags = 0
                if item.get("is_sliced"): flags |= 0x01
                if item.get("has_powerup"): flags |= 0x02
                
                # Packing 42 bits into 6 bytes
                # Bits: 41-28: dmin, 27-14: dmax, 13-8: speed, 7-4: wound, 3-0: flags
                val = (dmin << 28) | (dmax << 14) | (speed << 8) | (wound << 4) | flags
                b.append((val >> 40) & 0xFF)
                b.append((val >> 32) & 0xFF)
                b.append((val >> 24) & 0xFF)
                b.append((val >> 16) & 0xFF)
                b.append((val >> 8) & 0xFF)
                b.append(val & 0xFF)
                
                # Accuracy (3x8 = 24 bits)
                b.append(int(max(-128, min(127, item.get("acc_zero", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_mid", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_max", 0)))) & 0xFF)

            elif itype == 1: # Armor
                # Header: itype(2) | mask(6) was already added
                # Armor Rating(2) | Effectiveness(6: 0-100 step 2) = 8 bits
                rating = V6_ARMOR_RATINGS.get(item.get("armor_rating"), 0)
                eff = int(min(item.get("effectiveness", 0), 100) // 2) 
                b.append((rating << 6) | eff)
                
                # Protections: 8 stats, 7 bits each (0-100) = 56 bits (7 bytes)
                prots = [item.get(p, 0) for p in ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]]
                p_val = 0
                for p in prots:
                    p_val = (p_val << 7) | int(min(p, 100))
                b.extend(p_val.to_bytes(7, 'big'))
            
            # Use remaining budget for Name (Target ~32 bytes total for ~55 chars in B85)
            # 32 bytes * 1.25 (B85 expansion) = 40 chars + 4 (lvs:) = 44 chars.
            # We can afford more. 40 bytes -> 50 chars + 4 = 54 chars.
            name = item.get("name", "Unknown")
            # Truncate name to fit in the remaining space
            # Target total 24-28 bytes to stay under 55 chars after AES padding (16-byte blocks)
            # 32 bytes (2 blocks) -> 40 chars. + 4 prefix = 44.
            # 48 bytes (3 blocks) -> 60 chars. + 4 prefix = 64.
            # So we MUST stay <= 32 bytes AFTER padding.
            # That means len(b) must be <= 31 before padding (pad adds at least 1 byte).
            available = 31 - len(b)
            if available > 0:
                name_bytes = name.encode('ascii', 'ignore')[:available]
                b.extend(name_bytes)

            # Final encryption
            key = self.encryption_key.encode('utf-8').ljust(32)[:32]
            iv = b"LivyLogsShortIV1"
            # No padding needed if we don't use Block mode, but we use CBC here for consistency.
            # We must pad to 16.
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(bytes(b), AES.block_size))
            return "lvs:" + b85_to_safe(base64.b85encode(encrypted).decode('utf-8'))
        except Exception as e:
            print(f"v10 encryption error: {e}")
            return self.encrypt_item(item)

    def decrypt_item_v10(self, decrypted):
        """Helper for decrypt_item to handle V10 unpacked bytes."""
        try:
            itype = (decrypted[0] >> 6)
            mask = decrypted[0] & 0x3F
            
            data = {}
            offset = 1
            if itype == 0: # Weapon
                header = decrypted[offset]
                wtype_idx = (header >> 5) & 0x07
                dtype_idx = (header >> 2) & 0x07
                ap_idx = header & 0x03
                offset += 1
                
                val = int.from_bytes(decrypted[offset:offset+6], 'big')
                # val bits: 41-28: dmin, 27-14: dmax, 13-8: speed, 7-4: wound, 3-0: flags
                dmin = (val >> 28) & 0x3FFF
                dmax = (val >> 14) & 0x3FFF
                speed = ((val >> 8) & 0x3F) / 10.0
                wound = (val >> 4) & 0x0F
                flags = val & 0x0F
                offset += 6
                
                acc_zero = int.from_bytes([decrypted[offset]], 'big', signed=True)
                acc_mid = int.from_bytes([decrypted[offset+1]], 'big', signed=True)
                acc_max = int.from_bytes([decrypted[offset+2]], 'big', signed=True)
                offset += 3
                
                wtype = {v: k for k, v in V6_WEAPON_CATEGORIES.items()}.get(wtype_idx, "Unknown")
                dtype = {v: k for k, v in V6_DAMAGE_TYPES.items()}.get(dtype_idx, "Kinetic")
                ap = {v: k for k, v in V6_AP_LEVELS.items()}.get(ap_idx, "None")
                
                data = {
                    "item_type": "Weapon", "weapon_type": wtype, "damage_type": dtype,
                    "armor_piercing": ap, "damage_min": dmin, "damage_max": dmax,
                    "speed": speed, "wound_chance": float(wound),
                    "acc_zero": acc_zero, "acc_mid": acc_mid, "acc_max": acc_max,
                    "is_sliced": bool(flags & 0x01), "has_powerup": bool(flags & 0x02)
                }
            elif itype == 1: # Armor
                header = decrypted[offset]
                rating_idx = (header >> 6) & 0x03
                eff = (header & 0x3F) * 2
                offset += 1
                
                p_val = int.from_bytes(decrypted[offset:offset+7], 'big')
                offset += 7
                p_keys = ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]
                data = {"item_type": "Armor", "effectiveness": eff}
                for i in range(7, -1, -1):
                    data[p_keys[i]] = (p_val & 0x7F)
                    p_val >>= 7
                rating = {v: k for k, v in V6_ARMOR_RATINGS.items()}.get(rating_idx, "None")
                data["armor_rating"] = rating
            
            # Name follows
            name = decrypted[offset:].decode('ascii', 'ignore').strip()
            # If name has non-printable chars due to AES padding, clean it
            name = ''.join(c for c in name if c.isprintable())
            data["name"] = name
            return data
        except: return None

    def encrypt_item_v11(self, item_data):
        """V11 Extended Packing: Uses the doubled character limit (~400 chars) 
        to include raw text and higher precision."""
        import zlib
        import base64
        
        # 1. Start with standard V10 packing logic (simulated here)
        # We pack the core stats first
        core_str = f"{item_data.get('name', 'Item')}|{item_data.get('item_type', 'Weapon')}"
        if item_data.get('item_type') == "Weapon":
            core_str += f"|{item_data.get('damage_min', 0)}|{item_data.get('damage_max', 0)}|{item_data.get('speed', 0)}|{item_data.get('wound_chance', 0)}"
        
        # 2. Add the "Bonus" data enabled by the higher limit: Raw OCR Text
        # This ensures 1:1 reconstruction even if parsing fails later
        raw_text = item_data.get('raw_ocr_text', '')
        if raw_text:
            # Compress the raw text to save space
            # Use safe substitutions to avoid delimiter collisions
            compressed_raw = zlib.compress(raw_text.encode('utf-8'), level=9)
            raw_b85 = base64.b85encode(compressed_raw).decode('utf-8').replace("|", "@P@").replace("!", "@E@")
            core_str += f"|RAW:{raw_b85}"
            
        # 3. Add Chroma Proof if available (Visual-first strategy)
        chroma = item_data.get('chroma_proof', '')
        if chroma:
            core_str += f"|CP:{chroma.replace('chromalink:', '')}"

        # 4. Final Encode
        final_compressed = zlib.compress(core_str.encode('utf-8'), level=9)
        b85 = base64.b85encode(final_compressed).decode('utf-8')
        return "lvs:" + b85_to_safe(b85)

    def decrypt_item_v11(self, link):
        import zlib
        import base64
        try:
            b85_data = link
            if b85_data.startswith("lvs:"):
                b85_data = b85_data.replace("lvs:", "")
            elif b85_data.startswith("itemlink v11:"):
                b85_data = b85_data.replace("itemlink v11:", "")
            
            # Safe decoding
            if not any(c in b85_data for c in ";&<>"):
                b85_data = b85_from_safe(b85_data)
                
            decompressed = zlib.decompress(base64.b85decode(b85_data)).decode('utf-8')
            parts = decompressed.split('|')
            
            item_data = {
                "name": parts[0],
                "item_type": parts[1]
            }
            
            if item_data["item_type"] == "Weapon" and len(parts) >= 6:
                item_data["damage_min"] = float(parts[2])
                item_data["damage_max"] = float(parts[3])
                item_data["speed"] = float(parts[4])
                item_data["wound_chance"] = float(parts[5])
                
            # Check for RAW text
            for p in parts:
                if p.startswith("RAW:"):
                    raw_b85 = p[4:].replace("@E@", "!").replace("@P@", "|")
                    raw_text = zlib.decompress(base64.b85decode(raw_b85)).decode('utf-8')
                    item_data["raw_ocr_text"] = raw_text
                elif p.startswith("CP:"):
                    item_data["chroma_proof"] = "chromalink:" + p[3:]
                    
            return item_data
        except:
            return None
    def quick_v10_scan(self):
        """One-click workflow for V11 reconstruction strategy (Doubled capacity)."""
        from PIL import ImageGrab, Image, ImageOps, ImageEnhance
        import io
        import zlib
        import base64
        import numpy as np
        
        if hasattr(self, 'v10_btn'):
            self.v10_btn.config(bg="orange", text="SCANNING CLIPBOARD...")
        
        self.status_label.config(text="Processing Quick Scan...", fg="#0066cc")
        self.window.update_idletasks()
        
        img = ImageGrab.grabclipboard()
        
        if not isinstance(img, Image.Image):
            self.status_label.config(text="Nothing to scan! (Clipboard empty)", fg="yellow")
            if hasattr(self, 'v10_btn'):
                self.v10_btn.config(bg="#333", text="COPY LINK CLIPBOARD")
            return

        # Attempt GPU acceleration via OpenCV if available
        gpu_active = False
        try:
            import cv2
            # Use UMat for OpenCL acceleration
            img_np = np.array(img.convert('RGB'))
            umat = cv2.UMat(img_np)
            gray_umat = cv2.cvtColor(umat, cv2.COLOR_RGB2GRAY)
            
            # Contrast and Sharpness equivalent in OpenCV
            alpha = 2.5
            beta = -100
            contrast_umat = cv2.addWeighted(gray_umat, alpha, gray_umat, 0, beta)
            
            # Laplacian for sharpening
            blurred_umat = cv2.GaussianBlur(contrast_umat, (0, 0), 3)
            sharp_umat = cv2.addWeighted(contrast_umat, 1.5, blurred_umat, -0.5, 0)
            
            processed_img_np = sharp_umat.get()
            processed_img = Image.fromarray(processed_img_np)
            gpu_active = True
        except:
            # Fallback to CPU-based PIL
            processed_img = img.convert('L')
            processed_img = ImageEnhance.Contrast(processed_img).enhance(2.5)
            processed_img = ImageEnhance.Sharpness(processed_img).enhance(2.0)

        # OCR
        if not pytesseract:
            self.status_label.config(text="OCR not available", fg="red")
            if hasattr(self, 'v10_btn'):
                self.v10_btn.config(bg="#333", text="COPY LINK CLIPBOARD")
            return

        try:
            # Multi-PSM strategy for maximum reliability
            ocr_text = ""
            for psm in [6, 4, 11]:
                text = pytesseract.image_to_string(processed_img, config=f'--psm {psm}')
                if text and len(text.strip()) > 10:
                    ocr_text = text
                    break
            
            if not ocr_text:
                ocr_text = pytesseract.image_to_string(img)

            if not ocr_text or len(ocr_text.strip()) < 2:
                self.status_label.config(text="OCR failed to find text.", fg="red")
                if hasattr(self, 'v10_btn'):
                    self.v10_btn.config(bg="#333", text="COPY LINK CLIPBOARD")
                return

            item_data = self._identify_item_from_text(ocr_text)
            if not item_data:
                item_data = {"name": "Quick Item", "item_type": "Misc", "damage_type": "None"}
            
            item_data["raw_ocr"] = ocr_text
            item_data["raw_ocr_text"] = ocr_text # For V11 packing
            
            # Generate Chroma Proof for visual-first reconstruction
            try:
                item_data["chroma_proof"] = self.chroma_compress(img)
            except:
                pass

            # Add metadata
            import time
            item_data["sender"] = "Me"
            item_data["channel"] = "Scanner"
            item_data["timestamp"] = time.strftime("%I:%M%p").lower()
            
            # Copy link to clipboard (Using V12 Ultra-Compact packing)
            link = self.encrypt_item_v12(item_data)
            set_clipboard_text(link)
            
            if hasattr(self, 'v10_btn'):
                self.v10_btn.config(bg="green", text="LINK COPIED!")
                # Reset after 10 seconds
                self.window.after(10000, lambda: self.v10_btn.config(bg="#333", text="COPY LINK CLIPBOARD"))
            
            self.status_label.config(text="COMPACT LINK COPIED!", fg="#00ff00")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            if hasattr(self, 'v10_btn'):
                self.v10_btn.config(bg="#333", text="COPY LINK CLIPBOARD")

    def toggle_wand(self):
        if self.item_wand.active:
            self.item_wand.stop()
            self.wand_btn.config(text="WAND SCAN", bg="#333")
        else:
            self.item_wand.start()
            self.wand_btn.config(text="WAND ACTIVE (STOP)", bg="#d31a17")

    def paste_and_scan(self):
        from PIL import ImageGrab, Image
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            self.process_image_direct(img)
            return
            
        try:
            import pyperclip
            from PIL import ImageGrab, Image
            import io

            # Try text first
            text = pyperclip.paste()
            if text and text.strip():
                self.process_scan(text)
                return

            # Try image from clipboard
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.status_label.config(text="Processing image from clipboard...", fg="white")
                self.window.update_idletasks()
                
                # Pre-process image for better OCR
                try:
                    # Convert to grayscale
                    processed_img = img.convert('L')
                    # Increase contrast
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(processed_img)
                    processed_img = enhancer.enhance(2.0)
                    
                    # Also try a sharper version
                    sharpener = ImageEnhance.Sharpness(processed_img)
                    processed_img = sharpener.enhance(1.5)
                except:
                    processed_img = img

                # Perform OCR on the image
                try:
                    import pytesseract
                    # Try with a few different configurations if the first one fails
                    configs = [
                        '--psm 6', # Assume a single uniform block of text
                        '--psm 4', # Assume a single column of text of variable sizes
                        '--psm 11' # Sparse text. Find as much text as possible in no particular order.
                    ]
                    
                    ocr_text = ""
                    for config in configs:
                        ocr_text = pytesseract.image_to_string(processed_img, config=config)
                        if ocr_text and ocr_text.strip():
                            break
                    
                    if not ocr_text or not ocr_text.strip():
                        # Try original image as fallback
                        ocr_text = pytesseract.image_to_string(img)

                    if ocr_text and ocr_text.strip():
                        self.process_scan(ocr_text)
                    else:
                        self.status_label.config(text="OCR found no text. Try AI ASSIST?", fg="yellow", cursor="hand2")
                        self.status_label.bind("<Button-1>", lambda e: self.send_to_ai(img))
                except Exception as e:
                    self.status_label.config(text=f"OCR Error: {str(e)}", fg="red")
            else:
                self.status_label.config(text="Clipboard is empty (no text or image)!", fg="yellow")
        except Exception as e:
            self.status_label.config(text=f"Paste error: {str(e)}", fg="red")

    def process_image_direct(self, img):
        """Processes an image directly (from clipboard or other windows) through OCR."""
        self.status_label.config(text="Processing image...", fg="white")
        self.window.update_idletasks()
        
        try:
            # Pre-processing
            processed_img = img.convert('L')
            from PIL import ImageEnhance
            processed_img = ImageEnhance.Contrast(processed_img).enhance(2.0)
            processed_img = ImageEnhance.Sharpness(processed_img).enhance(1.5)
            
            if pytesseract:
                configs = ['--psm 6', '--psm 4', '--psm 11']
                ocr_text = ""
                for config in configs:
                    ocr_text = pytesseract.image_to_string(processed_img, config=config)
                    if ocr_text and ocr_text.strip():
                        break
                
                if not ocr_text or not ocr_text.strip():
                    ocr_text = pytesseract.image_to_string(img)

                if ocr_text and ocr_text.strip():
                    # Notify app of new link activity
                    if hasattr(self.app, 'new_link_available'):
                        self.app.new_link_available = True
                    self.process_scan(ocr_text)
                else:
                    self.status_label.config(text="OCR found no text.", fg="yellow")
        except Exception as e:
            self.status_label.config(text=f"OCR Error: {str(e)}", fg="red")

    def show_drill_down(self, item):
        # Clear previous UI
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Drill Down Header with Back Button
        header = tk.Frame(self.content_container, bg="black")
        header.pack(fill=tk.X, pady=5)
        
        def go_back():
            self.show(force_open=True)

        tk.Button(header, text="< BACK", command=go_back,
                  bg="#333333", fg="white", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Label(header, text=item.get("name", "UNKNOWN").upper(), 
                 fg="#d31a17", bg="black", font=("Lilita One", 12)).pack(side=tk.LEFT, padx=10)

        # Scrollable area for stats
        container = tk.Frame(self.content_container, bg="black")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(container, bg="black", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="black")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=280) # Fixed width for alignment
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Reuse stats logic from ItemDetailWindow style
        stats = []
        item_type = item.get("item_type", "Weapon")
        
        if item_type == "Resource":
            res_stats = [
                ("Overall Quality", item.get("overall_quality")),
                ("Malleability", item.get("malleability")),
                ("Unit Toughness", item.get("unit_toughness")),
                ("Decay Resistance", item.get("decay_resistance")),
                ("Potential Energy", item.get("potential_energy")),
                ("Conductivity", item.get("conductivity")),
                ("Shock Resistance", item.get("shock_resistance")),
                ("Heat Resistance", item.get("heat_resistance")),
                ("Cold Resistance", item.get("cold_resistance")),
                ("Entangle Resistance", item.get("entangle_resistance")),
                ("Flavor", item.get("flavor"))
            ]
            for label, val in res_stats:
                if val is not None:
                    stats.append((label, str(val)))
        elif item_type == "Armor":
            stats = [
                ("Armor Rating", item.get("armor_rating", "None")),
                ("Condition", f"{item.get('condition', 0)} / {item.get('max_condition', 0)}"),
                ("Effectiveness", f"{item.get('effectiveness', 0)}%")
            ]
            for prot in ["Kinetic", "Energy", "Blast", "Stun", "Heat", "Cold", "Acid", "Electricity", "Environmental"]:
                val = item.get(prot.lower())
                if val: stats.append((prot, f"{val}%"))
            if item.get("health_cost"):
                stats.append(("Health Encumbrance", str(item.get('health_cost', 0))))
                stats.append(("Action Encumbrance", str(item.get('action_cost', 0))))
                stats.append(("Mind Encumbrance", str(item.get('mind_cost', 0))))
        elif item_type == "Component":
            if "mod_damage_min" in item: stats.append(("Minimum Damage", f"{item['mod_damage_min']:+d}"))
            if "mod_damage_max" in item: stats.append(("Maximum Damage", f"{item['mod_damage_max']:+d}"))
            if "mod_speed" in item: stats.append(("Speed Modifier", f"{item['mod_speed']:+.1f}"))
            if "mod_accuracy" in item: stats.append(("Accuracy Modifier", f"{item['mod_accuracy']:+d}"))
            if "mod_effectiveness" in item: stats.append(("Effectiveness Modifier", f"{item['mod_effectiveness']:+d}%"))
            if "use_count" in item: stats.append(("Uses", str(item['use_count'])))
        elif item_type == "Weapon":
            stats = [
                ("Weapon Type", item.get("weapon_type", "Unknown")),
                ("Min Damage", str(item.get('damage_min', 0))),
                ("Max Damage", str(item.get('damage_max', 0))),
                ("Attack Speed", f"{item.get('speed', 0.0):.1f}"),
                ("Damage Type", item.get("damage_type", "Kinetic")),
                ("Armor Piercing", item.get("armor_piercing", "None")),
                ("Wound Chance", f"{item.get('wound_chance', 0.0):.1f}%"),
            ]
            if item.get("acc_zero"):
                stats.append(("Accuracy", f"{item.get('acc_zero',0)} / {item.get('acc_mid',0)} / {item.get('acc_max',0)}"))
            if item.get("health_cost"):
                stats.append(("Health Cost", str(item.get('health_cost', 0))))
                stats.append(("Action Cost", str(item.get('action_cost', 0))))
                stats.append(("Mind Cost", str(item.get('mind_cost', 0))))
        
        # Sliced Status
        if item.get("is_sliced"):
            stats.append(("Status", "ALTERED / SLICED"))
        
        # Powerup Status
        if item.get("has_powerup"):
            stats.append(("Powerup", "ACTIVE"))
            pu_mods = item.get("powerup_stats", {})
            for pu_name, pu_val in pu_mods.items():
                stats.append((f"PU {pu_name}", f"{pu_val:+d}%"))

        # Skill Mods
        mods = item.get("skill_mods", {})
        for mod_name, mod_val in mods.items():
            stats.append((mod_name, f"+{mod_val}" if mod_val > 0 else str(mod_val)))

        for label, value in stats:
            row = tk.Frame(scroll_frame, bg="black")
            row.pack(fill=tk.X, pady=1)
            fg_color = "#CD853F" if label != "Status" else "#00FF00"
            tk.Label(row, text=f"{label}:", fg=fg_color, bg="black", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            tk.Label(row, text=f" {value}", fg="white", bg="black", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Action Button (Share to Discord)
        def share_discord():
            cipher = self.encrypt_item(item)
            self.send_to_discord_webhook(cipher)

        tk.Button(self.content_container, text="SHARE TO DISCORD", command=share_discord,
                  bg="#7289da", fg="white", font=("Lilita One", 10)).pack(fill=tk.X, padx=10, pady=5)

    def _on_canvas_resize(self, event):
        # Update reticle to match canvas borders
        w, h = event.width, event.height
        self.canvas.coords(self.reticle, 2, 2, w-2, h-2)

    def _get_obfuscated_key(self):
        # XOR key 0x7A from parser.c
        key_bytes = [0x1b, 0x5a, 0x0c, 0x1f, 0x08, 0x03, 0x5a, 0x09, 0x1f, 0x19, 0x0f, 0x08, 0x1f, 0x5a, 0x11, 0x1f, 0x03]
        return "".join(chr(b ^ 0x7A) for b in key_bytes)

    def chroma_compress(self, img):
        from PIL import Image, ImageOps, ImageEnhance
        import io
        import zlib
        import base64
        import numpy as np

        # Attempt GPU acceleration for Chroma Key
        try:
            import cv2
            img_np = np.array(img.convert('RGB'))
            umat = cv2.UMat(img_np)
            gray_umat = cv2.cvtColor(umat, cv2.COLOR_RGB2GRAY)
            
            # Thresholding via GPU
            _, thresh_umat = cv2.threshold(gray_umat, 150, 255, cv2.THRESH_BINARY)
            
            # Get bounding box using GPU-processed image
            thresh_np = thresh_umat.get()
            coords = cv2.findNonZero(thresh_np)
            if coords is not None:
                x, y, w, h = cv2.boundingRect(coords)
                thresh_np = thresh_np[y:y+h, x:x+w]
            
            # Resize via GPU
            target_w = 300 # Scaled to fit ~400 chars while being nearly double
            w_percent = (target_w / float(thresh_np.shape[1]))
            target_h = int((float(thresh_np.shape[0]) * float(w_percent)))
            
            # Re-upload for GPU resize
            tiny_umat = cv2.resize(cv2.UMat(thresh_np), (target_w, target_h), interpolation=cv2.INTER_NEAREST)
            text_only = Image.fromarray(tiny_umat.get()).convert('1')
        except:
            # CPU Fallback
            gray = ImageOps.grayscale(img)
            enhancer = ImageEnhance.Contrast(gray)
            high_contrast = enhancer.enhance(3.0)
            text_only = high_contrast.point(lambda p: 255 if p > 150 else 0).convert('1')
            bbox = text_only.getbbox()
            if bbox:
                text_only = text_only.crop(bbox)
            target_w = 300 # Scaled to fit ~400 chars while being nearly double
            w_percent = (target_w / float(text_only.size[0]))
            target_h = int((float(text_only.size[1]) * float(w_percent)))
            text_only = text_only.resize((target_w, target_h), Image.NEAREST)
            
        # 4. Encode
        img_byte_arr = io.BytesIO()
        text_only.save(img_byte_arr, format='PNG', optimize=True, bits=1)
        compressed = zlib.compress(img_byte_arr.getvalue(), level=9)
        b85_data = base64.b85encode(compressed).decode('utf-8')
        return "chromalink:" + b85_data

    def scan_item(self):
        self.status_label.config(text="Scanning...", fg="yellow")
        self.window.update()
        
        # Get coordinates of the canvas relative to screen
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Hide window briefly to capture screen below it
        self.window.attributes("-alpha", 0)
        self.window.update()
        
        try:
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            self.last_screenshot = screenshot # Keep for chroma proofing
        except Exception as e:
            self.status_label.config(text=f"Capture Error: {e}", fg="red")
            self.window.attributes("-alpha", self.app.current_alpha)
            return
        
        self.window.attributes("-alpha", self.app.current_alpha)
        self.window.update()
        
        if pytesseract:
            try:
                # Check version as a connectivity test
                pytesseract.get_tesseract_version()
                text = pytesseract.image_to_string(screenshot)
                self.process_scan(text)
            except Exception as e:
                import webbrowser
                err_msg = str(e)
                if "tesseract is not installed or it's not in your PATH" in err_msg.lower() or "no such file" in err_msg.lower():
                    self.status_label.config(text=f"OCR Error: Tesseract missing (Click to fix)", fg="orange", cursor="hand2")
                    self.status_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki"))
                else:
                    self.status_label.config(text=f"OCR Error: {e}", fg="red")
                print(f"[ERROR] OCR Error: {e}")
        else:
            self.status_label.config(text="OCR (pytesseract) not available", fg="red")

    def process_scan(self, text):
        # The user wants 1:1 raw OCR with zero filtering at the collection level.
        # We pass the raw text to the app's filter (identify_item) but keep the original.
        item_data = self._identify_item_from_text(text)
        
        # We ALWAYS proceed to preview now because we have the raw text.
        if item_data:
            item_data["raw_ocr"] = text
            self.show_scan_preview(item_data)
        else:
            # Fallback for completely unrecognizable text
            item_data = {
                "name": "Unidentified Scan",
                "item_type": "Misc",
                "damage_type": "None",
                "raw_ocr": text
            }
            self.show_scan_preview(item_data)

    def show_scan_preview(self, item_data):
        preview_win = tk.Toplevel(self.window)
        try:
            preview_win.attributes("-toolwindow", True)
        except: pass
        preview_win.title("SCAN PREVIEW & VERIFY")
        preview_win.geometry("600x700")
        preview_win.configure(bg="black")
        preview_win.transient(self.window)
        preview_win.grab_set()

        tk.Label(preview_win, text="VERIFY SCAN RESULTS", fg="#d31a17", bg="black", font=("Lilita One", 14)).pack(pady=10)

        # Upper section: Item Type selector
        type_frame = tk.Frame(preview_win, bg="black")
        type_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(type_frame, text="ITEM TYPE:", fg="white", bg="black", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        type_var = tk.StringVar(value=item_data.get("item_type", "Misc"))
        type_menu = tk.OptionMenu(type_frame, type_var, "Weapon", "Armor", "Resource", "Component", "Misc")
        type_menu.config(bg="#333", fg="white", width=12)
        type_menu.pack(side=tk.LEFT, padx=10)

        main_frame = tk.Frame(preview_win, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left side: Editable stats (Dynamic)
        edit_frame = tk.Frame(main_frame, bg="#1a1a1a", bd=1, relief=tk.SUNKEN)
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
        
        tk.Label(edit_frame, text="PARSED STATS", fg="white", bg="#1a1a1a", font=("Segoe UI", 10, "bold")).pack(pady=5)

        stat_container = tk.Frame(edit_frame, bg="#1a1a1a")
        stat_container.pack(fill=tk.BOTH, expand=True)

        entries = {}
        
        def render_fields(*args):
            for widget in stat_container.winfo_children():
                widget.destroy()
            entries.clear()
            
            curr_type = type_var.get()
            
            def add_entry(label_text, key, current_val):
                row = tk.Frame(stat_container, bg="#1a1a1a")
                row.pack(fill=tk.X, padx=5, pady=2)
                tk.Label(row, text=label_text, fg="#CD853F", bg="#1a1a1a", width=12, anchor=tk.W).pack(side=tk.LEFT)
                entry = tk.Entry(row, bg="#333", fg="white", insertbackground="white")
                val = str(current_val) if current_val is not None else ""
                if key == "name":
                    val = val.replace("Variation Of: ", "").replace("Variation Of:", "").strip()
                entry.insert(0, val)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                entries[key] = entry

            add_entry("Name:", "name", item_data.get("name", ""))
            
            if curr_type == "Weapon":
                add_entry("Min Dmg:", "damage_min", item_data.get("damage_min", 0))
                add_entry("Max Dmg:", "damage_max", item_data.get("damage_max", 0))
                add_entry("Speed:", "speed", item_data.get("speed", 0.0))
                add_entry("Wound %:", "wound_chance", item_data.get("wound_chance", 0.0))
                add_entry("Dmg Type:", "damage_type", item_data.get("damage_type", "Kinetic"))
                add_entry("Armor Pierc:", "armor_piercing", item_data.get("armor_piercing", "None"))
                add_entry("Wep Type:", "weapon_type", item_data.get("weapon_type", "Unknown"))
            elif curr_type == "Armor":
                add_entry("Effectiveness:", "effectiveness", item_data.get("effectiveness", 0))
                add_entry("Armor Rating:", "armor_rating", item_data.get("armor_rating", "None"))
                for prot in ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]:
                    add_entry(f"{prot.title()}:", prot, item_data.get(prot, 0))
            elif curr_type == "Resource":
                add_entry("OQ:", "overall_quality", item_data.get("overall_quality", 0))
                add_entry("UT:", "unit_toughness", item_data.get("unit_toughness", 0))
            elif curr_type == "Component":
                add_entry("Min Dmg Mod:", "mod_damage_min", item_data.get("mod_damage_min", 0))
                add_entry("Max Dmg Mod:", "mod_damage_max", item_data.get("mod_damage_max", 0))

        type_var.trace("w", render_fields)
        render_fields()

        # Right side: Raw OCR
        raw_frame = tk.Frame(main_frame, bg="#1a1a1a", bd=1, relief=tk.SUNKEN)
        raw_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        
        tk.Label(raw_frame, text="RAW OCR (1:1) - EDITABLE", fg="#00FF00", bg="#1a1a1a", font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        raw_text_box = tk.Text(raw_frame, bg="black", fg="#00FF00", font=("Consolas", 9), wrap=tk.WORD, undo=True)
        raw_text_box.insert(tk.END, item_data.get("raw_ocr", ""))
        raw_text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def re_scan():
            new_text = raw_text_box.get("1.0", tk.END)
            new_data = self._identify_item_from_text(new_text)
            if new_data:
                type_var.set(new_data.get("item_type", "Misc"))
                # Entries are refreshed by trace on type_var
                for k, entry in entries.items():
                    if k in new_data:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(new_data[k]))

        tk.Button(raw_frame, text="RE-SCAN EDITS", command=re_scan, bg="#333", fg="white").pack(pady=2)

        def confirm():
            # Update item_data from entries
            item_data["item_type"] = type_var.get()
            item_data["raw_ocr"] = raw_text_box.get("1.0", tk.END).strip()
            item_data["raw_ocr_text"] = item_data["raw_ocr"]
            
            # Generate Chroma Proof for visual-first reconstruction
            if hasattr(self, 'last_screenshot') and self.last_screenshot:
                try:
                    item_data["chroma_proof"] = self.chroma_compress(self.last_screenshot)
                except:
                    pass
            
            for key, entry in entries.items():
                val = entry.get()
                if key in ["damage_min", "damage_max", "effectiveness", "overall_quality", "unit_toughness", "mod_damage_min", "mod_damage_max", "kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]:
                    try: item_data[key] = int(float(val))
                    except: pass
                elif key in ["speed", "wound_chance"]:
                    try: item_data[key] = float(val)
                    except: pass
                else:
                    item_data[key] = val
            
            if self.validate_item(item_data):
                # Add metadata
                import time
                item_data["sender"] = "Me"
                item_data["channel"] = "Scanner"
                item_data["timestamp"] = time.strftime("%I:%M%p").lower()
                
                # Copy ultra-compact V12 link (Target 24 chars)
                cipher = self.encrypt_item_v12(item_data)
                self.status_label.config(text="Compact Link copied!", fg="#00ff00")
                
                set_clipboard_text(cipher)
                preview_win.destroy()
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", "Required fields (Name, Dmg Type) missing or invalid.")

        btn_frame = tk.Frame(preview_win, bg="black")
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="CANCEL", command=preview_win.destroy, bg="#333", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        
        def send_to_ai():
            raw = raw_text_box.get("1.0", tk.END).strip()
            if raw:
                self.app.open_uncle_rico()
                if hasattr(self.app, 'uncle_rico_win'):
                    self.app.uncle_rico_win._run_nlu(raw, is_ocr=True)
            preview_win.destroy()

        tk.Button(btn_frame, text="SEND TO AI", command=send_to_ai, bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        
        def send_to_chat():
            raw = raw_text_box.get("1.0", tk.END).strip()
            item_type = type_var.get()
            name = entries.get("name").get() if "name" in entries else "Unknown Item"
            
            summary = f"**{name}** ({item_type})\n"
            summary += "Parsed Stats:\n"
            for k, e in entries.items():
                if k != "name" and e.get():
                    summary += f"• {k.replace('_', ' ').title()}: {e.get()}\n"
            
            self.app.open_discord_chat()
            if hasattr(self.app, 'discord_win'):
                # We can't easily pass image here yet, but we can pass text
                # Or we can trigger a new screenshot of the preview window itself!
                self.app.discord_win.msg_entry.insert(0, summary)
                # We don't auto-send to allow review, or we could.
            preview_win.destroy()

        tk.Button(btn_frame, text="SHARE TO CHAT", command=send_to_chat, bg="#5865F2", fg="white", width=12).pack(side=tk.LEFT, padx=10)

        def send_to_discord():
            # Build a compact link and send it
            item_data = {}
            item_data["item_type"] = type_var.get()
            for key, entry in entries.items():
                val = entry.get()
                if key in ["damage_min", "damage_max", "effectiveness", "overall_quality", "unit_toughness", "mod_damage_min", "mod_damage_max", "kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]:
                    try: item_data[key] = int(float(val))
                    except: pass
                elif key in ["speed", "wound_chance"]:
                    try: item_data[key] = float(val)
                    except: pass
                else:
                    item_data[key] = val
            link = self.encrypt_item_v12(item_data)
            self.send_to_discord_webhook(link)

        tk.Button(btn_frame, text="SEND TO DISCORD", command=send_to_discord, bg="#5865F2", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="CREATE LINK", command=confirm, bg="#d31a17", fg="white", width=12).pack(side=tk.RIGHT, padx=10)
    
    def refresh_history(self):
        if hasattr(self, 'tree') and self.tree.winfo_exists():
            self.history = self._load_history() # Ensure we have latest
            
            # Filter out my own scans as requested
            # sender "Me" or matches app.char_id
            filtered_history = []
            for item in self.history:
                sender = item.get("sender", "Me")
                if sender == "Me": continue
                if hasattr(self.app, 'char_id') and sender == self.app.char_id: continue
                filtered_history.append(item)
                
            self.history = filtered_history
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for i, item in enumerate(self.history):
                name = item.get("name", "Unknown")
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree.insert("", tk.END, values=(name,), tags=(tag,))

    def show_history(self):
        history_win = tk.Toplevel(self.window)
        try:
            history_win.attributes("-toolwindow", True)
        except: pass
        history_win.title("SCAN HISTORY")
        history_win.geometry("250x300")
        history_win.configure(bg="black")
        
        tk.Label(history_win, text="RECENT SCANS", fg="#d31a17", bg="black", font=("Lilita One", 12)).pack(pady=5)
        
        listbox = tk.Listbox(history_win, bg="#1a1a1a", fg="white", selectbackground="#d31a17")
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for i, item in enumerate(self.history):
            listbox.insert(tk.END, f"{item.get('name', 'Unknown')}")
            
        def open_selected():
            idx = listbox.curselection()
            if idx:
                item = self.history[idx[0]]
                from windows.item_detail import ItemDetailWindow
                detail = ItemDetailWindow(self.app, "History", item)
                detail.show(force_open=True)
                history_win.destroy()
        
        tk.Button(history_win, text="OPEN", command=open_selected, bg="#d31a17", fg="white").pack(pady=5)

    def _identify_item_from_text(self, text):
        if not text: return None
        # Scan for predefined custom items first
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            normalized_name = lines[0].upper()
            if normalized_name in self.custom_items:
                return self.custom_items[normalized_name]

        # Attribute extraction engine for weapons, resources, and armor
        data = {
            "name": "Unknown Item",
            "item_type": "Misc",
            "damage_type": "None",
            "skill_mods": {}
        }

        import re
        
        # Determine item identity from primary identifier (Skipping noise)
        if lines:
            for line in lines:
                candidate = line.upper()
                # Skip noise lines that often appear at the top of OCR
                # Only skip if the line IS exactly the noise or just a header
                if candidate in ["[INVENTORY]", "GROUP CHAT", "SPATIAL CHAT", "TELL", "CHAT", "LOG", "PLAYER", "TARGET", "INVENTORY", "SCAN PREVIEW & VERIFY", "VERIFY SCAN RESULTS", "SCANNER"]:
                    continue
                # Also check for "TARGET: <Name>" or "PLAYER: <Name>" which are headers
                if candidate.startswith("TARGET:") or candidate.startswith("PLAYER:") or candidate.startswith("INVENTORY:") or candidate.startswith("SCAN PREVIEW"):
                    continue
                # If the line is too short or just a single character, it might be OCR noise
                if len(line.strip()) <= 1:
                    continue
                data["name"] = line.replace("Variation Of: ", "").replace("Variation Of:", "").strip()
                break
        
        # Sliced detection
        if "altered" in text.lower() or "sliced" in text.lower():
            data["is_sliced"] = True
        
        # Powerup detection
        if "powerup" in text.lower():
            data["has_powerup"] = True
            data["powerup_stats"] = {}
        
        # If still unknown name, take first line
        if data["name"] == "Unknown Item" and lines:
            data["name"] = lines[0].replace("Variation Of: ", "").replace("Variation Of:", "").strip()

        found_any = False
        for line in lines:
            l = line.lower()
            
            # Classification logic
            if any(x in l for x in ["pistol", "carbine", "rifle", "sword", "2h", "axe", "polearm", "heavy", "blaster", "unarmed", "curved"]):
                # Ensure it's not a component part (like "Blaster Rifle Barrel")
                if "component" not in l and "module" not in l and "core" not in l and "segment" not in l and "barrel" not in l:
                    data["item_type"] = "Weapon"
                    data["weapon_type"] = "Unknown"
                    if "pistol" in l: data["weapon_type"] = "Pistol"
                    elif "carbine" in l: data["weapon_type"] = "Carbine"
                    elif "rifle" in l: data["weapon_type"] = "Rifle"
                    elif "sword" in l: data["weapon_type"] = "1H Sword"
                    elif "2h" in l: data["weapon_type"] = "2H Sword"
                    elif "axe" in l: data["weapon_type"] = "Axe"
                    elif "polearm" in l: data["weapon_type"] = "Polearm"
                    elif "heavy" in l: data["weapon_type"] = "Heavy"
                    elif "unarmed" in l: data["weapon_type"] = "Unarmed"
                    elif "curved" in l: data["weapon_type"] = "2H Sword"
                    elif "blaster" in l:
                        # Fallback for blaster items that don't specify type on same line
                        if "rifle" in text.lower(): data["weapon_type"] = "Rifle"
                        elif "pistol" in text.lower(): data["weapon_type"] = "Pistol"
                        elif "carbine" in text.lower(): data["weapon_type"] = "Carbine"

            if ("armor" in l or "protection" in l) and "armor piercing" not in l:
                data["item_type"] = "Armor"

            if "component" in l or "module" in l or "core" in l or "segment" in l or "vibro" in l or "barrel" in l:
                data["item_type"] = "Component"

            # Numeric value extraction - Weapons
            if data["item_type"] == "Weapon" or any(x in l for x in ["damage", "speed", "wound", "accuracy", "range"]):
                # Match "damage: 100 - 200" or "damage: 100-200" or "damage 100-200"
                dmg_range_match = re.search(r"damage\s*:?\s*(\d+)\s*[-\s]\s*(\d+)", l)
                if dmg_range_match:
                    data["damage_min"] = int(dmg_range_match.group(1))
                    data["damage_max"] = int(dmg_range_match.group(2))
                    data["item_type"] = "Weapon"
                    found_any = True
                else:
                    # Try explicit "Min Damage" and "Max Damage"
                    min_match = re.search(r"(?:min(?:imum)?)\s*damage\s*:?\s*(\d+)", l)
                    if min_match:
                        data["damage_min"] = int(min_match.group(1))
                        data["item_type"] = "Weapon"
                        found_any = True
                        # If we haven't found max yet, default it to min
                        if "damage_max" not in data: data["damage_max"] = data["damage_min"]
                    
                    max_match = re.search(r"(?:max(?:imum)?)\s*damage\s*:?\s*(\d+)", l)
                    if max_match:
                        data["damage_max"] = int(max_match.group(1))
                        data["item_type"] = "Weapon"
                        found_any = True
                        # If we haven't found min yet, default it to max
                        if "damage_min" not in data: data["damage_min"] = data["damage_max"]
                    
                    # Try single value damage: "damage: 124"
                    if not dmg_range_match and not min_match and not max_match:
                        dmg_match_single = re.search(r"damage\s*:?\s*(\d+)", l)
                        if dmg_match_single and not re.search(r"damage\s*:?\s*[+-]\d+", l):
                            val = int(dmg_match_single.group(1))
                            if "min" not in data: data["damage_min"] = val
                            if "max" not in data: data["damage_max"] = val
                            data["item_type"] = "Weapon"
                            found_any = True

                # Match "speed: 1.5" or "speed 1.5" or "attack speed: 1.5"
                speed_match = re.search(r"(?:attack\s+)?speed\s*:?\s*([\d.]+)", l)
                if speed_match:
                    data["speed"] = float(speed_match.group(1))
                    found_any = True

                # Match "wound chance: 15.0" or "wound 15"
                wound_match = re.search(r"wound\s*(?:chance)?\s*:?\s*([\d.]+)", l)
                if wound_match:
                    data["wound_chance"] = float(wound_match.group(1))
                    found_any = True

            # Armor Stats
            if "armor rating" in l:
                if "none" in l: data["armor_rating"] = "None"
                elif "light" in l: data["armor_rating"] = "Light"
                elif "medium" in l: data["armor_rating"] = "Medium"
                elif "heavy" in l: data["armor_rating"] = "Heavy"
                data["item_type"] = "Armor"
                found_any = True

            eff_match = re.search(r"effectiveness\s*:?\s*(\d+)\s*%", l)
            if eff_match:
                data["effectiveness"] = int(eff_match.group(1))
                data["item_type"] = "Armor"
                found_any = True

            # Individual Protections
            for prot in ["kinetic", "energy", "blast", "stun", "heat", "fire", "cold", "acid", "electricity", "environmental"]:
                # Match "Kinetic: 40%" or "Kinetic 40%" or "Kinetic: 40"
                prot_match = re.search(rf"{prot}\s*:?\s*(\d+)\s*%?", l)
                if prot_match:
                    pname = prot
                    if pname == "fire": pname = "heat"
                    data[pname] = int(prot_match.group(1))
                    data["item_type"] = "Armor"
                    found_any = True

            # Component Modifiers
            mod_dmg_match = re.search(r"(?:damage|min(?:imum)?\s*damage|max(?:imum)?\s*damage)\s*:?\s*([+-]?\d+)", l)
            if mod_dmg_match and not l.lower().strip().startswith("damage:"): # Avoid overriding weapon base damage
                val = int(mod_dmg_match.group(1))
                if "min" in l:
                    data["mod_damage_min"] = val
                    data["skill_mods"]["Minimum Damage"] = val
                elif "max" in l:
                    data["mod_damage_max"] = val
                    data["skill_mods"]["Maximum Damage"] = val
                elif "+" in l or "-" in l:
                    data["mod_damage_min"] = val
                    data["mod_damage_max"] = val
                    data["skill_mods"]["Damage"] = val
                
                # If we found any component-specific damage mod, it might be a component
                # But we check if it's already a weapon first
                if data["item_type"] != "Weapon" and ("min" in l or "max" in l or "+" in l or "-" in l):
                    data["item_type"] = "Component"
                    found_any = True
                
            use_match = re.search(r"use\s*count\s*:?\s*(\d+)", l)
            if use_match:
                data["use_count"] = int(use_match.group(1))
                data["skill_mods"]["Use Count"] = int(use_match.group(1))
                found_any = True

            mod_speed_match = re.search(r"speed\s*([+-][\d.]+)", l)
            if mod_speed_match:
                val = float(mod_speed_match.group(1))
                data["mod_speed"] = val
                data["item_type"] = "Component"
                found_any = True
                data["skill_mods"]["Speed"] = val

            mod_acc_match = re.search(r"accuracy\s*([+-]\d+)", l)
            if mod_acc_match:
                val = int(mod_acc_match.group(1))
                data["mod_accuracy"] = val
                data["item_type"] = "Component"
                found_any = True
                data["skill_mods"]["Accuracy"] = val

            mod_eff_match = re.search(r"effectiveness\s*([+-]\d+)%", l)
            if mod_eff_match:
                val = int(mod_eff_match.group(1))
                data["mod_effectiveness"] = val
                data["item_type"] = "Component"
                found_any = True
                data["skill_mods"]["Effectiveness"] = val

            # Resource Attribute Scanning
            trait_patterns = {
                "cold resistance": "cold_resistance",
                "conductivity": "conductivity",
                "decay resistance": "decay_resistance",
                "entangle resistance": "entangle_resistance",
                "flavor": "flavor",
                "heat resistance": "heat_resistance",
                "malleability": "malleability",
                "potential energy": "potential_energy",
                "overall quality": "overall_quality",
                "shock resistance": "shock_resistance",
                "unit toughness": "unit_toughness"
            }

            # General stat mapping for component/misc (Generic labels)
            generic_matches = re.finditer(r"([a-zA-Z\s]+)\s*:?\s*([\d.]+)", l)
            for generic_match in generic_matches:
                stat_name_raw = generic_match.group(1).strip()
                if not stat_name_raw: continue
                stat_name = stat_name_raw.title()
                try:
                    stat_val = float(generic_match.group(2))
                    # Only accept if there's a colon OR it's a known numeric stat format
                    has_colon = ":" in l
                    is_known_stat = stat_name.lower() in ["damage", "speed", "accuracy", "effectiveness", "range", "overall quality", "unit toughness", "nutrition", "organic", "inorganic", "charges", "uses"] or stat_name.lower() in trait_patterns
                    
                    if (has_colon or is_known_stat) and stat_name.lower() not in ["condition", "health", "action", "mind", "speed", "range"] and stat_name.lower() not in trait_patterns:
                        data["skill_mods"][stat_name] = stat_val
                        found_any = True
                except ValueError:
                    continue
            
            for trait, target_key in trait_patterns.items():
                if trait in l:
                    val_search = re.search(rf"{trait}\s*:?\s*(\d+)", l)
                    if val_search:
                        data[target_key] = int(val_search.group(1))
                        data["item_type"] = "Resource"
                        found_any = True

            # Condition
            cond_match = re.search(r"condition\s*:?\s*(\d+)\s*/\s*(\d+)", l)
            if cond_match:
                data["condition"] = int(cond_match.group(1))
                data["max_condition"] = int(cond_match.group(2))
                found_any = True

            # Skill Mods (e.g., "Bleed Resistance +5")
            # Improved regex to handle cases where there might be a colon or just a space
            mod_matches = re.finditer(r"([a-zA-Z\s]+)\s*:?\s*([+-]\d+)", l)
            for mod_match in mod_matches:
                mod_name_raw = mod_match.group(1).strip()
                if not mod_name_raw: continue
                mod_name = mod_name_raw.title()
                mod_val = int(mod_match.group(2))
                # Filter out things that aren't mods (like damage ranges or costs handled elsewhere)
                if mod_name.lower() not in ["damage", "speed", "condition", "range", "accuracy", "health", "action", "mind", "dh", "t", "a", "wound", "fire", "effectiveness", "kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity", "environmental", "type"]:
                    data["skill_mods"][mod_name] = mod_val
                    found_any = True

            # Existing patterns
            if "damage type" in l or "type" in l:
                # SWG uses both "Heat" and "Fire" sometimes, but "Heat" is the protection name.
                # In weapons it usually says "Damage Type: Kinetic" etc.
                for dt in ["Kinetic", "Energy", "Fire", "Heat", "Cold", "Acid", "Electricity", "Stun", "Blast"]:
                    if dt.lower() in l:
                        # Normalize Fire to Heat for consistency if needed, but SWG uses Heat for Armor.
                        # Actually V6_DAMAGE_TYPES uses "Heat".
                        display_dt = dt
                        if dt == "Fire": display_dt = "Heat"
                        data["damage_type"] = display_dt
                        break

            # Powerup stats extraction (e.g., "Speed: +10%", "Damage: +15%")
            if "powerup" in l:
                # Often powerup stats follow the line containing "Powerup"
                pass 
            
            # In SWG, powerup stats are often listed as "Attribute: +Value%" or similar
            # Look for lines like "Attack Speed: +12%" inside a powerup-enabled weapon
            if data.get("has_powerup") and ("+" in l or "%" in l):
                pu_match = re.search(r"([a-zA-Z\s]+)\s*:?\s*([+-]\d+)\s*%", l)
                if pu_match:
                    stat_name = pu_match.group(1).strip().title()
                    stat_val = int(pu_match.group(2))
                    data["powerup_stats"][stat_name] = stat_val

            if "armor piercing" in l:
                if "none" in l: data["armor_piercing"] = "None"
                elif "light" in l: data["armor_piercing"] = "Light"
                elif "medium" in l: data["armor_piercing"] = "Medium"
                elif "heavy" in l: data["armor_piercing"] = "Heavy"

            range_match = re.search(r"range\s*:?\s*(\d+)\s+(\d+)\s+(\d+)", l)
            if range_match:
                data["range_zero"] = float(range_match.group(1))
                data["range_mid"] = float(range_match.group(2))
                data["range_max"] = float(range_match.group(3))
                found_any = True
            
            # Accuracy
            acc_match = re.search(r"accuracy\s*:?\s*([+-]?\d+)\s+([+-]?\d+)\s+([+-]?\d+)", l)
            if acc_match:
                data["acc_zero"] = int(acc_match.group(1))
                data["acc_mid"] = int(acc_match.group(2))
                data["acc_max"] = int(acc_match.group(3))
                found_any = True
            else:
                # Try individual accuracy labels if listed separately
                # e.g. "Accuracy (Point Blank): 10", "Accuracy (Mid Range): 5", "Accuracy (Long Range): -5"
                if "accuracy" in l:
                    val_match = re.search(r"([+-]?\d+)", l)
                    if val_match:
                        val = int(val_match.group(1))
                        if "point blank" in l or "zero" in l: data["acc_zero"] = val
                        elif "mid" in l: data["acc_mid"] = val
                        elif "max" in l or "long" in l: data["acc_max"] = val
                        found_any = True

            usage_metrics = re.findall(r"(health|action|mind)\s+:?\s*(\d+)", l)
            if usage_metrics:
                for u_name, u_val in usage_metrics:
                    data[f"{u_name}_cost"] = int(u_val)
                    found_any = True

            # Explicit Cost extraction
            for cost_type in ["health", "action", "mind"]:
                # Matches "Health: 10" or "Health Cost: 10" or "Health 10" or "Health Encumbrance: 10"
                cost_match = re.search(rf"{cost_type}\s*(?:cost|encumbrance)?\s*:?\s*(\d+)", l)
                if cost_match and f"{cost_type}_cost" not in data:
                    data[f"{cost_type}_cost"] = int(cost_match.group(1))
                    found_any = True
                
                # Try block format if separate
                if cost_type in l and f"{cost_type}_cost" not in data:
                    val_match = re.search(r"(\d+)", l)
                    if val_match:
                        # Ensure we don't pick up something else like "Health +5" as cost
                        if "+" not in l and "-" not in l:
                            data[f"{cost_type}_cost"] = int(val_match.group(1))
                            found_any = True

        return data

    def validate_item(self, item):
        try:
            validate(instance=item, schema=ITEM_SCHEMA)
            return True
        except jsonschema.exceptions.ValidationError as e:
            print(f"Validation error: {e}")
            return False

    def encrypt_item(self, item):
        # v12 format: 16-byte Stateless Compact (Target: 24 characters)
        return self.encrypt_item_v12(item)

    def encrypt_item_old(self, item):
        # v6 format: 16-byte Stateless Compact (Target: ~23 characters)
        try:
            b = bytearray()
            itype = V6_ITEM_TYPES.get(item.get("item_type"), 0)
            
            if itype == 0: # Weapon
                # 1: Type(2) | WepType(3) | DmgType(3)
                header = (itype << 6) | (V6_WEAPON_CATEGORIES.get(item.get("weapon_type"), 0) << 3) | (V6_DAMAGE_TYPES.get(item.get("damage_type"), 0) & 0x07)
                b.append(header)
                # 2: AP(2) | Speed(6: val*10)
                ap = V6_AP_LEVELS.get(item.get("armor_piercing"), 0)
                speed = int(min(item.get("speed", 0) * 10, 63))
                b.append((ap << 6) | speed)
                # 3-5: DmgMin(10) | DmgMax(10) | Wound(4)
                dmin = int(item.get("damage_min", 0)) & 0x3FF
                dmax = int(item.get("damage_max", 0)) & 0x3FF
                # Store wound * 10 to preserve one decimal place (max 15.9)
                # We need more bits. Let's steal 4 bits from the unused space in the flag byte
                # or just use a dedicated byte for wound if we want full precision.
                # Actually, the current 4 bits only allow 0-15.
                # If we round it, 10.1 becomes 10, which is acceptable.
                wound_packed = int(round(item.get("wound_chance", 0))) & 0x0F
                val = (dmin << 14) | (dmax << 4) | wound_packed
                b.extend(val.to_bytes(3, 'big'))
                
                # 6-8: Accuracy (Zero/Mid/Max - 3x8 bits = 24 bits = 3 bytes)
                b.append(int(max(-128, min(127, item.get("acc_zero", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_mid", 0)))) & 0xFF)
                b.append(int(max(-128, min(127, item.get("acc_max", 0)))) & 0xFF)
                
                # Flags (Sliced, Powerup) - Uses spare bits or extra byte
                # We'll use 1 byte for flags at index 8
                flags = 0
                if item.get("is_sliced"): flags |= 0x01
                if item.get("has_powerup"): flags |= 0x02
                
                # Boundary check: Ensure we have exactly 9 bytes before appending flags
                while len(b) < 8: b.append(0)
                b.append(flags)

                # 9-12: Name Truncated (4 chars)
                name = item.get("name", "ITEM")[:4].upper().ljust(4)
                b.extend(name.encode('ascii', 'ignore'))
            
            elif itype == 1: # Armor
                # 1: Type(2) | Rating(2) | Eff(4)
                rating = V6_ARMOR_RATINGS.get(item.get("armor_rating"), 0)
                eff = int(min(item.get("effectiveness", 0) // 5, 15)) # 0-75% in 5% steps
                b.append((itype << 6) | (rating << 4) | eff)
                # 2-4: Protections (8 stats, 3 bits each = 24 bits = 3 bytes)
                # 0=0%, 1=10%, 2=20% ... 7=70%+
                prots = [item.get(p, 0) for p in ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]]
                p_val = 0
                for p in prots:
                    p_val = (p_val << 3) | int(min(p // 10, 7))
                b.extend(p_val.to_bytes(3, 'big'))
                # 5-8: Name
                name = item.get("name", "ARMO")[:4].upper().ljust(4)
                b.extend(name.encode('ascii', 'ignore'))

            elif itype == 2: # Resource
                # 1: Type(2) | ClassIdx(6) - Simplified
                b.append((itype << 6) | 0) 
                # 2-5: OQ(10) | T1(10) | T1_Idx(4) | T2(10) | T2_Idx(4) = 38 bits -> 5 bytes
                traits = []
                for t in V6_RESOURCE_TRAITS:
                    if item.get(t): traits.append((t, item[t]))
                # Sort by value but keep OQ at top if available
                traits.sort(key=lambda x: x[1], reverse=True)
                
                oq = int(item.get("overall_quality", 0)) & 0x3FF
                t1_val = 0
                t1_idx = 0
                t2_val = 0
                t2_idx = 0
                
                # Filter out OQ from traits list to pick two other top traits
                other_traits = [t for t in traits if t[0] != "overall_quality"]
                
                if len(other_traits) > 0:
                    t1_val = int(other_traits[0][1]) & 0x3FF
                    t1_idx = V6_RESOURCE_TRAITS_MAP.get(other_traits[0][0], 0) & 0x0F
                if len(other_traits) > 1:
                    t2_val = int(other_traits[1][1]) & 0x3FF
                    t2_idx = V6_RESOURCE_TRAITS_MAP.get(other_traits[1][0], 0) & 0x0F
                
                # Packing: OQ(10) | T1V(10) | T1I(4) | T2V(10) | T2I(4) = 38 bits
                val = (oq << 28) | (t1_val << 18) | (t1_idx << 14) | (t2_val << 4) | t2_idx
                b.extend(val.to_bytes(5, 'big'))
                # 7-10: Name
                name = item.get("name", "RESO")[:4].upper().ljust(4)
                b.extend(name.encode('ascii', 'ignore'))
            
            else: # Default/Component
                # 1: Type(2) | Unused(6)
                b.append((itype << 6))
                # 2-5: Best 2 stats (Dmg, Speed)
                d_mod = int(item.get("mod_damage_min", 0) * 10) & 0x3FF
                s_mod = int(item.get("mod_speed", 0) * 100) & 0x3FF
                val = (d_mod << 10) | s_mod
                b.extend(val.to_bytes(3, 'big'))
                # 5-12: Name (Up to 8 chars)
                name = item.get("name", "ITEM")[:8].upper().ljust(8)
                b.extend(name.encode('ascii', 'ignore'))

            # Final encryption: pad to 16 bytes (one AES block)
            key = self.encryption_key.encode('utf-8').ljust(32)[:32]
            iv = b"LivyLogsShortIV1"
            
            # Add safety check: if the resulting cipher contains restricted combinations,
            # we add a random salt and retry.
            for retry in range(100):
                temp_b = bytearray(b)
                # Byte 15 is reserved for safety salt if needed
                while len(temp_b) < 15: temp_b.append(0)
                temp_b.append(random.randint(0, 255) if retry > 0 else 0)
                
                cipher = AES.new(key, AES.MODE_CBC, iv)
                encrypted = cipher.encrypt(bytes(temp_b[:16]))
                b85_std = base64.b85encode(encrypted).decode('utf-8')
                link_text = b85_to_safe(b85_std)
                
                if self.is_cipher_clean(link_text):
                    return "lvs:" + link_text
                    
            # Fallback to standard if safety loop fails
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(bytes(b[:16]))
            return "lvs:" + b85_to_safe(base64.b85encode(encrypted).decode('utf-8'))
        except Exception as e:
            print(f"v6 encryption error: {e}")
            return self.encrypt_item_v4(item)

    def encrypt_item_v4(self, item):
        # v4 format: Bit-packed binary + Base85 + Static IV + short prefix 'il:'
        # This is for ultimate space efficiency (Target: < 80 chars)
        try:
            payload = {}
            for k, v in item.items():
                k_idx = V4_KEY_MAP.get(k, k)
                if isinstance(v, str) and v in V4_VAL_MAP:
                    v = V4_VAL_MAP[v]
                payload[k_idx] = v
            
            # Using MsgPack or similar binary format would be better, but let's stick to compact JSON + Zlib
            # for now, but with aggressive value mapping.
            json_data = json.dumps(payload, separators=(',', ':'))
            import hashlib
            checksum = hashlib.md5(json_data.encode()).digest()[:1] # 1 byte checksum
            compressed = zlib.compress(json_data.encode('utf-8'), level=9)
            data = checksum + compressed
            
            key = self.encryption_key.encode('utf-8').ljust(32)[:32]
            iv = b"LivyLogsShortIV1" # 16 byte static IV
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(data, AES.block_size))
            
            # Return with 'lvs:' prefix
            b85 = base64.b85encode(encrypted).decode('utf-8')
            return "lvs:" + b85_to_safe(b85)
        except Exception as e:
            print(f"v4 encryption error: {e}")
            # Fallback to v3 if v4 fails
            return self.encrypt_item_v3(item)

    def encrypt_item_v3(self, item):
        # v3 format: Aggressive compression + Base85 + Static IV
        compact_item = {}
        for k, v in item.items():
            if k in V2_KEY_MAP:
                compact_item[V2_KEY_MAP[k]] = v
            else:
                compact_item[k] = v
        
        # Use a 2-byte checksum for integrity instead of random salt to save space
        json_data = json.dumps(compact_item, separators=(',', ':'))
        import hashlib
        checksum = hashlib.md5(json_data.encode()).digest()[:2]
        # Compress
        compressed_data = zlib.compress(json_data.encode('utf-8'))
        data = checksum + compressed_data
        
        key = self.encryption_key.encode('utf-8').ljust(32)[:32] # Ensure 32 bytes
        iv = b"LivyLogsStaticIV" # Fixed IV to save 16 bytes in the payload
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(pad(data, AES.block_size))
        # v3 prefix and Base85 (more compact than Base64)
        b85_std = base64.b85encode(encrypted_data).decode('utf-8')
        return "lvs:" + b85_to_safe(b85_std)

    def decrypt_item(self, cipher_text):
        """Decrypt an item link received from another player."""
        if not AES:
            return None
            
        try:
            if cipher_text.startswith("lvs:"):
                raw_data = cipher_text[4:]
            else:
                raw_data = cipher_text
                
            encrypted_data = base64.b85decode(raw_data)
            key = self.encryption_key.encode('utf-8').ljust(32)[:32]
            iv = b"LivyLogsShortIV1"
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted_data)
            
            # Remove padding
            pad_len = decrypted[-1]
            if pad_len < 16:
                decrypted = decrypted[:-pad_len]
            
            # Try JSON format first (new simplified format)
            try:
                data = json.loads(decrypted.decode('utf-8'))
                
                if data.get("t") == "res":
                    return {
                        "name": data.get("n", "Resource"),
                        "item_type": "Resource",
                        "overall_quality": data.get("oq", 0),
                        "unit_toughness": data.get("ut", 0)
                    }
                elif data.get("t") == "img":
                    return {
                        "name": "Scanned Item",
                        "item_type": "Misc",
                        "chroma_proof": data.get("c", "")
                    }
                
                return data
            except:
                pass
            
            # Try V12 format (16 bytes)
            if len(decrypted) >= 16:
                itype = (decrypted[0] >> 6)
                name = decrypted[8:16].decode('ascii', 'ignore').strip()
                
                if itype == 0:  # Weapon
                    cat_idx = (decrypted[0] >> 3) & 0x07
                    dt_idx = decrypted[0] & 0x07
                    val = int.from_bytes(decrypted[1:4], 'big')
                    dmin = (val >> 14) & 0x3FF
                    dmax = (val >> 4) & 0x3FF
                    ap_idx = (val >> 2) & 0x03
                    byte4 = decrypted[4]
                    speed = (byte4 >> 2) / 10.0
                    wound = (byte4 & 0x03) * 5
                    
                    weapon_types = {0: "Pistol", 1: "Carbine", 2: "Rifle", 3: "1H Sword", 4: "2H Sword", 5: "Axe", 6: "Polearm", 7: "Unarmed"}
                    damage_types = {0: "Energy", 1: "Kinetic", 2: "Blast", 3: "Stun", 4: "Heat", 5: "Cold", 6: "Acid", 7: "Electricity", 8: "None"}
                    ap_levels = {0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}
                    
                    return {
                        "name": name, "item_type": "Weapon",
                        "weapon_type": weapon_types.get(cat_idx, "Unknown"),
                        "damage_type": damage_types.get(dt_idx, "Kinetic"),
                        "armor_piercing": ap_levels.get(ap_idx, "None"),
                        "damage_min": dmin, "damage_max": dmax,
                        "speed": speed, "wound_chance": float(wound)
                    }
                elif itype == 1:  # Armor
                    rating_idx = (decrypted[0] >> 4) & 0x03
                    armor_ratings = {0: "None", 1: "Light", 2: "Medium", 3: "Heavy"}
                    return {
                        "name": name, "item_type": "Armor",
                        "armor_rating": armor_ratings.get(rating_idx, "None")
                    }
                elif itype == 2:  # Resource
                    return {
                        "name": name, "item_type": "Resource",
                        "damage_type": "None"
                    }
                else:  # Component
                    return {
                        "name": name, "item_type": "Component",
                        "damage_type": "None"
                    }
                    
            return None
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
