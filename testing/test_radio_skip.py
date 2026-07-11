import threading
import time
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from radio_manager import RadioManager

def test_skip():
    print("Testing Radio Skip Functionality...")
    
    def callback(is_playing):
        print(f"[UI Callback] Playing: {is_playing}")

    mgr = RadioManager(status_callback=callback)
    
    # Manually trigger an interrupt for testing
    mgr.local_mp3s = ["Hottest hits.mp3"] # Ensure we have something to play
    
    print("\n>>> Playing station...")
    mgr.play("181.FM OLDSCHOOL")
    time.sleep(2)
    
    print("\n>>> Triggering skip (should go to next station)...")
    mgr.skip()
    time.sleep(2)
    
    # Force an interrupt
    print("\n>>> Forcing interrupt...")
    
    def run_interrupt():
        try:
            mgr._handle_interrupt()
        except Exception as e:
            print(f"Interrupt Thread Error: {e}")
        
    t = threading.Thread(target=run_interrupt)
    t.start()
    time.sleep(2) # Give it a bit more time to start
    
    print("\n>>> Skipping interrupt...")
    mgr.skip()
    
    # Wait for interrupt thread to finish
    t.join(timeout=5)
    print(f"Interrupt thread finished: {not t.is_alive()}")
    
    print("\n>>> Final stop...")
    mgr.stop()
    time.sleep(1)
    print("Test Complete.")

if __name__ == "__main__":
    try:
        test_skip()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Test Error: {e}")
