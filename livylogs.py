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
import time
import threading
from utils import get_resource_path
from configparser import ConfigParser
from constants import MIN_WIDTH, MIN_HEIGHT

def show_splash():
    # Load settings to match main window's initial position and size
    config = ConfigParser()
    config.read("settings.ini")
    
    width = max(MIN_WIDTH, config.getint("General", "width", fallback=400))
    height = max(MIN_HEIGHT, config.getint("General", "height", fallback=50))
    # Match the 700x400 forced geometry in main app
    width, height = 700, 400
    x = config.get("General", "x", fallback="971")
    y = config.get("General", "y", fallback="92")

    # Attempt to use VLC for video splash if available
    vlc_available = False
    vlc_path = r'C:\Program Files\VideoLAN\VLC'
    if os.path.exists(vlc_path):
        try:
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(vlc_path)
            os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
            import vlc
            vlc_available = True
        except:
            pass

    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="black")
    
    splash.geometry(f"{width}x{height}+{x}+{y}")

    video_played = False
    if vlc_available:
        try:
            import vlc
            # Check multiple potential locations for splash assets
            video_locations = [
                get_resource_path("splash.mp4"),
                os.path.abspath("splash.mp4"),
            ]
            
            video_path = next((p for p in video_locations if os.path.exists(p)), None)
            
            if video_path:
                instance = vlc.Instance("--no-xlib", "--quiet", "--no-video-title-show")
                player = instance.media_player_new()
                player.video_set_aspect_ratio(f"{width}:{height}")
                
                # Embed VLC in Tkinter window
                h = splash.winfo_id()
                if sys.platform == "win32":
                    player.set_hwnd(h)
                else:
                    player.set_xwindow(h)

                # Load and play video
                media = instance.media_new(video_path)
                player.set_media(media)
                player.play()
                
                # Wait for video to finish or 5 seconds max
                start_time = time.time()
                while time.time() - start_time < 5:
                    splash.update()
                    state = player.get_state()
                    if state in [vlc.State.Ended, vlc.State.Error]:
                        break
                    time.sleep(0.01)
                
                video_played = True
                player.stop()
        except Exception as e:
            print(f"VLC Splash Error: {e}")

    if not video_played:
        try:
            from PIL import Image, ImageTk
            img_path = get_resource_path("livylogs.png")
            if not os.path.exists(img_path):
                img_path = get_resource_path("iconbell.jpg")
                
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(splash, image=photo, bg="black")
                label.image = photo
                label.place(x=0, y=0, relwidth=1, relheight=1)
                splash.update()
                time.sleep(2)
            else:
                tk.Label(splash, text="LivyLogs", fg="#00a2ff", bg="black", font=("Segoe UI", 30, "bold")).pack(expand=True, fill=tk.BOTH)
                splash.update()
                time.sleep(2)
        except Exception as e:
            pass

    try:
        splash.destroy()
    except: pass

def main():
    # Show splash screen first
    try:
        show_splash()
    except Exception as e:
        print(f"Splash error: {e}")
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
