
import ctypes
import json
import time
from datetime import datetime

def send_event(h, event):
    j = json.dumps(event) + "\n"
    data = j.encode('utf-8')
    bytes_written = ctypes.c_ulong(0)
    res = ctypes.windll.kernel32.WriteFile(h, data, len(data), ctypes.byref(bytes_written), None)
    if not res:
        print(f"Failed to write to pipe: {ctypes.windll.kernel32.GetLastError()}")
    else:
        print(f"Sent: {j.strip()}")

def main():
    pipe_path = r"\\.\pipe\LivyLogsPipe"
    
    print(f"Connecting to {pipe_path}...")
    # Wait for pipe
    h = -1
    for i in range(10):
        if ctypes.windll.kernel32.WaitNamedPipeW(pipe_path, 1000):
            h = ctypes.windll.kernel32.CreateFileW(pipe_path, 0x40000000, 0, None, 3, 0, None)
            if h != -1:
                break
        print(f"Retry {i+1}...")
        time.sleep(1)
    
    if h == -1:
        print("Could not connect to pipe. Is LivyLogs running?")
        return

    try:
        # 1. Stats event
        send_event(h, {
            "type": "stats",
            "name": "You",
            "damage": 5000,
            "healing": 1000,
            "taken": 200,
            "hits": 50,
            "mobs": 1,
            "loot": 1,
            "xp": 1000
        })
        
        send_event(h, {
            "type": "stats",
            "name": "Eliemau",
            "damage": 12000,
            "healing": 0,
            "taken": 500,
            "hits": 120,
            "mobs": 5,
            "loot": 0,
            "xp": 5000
        })

        time.sleep(1)

        # 2. Loot event
        send_event(h, {
            "type": "loot",
            "source": "You",
            "item": "Test Item",
            "credits": 0
        })

        # 3. XP event
        send_event(h, {
            "type": "xp",
            "source": "You",
            "amount": 500,
            "xp_type": "Combat"
        })
        time.sleep(0.5)

        # 4. Mobs event
        send_event(h, {
            "type": "mobs",
            "source": "You",
            "target": "Stormtrooper"
        })
        time.sleep(0.5)

        # 5. Dealt event
        send_event(h, {
            "type": "dealt",
            "source": "You",
            "target": "Stormtrooper",
            "damage": 150,
            "ability": "Laser Shot"
        })

        print("Finished sending simulation data.")
        time.sleep(2)

    finally:
        ctypes.windll.kernel32.CloseHandle(h)

if __name__ == "__main__":
    main()
