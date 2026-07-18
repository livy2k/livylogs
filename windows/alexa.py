"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
import json
import difflib
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END,
    ACCENT_RED, ACCENT_ORANGE, ENTRY_BG, BORDER_HIGHLIGHT
)
from ai_handler import AIHandler

class AlexaWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Alexa", "AlexaWindow", 300, 270, fixed_size=False)
        self._is_broken = False
        self.view_state = "main" # "main", "geocodes", "ghettosmith", "drops"
        self.weapon_values = {}
        self.load_weapon_values()
        self.last_drops_refresh = 0
        self.search_query = ""
        self.search_active = False
        self.ai_agent = AIHandler(system_prompt=(
            "You are Uncle Recon, a weathered and cynical intelligence operative from the Star Wars Galaxies era. "
            "You provide tactical advice, information on entities (mobs), and schematics. "
            "Your tone is helpful but gruff. Use Star Wars slang occasionally. "
            "If provided with 'Game Data Context', use it to give specific answers about NPCs, drops, or crafting."
        ))
        self.ai_messages = [] # List of (role, text)

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
        if self._is_broken:
            return
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
            elif self.view_state == "radio":
                self.show_radio_view()
            elif self.view_state == "ukn":
                self.show_ukn_view()
            elif self.view_state == "rico":
                self.show_rico_view()
        else:
            # We are in the same view, only update content if needed
            if self.view_state == "drops":
                self.update_drops_content(force=force)
            elif self.view_state == "ghettosmith":
                # Ghettosmith content is static for now, no need to update
                pass
            elif self.view_state == "rico":
                self.update_rico_content(force=force)
            # Geocodes, Main, and UKN are static

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
            "pady": 6,
            "cursor": "hand2",
            "relief": tk.FLAT,
            "highlightthickness": 1,
            "highlightbackground": BORDER_COLOR
        }

        radio_btn = tk.Button(btn_frame, text="RADIO", command=lambda: self.switch_view("radio"), **btn_style)
        radio_btn.pack(fill=tk.X, pady=2)
        radio_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        radio_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

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

        rico_btn = tk.Button(btn_frame, text="UNCLE RECON", command=lambda: self.switch_view("rico"), **btn_style)
        rico_btn.pack(fill=tk.X, pady=2)
        rico_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        rico_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        mitigation_btn = tk.Button(btn_frame, text="MITIGATION", command=self.open_armor_calc, **btn_style)
        mitigation_btn.pack(fill=tk.X, pady=2)
        mitigation_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        mitigation_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        hitmiss_btn = tk.Button(btn_frame, text="COMPAT RES", command=self.open_hitmiss_calc, **btn_style)
        hitmiss_btn.pack(fill=tk.X, pady=2)
        hitmiss_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        hitmiss_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))
        
        # Icon beside label
        try:
            from PIL import Image, ImageTk
            import os
            from utils import get_resource_path
            icon_path = get_resource_path("hitmiss_icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((20, 20), Image.Resampling.LANCZOS)
                self.hitmiss_btn_img = ImageTk.PhotoImage(img)
                self.hitmiss_icon_lbl = tk.Label(hitmiss_btn, image=self.hitmiss_btn_img, bg=PANEL_DARK)
            else:
                self.hitmiss_icon_lbl = tk.Label(hitmiss_btn, text="🎯", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12))
            
            self.hitmiss_icon_lbl.place(relx=0.25, rely=0.5, anchor="center")
            # Update hover colors for icon too
            hitmiss_btn.bind("<Enter>", lambda e: (e.widget.configure(bg=BUTTON_HOVER), self.hitmiss_icon_lbl.configure(bg=BUTTON_HOVER)), add="+")
            hitmiss_btn.bind("<Leave>", lambda e: (e.widget.configure(bg=PANEL_DARK), self.hitmiss_icon_lbl.configure(bg=PANEL_DARK)), add="+")
        except: pass

        resists_btn = tk.Button(btn_frame, text="CM", command=self.open_resists_calc, **btn_style)
        resists_btn.pack(fill=tk.X, pady=2)
        resists_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        resists_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        calc_btn = tk.Button(btn_frame, text="CALC", command=self.open_calculator, **btn_style)
        calc_btn.pack(fill=tk.X, pady=2)
        calc_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        calc_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

        ukn_btn = tk.Button(btn_frame, text="UKN", command=lambda: self.switch_view("ukn"), **btn_style)
        ukn_btn.pack(fill=tk.X, pady=2)
        ukn_btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
        ukn_btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

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

    def open_hitmiss_calc(self):
        from windows.hit_miss_calc import HitMissCalcWindow
        if not hasattr(self.app, 'hitmiss_win') or not self.app.hitmiss_win:
            self.app.hitmiss_win = HitMissCalcWindow(self.app)
        self.app.hitmiss_win.show()

    def open_resists_calc(self):
        from windows.resists_calc import ResistsCalcWindow
        if not hasattr(self.app, 'resists_win') or not self.app.resists_win:
            self.app.resists_win = ResistsCalcWindow(self.app)
        self.app.resists_win.show()

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

    def show_rico_view(self):
        # Trigger AI model loading immediately when opening the view
        if self.ai_agent and hasattr(self.ai_agent, 'local_model') and not self.ai_agent.local_model and not self.ai_agent.is_loading_local:
            self.ai_agent._load_local_model()

        # Clear existing view
        for widget in self.content_container.winfo_children(): widget.destroy()
        
        # Google-esque Clean Layout
        top_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=10)
        top_frame.pack(fill=tk.X)
        
        # Simple Back Arrow
        back_btn = tk.Label(top_frame, text="←", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), cursor="hand2")
        back_btn.pack(side=tk.LEFT, padx=15)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))

        # Title / Mode Label
        self.rico_title_label = tk.Label(top_frame, text="UNCLE RICO SEARCH", bg=PANEL_DARK, fg=ACCENT_RED, font=("Lilita One", 10))
        self.rico_title_label.pack(side=tk.LEFT)

        # Mute Button
        self.mute_btn = tk.Label(top_frame, text="🔇" if getattr(self, '_is_muted', False) else "🔊", 
                               bg=PANEL_DARK, fg=ACCENT_RED if getattr(self, '_is_muted', False) else TEXT_SECONDARY, 
                               font=("Segoe UI", 12), cursor="hand2")
        self.mute_btn.pack(side=tk.RIGHT, padx=15)
        
        def toggle_mute(e):
            self._is_muted = not getattr(self, '_is_muted', False)
            if self._is_muted:
                self.mute_btn.config(text="🔇", fg=ACCENT_RED)
                if hasattr(self.app, 'radio_mgr'):
                    self.app.radio_mgr.stop()
            else:
                self.mute_btn.config(text="🔊", fg=TEXT_SECONDARY)
        
        self.mute_btn.bind("<Button-1>", toggle_mute)
        self.mute_btn.bind("<Enter>", lambda e: self.mute_btn.config(fg=TEXT_PRIMARY if not getattr(self, '_is_muted', False) else "#ff6666"))
        self.mute_btn.bind("<Leave>", lambda e: self.mute_btn.config(fg=TEXT_SECONDARY if not getattr(self, '_is_muted', False) else ACCENT_RED))

        # Main Interaction Area
        main_area = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_area.pack(fill=tk.BOTH, expand=True)

        # Results area (Scrollable)
        container = tk.Frame(main_area, bg=WINDOW_BG)
        container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        canvas = tk.Canvas(container, bg=WINDOW_BG, highlightthickness=0, bd=0)
        self.rico_canvas = canvas # Store for autoscroll
        
        # Themed Scrollbar Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Rico.Vertical.TScrollbar", 
                        gripcount=0,
                        background=PANEL_DARK, 
                        troughcolor=WINDOW_BG, 
                        bordercolor=BORDER_COLOR, 
                        arrowcolor=ACCENT_RED,
                        lightcolor=PANEL_DARK,
                        darkcolor=PANEL_DARK,
                        width=10) # Thinner scrollbar
        style.map("Rico.Vertical.TScrollbar",
                  background=[('active', BORDER_HIGHLIGHT), ('pressed', ACCENT_RED)])

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview, style="Rico.Vertical.TScrollbar")
        # Use a consistent inner background
        scroll_frame = tk.Frame(canvas, bg=WINDOW_BG)
        self.rico_scroll_frame = scroll_frame

        def _on_scroll_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frame.bind("<Configure>", _on_scroll_frame_configure)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", tags="frame")
        
        def _on_canvas_configure(e):
             canvas.itemconfig("frame", width=e.width)
             # Update wraplengths for all labels in bubbles
             for widget in scroll_frame.winfo_children():
                 if isinstance(widget, tk.Frame): # Bubble container
                     for sub in widget.winfo_children():
                         if isinstance(sub, tk.Frame): # Bubble
                             for label in sub.winfo_children():
                                 if isinstance(label, tk.Label):
                                     label.config(wraplength=max(100, e.width - 120)) 
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        scroll_frame.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Chat Input Box for Rico (Bottom anchored)
        input_container = tk.Frame(main_area, bg=PANEL_DARK, pady=15, padx=20)
        input_container.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Search-bar style entry with rounded-look corners (via border)
        entry_outer = tk.Frame(input_container, bg=BORDER_COLOR, padx=1, pady=1)
        entry_outer.pack(fill=tk.X)
        
        entry_frame = tk.Frame(entry_outer, bg=ENTRY_BG)
        entry_frame.pack(fill=tk.X)
        
        rico_input = tk.Entry(entry_frame, bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=ACCENT_RED,
                             font=("Segoe UI", 11), borderwidth=0, highlightthickness=0)
        rico_input.pack(fill=tk.X, side=tk.LEFT, padx=15, pady=8, expand=True)
        rico_input.focus_set()
        
        def handle_paste(event):
            try:
                text = self.window.clipboard_get()
                if text:
                    # Truncate if too long to avoid crash
                    if len(text) > 1000: text = text[:1000]
                    rico_input.insert(tk.INSERT, text)
            except: pass
            return "break"
        
        rico_input.bind("<Control-v>", handle_paste)
        rico_input.bind("<Control-V>", handle_paste)
        
        # AI Status Bar
        self.ai_status_label = tk.Label(input_container, text="● Archives Active (Pseudo-AI)", bg=PANEL_DARK, fg="#00ff00", font=("Segoe UI", 8, "bold"))
        self.ai_status_label.pack(fill=tk.X, pady=(8, 0))

        def on_rico_submit(e=None):
            val = rico_input.get().strip()
            if val:
                # Protection: Max length 500 chars
                if len(val) > 500:
                    val = val[:500] + "..."
                
                self.ai_messages.append(("user", val))
                # Add a temporary "thinking" message for pulsing effect
                self.ai_messages.append(("rico_thinking", "..."))
                
                rico_input.delete(0, tk.END)
                self.update_rico_content(force=True)
                
                # Async ask: passing context_data=None forces handler to do its own DB lookup in background
                self.ai_agent.ask(val, context_data=None, callback=lambda ans: self.on_ai_response(ans))
        
        rico_input.bind("<Return>", on_rico_submit)
        
        # Hardened Paste Logic
        def handle_paste(event):
            try:
                # Try to get clipboard content
                content = self.window.clipboard_get()
                if not isinstance(content, str):
                    return "break"
                # Protection: Max 1000 chars for paste, strip non-text
                if len(content) > 1000:
                    content = content[:1000]
                # Insert manually to ensure we control the flow
                rico_input.insert(tk.INSERT, content)
                return "break" # Prevent default paste
            except:
                return "break"
        
        rico_input.bind("<<Paste>>", handle_paste)
        rico_input.bind("<Control-v>", handle_paste)

        if not self.ai_messages:
            # Uncle Rico Greeting (Modern Styled)
            greeting_text = self.ai_agent.get_metallica_opening()
            self.ai_messages.append(("assistant", greeting_text))
            self.update_rico_content(force=True)
        else:
            self.update_rico_content(force=True)

    def on_ai_response(self, response):
        # Remove any temporary thinking indicators
        self.ai_messages = [m for m in self.ai_messages if m[0] != "rico_thinking"]
        
        sync_data = None
        if response and "---METALLICA_SYNC---" in response:
            parts = response.split("---METALLICA_SYNC---")
            response = parts[0].strip()
            try:
                sync_data = json.loads(parts[1].strip())
            except: pass

        # Handle "Searching" status
        if response and "[STILL SEARCHING...]" in response:
            # Check if we already have a still searching message to avoid dupes
            if self.ai_messages and "[STILL SEARCHING...]" in self.ai_messages[-1][1]:
                self.ai_messages[-1] = ("assistant", response)
            else:
                self.ai_messages.append(("assistant", response))
            
            if self.view_state == "rico":
                self.window.after(0, lambda: self.update_rico_content(force=True))
            return

        # If we got a real answer, replace the last "searching" message if it exists
        if self.ai_messages and "[STILL SEARCHING...]" in self.ai_messages[-1][1]:
            self.ai_messages[-1] = ("assistant", response)
        else:
            self.ai_messages.append(("assistant", response))
        
        # Display tab if present
        if sync_data and "tab" in sync_data:
            # Check if muted before playing
            is_muted = getattr(self, '_is_muted', False)

            tab_msg = f"\n--- {sync_data['title'].upper()} GUITAR TAB ---\n{sync_data['tab']}"
            self.ai_messages.append(("assistant", tab_msg))
            
            # Start MIDI playback if not muted
            if not is_muted:
                try:
                    import midistyle
                    midistyle.play_tab_midi(sync_data['tab'])
                except Exception as e:
                    print(f"[MIDI] Error triggering playback: {e}")

        if self.view_state == "rico":
            def update():
                self.update_rico_content(force=True)
                # Auto-scroll to bottom
                self.window.after(100, lambda: self.rico_canvas.yview_moveto(1.0))
                # Update status label based on response tag
                if "Imperial Archives" in response:
                    self.ai_status_label.config(text="● Archives Active (Pseudo-AI)", fg="#00ff00")
                elif "Things were better in '82" in response or "Tactical link failure" in response:
                    self.ai_status_label.config(text="● Archives Offline", fg=ACCENT_RED)
                else:
                    self.ai_status_label.config(text="● Archives Active (Pseudo-AI)", fg="#00ff00")
            self.window.after(0, update)

    def update_rico_content(self, force=False):
        if not hasattr(self, 'rico_scroll_frame') or not self.rico_scroll_frame.winfo_exists():
            return
        
        # Only rebuild if forced or if we don't have enough widgets for our messages
        current_widgets = [w for w in self.rico_scroll_frame.winfo_children() if hasattr(w, '_msg_idx')]
        if not force and len(current_widgets) == len(self.ai_messages):
            # Just update the thinking label if it changed, but don't rebuild
            thinking_dots = getattr(self, '_thinking_dots', "...")
            if hasattr(self, '_thinking_label') and self._thinking_label.winfo_exists():
                try:
                    self._thinking_label.config(text=thinking_dots)
                except: pass
            return

        # If we have existing widgets and just need to add the LATEST message:
        if not force and len(current_widgets) > 0 and len(self.ai_messages) == len(current_widgets) + 1:
            self._add_single_message(self.ai_messages[-1], len(self.ai_messages)-1)
            return

        # Fallback to full rebuild for state changes (e.g. view switch, first load)
        for widget in self.rico_scroll_frame.winfo_children(): widget.destroy()

        if not self.ai_messages:
            # Welcome message handling
            greeting_text = self.ai_agent.get_metallica_opening()
            self.ai_messages.append(("assistant", greeting_text))
            self._add_single_message(("assistant", greeting_text), 0)
        else:
            # Spacer at top
            tk.Frame(self.rico_scroll_frame, bg=WINDOW_BG, height=10).pack()
            for i, msg in enumerate(self.ai_messages):
                self._add_single_message(msg, i)
            
            # Spacer at bottom
            tk.Frame(self.rico_scroll_frame, bg=WINDOW_BG, height=20).pack()
        
        if force:
            self.window.after(50, lambda: self.rico_canvas.yview_moveto(1.0))

    def _add_single_message(self, msg, idx):
        role, text = msg
        is_user = role == "user"
        is_thinking = role == "rico_thinking"
        
        canvas_width = self.rico_canvas.winfo_width()
        if canvas_width < 100: canvas_width = 300 # Fallback
        wrap_val = max(100, canvas_width - 120)

        # Container for alignment
        bubble_container = tk.Frame(self.rico_scroll_frame, bg=WINDOW_BG, pady=4) # Reduced pady
        bubble_container.pack(fill=tk.X, padx=20)
        bubble_container._msg_idx = idx # Mark it for tracking
        
        # Consistent Height Role Label to prevent bouncing
        role_frame = tk.Frame(bubble_container, bg=WINDOW_BG, width=80, height=20)
        role_frame.pack_propagate(False)
        role_frame.pack(side=tk.RIGHT if is_user else tk.LEFT, padx=5)

        role_name = "YOU" if is_user else "UNCLE RICO"
        role_label = tk.Label(role_frame, text=role_name, 
                             bg=WINDOW_BG, fg=ACCENT_RED if not is_user else TEXT_SECONDARY, 
                             font=("Lilita One", 8))
        role_label.pack(expand=True)
        
        # Bubble Layout
        bg_color = "#1c1f24" if is_user else PANEL_DARK
        border_color = "#3a3f4b" if is_user else BORDER_COLOR
        
        bubble_outer = tk.Frame(bubble_container, bg=WINDOW_BG)
        bubble_outer.pack(side=tk.RIGHT if is_user else tk.LEFT, fill=tk.X, expand=True)
        
        bubble = tk.Frame(bubble_outer, bg=bg_color, padx=15, pady=10, 
                         highlightthickness=1, highlightbackground=border_color)
        bubble.pack(side=tk.RIGHT if is_user else tk.LEFT)
        
        # Context menu for copying
        def show_context_menu(e, content=text):
            m = tk.Menu(self.window, tearoff=0, bg=PANEL_DARK, fg=TEXT_PRIMARY, activebackground=ACCENT_RED)
            m.add_command(label="COPY MESSAGE", command=lambda: (self.window.clipboard_clear(), self.window.clipboard_append(content)))
            m.post(e.x_root, e.y_root)

        bubble.bind("<Button-3>", show_context_menu)
        
        msg_font = ("Segoe UI", 10) if is_user else ("Consolas", 10)
        msg_fg = TEXT_PRIMARY if is_user else "#aeb7c0"
        
        display_text = text
        if is_thinking:
            display_text = getattr(self, '_thinking_dots', "...")
            self._thinking_label = tk.Label(bubble, text=display_text, bg=bg_color, fg=msg_fg, font=msg_font, 
                                          wraplength=wrap_val, justify="left", anchor="w")
            self._thinking_label.pack()
            if not hasattr(self, '_thinking_anim_id'):
                self._animate_thinking()
        else:
            tk.Label(bubble, text=display_text, bg=bg_color, fg=msg_fg, font=msg_font, 
                     wraplength=wrap_val, justify="left", anchor="w").pack()
        
        # Auto-scroll on new message
        self.window.after(10, lambda: self.rico_canvas.yview_moveto(1.0))

    def _animate_thinking(self):
        if not hasattr(self, '_thinking_dots'): self._thinking_dots = "."
        
        dots = self._thinking_dots
        if dots == ".": self._thinking_dots = ".."
        elif dots == "..": self._thinking_dots = "..."
        else: self._thinking_dots = "."
        
        # Update the thinking label directly if it exists
        if hasattr(self, '_thinking_label') and self._thinking_label.winfo_exists():
            try:
                self._thinking_label.config(text=self._thinking_dots)
            except: pass
        
        # Check if we still have thinking messages
        has_thinking = any(m[0] == "rico_thinking" for m in self.ai_messages)
        if has_thinking and self.view_state == "rico":
            self._thinking_anim_id = self.window.after(500, self._animate_thinking)
        else:
            if hasattr(self, '_thinking_anim_id'):
                self.window.after_cancel(self._thinking_anim_id)
                delattr(self, '_thinking_anim_id')

    def show_radio_view(self):
        # Navigation Row
        nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
        nav_row.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(nav_row, text="RADIO STATIONS", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        back_btn = tk.Label(nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.pack(side=tk.RIGHT)
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))
        
        # Content
        content_frame = tk.Frame(self.content_container, bg=WINDOW_BG, padx=10, pady=5)
        content_frame.pack(fill=tk.BOTH, expand=True)

        from radio_manager import SAFE_RAP_STATIONS
        
        for name in SAFE_RAP_STATIONS.keys():
            btn = tk.Button(content_frame, text=name, bg=PANEL_DARK, fg=TEXT_PRIMARY, 
                            activebackground=BUTTON_HOVER, activeforeground=TEXT_ACCENT,
                            font=("Segoe UI", 9, "bold"), bd=0, pady=5, cursor="hand2",
                            command=lambda n=name: self.app.radio_mgr.play(n))
            btn.pack(fill=tk.X, pady=2)
            btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
            btn.bind("<Leave>", lambda e: e.widget.configure(bg=PANEL_DARK))

    def show_ukn_view(self):
        # Navigation Row
        nav_row = tk.Frame(self.content_container, bg=PANEL_DARK)
        nav_row.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(nav_row, text="LIVIUS KEY (UKN)", bg=PANEL_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        back_btn = tk.Label(nav_row, text="⬆", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=5)
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.pack(side=tk.RIGHT)
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))

        # Scrollable area
        container = tk.Frame(self.content_container, bg=WINDOW_BG)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=WINDOW_BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=WINDOW_BG)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        def _on_canvas_configure(e):
             canvas.itemconfig(1, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Icon Data
        # st_type: (icon, label, color, description)
        ukn_data = [
            ("knockdown", "🎯", "DB", "#FF8800", "Knockdown (Scope Target)"),
            ("posture", "🧎", "PD", "#00FFFF", "Posture Change (Kneeling)"),
            ("intimidate", "!!!", "Int", "#FF00FF", "Intimidate"),
            ("poison", "🧪", "DOT", "#00FF00", "Poison Hits (Beaker)"),
            ("incap", "🥴", "inc", "#FF0000", "Incapacitated (:s face)"),
            ("death", "💀", "", "#888888", "Dead (Grey Name)"),
            ("top_dps", "🏋️", "MVP", "#00FFFF", "Top DPS (MVP - Scales up)"),
            ("top_tank", "🐑", "Tank", "#FFFFFF", "Top Tank (Sheep - Scales up)"),
            ("top_healing", "✚", "ems", "#00FF00", "Top Healing (EMS - Scales up)"),
            ("kills", "🏋️", "KB", "#FFFF00", "PvP Killing Blows"),
        ]

        for st_type, icon, label, col, desc in ukn_data:
            f = tk.Frame(scroll_frame, bg=PANEL_DARK, pady=5, highlightthickness=1, highlightbackground=BORDER_COLOR)
            f.pack(fill=tk.X, pady=2, padx=5)
            
            # Icon Preview (Canvas style to match LIVIUS)
            icon_canvas = tk.Canvas(f, bg=PANEL_DARK, width=40, height=40, highlightthickness=0)
            icon_canvas.pack(side=tk.LEFT, padx=10)
            
            cx, cy = 20, 20
            icon_canvas.create_text(cx, cy, text=icon, font=("Segoe UI Emoji", 18), fill="white")
            if label:
                for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                    icon_canvas.create_text(cx+dx, cy+dy, text=label, font=("Arial", 8, "bold"), fill="black")
                icon_canvas.create_text(cx, cy, text=label, font=("Arial", 8, "bold"), fill=col)
            
            # Description
            info_frame = tk.Frame(f, bg=PANEL_DARK)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            tk.Label(info_frame, text=desc, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            if label:
                tk.Label(info_frame, text=f"Label: {label}", bg=PANEL_DARK, fg=col, font=("Consolas", 8)).pack(anchor="w")

    def save_config(self):
        """Save window position/size to app config. Safe to call even if window is not open."""
        if not self.window or not self.window.winfo_exists():
            return
        try:
            if self.config_key not in self.app.config:
                self.app.config[self.config_key] = {}
            self.app.config[self.config_key].update({
                "width": str(self.window.winfo_width()),
                "height": str(self.window.winfo_height()),
                "x": str(self.window.winfo_x()),
                "y": str(self.window.winfo_y())
            })
        except:
            pass

    def close(self):
        self._is_broken = False
        super().close()

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
