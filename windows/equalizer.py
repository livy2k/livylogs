"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)

class EqualizerWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Equalizer", "EqualizerWindow", 400, 320, fixed_size=True)
        self.bands = [0.0] * 10
        self.preamp = 0.0
        self.bass_boost_active = False
        
        # Load current state from radio manager
        if hasattr(self.app, 'radio_mgr') and self.app.radio_mgr:
            self.bands, self.preamp = self.app.radio_mgr.get_equalizer()
            
        self.sliders = []
        self.frequencies = [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists(): return
        
        for widget in self.content_container.winfo_children():
            widget.destroy()
            
        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Preamp Slider
        pre_frame = tk.Frame(main_frame, bg=PANEL_DARK, pady=5)
        pre_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(pre_frame, text="PRE-AMP", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.pre_slider = ttk.Scale(pre_frame, from_=-20, to=20, value=self.preamp, orient=tk.HORIZONTAL, command=self.update_eq)
        self.pre_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Sliders Container
        sliders_frame = tk.Frame(main_frame, bg=WINDOW_BG)
        sliders_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sliders = []
        for i, freq in enumerate(self.frequencies):
            f_frame = tk.Frame(sliders_frame, bg=WINDOW_BG)
            f_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
            
            s = ttk.Scale(f_frame, from_=20, to=-20, value=self.bands[i], orient=tk.VERTICAL, command=self.update_eq)
            s.pack(fill=tk.Y, expand=True)
            self.sliders.append(s)
            
            lbl_text = f"{freq}" if freq < 1000 else f"{int(freq/1000)}k"
            tk.Label(f_frame, text=lbl_text, bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Consolas", 7)).pack()

        # Controls
        ctrl_frame = tk.Frame(main_frame, bg=WINDOW_BG, pady=10)
        ctrl_frame.pack(fill=tk.X)
        
        self.bb_btn = tk.Button(ctrl_frame, text="BASS BOOST: OFF", bg=PANEL_DARK, fg=TEXT_PRIMARY,
                                font=("Segoe UI", 9, "bold"), bd=1, relief=tk.FLAT, padx=10,
                                command=self.toggle_bass_boost)
        self.bb_btn.pack(side=tk.LEFT)
        
        tk.Button(ctrl_frame, text="RESET", bg=PANEL_DARK, fg=TEXT_PRIMARY,
                  font=("Segoe UI", 9, "bold"), bd=1, relief=tk.FLAT, padx=10,
                  command=self.reset_eq).pack(side=tk.RIGHT)

    def update_eq(self, *args):
        self.preamp = self.pre_slider.get()
        self.bands = [s.get() for s in self.sliders]
        
        if hasattr(self.app, 'radio_mgr') and self.app.radio_mgr:
            self.app.radio_mgr.set_equalizer(self.bands, self.preamp)

    def toggle_bass_boost(self):
        self.bass_boost_active = not self.bass_boost_active
        if self.bass_boost_active:
            # Boost low frequencies
            self.bands[0] = 12.0 # 31.25Hz
            self.bands[1] = 10.0 # 62.5Hz
            self.bands[2] = 8.0  # 125Hz
            self.bb_btn.config(text="BASS BOOST: ON", fg=ACCENT_BLUE)
        else:
            self.bands[0] = 0.0
            self.bands[1] = 0.0
            self.bands[2] = 0.0
            self.bb_btn.config(text="BASS BOOST: OFF", fg=TEXT_PRIMARY)
        
        # Update sliders visual
        for i, val in enumerate(self.bands):
            self.sliders[i].set(val)
        self.update_eq()

    def reset_eq(self):
        self.preamp = 0.0
        self.bands = [0.0] * 10
        self.pre_slider.set(0.0)
        for s in self.sliders:
            s.set(0.0)
        self.bass_boost_active = False
        self.bb_btn.config(text="BASS BOOST: OFF", fg=TEXT_PRIMARY)
        self.update_eq()
