import tkinter as tk
from tkinter import ttk
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class AlexaWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Alexa", "AlexaWindow", 300, 270, fixed_size=False)
        self.view_state = "main" # "main", "geocodes", "ghettosmith", "drops"
        self.weapon_values = {}
        self.load_weapon_values()
        self.last_drops_refresh = 0
        self.search_query = ""
        self.search_active = False

    def load_weapon_values(self):
        import os
        from utils import get_resource_path
        path = get_resource_path(os.path.join("filters", "ghettosmith.txt"))
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            name = " ".join(parts[:-1]).lower()
                            try:
                                val = float(parts[-1])
                                self.weapon_values[name] = val
                            except: pass
            except: pass

    def show(self, force_open=False):
        super().show(force_open)
        # Ensure view state is initialized when window is first shown
        self._last_view_state = None 
        self.refresh(force=True)

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return

        # Restore title label position and search elements
        w = self.title_bar.winfo_width()
        h = self.title_bar.winfo_height()
        
        if not hasattr(self, 'search_btn'):
            self.search_btn = tk.Label(self.title_bar, text="🔍", bg=TITLE_GRADIENT_END, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
            self.search_btn.bind("<Button-1>", lambda e: self.toggle_search())
            self.search_btn.bind("<Enter>", lambda e: self.search_btn.config(fg=TEXT_PRIMARY))
            self.search_btn.bind("<Leave>", lambda e: self.search_btn.config(fg=TEXT_SECONDARY))
            self.title_bar.create_window(w - 35, h // 2, window=self.search_btn, anchor="e", tags="search_btn")

            self.search_entry = tk.Entry(self.title_bar, bg=PANEL_DARK, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, 
                                        font=("Segoe UI", 9), bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
            self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_change())
            self.search_entry_window = self.title_bar.create_window(w - 60, h // 2, window=self.search_entry, anchor="e", width=120, state="hidden", tags="search_entry")
        else:
            self.title_bar.coords("search_btn", w - 35, h // 2)
            self.title_bar.coords("search_entry", w - 60, h // 2)

        # Only throttle drops view
        import time
        now = time.time()
        if self.view_state == "drops" and not force:
            if now - self.last_drops_refresh < 15:
                return
        
        if self.view_state == "drops":
            self.last_drops_refresh = now

        # View switching logic using persistent containers where possible
        if not hasattr(self, '_last_view_state') or self._last_view_state != self.view_state:
            for widget in self.content_container.winfo_children():
                widget.destroy()
            self._last_view_state = self.view_state
            
            # Reset row trackers for new view
            self._row_frames = {}
            self._row_widgets = {}
            
            if self.view_state == "main":
                self.show_main_view()
            elif self.view_state == "geocodes":
                self.show_geocodes_view()
            elif self.view_state == "ghettosmith":
                self.show_ghettosmith_view()
            elif self.view_state == "drops":
                self.show_drops_view()
        else:
            # We are in the same view, only update content if needed
            if self.view_state == "drops":
                self.update_drops_content(force=force)
            elif self.view_state == "ghettosmith":
                # Ghettosmith content is static for now, no need to update
                pass
            # Geocodes and Main are static

    def update_drops_content(self, force=False):
        # We need a reference to the scroll_frame in show_drops_view
        if not hasattr(self, 'drops_scroll_frame') or not self.drops_scroll_frame.winfo_exists():
            return
        
        drops = self.app.permanent_drops
        if not drops:
            return

        query = self.search_query.lower()
        filtered_items = [item for item in drops.keys() if query in item.lower() or any(query in d.lower() for d in drops[item])]
        
        # Key check
        drops_key = f"drops_{len(filtered_items)}_{query}"
        if not force and hasattr(self, '_last_drops_key') and self._last_drops_key == drops_key:
            return
        self._last_drops_key = drops_key

        # Rebuild drops content surgically
        for widget in self.drops_scroll_frame.winfo_children():
            widget.destroy()
        
        if not filtered_items:
            tk.Label(self.drops_scroll_frame, text="No matches found.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20, padx=10)
            return

        for item in sorted(filtered_items):
            f = tk.Frame(self.drops_scroll_frame, bg=WINDOW_BG, pady=4)
            f.pack(fill=tk.X, padx=5)
            
            tk.Label(f, text=item, bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            
            droppers = ", ".join(drops[item])
            if len(droppers) > 30: droppers = droppers[:27] + "..."
            tk.Label(f, text=droppers, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack(side=tk.RIGHT)

    def show_main_view(self):
        btn_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        btn_frame.pack(fill=tk.BOTH, expand=True)

        btn_style = {
            "bg": PANEL_DARK,
            "fg": TEXT_PRIMARY,
            "activebackground": BUTTON_HOVER,
            "activeforeground": TEXT_ACCENT,
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0,
            "pady": 8,
            "cursor": "hand2",
            "relief": tk.FLAT,
            "highlightthickness": 1,
            "highlightbackground": BORDER_COLOR
        }

        geo_btn = tk.Button(btn_frame, text="GEO CODES", command=lambda: self.switch_view("geocodes"), **btn_style)
        geo_btn.pack(fill=tk.X, pady=2)
        geo_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        geo_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        smith_btn = tk.Button(btn_frame, text="GHETTO SMITH", command=lambda: self.switch_view("ghettosmith"), **btn_style)
        smith_btn.pack(fill=tk.X, pady=2)
        smith_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        smith_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        drops_btn = tk.Button(btn_frame, text="DROPS", command=lambda: self.switch_view("drops"), **btn_style)
        drops_btn.pack(fill=tk.X, pady=2)
        drops_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        drops_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        armor_btn = tk.Button(btn_frame, text="ARMOR", command=self.open_armor_calc, **btn_style)
        armor_btn.pack(fill=tk.X, pady=2)
        armor_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        armor_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        calc_btn = tk.Button(btn_frame, text="CALC", command=self.open_calculator, **btn_style)
        calc_btn.pack(fill=tk.X, pady=2)
        calc_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        calc_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

    def open_calculator(self):
        from windows.calculator import CalculatorWindow
        if not hasattr(self.app, 'calc_win') or not self.app.calc_win:
            self.app.calc_win = CalculatorWindow(self.app)
        self.app.calc_win.show()

    def open_armor_calc(self):
        from windows.armor_calc import ArmorCalcWindow
        if not hasattr(self.app, 'armor_win') or not self.app.armor_win:
            self.app.armor_win = ArmorCalcWindow(self.app)
        self.app.armor_win.show()

    def show_geocodes_view(self):
        # Navigation Row
        nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
        nav_row.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(nav_row, text="GEO CODES", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        back_btn = tk.Label(nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.pack(side=tk.RIGHT)
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))
        
        top_btn = tk.Label(nav_row, text="↩", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        top_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        top_btn.pack(side=tk.RIGHT)
        top_btn.bind("<Enter>", lambda e: top_btn.config(fg=TEXT_PRIMARY))
        top_btn.bind("<Leave>", lambda e: top_btn.config(fg=TEXT_SECONDARY))

        # Content - Single column list
        codes = [
            "32281",
            "12872",
            "12753 MERC",
            "86332 SCIENTIST",
            "11380 MUTANT",
            "52577",
            "78660 ACKLAY"
        ]
        
        content_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        for code in codes:
            tk.Label(content_frame, text=code, bg=PANEL_DARK, fg=TEXT_ACCENT, 
                     font=("Consolas", 10, "bold"), anchor="w").pack(fill=tk.X)

    def show_ghettosmith_view(self):
        # Navigation Row
        nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
        nav_row.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(nav_row, text="GHETTO SMITH", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        back_btn = tk.Label(nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.pack(side=tk.RIGHT)
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))
        
        top_btn = tk.Label(nav_row, text="↩", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        top_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        top_btn.pack(side=tk.RIGHT)
        top_btn.bind("<Enter>", lambda e: top_btn.config(fg=TEXT_PRIMARY))
        top_btn.bind("<Leave>", lambda e: top_btn.config(fg=TEXT_SECONDARY))

        list_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        list_frame.pack(fill=tk.BOTH, expand=True)

        all_loot = []
        for p, loots in self.app.loot_data.items():
            for l in loots:
                item_name = l["item"].lower()
                match = next((name for name in self.weapon_values if name in item_name), None)
                if match:
                    all_loot.append({
                        "player": p,
                        "item": l["item"],
                        "value": self.weapon_values[match],
                        "timestamp": l["timestamp"]
                    })
        
        all_loot.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if not all_loot:
            tk.Label(list_frame, text="No items detected yet.", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack(pady=20)
            return

        for entry in all_loot[:10]:
            f = tk.Frame(list_frame, bg=WINDOW_BG, pady=2)
            f.pack(fill=tk.X)
            ts = entry["timestamp"].strftime("%H:%M")
            tk.Label(f, text=f"[{ts}]", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Consolas", 8)).pack(side=tk.LEFT)
            tk.Label(f, text=f" {entry['player'][:8]}:", bg=WINDOW_BG, fg=TEXT_ACCENT, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
            tk.Label(f, text=f" {entry['item']}", bg=WINDOW_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 8), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(f, text=f"{entry['value']}", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT)

    def show_drops_view(self):
        # Navigation Row
        nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
        nav_row.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(nav_row, text="DROPS", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        back_btn = tk.Label(nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.pack(side=tk.RIGHT)
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))
        
        top_btn = tk.Label(nav_row, text="↩", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        top_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        top_btn.pack(side=tk.RIGHT)
        top_btn.bind("<Enter>", lambda e: top_btn.config(fg=TEXT_PRIMARY))
        top_btn.bind("<Leave>", lambda e: top_btn.config(fg=TEXT_SECONDARY))

        # Use a scrollable area if there are many drops
        container = tk.Frame(self.content_container, bg=WINDOW_BG)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=WINDOW_BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=WINDOW_BG)
        self.drops_scroll_frame = scroll_frame # Store for updates

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        # Ensure scroll frame width matches canvas
        def _on_canvas_configure(e):
             canvas.itemconfig(1, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Clean up binding when frame is destroyed
        scroll_frame.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.update_drops_content(force=True)

    def switch_view(self, state):
        self.view_state = state
        self.search_active = False
        self.search_query = ""
        if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            self.search_entry.delete(0, tk.END)
            self.title_bar.itemconfig(self.search_entry_window, state="hidden")
        self._last_view_state = None # Force content rebuild
        try:
            self.app.save_config()
        except: pass
        self.refresh(force=True)

    def toggle_search(self):
        self.search_active = not self.search_active
        if self.search_active:
            self.title_bar.itemconfig(self.search_entry_window, state="normal")
            self.search_entry.focus_set()
        else:
            self.title_bar.itemconfig(self.search_entry_window, state="hidden")
            self.search_query = ""
            if self.search_entry.winfo_exists():
                self.search_entry.delete(0, tk.END)
            self.refresh(force=True)

    def on_search_change(self):
        self.search_query = self.search_entry.get()
        self.refresh(force=True)
