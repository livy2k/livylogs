import tkinter as tk
import time
from tkinter import ttk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, BORDER_COLOR
)
from windows.base_window import BasePopoutWindow

class SkimmersWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Skimmers", "SkimmersWindow", 350, 400)
        self.drill_down_player = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
        self.back_btn.pack(side=tk.LEFT, before=self.title_label)
        self.back_btn.bind("<Button-1>", lambda e: self.go_back())
        self.back_btn.pack_forget()

        # Additional title bar buttons for Skimmers
        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_skimmers_manual())

        search_btn = tk.Label(self.title_bar, text="🔍", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
        search_btn.pack(side=tk.LEFT)
        search_btn.bind("<Button-1>", lambda e: self.app.toggle_skimmer_search())
        if self.app.skimmer_search_mode: search_btn.config(fg=ACCENT_BLUE)

    def go_back(self):
        self.drill_down_player = None
        self.back_btn.pack_forget()
        self.refresh(force=True)

    def drill_down(self, player):
        self.drill_down_player = player
        self.back_btn.pack(side=tk.LEFT, before=self.title_label)
        self.refresh(force=True)

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # User requested 5s for skimmers, but we should refresh if search is active
        throttle = 1.0 if self.app.skimmer_search_mode else 5.0
        do_full = force or (now - self.last_full_refresh >= throttle)

        # Use persistent container for search and tabs to reduce flicker
        if not hasattr(self, 'scrollable_frame'):
            for widget in self.content_container.winfo_children(): widget.destroy()
            
            self.header_area = tk.Frame(self.content_container, bg=self.window["bg"])
            self.header_area.pack(fill=tk.X)
            
            # Filter Tabs (Loot, Combat, System)
            self.t_frame = tk.Frame(self.header_area, bg=PANEL_DARK); self.t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'skimmer_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("LOOT", "loot"), ("SYSTEM", "system")]:
                btn = tk.Label(self.t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 8, "bold"), padx=10, pady=5, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_tab_cmd(val))
                self.tab_btns[val] = btn

            # Inventory Full Alert
            self.inventory_alert = tk.Frame(self.header_area, bg="#442222", pady=5)
            tk.Label(self.inventory_alert, text="⚠ INVENTORY FULL", bg="#442222", fg="#ff6666", font=("Segoe UI", 9, "bold")).pack()

            # Scrollable area
            canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
            self.scrollable_frame = tk.Frame(canvas, bg=WINDOW_BG)

            self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            def _on_mousewheel(event): canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            do_full = True

        # Update Search Bar (it can be toggled)
        if self.app.skimmer_search_mode:
            if not hasattr(self, 'search_frame'):
                self.search_frame = tk.Frame(self.header_area, bg=PANEL_DARK, pady=5)
                self.search_frame.pack(fill=tk.X, pady=(0, 5), before=self.inventory_alert)
                tk.Label(self.search_frame, text="SEARCH:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
                ent = tk.Entry(self.search_frame, textvariable=self.app.skimmer_search_query, bg=WINDOW_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief=tk.FLAT, font=("Segoe UI", 9))
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                ent.focus_set()
                ent.bind("<KeyRelease>", lambda e: self.app.root.after(100, self.refresh))
        else:
            if hasattr(self, 'search_frame'):
                self.search_frame.destroy()
                delattr(self, 'search_frame')

        # Visibility logic for tabs during drill down
        if self.drill_down_player:
            if hasattr(self, 'back_btn'): self.back_btn.pack(side=tk.LEFT, before=self.title_label)
            self.t_frame.pack_forget()
            if hasattr(self, 'search_frame'): self.search_frame.pack_forget()
        else:
            if hasattr(self, 'back_btn'): self.back_btn.pack_forget()
            self.t_frame.pack(fill=tk.X, pady=(0, 5), before=self.inventory_alert)
            if hasattr(self, 'search_frame'): self.search_frame.pack(fill=tk.X, pady=(0, 5), before=self.inventory_alert)
            
            # Update Tab Buttons
            tab = getattr(self.app, 'skimmer_tab', 'loot')
            for v, btn in self.tab_btns.items():
                active = (v == tab)
                btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)

        # Update Inventory Alert
        if self.app.inventory_full:
            self.inventory_alert.pack(fill=tk.X, pady=(0, 5))
        else:
            self.inventory_alert.pack_forget()

        if not do_full: return
        self.last_full_refresh = now

        # Update List
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        
        if self.drill_down_player:
            # Show only loot for this specific player
            p_loot = self.app.loot_data.get(self.drill_down_player, [])
            
            # Merge remote loot if available
            remote_p_loot = []
            if self.app.enable_sync.get() and self.app.sync_data:
                remote_p_loot = self.app.sync_data.get("data", {}).get("loot", {}).get(self.drill_down_player, [])
            
            all_p_loot = p_loot.copy()
            seen_items = set((i["item"], i["timestamp"]) for i in all_p_loot)
            for ri in remote_p_loot:
                ts = ri.get("timestamp")
                if isinstance(ts, (int, float)): from datetime import datetime; ts = datetime.fromtimestamp(ts)
                if (ri["item"], ts) not in seen_items:
                    all_p_loot.append({"item": ri["item"], "timestamp": ts})

            if not all_p_loot:
                tk.Label(self.scrollable_frame, text=f"No loot recorded for {self.drill_down_player}", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                return
            
            all_p_loot.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, reverse=True)
            for item in all_p_loot[:100]:
                ts = item["timestamp"].strftime("%H:%M:%S") if item["timestamp"] else "??:??:??"
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG, pady=2); f.pack(fill=tk.X)
                tk.Label(f, text=f"[{ts}]", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Consolas", 8)).pack(side=tk.LEFT)
                tk.Label(f, text=f" {item['item']}", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            return

        # Top-level View: List players who have loot
        query = self.app.skimmer_search_query.get().lower() if self.app.skimmer_search_mode else ""
        players_with_loot = set(self.app.loot_data.keys())
        if self.app.enable_sync.get() and self.app.sync_data:
            players_with_loot.update(self.app.sync_data.get("data", {}).get("loot", {}).keys())

        final_players = sorted(list(players_with_loot))
        if not final_players:
            tk.Label(self.scrollable_frame, text="No loot recorded", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
        else:
            for p in final_players:
                if query and query not in p.lower(): continue
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG, pady=4, cursor="hand2"); f.pack(fill=tk.X)
                f.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                
                color = ACCENT_BLUE if (p == "You" or p == self.app.char_name.get()) else TEXT_ACCENT
                lbl = tk.Label(f, text=p, bg=WINDOW_BG, fg=color, font=("Segoe UI", 10, "bold"))
                lbl.pack(side=tk.LEFT, padx=10)
                lbl.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                
                count = len(self.app.loot_data.get(p, []))
                tk.Label(f, text=f"({count} items)", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=10)
