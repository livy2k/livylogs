import time
import json
import ctypes
import os

PIPE_NAME = r'\\.\pipe\LivyLogsPipe'
GENERIC_READ = 0x80000000
OPEN_EXISTING = 3

def verify_engine():
    print(f"Connecting to pipe: {PIPE_NAME}")
    while True:
        h_pipe = ctypes.windll.kernel32.CreateFileW(
            PIPE_NAME,
            GENERIC_READ,
            0,
            None,
            OPEN_EXISTING,
            0,
            None
        )
        if h_pipe != -1:
            print("Connected to pipe!")
            break
        print("Waiting for pipe...")
        time.sleep(1)

    buffer = ctypes.create_string_buffer(65536)
    bytes_read = ctypes.c_ulong(0)
    
    event_counts = {}

    try:
        while True:
            res = ctypes.windll.kernel32.ReadFile(
                h_pipe,
                buffer,
                65535,
                ctypes.byref(bytes_read),
                None
            )
            if res and bytes_read.value > 0:
                data = buffer.raw[:bytes_read.value].decode('utf-8', errors='ignore')
                lines = data.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    try:
                        event = json.loads(line)
                        etype = event.get('type')
                        event_counts[etype] = event_counts.get(etype, 0) + 1
                        
                        # Print some samples
                        if etype in ['dealt', 'loot', 'xp', 'mobs', 'healing']:
                            print(f"Sample {etype}: {line}")
                    except:
                        # Might be a partial line or non-json
                        pass
            else:
                print("Pipe closed or read error.")
                break
            
            # Print counts every few reads
            print(f"Current Counts: {event_counts}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        ctypes.windll.kernel32.CloseHandle(h_pipe)

if __name__ == "__main__":
    verify_engine()
