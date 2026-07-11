import tkinter as tk
from tkinter import ttk
import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_drilldown_transition():
    print("[TEST] Starting drill-down transition test...")
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # Add some data
    app.process_external_event({"type": "stats", "name": "Livy", "damage": 5000, "healing": 200})
    app.process_external_event({"type": "dealt", "source": "Livy", "target": "Droid", "damage": 100, "ability": "Strike"})
    
    print("[TEST] Opening Details Window...")
    details = app.details_win
    details.show()
    details.refresh(force=True)
    root.update()
    
    # 1. Drill down into Livy
    print("[TEST] Drilling down into 'Livy'...")
    details.drill_down("Livy")
    root.update()
    
    # Check if detail_view is mapped and top_view is not
    if details.detail_view.winfo_ismapped() and not details.top_view.winfo_ismapped():
        print("[TEST] SUCCESS: Drill-down view active.")
    else:
        print(f"[TEST] FAILURE: State mismatch. Detail mapped: {details.detail_view.winfo_ismapped()}, Top mapped: {details.top_view.winfo_ismapped()}")

    # 2. Go back to top
    print("[TEST] Going back to top...")
    details.go_to_top()
    root.update()
    
    if details.top_view.winfo_ismapped() and not details.detail_view.winfo_ismapped():
        print("[TEST] SUCCESS: Top view restored.")
        # Check for gap: If top_view is at the top of content_container (y=0 or y=nav_row height)
        # nav_row should be forgotten
        if details.nav_row.winfo_ismapped():
            print("[TEST] FAILURE: nav_row still mapped in top view.")
        else:
            print("[TEST] SUCCESS: nav_row correctly hidden.")
            
        y_pos = details.top_view.winfo_y()
        # content_container has padx=8, pady=8
        print(f"[TEST] top_view y position: {y_pos}")
        if y_pos == 8: 
            print("[TEST] SUCCESS: top_view is at the expected top position (8px due to container pady).")
        elif y_pos < 8:
            print("[TEST] SUCCESS: top_view is near the top.")
        else:
            print(f"[TEST] WARNING: top_view y position is {y_pos}, might have a gap if nav_row (bg=PANEL_DARK) is showing.")
    else:
        print(f"[TEST] FAILURE: State mismatch. Top mapped: {details.top_view.winfo_ismapped()}, Detail mapped: {details.detail_view.winfo_ismapped()}")

    print("[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_drilldown_transition()
