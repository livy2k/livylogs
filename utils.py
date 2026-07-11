"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import ctypes
from ctypes import wintypes
from datetime import datetime
from constants import user32, SNAP_THRESHOLD

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    import os
    import sys
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_window_minimized(hwnd):
    """Checks if a window is minimized using Win32 API."""
    from constants import WINDOWPLACEMENT
    placement = WINDOWPLACEMENT()
    placement.length = ctypes.sizeof(WINDOWPLACEMENT)
    if user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
        return placement.showCmd == 2 # SW_SHOWMINIMIZED
    return False

def apply_snapping(window, x, y):
    """Applies snapping to screen edges."""
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    ww = window.winfo_width()
    wh = window.winfo_height()

    if abs(x) < SNAP_THRESHOLD: x = 0
    if abs(y) < SNAP_THRESHOLD: y = 0
    if abs(x + ww - sw) < SNAP_THRESHOLD: x = sw - ww
    if abs(y + wh - sh) < SNAP_THRESHOLD: y = sh - wh
    
    return x, y

def extract_character_id(file_path):
    """Extracts character name or ID from log filename."""
    import os
    import re
    if not file_path: return ""
    filename = os.path.basename(file_path)
    # Match something like "281474996439106_chatlog.txt" or "Livy_chatlog.txt"
    match = re.match(r"^(?P<id>.+?)_chatlog\.txt", filename, re.IGNORECASE)
    if match:
        return match.group("id")
    return ""

def create_rainbow_name(parent, app, name, base_color, font, bg):
    """Creates a gradient name inside the parent frame if multiple classes exist."""
    import tkinter as tk
    from constants import COLOR_DEFAULT_CLASS
    
    classes = app.player_classes.get(name, [])
    if len(classes) <= 1:
        color = base_color
        if classes:
            color = app.class_configs.get(classes[0], {}).get("color", COLOR_DEFAULT_CLASS)
        
        lbl = tk.Label(parent, text=name, bg=bg, fg=color, font=font)
        lbl.pack(side=tk.LEFT)
        return [lbl]

    # Helper to interpolate between two hex colors
    def interpolate_color(c1_name, c2_name, factor):
        try:
            # Convert names/hex to RGB
            rgb1 = parent.winfo_rgb(c1_name)
            rgb2 = parent.winfo_rgb(c2_name)
            
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * factor) >> 8
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * factor) >> 8
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * factor) >> 8
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return c1_name

    # Multiple classes - gradient mode
    labels = []
    # Check if we should show class colors
    if not getattr(app, "show_class_colors", tk.BooleanVar(value=True)).get():
        lbl = tk.Label(parent, text=name, bg=bg, fg=base_color, font=font)
        lbl.pack(side=tk.LEFT)
        return [lbl]

    # Get colors for all classes
    colors = [app.class_configs.get(cls_name, {}).get("color", COLOR_DEFAULT_CLASS) for cls_name in classes]
    
    # Reorder colors per user clarification:
    # 1st color -> leftmost
    # 2nd color -> rightmost
    # Further colors (3rd, 4th, ...) push the 2nd color towards the left
    # Final order should be: [Color1, Color3, Color4, ..., Color2]
    if len(colors) > 2:
        reordered = [colors[0]] + colors[2:] + [colors[1]]
        colors = reordered
    
    if len(name) <= 1:
        lbl = tk.Label(parent, text=name, bg=bg, fg=colors[0], font=font)
        lbl.pack(side=tk.LEFT)
        return [lbl]

    for i, char in enumerate(name):
        num_colors = len(colors)
        if num_colors > 1:
            pos = i / (len(name) - 1)
            
            # "Fade in" effect for secondary colors:
            # We use a non-linear power function to keep the first color longer
            # and make the transition to secondary colors happen more towards the end.
            # pos_weighted = pos ** 1.5 
            # Actually, the user says "secondary or later colors should fade in to not be distracting"
            # Maybe they mean the colors themselves should be faded?
            # Or they mean the transition should be smooth.
            # Let's try pos_weighted = pos ** 2.0 to give more weight to the first color.
            pos_weighted = pos ** 1.5
            
            segment_float = pos_weighted * (num_colors - 1)
            idx = int(segment_float)
            if idx >= num_colors - 1:
                idx = num_colors - 2
                factor = 1.0
            else:
                factor = segment_float - idx
            
            char_color = interpolate_color(colors[idx], colors[idx+1], factor)
        else:
            char_color = colors[0]

        lbl = tk.Label(parent, text=char, bg=bg, fg=char_color, font=font)
        lbl.pack(side=tk.LEFT)
        labels.append(lbl)
    
    return labels

