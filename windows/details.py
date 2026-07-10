import tkinter as tk
import time
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, TEXT_ACCENT, COLOR_DEFAULT_CLASS,
    TITLE_GRADIENT_START
)
from utils import create_rainbow_name
from windows.base_window import BasePopoutWindow

class DetailsWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Details", "DetailsWindow", 400, 500)
        self.drill_down_player = None
        self.back_btn = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        self.back_btn = tk.Label(self.title_bar, text=" ← ", bg=TITLE_GRADIENT_START, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
        self.back_btn.bind("<Button-1>", lambda e: self.go_back())

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
        
        do_full = force or (now - self.last_full_refresh >= 1.0)

        # Use persistent container to reduce flicker
        if not hasattr(self, 'scroll_canvas'):
            for widget in self.content_container.winfo_children(): widget.destroy()

            self.top_view = tk.Frame(self.content_container, bg=WINDOW_BG)
            
            # Scrollable area for top-level player list
            self.scroll_canvas = tk.Canvas(self.top_view, bg=WINDOW_BG, highlightthickness=0)
            # scrollbar = ttk.Scrollbar(self.top_view, orient="vertical", command=self.scroll_canvas.yview)
            scrollbar = tk.Scrollbar(self.top_view, orient="vertical", command=self.scroll_canvas.yview, bg=PANEL_DARK, troughcolor=WINDOW_BG, bd=0, highlightthickness=0)
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
            # sb_txt = ttk.Scrollbar(log_frame, orient="vertical", command=self.txt.yview)
            sb_txt = tk.Scrollbar(log_frame, orient="vertical", command=self.txt.yview, bg=PANEL_DARK, troughcolor=WINDOW_BG, bd=0, highlightthickness=0)
            self.txt.configure(yscrollcommand=sb_txt.set)
            sb_txt.pack(side=tk.RIGHT, fill=tk.Y)
            self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            do_full = True

        if self.drill_down_player:
            # Back button handled above
            if hasattr(self, 'top_view') and self.top_view.winfo_exists():
                self.top_view.pack_forget()
            if hasattr(self, 'detail_view') and self.detail_view.winfo_exists():
                self.detail_view.pack(fill=tk.BOTH, expand=True)
        else:
            # Back button hidden above
            if hasattr(self, 'detail_view') and self.detail_view.winfo_exists():
                self.detail_view.pack_forget()
            if hasattr(self, 'top_view') and self.top_view.winfo_exists():
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
                    
                    is_boss = p.lower() in self.app.bosses
                    
                    color = ACCENT_BLUE if (p == "You" or p == self.app.char_name.get()) else TEXT_ACCENT
                    if is_boss:
                        color = "#ff4444" # Red text for bosses
                        lbl = tk.Label(f, text=p, bg=WINDOW_BG, fg=color, font=("Segoe UI", 10, "bold"))
                        lbl.pack(side=tk.LEFT, padx=10)
                        lbl.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                    else:
                        name_container = tk.Frame(f, bg=WINDOW_BG)
                        name_container.pack(side=tk.LEFT, padx=10)
                        labels = create_rainbow_name(name_container, self.app, p, color, ("Segoe UI", 10, "bold"), WINDOW_BG)
                        for l in labels:
                            l.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                        name_container.bind("<Button-1>", lambda e, name=p: self.drill_down(name))
                    
                    if is_boss:
                        tk.Label(f, text="☠", bg=WINDOW_BG, fg="#ff4444", font=("Segoe UI", 12)).pack(side=tk.LEFT)
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
        if hasattr(self, 'lbl_det_dmg') and self.lbl_det_dmg.winfo_exists():
            self.lbl_det_dmg.config(text=f"DAMAGE: {dmg:,.0f}")
        if hasattr(self, 'lbl_det_heal') and self.lbl_det_heal.winfo_exists():
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
