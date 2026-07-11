import os
import sys
import time
import threading

# Add VLC to path
vlc_path = r'C:\Program Files\VideoLAN\VLC'
if os.path.exists(vlc_path):
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(vlc_path)
    os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']

try:
    from radio_manager import RadioManager, SAFE_RAP_STATIONS
    print("RadioManager imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_metadata():
    mgr = RadioManager()
    station = "RNS 420AM"
    
    print(f"Testing station: {station}")
    mgr.play(station)
    
    # Wait for it to start and fetch metadata
    for i in range(15):
        time.sleep(1)
        if mgr.current_song_name:
            print(f"Metadata found: {mgr.current_song_name}")
            break
        print(f"Waiting... ({i+1}/15)")
    
    if mgr.is_playing:
        print("Radio is playing successfully!")
        time.sleep(2)
        mgr.stop()
        print("Radio stopped.")
    else:
        print("Radio failed to start.")

if __name__ == "__main__":
    test_metadata()