def get_time_ago(dt):
    if not dt: return ""
    diff = (datetime.now() - dt).total_seconds()
    if diff < 1: return "just now"
    
    parts = []
    hours = int(diff // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)
    
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0 or not parts: parts.append(f"{seconds}s")
    
    return "".join(parts) + " ago"

def normalize_name(name):
    if not name: return "Unknown"
    # Remove leading/trailing spaces
    name = name.strip()
    
    # Remove anything in parentheses ( )
    import re
    name = re.sub(r"\(.*?\)", "", name).strip()
    
    # Remove NPC articles (prefixes) and "unknown" suffixes repeatedly
    # until no more matching prefixes/suffixes are found
    while True:
        original_name = name
        lower_name = name.lower()
        
        # Strip prefixes
        if lower_name.startswith("a "): name = name[2:]
        elif lower_name.startswith("an "): name = name[3:]
        elif lower_name.startswith("the "): name = name[4:]
        
        # Strip common accidental suffixes
        name = name.strip()
        lower_name = name.lower()
        suffixes = [" melee", " ranged", " unarmed", " polearm", " 1h", " 2h", " unknown", " unknown", "unknown"]
        for s in suffixes:
            if lower_name.endswith(s):
                name = name[:-len(s)].strip()
                lower_name = name.lower()
                break
        
        # Additional: if name contains " a ", " an ", " the " in the middle, it might be a messy log entry
        # like "th Shot II a Krayt Drag"
        # Let's try to find the LAST occurrence of an article and take everything after it
        # ONLY if it's an NPC-like name (not a known player/You)
        articles = [" a ", " an ", " the "]
        found_article = False
        for art in articles:
            idx = lower_name.rfind(art)
            if idx != -1:
                # Check if what's before it looks like junk (e.g. "th Shot II")
                # and what's after it looks like a name
                name = name[idx + len(art):].strip()
                lower_name = name.lower()
                found_article = True
                break
        
        if name == original_name:
            break

    # Normalize "You" variations
    if name.lower() in ["you", "damage you"]:
        return "You"
    return name

def is_probable_player(name, bosses=None, known_npcs=None, known_players=None):
    if not name or name == "Unknown": return False
    
    # Normalize before checking heuristics
    name = normalize_name(name)
    if name == "You": return True
    
    # Check if we've already confirmed this as a player
    lower_name = name.lower()
    if known_players and lower_name in known_players:
        return True
    
    # If it's in our bosses or known NPCs list, it's NOT a player
    if bosses and lower_name in bosses: return False
    if known_npcs and lower_name in known_npcs: return False
    
    # Specific filter for common NPCs that don't start with articles
    npc_keywords = ["trooper", "guard", "scout", "officer", "droid"]
    for kw in npc_keywords:
        if kw in lower_name:
            return False

    # Heuristic: NPCs often start with "a " or "an " or "the "
    if lower_name.startswith("a ") or lower_name.startswith("an ") or lower_name.startswith("the "):
        return False
    # Heuristic: Players usually don't have spaces in SWG (unless they have a surname)
    # but NPCs often have multiple words like "SpecForce marine".
    # This is tricky because players CAN have surnames.
    # However, if it's one word and doesn't start with "a/an/the", it's likely a player.
    # Also if it's two words where both are capitalized, it's likely a player.
    words = name.split()
    if len(words) == 1: return True
    if len(words) == 2:
        if words[0][0].isupper() and words[1][0].isupper():
            return True
    return False

def get_dynamic_text_color(alpha):
    # Standard TEXT_PRIMARY is #dcdcdc (220, 220, 220)
    # Brighten as alpha goes from 0.7 down to 0.4
    if alpha >= 0.7:
        return "#dcdcdc"
    
    # Calculate factor: 0.0 at 0.7 alpha, 1.0 at 0.4 alpha
    factor = max(0, min(1.0, (0.7 - alpha) / 0.3))
    
    # Interpolate from 220 to 255
    val = int(220 + (255 - 220) * factor)
    return f"#{val:02x}{val:02x}{val:02x}"

def save_log_segment(original_log_path, duration_minutes):
    """Saves the last duration_minutes of combat log to a new file in a 'saved_logs' directory."""
    import os
    import re
    from datetime import datetime, timedelta
    
    if not original_log_path or not os.path.exists(original_log_path):
        return None
        
    # Create saved_logs directory in the executable's directory
    exe_dir = os.path.dirname(os.path.abspath(original_log_path)) # Fallback if we can't get better
    try:
        import sys
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.abspath(".")
    except: pass
    
    save_dir = os.path.join(exe_dir, "saved_logs")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    # Determine filename: parse1, parse2, etc.
    i = 1
    while os.path.exists(os.path.join(save_dir, f"parse{i}.txt")):
        i += 1
    save_path = os.path.join(save_dir, f"parse{i}.txt")
    
    # Calculate time limit
    limit = datetime.now() - timedelta(minutes=duration_minutes)
    
    timestamp_pattern = re.compile(r"\[?(\d{4}-\d{2}-\d{2} )?(\d{2}:\d{2}:\d{2})\]?")
    
    lines_to_save = []
    earliest_ts = None
    
    try:
        with open(original_log_path, "r", encoding="utf-8", errors="replace") as f:
            # We want the LAST duration_minutes. 
            # A simple way is to read all lines and filter, but files can be large.
            # However, for 60 mins of combat, it's usually manageable.
            all_lines = f.readlines()
            
            for line in all_lines:
                ts_match = timestamp_pattern.search(line)
                if ts_match:
                    ts_str = ts_match.group(2)
                    try:
                        ts = datetime.strptime(ts_str, "%H:%M:%S")
                        now = datetime.now()
                        ts = ts.replace(year=now.year, month=now.month, day=now.day)
                        if ts > now + timedelta(minutes=5):
                            ts -= timedelta(days=1)
                        
                        if ts >= limit:
                            lines_to_save.append(line)
                            if earliest_ts is None:
                                earliest_ts = ts
                    except:
                        if lines_to_save: # Keep lines that don't have TS but follow a good TS
                            lines_to_save.append(line)
                elif lines_to_save:
                    lines_to_save.append(line)
                    
        if lines_to_save:
            # User wants the earlier timestamp captured in the log in the file or filename?
            # "with the earlier timestamp captured in that 60minute log time"
            # I'll add a header to the file with the start time.
            with open(save_path, "w", encoding="utf-8") as f:
                if earliest_ts:
                    f.write(f"--- LOG SAVED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    f.write(f"--- START TIMESTAMP: {earliest_ts.strftime('%H:%M:%S')} ---\n")
                f.writelines(lines_to_save)
            return save_path
    except Exception as e:
        print(f"Error saving log segment: {e}")
        
    return None
