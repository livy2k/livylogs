def text_to_dot_matrix(text, width, height, font_family="Consolas", font_size=10):
    """Converts text to a bitmask for dot matrix display."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a small image and draw text on it
    # We use a 1-bit image (mode "1")
    img = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to load a font, fallback to default
        try:
            # On Windows, fonts are usually in C:\Windows\Fonts
            # We try to find LilitaOne.ttf in our assets first if possible
            import os
            font_path = get_resource_path("LilitaOne.ttf")
            if not os.path.exists(font_path):
                 font_path = os.path.join("UImaker", "assets", "fonts", "LilitaOne", "LilitaOne.ttf")
            if not os.path.exists(font_path):
                 font_path = font_family + ".ttf"
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
            
        # Get text bounding box and center it
        # textsize is deprecated in newer PIL, use textbbox
        try:
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            w, h = right - left, bottom - top
            draw.text(((width - w) // 2 - left, (height - h) // 2 - top), text, font=font, fill=1)
        except AttributeError:
            # Older PIL
            w, h = draw.textsize(text, font=font)
            draw.text(((width - w) // 2, (height - h) // 2), text, font=font, fill=1)
        
        # Convert to list of lists
        pixels = list(img.getdata())
        matrix = []
        for r in range(height):
            matrix.append(pixels[r * width : (r + 1) * width])
        return matrix
    except Exception as e:
        print(f"[DEBUG] text_to_dot_matrix error: {e}")
        return None

def image_to_ascii(image_data, width=40, height=20):
    """Converts image data (bytes or path) to ASCII art."""
    from PIL import Image
    import io
    
    try:
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(image_data)
            
        # Convert to grayscale and resize
        img = img.convert("L")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # ASCII characters from dark to light
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
        
        pixels = img.getdata()
        ascii_str = ""
        for i, pixel in enumerate(pixels):
            # Map 0-255 to index 0-10
            ascii_str += chars[pixel // 25]
            if (i + 1) % width == 0:
                ascii_str += "\n"
        return ascii_str
    except Exception as e:
        print(f"[DEBUG] ASCII Conversion Error: {e}")
        return None

"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import ctypes
import os
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
    
    # Remove anything in parentheses ( ) or brackets [ ]
    import re
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\[.*?\]", "", name).strip()
    
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
        suffixes = [
            " melee", " ranged", " unarmed", " polearm", " 1h", " 2h", 
            " unknown", "unknown", 
            " looks very", " looks", " has been", " have been", 
            " is", " was", " use", " used", " using", 
            " [combat]", " [spatial]", " [group]", " [chat]", " [tell]"
        ]
        for s in suffixes:
            if lower_name.endswith(s):
                name = name[:-len(s)].strip()
                lower_name = name.lower()
                break
        
        # Verb fragments in the middle or end
        verbs = [" looks very ", " looks ", " has been ", " have been ", " is ", " was "]
        for v in verbs:
            v_idx = lower_name.find(v)
            if v_idx != -1:
                name = name[:v_idx].strip()
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
    if name.lower() in [
        "you", "damage you", "yourself", "s you", "s yourself", 
        "you have completely", "you have been", "you have", 
        "you use", "by you", "you are", "you're", "you intimidate", 
        "you use", "you!", "has been", "stands up", "falls down", "kneels",
        "by you!", "intimidated by you", "intimidated by you!", "ou", "ou!", "you "
    ]:
        return "You"
    
    # Aggressive stripping of descriptive fragments from NPC names
    lower_n = name.lower()
    # Expanded list of status verbs and fragments common in SWG logs
    # We check if these are in the name; if so, we assume they are state fragments
    # and strip everything from that point onwards.
    status_frags = [
        " looks very intimidated by you", " looks very", " has been ", " have been ", 
        " is ", " was ", " looks ", " by ", 
        " used ", " uses ", " intimidated", " kneeling", " prone", 
        " incapacitated", " knocked down", " kneel", " has defeated ",
        " use ", " attacks ", " deals ", " heals ", " hits ", " apply ",
        " resist ", " no longer ", " incapacitated by ", " intimidated by ",
        " knocked down by ", " kneels ", " prone by ", " stands up", " falls down", " on a "
    ]
    
    # If we see a state keyword, it confirms this name is a log fragment
    # We strip it to reveal the actual actor/victim name.
    for frag in status_frags:
        if frag in lower_n:
            name = name[:lower_n.find(frag)].strip()
            lower_n = name.lower()
            
    # Cleanup articles
    if lower_n.startswith("a "): name = name[2:]
    elif lower_n.startswith("an "): name = name[3:]
    elif lower_n.startswith("the "): name = name[4:]
    
    # Final check for common prefixes like "by " (independent of being a fragment)
    lower_n = name.lower()
    if lower_n.startswith("by "): name = name[3:]

    # RE-CHECK for "You" after article/prefix cleanup
    if name.lower() in [
        "you", "damage you", "yourself", "s you", "s yourself", 
        "you have completely", "you have been", "you have", 
        "you use", "by you", "you are", "you're", "you intimidate", 
        "you use", "you!", "has been", "stands up", "falls down", "kneels",
        "by you!", "intimidated by you", "intimidated by you!", "ou", "ou!", "you "
    ]:
        return "You"
    
    # Guard: if the result is empty or just a fragment like "use" or "is", keep original or return Unknown
    if not name or name.lower() in ["use", "is", "has", "was"]:
        return "Unknown"
    
    return name.strip()

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
    
    # Heuristic: NPCs often start with "a " or "an " or "the "
    if lower_name.startswith("a ") or lower_name.startswith("an ") or lower_name.startswith("the "):
        return False
    
    # Specific filter for common NPCs that don't start with articles
    npc_keywords = ["trooper", "guard", "scout", "officer", "droid", "gundark", "krayt", "dragon", "mandalorian"]
    for kw in npc_keywords:
        if kw in lower_name:
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

def split_file(file_path, chunk_size_mb=50):
    """Splits a large file into chunks of chunk_size_mb."""
    if not os.path.exists(file_path):
        return []
    
    file_size = os.path.getsize(file_path)
    chunk_size = chunk_size_mb * 1024 * 1024
    chunks = []
    
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            chunk_name = f"{file_path}.part{chunk_num}"
            with open(chunk_name, 'wb') as chunk_file:
                chunk_file.write(data)
            chunks.append(chunk_name)
            chunk_num += 1
            
    print(f"[Splitter] {file_path} split into {len(chunks)} parts.")
    return chunks

def join_files(base_path, output_path=None):
    """Joins file chunks (base_path.part0, base_path.part1, etc.) into a single file."""
    if output_path is None:
        output_path = base_path
        
    chunk_num = 0
    found_any = False
    
    with open(output_path, 'wb') as output_file:
        while True:
            chunk_name = f"{base_path}.part{chunk_num}"
            if not os.path.exists(chunk_name):
                break
            with open(chunk_name, 'rb') as chunk_file:
                output_file.write(chunk_file.read())
            found_any = True
            chunk_num += 1
            
    if found_any:
        print(f"[Joiner] Reconstructed {output_path} from {chunk_num} parts.")
        return output_path
    return None

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
