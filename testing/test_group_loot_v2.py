import time
import tkinter as tk
from datetime import datetime
from livylogs_main import CombatLogApp

def test_group_loot_updated():
    root = tk.Tk()
    app = CombatLogApp(root)
    
    group_member = "Artoo Detoo"
    group_looter = "Han Solo"
    group_member_npc_name = "trooper"
    
    # 1. Simulate group member (Artoo) doing damage - should be marked as player
    event_dmg = {
        "type": "dealt",
        "source": group_member,
        "target": "Stormtrooper",
        "damage": 100,
        "ability": "Zap",
        "timestamp": datetime.now()
    }
    app.process_external_event(event_dmg)
    
    # Give Artoo some loot too, otherwise he won't show in LOOT tab
    app.process_external_event({
        "type": "loot", "source": group_member, "item": "Droid Oil", "target": "Stormtrooper", "timestamp": datetime.now()
    })
    
    # 2. Simulate [group] loot event for a new player who hasn't fought - should be marked as player
    event_group_loot = {
        "type": "loot",
        "source": f"[group] {group_looter}",
        "item": "Kessel Spice",
        "target": "Crate",
        "timestamp": datetime.now()
    }
    app.process_external_event(event_group_loot)
    
    # 3. Simulate "trooper" doing damage - should be marked as player despite name
    event_dmg_npc = {
        "type": "dealt",
        "source": group_member_npc_name,
        "target": "Rebel",
        "damage": 50,
        "ability": "Blaster",
        "timestamp": datetime.now()
    }
    app.process_external_event(event_dmg_npc)
    
    # Give trooper loot
    app.process_external_event({
        "type": "loot", "source": group_member_npc_name, "item": "Blaster Bolt", "target": "Rebel", "timestamp": datetime.now()
    })

    print(f"Known Players: {app.known_players}")
    
    # Check Skimmers Window
    app.skimmers_win.show()
    app.skimmers_win.refresh(force=True)
    
    players_in_skimmers = list(app.skimmers_win._row_frames.keys())
    print(f"Players in Skimmers: {players_in_skimmers}")
    
    success = True
    for p in [group_member, group_looter, group_member_npc_name]:
        if p in players_in_skimmers:
            print(f"SUCCESS: {p} found in Skimmers.")
        else:
            print(f"FAIL: {p} NOT found in Skimmers.")
            success = False

    if success:
        print("\nALL Group and Combatant tests passed!")
    
    root.destroy()

if __name__ == "__main__":
    test_group_loot_updated()
