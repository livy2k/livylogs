import json
import time

def test_livius_logic():
    # Mocking what the C engine would send
    events = [
        {"type": "chat", "channel": "Groupchat", "source": "Leloglo", "message": "123"},
        {"type": "chat", "channel": "Groupchat", "source": "Eliemau", "message": "hello"},
        {"type": "chat", "channel": "Groupchat", "source": "Fikiosa", "message": "123"},
        {"type": "stats", "name": "Eliemau", "damage": 100, "hits": 1},
        {"type": "stats", "name": "Rehote", "damage": 50, "hits": 1},
        {"type": "stats", "name": "Leloglo", "damage": 200, "hits": 1},
    ]

    friendly_players = set()
    enemy_players = set()
    groupchat_123_players = set()
    player_data = {}
    
    # Simple mock of is_probable_player
    def is_probable_player(name):
        return name not in ["System", "You"]

    for event in events:
        etype = event.get("type")
        if etype == "chat":
            if event.get("channel") == "Groupchat" and event.get("message") == "123":
                source = event.get("source")
                friendly_players.add(source)
                groupchat_123_players.add(source)
                if source in enemy_players:
                    enemy_players.remove(source)
        elif etype == "stats":
            name = event.get("name")
            player_data.setdefault(name, {"damage": 0, "healing": 0})
            player_data[name]["damage"] += event.get("damage", 0)
            player_data[name]["healing"] += event.get("healing", 0)
            if name != "You" and name not in friendly_players and is_probable_player(name):
                enemy_players.add(name)

    def has_output(name):
        d = player_data.get(name, {})
        return d.get("damage", 0) > 0 or d.get("healing", 0) > 0

    visible_friendlies = {
        p for p in friendly_players
        if has_output(p) or p in groupchat_123_players
    }
    visible_enemies = {
        p for p in enemy_players
        if has_output(p)
    }

    print(f"Friendlies: {friendly_players}")
    print(f"Enemies: {enemy_players}")
    
    assert "Leloglo" in friendly_players
    assert "Fikiosa" in friendly_players
    assert "Eliemau" in enemy_players # Sent 'hello', then did damage
    assert "Rehote" in enemy_players
    assert "Leloglo" not in enemy_players

    # Visibility rules requested by user:
    # - 123 groupchat friendlies always visible even with no output
    # - enemies must have done damage or healing to be visible
    assert "Fikiosa" in visible_friendlies
    assert "Leloglo" in visible_friendlies
    assert "Eliemau" in visible_enemies
    assert "Rehote" in visible_enemies

    enemy_players.add("ZeroEnemy")
    player_data["ZeroEnemy"] = {"damage": 0, "healing": 0}
    visible_enemies = {p for p in enemy_players if has_output(p)}
    assert "ZeroEnemy" not in visible_enemies

if __name__ == "__main__":
    test_livius_logic()
    print("Test passed!")
