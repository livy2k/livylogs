"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

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
    "RNS 420AM": "https://stream.bigfm.de/oldschoolrap/aac-128/liveradioie"
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
        
        # Load all stations (safe + custom)
        # We allow custom_stations.txt to completely override defaults if desired,
        # but by default we merge them.
        self.stations = SAFE_RAP_STATIONS.copy()
        self.load_stations()
        
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
        self._pending_metadata = None
        self._metadata_timer = None
        self.metadata_delay = 2.5 # 2.5 seconds offset for buffering
        self.current_art_url = None
        self.current_art_data = None # Raw image data for ASCII
        self.art_changed = False
        self.stream_mixer = None
        self._is_fading_in = False
        self.equalizer = None # Current vlc.AudioEqualizer object
        self.eq_bands = [0.0] * 10
        self.eq_preamp = 0.0
        self._skip_track = False
        
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

    def load_stations(self):
        """Loads custom radio stations from custom_stations.txt"""
        filename = "custom_stations.txt"
        # Always ensure the file exists so the user can find it
        if not os.path.exists(filename):
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("###############################################################################\n")
                    f.write("# LIVYLOGS CUSTOM RADIO STATIONS\n")
                    f.write("###############################################################################\n")
                    f.write("#\n")
                    f.write("# Instructions:\n")
                    f.write("# 1. Add your custom radio stations below.\n")
                    f.write("# 2. Each station should be on its own line.\n")
                    f.write("# 3. Format: Station Name | Stream URL\n")
                    f.write("#    Example: My Cool Station | http://streaming.example.com/radio.mp3\n")
                    f.write("#\n")
                    f.write("# Linking External Services (Spotify, YouTube, etc.):\n")
                    f.write("# - Direct Spotify/YouTube links are NOT supported directly due to DRM.\n")
                    f.write("# - To link YouTube: Search for the video/playlist on \"YouTube to MP3 Stream\" \n")
                    f.write("#   websites that provide a direct .mp3 or .m3u8 URL.\n")
                    f.write("# - To link Spotify: Use \"Spotify to Radio\" tools or search for the artist \n")
                    f.write("#   on \"Radio-Browser.info\" to find a stream playing that genre.\n")
                    f.write("# - Recommended: Use \"https://www.radio-browser.info/\" to find thousands \n")
                    f.write("#   of free streams. Look for the \"Stream URL\" ending in .mp3 or .pls.\n")
                    f.write("#\n")
                    f.write("# Specific How-To for YouTube:\n")
                    f.write("# 1. Go to a site like \"https://y2mate.is\" or \"https://loader.to\".\n")
                    f.write("# 2. Paste your YouTube link and look for a \"Live Stream\" or \"Permanent Link\".\n")
                    f.write("# 3. Copy that URL and paste it here: [Name] | [URL]\n")
                    f.write("#\n")
                    f.write("# Specific How-To for Spotify:\n")
                    f.write("# 1. Open your Spotify Playlist.\n")
                    f.write("# 2. Use a tool like \"Soundiiz\" to export it to a generic PLS or M3U8.\n")
                    f.write("# 3. Or simply find a similar Radio Station on TuneIn and use its URL.\n")
                    f.write("#\n")
                    f.write("# Tips:\n")
                    f.write("# - The Station Name is what will show up on the radio display.\n")
                    f.write("# - Use a vertical bar (|) to separate the name from the URL.\n")
                    f.write("# - Most MP3, AAC, and PLS streams are supported via VLC.\n")
                    f.write("# - Lines starting with # are comments and will be ignored.\n")
                    f.write("# - Empty lines will also be ignored.\n")
                    f.write("#\n")
                    f.write("###############################################################################\n\n")
                    f.write("# Examples (Remove the # to enable):\n")
                    f.write("# Lofi Girl | https://lofi.stream.url/live.mp3\n")
                    f.write("# Classic Rock | http://classic.rock.example/stream\n")
            except: pass

        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "|" in line:
                            parts = [p.strip() for p in line.split("|")]
                            if len(parts) >= 2:
                                name, url = parts[0], parts[1]
                                self.stations[name] = url
            except Exception as e:
                print(f"[DEBUG] Error loading custom stations: {e}")
        
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
        channel = None
        try:
            channel = self.stoner_lib.play_next_sequential()
        except Exception as e:
            print(f"[DEBUG] Error playing startup sound: {e}")
        
        # Fallback if SFX fails or is missing
        if not channel:
            print("[DEBUG] No startup sound channel, skipping wait.")
            station_name = list(self.stations.keys())[0]
            self.play(station_name)
            return

        # We need to simulate the worker thread for the radio UI to think something is playing
        # or we just transition to a station after the sound ends.
        def _wait_and_play_station():
            try:
                if channel:
                    while channel.get_busy() and not self._stop_event.is_set():
                        time.sleep(0.1)
            except Exception as e:
                print(f"[DEBUG] Error in startup sound wait thread: {e}")
            
            if self._stop_event.is_set():
                return

            # Now play a real station
            try:
                station_name = list(self.stations.keys())[0]
                self.play(station_name)
            except Exception as e:
                print(f"[DEBUG] Error starting station after sound: {e}")

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=_wait_and_play_station, daemon=True)
        self._worker_thread.start()

    def next_station(self):
        stations = list(self.stations.keys())
        if not self.current_station or self.current_station not in stations:
            new_idx = 0
        else:
            new_idx = (stations.index(self.current_station) + 1) % len(stations)
        self.play(stations[new_idx])

    def prev_station(self):
        stations = list(self.stations.keys())
        if not self.current_station or self.current_station not in stations:
            new_idx = len(stations) - 1
        else:
            new_idx = (stations.index(self.current_station) - 1) % len(stations)
        self.play(stations[new_idx])

    def play_local_file(self, file_path):
        """Plays a single local audio file."""
        if not os.path.exists(file_path):
            return
            
        self.stop(is_transition=True)
        self.current_art_url = None
        self.current_station = "LOCAL AUX"
        self.current_song_name = os.path.basename(file_path)
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._local_playback_thread, args=(file_path,), daemon=True)
        self._worker_thread.start()

    def play_local_playlist(self, file_list):
        """Plays a list of local audio files."""
        if not file_list:
            return
            
        self.stop(is_transition=True)
        self.current_art_url = None
        self.current_station = "LOCAL PLAYLIST"
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._playlist_playback_thread, args=(file_list,), daemon=True)
        self._worker_thread.start()

    def pause(self):
        """Pauses the current playback."""
        if hasattr(self, 'player') and self.player:
            self.player.pause()
            # Note: VLC pause() toggles pause state
            
    def next_track(self):
        """Skip to next track (only for playlists)."""
        if self.current_station == "LOCAL PLAYLIST":
            # We can't easily tell the thread to skip without complex signaling
            # But we can set a flag that the thread checks
            self._skip_track = True

    def prev_track(self):
        """Skip to previous track (only for playlists)."""
        # Playlists currently only go forward, but we could implement a full player state
        pass

    def _local_playback_thread(self, file_path):
        """Thread for playing a single local file."""
        try:
            import vlc
            instance = vlc.Instance("--no-xlib", "--quiet")
            self.player = instance.media_player_new()
            
            media = instance.media_new_path(file_path)
            self.player.set_media(media)
            self.player.audio_set_volume(self.volume)
            
            if self.equalizer:
                if hasattr(self.player, 'audio_set_equalizer'):
                    self.player.audio_set_equalizer(self.equalizer)
                elif hasattr(self.player, 'set_equalizer'):
                    self.player.set_equalizer(self.equalizer)
                
            if self.status_callback:
                self.status_callback(True)
            
            self.is_playing = True
            self.player.play()
            
            # Wait for it to finish or be stopped
            while not self._stop_event.is_set():
                state = self.player.get_state()
                if state in [vlc.State.Ended, vlc.State.Error, vlc.State.Stopped]:
                    break
                
                # Extract metadata for local file
                m = self.player.get_media()
                if m:
                    artist = m.get_meta(vlc.Meta.Artist)
                    title = m.get_meta(vlc.Meta.Title)
                    if artist and title:
                        self.current_song_name = f"{artist} - {title}"
                    elif title:
                        self.current_song_name = title
                    else:
                        self.current_song_name = os.path.basename(file_path)

                    # Extract Art
                    art_url = m.get_meta(vlc.Meta.ArtworkURL)
                    if not art_url:
                        art_url = self._lookup_cover_art(self.current_song_name)
                        
                    if art_url and art_url != self.current_art_url:
                        self.current_art_url = art_url
                        self._extract_art_data(art_url)

                time.sleep(0.5)
                
        except Exception as e:
            print(f"[DEBUG] Local playback error: {e}")
        finally:
            if self.player:
                self.player.stop()
                self.player.release()
                self.player = None
            if instance:
                instance.release()
            self.is_playing = False
            if self.status_callback:
                self.status_callback(False)

    def _playlist_playback_thread(self, file_list):
        """Thread for playing a sequence of local files."""
        try:
            import vlc
            instance = vlc.Instance("--no-xlib", "--quiet")
            
            self._skip_track = False
            for file_path in file_list:
                if self._stop_event.is_set():
                    break
                    
                self.player = instance.media_player_new()
                media = instance.media_new_path(file_path)
                self.player.set_media(media)
                self.player.audio_set_volume(self.volume)
                self.current_song_name = os.path.basename(file_path)
                
                if self.equalizer:
                    if hasattr(self.player, 'audio_set_equalizer'):
                        self.player.audio_set_equalizer(self.equalizer)
                    elif hasattr(self.player, 'set_equalizer'):
                        self.player.set_equalizer(self.equalizer)
                    
                if self.status_callback:
                    self.status_callback(True)
                
                self.is_playing = True
                self.player.play()
                
                # Wait for current file to finish
                while not self._stop_event.is_set() and not self._skip_track:
                    state = self.player.get_state()
                    if state in [vlc.State.Ended, vlc.State.Error, vlc.State.Stopped]:
                        break
                    
                    # Metadata extraction
                    m = self.player.get_media()
                    if m:
                        artist = m.get_meta(vlc.Meta.Artist)
                        title = m.get_meta(vlc.Meta.Title)
                        if artist and title:
                            self.current_song_name = f"{artist} - {title}"
                        elif title:
                            self.current_song_name = title

                        # Extract Art
                        art_url = m.get_meta(vlc.Meta.ArtworkURL)
                        if not art_url:
                            art_url = self._lookup_cover_art(self.current_song_name)
                            
                        if art_url and art_url != self.current_art_url:
                            self.current_art_url = art_url
                            self._extract_art_data(art_url)
                    
                    time.sleep(0.5)
                
                self._skip_track = False
                self.player.stop()
                self.player.release()
                self.player = None
                
        except Exception as e:
            print(f"[DEBUG] Playlist playback error: {e}")
        finally:
            self.is_playing = False
            if self.status_callback:
                self.status_callback(False)
            if instance:
                instance.release()

    def play(self, station_name, force_join=True):
        if station_name not in self.stations:
            # Refresh stations and check again in case user just added it
            self.load_stations()
            if station_name not in self.stations:
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
        # Cancel any pending metadata updates
        if self._metadata_timer:
            self._metadata_timer.cancel()
            self._metadata_timer = None
        self._pending_metadata = None

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
        if hasattr(self, 'player') and self.player:
            # We must use a direct call to avoid any potential thread/instance lock issues
            try:
                # Store it as an attribute to check if it's already set
                current = self.player.audio_get_volume()
                if current != int(self.volume):
                    self.player.audio_set_volume(int(self.volume))
            except: pass

    def set_equalizer(self, bands, preamp=0.0):
        """
        bands: list of 10 floats (-20.0 to 20.0)
        preamp: float (-20.0 to 20.0)
        """
        self.eq_bands = bands
        self.eq_preamp = preamp
        
        if self.vlc_available:
            try:
                import vlc
                if self.equalizer is None:
                    self.equalizer = vlc.AudioEqualizer()
                
                # Preamp is set on the equalizer object
                self.equalizer.set_preamp(preamp)
                for i in range(min(len(bands), 10)):
                    # VLC expects 10 bands at specific frequencies
                    self.equalizer.set_amp_at_index(bands[i], i)
                
                # IMPORTANT: Apply to active player if it exists
                if hasattr(self, 'player') and self.player:
                    if hasattr(self.player, 'audio_set_equalizer'):
                        self.player.audio_set_equalizer(self.equalizer)
                    elif hasattr(self.player, 'set_equalizer'):
                        self.player.set_equalizer(self.equalizer)
                    else:
                        print("[DEBUG] MediaPlayer has no equalizer support")
            except Exception as e:
                print(f"[DEBUG] Error setting EQ: {e}")

    def get_equalizer(self):
        return self.eq_bands, self.eq_preamp

    def _stream_thread(self, station_name):
        self.last_interrupt_time = time.time()
        
        # Use VLC for playback as it's more stable for streaming
        instance = vlc.Instance("--no-xlib", "--quiet", "--network-caching=2000")
        self.player = instance.media_player_new()
        
        url = self.stations[station_name]
        media = instance.media_new(url)
        self.player.set_media(media)
        
        # Track volume
        if self._is_fading_in:
             self.player.audio_set_volume(0)
        else:
             self.player.audio_set_volume(self.volume)

        # Apply equalizer if set
        if self.equalizer:
            try:
                if hasattr(self.player, 'audio_set_equalizer'):
                    self.player.audio_set_equalizer(self.equalizer)
                elif hasattr(self.player, 'set_equalizer'):
                    self.player.set_equalizer(self.equalizer)
            except Exception as e:
                print(f"[DEBUG] Failed to apply EQ to new player: {e}")

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
                
                # Update metadata
                media = self.player.get_media()
                if media:
                    raw_playing = media.get_meta(vlc.Meta.NowPlaying)
                    if not raw_playing:
                        artist = media.get_meta(vlc.Meta.Artist)
                        title = media.get_meta(vlc.Meta.Title)
                        if artist and title: raw_playing = f"{artist} - {title}"
                        elif title: raw_playing = title

                    if raw_playing:
                        parsed = self._parse_metadata(raw_playing)
                        if parsed != self._pending_metadata and parsed != self.current_song_name:
                            # Start a delayed update
                            if self._metadata_timer:
                                self._metadata_timer.cancel()
                            
                            self._pending_metadata = parsed
                            
                            def _apply_metadata(meta_val):
                                if not self._stop_event.is_set():
                                    self.current_song_name = meta_val
                                    self._pending_metadata = None
                                    self._metadata_timer = None
                                    
                                    # Extract Art when song actually changes
                                    if self.player:
                                        m_obj = self.player.get_media()
                                        art_url = None
                                        if m_obj:
                                            art_url = m_obj.get_meta(vlc.Meta.ArtworkURL)
                                        
                                        # If no art URL in metadata, try lookup
                                        if not art_url:
                                            art_url = self._lookup_cover_art(self.current_song_name)
                                            
                                        if art_url and art_url != self.current_art_url:
                                            self.current_art_url = art_url
                                            self._extract_art_data(art_url)
                            
                            self._metadata_timer = threading.Timer(self.metadata_delay, _apply_metadata, args=[parsed])
                            self._metadata_timer.daemon = True
                            self._metadata_timer.start()
                
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

    def _parse_metadata(self, raw_metadata):
        if not raw_metadata:
            return None
        
        import re
        text = raw_metadata.strip()
        
        # 1. Remove obvious clutter
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'(?i)^(LIVE|ON AIR|STREAMING|NOW PLAYING):\s*', '', text)
        text = re.sub(r'(?i)\s*(\(?(buy on iTunes|on air|listening to|streaming|radio|live)\)?)\s*', '', text)
        
        # 2. Extract Artist and Song
        if " - " in text:
            parts = [p.strip() for p in text.split(" - ") if p.strip()]
            if len(parts) >= 2:
                # If we have "Station - Artist - Song", the candidate artist string is parts[-2]
                raw_artist = parts[-2]
                song = parts[-1]
                
                # Split artists by common delimiters: " feat. ", " ft. ", " & ", ", "
                artists = re.split(r'(?i)\s+(?:feat\.?|ft\.?|&)\s+|,\s+', raw_artist)
                artists = [a.strip() for a in artists if a.strip()]
                
                # Take up to the first three artists
                display_artists = " & ".join(artists[:3])
                
                # Clean song name from (Remix), [Official Video], (feat. X) etc.
                # We strip anything in parentheses/brackets to keep it minimalist as per previous patterns
                song = re.sub(r'\s*[\(\[\{].*?[\)\]\}]\s*', ' ', song).strip()
                song = re.sub(r'\s*@.*$', '', song)
                
                result = f"{display_artists} - {song}".strip()
                if self._is_mostly_english(result):
                    return result
                return None
        
        # Fallback to general cleaning
        text = re.sub(r'\s+', ' ', text).strip()
        if self._is_mostly_english(text):
            return text
        return None

    def _is_mostly_english(self, text):
        if not text:
            return True
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            non_ascii = len([c for c in text if ord(c) > 127])
            # If more than 20% of the text is non-ASCII, it's likely not English/Latin-based
            if non_ascii / len(text) > 0.2:
                return False
            return True

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

    def _extract_art_data(self, art_url):
        """Fetches and stores raw art data for ASCII conversion."""
        if not art_url:
            self.current_art_data = None
            self.art_changed = True
            return

        def _fetch_art():
            try:
                data = None
                print(f"[DEBUG] Fetching art from: {art_url}")
                if art_url.startswith("file:///"):
                    # Local file URL from VLC metadata
                    local_path = urllib.parse.unquote(art_url[8:])
                    if os.path.exists(local_path):
                        with open(local_path, "rb") as f:
                            data = f.read()
                elif art_url.startswith("http"):
                    # Use a standard User-Agent to avoid being blocked by some CDNs
                    headers = {"User-Agent": "LivyLogs/1.0 (https://github.com/LivyC/LivyLogs)"}
                    resp = requests.get(art_url, timeout=5, headers=headers)
                    if resp.status_code == 200:
                        data = resp.content
                
                if data:
                    self.current_art_data = data
                    self.art_changed = True
            except Exception as e:
                print(f"[DEBUG] Art fetch error: {e}")

        threading.Thread(target=_fetch_art, daemon=True).start()

    def _lookup_cover_art(self, song_name):
        """Attempts to find cover art URL for a song name (Artist - Title)."""
        if not song_name or " - " not in song_name:
            return None
            
        # Check cache first
        if not hasattr(self, "_art_cache"):
            self._art_cache = {}
            
        if song_name in self._art_cache:
            return self._art_cache[song_name]
            
        try:
            # We'll use the iTunes Search API as it's very fast, free, and doesn't require an API key
            # It's much lighter than MusicBrainz for simple cover art.
            query = urllib.parse.quote(song_name)
            api_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
            
            resp = requests.get(api_url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("resultCount", 0) > 0:
                    # Prefer higher resolution for the popup window, 100x100 is fine for lookup
                    # but iTunes also offers artworkUrl600
                    artwork_url = data["results"][0].get("artworkUrl600")
                    if not artwork_url:
                        artwork_url = data["results"][0].get("artworkUrl100")
                        
                    if artwork_url:
                        self._art_cache[song_name] = artwork_url
                        return artwork_url
            
            # If not found, cache None to avoid re-searching
            self._art_cache[song_name] = None
        except Exception as e:
            print(f"[DEBUG] Cover art lookup error: {e}")
            
        return None

    def _fade_in_stream(self):
        # This is now handled internally by _stream_thread's VLC logic
        pass
