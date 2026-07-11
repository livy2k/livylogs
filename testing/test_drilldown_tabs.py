import tkinter as tk
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_drilldown_tabs():
    print("[TEST] Starting drill-down tabs verification...")
    root = tk.Tk()
    # Mocking char_name since it might be needed
    root.withdraw() 
    app = CombatLogApp(root)
    
    # Add some data
    app.process_external_event({"type": "stats", "name": "Livy", "damage": 5000, "healing": 200})
    app.process_external_event({"type": "dealt", "source": "Livy", "target": "Droid", "damage": 100, "ability": "Strike"})
    app.process_external_event({"type": "taken", "victim": "Livy", "attacker": "Stormtrooper", "damage": 50, "ability": "Blaster"})
    
    print("[TEST] Opening Details Window...")
    details = app.details_win
    details.show()
    details.refresh(force=True)
    root.update()
    
    # 1. Drill down into Livy
    print("[TEST] Drilling down into 'Livy'...")
    details.drill_down("Livy")
    root.update()
    
    # Check tabs
    tabs = details.tab_btns
    print(f"[TEST] Available tabs: {list(tabs.keys())}")
    
    if "all" in tabs:
        print("[TEST] FAILURE: 'ALL' tab still exists in Details window.")
    else:
        print("[TEST] SUCCESS: 'ALL' tab removed from Details window.")
        
    current_tab = getattr(app, 'details_tab', 'none')
    print(f"[TEST] Current active tab: {current_tab}")
    if current_tab == "dealt":
        print("[TEST] SUCCESS: Default tab is 'DEALT'.")
    else:
        print(f"[TEST] FAILURE: Default tab is '{current_tab}', expected 'dealt'.")

    # 2. Check Leaderboard Window
    print("[TEST] Opening Leaderboard Window...")
    leaderboard = app.leaderboard_win
    leaderboard.show()
    leaderboard.refresh(force=True)
    root.update()
    
    print("[TEST] Drilling down into 'Livy' in Leaderboard...")
    leaderboard.drill_down("Livy")
    root.update()
    
    tabs_lb = leaderboard.tab_btns
    print(f"[TEST] Available tabs in Leaderboard: {list(tabs_lb.keys())}")
    
    if "all" in tabs_lb:
        print("[TEST] FAILURE: 'ALL' tab still exists in Leaderboard window.")
    else:
        print("[TEST] SUCCESS: 'ALL' tab removed from Leaderboard window.")

    print("[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_drilldown_tabs()
