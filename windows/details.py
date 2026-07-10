import tkinter as tk
from tkinter import ttk
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

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return

        # Restore title label position
        if hasattr(self, 'title_label') and self.title_label.winfo_exists():
            try:
                self.title_bar.coords(self.title_bar.find_withtag(self.title_label), 10, 16)
            except: pass
        
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Determine if we should do a full data calculation
        is_empty = True
        if hasattr(self, 'player_list_frame') and self.player_list_frame.winfo_exists():
            children = self.player_list_frame.winfo_children()
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
        
        # Determine frequency based on state
        if is_empty:
            # Refresh every 200ms if empty to catch first data quickly
            refresh_interval = 0.2
        else:
            # User requested 3s refresh for secondary windows to help performance
            refresh_interval = 3.0

        do_full = force or is_empty or (now - self.last_full_refresh >= refresh_interval)

        # Use persistent container to reduce flicker
        if not hasattr(self, 'scroll_canvas'):
            for widget in self.content_container.winfo_children(): widget.destroy()

            # Navigation Row (Below title bar, contains icons and player name in drilldown)
            self.nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
            self.nav_row.pack(fill=tk.X)
            self.nav_row.pack_forget() # Hidden initially

            self.nav_player_label = tk.Label(self.nav_row, text="", bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Segoe UI", 9, "bold"))
            self.nav_player_label.pack(side=tk.LEFT, padx=10)

            # Navigation Buttons in nav row
            self.back_btn = tk.Label(self.nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2", padx=5)
            self.back_btn.bind("<Button-1>", lambda e: self.go_back())
            self.back_btn.pack(side=tk.RIGHT)
            
            self.top_btn = tk.Label(self.nav_row, text="↩", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2", padx=5)
            self.top_btn.bind("<Button-1>", lambda e: self.go_to_top())
            self.top_btn.pack(side=tk.RIGHT)

            self.top_view = tk.Frame(self.content_container, bg=WINDOW_BG)
            
            # Header
            h_frame = tk.Frame(self.top_view, bg=PANEL_DARK); h_frame.pack(fill=tk.X, pady=(0, 5))
            tk.Label(h_frame, text="PLAYER", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=5)

            # Scrollable area
            self.scroll_canvas = tk.Canvas(self.top_view, bg=WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.top_view, orient="vertical", command=self.scroll_canvas.yview)
            self.player_list_frame = tk.Frame(self.scroll_canvas, bg=WINDOW_BG)

            self.player_list_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
            self.scroll_canvas.create_window((0, 0), window=self.player_list_frame, anchor="nw")
            
            def _on_canvas_configure(e):
                self.scroll_canvas.itemconfig(1, width=e.width)
            self.scroll_canvas.bind("<Configure>", _on_canvas_configure)

            self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
            
            def _on_mousewheel(event):
                if not self.window: return
                self.scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            self.window.bind("<MouseWheel>", _on_mousewheel)
            self.player_list_frame.bind("<MouseWheel>", _on_mousewheel)
            self.scroll_canvas.bind("<MouseWheel>", _on_mousewheel)

            self.scroll_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            do_full = True

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
            
            def _on_txt_mousewheel(event):
                self.txt.yview_scroll(int(-1*(event.delta/120)), "units")
            self.txt.bind("<MouseWheel>", _on_txt_mousewheel)
            
            sb_txt.pack(side=tk.RIGHT, fill=tk.Y)
            self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            do_full = True

        # Update Title and Navigation Buttons
        is_drill = getattr(self, 'is_drilldown', False)
        if is_drill:
            if hasattr(self, 'nav_row') and self.nav_row.winfo_exists():
                if hasattr(self, 'top_view') and self.top_view.winfo_exists() and self.top_view.winfo_ismapped():
                    self.nav_row.pack(fill=tk.X, before=self.top_view)
                elif hasattr(self, 'detail_view') and self.detail_view.winfo_exists() and self.detail_view.winfo_ismapped():
                    self.nav_row.pack(fill=tk.X, before=self.detail_view)
                else:
                    self.nav_row.pack(fill=tk.X)
                p_name = getattr(self, 'selected_player', 'PLAYER')
                ctx_text = p_name.upper()
                is_you = ctx_text == "YOU" or ctx_text == self.app.char_name.get().upper()
                self.nav_player_label.config(text=ctx_text, fg="#00ffff" if is_you else TEXT_ACCENT)

            try: self.title_bar.itemconfig(self.title_label, text="DETAILS")
            except: pass
        else:
            if hasattr(self, 'nav_row'):
                self.nav_row.pack_forget()
            try: self.title_bar.itemconfig(self.title_label, text="Details")
            except: pass

        # Player List View
        players = sorted(list(self.app.player_data.keys()))
        current_widgets = self.player_list_frame.winfo_children()

        if is_drill:
            if hasattr(self, 'top_view'): self.top_view.pack_forget()
            if hasattr(self, 'detail_view'): self.detail_view.pack(fill=tk.BOTH, expand=True)
        else:
            if hasattr(self, 'detail_view'): self.detail_view.pack_forget()
            if hasattr(self, 'top_view') and self.top_view.winfo_exists():
                self.top_view.pack(fill=tk.BOTH, expand=True)

        if not do_full: return
        self.last_full_refresh = now

        # Surgical update for top player list
        last_players = getattr(self, '_last_players', [])
        
        # If transitioning to empty, show "No combat data" immediately
        if not players:
            if last_players: # Only clear if we actually had players before
                for widget in current_widgets: widget.destroy()
                tk.Label(self.player_list_frame, text="No combat data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                self._last_players = []
                self._row_frames = {}
            elif not current_widgets: # First time setup
                tk.Label(self.player_list_frame, text="No combat data", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
                self._last_players = []
                self._row_frames = {}
            return

        if not hasattr(self, '_row_frames'): self._row_frames = {}

        if len(self._row_frames) != len(players) or force:
            for widget in current_widgets: widget.destroy()
            self._last_players = players
            self._row_frames = {}
            for p in players:
                f = tk.Frame(self.player_list_frame, bg=WINDOW_BG); f.pack(fill=tk.X, pady=1)
                self._row_frames[p] = f
                
                is_you = p == "You" or p == self.app.char_name.get()
                color = "#00ffff" if is_you else TEXT_PRIMARY
                create_rainbow_name(f, self.app, p, color, ("Segoe UI", 9, "bold"), WINDOW_BG)
                f.bind("<Button-1>", lambda e, p=p: self.drill_down(p))
                for child in f.winfo_children():
                    child.bind("<Button-1>", lambda e, p=p: self.drill_down(p))
        else:
            # Reorder existing frames
            for p in players:
                if p in self._row_frames:
                    f = self._row_frames[p]
                    f.pack_forget()
                    f.pack(fill=tk.X, pady=1)
                else:
                    self.refresh(force=True)
                    return

        # Refresh Drill-down view if active
        if is_drill:
            p = getattr(self, 'selected_player', '')
            tab = getattr(self.app, 'details_tab', 'all')
            
            # Update Tab Buttons
            if hasattr(self, 'tab_btns'):
                for v, btn in self.tab_btns.items():
                    try:
                        active = (v == tab)
                        btn.config(bg=ACCENT_BLUE if active else PANEL_DARK, fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
                    except: pass

            data = self.app.player_data.get(p, {})
            
            # Show Player Name prominently
            if not hasattr(self, 'player_header'):
                self.player_header = tk.Label(self.detail_view, text="", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold"))
                self.player_header.pack(side=tk.TOP, anchor="w", padx=10, pady=(10, 5))
            
            self.player_header.config(text=f"COMBAT LOG: {p.upper()}", fg="#00ffff" if (p == "You" or p == self.app.char_name.get()) else ACCENT_BLUE)

            self.lbl_det_dmg.config(text=f"DAMAGE: {data.get('damage', 0):,}")
            self.lbl_det_heal.config(text=f"HEALING: {data.get('healing', 0):,}")

            log_key = f"log_{p}_{tab}_{len(data.get('log', []))}"
            if not force and hasattr(self, '_last_log_key') and self._last_log_key == log_key:
                return
            self._last_log_key = log_key

            events = data.get('log', [])
            if tab != "all":
                events = [e for e in events if e.get('type') == tab]
            
            self.txt.config(state=tk.NORMAL)
            self.txt.delete("1.0", tk.END)
            for e in events[-100:]:
                self.txt.insert(tk.END, f"[{e.get('time', '')}] {e.get('msg', '')}\n")
            self.txt.see(tk.END)
            self.txt.config(state=tk.DISABLED)

        return

    def drill_down(self, player):
        self.is_drilldown = True
        self.selected_player = player
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_to_top(self):
        self.is_drilldown = False
        self.last_full_refresh = 0
        self.refresh(force=True)

    def go_back(self):
        self.go_to_top()
