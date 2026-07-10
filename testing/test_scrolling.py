import tkinter as tk
from tkinter import ttk
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from constants import *
from livylogs_main import CombatLogApp

def test_scrolling():
    print("[TEST] Starting scroll test...")
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # Initialize the ttk style (normally done in app.build_layout)
    style = ttk.Style()
    style.theme_use('clam')
    
    # Mock a lot of players to force scrollbar
    print("[TEST] Generating 50 players...")
    for i in range(50):
        app.process_external_event({"type": "stats", "name": f"Player_{i:02d}", "damage": 1000 - i, "healing": 0})
    
    print("[TEST] Showing Leaderboard...")
    win = app.leaderboard_win
    win.show()
    # Force the refresh
    win.last_full_refresh = 0
    win.refresh(force=True)
    root.update()
    
    # Check if scrollbar is visible and has a non-zero range
    win = app.leaderboard_win
    canvas = None
    scrollbar = None
    
    # Find canvas and scrollbar in leaderboard_win
    for child in win.content_container.winfo_children():
        if isinstance(child, tk.Canvas):
            canvas = child
        elif isinstance(child, (tk.Scrollbar, ttk.Scrollbar)):
            scrollbar = child
            
    if canvas and scrollbar:
        root.update()
        s_range = scrollbar.get()
        print(f"[TEST] Scrollbar range: {s_range}")
        if s_range[0] == 0.0 and s_range[1] < 1.0:
            print("[TEST] SUCCESS: Scrollbar is active (thumb is smaller than trough).")
        else:
            print(f"[TEST] FAILURE: Scrollbar might not be active or content is not overflowing. Range: {s_range}")
    else:
        print(f"[TEST] FAILURE: Could not find canvas or scrollbar. Canvas found: {canvas is not None}, Scrollbar found: {scrollbar is not None}")

    # Keep it open for a few seconds if you were watching, but since I'm an agent I'll just close it
    print("[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_scrolling()
