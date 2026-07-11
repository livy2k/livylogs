
import time
import json
import win32file
import win32pipe
import threading
import os

PIPE_NAME = r'\\.\pipe\LivyLogsPipe'

def send_event(pipe, event):
    data = json.dumps(event) + "\n"
    win32file.WriteFile(pipe, data.encode('utf-8'))

def test_session_persistence():
    print("Starting session persistence test...")
    # Create the pipe
    try:
        pipe = win32pipe.CreateNamedPipe(
            PIPE_NAME,
            win32pipe.PIPE_ACCESS_OUTBOUND,
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
            1, 65536, 65536, 0, None
        )
    except Exception as e:
        print(f"Failed to create pipe: {e}")
        return

    print("Pipe created, waiting for connection...")
    win32pipe.ConnectNamedPipe(pipe, None)
    print("Connected!")

    # 1. Start combat
    print("Simulating combat 1...")
    send_event(pipe, {"type": "dealt", "source": "You", "target": "Stormtrooper", "damage": 1000, "ability": "Strike"})
    time.sleep(1)
    
    # Send stats update (engine-like sync)
    send_event(pipe, {"type": "stats", "name": "You", "damage": 1000, "healing": 0})
    time.sleep(1)

    # 2. Let combat timeout (5 seconds)
    print("Waiting for combat timeout (6s)...")
    time.sleep(6)

    # 3. Check stats (In real app we would check UI, here we simulate another event)
    # If the app correctly kept session data, 'damage' for You should still be 1000.
    # We send a new combat event.
    print("Simulating combat 2...")
    send_event(pipe, {"type": "dealt", "source": "You", "target": "Stormtrooper", "damage": 500, "ability": "Strike"})
    time.sleep(1)
    
    # Engine sends new session stats (1500 total)
    send_event(pipe, {"type": "stats", "name": "You", "damage": 1500, "healing": 0})
    time.sleep(1)

    print("Test events sent. Please check the Leaderboard/Details windows.")
    print("Leaderboard should show 1,500 damage.")
    print("Damage Meter should show 500 damage (for the current encounter).")
    
    time.sleep(5)
    win32file.CloseHandle(pipe)

if __name__ == "__main__":
    test_session_persistence()
