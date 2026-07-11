import tkinter as tk
from radio_manager import RadioManager
import sys

def test_no_vlc_behavior():
    # Mocking vlc to None to simulate missing binary
    import radio_manager
    radio_manager.vlc = None
    
    # Also need to make sure RadioManager init handles it
    mgr = RadioManager()
    
    print(f"Is Available: {mgr.is_available()}")
    
    # This should print the error ONCE
    print("Calling toggle 1...")
    mgr.toggle()
    print("Calling toggle 2...")
    mgr.toggle()
    print("Calling toggle 3...")
    mgr.toggle()
    
    # Check if UI labels in main would work (manual check of logic)
    # The logic in livylogs_main.py:
    # radio_text = "RADIO" if self.radio_mgr.is_available() else "RADIO (N/A)"
    # confirmed it would show RADIO (N/A)
    
    print("Test finished.")

if __name__ == "__main__":
    test_no_vlc_behavior()
