"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import os
import pygame
import random

class StonerSoundLibrary:
    def __init__(self, audio_dir="sfx"):
        """Initializes the pygame mixer and structures the audio library paths."""
        try:
            # Increased buffer to 2048 to prevent stuttering and conflicts
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        except Exception as e:
            print(f"[Error] Failed to initialize pygame mixer: {e}")

        self.audio_dir = audio_dir
        self.sounds = {}
        
        # We'll use this list for sequential playback as requested
        self.sequential_sfx = [
            ("smoke", "sfx_deep_cough_01"),
            ("smoke", "sfx_water_bubble_loop"),
            ("smoke", "sfx_lighter_flick_fail"),
            ("smoke", "sfx_lighter_flick_success"),
            ("smoke", "sfx_long_exhale_sigh"),
            ("chords", "sfx_reverb_guitar_twang"),
            ("chords", "sfx_reggae_airhorn"),
            ("chords", "sfx_lazy_bass_slide"),
            ("chords", "sfx_trippy_phaser_synth"),
            ("voice", "sfx_voice_dude_what"),
            ("voice", "sfx_voice_is_that_you"),
            ("voice", "sfx_giggle_snicker_loop"),
            ("voice", "sfx_heavy_eyelids_blink"),
            ("munchies", "sfx_bag_rustle_loud"),
            ("munchies", "sfx_loud_crunch_chew"),
            ("munchies", "sfx_fridge_door_hum"),
            ("hazards", "sfx_slow_car_horn"),
            ("hazards", "sfx_tire_screech_slow"),
            ("hazards", "sfx_coughing_fit_chaos"),
            ("hazards", "sfx_paranoia_siren_distant"),
        ]
        self.current_sfx_idx = 0
        self.randomize_start()

        # Organized dictionary mapping categories to filenames
        self.library_manifest = {
            "smoke": [
                "sfx_deep_cough_01.wav",
                "sfx_water_bubble_loop.wav",
                "sfx_lighter_flick_fail.wav",
                "sfx_lighter_flick_success.wav",
                "sfx_long_exhale_sigh.wav",
            ],
            "chords": [
                "sfx_reverb_guitar_twang.wav",
                "sfx_reggae_airhorn.wav",
                "sfx_lazy_bass_slide.wav",
                "sfx_trippy_phaser_synth.wav",
            ],
            "voice": [
                "sfx_voice_dude_what.wav",
                "sfx_voice_is_that_you.wav",
                "sfx_giggle_snicker_loop.wav",
                "sfx_heavy_eyelids_blink.wav",
            ],
            "munchies": [
                "sfx_bag_rustle_loud.wav",
                "sfx_loud_crunch_chew.wav",
                "sfx_fridge_door_hum.wav",
            ],
            "hazards": [
                "sfx_slow_car_horn.wav",
                "sfx_tire_screech_slow.wav",
                "sfx_coughing_fit_chaos.wav",
                "sfx_paranoia_siren_distant.wav",
            ],
        }

        self._load_all_sounds()

    def _load_all_sounds(self):
        """Iterates through manifest and pre-loads audio into memory."""
        for category, files in self.library_manifest.items():
            self.sounds[category] = {}
            for file_name in files:
                # Strips .wav extension to create a clean key name
                key = file_name.replace(".wav", "")
                full_path = os.path.join(self.audio_dir, category, file_name)

                # Graceful loading: creates placeholders if files don't exist yet
                if os.path.exists(full_path):
                    try:
                        self.sounds[category][key] = pygame.mixer.Sound(full_path)
                    except Exception as e:
                        print(f"[Error] Failed to load {full_path}: {e}")
                        self.sounds[category][key] = None
                else:
                    self.sounds[category][key] = None
                    # print(f"[Warning] Missing audio file. Place it at: {full_path}")

    def play(self, category, sfx_id, loops=0, volume=1.0):
        """Plays a specific sound effect with custom loops and volume controls."""
        category_dict = self.sounds.get(category)
        if not category_dict:
            return None

        sound_obj = category_dict.get(sfx_id)
        if sound_obj is None:
            return None

        # Play sound on an available channel and set volume
        try:
            channel = sound_obj.play(loops=loops)
            if channel:
                channel.set_volume(volume)
            return channel
        except:
            return None

    def play_next_sequential(self):
        """Plays the next sound in the sequential list."""
        if not self.sequential_sfx:
            return None
            
        category, sfx_id = self.sequential_sfx[self.current_sfx_idx]
        channel = self.play(category, sfx_id)
        
        # Increment index for next time
        self.current_sfx_idx = (self.current_sfx_idx + 1) % len(self.sequential_sfx)
        return channel

    def randomize_start(self):
        """Sets the sequential index to a random starting point."""
        if self.sequential_sfx:
            self.current_sfx_idx = random.randint(0, len(self.sequential_sfx) - 1)
