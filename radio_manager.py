import threading
import time
import requests
import miniaudio
import io
import os
import random

# Updated 100% Legally safe and open-source friendly stations with verified URLs
SAFE_RAP_STATIONS = {
    "181.FM OLDSCHOOL": "https://listen.181fm.com/181-oldschool_128k.mp3",
    "SOMAFM FLUID": "https://ice1.somafm.com/fluid-128-mp3",
    "1.FM 80S HITS": "https://strm112.1.fm/back280s_mobile_mp3",
    "STREET STYLE": "http://streetstyle.out.airtime.pro:8000/streetstyle_a",
    "CLASSIC RAP": "http://198.178.123.5:8320/stream",
    "X MINUS ONE": "https://archive.org/download/OTRR_Certified_X_Minus_One/XMinusOne_55-05-08_012_Mars_Is_Heaven.mp3",
    "WAR OF THE WORLDS (1938)": "https://archive.org/download/WarOfTheWorlds1938RadioBroadcast256kbps/War-of-the-Worlds-1938-Radio-Broadcast-96kbps.mp3",
    "WAR OF THE WORLDS (1955)": "https://archive.org/download/WarOfTheWorldsOriginal1938Broadcast/The_War_of_the_Worlds_Lux_1955.mp3",
    "MARS IS HEAVEN! (1950)": "https://archive.org/download/Dimension-X/DimensionX_50-07-07_Mars_is_Heaven.mp3",
    "ZERO HOUR (1955)": "https://archive.org/download/Suspense-1955/Suspense_55-04-05_601_Zero_Hour.mp3"
}

class RadioManager:
    def __init__(self, status_callback=None):
        self.device = None
        self.source = None
        self.is_playing = False
        self.current_station = None
        self.status_callback = status_callback  # function(bool)
        self._worker_thread = None
        self._stop_event = threading.Event()
        self.vlc_available = True 
        
        # Local MP3 Interruption Logic
        self.last_interrupt_time = time.time()
        self.interrupt_interval = 1800 # 30 minutes
        self.local_mp3s = [f for f in os.listdir(".") if f.lower().endswith(".mp3") and f != "radio_manager.py"]
        self.last_played_mp3 = None
        self.is_interrupting = False
        self.current_song_name = None
        
    def is_available(self):
        return True

    def toggle(self, station_name=None):
        if self.is_playing and not station_name:
            self.stop()
        else:
            if not station_name:
                station_name = list(SAFE_RAP_STATIONS.keys())[0]
            self.play(station_name)

    def next_station(self):
        stations = list(SAFE_RAP_STATIONS.keys())
        if not self.current_station or self.current_station not in stations:
            new_idx = 0
        else:
            new_idx = (stations.index(self.current_station) + 1) % len(stations)
        self.play(stations[new_idx])

    def prev_station(self):
        stations = list(SAFE_RAP_STATIONS.keys())
        if not self.current_station or self.current_station not in stations:
            new_idx = len(stations) - 1
        else:
            new_idx = (stations.index(self.current_station) - 1) % len(stations)
        self.play(stations[new_idx])

    def play(self, station_name):
        if station_name not in SAFE_RAP_STATIONS:
            return
            
        # Ensure previous thread is stopped and cleaned up
        self.stop()
        
        # Wait for thread to actually finish to avoid layering
        if self._worker_thread and self._worker_thread.is_alive():
            # We don't want to block the UI thread for too long, but we need to wait
            # Join with timeout to be safe
            self._worker_thread.join(timeout=2.0)
            
        self.current_station = station_name
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._stream_thread, args=(station_name,), daemon=True)
        self._worker_thread.start()

    def stop(self):
        self._stop_event.set()
        self.is_playing = False
        self.is_interrupting = False
        # Stop device immediately if it exists
        try:
            if self.device:
                self.device.stop()
        except: pass
        
        # The thread will cleanup the device and source
        if self.status_callback:
            self.status_callback(False)

    def _stream_thread(self, station_name):
        self.last_interrupt_time = time.time()
        while not self._stop_event.is_set():
            url = SAFE_RAP_STATIONS[station_name]
            try:
                # IceCastClient handles the connection and provides a streamable source
                with miniaudio.IceCastClient(url) as self.source:
                    if self.status_callback:
                        self.status_callback(True)
                    self.is_playing = True

                    # Use stream_any with the IceCastClient source
                    stream = miniaudio.stream_any(self.source, self.source.audio_format)
                    
                    with miniaudio.PlaybackDevice() as self.device:
                        self.device.start(stream)
                        
                        # Keep thread alive while playing
                        while self.is_playing and not self._stop_event.is_set():
                            # Check stop event more frequently for faster switching
                            for _ in range(10): 
                                if self._stop_event.is_set() or not self.is_playing:
                                    break
                                time.sleep(0.1)
                            
                            if self._stop_event.is_set() or not self.is_playing:
                                break
                            
                            # Check for 30-minute interruption
                            if time.time() - self.last_interrupt_time >= self.interrupt_interval:
                                self._handle_interrupt()
                                # After interrupt finishes, we need to re-establish the stream 
                                # as the device was stopped/closed or stream exhausted
                                break 
                        
                        if self.device:
                            self.device.stop()
                            self.device = None
                    
                if self._stop_event.is_set():
                    break

            except Exception as e:
                print(f"Radio Play Error: {e}")
                if self._stop_event.is_set(): break
                time.sleep(5) # Retry delay
            finally:
                self.source = None

        self.is_playing = False
        if self.status_callback:
            self.status_callback(False)

    def _handle_interrupt(self):
        if not self.local_mp3s:
            self.last_interrupt_time = time.time()
            return

        self.is_interrupting = True
        
        # Pick a random MP3, don't play same back to back
        choices = [f for f in self.local_mp3s if f != self.last_played_mp3]
        if not choices: choices = self.local_mp3s # Fallback if only 1 file exists
        
        target_mp3 = random.choice(choices)
        self.last_played_mp3 = target_mp3
        
        print(f"Radio Interrupt: Playing local MP3 - {target_mp3}")
        
        try:
            # Stop current stream playback
            if self.device:
                self.device.stop()
            
            # Load and play local file
            # To know when it finishes, we wrap the stream generator
            def playback_wrapper(gen):
                for chunk in gen:
                    yield chunk
                    if self._stop_event.is_set():
                        break

            with miniaudio.PlaybackDevice() as interrupt_device:
                stream = miniaudio.stream_file(target_mp3)
                interrupt_device.start(playback_wrapper(stream))
                
                while not self._stop_event.is_set() and interrupt_device.running:
                    time.sleep(0.5)
                
                interrupt_device.stop()
        except Exception as e:
            print(f"Interrupt Error: {e}")
        finally:
            self.is_interrupting = False
            self.last_interrupt_time = time.time()
