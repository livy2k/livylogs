import time
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath("."))

from radio_manager import RadioManager

def test_interrupt():
    print("Starting Radio Interrupt Test...")
    
    played_files = []
    def status_cb(playing):
        state = "Playing" if playing else "Stopped"
        print(f"Status changed: {state}")

    mgr = RadioManager(status_callback=status_cb)
    
    # Speed up the interval for testing
    mgr.interrupt_interval = 5 # 5 seconds
    
    print(f"Local MP3s found: {mgr.local_mp3s}")
    
    if not mgr.local_mp3s:
        print("No MP3s found in root. Please add some .mp3 files to the root directory for this test.")
        return

    # Mock _stream_thread to not actually connect to internet but test logic
    # Actually, we can just let it run if we have internet, but let's see.
    # We want to verify that _handle_interrupt is called and picks a random file.
    
    mgr.play("181.FM OLDSCHOOL")
    
    start_time = time.time()
    while time.time() - start_time < 20: # Run for 20 seconds
        if mgr.is_interrupting:
            print(f"INTERRUPTING with: {mgr.last_played_mp3}")
            played_files.append(mgr.last_played_mp3)
        time.sleep(1)
    
    mgr.stop()
    print(f"Files played during test: {played_files}")
    
    if len(played_files) > 1:
        # Check no back-to-back same files
        for i in range(len(played_files) - 1):
            if played_files[i] == played_files[i+1]:
                print(f"FAILED: Back-to-back same file {played_files[i]}")
                return
        print("PASSED: No back-to-back repetitions.")
    else:
        print("Test ran but not enough interrupts occurred to verify repetition logic.")

if __name__ == "__main__":
    test_interrupt()
