import tkinter as tk
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)

class ResistsCalcWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "CM", "ResistsCalcWindow", 420, 750, fixed_size=True)
        self.inputs = {}
        self.built = False

    def show(self, force_open=False):
        super().show(force_open)
        if not self.built:
            self.build_ui()
            self.built = True
        self.refresh(force=True)

    def build_ui(self):
        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG, padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        def create_input(parent, label, key, default="0"):
            frame = tk.Frame(parent, bg=WINDOW_BG, pady=4)
            frame.pack(fill=tk.X)
            
            lbl = tk.Label(frame, text=label, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
            lbl.pack(side=tk.LEFT)
            
            var = tk.StringVar(value=default)
            ent = tk.Entry(frame, textvariable=var, bg=PANEL_DARK, fg=TEXT_PRIMARY,
                           insertbackground=TEXT_PRIMARY, bd=0, font=("Consolas", 10), width=10, justify="center")
            ent.pack(side=tk.RIGHT)
            var.trace_add("write", lambda *args: self.calculate())
            self.inputs[key] = var

        # Section 1: STRENGTH
        tk.Label(main_frame, text="STRENGTH", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Value Slider (Base Damage)
        val_frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        val_frame.pack(fill=tk.X)
        tk.Label(val_frame, text="Value", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.val_var = tk.StringVar(value="500")
        self.val_slider = tk.Scale(val_frame, from_=0, to=2000, orient=tk.HORIZONTAL, 
                                     bg=WINDOW_BG, fg=TEXT_SECONDARY, highlightthickness=0,
                                     troughcolor=PANEL_DARK, activebackground=ACCENT_BLUE,
                                     showvalue=True, bd=0, font=("Consolas", 8),
                                     variable=self.val_var, command=lambda _: self.calculate())
        self.val_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.inputs["base_tick"] = self.val_var

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Section 2: CHANCE
        tk.Label(main_frame, text="CHANCE", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # POT Slider
        pot_frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        pot_frame.pack(fill=tk.X)
        tk.Label(pot_frame, text="POT", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.pot_var = tk.StringVar(value="40")
        self.pot_slider = tk.Scale(pot_frame, from_=0, to=200, orient=tk.HORIZONTAL, 
                                     bg=WINDOW_BG, fg=TEXT_SECONDARY, highlightthickness=0,
                                     troughcolor=PANEL_DARK, activebackground=ACCENT_BLUE,
                                     showvalue=True, bd=0, font=("Consolas", 8),
                                     variable=self.pot_var, command=lambda _: self.calculate())
        self.pot_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.inputs["poison_potency"] = self.pot_var

        # RES Slider
        res_frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        res_frame.pack(fill=tk.X)
        tk.Label(res_frame, text="RES", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.res_var = tk.StringVar(value="50")
        self.res_slider = tk.Scale(res_frame, from_=0, to=200, orient=tk.HORIZONTAL, 
                                     bg=WINDOW_BG, fg=TEXT_SECONDARY, highlightthickness=0,
                                     troughcolor=PANEL_DARK, activebackground=ACCENT_BLUE,
                                     showvalue=True, bd=0, font=("Consolas", 8),
                                     variable=self.res_var, command=lambda _: self.calculate())
        self.res_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.inputs["poison_res"] = self.res_var
        
        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)
        
        # Section 3: APPLY
        tk.Label(main_frame, text="APPLY", bg=WINDOW_BG, fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        create_input(main_frame, "Buff", "poison_absorb", "50")
        
        jedi_frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=4)
        jedi_frame.pack(fill=tk.X)
        tk.Label(jedi_frame, text="Enhancer", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.jedi_enabled = tk.BooleanVar(value=False)
        self.jedi_check = tk.Checkbutton(jedi_frame, variable=self.jedi_enabled, bg=WINDOW_BG, activebackground=WINDOW_BG,
                                        selectcolor=PANEL_DARK, command=self.calculate)
        self.jedi_check.pack(side=tk.RIGHT)

        tk.Frame(main_frame, bg=BORDER_COLOR, height=1).pack(fill=tk.X, pady=10)

        # Results Area
        res_frame = tk.Frame(self.content_container, bg=PANEL_DARK, pady=15)
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chance_var = tk.StringVar(value="Stick: 0%")
        tk.Label(res_frame, textvariable=self.chance_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Segoe UI", 11, "bold")).pack()
        
        tk.Label(res_frame, text="Tick", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack()
        self.final_tick_var = tk.StringVar(value="0")
        tk.Label(res_frame, textvariable=self.final_tick_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Consolas", 18, "bold")).pack()
        
        tk.Label(res_frame, text="Mitigated", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack()
        self.mitigation_var = tk.StringVar(value="0%")
        # Unified display style
        tk.Label(res_frame, textvariable=self.mitigation_var, bg=PANEL_DARK, fg=TEXT_ACCENT, font=("Consolas", 18, "bold")).pack()

        self.calculate()

    def calculate(self):
        try:
            # 1. Activation Check
            # Threshold logic
            pwr = int(self.inputs["poison_potency"].get() or 0)
            res = int(self.inputs["poison_res"].get() or 0)
            
            # Net intensity
            diff = pwr - res
            
            # Probability is diff % (clamped between 0 and 100)
            activate_prob = max(0, min(100, diff))
            
            self.chance_var.set(f"Stick: {activate_prob:.1f}%")
            
            # 2. Attenuation Logic
            base_tick = int(self.inputs["base_tick"].get() or 0)
            absorb_val = int(self.inputs["poison_absorb"].get() or 0)
            
            # SWG Engine Logic:
            # - poison_absorption skill caps at 50%
            # - Jedi/Doc Buffs also cap at 50%
            
            # Primary absorption (Skill-based, capped at 50)
            capped_skill = min(50, absorb_val)
            skill_reduction = capped_skill / 100.0
            
            # Buff portion (Doc + Jedi)
            # User noted "target resistance is not the same as poison absorption but are the same doctor absorbtion"
            # This means 'Buff' (absorb_val) acts as the Doctor absorption.
            doc_reduction = absorb_val / 100.0
            
            innate_active = self.jedi_enabled.get()
            jedi_reduction = 0.50 if innate_active else 0.0
            
            # The buff portion (Doc + Jedi) is capped at 50% total
            buff_reduction = min(0.50, doc_reduction + jedi_reduction)
            
            # Calculate mitigated damage: Base -> apply skill -> apply buffs
            damage_after_skill = base_tick * (1.0 - skill_reduction)
            final_tick = damage_after_skill * (1.0 - buff_reduction)
            
            # Universal Hard Cap check (95%)
            total_attenuation = 1.0 - (final_tick / base_tick) if base_tick > 0 else 0
            if total_attenuation > 0.95:
                final_tick = base_tick * 0.05
                total_attenuation = 0.95
            
            final_tick = round(final_tick)
            final_tick = max(0, final_tick)
            
            self.final_tick_var.set(f"{final_tick:,}")
            self.mitigation_var.set(f"{round(total_attenuation * 100)}%")
        except Exception as e:
            self.chance_var.set("Error")
            self.final_tick_var.set("0")
            self.mitigation_var.set("0%")

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
                    elif isinstance(child, tk.Scale):
                        try:
                            child.config(fg=text_color)
                        except: pass
                    elif isinstance(child, tk.Frame):
                        update_recursive(child)
            update_recursive(self.content_container)
            self.calculate()
