import sys
import os
import time
from datetime import datetime, timedelta

# Mock dependencies
PANEL_DARK = "#1a1a1a"
TEXT_SECONDARY = "#aaaaaa"
TEXT_PRIMARY = "#ffffff"
ACCENT_BLUE = "#00a0ff"
WINDOW_BG = "#121212"

def clean_npc_name(name):
    if name.lower().startswith("corpse of "): name = name[10:]
    if " (" in name: name = name.split(" (")[0]
    if name.lower().startswith("a "): name = name[2:]
    if name.lower().startswith("an "): name = name[3:]
    return name

class MockApp:
    def __init__(self):
        self.running = True
        self.all_events = []
        self.player_data = {}
        self.locally_seen_players = {}
        self.loot_data = {}
        self.inventory_full = False
        self.app_start_time = datetime.now() - timedelta(seconds=10)
        self.time_window_skimmers = 5
        self.time_window_details = 5
        self.last_sk_reset = None
        self.last_dt_reset = None
        self.last_dm_reset = None
        self.last_lb_reset = None
        self.char_name = type('obj', (object,), {'get': lambda: "MyChar"})()
        self.leaderboard_cat = "damage"

    def process_events_for_ui(self, all_events):
        # Updated with the fix from livylogs_main.py
        now_dt = datetime.now()
        sk_limit = now_dt - timedelta(minutes=self.time_window_skimmers)
        dt_limit = now_dt - timedelta(minutes=self.time_window_details)
        
        new_player_data = {}
        new_loot_data = {}
        
        active_ids = set(id(e) for e in all_events if self.app_start_time and e["timestamp"] and e["timestamp"] >= self.app_start_time)

        for e in all_events:
            ts = e["timestamp"]
            if not ts: continue
            
            src_raw = e["source"].capitalize(); src_raw = "You" if src_raw.lower() == "you" else src_raw
            tgt_raw = e["target"].capitalize(); tgt_raw = "You" if tgt_raw.lower() == "you" else tgt_raw
            
            is_src_npc = " (" in src_raw or src_raw.lower().startswith(("a ", "an ", "your target"))
            is_tgt_npc = " (" in tgt_raw or tgt_raw.lower().startswith(("a ", "an ", "your target"))
            
            src = clean_npc_name(src_raw) if is_src_npc else src_raw
            tgt = clean_npc_name(tgt_raw) if is_tgt_npc else tgt_raw

            is_skimmer_relevant = ts >= sk_limit and (not self.last_sk_reset or ts >= self.last_sk_reset)
            is_details_relevant = ts >= dt_limit and (not self.last_dt_reset or ts >= self.last_dt_reset)
            is_dm_relevant = id(e) in active_ids and (not self.last_dm_reset or ts >= self.last_dm_reset)
            is_lb_relevant = (not self.last_lb_reset or ts >= self.last_lb_reset)

            if not (is_skimmer_relevant or is_details_relevant or is_dm_relevant or is_lb_relevant):
                continue

            if e["type"] == "loot":
                if is_skimmer_relevant:
                    if src not in new_loot_data: new_loot_data[src] = []
                    new_loot_data[src].append({"item": e["item"], "target": e["target"], "timestamp": ts})
                if is_lb_relevant:
                    if src not in new_player_data: new_player_data[src] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "targets": {}, "aoe_hits": 0}
                    new_player_data[src]["lb_loot"] += 1
                continue
            
            if not is_src_npc:
                if src not in new_player_data: new_player_data[src] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "targets": {}, "aoe_hits": 0}
                if is_dm_relevant:
                    new_player_data[src]["dm_damage"] += e["damage"]
                if is_lb_relevant:
                    new_player_data[src]["damage"] += e["damage"]
            
            tgt_check = tgt_raw
            if e["damage"] > 0 or e.get("is_mitigated"):
                if tgt_check == "You" or not is_tgt_npc:
                    if tgt_check not in new_player_data: new_player_data[tgt_check] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "targets": {}, "aoe_hits": 0}
                    if is_dm_relevant:
                        new_player_data[tgt_check]["dm_taken"] = new_player_data[tgt_check].get("dm_taken", 0) + e["damage"]
                elif is_lb_relevant:
                    if tgt_check not in new_player_data: new_player_data[tgt_check] = {"damage": 0, "healing": 0, "logs": [], "died": False, "dm_damage": 0, "dm_healing": 0, "lb_loot": 0, "targets": {}, "aoe_hits": 0}

        self.player_data = new_player_data
        self.loot_data = new_loot_data

        self.player_data = new_player_data
        self.loot_data = new_loot_data

def test_repro():
    app = MockApp()
    ts = datetime.now()
    events = [
        {"type": "dealt", "source": "You", "target": "a Gundark", "damage": 100, "timestamp": ts, "healing": 0},
        {"type": "dealt", "source": "Player2", "target": "a Gundark", "damage": 150, "timestamp": ts, "healing": 0},
        {"type": "loot", "source": "You", "target": "a Gundark", "item": "credits", "timestamp": ts, "damage": 0, "healing": 0},
    ]
    app.process_events_for_ui(events)
    print(f"Player data: {app.player_data.keys()}")
    print(f"You damage: {app.player_data.get('You', {}).get('damage')}")
    print(f"Player2 damage: {app.player_data.get('Player2', {}).get('damage')}")
    print(f"You lb_loot: {app.player_data.get('You', {}).get('lb_loot')}")

if __name__ == "__main__":
    test_repro()
