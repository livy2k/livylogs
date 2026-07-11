import os
# Ensure VLC binary is in the path for the vlc module to load correctly
vlc_path = r'C:\Program Files\VideoLAN\VLC'
if os.path.exists(vlc_path):
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(vlc_path)
    os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']

import vlc
import threading
import time
import requests
import miniaudio
import io
import random
import json
import urllib.parse
import collections
import subprocess
import numpy as np
import imageio_ffmpeg

class BufferedStreamSource:
    """A wrapper for stream data that provides buffering and transcoding if needed."""
    def __init__(self, url, buffer_size_bytes=1024*1024): # 1MB buffer
        self.url = url
        self.buffer = collections.deque()
        self.buffer_size_bytes = buffer_size_bytes
        self.current_buffer_fill = 0
        self.stop_event = threading.Event()
        self.error = None
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.is_raw = True
        self.sample_rate = 44100
        self.nchannels = 2
        self.sample_format = miniaudio.SampleFormat.SIGNED16
        self.error_in_readcallback = None
        self.ffmpeg_proc = None
        
        # Start background downloader/transcoder
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        
    def _process_loop(self):
        try:
            # Get bundled ffmpeg from imageio-ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # We use ffmpeg to transcode ANY input stream to raw PCM 16-bit 44.1kHz stereo
            # This solves AAC compatibility issues and network jitter.
            cmd = [
                ffmpeg_exe,
                '-loglevel', 'error',
                '-headers', f'User-Agent: {self.headers["User-Agent"]}\r\n',
                '-i', self.url,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', str(self.nchannels),
                '-'
            ]
            
            self.ffmpeg_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr for better error reporting
                bufsize=2 * 10**6 # Even larger pipe buffer (2MB)
            )
            
            while not self.stop_event.is_set():
                if self.current_buffer_fill < self.buffer_size_bytes:
                    chunk = self.ffmpeg_proc.stdout.read(131072) # Read even larger chunks (128KB)
                    if not chunk:
                        # Check if process died
                        if self.ffmpeg_proc.poll() is not None:
                            err_output = self.ffmpeg_proc.stderr.read().decode('utf-8', errors='ignore')
                            raise Exception(f"ffmpeg terminated: {err_output}")
                        break
                    self.buffer.append(chunk)
                    self.current_buffer_fill += len(chunk)
                else:
                    time.sleep(0.05)
                    
        except Exception as e:
            self.error = e
            print(f"BufferedStreamSource Error: {e}")
        finally:
            if self.ffmpeg_proc:
                self.ffmpeg_proc.terminate()

    def read(self, size, blocking=False):
        # Optional blocking wait for data
        if blocking and not self.buffer and not self.error:
            start_wait = time.time()
            while not self.buffer and not self.error and (time.time() - start_wait < 5):
                time.sleep(0.05)

        if not self.buffer:
            # If we have an error and no buffer, return silence
            if self.error: return b"\x00" * size
            # If we are just starting and haven't filled yet, return silence to avoid blocking
            return b"\x00" * size
            
        # POP NON-BLOCKING
        try:
            # We want to return EXACTLY 'size' bytes to keep miniaudio happy
            data = b""
            while len(data) < size:
                if not self.buffer:
                    # If we ran out of data, pad with silence
                    data += b"\x00" * (size - len(data))
                    break
                
                chunk = self.buffer.popleft()
                self.current_buffer_fill -= len(chunk)
                
                needed = size - len(data)
                if len(chunk) <= needed:
                    data += chunk
                else:
                    data += chunk[:needed]
                    remainder = chunk[needed:]
                    self.buffer.appendleft(remainder)
                    self.current_buffer_fill += len(remainder)
            return data
        except IndexError:
            return b"\x00" * size

    def close(self):
        self.stop_event.set()
        if self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.terminate()
                self.ffmpeg_proc.wait(timeout=1)
            except:
                try: self.ffmpeg_proc.kill()
                except: pass
        
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self.close()

class RadioStreamMixer:
    """Wrapper for miniaudio stream to provide volume control using NumPy for performance."""
    def __init__(self, generator, audio_format=miniaudio.SampleFormat.SIGNED16):
        self.generator = generator
        self.volume = 1.0
        self.audio_format = audio_format
        self._buffer = None
        
    def __iter__(self):
        return self
        
    def __next__(self):
        return self.send(None)
        
    def send(self, framecount):
        try:
            chunk = next(self.generator)
            if not chunk:
                return b""
                
            if self.volume <= 0.0:
                return b"\x00" * len(chunk)
            
            # Fast path for full volume
            if self.volume >= 0.999:
                return chunk

            # Apply volume using numpy
            dtype = np.float32 if self.audio_format == miniaudio.SampleFormat.FLOAT32 else np.int16
            
            # Use NumPy directly on the buffer
            samples = np.frombuffer(chunk, dtype=dtype)
            # Use out-of-place multiplication but minimize operations
            scaled = (samples * self.volume).astype(dtype)
            return scaled.tobytes()
        except (StopIteration, Exception):
            return b""

