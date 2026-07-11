import sys
import os
import threading
import time

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_radio_threading():
    print("Testing RadioManager Threading Transitions...")
    try:
        from radio_manager import RadioManager
        mgr = RadioManager()
        
        print("Initial play call...")
        mgr.play("STREET STYLE")
        time.sleep(1)
        
        print("Rapid toggle test (simulating UI interaction)...")
        for i in range(5):
            print(f" Toggle {i+1}")
            mgr.toggle()
            time.sleep(0.5)
            
        print("Play random mp3 transition test...")
        mgr.play_random_mp3()
        time.sleep(2)
        
        print("Stop test...")
        mgr.stop()
        
        print("Threading test finished successfully.")
        return True
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR during threading test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Use a timeout for the whole test to prevent hanging the runner
    test_thread = threading.Thread(target=test_radio_threading)
    test_thread.start()
    test_thread.join(timeout=30)
    
    if test_thread.is_alive():
        print("TEST FAILED: Hang detected during threading test.")
        sys.exit(1)
    else:
        sys.exit(0)
