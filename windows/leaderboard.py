import tkinter as tk
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
        self.drill_down_player = None
        self.back_btn = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
        self.back_btn.bind("<Button-1>", lambda e: self.go_back())
        # The back button will be placed by the refresh logic or drill_down

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

        # Ensure back button exists
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
        else:
            if not self.title_bar.find_withtag("back_btn"):
                try: self.title_bar.create_window(10, 16, window=self.back_btn, anchor="w", tags="back_btn")
                except: pass
                if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                    try:
                        self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 35, 16)
                    except: pass
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Determine if we should do a full data calculation
        do_full = force or (now - self.last_full_refresh >= 5.0)

        # Use an update strategy that minimizes widget recreation
        if not hasattr(self, 'list_container'):
            for widget in self.content_container.winfo_children(): widget.destroy()
            
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
            self.lbl_cat_head.pack(side=tk.RIGHT, padx=25) # Extra pad for scrollbar
        
            # Scrollable area
            canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            # scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
            scrollbar = tk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview, bg=PANEL_DARK, troughcolor=WINDOW_BG, bd=0, highlightthickness=0)
            self.list_container = tk.Frame(canvas, bg=WINDOW_BG)

            self.list_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=self.list_container, anchor="nw", width=self.default_w - 20)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            def _on_mousewheel(event): canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            do_full = True

        if self.drill_down_player:
            # Back button handled above
            if hasattr(self, 'lbl_rank') and self.lbl_rank.winfo_exists():
                self.lbl_rank.config(text="TARGET")
            if hasattr(self, 'lbl_player') and self.lbl_player.winfo_exists():
                self.lbl_player.pack_forget()
            if hasattr(self, 'lbl_cat_head') and self.lbl_cat_head.winfo_exists():
                self.lbl_cat_head.config(text="AMOUNT")
        else:
            # Back button hidden above
            if hasattr(self, 'c_frame') and self.c_frame.winfo_exists():
                self.c_frame.pack(fill=tk.X, pady=(0, 5), before=self.h_frame)
            if hasattr(self, 'lbl_rank') and self.lbl_rank.winfo_exists():
                self.lbl_rank.config(text="RANK")
            if hasattr(self, 'lbl_player') and self.lbl_player.winfo_exists():
                self.lbl_player.pack(side=tk.LEFT, padx=20, before=self.lbl_cat_head)
            
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

        if not do_full: return
        self.last_full_refresh = now

        # Rebuild only the list part
        for widget in self.list_container.winfo_children(): widget.destroy()

        if self.drill_down_player:
            p_data = self.app.player_data.get(self.drill_down_player, {})
            cat = getattr(self.app, 'leaderboard_cat', 'damage')
            
            if cat == "loot":
                # Special view for loot: show total credits and then items
                credits = p_data.get("total_credits", 0)
                if credits > 0:
                    f = tk.Frame(self.list_container, bg=self.window["bg"]); f.pack(fill=tk.X, pady=(5, 10))
                    tk.Label(f, text="TOTAL CREDITS", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
                    tk.Label(f, text=f"{credits:,.0f}cr", bg=self.window["bg"], fg=ACCENT_BLUE, font=("Segoe UI", 12, "bold")).pack(side=tk.RIGHT, padx=5)
                
                items = p_data.get("looted_items", [])
                if items:
                    tk.Label(self.list_container, text="RECENT ITEMS", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
                    # Show items in reverse order (most recent first)
                    for item in reversed(items):
                        f = tk.Frame(self.list_container, bg=self.window["bg"]); f.pack(fill=tk.X, pady=1)
                        tk.Label(f, text=item, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=15)
                
                if not credits and not items:
                    tk.Label(self.list_container, text="No detailed loot data", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                return

            targets = p_data.get("targets", {})

        # Regular Leaderboard View
        cat = getattr(self.app, 'leaderboard_cat', 'damage')
        data_list = []
        if cat in ["damage", "healing"]:
            for name, data in self.app.player_data.items():
                val = data.get(cat, 0)
                if val > 0: data_list.append((name, val))
        elif cat == "loot":
            for name, data in self.app.player_data.items():
                val = data.get("total_credits", 0)
                if val > 0: data_list.append((name, val))
            # If no credits yet, fall back to loot count to show something
            if not data_list:
                for name, data in self.app.player_data.items():
                    val = data.get("lb_loot", 0)
                    if val > 0: data_list.append((name, val))

        sorted_list = sorted(data_list, key=lambda x: x[1], reverse=True)
        
        # Merge web data if available
        merged_data = {name: val for name, val in sorted_list}
        if self.app.enable_sync.get() and self.app.sync_data:
            remote_data = self.app.sync_data.get("data", {}).get(cat, {})
            seen_recently = set(self.app.locally_seen_players.keys())
            for remote_name, remote_val in remote_data.items():
                if remote_name == self.app.char_name.get(): continue
                if cat in ["damage", "healing"] and remote_name not in seen_recently: continue
                if cat == "loot":
                    count = len(remote_val) if isinstance(remote_val, list) else remote_val
                    merged_data[remote_name] = max(merged_data.get(remote_name, 0), count)
                else:
                    merged_data[remote_name] = max(merged_data.get(remote_name, 0), remote_val)

        final_list = sorted(merged_data.items(), key=lambda x: x[1], reverse=True)

        if not final_list:
            tk.Label(self.list_container, text=f"No {cat} data", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            return

        for i, (name, val) in enumerate(final_list[:100]): # Limit to top 100
            f = tk.Frame(self.list_container, bg=self.window["bg"]); f.pack(fill=tk.X, pady=2)
            f.config(cursor="hand2")
            f.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
            
            is_boss = name.lower() in self.app.bosses
            
            color = ACCENT_BLUE if name == "You" or name == self.app.char_name.get() else TEXT_PRIMARY
            
            tk.Label(f, text=f"#{i+1}", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
            
            if is_boss:
                p_lbl = tk.Label(f, text=name, bg=self.window["bg"], fg="#ff4444", font=("Segoe UI", 9, "bold"))
                p_lbl.pack(side=tk.LEFT, padx=10)
                p_lbl.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
            else:
                name_container = tk.Frame(f, bg=self.window["bg"])
                name_container.pack(side=tk.LEFT, padx=10)
                labels = create_rainbow_name(name_container, self.app, name, color, ("Segoe UI", 9, "bold"), self.window["bg"])
                for l in labels:
                    l.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
                name_container.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
            
            if is_boss:
                tk.Label(f, text="☠", bg=self.window["bg"], fg="#ff4444", font=("Segoe UI", 11)).pack(side=tk.LEFT)

            if cat == "loot" and "total_credits" in self.app.player_data.get(name, {}):
                val_str = f"{val:,.0f}cr"
            else:
                val_str = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
            
            v_lbl = tk.Label(f, text=val_str, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9))
            v_lbl.pack(side=tk.RIGHT, padx=5)
            v_lbl.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
