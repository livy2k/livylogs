import tkinter as tk
from datetime import datetime
from livylogs_main import CombatLogApp
import os

def test_acklay():
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # 1. Ensure "Acklay" is in bosses
    if "acklay" not in app.bosses:
        app.bosses.append("acklay")
    
    now = datetime.now()
    
    events = [
        # Boss: "Acklay" - Should be in player_data
        {"type": "dealt", "source": "Acklay", "target": "You", "damage": 1000, "healing": 0, "timestamp": now},
        # Regular mob: "an Acklay" - Should be filtered (NPC)
        {"type": "dealt", "source": "an Acklay", "target": "You", "damage": 100, "healing": 0, "timestamp": now},
        # Player damage to boss
        {"type": "dealt", "source": "You", "target": "Acklay", "damage": 5000, "healing": 0, "timestamp": now}
    ]
    
    app.process_events_for_ui(events)
    
    print("Player Data Keys:", list(app.player_data.keys()))
    
    boss_key = "Acklay"
    if boss_key in app.player_data:
        print(f"SUCCESS: '{boss_key}' found in player_data.")
    else:
        print(f"FAIL: '{boss_key}' NOT found in player_data. Keys: {list(app.player_data.keys())}")
        
    # Check if 'an Acklay' was filtered
    # It would be cleaned to 'Acklay' if it were treated as an NPC, but it should NOT be in player_data
    # Unless it matched the boss list. 
    # BUT "an Acklay" lowercased is "an acklay", which is NOT in the boss list ["acklay"].
    # So is_src_npc will be True for "an Acklay".
    # And is_src_boss will be False for "an Acklay" (because "an acklay" != "acklay").
    
    found_npc = any("an Acklay" in k for k in app.player_data.keys())
    if not found_npc:
        print("SUCCESS: 'an Acklay' correctly filtered out of player_data.")
    else:
        print("FAIL: 'an Acklay' found in player_data!")

    root.destroy()

if __name__ == "__main__":
    test_acklay()
