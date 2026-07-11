
import time
import win32pipe, win32file, pywintypes
import json

PIPE_NAME = r'\\.\pipe\swg_combat_log'

def monitor_pipe():
    print(f"Connecting to pipe: {PIPE_NAME}")
    while True:
        try:
            handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            if res == 0:
                print(f"SetNamedPipeHandleState return code: {res}")
            
            print("Connected! Waiting for events...")
            
            while True:
                try:
                    resp = win32file.ReadFile(handle, 65536)
                    data = resp[1].decode('utf-8')
                    # Data might contain multiple JSON objects separated by newlines
                    for line in data.strip().split('\n'):
                        if not line.strip(): continue
                        try:
                            event = json.loads(line)
                            etype = event.get("type", "unknown")
                            if etype in ["chat", "poison", "incapacitated", "status_removed", "cooldown", "death", "kill"]:
                                print(f"[{time.strftime('%H:%M:%S')}] {line}")
                            elif etype == "stats":
                                # Only print stats if they have interesting info
                                if event.get("damage", 0) > 0 or event.get("healing", 0) > 0:
                                    print(f"[{time.strftime('%H:%M:%S')}] STATS: {event.get('name')} DMG={event.get('damage')} HEAL={event.get('healing')}")
                        except json.JSONDecodeError:
                            print(f"[{time.strftime('%H:%M:%S')}] Raw (Non-JSON): {line}")
                except pywintypes.error as e:
                    if e.args[0] == 109: # Broken pipe
                        print("Pipe broken, reconnecting...")
                        break
                    else:
                        print(f"Error reading pipe: {e}")
                        break
        except pywintypes.error as e:
            if e.args[0] == 2: # File not found
                print("Pipe not found (is parser.exe running?). Retrying in 2s...")
                time.sleep(2)
            else:
                print(f"Connection error: {e}. Retrying in 2s...")
                time.sleep(2)

if __name__ == "__main__":
    monitor_pipe()
