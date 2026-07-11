import miniaudio
import time
import urllib.request

def play_bare_stream():
    url = "http://listen.181fm.com/181-oldschool_128k.mp3"
    print(f"Connecting to: {url}")
    
    try:
        # Use miniaudio to stream directly from a URL response
        # Note: miniaudio.stream_any/stream_file usually expect a file-like object
        # We'll use a simple wrapper or just let miniaudio try to handle the stream
        
        response = urllib.request.urlopen(url)
        print("Response opened, starting miniaudio playback...")
        
        # Wrap the response to satisfy miniaudio's internal expectations
        class MiniaudioWrapper:
            def __init__(self, source):
                self.source = source
                self.error_in_readcallback = None
            def read(self, n):
                return self.source.read(n)
            def close(self):
                return self.source.close()

        import io
        data = response.read(1024 * 1024) # Read 1MB of the stream into memory
        print(f"Read {len(data)} bytes of stream data.")
        stream_data = io.BytesIO(data)
        
        stream = miniaudio.stream_any(stream_data) 
        
        with miniaudio.PlaybackDevice() as device:
            device.start(stream)
            print("Playback started. Listening for 10 seconds...")
            time.sleep(10)
            device.stop()
            
    except Exception as e:
        print(f"Error during bare playback: {e}")
    finally:
        print("Bare test complete.")

if __name__ == "__main__":
    play_bare_stream()
