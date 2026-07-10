import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def get_window_info(hwnd):
    if not hwnd: return "None"
    try:
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        return f"HWND: {hwnd:08x}, PID: {pid.value}, Title: '{title}'"
    except:
        return f"HWND: {hwnd:08x}, PID: ?, Title: ?"

def main():
    print("Window Diagnostic Tool started (ctypes version).")
    print("I will log focus changes for 30 seconds.")
    print("Please switch to your game now and stay there for a few seconds.")
    
    last_fg = None
    start_time = time.time()
    
    with open("window_diag.txt", "w") as f:
        while time.time() - start_time < 30:
            fg = user32.GetForegroundWindow()
            if fg != last_fg:
                info = get_window_info(fg)
                timestamp = time.strftime("%H:%M:%S")
                log_line = f"[{timestamp}] FOCUS CHANGE: {info}\n"
                print(log_line.strip())
                f.write(log_line)
                last_fg = fg
                
                f.write("  Relevant Windows:\n")
                
                # Callback for EnumWindows
                def enum_handler(hwnd, lparam):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        if "swgclient" in title or "star wars galaxies" in title or "livylogs" in title:
                            f.write(f"    - {get_window_info(hwnd)}\n")
                    return True

                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
                user32.EnumWindows(EnumWindowsProc(enum_handler), 0)
                f.flush()
            
            time.sleep(0.5)

    print("\nDiagnostic complete. Please send the contents of window_diag.txt")

if __name__ == "__main__":
    main()
