import sys
import os
import threading
import time
import pygame

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def diag_radio():
    print("--- Radio Diagnostic Start ---")
    try:
        from radio_manager import RadioManager
        
        def status_cb(playing):
            print(f"[STATUS] Radio playing: {playing}")
            
        mgr = RadioManager(status_callback=status_cb)
        
        print("\n1. Testing Stoner SFX Library...")
        if mgr.stoner_lib:
            print("SFX Library found.")
            # Test sequential play
            channel = mgr.stoner_lib.play_next_sequential()
            if channel:
                print("SFX playing...")
                # Wait a bit
                time.sleep(2)
            else:
                print("SFX failed to play (maybe missing files, but should return a channel if logic is okay)")
        else:
            print("SFX Library NOT found.")

        print("\n2. Testing Radio Play (toggle)...")
        # toggle() calls play_random_mp3() if not playing
        # play_random_mp3() plays SFX then transitions to first station
        mgr.toggle()
        
        print("Wait for transition (SFX + startup)...")
        for _ in range(30): # 3 seconds
            if mgr.current_station and mgr.current_station != "Radio Starting...":
                print(f"Station reached: {mgr.current_station}")
                break
            time.sleep(0.1)
        
        if mgr.is_playing:
            print("Radio is officially playing.")
        else:
            print("Radio failed to start playing within timeout.")

        print("\n3. Testing Station Transition...")
        if mgr.is_playing:
            old_station = mgr.current_station
            mgr.next_station()
            print(f"Switched to next station. Current: {mgr.current_station}")
            time.sleep(2)
            if mgr.current_station != old_station:
                print("Station transition success.")
            else:
                print("Station transition failed or same station.")

        print("\n4. Testing Stop...")
        mgr.stop()
        time.sleep(1)
        if not mgr.is_playing:
            print("Radio stopped successfully.")
        else:
            print("Radio failed to stop.")

        print("\n--- Diagnostic Finished ---")
        return True
    except Exception as e:
        import traceback
        print(f"CRITICAL DIAG ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Use a timeout for the whole test to prevent hanging the runner
    test_thread = threading.Thread(target=diag_radio)
    test_thread.start()
    test_thread.join(timeout=60)
    
    if test_thread.is_alive():
        print("TEST FAILED: Hang detected during diagnostic test.")
        sys.exit(1)
    else:
        sys.exit(0)
