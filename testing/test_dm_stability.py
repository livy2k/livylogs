import sys
import os
import time
from datetime import datetime, timedelta
import tkinter as tk

# Add the project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_dm_stability():
    print("[TEST] Initializing CombatLogApp...")
    root = tk.Tk()
    root.withdraw() 
    
    app = CombatLogApp(root)
    dm_win = app.damage_meter_win
    dm_win.show(force_open=True)
    
    print("[TEST] Simulating initial combat stats...")
    # Initial stats for You
    stats_event = {
        "type": "stats",
        "name": "You",
        "damage": 5000,
        "hits": 10,
        "misses": 2,
        "taken": 1000,
        "xp": 500
    }
    app.process_external_event(stats_event)
    
    # Force refresh
    dm_win.refresh(force=True)
    
    dmg_text = dm_win.lbl_dmg.cget("text")
    dps_text = dm_win.lbl_dps.cget("text")
    print(f"[TEST] Damage Meter - DMG: {dmg_text}, DPS: {dps_text}")
    
    assert dmg_text.replace(",", "") == "5000", f"Expected 5,000 damage, got {dmg_text}"
    
    print("[TEST] Simulating momentary idle (no new events)...")
    # Simulate a few idle refreshes (ticker)
    for i in range(3):
        time.sleep(0.2)
        dm_win.refresh(force=False)
        curr_dmg = dm_win.lbl_dmg.cget("text")
        print(f"[TEST] Idle Refresh {i+1} - DMG: {curr_dmg}")
        assert curr_dmg.replace(",", "") == "5000", f"Damage dropped to {curr_dmg} during idle!"

    print("[TEST] Simulating combat timeout (30s+ idle)...")
    # Artificially set last_combat_time to be old
    app.last_combat_time = time.time() - (app.time_window_dm + 5)
    
    # Process a minor event (e.g. loot) that shouldn't restart DM damage but might trigger cleanup
    loot_event = {
        "type": "loot",
        "source": "You",
        "target": "an Imperial Trooper", # Needed for NPC heuristic
        "item": "Rusty Spoon",
        "credits": 0,
        "timestamp": datetime.now()
    }
    print(f"DEBUG TEST: app.app_start_time before: {app.app_start_time}")
    print(f"DEBUG TEST: app.last_combat_time: {app.last_combat_time}, now: {time.time()}, diff: {time.time() - app.last_combat_time}")
    app.process_external_event(loot_event)
    print(f"DEBUG TEST: app.app_start_time after: {app.app_start_time}")
    print(f"DEBUG TEST: app.player_data['You']['dm_damage']: {app.player_data['You']['dm_damage']}")
    
    # Wait for any async after() calls if there were any, but here it's synchronous
    dm_win.refresh(force=True)
    curr_dmg = dm_win.lbl_dmg.cget("text")
    print(f"[TEST] After Timeout - DMG: {curr_dmg}")
    # It should be 0 because dm_damage is cleared on timeout in process_external_event
    assert curr_dmg == "0", f"Expected 0 damage after timeout, got {curr_dmg}"

    print("[TEST] Simulating NEW combat after timeout...")
    # New combat event
    new_dmg_event = {
        "type": "dealt",
        "source": "You",
        "target": "an Imperial Trooper",
        "damage": 100,
        "ability": "Attack",
        "timestamp": datetime.now()
    }
    app.process_external_event(new_dmg_event)
    
    dm_win.refresh(force=True)
    curr_dmg = dm_win.lbl_dmg.cget("text")
    print(f"[TEST] New Combat - DMG: {curr_dmg}")
    assert curr_dmg == "100", f"Expected 100 damage for new session, got {curr_dmg}"

    print("[TEST] Stability test passed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    try:
        test_dm_stability()
    except Exception as e:
        print(f"[TEST] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
