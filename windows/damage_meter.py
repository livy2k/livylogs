import tkinter as tk
import time
from datetime import datetime, timedelta
from constants import (
    PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, BORDER_COLOR,
    WINDOW_BG, TEXT_ACCENT
)
from windows.base_window import BasePopoutWindow

class DamageMeterWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Damage Meter", "DamageMeterWindow", 320, 200)

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists() or self.window.state() == "withdrawn": return
        
        # Ensure title bar exists
        if not hasattr(self, 'title_bar') or not self.title_bar.winfo_exists(): return
        
        # Throttled refresh for expensive data gathering
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Damage meter needs regular refresh for readability (was 100ms, too fast)
        # We use 0.5s here to match the UI throttle for responsiveness
        do_full = force or (now - self.last_full_refresh >= 0.5)
        
        # Initialize labels if not existing
        if not hasattr(self, 'lbl_dmg') or not self.lbl_dmg.winfo_exists():
            for widget in self.content_container.winfo_children(): widget.destroy()
            grid = tk.Frame(self.content_container, bg=self.window["bg"])
            grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Use fixed widths to prevent resizing jumps
            # Increased widths slightly to handle longer numbers/duration strings
            # and set fixed font for value labels to ensure character width consistency
            VAL_WIDTH = 12
            VAL_FONT = ("Consolas", 10, "bold") # Monospaced font for values
            
            # Configure columns to be uniform with enough minsize for 12-char labels
            grid.grid_columnconfigure(1, minsize=100)
            grid.grid_columnconfigure(3, minsize=100)
            
            # Row 0
            tk.Label(grid, text="DAMAGE", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
            self.lbl_dmg = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_dmg.grid(row=0, column=1, sticky="e")

            tk.Label(grid, text="DPS", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 0))
            self.lbl_dps = tk.Label(grid, text="0.0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_dps.grid(row=0, column=3, sticky="e")
            
            # Row 1
            tk.Label(grid, text="DURATION", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=1, column=0, sticky="w", pady=(5, 0))
            self.lbl_dur = tk.Label(grid, text="0s", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_dur.grid(row=1, column=1, sticky="e", pady=(5, 0))

            tk.Label(grid, text="HIT%", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(5, 0))
            self.lbl_hit = tk.Label(grid, text="0.0%", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_hit.grid(row=1, column=3, sticky="e", pady=(5, 0))
            
            # Row 2
            tk.Label(grid, text="TAKEN", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=2, column=0, sticky="w", pady=(5, 0))
            self.lbl_taken = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_taken.grid(row=2, column=1, sticky="e", pady=(5, 0))

            tk.Label(grid, text="MISS%", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=2, column=2, sticky="w", padx=(20, 0), pady=(5, 0))
            self.lbl_miss = tk.Label(grid, text="0.0%", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_miss.grid(row=2, column=3, sticky="e", pady=(5, 0))

            # Row 3 (XP)
            tk.Label(grid, text="XP", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=3, column=0, sticky="w", pady=(5, 0))
            self.lbl_xp = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_xp.grid(row=3, column=1, sticky="e", pady=(5, 0))

            tk.Label(grid, text="XP/H", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=3, column=2, sticky="w", padx=(20, 0), pady=(5, 0))
            self.lbl_xph = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=VAL_FONT, width=VAL_WIDTH, anchor="e")
            self.lbl_xph.grid(row=3, column=3, sticky="e", pady=(5, 0))
            
            do_full = True # Force full on first run

        # Bind context menu
        self.window.bind("<Button-3>", self.show_context_menu)
        self.content_container.bind("<Button-3>", self.show_context_menu)

        if do_full:
            self.last_full_refresh = now
            
            # Calculate duration
            now_dt = datetime.now()
            start_ts = self.app.app_start_time if self.app.app_start_time else now_dt
            if hasattr(self.app, 'last_dm_reset') and self.app.last_dm_reset and self.app.last_dm_reset > start_ts:
                start_ts = self.app.last_dm_reset
            
            dur = 0
            if self.app.app_start_time:
                # Check if combat is active or paused
                is_active = (time.time() - self.app.last_combat_time) <= self.app.time_window_dm
                if is_active:
                    # If active, project from app_start_time to current moment
                    dur = (datetime.now() - self.app.app_start_time).total_seconds()
                else:
                    # If paused, duration is fixed at the last combat hit time
                    combat_end = datetime.fromtimestamp(self.app.last_combat_time) if self.app.last_combat_time > 0 else now_dt
                    dur = (combat_end - self.app.app_start_time).total_seconds()
            
            dur = max(0, dur)
            
            # Get latest stats from main data engine
            stats = self.app.player_data.get("You")
            if stats:
                damage_dealt = stats.get("dm_damage", 0)
                damage_taken = stats.get("dm_taken", 0)
                hit_count = stats.get("dm_hits", 0)
                miss_count = stats.get("dm_misses", 0)
                taken_hits = stats.get("dm_taken_hits", 0)
                avoided_count = stats.get("dm_avoided", 0)
                total_xp = stats.get("lb_xp", 0)
            else:
                damage_dealt = 0
                damage_taken = 0
                hit_count = 0
                miss_count = 0
                taken_hits = 0
                avoided_count = 0
                total_xp = 0

            # Recalculate from all_events ONLY if player_data is missing 'You' AND we have events
            if not stats and self.app.app_start_time and self.app.all_events:
                events = [e for e in self.app.all_events if e["timestamp"] and e["timestamp"] >= start_ts and (e["source"] == "You" or e["target"] == "You")]
                if events:
                    damage_dealt = sum(e["damage"] for e in events if e["type"] == "dealt")
                    damage_taken = sum(e["damage"] for e in events if e["type"] == "taken")
                    hit_count = sum(1 for e in events if e["type"] == "dealt" and e["damage"] > 0)
                    miss_count = sum(1 for e in events if e["type"] == "dealt" and e.get("is_mitigated"))
                    taken_hits = sum(1 for e in events if e["type"] == "taken" and e["damage"] > 0)
                    avoided_count = sum(1 for e in events if e["type"] == "taken" and e.get("is_mitigated"))
                    # XP usually comes from 'stats' or 'xp' events, but if missing we rely on what's in logs or just 0
                
            dps = damage_dealt / max(1, dur) if dur > 0 else 0
            
            total_attempts = hit_count + miss_count
            hit_pct = (hit_count / total_attempts * 100) if total_attempts > 0 else 0
            
            total_taken_attempts = taken_hits + avoided_count
            miss_pct = (avoided_count / total_taken_attempts * 100) if total_taken_attempts > 0 else 0

            dur_session = max(1, (now_dt - self.app.session_start_time).total_seconds())
            xph = total_xp / (dur_session / 3600)

            # Update labels individually (no mass destroy)
            def update_if_changed(lbl, new_text):
                try:
                    if hasattr(self, lbl) and getattr(self, lbl).winfo_exists():
                        widget = getattr(self, lbl)
                        if widget.cget("text") != new_text:
                            widget.config(text=new_text)
                except: pass

            dur_str = ""
            if dur >= 3600:
                hours = int(dur // 3600)
                mins = int((dur % 3600) // 60)
                secs = int(dur % 60)
                dur_str = f"{hours}h{mins}m{secs}s"
            elif dur >= 60:
                mins = int(dur // 60)
                secs = int(dur % 60)
                dur_str = f"{mins}m{secs}s"
            else:
                dur_str = f"{dur:.0f}s"

            update_if_changed('lbl_dur', dur_str)
            update_if_changed('lbl_dmg', f"{damage_dealt:,.0f}")
            update_if_changed('lbl_dps', f"{dps:.1f}")
            update_if_changed('lbl_hit', f"{hit_pct:.1f}%")
            update_if_changed('lbl_taken', f"{damage_taken:,.0f}")
            update_if_changed('lbl_miss', f"{miss_pct:.1f}%")
            update_if_changed('lbl_xp', f"{total_xp:,.0f}")
            update_if_changed('lbl_xph', f"{xph:,.0f}")

    def copy_to_clipboard(self):
        # Summary for Damage Meter
        summary = [
            f"DAMAGE: {self.lbl_dmg.cget('text')}",
            f"DPS: {self.lbl_dps.cget('text')}",
            f"DURATION: {self.lbl_dur.cget('text')}",
            f"HIT%: {self.lbl_hit.cget('text')}",
            f"TAKEN: {self.lbl_taken.cget('text')}",
            f"MISS%: {self.lbl_miss.cget('text')}",
            f"XP: {self.lbl_xp.cget('text')}",
            f"XP/H: {self.lbl_xph.cget('text')}"
        ]
        text = "Combat Summary:\n" + "\n".join(summary)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
