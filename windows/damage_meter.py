import tkinter as tk
import time
from datetime import datetime, timedelta
from constants import (
    PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, BORDER_COLOR
)
from windows.base_window import BasePopoutWindow

class DamageMeterWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Damage Meter", "DamageMeterWindow", 320, 180)

    def show(self, force_open=False):
        super().show(force_open)
        if not self.window: return

        reset_btn = tk.Label(self.title_bar, text="RESET", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=10)
        reset_btn.pack(side=tk.RIGHT)
        reset_btn.bind("<Button-1>", lambda e: self.app.reset_damage_meter_manual())

    def refresh(self, force=False):
        if not self.window or self.window.state() == "withdrawn": return
        
        # Throttled refresh for expensive data gathering
        now = time.time()
        if not hasattr(self, 'last_full_refresh'): self.last_full_refresh = 0
        
        # Determine if we should do a full data calculation
        # Faster throttle (0.25s) for better responsiveness, or forced
        do_full = force or (now - self.last_full_refresh >= 0.25)
        
        # Initialize labels if not existing
        if not hasattr(self, 'lbl_dmg'):
            for widget in self.content_container.winfo_children(): widget.destroy()
            grid = tk.Frame(self.content_container, bg=self.window["bg"])
            grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Row 0
            tk.Label(grid, text="DAMAGE", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
            self.lbl_dmg = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_dmg.grid(row=0, column=1, sticky="e", padx=(10, 0))
            
            tk.Label(grid, text="DURATION", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w", padx=(30, 0))
            self.lbl_dur = tk.Label(grid, text="0s", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_dur.grid(row=0, column=3, sticky="e", padx=(10, 0))
            
            # Row 1
            tk.Label(grid, text="DPS", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=1, column=0, sticky="w", pady=(10, 0))
            self.lbl_dps = tk.Label(grid, text="0.0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_dps.grid(row=1, column=1, sticky="e", padx=(10, 0), pady=(10, 0))
            
            tk.Label(grid, text="HIT%", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=1, column=2, sticky="w", padx=(30, 0), pady=(10, 0))
            self.lbl_hit = tk.Label(grid, text="0.0%", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_hit.grid(row=1, column=3, sticky="e", padx=(10, 0), pady=(10, 0))
            
            # Row 2
            tk.Label(grid, text="TAKEN", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.lbl_taken = tk.Label(grid, text="0", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_taken.grid(row=2, column=1, sticky="e", padx=(10, 0), pady=(10, 0))
            
            tk.Label(grid, text="MISS%", bg=self.window["bg"], fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).grid(row=2, column=2, sticky="w", padx=(30, 0), pady=(10, 0))
            self.lbl_miss = tk.Label(grid, text="0.0%", bg=self.window["bg"], fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            self.lbl_miss.grid(row=2, column=3, sticky="e", padx=(10, 0), pady=(10, 0))
            
            do_full = True # Force full on first run

        # Calculate duration - ALWAYS UPDATE (High frequency)
        now_dt = datetime.now()
        start_ts = self.app.app_start_time if self.app.app_start_time else now_dt
        if hasattr(self.app, 'last_dm_reset') and self.app.last_dm_reset and self.app.last_dm_reset > start_ts:
            start_ts = self.app.last_dm_reset
        
        dur = 0
        if self.app.app_start_time:
            is_paused = self.app.last_combat_time > 0 and (time.time() - self.app.last_combat_time) > self.app.time_window_dm
            if not is_paused and self.app.last_combat_time > 0:
                anchor = getattr(self.app, 'last_log_sync_time', self.app.app_start_time)
                dur = (anchor + timedelta(seconds=time.time() - self.app.last_combat_time) - start_ts).total_seconds()
            else:
                dur = (datetime.fromtimestamp(self.app.last_combat_time if self.app.last_combat_time > 0 else time.time()) - start_ts).total_seconds()
        
        dur = max(0, dur)
        self.lbl_dur.config(text=f"{dur:.0f}s")

        if do_full:
            self.last_full_refresh = now
            events = [e for e in self.app.all_events if e["timestamp"] and e["timestamp"] >= start_ts and (e["source"] == "You" or e["target"] == "You")]
            
            # Use window-specific data if available to respect manual resets
            stats = self.app.player_data.get("You", {})
            damage_dealt = stats.get("dm_damage", 0)
            damage_taken = stats.get("dm_taken", 0)
            
            # Recalculate if stats are missing
            if not damage_dealt and not damage_taken and events:
                damage_dealt = sum(e["damage"] for e in events if e["type"] == "dealt")
                damage_taken = sum(e["damage"] for e in events if e["type"] == "taken")
                
            dps = damage_dealt / max(1, dur) if dur > 0 else 0
            
            hit_count = stats.get("dm_hits", 0)
            miss_count = stats.get("dm_misses", 0)
            # Recalculate if missing
            if not hit_count and not miss_count and events:
                hit_count = sum(1 for e in events if e["type"] == "dealt" and e["damage"] > 0)
                miss_count = sum(1 for e in events if e["type"] == "dealt" and e.get("is_mitigated"))
            
            total_attempts = hit_count + miss_count
            hit_pct = (hit_count / total_attempts * 100) if total_attempts > 0 else 0
            
            taken_hits = stats.get("dm_taken_hits", 0)
            avoided_count = stats.get("dm_avoided", 0)
            # Recalculate if missing
            if not taken_hits and not avoided_count and events:
                taken_hits = sum(1 for e in events if e["type"] == "taken" and e["damage"] > 0)
                avoided_count = sum(1 for e in events if e["type"] == "taken" and e.get("is_mitigated"))
                
            total_taken_attempts = taken_hits + avoided_count
            miss_pct = (avoided_count / total_taken_attempts * 100) if total_taken_attempts > 0 else 0

            # Update labels
            self.lbl_dmg.config(text=f"{damage_dealt:,.0f}")
            self.lbl_dps.config(text=f"{dps:.1f}")
            self.lbl_hit.config(text=f"{hit_pct:.1f}%")
            self.lbl_taken.config(text=f"{damage_taken:,.0f}")
            self.lbl_miss.config(text=f"{miss_pct:.1f}%")
