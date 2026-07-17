"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
import re
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class DPSCalcWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "DPS Calculator", "DPSCalcWindow", 400, 650, fixed_size=False)
        self.inputs = {}

    def show(self, force_open=False):
        super().show(force_open)
        if not hasattr(self, 'built') or not self.built:
            self.build_ui()
            self.built = True

    def build_ui(self):
        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG, padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        def create_input(parent, label, key, default="0", options=None, is_bool=False):
            frame = tk.Frame(parent, bg=WINDOW_BG, pady=4)
            frame.pack(fill=tk.X)
            tk.Label(frame, text=label, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            
            if is_bool:
                var = tk.BooleanVar(value=default == "True")
                self.inputs[key] = var
                tk.Checkbutton(frame, variable=var, bg=WINDOW_BG, activebackground=WINDOW_BG, 
                               selectcolor=PANEL_DARK, command=self.calculate).pack(side=tk.RIGHT)
            elif options:
                var = tk.StringVar(value=options[0])
                self.inputs[key] = var
                opt = tk.OptionMenu(frame, var, *options, command=lambda _: self.calculate())
                opt.config(bg=PANEL_DARK, fg=TEXT_PRIMARY, bd=0, highlightthickness=0, font=("Segoe UI", 8))
                opt["menu"].config(bg=PANEL_DARK, fg=TEXT_PRIMARY)
                opt.pack(side=tk.RIGHT)
            else:
                var = tk.StringVar(value=default)
                self.inputs[key] = var
                ent = tk.Entry(frame, textvariable=var, bg=PANEL_DARK, fg=TEXT_ACCENT, 
                               font=("Consolas", 10, "bold"), bd=0, width=8, justify="right")
                ent.pack(side=tk.RIGHT)
                var.trace_add("write", lambda *args: self.calculate())

        # Section: ATTACKER WEAPON
        tk.Label(main_frame, text="ATTACKER WEAPON", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        create_input(main_frame, "Min Damage", "min_dmg", "500")
        create_input(main_frame, "Max Damage", "max_dmg", "1000")
        create_input(main_frame, "Speed (sec)", "speed", "1.5")
        create_input(main_frame, "Damage Type", "dmg_type", options=["Energy", "Kinetic", "Blast", "Stun", "LS", "Heat", "Cold", "Acid", "Elec"])
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Section: DEFENDER STATS
        tk.Label(main_frame, text="DEFENDER PROTECTION", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        create_input(main_frame, "Armor Protection (%)", "armor", "90")
        create_input(main_frame, "Mitigation Level", "mit", options=["None", "Mit 1 (20%)", "Mit 2 (40%)", "Mit 3 (60%)"])
        create_input(main_frame, "PSG Protection (%)", "psg", "0")
        create_input(main_frame, "PSG Active?", "psg_active", "False", is_bool=True)
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Section: ACCURACY (Optional for true DPS)
        tk.Label(main_frame, text="HIT RESOLUTION", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        create_input(main_frame, "Hit Chance (%)", "hit_chance", "100")

        # Results Area
        res_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=15)
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dps_var = tk.StringVar(value="DPS: 0.0")
        tk.Label(res_frame, textvariable=self.dps_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Segoe UI", 14, "bold")).pack()
        
        self.hit_range_var = tk.StringVar(value="Hit: 0 - 0")
        tk.Label(res_frame, textvariable=self.hit_range_var, bg=PANEL_DARK, fg=TEXT_PRIMARY, font=("Consolas", 12, "bold")).pack()
        
        self.summary_var = tk.StringVar(value="")
        tk.Label(res_frame, textvariable=self.summary_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Consolas", 9), justify="left").pack(pady=5)

        self.calculate()

    def calculate(self, *args):
        try:
            # Get Inputs
            min_d = float(self.inputs["min_dmg"].get() or 0)
            max_d = float(self.inputs["max_dmg"].get() or 0)
            speed = float(self.inputs["speed"].get() or 1.0)
            if speed <= 0: speed = 1.0
            
            armor_pct = float(self.inputs["armor"].get() or 0)
            psg_pct = float(self.inputs["psg"].get() or 0)
            psg_active = self.inputs["psg_active"].get()
            hit_pct = float(self.inputs["hit_chance"].get() or 100) / 100.0
            
            mit_str = self.inputs["mit"].get()
            mit_pct = 0
            if "Mit 1" in mit_str: mit_pct = 20
            elif "Mit 2" in mit_str: mit_pct = 40
            elif "Mit 3" in mit_str: mit_pct = 60
            
            dmg_type = self.inputs["dmg_type"].get()
            
            def apply_mitigation(base):
                # 1. Armor
                val = base * (1.0 - (armor_pct / 100.0))
                # 2. PSG (Only for Energy/Kinetic/Blast usually)
                if psg_active and dmg_type in ["Energy", "Kinetic", "Blast"]:
                    val = val * (1.0 - (psg_pct / 100.0))
                # 3. Mitigation
                val = val * (1.0 - (mit_pct / 100.0))
                # hit chance factor
                val = val * hit_pct
                return val

            final_min = apply_mitigation(min_d)
            final_max = apply_mitigation(max_d)
            avg_hit = (final_min + final_max) / 2.0
            dps = avg_hit / speed

            self.dps_var.set(f"EST. DPS: {dps:,.1f}")
            self.hit_range_var.set(f"Final Hit: {int(final_min)} - {int(final_max)}")
            
            summary = f"Avg Hit: {avg_hit:,.1f}\n"
            summary += f"Reduction: {int((1 - (avg_hit / ((min_d+max_d)/2.0 if (min_d+max_d)>0 else 1))) * 100)}%\n"
            if psg_active: summary += f"PSG Applied: {psg_pct}%\n"
            
            self.summary_var.set(summary)
            
        except Exception as e:
            self.dps_var.set("Input Error")

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        if self.window.attributes("-alpha") != self.app.current_alpha:
            self.window.attributes("-alpha", self.app.current_alpha)
        if hasattr(self, 'built'):
            self.calculate()
