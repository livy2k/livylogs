import time

def test_status_logic():
    status_cooldowns = {}
    
    events = [
        {"type": "dealt", "source": "You", "target": "Turd", "ability": "Fire Knockdown"},
        {"type": "dealt", "source": "You", "target": "Turd", "ability": "Intimidate"},
        {"type": "dealt", "source": "You", "target": "Slinky", "ability": "Posture Change"},
    ]

    now = time.time()
    
    def process_event(event, current_time):
        ability = event.get("ability", "")
        target = event.get("target", "Unknown")
        if not ability: return
        
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
            else:
                print(f"Ignored {status_type} for {target} (cooldown)")

    # Initial events
    for event in events:
        process_event(event, now)

    assert status_cooldowns["Turd"]["knockdown"] == now
    assert status_cooldowns["Turd"]["intimidate"] == now
    assert status_cooldowns["Slinky"]["posture"] == now
    
    # Try knockdown again for Turd at +5s (should be ignored)
    process_event({"type": "dealt", "target": "Turd", "ability": "Knockdown Shot"}, now + 5)
    assert status_cooldowns["Turd"]["knockdown"] == now
    
    # Try knockdown again for Turd at +31s (should be recorded)
    process_event({"type": "dealt", "target": "Turd", "ability": "Knockdown Shot"}, now + 31)
    assert status_cooldowns["Turd"]["knockdown"] == now + 31
    
    # Verify Intimidate still on original time
    assert status_cooldowns["Turd"]["intimidate"] == now

if __name__ == "__main__":
    test_status_logic()
    print("Test passed!")
