import os
import tkinter as tk
from PIL import Image, ImageTk

def test_icon_load():
    root = tk.Tk()
    root.withdraw()
    
    icon_path = "iconbell.jpg"
    if not os.path.exists(icon_path):
        print(f"FAILED: {icon_path} not found")
        return

    try:
        img = Image.open(icon_path)
        print(f"SUCCESS: Opened {icon_path} ({img.size}, {img.format})")
        
        resized = img.resize((32, 32), Image.Resampling.LANCZOS)
        print(f"SUCCESS: Resized {icon_path} to 32x32")
        
        photo = ImageTk.PhotoImage(resized)
        print("SUCCESS: Created PhotoImage")
        
        root.iconphoto(True, photo)
        print("SUCCESS: Applied iconphoto to root")
        
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        root.destroy()

if __name__ == "__main__":
    test_icon_load()
