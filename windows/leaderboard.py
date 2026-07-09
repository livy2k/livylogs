import tkinter as tk
from constants import (
    PANEL_DARK, TEXT_SECONDARY
)
from windows.base_window import BasePopoutWindow

class LeaderboardWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Leaderboard", "LeaderboardWindow", 300, 400)

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_leaderboard_manual())
