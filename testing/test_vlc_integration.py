import os
import sys
import time
import threading

# Add VLC to path
vlc_path = r'C:\Program Files\VideoLAN\VLC'
if os.path.exists(vlc_path):
    os.add_dll_directory(vlc_path)

try:
    from radio_manager import RadioManager, SAFE_RAP_STATIONS
    print("RadioManager imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_vlc_radio():
    mgr = RadioManager()
    station = "88.6 ROCK"
    
    print(f"Testing station: {station}")
    mgr.play(station)
    
    # Wait for it to start
    time.sleep(5)
    
    if mgr.is_playing:
        print("Radio is playing successfully!")
        print(f"Current volume: {mgr.volume}")
        
        print("Testing volume change to 50...")
        mgr.set_volume(50)
        time.sleep(2)
        print(f"Volume set to: {mgr.volume}")
        
        print("Testing volume change to 10...")
        mgr.set_volume(10)
        time.sleep(2)
        
        print("Stopping radio...")
        mgr.stop()
        time.sleep(1)
        if not mgr.is_playing:
            print("Radio stopped successfully.")
        else:
            print("Radio failed to stop.")
    else:
        print("Radio failed to start.")

if __name__ == "__main__":
    test_vlc_radio()
