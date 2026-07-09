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
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showwarning("LivyLogs", "Another instance of LivyLogs is already running.")
        temp_root.destroy()
        sys.exit(0)

    try:
        root = tk.Tk()
        app = CombatLogApp(root)
        root.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("LivyLogs Critical Error", f"The application encountered a critical error:\n{e}")
        except: pass
    finally:
        if mutex: kernel32.CloseHandle(mutex)

if __name__ == "__main__":
    main()
