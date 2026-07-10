import time
import json
import ctypes
import os
import subprocess

PIPE_NAME = r'\\.\pipe\LivyLogsPipe'
GENERIC_READ = 0x80000000
OPEN_EXISTING = 3

def test_normalization():
    # Start engine in background
    print("Starting engine...")
    engine_proc = subprocess.Popen(['parser.exe', 'testing\\test_chatlog.txt'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    
    time.sleep(2) # Wait for engine to start
    
    print(f"Connecting to pipe: {PIPE_NAME}")
    h_pipe = ctypes.windll.kernel32.CreateFileW(
        PIPE_NAME,
        GENERIC_READ,
        0,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if h_pipe == -1:
        print("Failed to connect to pipe.")
        engine_proc.kill()
        return

    print("Connected!")
    
    buffer = ctypes.create_string_buffer(65536)
    bytes_read = ctypes.c_ulong(0)
    
    found_damage_you = False
    found_you = False
    start_time = time.time()
    
    try:
        while time.time() - start_time < 5: # Run for 5 seconds
            res = ctypes.windll.kernel32.ReadFile(
                h_pipe,
                buffer,
                65535,
                ctypes.byref(bytes_read),
                None
            )
            if res and bytes_read.value > 0:
                data = buffer.raw[:bytes_read.value].decode('utf-8', errors='ignore')
                if "Damage You" in data:
                    found_damage_you = True
                    print(f"FOUND RAW 'Damage You' in pipe data: {data[:100]}...")
                if '"source": "You"' in data or '"target": "You"' in data or '"name": "You"' in data:
                    found_you = True
            time.sleep(0.1)
    finally:
        ctypes.windll.kernel32.CloseHandle(h_pipe)
        engine_proc.kill()

    if found_you and not found_damage_you:
        print("\nSUCCESS: Found 'You' but NO 'Damage You' in engine output.")
    elif found_damage_you:
        print("\nFAILURE: Still found 'Damage You' in engine output.")
    else:
        print("\nINCONCLUSIVE: Did not find 'You' or 'Damage You'. Check if test log has player data.")

if __name__ == "__main__":
    test_normalization()
