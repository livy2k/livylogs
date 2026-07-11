import tkinter as tk
from tkinter import ttk
import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_scroll_reset():
    print("[TEST] Starting scroll reset verification...")
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # Add a lot of data to make it scrollable
    for i in range(50):
        app.process_external_event({"type": "stats", "name": f"Player_{i:02d}", "damage": 1000, "healing": 0})
    
    print("[TEST] Opening Details Window...")
    details = app.details_win
    details.show()
    details.refresh(force=True)
    root.update()
    
    # Scroll down the top view
    print("[TEST] Scrolling down the top view...")
    details.scroll_canvas.yview_moveto(0.5)
    root.update()
    initial_pos = details.scroll_canvas.yview()[0]
    print(f"[TEST] Top view scroll position: {initial_pos}")
    
    # 1. Drill down
    print("[TEST] Drilling down into 'Player_00'...")
    details.drill_down("Player_00")
    root.update()
    
    # Check if top view canvas reset (it should, although it's hidden)
    top_pos_after_drill = details.scroll_canvas.yview()[0]
    print(f"[TEST] Top view scroll position after drill-down: {top_pos_after_drill}")
    
    # Scroll the log view
    print("[TEST] Scrolling down the log view...")
    details.txt.yview_moveto(0.5)
    root.update()
    log_pos = details.txt.yview()[0]
    print(f"[TEST] Log view scroll position: {log_pos}")
    
    # 2. Go back to top
    print("[TEST] Going back to top...")
    details.go_to_top()
    root.update()
    
    top_pos_final = details.scroll_canvas.yview()[0]
    print(f"[TEST] Top view scroll position after returning: {top_pos_final}")
    
    if top_pos_final == 0.0:
        print("[TEST] SUCCESS: Scroll position reset to 0.0")
    else:
        print(f"[TEST] FAILURE: Scroll position is {top_pos_final}")

    print("[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_scroll_reset()
