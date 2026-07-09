import tkinter as tk
import time
from datetime import datetime
from constants import (
    PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, WINDOW_BG
)
from windows.base_window import BasePopoutWindow

class LeaderboardWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Leaderboard", "LeaderboardWindow", 300, 400)
        self.drill_down_player = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
        self.back_btn.pack(side=tk.LEFT, before=self.title_label)
        self.back_btn.bind("<Button-1>", lambda e: self.go_back())
        self.back_btn.pack_forget()

        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_leaderboard_manual())

    def go_back(self):
        self.drill_down_player = None
        if hasattr(self, 'back_btn'): self.back_btn.pack_forget()
        self.refresh(force=True)

    def drill_down(self, player):
        self.drill_down_player = player
        if hasattr(self, 'back_btn'): self.back_btn.pack(side=tk.LEFT, before=self.title_label)
        self.refresh(force=True)

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
            from tkinter import ttk
            canvas = tk.Canvas(self.content_container, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
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
            if hasattr(self, 'back_btn'): self.back_btn.pack(side=tk.LEFT, before=self.title_label)
            self.c_frame.pack_forget()
            self.lbl_rank.config(text="TARGET")
            self.lbl_player.pack_forget()
            self.lbl_cat_head.config(text="AMOUNT")
        else:
            if hasattr(self, 'back_btn'): self.back_btn.pack_forget()
            self.c_frame.pack(fill=tk.X, pady=(0, 5), before=self.h_frame)
            self.lbl_rank.config(text="RANK")
            self.lbl_player.pack(side=tk.LEFT, padx=20, before=self.lbl_cat_head)
            
            # Update Category Buttons
            cat = getattr(self.app, 'leaderboard_cat', 'damage')
            for v, btn in self.cat_btns.items():
                active = (v == cat)
                btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
            self.lbl_cat_head.config(text=cat.upper())

        if not do_full: return
        self.last_full_refresh = now

        # Rebuild only the list part
        for widget in self.list_container.winfo_children(): widget.destroy()

        if self.drill_down_player:
            p_data = self.app.player_data.get(self.drill_down_player, {})
            targets = p_data.get("targets", {})
            cat = getattr(self.app, 'leaderboard_cat', 'damage')
            
            drill_list = []
            for t_name, t_vals in targets.items():
                val = t_vals.get(cat, 0)
                if val > 0: drill_list.append((t_name, val))
            
            sorted_drill = sorted(drill_list, key=lambda x: x[1], reverse=True)
            
            if not sorted_drill:
                tk.Label(self.list_container, text=f"No {cat} breakdown for {self.drill_down_player}", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                return

            for name, val in sorted_drill:
                f = tk.Frame(self.list_container, bg=self.window["bg"]); f.pack(fill=tk.X, pady=2)
                tk.Label(f, text=name, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
                val_str = f"{val:,.0f}"
                tk.Label(f, text=val_str, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=5)
            return

        # Regular Leaderboard View
        cat = getattr(self.app, 'leaderboard_cat', 'damage')
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
            
            color = ACCENT_BLUE if name == "You" or name == self.app.char_name.get() else TEXT_PRIMARY
            tk.Label(f, text=f"#{i+1}", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
            
            p_lbl = tk.Label(f, text=name, bg=self.window["bg"], fg=color, font=("Segoe UI", 9, "bold"))
            p_lbl.pack(side=tk.LEFT, padx=10)
            p_lbl.bind("<Button-1>", lambda e, n=name: self.drill_down(n))

            val_str = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
            v_lbl = tk.Label(f, text=val_str, bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 9))
            v_lbl.pack(side=tk.RIGHT, padx=5)
            v_lbl.bind("<Button-1>", lambda e, n=name: self.drill_down(n))
