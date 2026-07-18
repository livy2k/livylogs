"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
import time
from PIL import Image, ImageTk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, TEXT_ACCENT, TEXT_DISABLED,
    PANEL_BG, BORDER_COLOR, BORDER_HIGHLIGHT
)
from windows.base_window import BasePopoutWindow

class LiviusWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "LIVIUS", "LiviusWindow", 750, 600, show_title=True)
        self._is_broken = False
        self.friendlies = set()
        self.enemies = set()
        self.last_full_refresh = 0
        self.bg_textures = {} # Cache for panel textures
        self.icon_images = {} # Cache for custom icons

    def _get_icon(self, name, size=(24, 24)):
        if name in self.icon_images:
            return self.icon_images[name]
        
        try:
            path = f"res/icons/{name}.png"
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.icon_images[name] = photo
            return photo
        except Exception:
            return None

    def _get_panel_texture(self, width, height, is_alternate=False):
        key = (width, height, is_alternate)
        if key in self.bg_textures:
            return self.bg_textures[key]
        
        try:
            # Base colors for the brushed metal look
            if is_alternate:
                base_color = (36, 39, 45) # Lighter
            else:
                base_color = (26, 29, 35) # Darker
            
            img = Image.new('RGB', (width, height), base_color)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Add fine brushed metal streaks (horizontal)
            import random
            for y in range(height):
                # Small variation in brightness for each "brush" line
                variation = random.randint(-2, 2)
                c_r = max(0, min(255, base_color[0] + variation))
                c_g = max(0, min(255, base_color[1] + variation))
                c_b = max(0, min(255, base_color[2] + variation))
                color = (c_r, c_g, c_b)
                draw.line((0, y, width, y), fill=color, width=1)
            
            # Add subtle vertical highlights to give it a curved/metallic feel
            for x in range(width):
                # Highlight intensity based on horizontal position (subtle gradient)
                dist_from_center = abs(x - width/2) / (width/2)
                if dist_from_center < 0.2:
                    h = int((1.0 - dist_from_center/0.2) * 3)
                    if h > 0:
                        # Draw a very faint vertical line
                        for y in range(height):
                            current = img.getpixel((x, y))
                            new_color = (
                                min(255, current[0] + h),
                                min(255, current[1] + h),
                                min(255, current[2] + h)
                            )
                            img.putpixel((x, y), new_color)

            # Add a top and bottom edge highlight/shadow for "panel" effect
            for x in range(width):
                # Top highlight
                current = img.getpixel((x, 0))
                img.putpixel((x, 0), (min(255, current[0]+15), min(255, current[1]+15), min(255, current[2]+15)))
                # Bottom shadow
                current = img.getpixel((x, height-1))
                img.putpixel((x, height-1), (max(0, current[0]-10), max(0, current[1]-10), max(0, current[2]-10)))

            photo = ImageTk.PhotoImage(img)
            self.bg_textures[key] = photo
            return photo
        except Exception as e:
            return None

    def refresh(self, force=False):
        if self._is_broken:
            return
        if not self.window or not self.window.winfo_exists():
            return
            
        try:
            self._refresh_internal(force)
        except Exception as e:
            try:
                with open("livius_debug.log", "a") as f:
                    import traceback
                    f.write(f"[{time.strftime('%H:%M:%S')}] REFRESH CRASH: {e}\n{traceback.format_exc()}\n")
            except: pass

    def _refresh_internal(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn":
            return

        now = time.time()
        # Refresh every 0.2 seconds for smooth countdown
        if not force and (now - self.last_full_refresh < 0.2):
            return
        
        self.last_full_refresh = now

        # Update window geometry (sync config)
        if force:
            try:
                # Force winfo update to get real dimensions if they just changed
                self.window.update_idletasks()
            except: pass

        # Calculate scale factor based on window dimensions
        # Default size was 750x600
        cur_w = self.window.winfo_width()
        cur_h = self.window.winfo_height()
        if cur_w < 100: cur_w = self.default_w
        if cur_h < 100: cur_h = self.default_h
        
        self.scale_x = cur_w / 750.0
        self.scale_y = cur_h / 600.0
        self.scale = min(self.scale_x, self.scale_y)

        # Get data from app
        friendlies_set = getattr(self.app, 'friendly_players', set())
        enemies_set = getattr(self.app, 'enemy_players', set())
        arrival_order = getattr(self.app, 'player_arrival_order', [])
        
        # Sort by arrival order, but PRIORITIZE focus targets and You at the top
        friendly_focus = getattr(self.app, 'current_focus_target', {}).get('friendly')
        enemy_focus = getattr(self.app, 'current_focus_target', {}).get('enemy')

        friendlies_list = []
        for p in arrival_order:
            if p in friendlies_set or p == "You":
                friendlies_list.append(p)
        
        enemies_list = []
        for p in arrival_order:
            if p in enemies_set and p != "You":
                enemies_list.append(p)
        
        # Any players not in arrival order but in sets (fallback)
        f_fallback = [p for p in friendlies_set if p not in friendlies_list]
        if "You" not in friendlies_list and "You" not in f_fallback:
            f_fallback.append("You")
        
        for p in sorted(f_fallback):
            if p not in friendlies_list:
                friendlies_list.append(p)
        
        e_fallback = [p for p in enemies_set if p not in enemies_list and p != "You"]
        for p in sorted(e_fallback):
            if p not in enemies_list:
                enemies_list.append(p)

        # Helper to calculate recent damage taken
        def get_recent_dmg(p_name):
            p_data = self.app.player_data.get(p_name, {})
            history = p_data.get("taken_damage_history", [])
            now = time.time()
            return sum(amt for ts, amt in history if now - ts < 4)

        # Helper to get 911 priority
        def get_911_priority(p_name):
            p_data = self.app.player_data.get(p_name, {})
            last_911 = p_data.get("last_911_time", 0)
            # If typed 911 in the last 30 seconds, they get priority
            if time.time() - last_911 < 30:
                return last_911
            return 0

        # Sort friendlies: 911 priority first, then recent damage taken
        friendlies_list.sort(key=lambda p: (get_911_priority(p), get_recent_dmg(p)), reverse=True)

        # Move 'You' and Focus Targets to the TOP (Overriding the damage-taken sort if necessary)
        if friendly_focus and friendly_focus in friendlies_list:
            friendlies_list.remove(friendly_focus)
            friendlies_list.insert(0, friendly_focus)
        
        # 'You' should be at top unless someone else has 911
        if "You" in friendlies_list:
            friendlies_list.remove("You")
            # Find the first index that is NOT a 911 player
            insert_idx = 0
            for i, p in enumerate(friendlies_list):
                # Only put "You" below others if they have 911 AND "You" does not
                if get_911_priority(p) > 0 and get_911_priority("You") == 0:
                    insert_idx = i + 1
                else:
                    break
            friendlies_list.insert(insert_idx, "You")
            
        if enemy_focus and enemy_focus in enemies_list:
            enemies_list.remove(enemy_focus)
            enemies_list.insert(0, enemy_focus)

        try:
            with open("livius_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] REFRESH LISTS: Friendlies={len(friendlies_list)}, Enemies={len(enemies_list)}\n")
                if friendlies_list: f.write(f"  F_LIST: {friendlies_list}\n")
                if enemies_list: f.write(f"  E_LIST: {enemies_list}\n")
        except: pass

        # DIAGNOSTIC: Force "You" into friendlies if it's missing but we have data
        if "You" not in friendlies_list and "You" in self.app.player_data:
             friendlies_list.append("You")

        # Build main container ONCE
        if not hasattr(self, 'main_container'):
            for widget in self.content_container.winfo_children():
                try:
                    widget.destroy()
                except: pass
            
            # Use a slightly darker background for the whole content
            self.main_container = tk.Frame(self.content_container, bg=WINDOW_BG)
            self.main_container.pack(fill=tk.BOTH, expand=True)
            
            # Main panels with a "brushed" look
            self.left_panel = tk.Frame(self.main_container, bg=PANEL_DARK, bd=1, relief=tk.RIDGE)
            self.left_panel.place(relx=0, rely=0, relwidth=0.5, relheight=1)
            
            self.right_panel = tk.Frame(self.main_container, bg=PANEL_DARK, bd=1, relief=tk.RIDGE)
            self.right_panel.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            
            self.friendly_list_frame = tk.Frame(self.left_panel, bg=PANEL_DARK)
            self.friendly_list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
            self.enemy_list_frame = tk.Frame(self.right_panel, bg=PANEL_DARK)
            self.enemy_list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Update lists
        try:
            with open("livius_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] REFRESH: Friendlies={len(friendlies_list)}, Enemies={len(enemies_list)}\n")
        except: pass
        
        self._update_list(self.friendly_list_frame, friendlies_list, "#00FF00")
        self._update_list(self.enemy_list_frame, enemies_list, "#FF0000")
        
        if force:
            self.window.lift()

    def save_config(self):
        """Save window position/size to app config. Safe to call even if window is not open."""
        if not self.window or not self.window.winfo_exists():
            return
        try:
            if self.config_key not in self.app.config:
                self.app.config[self.config_key] = {}
            self.app.config[self.config_key].update({
                "width": str(self.window.winfo_width()),
                "height": str(self.window.winfo_height()),
                "x": str(self.window.winfo_x()),
                "y": str(self.window.winfo_y())
            })
        except:
            pass

    def close(self):
        self._is_broken = False
        super().close()

    def _update_list(self, frame, players, color):
        current_widgets = frame.winfo_children()
        now = time.time()
        
        # Determine panel dimensions based on scaling
        scale_x = getattr(self, 'scale_x', 1.0)
        scale_y = getattr(self, 'scale_y', 1.0)
        scale = getattr(self, 'scale', 1.0)
        
        panel_height = int(70 * scale_y)
        
        # Scaling for fonts
        name_font_size = max(10, int(14 * scale))
        status_label_font_size = max(12, int(16 * scale))
        timer_font_size = max(10, int(14 * scale))
        
        # Adjust number of rows
        while len(current_widgets) < len(players):
            row = tk.Frame(frame, bg=PANEL_DARK, height=panel_height)
            row.pack(fill=tk.X, pady=2)
            row.pack_propagate(False)
            current_widgets = frame.winfo_children()
            
        # Hide extra rows
        for i in range(len(players), len(current_widgets)):
            current_widgets[i].pack_forget()
            
        # Update rows
        for i, player_name in enumerate(players):
            from utils import normalize_name
            p_norm = normalize_name(player_name)
            if p_norm == "Unknown":
                current_widgets[i].pack_forget()
                continue
            
            # Skip pure fragments (but not "You")
            fragment_words = {"use", "is", "has", "was", "by", "a", "an", "the", "you", "yourself", "damage", "you!", "ou", "ou!"}
            if p_norm != "You" and p_norm.lower() in fragment_words:
                current_widgets[i].pack_forget()
                continue
                
            row = current_widgets[i]
            row.pack(fill=tk.X, pady=2)
            
            # 1. Row Configuration
            row_bg = "#1a1d23" if i % 2 == 0 else "#24272d"
            row.config(bg=row_bg, height=panel_height)
            
            # Check if focus target
            is_focus = False
            if color == "#00FF00" and player_name == getattr(self.app, 'current_focus_target', {}).get('friendly'):
                is_focus = True
            elif color == "#FF0000" and player_name == getattr(self.app, 'current_focus_target', {}).get('enemy'):
                is_focus = True
    
            if is_focus and getattr(self.app, 'pulse_state', False):
                row_bg = "#880000"
                row.config(bg=row_bg)

            # Get or create content frame
            content = None
            for child in row.winfo_children():
                if isinstance(child, tk.Frame) and child.winfo_children():
                    content = child
                    break
            
            if content is None:
                content = tk.Frame(row, bg=row_bg)
                content.pack(fill=tk.BOTH, expand=True, padx=5)
            else:
                content.config(bg=row_bg)

            # LEFT SIDE: Status Blocks (KD, PD, INT, INC)
            status_container = None
            for child in content.winfo_children():
                if isinstance(child, tk.Frame) and child.winfo_children():
                    # Check if it's the status container (has KD/PD/INT/INC labels)
                    for sub in child.winfo_children():
                        if isinstance(sub, tk.Frame) and sub.winfo_children():
                            for lbl in sub.winfo_children():
                                if isinstance(lbl, tk.Label) and lbl.cget("text") in ["KD", "PD", "INT", "INC"]:
                                    status_container = child
                                    break
                        if status_container:
                            break
                if status_container:
                    break
            
            if status_container is None:
                status_container = tk.Frame(content, bg=row_bg)
                status_container.pack(side=tk.LEFT, fill=tk.Y)
            else:
                status_container.config(bg=row_bg)

            p_data = self.app.player_data.get(player_name, {})
            player_statuses = self.app.status_cooldowns.get(player_name, {})
            status_effects_start = p_data.get("status_effects", {})
    
            tracked = [
                ("knockdown", "KD"),
                ("posture", "PD"),
                ("intimidate", "INT"),
                ("incapacitated", "INC")
            ]

            # Ensure we have enough status frames
            status_frames = status_container.winfo_children()
            while len(status_frames) < len(tracked):
                st_frame = tk.Frame(status_container, bg=row_bg, width=int(55 * scale_x))
                st_frame.pack(side=tk.LEFT, fill=tk.Y, padx=1)
                st_frame.pack_propagate(False)
                status_frames = status_container.winfo_children()
            
            for idx, (st_type, st_label) in enumerate(tracked):
                st_frame = status_frames[idx]
                st_frame.config(bg=row_bg, width=int(55 * scale_x))

                start_time = player_statuses.get(st_type, 0)
                elapsed = now - start_time
        
                st_col = "#444444" # Default greyed out
                timer_text = ""
        
                if start_time > 0 and elapsed < 28:
                    remaining = int(28 - elapsed)
                    timer_text = f"{remaining:02d}"
            
                    # Active phase check
                    active_start = status_effects_start.get(st_type, 0)
                    active_dur = 28 if st_type in ["intimidate", "incapacitated"] else 8
                    if now - active_start < active_dur:
                        st_col = "#FF0000" # Red Active
                    else:
                        st_col = "#FFFF00" # Yellow Immunity
        
                # Update label widgets inside st_frame
                st_children = st_frame.winfo_children()
                # First child should be the label (KD/PD/INT/INC)
                if len(st_children) >= 1:
                    lbl = st_children[0]
                    if isinstance(lbl, tk.Label):
                        lbl.config(text=st_label, fg=st_col, bg=row_bg, 
                                   font=("Arial", status_label_font_size, "bold"))
                else:
                    lbl = tk.Label(st_frame, text=st_label, fg=st_col, bg=row_bg, 
                                   font=("Arial", status_label_font_size, "bold"))
                    lbl.pack(side=tk.TOP, pady=(5,0))
                
                # Second child should be the timer label
                if timer_text:
                    if len(st_children) >= 2:
                        timer_lbl = st_children[1]
                        if isinstance(timer_lbl, tk.Label):
                            timer_lbl.config(text=timer_text, fg=st_col, bg=row_bg, 
                                             font=("Consolas", timer_font_size, "bold"))
                    else:
                        timer_lbl = tk.Label(st_frame, text=timer_text, fg=st_col, bg=row_bg, 
                                             font=("Consolas", timer_font_size, "bold"))
                        timer_lbl.pack(side=tk.TOP)
                else:
                    # Remove timer label if it exists
                    if len(st_children) >= 2:
                        st_children[1].destroy()

            # RIGHT SIDE: Achievements and Name
            right_side = None
            for child in content.winfo_children():
                if isinstance(child, tk.Frame) and child != status_container:
                    right_side = child
                    break
            
            if right_side is None:
                right_side = tk.Frame(content, bg=row_bg)
                right_side.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            else:
                right_side.config(bg=row_bg)

            # Achievements (MVP, TNK, EMS)
            ach_frame = None
            for child in right_side.winfo_children():
                if isinstance(child, tk.Frame):
                    ach_frame = child
                    break
            
            if ach_frame is None:
                ach_frame = tk.Frame(right_side, bg=row_bg)
                ach_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            else:
                ach_frame.config(bg=row_bg)

            # Update achievement labels
            ach_labels = ach_frame.winfo_children()
            expected_ach = []
            if player_name == self.app.current_top_dps.get('friendly') or player_name == self.app.current_top_dps.get('enemy'):
                expected_ach.append(("MVP", "#00FFFF"))
            if player_name == self.app.current_top_tank.get('friendly') or player_name == self.app.current_top_tank.get('enemy'):
                expected_ach.append(("TNK", "#FFFFFF"))
            if player_name == self.app.current_top_healing.get('friendly') or player_name == self.app.current_top_healing.get('enemy'):
                expected_ach.append(("EMS", "#00FF00"))
            
            # Remove extra labels
            while len(ach_labels) > len(expected_ach):
                ach_labels[-1].destroy()
                ach_labels = ach_frame.winfo_children()
            
            # Update existing or create new
            for idx, (text, fg) in enumerate(expected_ach):
                if idx < len(ach_labels):
                    lbl = ach_labels[idx]
                    if isinstance(lbl, tk.Label):
                        lbl.config(text=text, fg=fg, bg=row_bg, font=("Arial", name_font_size, "bold"))
                else:
                    lbl = tk.Label(ach_frame, text=text, fg=fg, bg=row_bg, font=("Arial", name_font_size, "bold"))
                    lbl.pack(side=tk.LEFT, padx=2)

            # Name - Cyan for You, Right Aligned
            is_you = (player_name == "You")
            name_col = "#00FFFF" if is_you else color
            if p_data.get("died"): name_col = "#666666"

            # Find or create name label
            name_lbl = None
            for child in right_side.winfo_children():
                if isinstance(child, tk.Label) and child != ach_frame:
                    name_lbl = child
                    break
            
            if name_lbl is None:
                name_lbl = tk.Label(right_side, text=player_name.upper(), fg=name_col, bg=row_bg,
                                    font=("Arial", name_font_size, "bold"), anchor="e")
                name_lbl.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
            else:
                name_lbl.config(text=player_name.upper(), fg=name_col, bg=row_bg,
                                font=("Arial", name_font_size, "bold"))
