import tkinter as tk
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
        self.drill_down_player = None
        self.search_btn = None
        self.back_btn = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        if not hasattr(self, 'back_btn'):
            self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
            self.back_btn.bind("<Button-1>", lambda e: self.go_back())
        
        if not hasattr(self, 'search_btn'):
            self.search_btn = tk.Label(self.title_bar, text="🔍", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
            self.search_btn.bind("<Button-1>", lambda e: [self.app.toggle_skimmer_search(), self.refresh(force=True)])
        
        # Initial search button placement (will be managed by refresh)
        if not self.title_bar.find_withtag("search_btn"):
            self.title_bar.create_window(self.default_w - 35, 16, window=self.search_btn, anchor="e", tags="search_btn")

    def go_back(self):
        self.drill_down_player = None
        if hasattr(self, 'back_btn'): self.title_bar.delete("back_btn")
        self.refresh(force=True)

    def drill_down(self, player):
        self.drill_down_player = player
        if hasattr(self, 'back_btn'):
            self.title_bar.delete("back_btn")
            self.title_bar.create_window(10, 16, window=self.back_btn, anchor="w", tags="back_btn")
            # Shift title label to the right
            self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 35, 16)
        self.refresh(force=True)

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return

        # Ensure buttons exist
        if not self.search_btn or not self.search_btn.winfo_exists():
            self.search_btn = tk.Label(self.title_bar, text="🔍", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
            self.search_btn.bind("<Button-1>", lambda e: [self.app.toggle_skimmer_search(), self.refresh(force=True)])
        
        if not self.back_btn or not self.back_btn.winfo_exists():
            self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
            self.back_btn.bind("<Button-1>", lambda e: self.go_back())

        # Ensure back button state
        if not self.drill_down_player:
            try: self.title_bar.delete("back_btn")
            except: pass
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
        else:
            if not self.title_bar.find_withtag("back_btn"):
                try: self.title_bar.create_window(10, 16, window=self.back_btn, anchor="w", tags="back_btn")
                except: pass
                if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                    try:
                        self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 35, 16)
                    except: pass
            # Hide search button during drill down
            try: self.title_bar.delete("search_btn")
            except: pass
        
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
            
            # Filter Tabs (Loot)
            self.t_frame = tk.Frame(self.header_area, bg=PANEL_DARK); self.t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'skimmer_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("LOOT", "loot")]:
                btn = tk.Label(self.t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 8, "bold"), padx=10, pady=5, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_tab_cmd(val))
                self.tab_btns[val] = btn
            
            # Inventory Full Alert (placed after tabs initially)
            self.inventory_alert = tk.Frame(self.header_area, bg="#442222", pady=5)
            tk.Label(self.inventory_alert, text="⚠ INVENTORY FULL", bg="#442222", fg="#ff6666", font=("Segoe UI", 9, "bold")).pack()
            self.inventory_alert.pack_forget() # Hide it initially

            # Scrollable area
            canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            # scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
            scrollbar = tk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview, bg=PANEL_DARK, troughcolor=WINDOW_BG, bd=0, highlightthickness=0)
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
            # Back button handled above
            if hasattr(self, 't_frame') and self.t_frame.winfo_exists():
                self.t_frame.pack_forget()
            if hasattr(self, 'search_frame') and self.search_frame.winfo_exists():
                self.search_frame.pack_forget()
        else:
            # Back button hidden above
            if hasattr(self, 't_frame') and self.t_frame.winfo_exists():
                self.t_frame.pack(fill=tk.X, pady=(0, 5)) 
            if hasattr(self, 'search_frame') and self.search_frame.winfo_exists():
                self.search_frame.pack(fill=tk.X, pady=(0, 5)) 
            
            # Update Tab Buttons
            tab = getattr(self.app, 'skimmer_tab', 'loot')
            if hasattr(self, 'tab_btns'):
                for v, btn in self.tab_btns.items():
                    if btn.winfo_exists():
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

        tab = getattr(self.app, 'skimmer_tab', 'loot')

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
                tk.Label(self.scrollable_frame, text=f"No {tab} recorded for {self.drill_down_player}", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                return
            
            all_p_loot.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, reverse=True)
            for item in all_p_loot[:100]:
                ts = item["timestamp"].strftime("%H:%M:%S") if item["timestamp"] else "??:??:??"
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG, pady=2); f.pack(fill=tk.X)
                tk.Label(f, text=f"[{ts}]", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Consolas", 8)).pack(side=tk.LEFT)
                
                display_text = f" {item['item']}"

                tk.Label(f, text=display_text, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            return

        # Top-level View: List players who have loot
        query = self.app.skimmer_search_query.get().lower() if self.app.skimmer_search_mode else ""
        
        players_with_loot = set(self.app.loot_data.keys())
        if self.app.enable_sync.get() and self.app.sync_data:
            players_with_loot.update(self.app.sync_data.get("data", {}).get("loot", {}).keys())

        final_players = sorted(list(players_with_loot))
        if not final_players:
            tk.Label(self.scrollable_frame, text=f"No {tab} recorded", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
        else:
            for p in final_players:
                if query and query not in p.lower(): continue
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG, pady=4, cursor="hand2"); f.pack(fill=tk.X)
                f.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                
                color = ACCENT_BLUE if (p == "You" or p == self.app.char_name.get()) else TEXT_ACCENT
                
                name_container = tk.Frame(f, bg=WINDOW_BG)
                name_container.pack(side=tk.LEFT, padx=10)
                labels = create_rainbow_name(name_container, self.app, p, color, ("Segoe UI", 10, "bold"), WINDOW_BG)
                for l in labels:
                    l.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                name_container.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                
                count = len(self.app.loot_data.get(p, []))
                tk.Label(f, text=f"({count} items)", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=10)
