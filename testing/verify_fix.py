
import time
import os
import json
import ctypes

PIPE_NAME = r"\\.\pipe\LivyLogsPipe"
TEST_LOG = os.path.join("testing", "test_chatlog.txt")

def verify_test_mode():
    if not os.path.exists("testing"):
        os.makedirs("testing")
        
    print(f"Starting verification...")
    
    # 1. Write some fresh data to the test log
    ts = time.strftime("%H:%M:%S")
    test_lines = [
        f"[Spatial]  {ts} [GROUP] Turd hits a Rebel Colonel for 500 points of damage.\n",
        f"[Spatial]  {ts} [GROUP] You heal Leloglo for 200 points of damage.\n",
        f"[Spatial]  {ts} [GROUP] Leloglo looted 150 credits from a stormtrooper.\n",
        f"[Spatial]  {ts} [GROUP] You have defeated a SpecForce marine.\n",
        f"[Spatial]  {ts} [GROUP] You receive 1000 points of Combat experience.\n"
    ]
    
    with open(TEST_LOG, "a") as f:
        for line in test_lines:
            f.write(line)
        f.flush()
    print(f"Wrote {len(test_lines)} lines to {TEST_LOG}")

    # 2. Try to connect to the pipe and see if we get the data
    import subprocess
    try:
        output = subprocess.check_output("tasklist /FI \"IMAGENAME eq parser.exe\"", shell=True).decode()
    except:
        output = ""
        
    if "parser.exe" not in output:
        print("Engine is not running. Starting it...")
        subprocess.Popen(["parser.exe", TEST_LOG], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(2)

    try:
        kernel32 = ctypes.windll.kernel32
        GENERIC_READ = 0x80000000
        OPEN_EXISTING = 3
        handle = kernel32.CreateFileW(
            PIPE_NAME,
            GENERIC_READ,
            0, None,
            OPEN_EXISTING,
            0, None
        )
        
        if handle == -1:
            print(f"Failed to connect to pipe: {PIPE_NAME}. Error: {kernel32.GetLastError()}")
            return

        print(f"Connected to pipe: {PIPE_NAME}")
        
        # Read for 5 seconds
        start_time = time.time()
        found_types = set()
        buf = ctypes.create_string_buffer(4096)
        read = ctypes.c_ulong(0)
        
        while time.time() - start_time < 5:
            if kernel32.ReadFile(handle, buf, 4095, ctypes.byref(read), None) and read.value > 0:
                data = buf.raw[:read.value].decode('utf-8', errors='ignore')
                for line in data.split('\n'):
                    if line.strip():
                        try:
                            j = json.loads(line)
                            found_types.add(j.get('type'))
                            print(f"Received: {j.get('type')} from {j.get('source', j.get('name', 'Unknown'))}")
                        except:
                            pass
            time.sleep(0.1)
        
        print(f"\nVerification Summary:")
        print(f"Event types found: {found_types}")
        if all(t in found_types for t in ['damage', 'healing', 'loot', 'stats']):
            print("SUCCESS: All core event types detected!")
        else:
            print("PARTIAL: Some types missing.")
            
        kernel32.CloseHandle(handle)
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    verify_test_mode()
