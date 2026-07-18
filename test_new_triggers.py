
import time
import json

class MockApp:
    def __init__(self):
        self.player_data = {}
        self.status_cooldowns = {}
        self.char_name = type('obj', (object,), {'get': lambda *args: "IiIiIiIi"})()
        self.player_arrival_order = []
        self.friendly_players = set()
        self.enemy_players = set()

    def _init_player_data(self, target, died=False):
        if target not in self.player_data:
            self.player_data[target] = {
                "status_effects": {},
                "logs": [],
                "knockdown_count": 0,
                "posture_count": 0
            }

    def _trigger_status_effect(self, target, ability_text, status_type_override=None, offset_override=None, event_time=None):
        from utils import normalize_name
        target = normalize_name(target)
        char_name_curr = self.char_name.get()
        if char_name_curr and target.lower() == char_name_curr.lower(): 
            target = "You"

        cur_time = float(event_time) if event_time is not None else time.time()
        status_type = status_type_override
        
        if not status_type and ability_text:
            ability_lower = ability_text.lower()
            if "knockdown" in ability_lower or "knocked down" in ability_lower or "stands up" in ability_lower or "falls down" in ability_lower:
                status_type = "knockdown"
            elif "posture" in ability_lower or "kneel" in ability_lower or "prone" in ability_lower or "kneeling" in ability_lower:
                status_type = "posture"

        if status_type:
            self._init_player_data(target)
            if target not in self.status_cooldowns:
                self.status_cooldowns[target] = {}

            duration = 30
            if offset_override is not None:
                duration = offset_override

            last_time = self.status_cooldowns[target].get(status_type, 0)
            if cur_time - last_time > duration:
                self.status_cooldowns[target][status_type] = cur_time
                self.player_data[target]["status_effects"][status_type] = cur_time
                count_key = f"{status_type}_count"
                self.player_data[target][count_key] = self.player_data[target].get(count_key, 0) + 1
                print(f"Triggered {status_type} on {target} with duration {duration}")

def test_triggers():
    app = MockApp()
    
    # Simulate Engine Events
    events = [
        {"type": "status", "target": "IiIiIiIi", "status": "knockdown", "offset": 27},
        {"type": "status", "target": "SomeTarget", "status": "posture", "offset": 28},
        {"type": "status", "target": "IiIiIiIi", "status": "knockdown", "offset": 27} # Should be on cooldown
    ]
    
    for ev in events:
        target = ev.get("target")
        status = ev.get("status")
        offset = ev.get("offset")
        app._trigger_status_effect(target, "", status_type_override=status, offset_override=offset)

    # Check Results
    you_kd = app.player_data.get("You", {}).get("knockdown_count", 0)
    target_pd = app.player_data.get("SomeTarget", {}).get("posture_count", 0)
    
    print(f"You KD Count: {you_kd}")
    print(f"SomeTarget PD Count: {target_pd}")

    if you_kd == 1 and target_pd == 1:
        print("TEST PASSED")
    else:
        print("TEST FAILED")

def test_event_time_anchor_for_cooldown():
    app = MockApp()

    # First event happens at t=1000 and is accepted.
    app._trigger_status_effect("SomeTarget", "", status_type_override="knockdown", offset_override=29, event_time=1000)

    # Simulate delayed processing by not sleeping and sending an old event first (should stay on cooldown).
    app._trigger_status_effect("SomeTarget", "", status_type_override="knockdown", offset_override=29, event_time=1020)
    assert app.player_data["SomeTarget"]["knockdown_count"] == 1

    # Event timestamp crosses cooldown boundary; should trigger even if processed immediately after prior call.
    app._trigger_status_effect("SomeTarget", "", status_type_override="knockdown", offset_override=29, event_time=1031)
    assert app.player_data["SomeTarget"]["knockdown_count"] == 2

    print("EVENT TIME ANCHOR TEST PASSED")

if __name__ == "__main__":
    test_triggers()
    test_event_time_anchor_for_cooldown()
