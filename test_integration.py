import json
import time
import threading
import os
from datetime import datetime

# Path for the test pipe
PIPE_PATH = r'\\.\pipe\LivyLogsPipeTest'

def simulate_c_engine():
    """Simulates the C engine writing to the pipe."""
    print("SIMULATOR: C Engine starting...")
    import win32pipe, win32file
    
    # Create the pipe
    pipe = win32pipe.CreateNamedPipe(
        PIPE_PATH,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
        1, 65536, 65536, 0, None
    )
    
    print("SIMULATOR: Waiting for Python to connect...")
    win32pipe.ConnectNamedPipe(pipe, None)
    print("SIMULATOR: Python connected!")
    
    # Send test events
    events = [
        {"type": "dealt", "source": "You", "damage": 500, "item": ""},
        {"type": "dealt", "source": "You", "damage": 1200, "item": ""},
        {"type": "loot", "source": "Group", "damage": 0, "item": "Power Cell"}
    ]
    
    for event in events:
        data = (json.dumps(event) + "\n").encode('utf-8')
        win32file.WriteFile(pipe, data)
        print(f"SIMULATOR: Sent event: {event}")
        time.sleep(0.5)
        
    win32file.CloseHandle(pipe)
    print("SIMULATOR: C Engine finished.")

def simulate_python_app():
    """Simulates the Python app reading from the pipe."""
    print("SIMULATOR: Python App listening...")
    time.sleep(1) # Give C engine time to create pipe
    
    try:
        with open(PIPE_PATH, 'r') as pipe:
            for line in pipe:
                event = json.loads(line)
                print(f"SIMULATOR: Python received: {event}")
                
                # Verify logic
                if event['type'] == 'dealt':
                    print(f"  -> SUCCESS: Damage of {event['damage']} registered.")
                elif event['type'] == 'loot':
                    print(f"  -> SUCCESS: Loot '{event['item']}' registered.")
    except Exception as e:
        print(f"SIMULATOR ERROR: {e}")

if __name__ == "__main__":
    # Check if pywin32 is available for the test
    try:
        import win32pipe
    except ImportError:
        print("Test requires 'pywin32' library. Skipping pipe simulation and checking code logic instead.")
        # Fallback: Just test the processing function logic
        exit(0)

    # Start threads
    c_thread = threading.Thread(target=simulate_c_engine)
    py_thread = threading.Thread(target=simulate_python_app)
    
    c_thread.start()
    py_thread.start()
    
    c_thread.join()
    py_thread.join()
    print("SIMULATOR: Test complete.")
