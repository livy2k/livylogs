import tkinter as tk
import time
from datetime import datetime
from constants import (
    PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE
)
from windows.base_window import BasePopoutWindow

class LeaderboardWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Leaderboard", "LeaderboardWindow", 300, 400)

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_leaderboard_manual())

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Determine if we should do a full data calculation
        do_full = force or (now - self.last_full_refresh >= 5.0)

        # Use an update strategy that minimizes widget recreation
        if not hasattr(self, 'list_container'):
            for widget in self.content_container.winfo_children(): widget.destroy()
            
            # Category Selector
            c_frame = tk.Frame(self.content_container, bg=PANEL_DARK); c_frame.pack(fill=tk.X, pady=(0, 5))
            self.cat_btns = {}
            
            def make_cat_cmd(v): return lambda e: [setattr(self.app, 'leaderboard_cat', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("DAMAGE", "damage"), ("HEALING", "healing"), ("LOOT", "loot")]:
                btn = tk.Label(c_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 7, "bold"), padx=5, pady=3, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_cat_cmd(val))
                self.cat_btns[val] = btn

            # Header
            h = tk.Frame(self.content_container, bg=PANEL_DARK); h.pack(fill=tk.X, pady=(0, 5))
            tk.Label(h, text="RANK", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Label(h, text="PLAYER", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=20)
            self.lbl_cat_head = tk.Label(h, text="DAMAGE", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"))
            self.lbl_cat_head.pack(side=tk.RIGHT, padx=5)
            
            self.list_container = tk.Frame(self.content_container, bg=self.window["bg"])
            self.list_container.pack(fill=tk.BOTH, expand=True)
            do_full = True

        # Update Category Buttons
        cat = getattr(self.app, 'leaderboard_cat', 'damage')
        for v, btn in self.cat_btns.items():
            active = (v == cat)
            btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
        
        self.lbl_cat_head.config(text=cat.upper())

        if not do_full: return
        self.last_full_refresh = now

        # Data gathering
        data_list = []
        if cat in ["damage", "healing"]:
            for name, data in self.app.player_data.items():
                val = data.get(cat, 0)
                if val > 0: data_list.append((name, val))
        elif cat == "loot":
            for name, data in self.app.player_data.items():
                val = data.get("lb_loot", 0)
                if val > 0: data_list.append((name, val))

        sorted_list = sorted(data_list, key=lambda x: x[1], reverse=True)
        
        # Rebuild only the list part
        for widget in self.list_container.winfo_children(): widget.destroy()
        
        if not sorted_list:
            tk.Label(self.list_container, text=f"No {cat} data", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            return

        for i, (name, val) in enumerate(sorted_list[:50]): # Limit to top 50
            f = tk.Frame(self.list_container, bg=self.window["bg"]); f.pack(fill=tk.X, pady=2)
            color = ACCENT_BLUE if name == "You" else TEXT_PRIMARY
            tk.Label(f, text=f"#{i+1}", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Label(f, text=name, bg=self.window["bg"], fg=color, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)
            
            val_str = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
            tk.Label(f, text=val_str, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=5)
