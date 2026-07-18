
import tkinter as tk
import time

def test_focus():
    root = tk.Tk()
    root.withdraw()
    
    # Simulate the app's popout window structure
    parent = tk.Toplevel(root)
    parent.overrideredirect(True)
    parent.geometry("1x1+0+0")
    parent.withdraw()
    
    win = tk.Toplevel(parent)
    win.geometry("300x200+100+100")
    win.overrideredirect(True)
    win.configure(bg="#2c2c2c")
    
    entry_var = tk.StringVar()
    entry = tk.Entry(win, textvariable=entry_var, bg="#1a1a1a", fg="white", insertbackground="white")
    entry.pack(pady=20, padx=20, fill=tk.X)
    
    label = tk.Label(win, text="Try typing here", bg="#2c2c2c", fg="white")
    label.pack()

    def _force_focus(event=None):
        print("Forcing focus...")
        win.lift()
        win.focus_force()
        def _set():
            print("Setting entry focus")
            entry.focus_set()
        win.after(10, _set)

    # Bindings like in the app
    entry.bind("<Button-1>", lambda e: [_force_focus(), entry.focus_set()])
    win.bind("<Button-1>", lambda e: _force_focus())
    
    # Global paste simulation
    def _on_paste(event=None):
        print("Global paste triggered")
        try:
            content = win.clipboard_get()
            entry.insert(tk.INSERT, content)
        except:
            print("Clipboard empty or error")
        return "break"
        
    win.bind("<Control-v>", _on_paste)
    
    # Initial focus
    win.after(200, _force_focus)
    
    # Exit after some time or button
    btn = tk.Button(win, text="Exit Test", command=root.destroy)
    btn.pack(pady=10)
    
    print("Test window opened. Try clicking and typing.")
    root.mainloop()

if __name__ == "__main__":
    # We can't easily run a GUI test in this environment and see it, 
    # but we can verify the code compiles and the logic is sound.
    # test_focus()
    pass
