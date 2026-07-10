import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
from constants import (
    PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, WINDOW_BG, COLOR_DEFAULT_CLASS,
    TITLE_GRADIENT_START
)
from utils import create_rainbow_name
from windows.base_window import BasePopoutWindow

class LeaderboardWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Leaderboard", "LeaderboardWindow", 300, 400)

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return

        # Restore title label position
        if hasattr(self, 'title_label') and self.title_label.winfo_exists():
            try:
                self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 10, 16)
            except: pass
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Determine if we should do a full data calculation
        # If we currently have a "No data" message or list is empty, force a full refresh
        is_empty = True
        if hasattr(self, 'list_container') and self.list_container.winfo_exists():
            # Check if we have any widgets that aren't the "No data" label
            children = self.list_container.winfo_children()
            if children:
                for w in children:
                    if isinstance(w, tk.Label):
                        text = w.cget("text")
                        if "No " not in text:
                            is_empty = False
                            break
                    else:
                        is_empty = False
                        break

        # Determine frequency based on state
        if is_empty:
            # Refresh every 200ms if empty to catch first data quickly
            refresh_interval = 0.2
        else:
            # User requested 3s refresh for secondary windows to help performance
            refresh_interval = 3.0
        
        do_full = force or is_empty or (now - self.last_full_refresh >= refresh_interval)

        # Use an update strategy that minimizes widget recreation
        if not hasattr(self, 'list_container'):
            for widget in self.content_container.winfo_children(): widget.destroy()
            
            # Navigation Row (Below title bar, contains icons and player name in drilldown)
            self.nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
            self.nav_row.pack(fill=tk.X)
            self.nav_row.pack_forget() # Hidden initially

            self.nav_player_label = tk.Label(self.nav_row, text="", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"))
            self.nav_player_label.pack(side=tk.LEFT, padx=10)

            # Navigation Buttons in nav row
            self.back_btn = tk.Label(self.nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2", padx=5)
            self.back_btn.bind("<Button-1>", lambda e: self.go_back())
            self.back_btn.pack(side=tk.RIGHT)
            
            self.top_btn = tk.Label(self.nav_row, text="↩", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2", padx=5)
            self.top_btn.bind("<Button-1>", lambda e: self.go_to_top())
            self.top_btn.pack(side=tk.RIGHT)

            # Category Selector
            self.c_frame = tk.Frame(self.content_container, bg=PANEL_DARK); self.c_frame.pack(fill=tk.X, pady=(0, 5))
            self.cat_btns = {}
            
            def make_cat_cmd(v): return lambda e: [setattr(self.app, 'leaderboard_cat', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("DAMAGE", "damage"), ("HEALING", "healing"), ("LOOT", "loot")]:
                btn = tk.Label(self.c_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 7, "bold"), padx=5, pady=3, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_cat_cmd(val))
                self.cat_btns[val] = btn

            # Header
            self.h_frame = tk.Frame(self.content_container, bg=PANEL_DARK); self.h_frame.pack(fill=tk.X, pady=(0, 5))
            self.lbl_rank = tk.Label(self.h_frame, text="RANK", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"))
            self.lbl_rank.pack(side=tk.LEFT, padx=5)
            self.lbl_player = tk.Label(self.h_frame, text="PLAYER", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"))
            self.lbl_player.pack(side=tk.LEFT, padx=20)
            self.lbl_cat_head = tk.Label(self.h_frame, text="DAMAGE", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"))
            self.lbl_cat_head.pack(side=tk.RIGHT, padx=5) 
        
            # Scrollable area
            canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
            self.list_container = tk.Frame(canvas, bg=WINDOW_BG)

            self.list_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=self.list_container, anchor="nw")
            
            def _on_canvas_configure(e):
                 canvas.itemconfig(1, width=e.width)
            canvas.bind("<Configure>", _on_canvas_configure)
            
            canvas.configure(yscrollcommand=scrollbar.set)
            
            def _on_mousewheel(event):
                if not self.window: return
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            self.window.bind("<MouseWheel>", _on_mousewheel)
            self.list_container.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<MouseWheel>", _on_mousewheel)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            do_full = True

        # Update Category Buttons
        cat = getattr(self.app, 'leaderboard_cat', 'damage')
        if hasattr(self, 'cat_btns'):
            for v, btn in self.cat_btns.items():
                try:
                    if btn.winfo_exists():
                        active = (v == cat)
                        btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
                except: pass
        if hasattr(self, 'lbl_cat_head') and self.lbl_cat_head.winfo_exists():
            self.lbl_cat_head.config(text=cat.upper())

        # Update Title and Navigation Buttons
        is_drill = getattr(self, 'is_drilldown', False)
        if is_drill:
            if hasattr(self, 'nav_row') and self.nav_row.winfo_exists():
                if hasattr(self, 'c_frame') and self.c_frame.winfo_exists() and self.c_frame.winfo_ismapped():
                    self.nav_row.pack(fill=tk.X, before=self.c_frame)
                else:
                    self.nav_row.pack(fill=tk.X)
                p_name = getattr(self, 'selected_player', 'PLAYER')
                ctx_text = p_name.upper()
                is_you = ctx_text == "YOU" or ctx_text == self.app.char_name.get().upper()
                self.nav_player_label.config(text=ctx_text, fg="#00ffff" if is_you else ACCENT_BLUE)

            try: self.title_bar.itemconfig(self.title_label, text="LEADERBOARD")
            except: pass
        else:
            if hasattr(self, 'nav_row'):
                self.nav_row.pack_forget()
            try: self.title_bar.itemconfig(self.title_label, text="Leaderboard")
            except: pass

        if not do_full: return
        self.last_full_refresh = now

        # Use caching to minimize flicker
        cat = getattr(self.app, 'leaderboard_cat', 'damage')
        
        cache_key = f"main_{cat}_{len(self.app.player_data)}_{sum(d.get(cat,0) for d in self.app.player_data.values())}"
        
        if not force and hasattr(self, '_last_cache_key') and self._last_cache_key == cache_key:
            return
        
        self._last_cache_key = cache_key

        # Main Leaderboard View
        data_list = []
        if cat in ["damage", "healing"]:
            for name, data in self.app.player_data.items():
                val = data.get(cat, 0)
                if val > 0: data_list.append((name, val))
        elif cat == "loot":
            for name, data in self.app.player_data.items():
                val = data.get("total_credits", 0)
                if val > 0: data_list.append((name, val))
            if not data_list:
                for name, data in self.app.player_data.items():
                    val = data.get("lb_loot", 0)
                    if val > 0: data_list.append((name, val))

        sorted_list = sorted(data_list, key=lambda x: x[1], reverse=True)
        merged_data = {name: val for name, val in sorted_list}
        if self.app.enable_sync.get() and self.app.sync_data:
            remote_data = self.app.sync_data.get("data", {}).get(cat, {})
            seen_recently = set(self.app.locally_seen_players.keys())
            for remote_name, remote_val in remote_data.items():
                if remote_name == self.app.char_name.get(): continue
                if cat in ["damage", "healing"] and remote_name not in seen_recently and remote_name not in merged_data: continue
                if cat == "loot":
                    count = len(remote_val) if isinstance(remote_val, list) else remote_val
                    merged_data[remote_name] = max(merged_data.get(remote_name, 0), count)
                else:
                    merged_data[remote_name] = max(merged_data.get(remote_name, 0), remote_val)

        final_list = sorted(merged_data.items(), key=lambda x: x[1], reverse=True)

        # Reordering check for smoother updates
        current_order = getattr(self, '_last_order', [])
        new_order = [name for name, _ in final_list[:100]]
        order_changed = current_order != new_order
        self._last_order = new_order

        # Clear or setup Drill-down vs Main
        if is_drill:
            self.c_frame.pack_forget()
            self.h_frame.pack_forget()
        else:
            self.c_frame.pack(fill=tk.X, pady=(0, 5))
            self.h_frame.pack(fill=tk.X, pady=(0, 5))

        current_widgets = self.list_container.winfo_children()
        
        if is_drill:
            p = getattr(self, 'selected_player', '')
            for widget in current_widgets: widget.destroy()
            
            tk.Label(self.list_container, text=f"DETAILS FOR {p.upper()}", bg=WINDOW_BG, fg="#00ffff" if (p == "You" or p == self.app.char_name.get()) else ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
            
            p_data = self.app.player_data.get(p, {})
            stats_to_show = [
                ("Total Damage", f"{p_data.get('damage', 0):,}"),
                ("Total Healing", f"{p_data.get('healing', 0):,}"),
                ("Mob Kills", f"{p_data.get('lb_mobs', 0):,}"),
                ("Loot Credits", f"{p_data.get('total_credits', 0):,}cr"),
            ]
            
            for label, val in stats_to_show:
                row = tk.Frame(self.list_container, bg=PANEL_DARK, padx=10, pady=5)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=label, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
                tk.Label(row, text=val, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)
            
            return

        if not final_list[:100]:
            if current_widgets:
                # Check if we already have the "No data" label to avoid redundant destruction
                is_no_data = False
                if len(current_widgets) == 1 and isinstance(current_widgets[0], tk.Label):
                    if "No " in current_widgets[0].cget("text"):
                        is_no_data = True
                
                if not is_no_data:
                    for widget in current_widgets: widget.destroy()
                    tk.Label(self.list_container, text=f"No {cat} data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            elif not current_widgets:
                tk.Label(self.list_container, text=f"No {cat} data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            self._last_order = []
            self._row_frames = {}
            self._row_widgets = {}
            self._row_ranks = {}
            return

        # Ensure we have row tracking
        if not hasattr(self, '_row_frames'): self._row_frames = {}
        if not hasattr(self, '_row_widgets'): self._row_widgets = {}
        if not hasattr(self, '_row_ranks'): self._row_ranks = {}

        if len(self._row_frames) != len(final_list[:100]) or force:
            # Full rebuild if count changed or forced
            for widget in current_widgets: widget.destroy()
            self._row_frames = {}
            self._row_widgets = {}
            self._row_ranks = {}
            
            for i, (name, val) in enumerate(final_list[:100]):
                f = tk.Frame(self.list_container, bg=WINDOW_BG); f.pack(fill=tk.X, pady=2)
                self._row_frames[name] = f
                
                is_boss = name.lower() in self.app.bosses
                is_you = name == "You" or name == self.app.char_name.get()
                color = "#00ffff" if is_you else TEXT_PRIMARY
                
                rank_lbl = tk.Label(f, text=f"#{i+1}", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold"))
                rank_lbl.pack(side=tk.LEFT, padx=5)
                self._row_ranks[name] = rank_lbl
                
                if is_boss:
                    p_lbl = tk.Label(f, text=name, bg=WINDOW_BG, fg="#ff4444", font=("Segoe UI", 9, "bold"))
                    p_lbl.pack(side=tk.LEFT, padx=10)
                else:
                    name_container = tk.Frame(f, bg=WINDOW_BG)
                    name_container.pack(side=tk.LEFT, padx=10)
                    create_rainbow_name(name_container, self.app, name, color, ("Segoe UI", 9, "bold"), WINDOW_BG)
                
                val_str = f"{val:,.0f}cr" if cat == "loot" and "total_credits" in self.app.player_data.get(name, {}) else f"{val:,.0f}"
                val_lbl = tk.Label(f, text=val_str, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9))
                val_lbl.pack(side=tk.RIGHT, padx=5)
                self._row_widgets[name] = val_lbl
                
                f.bind("<Button-1>", lambda e, p=name: self.drill_down(p))
                for child in f.winfo_children():
                    child.bind("<Button-1>", lambda e, p=name: self.drill_down(p))
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            subchild.bind("<Button-1>", lambda e, p=name: self.drill_down(p))
        else:
            # Reorder existing frames and update values
            for i, (name, val) in enumerate(final_list[:100]):
                if name in self._row_frames:
                    f = self._row_frames[name]
                    f.pack_forget()
                    f.pack(fill=tk.X, pady=2)
                    
                    # Update rank
                    rank_str = f"#{i+1}"
                    if self._row_ranks[name].cget("text") != rank_str:
                        self._row_ranks[name].config(text=rank_str)
                    
                    # Update value
                    val_str = f"{val:,.0f}cr" if cat == "loot" and "total_credits" in self.app.player_data.get(name, {}) else f"{val:,.0f}"
                    if self._row_widgets[name].cget("text") != val_str:
                        self._row_widgets[name].config(text=val_str)
                else:
                    # This shouldn't happen if len matches, but safety first
                    force = True
                    self.refresh(force=True)
                    return
        return

    def drill_down(self, player):
        self.is_drilldown = True
        self.selected_player = player
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_to_top(self):
        self.is_drilldown = False
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_back(self):
        self.go_to_top()
