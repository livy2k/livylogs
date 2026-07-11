import time

def test_incap_and_death():
    player_data = {}
    
    events = [
        {"type": "chat", "source": "Livy", "channel": "Groupchat", "message": "123"},
        {"type": "incapacitated", "target": "Enemy1"},
        {"type": "incapacitated", "target": "Enemy2"},
        {"type": "incapacitated", "target": "Enemy2"},
        {"type": "death", "target": "Enemy1"},
        {"type": "death", "target": "Slinky"},
    ]

    def process_event(event):
        event_type = event.get("type")
        target = event.get("target", "Unknown")
        
        if event_type == "incapacitated":
            if target not in player_data:
                player_data[target] = {"incapacitated_count": 0, "died": False}
            player_data[target]["incapacitated_count"] += 1
            print(f"Incap recorded for {target}, total: {player_data[target]['incapacitated_count']}")

        if event_type == "death":
            if target not in player_data:
                player_data[target] = {"incapacitated_count": 0, "died": True}
            else:
                player_data[target]["died"] = True
            print(f"Death recorded for {target}")

    for event in events:
        process_event(event)

    assert player_data["Enemy1"]["incapacitated_count"] == 1
    assert player_data["Enemy1"]["died"] == True
    assert player_data["Enemy2"]["incapacitated_count"] == 2
    assert player_data["Enemy2"]["died"] == False
    assert player_data["Slinky"]["died"] == True
    
    print("Test passed!")

if __name__ == "__main__":
    test_incap_and_death()
