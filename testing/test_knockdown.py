import time

def test_knockdown_logic():
    knockdown_cooldowns = {}
    
    events = [
        {"type": "dealt", "source": "You", "target": "Turd", "ability": "Fire Knockdown"},
        {"type": "dealt", "source": "Leloglo", "target": "Rehote", "ability": "Knockdown Shot"},
        {"type": "dealt", "source": "Eliemau", "target": "Turd", "ability": "Regular Shot"}, # Should not trigger
        {"type": "dealt", "source": "You", "target": "Slinky", "ability": "Posture Change"}, # Should trigger
        {"type": "dealt", "source": "You", "target": "BigGuy", "ability": "Intimidate"}, # Should trigger
    ]

    now = time.time()
    
    for event in events:
        ability = event.get("ability", "")
        target = event.get("target", "Unknown")
        
        if ability and ("knockdown" in ability.lower() or "posture change" in ability.lower() or "intimidate" in ability.lower()):
            if target and target != "Unknown":
                cur_time = now # Use fixed time for test
                last_kd = knockdown_cooldowns.get(target, 0)
                if cur_time - last_kd > 30:
                    knockdown_cooldowns[target] = cur_time
                    print(f"Cooldown recorded for {target} via {ability}")
                else:
                    print(f"Cooldown ignored for {target} (on cooldown)")

    assert "Turd" in knockdown_cooldowns
    assert "Rehote" in knockdown_cooldowns
    assert "Slinky" in knockdown_cooldowns
    assert "BigGuy" in knockdown_cooldowns
    
    # Try again immediately (should be ignored)
    event2 = {"type": "dealt", "source": "You", "target": "Turd", "ability": "Fire Knockdown"}
    target = event2.get("target")
    ability = event2.get("ability")
    cur_time = now + 5
    last_kd = knockdown_cooldowns.get(target, 0)
    if cur_time - last_kd > 30:
        knockdown_cooldowns[target] = cur_time
    else:
        print(f"Confirmed: {target} ignored at +5s")
        
    assert knockdown_cooldowns["Turd"] == now
    
    # Try again after 31s (should be recorded)
    cur_time = now + 31
    last_kd = knockdown_cooldowns.get(target, 0)
    if cur_time - last_kd > 30:
        knockdown_cooldowns[target] = cur_time
        print(f"Confirmed: {target} recorded at +31s")

    assert knockdown_cooldowns["Turd"] == now + 31

if __name__ == "__main__":
    test_knockdown_logic()
    print("Test passed!")
