import time

def test_poison_logic():
    player_data = {}
    
    events = [
        {"type": "poison", "source": "You", "target": "Turd"},
        {"type": "poison", "source": "You", "target": "Slinky"},
        {"type": "poison", "source": "You", "target": "Turd"},
        {"type": "poison_resist", "target": "Turd"},
    ]

    def process_event(event):
        event_type = event.get("type")
        source = event.get("source", "Unknown")
        target = event.get("target", "Unknown")
        
        if event_type == "poison":
            if source not in player_data:
                player_data[source] = {"poison_hits": 0, "logs": []}
            player_data[source]["poison_hits"] += 1
            player_data[source]["logs"].append(f"Applied poison to {target}")
            print(f"Poison hit recorded for {source} on {target}")

        if event_type == "poison_resist":
            if "You" not in player_data:
                player_data["You"] = {"poison_hits": 0, "logs": []}
            player_data["You"]["logs"].append(f"{target} resisted your poison")
            print(f"Poison resist recorded for {target}")

    for event in events:
        process_event(event)

    assert player_data["You"]["poison_hits"] == 3
    assert len(player_data["You"]["logs"]) == 4 # 3 hits + 1 resist
    
    print("Test passed!")

if __name__ == "__main__":
    test_poison_logic()
