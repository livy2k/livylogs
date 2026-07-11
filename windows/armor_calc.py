import tkinter as tk
import math
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class ArmorCalcWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Defense Calculator", "ArmorCalcWindow", 400, 640, fixed_size=True)
        self.inputs = {}
        self.built = False

    def show(self, force_open=False):
        super().show(force_open)
        if not self.built:
            self.build_ui()
            self.built = True
        # Apply initial transparency
        self.refresh(force=True)

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

        # Section Labels
        tk.Label(main_frame, text="OFFENSIVE PROFILE", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        create_input(main_frame, "Minimum Damage", "min_dmg", "500")
        create_input(main_frame, "Maximum Damage", "max_dmg", "1000")
        create_input(main_frame, "Penetration (0-3)", "weapon_ap", options=[0, 1, 2, 3])
        
        # Damage Type
        frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        frame.pack(fill=tk.X)
        tk.Label(frame, text="Damage Type", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.dmg_type_var = tk.StringVar(value="Kinetic")
        dmg_types = ["Kinetic", "Energy", "Blast", "Heat", "Cold", "Acid", "Electricity", "Stun", "Lightsaber"]
        self.dmg_type_opt = tk.OptionMenu(frame, self.dmg_type_var, *dmg_types, command=lambda _: self.calculate())
        self.dmg_type_opt.config(bg=BUTTON_BG, fg=TEXT_PRIMARY, activebackground=BUTTON_HOVER, 
                                 activeforeground=TEXT_ACCENT, bd=0, highlightthickness=0, font=("Segoe UI", 9), width=10)
        self.dmg_type_opt.pack(side=tk.RIGHT)

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Mitigation Section
        tk.Label(main_frame, text="DEFENSIVE PROFILE", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        create_input(main_frame, "Protection Tier (0-3)", "armor_ar", options=[0, 1, 2, 3])
        create_input(main_frame, "Base Absorption % (0-92)", "armor_eff", "80")
        create_input(main_frame, "Mastery Level (0-3)", "mitigation", options=[0, 1, 2, 3])
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)
        
        # Secondary Section
        tk.Label(main_frame, text="SUPPLEMENTAL SHIELD", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        psg_toggle_frame = tk.Frame(main_frame, bg=WINDOW_BG)
        psg_toggle_frame.pack(fill=tk.X)
        tk.Label(psg_toggle_frame, text="Shield Active", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.psg_enabled = tk.BooleanVar(value=False)
        self.psg_check = tk.Checkbutton(psg_toggle_frame, variable=self.psg_enabled, bg=WINDOW_BG, activebackground=WINDOW_BG,
                                        selectcolor=PANEL_DARK, command=self.calculate)
        self.psg_check.pack(side=tk.RIGHT)

        create_input(main_frame, "Shield Capacity %", "psg_eff", "40")

        create_input(main_frame, "Shield Integrity", "psg_cond", "1000")

        # Results Area
        res_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=10)
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_range_var = tk.StringVar(value="0 - 0")
        tk.Label(res_frame, text="MITIGATED DAMAGE RANGE", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack()
        tk.Label(res_frame, textvariable=self.result_range_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Consolas", 16, "bold")).pack()
        
        self.reduction_var = tk.StringVar(value="Total Reduction: 0%")
        tk.Label(res_frame, textvariable=self.reduction_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack()

        self.psg_loss_var = tk.StringVar(value="Shield Impact: 0")
        tk.Label(res_frame, textvariable=self.psg_loss_var, bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack()

        self.calculate()

    def calculate(self):
        try:
            min_dmg = int(self.inputs["min_dmg"].get() or 0)
            max_dmg = int(self.inputs["max_dmg"].get() or 0)
            weapon_ap = int(self.inputs["weapon_ap"].get())
            
            armor_ar = int(self.inputs["armor_ar"].get())
            armor_eff = min(92, int(self.inputs["armor_eff"].get() or 0))
            mitigation_lvl = int(self.inputs["mitigation"].get())
            
            psg_equipped = self.psg_enabled.get()
            psg_eff = int(self.inputs["psg_eff"].get() or 0)
            psg_cond = int(self.inputs["psg_cond"].get() or 0)

            # Vulnerability is assumed if rating/resist is 0
            is_armor_vuln = (armor_ar == 0 and armor_eff == 0)
            is_psg_vuln = (psg_eff == 0)

            def mitigate(damage):
                curr = float(damage)
                psg_absorbed = 0
                
                # Step 1: Shield
                if psg_equipped and psg_cond > 0:
                    # Shields provide base tier 1 protection
                    psg_tier = 1
                    if not is_psg_vuln:
                        if psg_tier > weapon_ap:
                            divisor = 2 ** (psg_tier - weapon_ap)
                            curr /= divisor
                        
                        psg_absorbed = round(curr * (psg_eff / 100.0))
                        curr -= psg_absorbed
                
                # Step 2: Tier check
                if not is_armor_vuln:
                    if armor_ar > weapon_ap:
                        divisor = 2 ** (armor_ar - weapon_ap)
                        curr /= divisor
                
                # Step 3: Suit Resistances
                final_resist = 0 if is_armor_vuln else armor_eff
                reduction_factor = (100 - final_resist) / 100.0
                curr = round(curr * reduction_factor)
                
                return max(0, int(curr)), psg_absorbed

            # Application Mastery (Dispersion Logic)
            mastery_steps = {0: 0.0, 1: 0.20, 2: 0.40, 3: 0.60}
            dispersion = mastery_steps.get(mitigation_lvl, 0.0)
            
            dmg_range = max_dmg - min_dmg
            new_range = round(dmg_range * (1.0 - dispersion))
            eff_max_dmg = min_dmg + new_range
            
            final_min, psg_loss_min = mitigate(min_dmg)
            final_max, psg_loss_max = mitigate(eff_max_dmg)
            
            self.result_range_var.set(f"{final_min:,} - {final_max:,}")
            
            # Estimate total reduction (on avg)
            avg_base = (min_dmg + max_dmg) / 2.0
            avg_final = (final_min + final_max) / 2.0
            if avg_base > 0:
                red_pct = round((1.0 - (avg_final / avg_base)) * 100, 1)
                self.reduction_var.set(f"Total Reduction: {red_pct}%")
            else:
                self.reduction_var.set("Total Reduction: 0%")

            avg_psg_loss = round((psg_loss_min + psg_loss_max) / 2.0)
            self.psg_loss_var.set(f"Shield Impact: {avg_psg_loss}")
        except Exception as e:
            self.result_range_var.set("Error")
            self.reduction_var.set("Check Input Values")

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        # Sync transparency
        if self.window.attributes("-alpha") != self.app.current_alpha:
            self.window.attributes("-alpha", self.app.current_alpha)
        
        # Update text contrast based on transparency
        from utils import get_dynamic_text_color
        text_color = get_dynamic_text_color(self.app.current_alpha)
        
        # Apply to all relevant labels and widgets
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
