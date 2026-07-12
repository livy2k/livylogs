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
        
        # Presets Menu
        preset_options = [
            "Flat", "Classical", "Club", "Dance", "Full Bass", 
            "Full Treble", "Headphones", "Large Hall", "Live", 
            "Party", "Pop", "Reggae", "Rock", "Ska", "Soft", 
            "Soft Rock", "Techno"
        ]
        self.preset_var = tk.StringVar(value="Presets")
        self.preset_menu = ttk.OptionMenu(ctrl_frame, self.preset_var, "Presets", *preset_options, command=self.load_preset)
        self.preset_menu.pack(side=tk.LEFT, padx=(0, 10))
        
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

    def load_preset(self, preset_name):
        # Preset values (standard VLC presets - approx)
        presets = {
            "Flat": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "Classical": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -7.0, -7.0, -7.0, -9.0],
            "Club": [0.0, 0.0, 1.5, 3.0, 3.0, 3.0, 1.5, 0.0, 0.0, 0.0],
            "Dance": [9.0, 7.0, 2.0, 0.0, 0.0, -5.0, -7.0, -7.0, 0.0, 0.0],
            "Full Bass": [15.0, 15.0, 15.0, 0.0, -7.0, -10.0, -12.0, -14.0, -15.0, -15.0],
            "Full Treble": [-15.0, -15.0, -15.0, -10.0, -5.0, 2.0, 11.0, 15.0, 15.0, 15.0],
            "Headphones": [4.5, 11.0, 5.5, -3.0, -2.0, 1.5, 4.5, 9.0, 12.5, 15.0],
            "Large Hall": [10.0, 10.0, 5.5, 5.5, 0.0, -4.5, -4.5, -4.5, 0.0, 0.0],
            "Live": [-4.5, 0.0, 4.0, 5.0, 5.5, 5.5, 4.0, 2.5, 2.5, 2.5],
            "Party": [7.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 7.0],
            "Pop": [-1.5, 3.0, 7.0, 8.0, 5.5, -2.0, -4.0, -4.0, -1.5, -1.5],
            "Reggae": [0.0, 0.0, 0.0, -5.0, 0.0, 6.5, 6.5, 0.0, 0.0, 0.0],
            "Rock": [8.0, 4.5, -5.5, -8.0, -3.0, 4.0, 8.5, 11.0, 11.0, 11.0],
            "Ska": [-2.5, -4.5, -4.0, -1.5, 4.0, 6.0, 8.5, 9.0, 11.0, 9.5],
            "Soft": [4.5, 1.5, 0.0, -1.5, -1.5, 2.0, 8.5, 11.0, 12.5, 14.0],
            "Soft Rock": [4.0, 4.0, 1.5, -1.5, -4.0, -5.0, -3.0, -1.5, 2.5, 8.5],
            "Techno": [8.0, 5.5, 0.0, -5.5, -4.5, 0.0, 8.0, 9.0, 9.0, 8.5]
        }
        
        if preset_name in presets:
            self.bands = presets[preset_name]
            for i, val in enumerate(self.bands):
                self.sliders[i].set(val)
            self.update_eq()

    def toggle_bass_boost(self):
        self.bass_boost_active = not self.bass_boost_active
        if self.bass_boost_active:
            # Boost low frequencies significantly to make it noticeable
            # Bands: 31Hz, 62Hz, 125Hz
            self.bands[0] = 15.0 # Max boost for sub-bass
            self.bands[1] = 12.0 # High boost for bass
            self.bands[2] = 8.0  # Moderate boost for low-mids
            self.bb_btn.config(text="BASS BOOST: ON", fg=ACCENT_BLUE)
        else:
            # Return to flat (or previous state)
            self.bands[0] = 0.0
            self.bands[1] = 0.0
            self.bands[2] = 0.0
            self.bb_btn.config(text="BASS BOOST: OFF", fg=TEXT_PRIMARY)
        
        # Update sliders visual
        for i, val in enumerate(self.bands):
            self.sliders[i].set(val)
        
        # We also want to increase pre-amp slightly when bass boost is on to avoid clipping
        # but VLC handles volume separately. Let's just update the EQ.
        self.update_eq()

    def reset_eq(self):
        self.preamp = 0.0
        self.bands = [0.0] * 10
        self.pre_slider.set(0.0)
        for s in self.sliders:
            s.set(0.0)
        self.bass_boost_active = False
        self.bb_btn.config(text="BASS BOOST: OFF", fg=TEXT_PRIMARY)
        self.preset_var.set("Presets")
        self.update_eq()
