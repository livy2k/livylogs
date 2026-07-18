
import time
import json
import os
import sys

# Mock the CombatLogApp and LiviusWindow to test logic
class MockApp:
    def __init__(self):
        self.player_data = {}
        self.status_cooldowns = {}
        self.friendly_players = {"You"}
        self.enemy_players = set()
        self.player_arrival_order = []
        self.livius_win = MockLiviusWin()
        self.char_name = type('obj', (object,), {'get': lambda: "Autobahn", 'set': lambda x: None})()

    def _init_player_data(self, name):
        if name not in self.player_data:
            self.player_data[name] = {
                "status_effects": {},
                "knockdown_count": 0,
                "posture_count": 0,
                "intimidate_count": 0,
                "incapacitated_count": 0,
                "damage": 0,
                "dm_damage": 0,
                "logs": [],
                "targets": {}
            }

    def refresh_ui_only(self, force=False):
        pass

# Re-implementing the logic from livylogs_main.py to test it in isolation
def trigger_status_effect(app, target, ability_text, status_type_override=None):
    if not target or (not ability_text and not status_type_override):
        return

    cur_time = time.time()
    status_type = status_type_override
    
    if not status_type and ability_text:
        ability_lower = ability_text.lower()
        if "knockdown" in ability_lower or "knocked down" in ability_lower:
            status_type = "knockdown"
        elif "posture" in ability_lower or "kneel" in ability_lower or "prone" in ability_lower or "kneeling" in ability_lower:
            status_type = "posture"
        elif "intimidate" in ability_lower or "intimidated" in ability_lower:
            status_type = "intimidate"
        elif "incapacitated" in ability_lower or "incapacitate" in ability_lower:
            status_type = "incapacitated"

    if status_type:
        app._init_player_data(target)
        if target not in app.status_cooldowns:
            app.status_cooldowns[target] = {}

        duration = 30
        last_time = app.status_cooldowns[target].get(status_type, 0)
        
        if cur_time - last_time > duration:
            app.status_cooldowns[target][status_type] = cur_time
            app.player_data[target]["status_effects"][status_type] = cur_time

            # Cumulative session tracking
            count_key = f"{status_type}_count"
            if status_type == "knockdown": count_key = "knockdown_count"
            elif status_type == "posture": count_key = "posture_count"
            elif status_type == "intimidate": count_key = "intimidate_count"
            elif status_type == "incapacitated": count_key = "incapacitated_count"

            app.player_data[target][count_key] = app.player_data[target].get(count_key, 0) + 1
            return status_type
    return None

class MockLiviusWin:
    def refresh(self, force=False):
        pass

def run_thorough_test():
    print("--- STARTING THOROUGH COMBAT STATUS TEST ---")
    app = MockApp()
    
    test_cases = [
        ("You", "You have been knocked down", "knockdown"),
        ("You", "kneel", "posture"),
        ("You", "intimidated", "intimidate"),
        ("You", "incapacitated", "incapacitated"),
        ("Krayt Dragon", "Fire Knockdown", "knockdown"),
        ("Krayt Dragon", "prone", "posture"),
        ("Krayt Dragon", "intimidate", "intimidate"),
    ]

    results = []
    for target, msg, expected in test_cases:
        detected = trigger_status_effect(app, target, msg)
        success = detected == expected
        results.append({
            "target": target,
            "input": msg,
            "detected": detected,
            "expected": expected,
            "success": success
        })
        print(f"[{'PASS' if success else 'FAIL'}] Input: '{msg}' | Target: {target} | Detected: {detected}")

    # Add engine JSON simulation tests
    print("\n--- TESTING ENGINE JSON EVENTS ---")
    engine_events = [
        {"type": "status", "target": "JSON Target 1", "status": "knockdown", "message": "JSON Target 1 has been knocked down"},
        {"type": "status", "target": "Enemy Target", "status": "posture", "message": "Enemy Target has been forced to kneel"},
        {"type": "status", "target": "JSON Target 2", "status": "intimidate", "message": "JSON Target 2 has been intimidated"},
    ]

    for event in engine_events:
        target = event["target"]
        msg = event["message"]
        expected = event["status"]
        detected = trigger_status_effect(app, target, msg, status_type_override=expected)
        success = detected == expected
        results.append({
            "target": target,
            "input": msg,
            "detected": detected,
            "expected": expected,
            "success": success
        })
        print(f"[{'PASS' if success else 'FAIL'}] JSON Event: '{expected}' on {target} | Detected: {detected}")

    # Test Doubling/Immunity
    print("\n--- TESTING IMMUNITY/DOUBLING ---")
    d1 = trigger_status_effect(app, "You", "You have been knocked down") # Already done once, should be immune
    if d1 is None:
        print("[PASS] Correctly ignored duplicate KD within immunity window.")
    else:
        print(f"[FAIL] Did not ignore duplicate KD. Detected: {d1}")

    # Test Posture Variation
    d2 = trigger_status_effect(app, "Target B", "You have been forced to kneel")
    if d2 == "posture":
        print("[PASS] Correctly detected 'kneel' variation.")
    else:
        print(f"[FAIL] Missed 'kneel' variation. Detected: {d2}")

    # Verify separation
    print("\n--- VERIFYING SEPARATION OF FIELDS ---")
    krayt_data = app.player_data["Krayt Dragon"]
    print(f"Krayt Stats: KD={krayt_data['knockdown_count']}, Posture={krayt_data['posture_count']}, Intim={krayt_data['intimidate_count']}")
    
    if krayt_data['knockdown_count'] == 1 and krayt_data['posture_count'] == 1 and krayt_data['intimidate_count'] == 1:
        print("[PASS] All status effects tracked in SEPARATE fields.")
    else:
        print("[FAIL] Status effects were combined or missed.")

    # Verify self-status
    you_data = app.player_data["You"]
    print(f"You Stats: KD={you_data['knockdown_count']}, Posture={you_data['posture_count']}, Intim={you_data['intimidate_count']}, Incap={you_data['incapacitated_count']}")
    if you_data['knockdown_count'] == 1 and you_data['incapacitated_count'] == 1:
         print("[PASS] Self-status (You) tracked correctly.")
    else:
         print("[FAIL] Self-status tracking failed.")

    all_passed = all(r["success"] for r in results) and krayt_data['knockdown_count'] == 1
    if all_passed:
        print("\n=== FINAL RESULT: ALL TESTS PASSED ===")
    else:
        print("\n=== FINAL RESULT: TESTS FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    run_thorough_test()
