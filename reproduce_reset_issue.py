import time
from datetime import datetime, timedelta

def reproduce_manual_reset_jump():
    # Mocking the relevant state variables and constants
    class MockApp:
        def __init__(self):
            self.app_start_time = None
            self.last_log_sync_time = None
            self.last_combat_time = 0
            self.damage_dealt = 0
            self.damage_taken = 0
            self.leaderboard_data = {}
            self.player_data = {}
            self.all_events = []
            self.actual_app_start_time = datetime.now()
            self.last_reset_time = self.actual_app_start_time
            self.time_window_dm = 30
            self.last_ui_update_time = 0
            self.last_full_ui_update = 0
            self.ui_update_delay = 0.05
            
        def reset_data(self):
            print("--- PERFORMING RESET ---")
            self.player_data = {}
            self.all_events = []
            self.last_read_offset = 0
            self.app_start_time = None
            self.last_combat_time = 0 
            self.last_log_sync_time = None
            self.last_reset_time = datetime.now()
            self.analyze_log(manual=True)

        def analyze_log(self, manual=False):
            now_dt = datetime.now()
            now_ts = time.time()
            
            # Simulated new events (e.g. read from log)
            # Scenario: There is an event in the log from 5 seconds ago.
            # Manual reset just happened, so self.last_reset_time is NOW.
            # But start_floor is self.last_reset_time - 300s.
            new_events = [{
                "timestamp": now_dt - timedelta(seconds=297),
                "damage": 100,
                "type": "dealt"
            }]
            
            # --- Logic from analyze_log ---
            is_initial_history_load = manual # If manual=True, it behaves like initial load
            
            if self.app_start_time is None:
                # FIX: If manual, floor should be NOW, not 5 mins ago.
                floor_buffer = 0 if manual else 300
                start_floor = max(self.actual_app_start_time, self.last_reset_time) - timedelta(seconds=floor_buffer)
                damage_events = [
                    e for e in new_events 
                    if e["damage"] > 0 and e["timestamp"] and e["timestamp"] >= start_floor
                ]
                
                if damage_events:
                    latest_damage_ts = max(e["timestamp"] for e in damage_events)
                    # Even if it's 5 seconds ago, it's considered "recent" (< 10s)
                    is_recent = (datetime.now() - latest_damage_ts).total_seconds() < 10
                    
                    if not is_initial_history_load or is_recent or manual:
                        print(f"DEBUG: Session initialized at {latest_damage_ts} (log age: {(now_dt - latest_damage_ts).total_seconds()}s)")
                        self.app_start_time = latest_damage_ts
                        self.last_log_sync_time = self.app_start_time
                        
            # Sync logic
                        log_age = (now_dt - self.app_start_time).total_seconds()
                        if log_age > 0:
                            # self.last_combat_time = now_ts - min(60.0, log_age)
                            # Let's say we don't clamp it in this mock to see the jump
                            self.last_combat_time = now_ts - log_age
                        else:
                            self.last_combat_time = now_ts
                        
                        print(f"DEBUG: last_combat_time set to {self.last_combat_time} (diff from now: {now_ts - self.last_combat_time}s)")

            # Duration calculation
            if self.app_start_time and self.last_combat_time > 0:
                anchor_ts = self.last_log_sync_time or self.app_start_time
                time_since_sync = now_ts - self.last_combat_time
                projected_now = anchor_ts + timedelta(seconds=time_since_sync)
                duration = (projected_now - self.app_start_time).total_seconds()
                print(f"RESULTING DURATION: {duration:.2f}s")

    app = MockApp()
    
    # 1. Start a session
    print("--- STARTING INITIAL SESSION ---")
    app.app_start_time = datetime.now() - timedelta(seconds=10)
    app.last_combat_time = time.time()
    
    # 2. Reset
    time.sleep(0.1)
    app.reset_data()

if __name__ == "__main__":
    reproduce_manual_reset_jump()
