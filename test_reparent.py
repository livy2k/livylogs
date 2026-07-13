import tkinter as tk
import subprocess
import time
import win32gui
import win32con
import os

class EmbeddedBrowser(tk.Frame):
    def __init__(self, parent, url):
        tk.Frame.__init__(self, parent, bg="black")
        self.parent = parent
        self.url = url
        self.browser_proc = None
        self.browser_hwnd = None
        
        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.update()
        self.hwnd = self.container.winfo_id()
        
        # Start browser in a new window with a specific title we can find
        # We'll try Chrome first as it's common. 
        # --app flag makes it a "minimal" window without toolbars
        try:
            cmd = [
                "chrome.exe",
                f"--app={self.url}",
                "--new-window",
                "--window-size=800,600"
            ]
            self.browser_proc = subprocess.Popen(cmd)
            
            # Wait for window and capture it
            self.after(1000, self.capture_window)
        except Exception as e:
            print(f"Failed to start Chrome: {e}")

    def capture_window(self):
        def enum_handler(hwnd, lparam):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # Look for Galaxy Harvester in title
                if "Galaxy Harvester" in title:
                    lparam.append(hwnd)
        
        hwnds = []
        win32gui.EnumWindows(enum_handler, hwnds)
        
        if hwnds:
            self.browser_hwnd = hwnds[0]
            # Reparent
            win32gui.SetParent(self.browser_hwnd, self.hwnd)
            
            # Remove title bar and borders from the captured window
            style = win32gui.GetWindowLong(self.browser_hwnd, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION
            style = style & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(self.browser_hwnd, win32con.GWL_STYLE, style)
            
            # Resize to fill container
            self.resize_browser()
            
    def resize_browser(self, event=None):
        if self.browser_hwnd:
            w = self.container.winfo_width()
            h = self.container.winfo_height()
            win32gui.SetWindowPos(self.browser_hwnd, 0, 0, 0, w, h, win32con.SWP_NOZORDER)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    browser = EmbeddedBrowser(root, "https://galaxyharvester.net/ghHome.py?")
    browser.pack(fill=tk.BOTH, expand=True)
    browser.bind("<Configure>", browser.resize_browser)
    root.mainloop()