# Updated 100% Legally safe and open-source friendly stations with verified URLs
SAFE_RAP_STATIONS = {
    "181.FM OLDSCHOOL": "http://listen.181fm.com/181-oldschool_128k.mp3",
    "SOMAFM FLUID": "http://ice1.somafm.com/fluid-128-mp3",
    "1.FM 80S HITS": "http://strm112.1.fm/back280s_mobile_mp3",
    "STREET STYLE": "http://streetstyle.out.airtime.pro:8000/streetstyle_a",
    "CLASSIC RAP": "http://198.178.123.5:8320/stream",
    "88.6 ROCK": "http://radio886.at/streams/radio_88.6/mp3",
    "88.6 CLASSIC ROCK": "http://radio886.at/streams/88.6_Classic_Rock/mp3",
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
        self.volume = 100
        self.status_callback = status_callback  # function(bool)
        self._worker_thread = None
        self._stop_event = threading.Event()
        self.vlc_available = True 
        
        # Local MP3 Interruption Logic
        self.last_interrupt_time = time.time()
        self.interrupt_interval = 1800 # 30 minutes
        self.sfx_dir = "sfx"
        self.root_dir = os.getcwd()
        self.local_mp3s = []
        if os.path.exists(self.sfx_dir):
            self.local_mp3s = [os.path.join(self.sfx_dir, f) for f in os.listdir(self.sfx_dir) if f.lower().endswith(".mp3")]
        
        self.last_played_mp3 = None
        self.is_interrupting = False
        self.current_song_name = None
        self.current_art_url = None
        self.stream_mixer = None
        self._is_fading_in = False
        
        # Stoner Sound Library Integration
        from sfx_library import StonerSoundLibrary
        self.stoner_lib = StonerSoundLibrary(self.sfx_dir)
        
        # Audio for startup
        self.rise_mp3 = os.path.join(self.root_dir, "sfx", "rise.mp3")
        
        # History for local MP3s
        self.played_history = []
        self._load_history()
        
    def _load_history(self):
        try:
            if os.path.exists("radio_history.json"):
                with open("radio_history.json", "r") as f:
                    self.played_history = json.load(f)
        except:
            self.played_history = []

    def _save_history(self):
        try:
            with open("radio_history.json", "w") as f:
                json.dump(self.played_history, f)
        except:
            pass
        
    def is_available(self):
        return True

    def toggle(self, station_name=None):
        if self.is_playing and not station_name:
            self.stop()
        else:
            # When turning ON without a specific station, play random local MP3
            if not station_name:
                self.play_random_mp3()
            else:
                self.play(station_name)

    def play_random_mp3(self):
        # Play a stoner sound effect instead of a random MP3
        self.stop(is_transition=True)
        
        self.current_art_url = None
        self.is_playing = True
        self.current_station = "Radio Starting..."
        if self.status_callback:
            self.status_callback(True)

        # Play stoner SFX
        channel = self.stoner_lib.play_next_sequential()
        
        # We need to simulate the worker thread for the radio UI to think something is playing
        # or we just transition to a station after the sound ends.
        def _wait_and_play_station():
            if channel:
                while channel.get_busy() and not self._stop_event.is_set():
                    time.sleep(0.1)
            
            if self._stop_event.is_set():
                return

            # Now play a real station
            station_name = list(SAFE_RAP_STATIONS.keys())[0]
            self.play(station_name)

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=_wait_and_play_station, daemon=True)
        self._worker_thread.start()

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

    def play(self, station_name, force_join=True):
        if station_name not in SAFE_RAP_STATIONS:
            return
            
        # Ensure previous thread is stopped and cleaned up
        self.stop(is_transition=True)
        self.current_art_url = None
        
        # We've already handled the join inside self.stop()
            
        self.current_station = station_name
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._stream_thread, args=(station_name,), daemon=True)
        self._worker_thread.start()

    def stop(self, is_transition=False):
        self._stop_event.set()
        if not is_transition:
            self.is_playing = False
        self.is_interrupting = False
        
        # Stop device immediately if it exists - DON'T WAIT for join to stop audio
        try:
            if self.device:
                self.device.stop()
                self.device = None # Clear reference
        except: pass

        # Clear stream mixer to break potential references
        self.stream_mixer = None

        # Ensure we are not trying to join the current thread
        if self._worker_thread and self._worker_thread.is_alive():
            if threading.current_thread() != self._worker_thread:
                # Use a shorter timeout to avoid UI freeze if thread is stuck
                self._worker_thread.join(timeout=0.1)
            else:
                # If we are the worker thread, we can't join ourselves.
                pass

        # The thread will cleanup the device and source
        if self.status_callback and not is_transition:
            self.status_callback(False)

    def set_volume(self, volume):
        self.volume = max(0, min(100, volume))
        # Update VLC player if it's active
        # We need to find a way to access the player from the thread
        # For now, let's add it to the manager
        if hasattr(self, 'player') and self.player:
            self.player.audio_set_volume(self.volume)

    def _stream_thread(self, station_name):
        self.last_interrupt_time = time.time()
        
        # Use VLC for playback as it's more stable for streaming
        instance = vlc.Instance("--no-xlib", "--quiet", "--network-caching=2000")
        self.player = instance.media_player_new()
        
        url = SAFE_RAP_STATIONS[station_name]
        media = instance.media_new(url)
        self.player.set_media(media)
        
        # Track volume
        if self._is_fading_in:
             self.player.audio_set_volume(0)
        else:
             self.player.audio_set_volume(self.volume)

        if self.status_callback:
            self.status_callback(True)
            
        self.is_playing = True
        self.current_station = station_name
        
        self.player.play()
        
        # Wait for player to actually start
        start_wait = time.time()
        while self.player.get_state() not in [vlc.State.Playing, vlc.State.Error] and time.time() - start_wait < 10:
             time.sleep(0.1)
             
        if self.player.get_state() == vlc.State.Error:
             print(f"VLC Error: Failed to play {url}")
             self.is_playing = False
             if self.status_callback: self.status_callback(False)
             return

        # Fade in logic for VLC
        if self._is_fading_in:
             for v in range(0, self.volume + 1, 5):
                  if self._stop_event.is_set(): break
                  self.player.audio_set_volume(v)
                  time.sleep(0.05)
             self._is_fading_in = False

        try:
            while not self._stop_event.is_set() and self.is_playing:
                state = self.player.get_state()
                if state in [vlc.State.Ended, vlc.State.Error]:
                    break
                
                # Check for 30-minute interruption
                if not self.is_interrupting and time.time() - self.last_interrupt_time >= self.interrupt_interval:
                    # For VLC, we just stop the player and do the interrupt
                    self.player.stop()
                    self._handle_interrupt()
                    break 
                
                time.sleep(0.5)
        finally:
            self.player.stop()
            self.player.release()
            self.player = None
            instance.release()

        self.is_playing = False
        if self.status_callback:
            self.status_callback(False)

    def _handle_interrupt(self):
        if not self.local_mp3s:
            self.last_interrupt_time = time.time()
            return

        # Check for interrupt-specific drops first
        dj_drops = [f for f in self.local_mp3s if "FREE DJ DROP" in f.upper() or "YO YO" in f.upper() or "SPINNING" in f.upper()]
        if dj_drops:
            target_mp3 = random.choice(dj_drops)
        else:
            choices = [f for f in self.local_mp3s if f != self.last_played_mp3]
            if not choices: choices = self.local_mp3s
            target_mp3 = random.choice(choices)

        self.is_interrupting = True
        self.last_played_mp3 = target_mp3
        
        print(f"Radio Interrupt: Playing local MP3 - {target_mp3}")
        
        try:
            # Note: For VLC, the stream player is already stopped by the caller of _handle_interrupt
            # or it will be stopped here if called from somewhere else.
            
            # Load and play local file using miniaudio (since it works well for local files)
            stream = miniaudio.stream_file(target_mp3)
            info = miniaudio.get_file_info(target_mp3)

            self.is_interrupting = False
            self._is_fading_in = True
            
            with miniaudio.PlaybackDevice(
                output_format=info.sample_format,
                nchannels=info.nchannels,
                sample_rate=info.sample_rate,
                buffersize_msec=1000
            ) as interrupt_device:
                interrupt_device.start(stream)
                
                duration = 0
                try:
                    info = miniaudio.get_file_info(target_mp3)
                    duration = info.duration
                except: pass

                start_time = time.time()
                fade_started = False

                while not self._stop_event.is_set() and interrupt_device.running:
                    elapsed = time.time() - start_time
                    
                    # 1.5 seconds before end, signal the thread to re-start the radio with fade
                    if duration > 2.0 and elapsed >= (duration - 1.5) and not fade_started:
                        fade_started = True
                        # For VLC, we re-start the thread which handles the fade itself
                        if self.current_station:
                             self.play(self.current_station)
                    
                    time.sleep(0.1)
                
                # If it ended and we didn't start the radio yet
                if not fade_started and not self._stop_event.is_set():
                    if self.current_station:
                         self.play(self.current_station)

                interrupt_device.stop()
        except Exception as e:
            print(f"Interrupt Error: {e}")
        finally:
            self.is_interrupting = False
            self.last_interrupt_time = time.time()

    def _fade_in_stream(self):
        # This is now handled internally by _stream_thread's VLC logic
        pass
