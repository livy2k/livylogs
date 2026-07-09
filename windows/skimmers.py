import tkinter as tk
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT
)
from windows.base_window import BasePopoutWindow

class SkimmersWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Skimmers", "SkimmersWindow", 350, 400)

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        # Additional title bar buttons for Skimmers
        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_skimmers_manual())

        search_btn = tk.Label(self.title_bar, text="🔍", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 10), cursor="hand2", padx=5)
        search_btn.pack(side=tk.LEFT)
        search_btn.bind("<Button-1>", lambda e: self.app.toggle_skimmer_search())
        if self.app.skimmer_search_mode: search_btn.config(fg=ACCENT_BLUE)

    def refresh(self):
        if not self.window: return
        for widget in self.content_container.winfo_children(): widget.destroy()
        
        # Simple list display logic (to be filled by CombatLogApp.refresh_skimmers_window content)
        # For now, this is a placeholder that CombatLogApp will call or we can move logic here.
        pass
