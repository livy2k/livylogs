import json
import time
import socket
import threading

def simulate_pipe():
    # In a real scenario, this would be the C engine writing to the named pipe.
    # For testing, we can simulate the JSON messages that the UI expects.
    
    events = [
        {"type": "stats", "name": "You", "damage": 1000, "healing": 0, "taken": 0, "hits": 10, "misses": 0, "avoided": 0, "aoe": 0, "loot": 0, "mobs": 0, "xp": 0},
        {"type": "xp", "source": "You", "amount": 500, "xp_type": "Combat"},
        {"type": "stats", "name": "You", "damage": 1000, "healing": 0, "taken": 0, "hits": 10, "misses": 0, "avoided": 0, "aoe": 0, "loot": 0, "mobs": 0, "xp": 500},
        {"type": "xp", "source": "You", "amount": 250, "xp_type": "Weapon"},
        {"type": "stats", "name": "You", "damage": 1500, "healing": 0, "taken": 0, "hits": 15, "misses": 0, "avoided": 0, "aoe": 0, "loot": 0, "mobs": 0, "xp": 750},
    ]

    print("Simulating XP events...")
    # Since we can't easily create a Named Pipe that the main app is already trying to create,
    # we can just test the logic by manually calling process_external_event if we were in the same process.
    # But as an external script, we can't do much without the pipe.
    
    # Let's instead verify the parsing logic by creating a mock log file and running a small C-like parser in Python
    # to see if it would extract the right data.
    
    test_lines = [
        "You receive 500 points of Combat experience",
        "You receive 250 points of Weapon experience",
        "You receive 1234 points of General experience"
    ]
    
    for line in test_lines:
        # Simulate C parsing: sscanf(clean + (p_xp - lower) + 12, "%lf", &amount)
        if "You receive " in line and " experience" in line:
            parts = line.split(" ")
            amount = float(parts[2])
            type_name = " ".join(parts[5:-1])
            print(f"Parsed: Amount={amount}, Type={type_name}")

if __name__ == "__main__":
    simulate_pipe()
