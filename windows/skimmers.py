"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
import time
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, BORDER_COLOR, COLOR_DEFAULT_CLASS,
    TITLE_GRADIENT_START
)
from utils import create_rainbow_name
from windows.base_window import BasePopoutWindow

class SkimmersWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Skimmers", "SkimmersWindow", 350, 400)
        self.search_btn = None
        self.item_detail_mode = False
        self.selected_item = None
        self.npc_detail_mode = False
        self.selected_npc = None

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return

        # Ensure search button exists
        if not self.search_btn or not self.search_btn.winfo_exists():
            self.search_btn = tk.Label(self.title_bar, text="🔍", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
            self.search_btn.bind("<Button-1>", lambda e: [self.app.toggle_skimmer_search(), self.refresh(force=True)])
        
        # Restore title label position
        if hasattr(self, 'title_label') and self.title_label.winfo_exists():
            try:
                self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 10, 16)
            except: pass
        
        # Show search button
        if not self.title_bar.find_withtag("search_btn"):
            try: self.title_bar.create_window(self.window.winfo_width() - 35, 16, window=self.search_btn, anchor="e", tags="search_btn")
            except: pass
        else:
            try: self.title_bar.coords("search_btn", self.window.winfo_width() - 35, 16)
            except: pass
        
        if self.app.skimmer_search_mode:
            try: self.search_btn.config(fg=ACCENT_BLUE)
            except: pass
        else:
            try: self.search_btn.config(fg=TEXT_SECONDARY)
            except: pass
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # User requested 1s for skimmers, but we should refresh if search is active or empty
        is_empty = True
        if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
            children = self.scrollable_frame.winfo_children()
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

        if is_empty:
            throttle = 0.2
        else:
            # User requested 3s refresh for secondary windows to help performance
            # Reduced to 1.5s as per request for smoother session updates
            throttle = 1.5
        
        do_full = force or is_empty or (now - self.last_full_refresh >= throttle)

        # Use persistent container for search and tabs to reduce flicker
        if not hasattr(self, 'scrollable_frame'):
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

            self.header_area = tk.Frame(self.content_container, bg=self.window["bg"])
            self.header_area.pack(fill=tk.X)
            
            # Filter Tabs (Loot, Mobs)
            self.t_frame = tk.Frame(self.header_area, bg=PANEL_DARK); self.t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'skimmer_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("LOOT", "loot"), ("MOBS", "mobs")]:
                btn = tk.Label(self.t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 8, "bold"), padx=10, pady=5, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_tab_cmd(val))
                self.tab_btns[val] = btn
            
            # Inventory Full Alert
            self.inventory_alert = tk.Frame(self.header_area, bg="#442222", pady=5)
            tk.Label(self.inventory_alert, text="⚠ INVENTORY FULL", bg="#442222", fg="#ff6666", font=("Segoe UI", 9, "bold")).pack()
            self.inventory_alert.pack_forget() # Hide it initially

            # Scrollable area
            self.canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas, bg=WINDOW_BG)

            self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            
            def _on_canvas_configure(e):
                 self.canvas.itemconfig(1, width=e.width)
            self.canvas.bind("<Configure>", _on_canvas_configure)
            
            self.canvas.configure(yscrollcommand=scrollbar.set)
            
            def _on_mousewheel(event):
                if not self.window: return
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            self.window.bind("<MouseWheel>", _on_mousewheel)
            self.scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
            self.canvas.bind("<MouseWheel>", _on_mousewheel)

            self.canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Bind context menus
            self.window.bind("<Button-3>", self.show_context_menu)
            self.canvas.bind("<Button-3>", self.show_context_menu)
            self.scrollable_frame.bind("<Button-3>", self.show_context_menu)
            
            do_full = True

        # Update Inventory Alert
        if self.app.inventory_full:
            self.inventory_alert.pack(fill=tk.X, pady=(0, 5))
        else:
            self.inventory_alert.pack_forget()

        # Update Search Bar
        if self.app.skimmer_search_mode:
            if not hasattr(self, 'search_frame'):
                self.search_frame = tk.Frame(self.header_area, bg=PANEL_DARK, pady=5)
                # Use pack without 'before' first, or ensure target is packed
                if self.inventory_alert.winfo_ismapped():
                    self.search_frame.pack(fill=tk.X, pady=(0, 5), before=self.inventory_alert)
                else:
                    self.search_frame.pack(fill=tk.X, pady=(0, 5))
                tk.Label(self.search_frame, text="SEARCH:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
                ent = tk.Entry(self.search_frame, textvariable=self.app.skimmer_search_query, bg=WINDOW_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief=tk.FLAT, font=("Segoe UI", 9))
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                ent.focus_set()
                ent.bind("<KeyRelease>", lambda e: self.app.root.after(100, self.refresh))
        else:
            if hasattr(self, 'search_frame'):
                self.search_frame.destroy()
                delattr(self, 'search_frame')

        # Update Tab Buttons
        tab = getattr(self.app, 'skimmer_tab', 'loot')
        if hasattr(self, 'tab_btns'):
            for v, btn in self.tab_btns.items():
                try:
                    if btn.winfo_exists():
                        active = (v == tab)
                        btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
                except: pass

        # Update Title and Navigation Buttons
        is_drill = getattr(self, 'is_drilldown', False)
        item_mode = getattr(self, 'item_detail_mode', False)
        npc_mode = getattr(self, 'npc_detail_mode', False)
        
        if is_drill or item_mode or npc_mode:
            if hasattr(self, 'nav_row') and self.nav_row.winfo_exists():
                if self.header_area.winfo_exists() and self.header_area.winfo_ismapped():
                    self.nav_row.pack(fill=tk.X, before=self.header_area)
                else:
                    self.nav_row.pack(fill=tk.X)
                
                # Context Label
                ctx_text = ""
                if npc_mode:
                    npc_name = getattr(self, 'selected_npc', 'NPC')
                    if len(npc_name) > 15: npc_name = npc_name[:12] + "..."
                    ctx_text = npc_name.upper()
                elif item_mode:
                    item_name = self.selected_item.get("item", "Item")
                    if len(item_name) > 15: item_name = item_name[:12] + "..."
                    ctx_text = item_name.upper()
                elif is_drill:
                    p_name = getattr(self, 'selected_player', 'PLAYER')
                    ctx_text = p_name.upper()
                
                # Color 'You' cyan
                is_you = ctx_text == "YOU" or ctx_text == self.app.char_name.get().upper()
                self.nav_player_label.config(text=ctx_text, fg="#00ffff" if is_you else ACCENT_BLUE)

            try: self.title_bar.itemconfig(self.title_label, text="SKIMMERS")
            except: pass
            
            # Hide Search Bar if drilldown (optional, but requested for 'loot for playername' view)
            # Actually, user says 'no nav bar' which usually means the nav row.
        else:
            if hasattr(self, 'nav_row'):
                self.nav_row.pack_forget()
            try: self.title_bar.itemconfig(self.title_label, text="Skimmers")
            except: pass
        
        # In drilldown views (is_drill, item_mode, npc_mode), we want the nav_row to be visible.
        # But we also need to make sure header_area (Tabs/Search) is managed correctly.
        if is_drill or item_mode or npc_mode:
            if self.header_area.winfo_exists():
                self.header_area.pack_forget()
        else:
            if self.header_area.winfo_exists() and not self.header_area.winfo_ismapped():
                if hasattr(self, 'canvas') and self.canvas.winfo_exists() and self.canvas.winfo_ismapped():
                    self.header_area.pack(fill=tk.X, before=self.canvas) # Ensure it packs before canvas
                else:
                    self.header_area.pack(fill=tk.X)

        if not do_full: return
        self.last_full_refresh = now

        # Main Skimmer logic
        tab = getattr(self.app, 'skimmer_tab', 'loot')
        query = self.app.skimmer_search_query.get().lower() if self.app.skimmer_search_mode else ""
        item_mode = getattr(self, 'item_detail_mode', False)
        npc_mode = getattr(self, 'npc_detail_mode', False)
        is_drill = getattr(self, 'is_drilldown', False)
        
        if npc_mode:
            npc = getattr(self, 'selected_npc', 'Unknown')
            player = getattr(self, 'selected_player', '')
            
            # Use persistent labels to avoid flicker
            if not hasattr(self, '_npc_header_lbl'):
                for widget in self.scrollable_frame.winfo_children(): widget.destroy()
                self._npc_header_lbl = tk.Label(self.scrollable_frame, text="NPC LOOT HISTORY", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold"))
                self._npc_header_lbl.pack(pady=(20, 10))
                self._npc_sub_header = tk.Label(self.scrollable_frame, text="", bg=WINDOW_BG, font=("Segoe UI", 9, "bold"))
                self._npc_sub_header.pack(pady=(0, 5))
                self._npc_name_lbl = tk.Label(self.scrollable_frame, text="", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"), wraplength=self.window.winfo_width()-40)
                self._npc_name_lbl.pack(pady=5)
                self._npc_content_frame = tk.Frame(self.scrollable_frame, bg=WINDOW_BG)
                self._npc_content_frame.pack(fill=tk.BOTH, expand=True)

            if player:
                is_you = player == "You" or player == self.app.char_name.get()
                self.update_if_changed(self._npc_sub_header, f"VIA {player.upper()}")
                self._npc_sub_header.config(fg="#00ffff" if is_you else TEXT_SECONDARY)
            else:
                self.update_if_changed(self._npc_sub_header, "")

            self.update_if_changed(self._npc_name_lbl, npc)
            
            # Key check for NPC loot list
            npc_key = f"npc_loot_{npc}_{player}_{query}"
            if not force and hasattr(self, '_last_npc_key') and self._last_npc_key == npc_key:
                return
            self._last_npc_key = npc_key

            for widget in self._npc_content_frame.winfo_children(): widget.destroy()
            
            # Find all loot from this NPC
            all_loot = []
            for p, loots in self.app.loot_data.items():
                for entry in loots:
                    if entry.get("target") == npc and not entry.get("credits"):
                        if not query or query in entry.get("item", "").lower() or query in p.lower():
                            all_loot.append((p, entry))
            
            if not all_loot:
                tk.Label(self._npc_content_frame, text="No items recorded", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            else:
                for p, entry in sorted(all_loot, key=lambda x: x[1].get('timestamp', 0), reverse=True):
                    f = tk.Frame(self._npc_content_frame, bg=WINDOW_BG); f.pack(fill=tk.X, pady=2, padx=5)
                    item_text = entry.get("item", "Unknown")
                    tk.Label(f, text=item_text, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9), wraplength=self.window.winfo_width()-150, justify="left").pack(side=tk.LEFT, padx=5)
                    
                    looter_color = ACCENT_BLUE
                    display_name = p
                    if p == "You" or p == self.app.char_name.get():
                        looter_color = "#00ffff"
                        display_name = "You"
                    
                    looter_lbl = tk.Label(f, text=display_name, bg=WINDOW_BG, fg=looter_color, font=("Segoe UI", 9, "bold"), cursor="hand2")
                    looter_lbl.pack(side=tk.RIGHT, padx=5)
                    looter_lbl.bind("<Button-1>", lambda e, p_name=p: [setattr(self, 'npc_detail_mode', False), setattr(self, 'item_detail_mode', False), setattr(self, 'is_drilldown', True), setattr(self, 'selected_player', p_name), self.refresh(force=True)])
            return

        if item_mode:
            for widget in self.scrollable_frame.winfo_children(): widget.destroy()
            
            item = self.selected_item
            player = getattr(self, 'selected_player', 'Unknown')
            tk.Label(self.scrollable_frame, text="ITEM DETAILS", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
            
            # Show Player Name prominently
            is_you = player == "You" or player == self.app.char_name.get()
            tk.Label(self.scrollable_frame, text=f"LOOTED BY: {player.upper()}", bg=WINDOW_BG, fg="#00ffff" if is_you else ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))

            # Item Name
            tk.Label(self.scrollable_frame, text=item.get("item", "Unknown"), bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"), wraplength=self.window.winfo_width()-40).pack(pady=5)
            
            # Looter
            looter_color = TEXT_SECONDARY
            display_name = player
            if player == "You" or player == self.app.char_name.get():
                looter_color = "#00ffff"
                display_name = "You"
            tk.Label(self.scrollable_frame, text=f"Looted by: {display_name}", bg=WINDOW_BG, fg=looter_color, font=("Segoe UI", 9, "bold" if display_name == "You" else "normal")).pack(pady=2)

            # Time
            ts = item.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "Unknown"
            tk.Label(self.scrollable_frame, text=f"Time: {ts_str}", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(pady=2)
            
            # Dropped by (NPC)
            target = item.get("target", "Unknown")
            target_lbl = tk.Label(self.scrollable_frame, text=f"Dropped by: {target}", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9), wraplength=self.window.winfo_width()-40, cursor="hand2" if target != "Unknown" else "")
            target_lbl.pack(pady=2)
            
            if target != "Unknown":
                target_lbl.config(fg=ACCENT_BLUE)
                def show_npc_detail(e, n=target, p=player):
                    self.npc_detail_mode = True
                    self.selected_npc = n
                    self.selected_player = p # Keep player context
                    self.refresh(force=True)
                target_lbl.bind("<Button-1>", show_npc_detail)
            
            return

        players_with_data = set()
        if tab == "loot":
            # Only include players who have actual items (exclude credits)
            for p, loots in self.app.loot_data.items():
                items = [entry for entry in loots if not entry.get("credits")]
                if items:
                    players_with_data.add(p)
            
            if self.app.enable_sync.get() and self.app.sync_data:
                sync_loot_dict = self.app.sync_data.get("data", {}).get("loot", {})
                for p, loots in sync_loot_dict.items():
                    items = [entry for entry in loots if not entry.get("credits")]
                    if items:
                        players_with_data.add(p)
        else: # mobs
            players_with_data = set(name for name, d in self.app.player_data.items() if d.get("lb_mobs", 0) > 0)

        # Ensure "You" is always considered if there is data, and query matches
        if not players_with_data and not query:
             # Basic check to see if we should show 'No data'
             pass

        from utils import is_probable_player
        final_players = sorted([p for p in players_with_data if (not query or query in p.lower()) and is_probable_player(p, self.app.bosses, known_players=self.app.known_players)])

        current_widgets = self.scrollable_frame.winfo_children()
        
        if is_drill:
            p = getattr(self, 'selected_player', '')
            
            # Use persistent labels to avoid flicker
            if not hasattr(self, '_drill_header_lbl'):
                for widget in self.scrollable_frame.winfo_children(): widget.destroy()
                self._drill_header_lbl = tk.Label(self.scrollable_frame, text="", bg=WINDOW_BG, font=("Segoe UI", 10, "bold"))
                self._drill_header_lbl.pack(pady=(10, 5))
                self._drill_content_frame = tk.Frame(self.scrollable_frame, bg=WINDOW_BG)
                self._drill_content_frame.pack(fill=tk.BOTH, expand=True)

            is_you = p == "You" or p == self.app.char_name.get()
            header_text = f"{tab.upper()} FOR {p.upper()}"
            header_color = "#00ffff" if is_you else ACCENT_BLUE
            self.update_if_changed(self._drill_header_lbl, header_text)
            self._drill_header_lbl.config(fg=header_color)

            if tab == "loot":
                raw_items = self.app.loot_data.get(p, [])
                if self.app.enable_sync.get() and self.app.sync_data:
                    sync_loot = self.app.sync_data.get("data", {}).get("loot", {}).get(p, [])
                    if sync_loot: 
                        raw_items = list(raw_items) + list(sync_loot)
                
                # Filter out credits
                items = [entry for entry in raw_items if not entry.get("credits")]
                if query:
                    items = [entry for entry in items if query in entry.get("item", "").lower() or query in entry.get("target", "").lower()]
                
                # For logs/lists in drilldown, we still need to clear/rebuild if they change significantly
                # but we can use a key check
                loot_key = f"loot_{p}_{len(items)}_{query}"
                if not force and hasattr(self, '_last_loot_key') and self._last_loot_key == loot_key:
                    return
                self._last_loot_key = loot_key
                
                for widget in self._drill_content_frame.winfo_children(): widget.destroy()
                
                if not items:
                    tk.Label(self._drill_content_frame, text="No items looted", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                else:
                    for entry in reversed(items[-100:]):
                        f = tk.Frame(self._drill_content_frame, bg=WINDOW_BG); f.pack(fill=tk.X, pady=1)
                        item_text = entry.get("item", "Unknown")
                        
                        lbl = tk.Label(f, text=item_text, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9), wraplength=self.window.winfo_width()-40, justify="left", cursor="hand2")
                        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
                        
                        def show_detail(e, itm=entry):
                            self.item_detail_mode = True
                            self.selected_item = itm
                            self.refresh(force=True)
                        
                        lbl.bind("<Button-1>", show_detail)
                        f.bind("<Button-1>", show_detail)
            else: # mobs
                mob_count = self.app.player_data.get(p, {}).get('lb_mobs', 0)
                mob_key = f"mobs_{p}_{mob_count}"
                if not force and hasattr(self, '_last_mob_key') and self._last_mob_key == mob_key:
                    return
                self._last_mob_key = mob_key
                
                for widget in self._drill_content_frame.winfo_children(): widget.destroy()
                tk.Label(self._drill_content_frame, text=f"MOB KILLS: {mob_count}", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).pack(pady=20)
            return

        self.header_area.pack(fill=tk.X)

        # Surgical update check
        current_players = getattr(self, '_last_players', [])
        
        if not final_players:
            if not hasattr(self, '_no_data_lbl'):
                for widget in self.scrollable_frame.winfo_children(): widget.destroy()
                self._no_data_lbl = tk.Label(self.scrollable_frame, text=f"No {tab} data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic"))
                self._no_data_lbl.pack(pady=20)
                self._row_frames = {}
                self._row_widgets = {}
            return

        if hasattr(self, '_no_data_lbl'):
            self._no_data_lbl.destroy()
            del self._no_data_lbl

        if not hasattr(self, '_row_frames'): self._row_frames = {}
        if not hasattr(self, '_row_widgets'): self._row_widgets = {}

        # Reorder and update
        for p in final_players:
            if p not in self._row_frames:
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG)
                self._row_frames[p] = f
                
                is_you = p == "You" or p == self.app.char_name.get()
                color = "#00ffff" if is_you else TEXT_PRIMARY
                
                # Create clickable container for the whole row
                row_click_frame = tk.Frame(f, bg=WINDOW_BG, cursor="hand2")
                row_click_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                create_rainbow_name(row_click_frame, self.app, p, color, ("Segoe UI", 9, "bold"), WINDOW_BG)
                
                # Store row mapping for value updates
                val_lbl = tk.Label(f, text="0", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8), cursor="hand2")
                val_lbl.pack(side=tk.RIGHT, padx=5)
                self._row_widgets[p] = val_lbl
                
                def drill_down_event(e, p_name=p):
                    self.drill_down(p_name)
                
                f.bind("<Button-1>", drill_down_event)
                for child in f.winfo_children():
                    child.bind("<Button-1>", drill_down_event)
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            subchild.bind("<Button-1>", drill_down_event)
            
            f = self._row_frames[p]
            f.pack(fill=tk.X, pady=1)
            
            if tab == "loot":
                raw_items = self.app.loot_data.get(p, [])
                items = [entry for entry in raw_items if not entry.get("credits")]
                val_str = f"{len(items)} items"
            else:
                count = self.app.player_data.get(p, {}).get("lb_mobs", 0)
                val_str = str(count)
            
            self.update_if_changed(self._row_widgets[p], val_str)

        # Cleanup old rows
        current_names = set(final_players)
        to_delete = [name for name in self._row_frames if name not in current_names]
        for name in to_delete:
            self._row_frames[name].destroy()
            del self._row_frames[name]
            del self._row_widgets[name]
        return
        return

    def drill_down(self, player):
        self.is_drilldown = True
        self.selected_player = player
        self.item_detail_mode = False
        self.npc_detail_mode = False
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_to_top(self):
        self.is_drilldown = False
        self.item_detail_mode = False
        self.npc_detail_mode = False
        self.selected_npc = None
        self.selected_item = None
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_back(self):
        if getattr(self, 'npc_detail_mode', False):
            self.npc_detail_mode = False
            self.selected_npc = None
        elif getattr(self, 'item_detail_mode', False):
            self.item_detail_mode = False
            self.selected_item = None
        else:
            self.is_drilldown = False
        self.last_full_refresh = 0
        self.refresh(force=True)

    def copy_to_clipboard(self):
        # Determine what to copy based on current view
        tab = getattr(self.app, 'skimmer_tab', 'loot')
        is_drill = getattr(self, 'is_drilldown', False)
        
        if is_drill:
            # Player-specific drilldown
            p = getattr(self, 'selected_player', 'PLAYER')
            if tab == 'loot':
                items = self.app.player_data.get(p, {}).get("looted_items", [])
                lines = [f"Loot for {p}:"]
                for itm in items:
                    lines.append(f"{itm.get('count', 1)}x {itm.get('name', 'Unknown')}")
            else:
                # Mobs
                mobs = self.app.player_data.get(p, {}).get("mobs", {})
                lines = [f"Mobs killed by {p}:"]
                for mob, count in sorted(mobs.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"{mob}: {count}")
        elif getattr(self, 'item_detail_mode', False):
            # Item detail (who has it)
            itm_name = getattr(self, 'selected_item', 'Unknown Item')
            lines = [f"Holders of {itm_name}:"]
            for p, pdata in self.app.player_data.items():
                count = sum(i.get('count', 1) for i in pdata.get('looted_items', []) if i.get('name') == itm_name)
                if count > 0:
                    lines.append(f"{p}: {count}")
        elif getattr(self, 'npc_detail_mode', False):
            # NPC detail (who killed it)
            npc_name = getattr(self, 'selected_npc', 'Unknown NPC')
            lines = [f"Killers of {npc_name}:"]
            for p, pdata in self.app.player_data.items():
                count = pdata.get('mobs', {}).get(npc_name, 0)
                if count > 0:
                    lines.append(f"{p}: {count}")
        else:
            # Global view
            if tab == 'loot':
                lines = ["GLOBAL LOOT:"]
                all_items = {}
                for pdata in self.app.player_data.values():
                    for itm in pdata.get('looted_items', []):
                        name = itm.get('name', 'Unknown')
                        all_items[name] = all_items.get(name, 0) + itm.get('count', 1)
                for name, count in sorted(all_items.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"{count}x {name}")
            else:
                lines = ["GLOBAL MOBS:"]
                all_mobs = {}
                for pdata in self.app.player_data.values():
                    for mob, count in pdata.get('mobs', {}).items():
                        all_mobs[mob] = all_mobs.get(mob, 0) + count
                for mob, count in sorted(all_mobs.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"{mob}: {count}")
                    
        if len(lines) > 1:
            self.window.clipboard_clear()
            self.window.clipboard_append("\n".join(lines))
