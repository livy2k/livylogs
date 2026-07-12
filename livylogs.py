"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import sys
import datetime
import os
import tkinter as tk
from livylogs_main import CombatLogApp
import ctypes
from tkinter import messagebox

def main():
    kernel32 = ctypes.windll.kernel32
    mutex_name = "LivyLogs_SingleInstance_Mutex"
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == 183:
        # Instead of just exiting, let's try to notify the user or just stay silent
        # Since the C engine now kills old processes, if we hit this, it means 
        # another instance started VERY recently or we are being launched manually.
        sys.exit(0)

    try:
        root = tk.Tk()
        app = CombatLogApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_exit)
        root.mainloop()
    except Exception as e:
        import traceback
        import os
        import datetime
        error_msg = f"--- UI CRASH {datetime.datetime.now()} ---\n" + traceback.format_exc()
        print(f"CRITICAL ERROR: {e}")
        try:
            with open("crash_log.txt", "a") as f:
                f.write(error_msg + "\n")
        except: pass
        try:
            messagebox.showerror("LivyLogs Critical Error", f"The application encountered a critical error:\n{e}\n\nSee crash_log.txt for details.")
        except: pass
    finally:
        # Before closing the mutex, try to clean up background processes 
        # in case we are exiting due to an error or manual close
        try:
            import subprocess
            engine_exes = ['parser.exe']
            for proc_name in engine_exes:
                subprocess.run(['taskkill', '/F', '/IM', proc_name, '/T'], 
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

        if 'mutex' in locals() and mutex: kernel32.CloseHandle(mutex)
        try:
            with open("crash_log.txt", "a") as f:
                import datetime
                f.write(f"--- APP EXIT {datetime.datetime.now()} ---\n")
        except: pass

if __name__ == "__main__":
    main()
