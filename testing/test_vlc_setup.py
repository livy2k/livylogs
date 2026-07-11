import os
import sys

# Try to point directly to VLC
vlc_path = r'C:\Program Files\VideoLAN\VLC'
if os.path.exists(vlc_path):
    os.add_dll_directory(vlc_path)
    os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']

try:
    import vlc
    print("VLC module imported successfully!")
    instance = vlc.Instance()
    print("VLC Instance created!")
except Exception as e:
    print(f"Failed to import/init VLC: {e}")
    import traceback
    traceback.print_exc()
