import tkinter as tk
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)

class AlexaWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Alexa", "AlexaWindow", 300, 270, fixed_size=False)
        self.view_state = "main" # "main", "geocodes", "ghettosmith"
        self.weapon_values = {}
        self.load_weapon_values()

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

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        # Clear container
        for widget in self.content_container.winfo_children():
            widget.destroy()

        if self.view_state == "main":
            self.show_main_view()
        elif self.view_state == "geocodes":
            self.show_geocodes_view()
        elif self.view_state == "ghettosmith":
            self.show_ghettosmith_view()

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
            "pady": 12,
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

    def show_geocodes_view(self):
        # Back button
        back_btn = tk.Label(self.content_container, text="← BACK", bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                          font=("Segoe UI", 9, "bold"), padx=10, pady=5, cursor="hand2")
        back_btn.pack(anchor="w", pady=(0, 5))
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))

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
        # Back button
        back_btn = tk.Label(self.content_container, text="← BACK", bg=PANEL_DARK, fg=TEXT_SECONDARY, 
                          font=("Segoe UI", 9, "bold"), padx=10, pady=5, cursor="hand2")
        back_btn.pack(anchor="w", pady=(0, 5))
        back_btn.bind("<Button-1>", lambda e: self.switch_view("main"))
        back_btn.bind("<Enter>", lambda e: back_btn.config(fg=TEXT_PRIMARY))
        back_btn.bind("<Leave>", lambda e: back_btn.config(fg=TEXT_SECONDARY))

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

    def switch_view(self, state):
        self.view_state = state
        self.refresh(force=True)
