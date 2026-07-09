import os
import time
from datetime import datetime

def test_mtime_behavior():
    log_path = "test_mtime.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    
    print(f"Testing behavior on {log_path}")
    
    # 1. Create file
    with open(log_path, "w") as f:
        f.write("Initial line\n")
        f.flush()
        # os.fsync(f.fileno()) # Force write to disk
    
    mtime1 = os.path.getmtime(log_path)
    size1 = os.path.getsize(log_path)
    print(f"Created: mtime={mtime1}, size={size1}")
    
    time.sleep(0.5)
    
    # 2. Append data
    with open(log_path, "a") as f:
        f.write("New data line\n")
        f.flush()
        # On some systems, mtime might not update yet if handle is open
    
    mtime2 = os.path.getmtime(log_path)
    size2 = os.path.getsize(log_path)
    print(f"Appended: mtime={mtime2}, size={size2}")
    
    if mtime2 == mtime1:
        print("ALERT: mtime did NOT update after append!")
    else:
        print("mtime updated correctly.")
        
    if size2 > size1:
        print("Size updated correctly.")
    else:
        print("ALERT: size did NOT update after append!")

    # 3. Repeat with time.sleep
    time.sleep(1.1)
    with open(log_path, "a") as f:
        f.write("Another line\n")
        f.flush()
        
    mtime3 = os.path.getmtime(log_path)
    size3 = os.path.getsize(log_path)
    print(f"Appended again: mtime={mtime3}, size={size3}")
    
    if os.path.exists(log_path):
        os.remove(log_path)

if __name__ == "__main__":
    test_mtime_behavior()
