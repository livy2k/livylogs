import tkinter as tk
from tkinter import ttk
import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_nav_consistency():
    print("[TEST] Starting navigation consistency test...")
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # Add some data
    app.process_external_event({"type": "stats", "name": "Livy", "damage": 5000, "healing": 200})
    
    windows = [
        ("Details", app.details_win),
        ("Leaderboard", app.leaderboard_win)
    ]
    
    for name, win in windows:
        print(f"\n[TEST] Testing {name} Window...")
        win.show()
        win.refresh(force=True)
        root.update()
        
        # Initially nav_row should not be mapped
        print(f"[TEST] {name}: Checking initial state (Top level)...")
        if win.nav_row.winfo_ismapped():
            print(f"[TEST] FAILURE: {name} nav_row should be hidden at top level.")
        else:
            print(f"[TEST] SUCCESS: {name} nav_row hidden at top level.")
            
        # Drill down
        print(f"[TEST] {name}: Drilling down...")
        win.drill_down("Livy")
        root.update()
        
        if win.nav_row.winfo_ismapped():
            h = win.nav_row.winfo_height()
            print(f"[TEST] SUCCESS: {name} nav_row visible in drill-down. Height: {h}")
            
            # Check labels/buttons styles roughly via properties
            # Note: winfo properties can be tricky before they are fully rendered, but height is a good indicator
            
            # Check player label padding/config
            try:
                padx = win.nav_player_label.pack_info().get('padx', 0)
                pady = win.nav_player_label.pack_info().get('pady', 0)
                print(f"[TEST] {name} nav_player_label padx: {padx}, pady: {pady}")
                
                btn_padx = win.back_btn.pack_info().get('padx', 0)
                btn_pady = win.back_btn.pack_info().get('pady', 0)
                print(f"[TEST] {name} back_btn padx: {btn_padx}, pady: {btn_pady}")
            except Exception as e:
                print(f"[TEST] WARNING: Could not inspect pack_info: {e}")
        else:
            print(f"[TEST] FAILURE: {name} nav_row should be visible in drill-down.")

        # Go back
        print(f"[TEST] {name}: Going back...")
        win.go_to_top()
        root.update()
        
        if not win.nav_row.winfo_ismapped():
            print(f"[TEST] SUCCESS: {name} nav_row hidden after returning.")
        else:
            print(f"[TEST] FAILURE: {name} nav_row still visible after returning.")

    print("\n[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_nav_consistency()
