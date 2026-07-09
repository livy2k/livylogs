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

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        # Additional title bar buttons for Skimmers
        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_skimmers_manual())

        search_btn = tk.Label(self.title_bar, text="🔍", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
        search_btn.pack(side=tk.LEFT)
        search_btn.bind("<Button-1>", lambda e: self.app.toggle_skimmer_search())
        if self.app.skimmer_search_mode: search_btn.config(fg=ACCENT_BLUE)

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
            t_frame = tk.Frame(self.header_area, bg=PANEL_DARK); t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'skimmer_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("LOOT", "loot"), ("SYSTEM", "system")]:
                btn = tk.Label(t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
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
        
        query = self.app.skimmer_search_query.get().lower() if self.app.skimmer_search_mode else ""
        items_to_show = []
        if tab == "loot":
            # Merge local loot data
            for player, items in self.app.loot_data.items():
                for item in items:
                    if not query or query in item["item"].lower() or query in player.lower():
                        items_to_show.append({"type": "loot", "player": player, "item": item["item"], "timestamp": item["timestamp"]})
            
            # Merge remote loot data if enabled
            if self.app.enable_sync.get() and self.app.sync_data:
                remote_loot = self.app.sync_data.get("data", {}).get("loot", {})
                for remote_player, remote_items in remote_loot.items():
                    # Don't duplicate local "You"
                    if remote_player == self.app.char_name.get(): continue
                    for item in remote_items:
                        # Remote item structure might need conversion if timestamp is string
                        ts = item.get("timestamp")
                        if isinstance(ts, str):
                            from datetime import datetime
                            try: ts = datetime.fromisoformat(ts)
                            except: ts = None
                        elif isinstance(ts, (int, float)):
                            from datetime import datetime
                            ts = datetime.fromtimestamp(ts)
                        
                        if not query or query in item["item"].lower() or query in remote_player.lower():
                            items_to_show.append({"type": "loot", "player": remote_player, "item": item["item"], "timestamp": ts})

        if not items_to_show:
            tk.Label(self.scrollable_frame, text="No items found", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
        else:
            items_to_show.sort(key=lambda x: x["timestamp"], reverse=True)
            for item in items_to_show[:100]: # Limit items
                ts = item["timestamp"].strftime("%H:%M:%S") if item["timestamp"] else "??:??:??"
                f = tk.Frame(self.scrollable_frame, bg=WINDOW_BG, pady=2); f.pack(fill=tk.X)
                tk.Label(f, text=f"[{ts}]", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Consolas", 8)).pack(side=tk.LEFT)
                tk.Label(f, text=f" {item['player']}", bg=WINDOW_BG, fg=ACCENT_BLUE if (item['player'] == "You" or item['player'] == self.app.char_name.get()) else TEXT_ACCENT, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
                tk.Label(f, text=f" looted {item['item']}", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
