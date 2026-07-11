import sys
import os
import time
import pygame

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_killstreaks():
    print("Testing KillstreakManager Logic...")
    try:
        from killstreak_manager import KillstreakManager
        
        # Create a dummy SFX folder if needed for testing (but it should exist)
        if not os.path.exists("sfx"):
            os.makedirs("sfx")
            
        mgr = KillstreakManager(sfx_dir="sfx")
        
        print("Simulating 3 kills...")
        mgr.record_kill() # 1
        mgr.record_kill() # 2 (Double kill)
        mgr.record_kill() # 3 (Multi kill & Killing Spree)
        
        print(f" Kill count: {mgr.kill_count}")
        print(f" Multikill count: {mgr.multikill_count}")
        
        if mgr.kill_count != 3 or mgr.multikill_count != 3:
            print("FAILED: Kill counts incorrect.")
            return False
            
        print("Simulating death...")
        mgr.record_death()
        
        if mgr.kill_count != 0 or mgr.multikill_count != 0:
            print("FAILED: Reset after death failed.")
            return False
            
        print("KillstreakManager test passed.")
        return True
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR during killstreak test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_killstreaks():
        sys.exit(0)
    else:
        sys.exit(1)
