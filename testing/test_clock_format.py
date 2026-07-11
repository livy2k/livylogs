
import tkinter as tk
from livylogs_main import CombatLogApp
import time
from datetime import datetime

def test_clock_format():
    root = tk.Tk()
    app = CombatLogApp(root)
    
    # Let the UI initialize
    root.update()
    
    print("Main window initialized.")
    if hasattr(app, 'clock_lbl'):
        current_text = app.clock_lbl.cget("text")
        print(f"Clock text: '{current_text}'")
        
        # Check if it has AM or PM
        if "AM" in current_text or "PM" in current_text:
            print("SUCCESS: Clock has AM/PM.")
        else:
            print("FAIL: Clock does NOT have AM/PM.")
            
        # Check if it's not in 24h format (e.g. doesn't start with 0 if it's single digit hour, or is 1-12)
        # Note: lstrip('0') was used, so '09:00:00 AM' becomes '9:00:00 AM'
        # '13:00:00' should not appear.
        try:
            hour_str = current_text.split(":")[0]
            hour = int(hour_str)
            if 1 <= hour <= 12:
                print(f"SUCCESS: Hour {hour} is in 12-hour range.")
            else:
                print(f"FAIL: Hour {hour} is NOT in 12-hour range.")
        except Exception as e:
            print(f"FAIL: Could not parse hour from '{current_text}': {e}")
    else:
        print("FAIL: clock_lbl not found in app.")
        
    root.destroy()

if __name__ == "__main__":
    test_clock_format()
