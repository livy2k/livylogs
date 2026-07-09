import os
import time
import ctypes
from ctypes import wintypes

# Windows constants
GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = -1

kernel32 = ctypes.windll.kernel32

def get_win32_size(path):
    handle = kernel32.CreateFileW(
        path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None
    )
    if handle == INVALID_HANDLE_VALUE:
        return -1
    
    size_high = wintypes.DWORD(0)
    size_low = kernel32.GetFileSize(handle, ctypes.byref(size_high))
    kernel32.CloseHandle(handle)
    return (size_high.value << 32) + size_low

def simulate_swg_logging():
    log_path = "swg_sim.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    
    print(f"Simulating SWG logging to {log_path}")
    print("Writing with buffering... check if win32 size updates.")
    
    # Simulate a process that keeps the file open with buffering
    with open(log_path, "w", buffering=1024*10) as f:
        for i in range(20):
            timestamp = time.strftime("%H:%M:%S")
            line = f"[Spatial]  {timestamp} You attack a target for {i+100} points of damage!\n"
            f.write(line)
            
            # ATTEMPT TO FORCE REFRESH BY OPENING IN ANOTHER PROCESS
            with open(log_path, "r", encoding="utf-8", errors="replace") as f2:
                data = f2.read()
                read_len = len(data)
            
            os_size = os.path.getsize(log_path)
            win32_size = get_win32_size(log_path)
            
            print(f"Iter {i}: os_size={os_size}, win32_size={win32_size}, read_len={read_len}")
            
            time.sleep(0.5)
        
    print("File closed.")
    print(f"Final OS size: {os.path.getsize(log_path)}")
    print(f"Final Win32 size: {get_win32_size(log_path)}")

if __name__ == "__main__":
    simulate_swg_logging()
