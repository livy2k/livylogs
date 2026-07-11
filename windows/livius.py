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
        # Refresh every 1 second
        if not force and (now - self.last_full_refresh < 1.0):
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
        
        # Sort by arrival order, but PRIORITIZE focus targets at the top
        friendly_focus = getattr(self.app, 'current_focus_target', {}).get('friendly')
        enemy_focus = getattr(self.app, 'current_focus_target', {}).get('enemy')

        friendlies_list = [p for p in arrival_order if p in friendlies_set]
        enemies_list = [p for p in arrival_order if p in enemies_set]
        
        # Any players not in arrival order but in sets (fallback)
        f_fallback = [p for p in friendlies_set if p not in friendlies_list]
        e_fallback = [p for p in enemies_set if p not in enemies_list]
        friendlies_list += sorted(f_fallback)
        enemies_list += sorted(e_fallback)

        # Move Focus Targets to the TOP
        if friendly_focus and friendly_focus in friendlies_list:
            friendlies_list.remove(friendly_focus)
            friendlies_list.insert(0, friendly_focus)
        if enemy_focus and enemy_focus in enemies_list:
            enemies_list.remove(enemy_focus)
            enemies_list.insert(0, enemy_focus)

        try:
            with open("livius_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] REFRESH LISTS: Friendlies={len(friendlies_list)}, Enemies={len(enemies_list)}\n")
                if friendlies_list: f.write(f"  F_LIST: {friendlies_list}\n")
                if enemies_list: f.write(f"  E_LIST: {enemies_list}\n")
        except: pass
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
            self.left_panel.place(relx=0.005, rely=0.005, relwidth=0.49, relheight=0.99)
            
            self.right_panel = tk.Frame(self.main_container, bg=PANEL_DARK, bd=1, relief=tk.RIDGE)
            self.right_panel.place(relx=0.505, rely=0.005, relwidth=0.49, relheight=0.99)
            
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

    def _update_list(self, frame, players, color):
        current_widgets = frame.winfo_children()
        now = time.time()
        
        # Determine panel dimensions based on scaling
        # Original: width=340, height=80
        scale_x = getattr(self, 'scale_x', 1.0)
        scale_y = getattr(self, 'scale_y', 1.0)
        scale = getattr(self, 'scale', 1.0)
        
        panel_width = int(340 * scale_x)
        panel_height = int(40 * scale_y)
        
        # Scaling for fonts
        name_font_size = max(6, int(10 * scale))
        timer_font_size = max(5, int(6 * scale))
        status_icon_base_size = int(14 * scale)
        mvp_icon_base_size = int(18 * scale)
        
        # Adjust number of rows
        while len(current_widgets) < len(players):
            # Row container
            row = tk.Frame(frame, bg=PANEL_DARK, height=panel_height)
            row.pack(fill=tk.X, pady=2)
            row.pack_propagate(False)
            
            # Label for background texture
            bg_label = tk.Label(row, name="bg_label", bg=PANEL_DARK)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Content container
            content = tk.Frame(row, name="content_frame", bg=PANEL_DARK)
            content.place(x=0, y=0, relwidth=1, relheight=1)
            
            # LEFT part: Status icons (KD, PD, Int, DOT, KB)
            status_outer = tk.Frame(content, name="status_outer", bg=PANEL_DARK)
            status_outer.pack(side=tk.LEFT, fill=tk.Y)
            
            status_frame = tk.Frame(status_outer, name="status_frame", bg=PANEL_DARK)
            status_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2)
            
            # RIGHT part: Player Name and Special icons
            right_container = tk.Frame(content, name="right_container", bg=PANEL_DARK)
            right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Player name - RIGHT ALIGNED
            lbl_name = tk.Label(right_container, name="player_name", bg=PANEL_DARK, font=("Arial", name_font_size, "bold"), anchor="e")
            lbl_name.pack(side=tk.RIGHT, fill=tk.Y, padx=2)
            
            # Special icons Frame (MV, Sheep, Incap, Death) - Just LEFT of the name
            achievement_frame = tk.Frame(right_container, name="achievement_frame", bg=PANEL_DARK)
            achievement_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
            
            # Use lift for ALL child widgets to be safe
            bg_label.lower()
            content.lift()
            status_outer.lift()
            right_container.lift()
            achievement_frame.lift()
            lbl_name.lift()
            
            current_widgets = frame.winfo_children()
            
        # Hide extra rows
        for i in range(len(players), len(current_widgets)):
            current_widgets[i].pack_forget()
            
        # Update existing rows
        for i, player in enumerate(players):
            row = current_widgets[i]
            row.config(height=panel_height)
            row.pack(fill=tk.X, pady=2)
            
            bg_label = row.nametowidget("bg_label")
            content = row.nametowidget("content_frame")
            status_outer = content.nametowidget("status_outer")
            status_frame = status_outer.nametowidget("status_frame")
            
            right_container = content.nametowidget("right_container")
            achievement_frame = right_container.nametowidget("achievement_frame")
            
            # Robust lookup for lbl_name
            try:
                lbl_name = right_container.nametowidget("player_name")
            except:
                lbl_name = None
                for child in right_container.winfo_children():
                    if child.winfo_name() == "player_name":
                        lbl_name = child
                        break
            
            if not lbl_name:
                continue
                
            # Set background texture
            texture = self._get_panel_texture(panel_width, panel_height, is_alternate=(i % 2 == 0))
            
            # Focus Target Flashing Logic
            is_focus = False
            if color == "#00FF00" and player == getattr(self.app, 'current_focus_target', {}).get('friendly'):
                is_focus = True
            elif color == "#FF0000" and player == getattr(self.app, 'current_focus_target', {}).get('enemy'):
                is_focus = True
                
            pulse = getattr(self.app, 'pulse_state', False)
            if is_focus and pulse:
                row_bg = "#880000" # Flashing Red
            else:
                row_bg = "#24272d" if i % 2 == 0 else "#1a1d23"
            
            try:
                if texture:
                    bg_label.config(image=texture, bg=row_bg)
                    bg_label.image = texture 
                    
                    content.config(bg=row_bg) 
                    status_outer.config(bg=row_bg)
                    status_frame.config(bg=row_bg)
                    right_container.config(bg=row_bg)
                    achievement_frame.config(bg=row_bg)
                    lbl_name.config(bg=row_bg)
                else:
                    bg_label.config(bg=row_bg, image="")
                    content.config(bg=row_bg)
                    status_outer.config(bg=row_bg)
                    status_frame.config(bg=row_bg)
                    right_container.config(bg=row_bg)
                    achievement_frame.config(bg=row_bg)
                    lbl_name.config(bg=row_bg)
                
                # Double ensure they are correctly layered every refresh
                bg_label.lower()
                content.lift()
            except (tk.TclError, RuntimeError) as e:
                try:
                    with open("livius_debug.log", "a") as f:
                        f.write(f"[{time.strftime('%H:%M:%S')}] ROW CONFIG ERROR for {player}: {e}\n")
                except: pass
                continue
            
            # Update Statuses - REUSE WIDGETS TO PREVENT FLICKER
            # Split into Left (Status) and Right (Achievement)
            left_active = []
            right_active = []
            
            # 1. Immunity Cooldowns (Left)
            player_statuses = self.app.status_cooldowns.get(player, {})
            for status_type, start_time in player_statuses.items():
                elapsed = now - start_time
                if elapsed < 30:
                    remaining = int(30 - elapsed)
                    left_active.append(("cooldown", status_type, f"{remaining:02d}", "#FFFF00"))
            
            p_data = self.app.player_data.get(player, {})
            
            # 2. Poison (Left)
            poison_hits = p_data.get("poison_hits", 0)
            if poison_hits > 0:
                left_active.append(("poison", "poison", f"{poison_hits:02d}", "#00FF00"))

            # 3. Kills (Flex) (Left)
            kills = p_data.get("kill_count", 0)
            if kills > 0:
                left_active.append(("kills", "kills", f"{kills:02d}", "#FFFF00")) # Yellow

            # 4. Top DPS (MV) (Right)
            is_top_dps = (player == self.app.current_top_dps['friendly'] or player == self.app.current_top_dps['enemy'])
            if is_top_dps:
                duration = self.app.top_dps_durations.get(player, 0)
                # MVP is the most important, starts bigger and grows larger
                size = mvp_icon_base_size + int(duration / 30) * int(4 * scale)
                size = min(int(36 * scale), size)
                right_active.append(("top_dps", "top_dps", "", "#00FFFF", size))
 
            # 5. Top Tank (Sheep) (Right)
            is_top_tank = (player == self.app.current_top_tank['friendly'] or player == self.app.current_top_tank['enemy'])
            if is_top_tank:
                duration = self.app.top_tank_durations.get(player, 0)
                # Grow size similar to Top DPS
                size = status_icon_base_size + int(duration / 30) * int(3 * scale)
                size = min(int(30 * scale), size)
                right_active.append(("top_tank", "top_tank", "", "#FFFFFF", size))
 
            # 6. Top Healing (EMS) (Right)
            is_top_heal = (player == self.app.current_top_healing['friendly'] or player == self.app.current_top_healing['enemy'])
            if is_top_heal:
                duration = self.app.top_healing_durations.get(player, 0)
                # Grow size similar to Top DPS
                size = status_icon_base_size + int(duration / 30) * int(3 * scale)
                size = min(int(30 * scale), size)
                right_active.append(("top_healing", "top_healing", "", "#00FF00", size))

            # 7. Incap (Right)
            incap_count = p_data.get("incapacitated_count", 0)
            if incap_count > 0:
                right_active.append(("incap", "incap", f"{incap_count:02d}", "#FFA500"))

            # 7. Death (Right)
            if p_data.get("died"):
                right_active.append(("death", "death", "", ""))

            def sync_status_widgets(parent_frame, active_list):
                widgets = parent_frame.winfo_children()
                while len(widgets) < len(active_list):
                    s_sub = tk.Frame(parent_frame, bg=row_bg)
                    s_sub.pack(side=tk.LEFT, padx=1)
                    tk.Label(s_sub, name="text", bg=row_bg, font=("Arial", timer_font_size, "bold")).pack(side=tk.TOP)
                    icon_cont = tk.Frame(s_sub, name="icon_cont", bg=row_bg)
                    icon_cont.pack(side=tk.TOP)
                    tk.Canvas(icon_cont, name="canvas", bg=row_bg, highlightthickness=0).pack()
                    widgets = parent_frame.winfo_children()
                
                # Status Mapping for Unicode Icons
                icon_map = {
                    "knockdown": "🎯",
                    "posture": "🧎",
                    "intimidate": "!!!",
                    "poison": "🧪",
                    "incap": "🥴",
                    "death": "💀",
                    "kills": "🏋️",
                    "top_dps": "🏋️",
                    "top_tank": "🐑",
                    "top_healing": "✚"
                }
                
                # Label Mapping for abbreviations
                label_map = {
                    "knockdown": "DB",
                    "posture": "PD",
                    "intimidate": "Int",
                    "poison": "DOT",
                    "incap": "inc",
                    "kills": "KB",
                    "top_dps": "MVP",
                    "top_tank": "TNK",
                    "top_healing": "ems"
                }

                for j, s_widget in enumerate(widgets):
                    if j >= len(active_list):
                        s_widget.pack_forget()
                        continue
                    
                    s_widget.config(bg=row_bg)
                    status_info = active_list[j]
                    st_cat, st_type, st_val, st_col = status_info[0], status_info[1], status_info[2], status_info[3]
                    st_size = status_info[4] if len(status_info) > 4 else status_icon_base_size
                    
                    icon_cont = s_widget.nametowidget("icon_cont")
                    icon_canvas = icon_cont.nametowidget("canvas")
                    text_lbl = s_widget.nametowidget("text")
                    
                    icon_canvas.config(bg=row_bg)
                    # For larger MVP icon, ensure canvas is wide enough
                    canvas_size = int(36 * scale)
                    if st_size > (canvas_size - 4):
                        icon_canvas.config(width=st_size + 4, height=st_size + 4)
                    else:
                        icon_canvas.config(width=canvas_size, height=canvas_size)
                        
                    unicode_char = icon_map.get(st_type)
                    if unicode_char:
                        icon_canvas.delete("all")
                        # Center based on current canvas size
                        cw = int(icon_canvas.cget("width"))
                        ch = int(icon_canvas.cget("height"))
                        cx, cy = cw // 2, ch // 2
                        
                        icon_canvas.create_text(cx, cy, text=unicode_char, font=("Segoe UI Emoji", st_size), fill="white", tags="icon")
                        abbr_text = label_map.get(st_type, "")
                        if abbr_text:
                            abbr_font_size = max(6, int(9 * scale)) if st_size <= (30 * scale) else max(8, int(11 * scale))
                            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                                icon_canvas.create_text(cx+dx, cy+dy, text=abbr_text, font=("Arial", abbr_font_size, "bold"), fill="black", tags="label_bg")
                            icon_canvas.create_text(cx, cy, text=abbr_text, font=("Arial", abbr_font_size, "bold"), fill=st_col, tags="label")
                        
                        text_lbl.config(text=st_val, fg=st_col, bg=row_bg, font=("Arial", timer_font_size, "bold"))
                        text_lbl.lift()
                        s_widget.pack(side=tk.LEFT, padx=1)
                    else:
                        s_widget.pack_forget()

            sync_status_widgets(status_frame, left_active)
            sync_status_widgets(achievement_frame, right_active)
            
            # Player Name
            display_color = color
            if p_data.get("died"):
                display_color = TEXT_DISABLED
            
            if lbl_name:
                lbl_name.config(text=player, fg=display_color)
