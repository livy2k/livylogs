import time

def test_early_removal():
    status_cooldowns = {}
    
    # Simulate events
    events = [
        {"type": "dealt", "target": "Turd", "ability": "Intimidate"},
        {"type": "status_removed", "target": "Turd", "status": "intimidate"},
    ]

    now = time.time()
    
    def process_event(event, current_time):
        event_type = event.get("type")
        target = event.get("target", "Unknown")
        ability = event.get("ability", "")
        
        # Track statuses
        if ability:
            low_ability = ability.lower()
            status_type = None
            if "knockdown" in low_ability: status_type = "knockdown"
            elif "posture change" in low_ability: status_type = "posture"
            elif "intimidate" in low_ability: status_type = "intimidate"
            
            if status_type and target and target != "Unknown":
                if target not in status_cooldowns:
                    status_cooldowns[target] = {}
                
                last_time = status_cooldowns[target].get(status_type, 0)
                if current_time - last_time > 30:
                    status_cooldowns[target][status_type] = current_time
                    print(f"Recorded {status_type} for {target}")

        # Early removal
        if event_type == "status_removed":
            status_type = event.get("status")
            if target and target != "Unknown" and target in status_cooldowns:
                if status_type in status_cooldowns[target]:
                    del status_cooldowns[target][status_type]
                    print(f"Removed {status_type} for {target} early")

    # 1. Apply intimidate
    process_event(events[0], now)
    assert "Turd" in status_cooldowns
    assert "intimidate" in status_cooldowns["Turd"]
    
    # 2. Remove early
    process_event(events[1], now + 5)
    assert "intimidate" not in status_cooldowns["Turd"]
    print("Success: Intimidate removed early.")

    # 3. Re-apply (should be allowed because it was removed, 
    # but wait - the game has a 30s immunity regardless of visual?)
    # The user said "if someone if knocked down with an icon that has a time to try and treat it as a cooldown players can watch"
    # If the icon is removed early, does it mean they can be intimidated again?
    # Usually "no longer intimidated" means the effect ended.
    # In many games, you can't be re-intimidated until the 30s is up.
    # If I remove it from status_cooldowns, my current logic ALLOWS re-application because last_time will be 0.
    # If I want to keep the immunity but hide the icon, I'd need a separate "active_icons" dict.
    # But the user said "remove the icon", and usually if the icon is gone, the "cooldown" (immunity) is what they are tracking.
    
    process_event({"type": "dealt", "target": "Turd", "ability": "Intimidate"}, now + 10)
    assert "intimidate" in status_cooldowns["Turd"]
    assert status_cooldowns["Turd"]["intimidate"] == now + 10
    print("Success: Re-applied after early removal.")

if __name__ == "__main__":
    test_early_removal()
    print("Test passed!")
