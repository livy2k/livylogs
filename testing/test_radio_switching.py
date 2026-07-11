import threading
import time
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from radio_manager import RadioManager

def test_switching():
    print("Testing Radio Switching Stability...")
    
    def callback(is_playing):
        print(f"[UI Callback] Playing: {is_playing}")

    mgr = RadioManager(status_callback=callback)
    
    stations = ["181.FM OLDSCHOOL", "SOMAFM FLUID", "1.FM 80S HITS"]
    
    for station in stations:
        print(f"\n>>> Switching to: {station}")
        mgr.play(station)
        time.sleep(2) # Let it play for a bit
        
    print("\n>>> Rapid switching test...")
    for i in range(5):
        st = stations[i % len(stations)]
        print(f"Rapid switch to: {st}")
        mgr.play(st)
        time.sleep(0.5)

    print("\n>>> Final stop...")
    mgr.stop()
    time.sleep(2)
    print("Test Complete.")

if __name__ == "__main__":
    try:
        test_switching()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Test Error: {e}")
