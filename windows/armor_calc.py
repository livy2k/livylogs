import tkinter as tk
import math
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class ArmorCalcWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Armor Reduction Calculator", "ArmorCalcWindow", 350, 520, fixed_size=True)
        self.inputs = {}
        self.built = False

    def show(self, force_open=False):
        super().show(force_open)
        if not self.built:
            self.build_ui()
            self.built = True

    def build_ui(self):
        # Create a scrollable or just a neatly packed layout
        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG, padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        def create_input(parent, label, key, default="0", options=None):
            frame = tk.Frame(parent, bg=WINDOW_BG, pady=4)
            frame.pack(fill=tk.X)
            
            lbl = tk.Label(frame, text=label, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
            lbl.pack(side=tk.LEFT)
            
            if options:
                var = tk.StringVar(value=options[0] if isinstance(options[0], str) else str(options[0]))
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
                               insertbackground=TEXT_PRIMARY, bd=0, font=("Consolas", 10), width=12, justify="center")
                ent.pack(side=tk.RIGHT)
                var.trace_add("write", lambda *args: self.calculate())
                self.inputs[key] = var

        # Damage Section
        tk.Label(main_frame, text="ATTACKER DATA", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        create_input(main_frame, "Base Min Damage", "min_dmg", "500")
        create_input(main_frame, "Base Max Damage", "max_dmg", "1000")
        create_input(main_frame, "Weapon AP (0-3)", "weapon_ap", options=[0, 1, 2, 3])
        
        # Damage Type
        frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        frame.pack(fill=tk.X)
        tk.Label(frame, text="Damage Type", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.dmg_type_var = tk.StringVar(value="Normal")
        self.dmg_type_opt = tk.OptionMenu(frame, self.dmg_type_var, "Normal", "Vulnerable", command=lambda _: self.calculate())
        self.dmg_type_opt.config(bg=BUTTON_BG, fg=TEXT_PRIMARY, activebackground=BUTTON_HOVER, 
                                 activeforeground=TEXT_ACCENT, bd=0, highlightthickness=0, font=("Segoe UI", 9), width=10)
        self.dmg_type_opt.pack(side=tk.RIGHT)

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Target Section
        tk.Label(main_frame, text="TARGET DEFENSES", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        create_input(main_frame, "Armor Rating (0-3)", "armor_ar", options=[0, 1, 2, 3])
        create_input(main_frame, "Armor Resist % (0-92)", "armor_eff", "80")
        create_input(main_frame, "Mitigation Level (0-3)", "mitigation", options=[0, 1, 2, 3])
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)
        
        # PSG Section
        tk.Label(main_frame, text="SHIELD GENERATOR (PSG)", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        psg_toggle_frame = tk.Frame(main_frame, bg=WINDOW_BG)
        psg_toggle_frame.pack(fill=tk.X)
        tk.Label(psg_toggle_frame, text="PSG Equipped", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.psg_enabled = tk.BooleanVar(value=False)
        self.psg_check = tk.Checkbutton(psg_toggle_frame, variable=self.psg_enabled, bg=WINDOW_BG, activebackground=WINDOW_BG,
                                        selectcolor=PANEL_DARK, command=self.calculate)
        self.psg_check.pack(side=tk.RIGHT)
        
        create_input(main_frame, "PSG Effectiveness %", "psg_eff", "40")

        # Results Area
        res_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=15)
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_range_var = tk.StringVar(value="0 - 0")
        tk.Label(res_frame, text="MITIGATED DAMAGE RANGE", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold")).pack()
        tk.Label(res_frame, textvariable=self.result_range_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Consolas", 18, "bold")).pack()
        
        self.reduction_var = tk.StringVar(value="Total Reduction: 0%")
        tk.Label(res_frame, textvariable=self.reduction_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack()

        self.calculate()

    def calculate(self):
        try:
            min_dmg = int(self.inputs["min_dmg"].get() or 0)
            max_dmg = int(self.inputs["max_dmg"].get() or 0)
            weapon_ap = int(self.inputs["weapon_ap"].get())
            is_vulnerable = self.dmg_type_var.get() == "Vulnerable"
            
            armor_ar = int(self.inputs["armor_ar"].get())
            armor_eff = min(92, int(self.inputs["armor_eff"].get() or 0))
            mitigation_lvl = int(self.inputs["mitigation"].get())
            
            psg_equipped = self.psg_enabled.get()
            psg_eff = int(self.inputs["psg_eff"].get() or 0)

            def mitigate(damage):
                curr = damage
                
                # Step 1: PSG
                if psg_equipped:
                    # PSG is AR 1
                    psg_ar = 1
                    if psg_ar > weapon_ap:
                        divisor = 2 ** (psg_ar - weapon_ap)
                        curr /= divisor
                    
                    absorbed = round(curr * (psg_eff / 100.0))
                    curr -= absorbed
                
                # Step 2: Armor AR vs AP
                if armor_ar > weapon_ap and not is_vulnerable:
                    divisor = 2 ** (armor_ar - weapon_ap)
                    curr /= divisor
                
                # Step 3: Suit Resistances
                final_resist = 0 if is_vulnerable else armor_eff
                reduction_factor = (100 - final_resist) / 100.0
                curr = round(curr * reduction_factor)
                
                return max(0, int(curr))

            # Apply Mitigation Skill (Damage Range Flattening)
            mit_percents = {0: 0.0, 1: 0.20, 2: 0.40, 3: 0.60}
            mit_percent = mit_percents.get(mitigation_lvl, 0.0)
            
            dmg_range = max_dmg - min_dmg
            new_range = round(dmg_range * (1.0 - mit_percent))
            eff_max_dmg = min_dmg + new_range
            
            final_min = mitigate(min_dmg)
            final_max = mitigate(eff_max_dmg)
            
            self.result_range_var.set(f"{final_min:,} - {final_max:,}")
            
            # Estimate total reduction (on avg)
            avg_base = (min_dmg + max_dmg) / 2.0
            avg_final = (final_min + final_max) / 2.0
            if avg_base > 0:
                red_pct = round((1.0 - (avg_final / avg_base)) * 100, 1)
                self.reduction_var.set(f"Total Reduction: {red_pct}%")
            else:
                self.reduction_var.set("Total Reduction: 0%")

        except Exception as e:
            self.result_range_var.set("Error")
            self.reduction_var.set("Check Input Values")

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        super().refresh(force=force)
