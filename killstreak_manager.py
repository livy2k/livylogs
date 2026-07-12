"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import time
import threading
import queue
import pygame
import os

class KillstreakManager:
    def __init__(self, sfx_dir="sfx"):
        self.sfx_dir = sfx_dir
        self.kill_count = 0
        self.last_kill_time = 0
        self.multikill_count = 0
        self.multikill_window = 20.0  # 20 seconds
        
        self.audio_queue = queue.Queue()
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        
        # Streak mapping
        self.streak_sfx = {
            3: "killingspree.ogg",
            4: "dominating.ogg",
            5: "unstoppable.ogg",
            6: "godlike.ogg",
            7: "wickedsick.ogg",
            10: "monsterkill.ogg"
        }
        
        # Multikill mapping
        self.multikill_sfx = {
            2: "doublekill.ogg",
            3: "multikill.ogg",
            4: "megakill.ogg",
            5: "ultrakill.ogg",
            6: "monsterkill.ogg"
        }

        if not pygame.mixer.get_init():
            try:
                # Set dummy driver if needed or just try to init
                import os
                if 'SDL_AUDIODRIVER' not in os.environ:
                    os.environ['SDL_AUDIODRIVER'] = 'dummy' # Fallback to dummy to prevent crash
                
                pygame.mixer.init()
            except Exception as e:
                print(f"Failed to initialize pygame mixer: {e}")
                try:
                    # Try one more time without dummy if it failed
                    if os.environ.get('SDL_AUDIODRIVER') == 'dummy':
                        del os.environ['SDL_AUDIODRIVER']
                        pygame.mixer.init()
                except: pass

    def record_kill(self):
        now = time.time()
        self.kill_count += 1
        
        # Multikill logic
        if now - self.last_kill_time <= self.multikill_window:
            self.multikill_count += 1
        else:
            self.multikill_count = 1
        
        self.last_kill_time = now
        
        # Queue SFX
        # 1. Multikill
        if self.multikill_count in self.multikill_sfx:
            self._queue_sfx(self.multikill_sfx[self.multikill_count])
        elif self.multikill_count > 6:
            self._queue_sfx(self.multikill_sfx[6])
            
        # 2. Killstreak
        if self.kill_count in self.streak_sfx:
            self._queue_sfx(self.streak_sfx[self.kill_count])
        elif self.kill_count > 10 and self.kill_count % 5 == 0:
            # Every 5 kills after 10, repeat monster kill or similar? 
            # User didn't specify, but let's keep it to the list for now.
            pass

    def record_death(self):
        self.kill_count = 0
        self.multikill_count = 0
        self.last_kill_time = 0

    def _queue_sfx(self, filename):
        path = os.path.join(self.sfx_dir, filename)
        if os.path.exists(path):
            self.audio_queue.put(path)

    def _playback_loop(self):
        while True:
            path = self.audio_queue.get()
            if path is None:
                break
            try:
                sound = pygame.mixer.Sound(path)
                channel = sound.play()
                while channel.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Killstreak Audio Error: {e}")
            finally:
                self.audio_queue.task_done()
