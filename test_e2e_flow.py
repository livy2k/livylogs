
import json
import time
import os
import sys

# Mock necessary classes to test logic without full Tkinter environment
class MockApp:
    def __init__(self):
        self.player_data = {}
        self.status_cooldowns = {}
        self.char_name_mock = "IiIiIiIi"
        self.bosses = []
        self.combat_active = False
        self.last_combat_time = 0
        self._arrival_order = []

    def _trigger_status_effect(self, target, msg, status_type_override=None, offset_override=0):
        from utils import normalize_name
        target = normalize_name(target)
        if target.lower() == self.char_name_mock.lower(): target = "You"
        
        if target not in self.player_data:
            self.player_data[target] = {"logs": [], "dm_damage": 0, "dm_healing": 0}
            if target not in self._arrival_order: self._arrival_order.append(target)
            
        now = time.time()
        if target not in self.status_cooldowns: self.status_cooldowns[target] = {}
        
        s_type = status_type_override or "unknown"
        # Mirror livylogs_main.py logic: duration is 28
        duration = 28
        if offset_override: duration = offset_override
        
        last_time = self.status_cooldowns[target].get(s_type, 0)
        if now - last_time > duration:
            self.status_cooldowns[target][s_type] = now
            print(f"[TEST] Triggered {s_type} on {target} (Duration: {duration})")

def run_e2e_logic_test():
    print("Running E2E Logic Test (Engine JSON -> UI Data)...")
    app = MockApp()
    
    # Simulating events that would come from parser.exe (offsets now 0 as per my change)
    events = [
        {"type": "status", "target": "You have been knocked down", "status": "knockdown", "offset": 0},
        {"type": "status", "target": "IiIiIiIi", "status": "knockdown", "offset": 0}, # from "stands up"
        {"type": "status", "target": "Queue Fives looks very intimidated by you!", "status": "intimidate", "source": "You", "offset": 0},
        {"type": "status", "target": "a Gundark", "status": "posture", "offset": 0} # from "kneels"
    ]
    
    from utils import normalize_name
    
    for ev in events:
        print(f"\nProcessing Event: {ev}")
        target = ev.get("target", "Unknown")
        status = ev.get("status", "unknown")
        offset = ev.get("offset", 0)
        
        # This mirrors the logic in livylogs_main.py process_external_event
        norm_target = normalize_name(target)
        if norm_target.lower() == app.char_name_mock.lower() or "you" in norm_target.lower():
            norm_target = "You"
            
        app._trigger_status_effect(norm_target, "test msg", status_type_override=status, offset_override=offset)

    print("\nFinal State Check:")
    for player, statuses in app.status_cooldowns.items():
        print(f"Player: {player} | Statuses: {list(statuses.keys())}")
        if player == "You":
            if "knockdown" in statuses: print("  - [PASS] 'You' correctly tracked knockdown")
        if player == "Queue Fives":
            if "intimidate" in statuses: print("  - [PASS] 'Queue Fives' correctly tracked intimidate")
        if player == "Gundark":
            if "posture" in statuses: print("  - [PASS] 'Gundark' correctly tracked posture")

if __name__ == "__main__":
    # Add project root to path for imports
    sys.path.append(os.getcwd())
    run_e2e_logic_test()
