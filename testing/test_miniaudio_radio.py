import miniaudio
import requests
import threading
import time

def stream_radio(url):
    print(f"Streaming from {url}...")
    try:
        # We need a generator that yields raw bytes from the response
        response = requests.get(url, stream=True)
        
        # miniaudio.stream_any allows us to decode various formats from a generator
        # It expects a generator that yields blocks of bytes
        def source_generator():
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk

        # Create a decoder from the generator
        # stream_any detects the format (MP3, etc) automatically
        with miniaudio.stream_any(source_generator(), "mp3") as stream:
            device = miniaudio.PlaybackDevice()
            device.start(stream)
            print("Playing... (will stop in 5s)")
            time.sleep(5)
            device.stop()
            print("Stopped.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with one of the stations
    test_url = "http://ice1.181fm.com/181-oldschool_128k.mp3"
    t = threading.Thread(target=stream_radio, args=(test_url,))
    t.start()
    t.join()
