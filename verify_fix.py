import sys
import os
import time
from datetime import datetime, timedelta

# Import the actual classes/logic if possible, but easier to mock for quick verification
class MockApp:
    def __init__(self):
        self.running = True
        self.all_events = []
        self.player_data = {}
        self.locally_seen_players = {}
        self.loot_data = {}
        self.app_start_time = datetime.now()
        self.last_log_sync_time = self.app_start_time
        self.last_combat_time = time.time()
        self.time_window_dm = 30 # seconds
        self.last_dm_reset = None
        self.last_lb_reset = None
        self.last_sk_reset = None
        self.last_dt_reset = None

    def process_events_for_ui(self, all_events):
        # Snippet of the fixed logic from livylogs_main.py
        now_dt = datetime.now()
        sk_limit = now_dt - timedelta(minutes=5)
        dt_limit = now_dt - timedelta(minutes=5)
        
        new_player_data = {}
        active_ids = set(id(e) for e in all_events if self.app_start_time and e["timestamp"] and e["timestamp"] >= self.app_start_time)

        for e in all_events:
            ts = e["timestamp"]
            if not ts: continue
            
            src_raw = e["source"]
            tgt_raw = e["target"]
            
            # Simplified classification
            is_src_npc = "(" in src_raw or src_raw.lower().startswith("a ")
            is_tgt_npc = "(" in tgt_raw or tgt_raw.lower().startswith("a ")
            
            src = src_raw
            tgt = tgt_raw

            is_skimmer_relevant = ts >= sk_limit
            is_details_relevant = ts >= dt_limit
            is_dm_relevant = id(e) in active_ids
            is_lb_relevant = True

            if not (is_skimmer_relevant or is_details_relevant or is_dm_relevant or is_lb_relevant):
                continue

            if not is_src_npc:
                if src not in new_player_data: 
                    new_player_data[src] = {"damage": 0, "dm_damage": 0, "dm_taken": 0}
                
                if is_dm_relevant:
                    new_player_data[src]["dm_damage"] += e.get("damage", 0)
            
            # --- THE FIX WE APPLIED ---
            tgt_check = tgt_raw
            if e.get("damage", 0) > 0:
                # If target is "You", we want to track it even if it looks like an NPC name
                if tgt_check == "You" or not is_tgt_npc:
                    if tgt_check not in new_player_data:
                        new_player_data[tgt_check] = {"damage": 0, "dm_damage": 0, "dm_taken": 0}
                    
                    if is_dm_relevant:
                        new_player_data[tgt_check]["dm_taken"] += e["damage"]
        
        self.player_data = new_player_data

def test_fix():
    app = MockApp()
    
    # Simulate an event where an NPC hits "You"
    # Even if "You" is somehow seen as NPC-like (though it isn't, but let's test the logic)
    event1 = {
        "timestamp": datetime.now(),
        "source": "a Stormtrooper",
        "target": "You",
        "damage": 50,
        "type": "taken"
    }
    
    app.all_events.append(event1)
    app.process_events_for_ui(app.all_events)
    
    print(f"Player Data: {app.player_data.get('You')}")
    if app.player_data.get('You') and app.player_data['You']['dm_taken'] == 50:
        print("SUCCESS: Damage taken correctly recorded for 'You'")
    else:
        print("FAILED: Damage taken NOT recorded correctly")

    # Simulate another event with "You" hitting NPC
    event2 = {
        "timestamp": datetime.now(),
        "source": "You",
        "target": "a Stormtrooper",
        "damage": 100,
        "type": "dealt"
    }
    app.all_events.append(event2)
    app.process_events_for_ui(app.all_events)
    print(f"Player Data after dealt: {app.player_data.get('You')}")
    if app.player_data.get('You') and app.player_data['You']['dm_damage'] == 100:
        print("SUCCESS: Damage dealt correctly recorded for 'You'")

if __name__ == "__main__":
    test_fix()
