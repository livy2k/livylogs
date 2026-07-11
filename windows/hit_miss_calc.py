"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
import random
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class HitMissCalcWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Combat Resolution Calculator", "HitMissCalcWindow", 450, 850, fixed_size=True)
        self.inputs = {}
        self.built = False
        self.icon_image = None

    def show(self, force_open=False):
        super().show(force_open)
        if not self.built:
            self.build_ui()
            self.built = True
        self.refresh(force=True)

    def build_ui(self):
        # Header with Icon
        header_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 0))

        try:
            from PIL import Image, ImageTk
            import os
            from utils import get_resource_path
            icon_path = get_resource_path("hitmiss_icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
                tk.Label(header_frame, image=self.icon_image, bg=WINDOW_BG).pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            print(f"Error loading HitMiss icon: {e}")

        tk.Label(header_frame, text="COMBAT RESOLUTION", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG, padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        def create_input(parent, label, key, default="0", options=None, is_bool=False):
            frame = tk.Frame(parent, bg=WINDOW_BG, pady=3)
            frame.pack(fill=tk.X)
            
            lbl = tk.Label(frame, text=label, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
            lbl.pack(side=tk.LEFT)
            
            if is_bool:
                var = tk.BooleanVar(value=default == "True")
                chk = tk.Checkbutton(frame, variable=var, bg=WINDOW_BG, activebackground=WINDOW_BG,
                                    selectcolor=PANEL_DARK, command=self.calculate)
                chk.pack(side=tk.RIGHT)
                self.inputs[key] = var
            elif options:
                var = tk.StringVar(value=str(options[0]))
                opt = tk.OptionMenu(frame, var, *options, command=lambda _: self.calculate())
                opt.config(bg=BUTTON_BG, fg=TEXT_PRIMARY, activebackground=BUTTON_HOVER, 
                           activeforeground=TEXT_ACCENT, bd=0, highlightthickness=0, 
                           font=("Segoe UI", 9), width=10)
                opt["menu"].config(bg=BUTTON_BG, fg=TEXT_PRIMARY, selectcolor=ACCENT_BLUE)
                opt.pack(side=tk.RIGHT)
                self.inputs[key] = var
            else:
                var = tk.StringVar(value=default)
                ent = tk.Entry(frame, textvariable=var, bg=PANEL_DARK, fg=TEXT_PRIMARY,
                               insertbackground=TEXT_PRIMARY, bd=0, font=("Consolas", 10), width=10, justify="center")
                ent.pack(side=tk.RIGHT)
                var.trace_add("write", lambda *args: self.calculate())
                self.inputs[key] = var

        # Attacker Section
        tk.Label(main_frame, text="ATTACKER PROFILE", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        create_input(main_frame, "Base Precision", "atk_base", "75")
        create_input(main_frame, "Equipment Bonus", "atk_weapon", "10")
        create_input(main_frame, "Distance Modifier", "range_mod", "15")
        create_input(main_frame, "Using Ranged Weapon?", "is_ranged", "True", is_bool=True)
        create_input(main_frame, "Impaired Vision?", "atk_blind", "False", is_bool=True)

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Defender Section
        tk.Label(main_frame, text="DEFENDER PROFILE", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 5))
        
        # Base Stats
        create_input(main_frame, "Fundamental Defense", "def_skill", "100")
        create_input(main_frame, "Enhancement Bonus", "def_tapes", "25")
        
        # Buffs that bypass cap
        create_input(main_frame, "Nutritional Buff", "def_food", "0")
        create_input(main_frame, "Leadership Bonus", "def_sl", "0")
        create_input(main_frame, "Environment Bonus", "def_city", "0")
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=8)
        
        # Environmental / Situational
        create_input(main_frame, "Stance Modifier", "def_posture", "15")
        create_input(main_frame, "Agility Modifier", "def_move", "10")
        create_input(main_frame, "Dodge Chance %", "dodge", "15")
        create_input(main_frame, "Parry Chance %", "parry", "5")
        
        # Defender States
        state_frame = tk.Frame(main_frame, bg=WINDOW_BG)
        state_frame.pack(fill=tk.X, pady=5)
        create_input(state_frame, "Target Obscured", "def_blind", "False", is_bool=True)
        create_input(state_frame, "Target Compromised", "def_stun", "False", is_bool=True)
        create_input(state_frame, "Target Suppressed", "def_intimidated", "False", is_bool=True)

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Results Area
        res_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=15)
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        self.hit_chance_var = tk.StringVar(value="Resolution Chance: 0%")
        tk.Label(res_frame, textvariable=self.hit_chance_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Segoe UI", 12, "bold")).pack()
        
        self.avoidance_var = tk.StringVar(value="Base Chance: 0% | Avoidance: 0%")
        tk.Label(res_frame, textvariable=self.avoidance_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack()

        self.summary_var = tk.StringVar(value="Ready")
        tk.Label(res_frame, textvariable=self.summary_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Consolas", 9), wraplength=350).pack(pady=5)

        self.calculate()

    def calculate(self):
        try:
            # 1. Attacker Accuracy
            atk_base = int(self.inputs["atk_base"].get() or 0)
            atk_weapon = int(self.inputs["atk_weapon"].get() or 0)
            range_mod = int(self.inputs["range_mod"].get() or 0)
            is_ranged = self.inputs["is_ranged"].get()
            atk_blind = self.inputs["atk_blind"].get()

            total_acc = atk_base + atk_weapon + range_mod
            if atk_blind:
                total_acc -= 60

            # 2. Defender Defense (Implementing SWG Server Logic)
            def_skill = int(self.inputs["def_skill"].get() or 0)
            def_tapes = int(self.inputs["def_tapes"].get() or 0)
            def_food = int(self.inputs["def_food"].get() or 0)
            def_sl = int(self.inputs["def_sl"].get() or 0)
            def_city = int(self.inputs["def_city"].get() or 0)
            
            def_blind = self.inputs["def_blind"].get()
            def_stun = self.inputs["def_stun"].get()
            def_intimidated = self.inputs["def_intimidated"].get()

            # A. Tape Cap (+25)
            capped_tapes = min(25, def_tapes)
            raw_defense = def_skill + capped_tapes
            
            # B. Apply Debuffs to Raw Score (Defensive Buffer Mechanic)
            debuffed_def = raw_defense
            if def_blind: debuffed_def -= 60
            if def_stun: debuffed_def -= 50
            if def_intimidated: debuffed_def -= 20
            
            # C. Server Baseline Cap (125)
            capped_base = min(125, debuffed_def)
            
            # D. External Overrides (Bypass Cap)
            external_buffs = def_food + def_sl + def_city
            final_base_defense = max(0, capped_base + external_buffs)

            # E. Situational Modifiers
            def_posture = int(self.inputs["def_posture"].get() or 0)
            def_move = int(self.inputs["def_move"].get() or 0)
            
            total_def = final_base_defense + def_posture + def_move

            # 3. Success Resolution
            # Combined result formula
            score_value = total_acc - total_def + 50
            
            # Probability evaluation
            raw_success_prob = max(0, min(100, score_value))
            
            # Adjust for specialization penalties
            if is_ranged:
                # 5% inherent variation
                raw_success_prob = min(95, raw_success_prob)
            
            # Global failure floor
            raw_success_prob = min(99, raw_success_prob)

            # 4. Secondary Mitigation
            dodge = int(self.inputs["dodge"].get() or 0)
            parry = int(self.inputs["parry"].get() or 0)
            
            avoid_prob = 0
            if not def_intimidated:
                avoid_prob = dodge if is_ranged else parry
            
            # Final Result = P(Initial Success) * P(Not Avoided)
            final_success_chance = raw_success_prob * (1.0 - (avoid_prob / 100.0))
            
            self.hit_chance_var.set(f"Final Success Chance: {final_success_chance:.1f}%")
            self.avoidance_var.set(f"Base Chance: {raw_success_prob}% | Avoidance: {avoid_prob}%")
            
            summary = f"Precision({total_acc}) vs Counter({total_def})\n"
            summary += f"Net Defense: {final_base_defense} (Raw {raw_defense} -> Capped {capped_base})\n"
            if external_buffs > 0: summary += f"Total Buffs: +{external_buffs}\n"
            if is_ranged: summary += "(Ranged Precision Adjustment Applied)\n"
            if def_intimidated: summary += "(Avoidance suppressed by Suppression effect)"
            
            self.summary_var.set(summary)
        except Exception as e:
            self.hit_chance_var.set("Error")
            self.summary_var.set("Check input values")

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        if self.window.attributes("-alpha") != self.app.current_alpha:
            self.window.attributes("-alpha", self.app.current_alpha)
            
        from utils import get_dynamic_text_color
        text_color = get_dynamic_text_color(self.app.current_alpha)
        
        if self.built:
            def update_recursive(parent):
                for child in parent.winfo_children():
                    if isinstance(child, (tk.Label, tk.Button, tk.Checkbutton)):
                        try:
                            curr_fg = child.cget("fg").lower()
                            if curr_fg not in [ACCENT_BLUE.lower(), TEXT_ACCENT.lower(), "#ff4444"]:
                                child.config(fg=text_color)
                        except: pass
                    elif isinstance(child, tk.Frame):
                        update_recursive(child)
            update_recursive(self.content_container)
            self.calculate()
