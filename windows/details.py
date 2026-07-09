import tkinter as tk
import time
from tkinter import ttk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, TEXT_ACCENT
)
from windows.base_window import BasePopoutWindow

class DetailsWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Details", "DetailsWindow", 400, 500)
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
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_details_manual())

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
        
        do_full = force or (now - self.last_full_refresh >= 1.0)

        # Use persistent container to reduce flicker
        if not hasattr(self, 'scroll_canvas'):
            for widget in self.content_container.winfo_children(): widget.destroy()

            self.top_view = tk.Frame(self.content_container, bg=WINDOW_BG)
            
            # Scrollable area for top-level player list
            self.scroll_canvas = tk.Canvas(self.top_view, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.top_view, orient="vertical", command=self.scroll_canvas.yview)
            self.player_list_frame = tk.Frame(self.scroll_canvas, bg=WINDOW_BG)
            self.player_list_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
            self.scroll_canvas.create_window((0, 0), window=self.player_list_frame, anchor="nw")
            self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
            
            self.scroll_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Drill-down view
            self.detail_view = tk.Frame(self.content_container, bg=WINDOW_BG)
            
            # Filter Tabs (All, Dealt, Taken)
            t_frame = tk.Frame(self.detail_view, bg=PANEL_DARK); t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'details_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("ALL", "all"), ("DEALT", "dealt"), ("TAKEN", "taken")]:
                btn = tk.Label(t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 8, "bold"), padx=10, pady=5, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_tab_cmd(val))
                self.tab_btns[val] = btn

            # Stats area
            s_f = tk.Frame(self.detail_view, bg=WINDOW_BG, padx=5); s_f.pack(fill=tk.X, pady=5)
            self.lbl_det_dmg = tk.Label(s_f, text="DAMAGE: 0", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_det_dmg.pack(side=tk.LEFT, padx=(0, 20))
            self.lbl_det_heal = tk.Label(s_f, text="HEALING: 0", bg=WINDOW_BG, fg="#44ff44", font=("Segoe UI", 10, "bold"))
            self.lbl_det_heal.pack(side=tk.LEFT)

            # Log area
            tk.Label(self.detail_view, text="RECENT EVENTS:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
            log_frame = tk.Frame(self.detail_view, bg=PANEL_DARK, padx=1, pady=1)
            log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.txt = tk.Text(log_frame, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Consolas", 9), relief=tk.FLAT, borderwidth=0, padx=5, pady=5)
            sb_txt = ttk.Scrollbar(log_frame, orient="vertical", command=self.txt.yview)
            self.txt.configure(yscrollcommand=sb_txt.set)
            sb_txt.pack(side=tk.RIGHT, fill=tk.Y)
            self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            do_full = True

        if self.drill_down_player:
            if hasattr(self, 'back_btn'): self.back_btn.pack(side=tk.LEFT, before=self.title_label)
            self.top_view.pack_forget()
            self.detail_view.pack(fill=tk.BOTH, expand=True)
        else:
            if hasattr(self, 'back_btn'): self.back_btn.pack_forget()
            self.detail_view.pack_forget()
            self.top_view.pack(fill=tk.BOTH, expand=True)

        if not do_full: return
        self.last_full_refresh = now

        if not self.drill_down_player:
            # Refresh player list
            for widget in self.player_list_frame.winfo_children(): widget.destroy()
            players = sorted(list(self.app.player_data.keys()))
            if not players:
                tk.Label(self.player_list_frame, text="No combat data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            else:
                for p in players:
                    f = tk.Frame(self.player_list_frame, bg=WINDOW_BG, pady=4, cursor="hand2"); f.pack(fill=tk.X)
                    f.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                    color = ACCENT_BLUE if (p == "You" or p == self.app.char_name.get()) else TEXT_ACCENT
                    lbl = tk.Label(f, text=p, bg=WINDOW_BG, fg=color, font=("Segoe UI", 10, "bold"))
                    lbl.pack(side=tk.LEFT, padx=10)
                    lbl.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
            return

        # Drill-down player view
        current = self.drill_down_player
        stats = self.app.player_data.get(current, {})
        
        # Update Tab Buttons
        tab = getattr(self.app, 'details_tab', 'all')
        for v, btn in self.tab_btns.items():
            active = (v == tab)
            btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)

        # Update Stats
        dmg = stats.get('damage', 0)
        heal = stats.get('healing', 0)
        self.lbl_det_dmg.config(text=f"DAMAGE: {dmg:,.0f}")
        self.lbl_det_heal.config(text=f"HEALING: {heal:,.0f}")

        # Update Logs
        logs = stats.get("logs", [])
        filtered_logs = logs
        if tab == 'dealt':
            filtered_logs = [l for l in logs if "Dealt" in l["text"] or "Healed" in l["text"]]
        elif tab == 'taken':
            filtered_logs = [l for l in logs if "Taken" in l["text"]]

        self.txt.config(state=tk.NORMAL)
        self.txt.delete("1.0", tk.END)
        if not filtered_logs:
            self.txt.insert(tk.END, f"No {tab} events for this player.")
        else:
            content = "\n".join(l["text"] for l in reversed(filtered_logs[-200:]))
            self.txt.insert(tk.END, content)
        self.txt.config(state=tk.DISABLED)
