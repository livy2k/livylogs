
import time
import numpy as np
import miniaudio
import threading
from radio_manager import SAFE_RAP_STATIONS, RadioStreamMixer

def monitor_audio_stream(station_name):
    print(f"Starting real-time monitoring for station: {station_name}")
    url = SAFE_RAP_STATIONS[station_name]
    print(f"URL: {url}")
    
    # Stats for monitoring
    callback_times = []
    chunk_sizes = []
    gaps = []
    
    last_callback_time = None
    
    def monitoring_wrapper(mixer):
        class MonitoredMixer:
            def __iter__(self): return self
            def __next__(self): return self.send(None)
            def send(self, framecount):
                nonlocal last_callback_time
                start_time = time.perf_counter()
                
                # Record timing between callbacks
                if last_callback_time is not None:
                    gaps.append(start_time - last_callback_time)
                
                # Call actual mixer
                try:
                    chunk = mixer.send(framecount)
                except Exception as e:
                    print(f"\nMixer Error in callback: {e}")
                    return b""
                
                # If we get an empty chunk, report it immediately to see if it's frequent
                if len(chunk) == 0:
                    print(".", end="", flush=True)

                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # Record processing duration and size
                callback_times.append(duration)
                chunk_sizes.append(len(chunk))
                last_callback_time = end_time
                
                return chunk
        return MonitoredMixer()

    try:
        print("Connecting to stream with BufferedStreamSource (Transcoding Enabled)...")
        from radio_manager import BufferedStreamSource, RadioStreamMixer
        import miniaudio
        import time
        import numpy as np
        import io
        
        with BufferedStreamSource(url) as source:
            print("Connected and Pre-buffering (Wait for 15s of PCM)...")
            
            # 15s of 44.1kHz 16bit Stereo PCM = 2,646,000 bytes
            target_prebuffer = 2646000
            start_wait = time.time()
            
            while source.current_buffer_fill < target_prebuffer and not source.error:
                print(f"Buffering: {source.current_buffer_fill/1024:.1f} KB / 2584 KB", end="\r")
                time.sleep(0.1)
                if time.time() - start_wait > 45: break
            
            print("\nBuffering complete. Starting playback.")
            
            def raw_pcm_gen():
                while True:
                    chunk = source.read(4096)
                    if not chunk:
                        time.sleep(0.01)
                        continue
                    yield chunk
            stream = raw_pcm_gen()
            
            audio_fmt = miniaudio.SampleFormat.SIGNED16
            mixer = RadioStreamMixer(stream, audio_fmt)

            # Wrap the mixer.send with our monitor
            monitored_send = monitoring_wrapper(mixer)
            
            print("Starting playback device...")
            with miniaudio.PlaybackDevice(
                output_format=audio_fmt,
                nchannels=2,
                sample_rate=44100,
                buffersize_msec=2000
            ) as device:
                device.start(monitored_send)
                print("Monitoring active. Listening for 5 seconds...")
                time.sleep(5)
                device.stop()
                print("\nMonitoring finished.")
                
    except Exception as e:
        print(f"Monitor Error: {e}")
        return

    if not callback_times:
        print("No audio data captured.")
        return

    # Analysis
    avg_proc_time = np.mean(callback_times)
    max_proc_time = np.max(callback_times)
    avg_gap = np.mean(gaps) if gaps else 0
    max_gap = np.max(gaps) if gaps else 0
    empty_chunks = sum(1 for size in chunk_sizes if size == 0)
    
    print("\n--- Audio Performance Report ---")
    print(f"Total callbacks: {len(callback_times)}")
    print(f"Average processing time: {avg_proc_time:.6f}s")
    print(f"Max processing time: {max_proc_time:.6f}s")
    print(f"Average time between callbacks: {avg_gap:.6f}s")
    print(f"Max time between callbacks: {max_gap:.6f}s")
    print(f"Empty chunks (underruns): {empty_chunks}")
    
    # Threshold check: 44100Hz, 16bit, 2ch -> 176400 bytes/sec
    # A typical framecount might be 1024 frames -> 4096 bytes.
    # 4096 / 176400 = 0.023s (expected interval)
    
    if empty_chunks > 0:
        print("ALERT: Detected empty chunks. The source is not providing data fast enough.")
    if max_proc_time > 0.01: # Should take well under 10ms
        print("ALERT: Some callbacks took too long to process (potential CPU bottleneck).")
    if max_gap > 0.1: # Significant pause
        print("ALERT: Large gap between audio callbacks detected.")

if __name__ == "__main__":
    # Test with one of the stations
    station = list(SAFE_RAP_STATIONS.keys())[0]
    monitor_audio_stream(station)
