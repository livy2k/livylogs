import ctypes
from ctypes import wintypes
import time
import os

kernel32 = ctypes.windll.kernel32

def test_pipe():
    pipe_path = r"\\.\pipe\LivyLogsPipe"
    print(f"Checking for pipe: {pipe_path}")
    
    if not kernel32.WaitNamedPipeW(pipe_path, 10000):
        print("Pipe not found (WaitNamedPipeW failed after 10s).")
        return
    
    print("Pipe found! Attempting to connect...")
    h = kernel32.CreateFileW(
        pipe_path,
        0x80000000, # GENERIC_READ
        0x00000003, # FILE_SHARE_READ | FILE_SHARE_WRITE
        None,
        3,          # OPEN_EXISTING
        0,
        None
    )
    
    if h == -1 or h == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        print(f"Failed to connect to pipe. Error: {err}")
        return
    
    print("Successfully connected to pipe! Waiting for data...")
    
    buf = ctypes.create_string_buffer(65536)
    bytes_read = wintypes.DWORD()
    
    try:
        start_time = time.time()
        while time.time() - start_time < 5:
            if kernel32.ReadFile(h, buf, 65536, ctypes.byref(bytes_read), None) and bytes_read.value > 0:
                data = buf.raw[:bytes_read.value]
                print(f"Received {bytes_read.value} bytes: {repr(data)}")
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        kernel32.CloseHandle(h)
        print("Closed pipe handle.")

if __name__ == "__main__":
    test_pipe()
