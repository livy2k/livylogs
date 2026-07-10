import sys
import os
import json
import time
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp
import tkinter as tk

def test_full_flow():
    print("[TEST] Initializing CombatLogApp...")
    root = tk.Tk()
    root.withdraw() # Hide the root window
    
    app = CombatLogApp(root)
    
    # Mock some events
    events = [
        {
            "type": "stats",
            "name": "You",
            "damage": 5000,
            "healing": 1000,
            "mobs": 1,
            "loot": 1,
            "xp": 1000
        },
        {
            "type": "stats",
            "name": "Eliemau",
            "damage": 12000,
            "healing": 0,
            "mobs": 5,
            "loot": 0,
            "xp": 5000
        },
        {
            "type": "loot",
            "source": "You",
            "item": "Test Item",
            "credits": 0,
            "timestamp": datetime.now()
        },
        {
            "type": "xp",
            "source": "You",
            "amount": 500,
            "xp_type": "Combat",
            "timestamp": datetime.now()
        }
    ]
    
    print("[TEST] Processing mock events...")
    for event in events:
        app.process_external_event(event)
    
    # Check player_data
    print(f"[TEST] player_data for 'You': {app.player_data.get('You')}")
    print(f"[TEST] player_data for 'Eliemau': {app.player_data.get('Eliemau')}")
    
    # Verify app_start_time is set
    print(f"[TEST] app_start_time: {app.app_start_time}")
    
    # Open secondary windows to check if they populate
    print("[TEST] Opening secondary windows...")
    app.leaderboard_win.show()
    app.details_win.show()
    app.skimmers_win.show()
    
    # Give them a moment to "refresh"
    # In real app this happens via the loop, we'll call it manually
    app.refresh_ui_only(force=True)
    
    # Check if data is present in windows (basic check)
    if hasattr(app, 'leaderboard_win') and app.leaderboard_win:
        print("[TEST] Leaderboard window exists.")
        # We can't easily check the UI content in a non-interactive environment, 
        # but we can check if it passed the 'empty' check
    
    if hasattr(app, 'details_win') and app.details_win:
        print("[TEST] Details window exists.")

    if hasattr(app, 'skimmers_win') and app.skimmers_win:
        print("[TEST] Skimmers window exists.")

    print("[TEST] Test completed successfully.")
    
    # Cleanup
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    try:
        test_full_flow()
    except Exception as e:
        print(f"[TEST] Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
