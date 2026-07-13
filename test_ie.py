import tkinter as tk
import win32com.client
import pythoncom
import time

class WebBrowser(tk.Frame):
    def __init__(self, parent, url):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        
        # Create a container for the IE control
        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # We need the window handle (HWND) of the container
        self.container.update()
        hwnd = self.container.winfo_id()
        
        # Use win32com to create the Internet Explorer control
        # "Shell.Explorer" is the ActiveX control for IE
        try:
            self.ie = win32com.client.Dispatch("Shell.Explorer.2")
            # We need to bind it to the window handle
            # This is tricky in pure Python/Tkinter without a specialized wrapper
            # But let's see if we can just navigate first
            self.ie.Visible = True
            # This usually opens a new window if not embedded properly.
            # To embed, we need IOleObject::SetClientSite etc.
            # However, pypiwin32 doesn't make it trivial to embed in a Tkinter frame directly.
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    browser = WebBrowser(root, "https://www.google.com")
    browser.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
