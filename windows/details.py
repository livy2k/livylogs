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

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_details_manual())

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        do_full = force or (now - self.last_full_refresh >= 1.0)

        # Use persistent container to reduce flicker
        if not hasattr(self, 'txt'):
            for widget in self.content_container.winfo_children(): widget.destroy()

            # Selection area
            sel = tk.Frame(self.content_container, bg=PANEL_DARK, pady=5); sel.pack(fill=tk.X, pady=(0, 5))
            tk.Label(sel, text="PLAYER:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)
            
            self.p_sel = ttk.Combobox(sel, state="readonly", width=20)
            self.p_sel.pack(side=tk.LEFT, padx=5)
            self.p_sel.bind("<<ComboboxSelected>>", lambda e: self.on_player_change(self.p_sel.get()))

            # Filter Tabs (All, Dealt, Taken)
            t_frame = tk.Frame(self.content_container, bg=PANEL_DARK); t_frame.pack(fill=tk.X, pady=(0, 5))
            self.tab_btns = {}
            
            def make_tab_cmd(v): return lambda e: [setattr(self.app, 'details_tab', v), setattr(self, 'last_full_refresh', 0), self.refresh()]

            for text, val in [("ALL", "all"), ("DEALT", "dealt"), ("TAKEN", "taken")]:
                btn = tk.Label(t_frame, text=text, bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                              font=("Segoe UI", 8, "bold"), padx=10, pady=5, cursor="hand2")
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                btn.bind("<Button-1>", make_tab_cmd(val))
                self.tab_btns[val] = btn

            # Stats area
            s_f = tk.Frame(self.content_container, bg=WINDOW_BG, padx=5); s_f.pack(fill=tk.X, pady=5)
            self.lbl_det_dmg = tk.Label(s_f, text="DAMAGE: 0", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_det_dmg.pack(side=tk.LEFT, padx=(0, 20))
            self.lbl_det_heal = tk.Label(s_f, text="HEALING: 0", bg=WINDOW_BG, fg="#44ff44", font=("Segoe UI", 10, "bold"))
            self.lbl_det_heal.pack(side=tk.LEFT)

            # Log area
            tk.Label(self.content_container, text="RECENT EVENTS:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
            log_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=1, pady=1)
            log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.txt = tk.Text(log_frame, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Consolas", 9), relief=tk.FLAT, borderwidth=0, padx=5, pady=5)
            sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.txt.yview)
            self.txt.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            do_full = True

        # Update Player Selector
        players = sorted(list(self.app.player_data.keys()))
        if not players:
            self.lbl_det_dmg.config(text="DAMAGE: 0")
            self.lbl_det_heal.config(text="HEALING: 0")
            self.txt.config(state=tk.NORMAL)
            self.txt.delete("1.0", tk.END)
            self.txt.insert(tk.END, "No combat data available")
            self.txt.config(state=tk.DISABLED)
            return

        current = getattr(self.app, 'current_detail_player', None)
        if not current or current not in players:
            current = "You" if "You" in players else players[0]
            self.app.current_detail_player = current
            
        self.p_sel.config(values=players)
        self.p_sel.set(current)

        # Update Tab Buttons
        tab = getattr(self.app, 'details_tab', 'all')
        for v, btn in self.tab_btns.items():
            active = (v == tab)
            btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)

        if not do_full: return
        self.last_full_refresh = now

        # Update Stats
        stats = self.app.player_data.get(current, {})
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
            # Join and insert for efficiency
            content = "\n".join(l["text"] for l in reversed(filtered_logs[-200:]))
            self.txt.insert(tk.END, content)
        self.txt.config(state=tk.DISABLED)

    def on_player_change(self, player):
        self.app.current_detail_player = player
        self.refresh()
