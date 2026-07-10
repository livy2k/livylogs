import tkinter as tk
from livylogs_main import CombatLogApp
import ctypes
from tkinter import messagebox
import sys

def main():
    kernel32 = ctypes.windll.kernel32
    mutex_name = "LivyLogs_SingleInstance_Mutex"
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == 183:
        sys.exit(0)

    try:
        root = tk.Tk()
        app = CombatLogApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        import os
        error_msg = traceback.format_exc()
        print(f"CRITICAL ERROR: {e}")
        print(error_msg)
        try:
            with open("crash_log.txt", "w") as f:
                f.write(error_msg)
        except: pass
        try:
            messagebox.showerror("LivyLogs Critical Error", f"The application encountered a critical error:\n{e}\n\nSee crash_log.txt for details.")
        except: pass
    finally:
        if mutex: kernel32.CloseHandle(mutex)

if __name__ == "__main__":
    main()
