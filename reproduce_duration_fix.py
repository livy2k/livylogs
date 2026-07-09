import time
from datetime import datetime, timedelta

def test_duration_start():
    # Mock calculate_dps
    def calculate_dps(events):
        damage = sum(e['damage'] for e in events)
        duration = 0
        if events:
            # Simple duration for testing
            duration = (max(e['timestamp'] for e in events) - min(e['timestamp'] for e in events)).total_seconds()
        return damage, 0, 0, duration, 0, 0, 0, 0

    class MockApp:
        def __init__(self):
            self.app_start_time = None
            self.last_combat_time = 0
            self.last_log_sync_time = None
            self.time_window_dm = 30
            self.all_events = []
            self.last_pulse_time = 0
            self.pulse_state = False
            self.damage_dealt = 0
            self.damage_taken = 0
            self.leaderboard_data = {}
            self.player_data = {}

        def process_external_event(self, event):
            damage = event.get("damage", 0)
            is_damage = damage > 0
            timestamp = event.get("timestamp")
            
            # Simplified Logic from the fix
            now = time.time()
            is_combat_timeout = self.app_start_time and (now - self.last_combat_time > self.time_window_dm)
            
            if is_combat_timeout:
                print("DEBUG: Combat session timed out (Pipe)")
                self.app_start_time = None
                self.last_log_sync_time = None
                self.damage_dealt = 0
                self.damage_taken = 0

            if is_damage:
                self.last_combat_time = now
                self.last_log_sync_time = timestamp
                
                if self.app_start_time is None:
                    self.app_start_time = timestamp
                    print(f"DEBUG: Session started via pipe at {timestamp}")

            self.all_events.append(event)
            self.update_live_stats([e for e in self.all_events if e['timestamp'] >= self.app_start_time] if self.app_start_time else [])

        def update_live_stats(self, events_for_ui, is_paused=False):
            damage_dealt, _, _, duration, _, _, _, _ = calculate_dps(events_for_ui)
            now_ts = time.time()
            now_dt = datetime.now()

            if not is_paused and self.app_start_time and self.last_combat_time > 0:
                anchor_ts = self.last_log_sync_time or self.app_start_time
                time_since_sync = now_ts - self.last_combat_time
                projected_now = anchor_ts + timedelta(seconds=time_since_sync)
                if projected_now > now_dt: projected_now = now_dt
                live_duration = (projected_now - self.app_start_time).total_seconds()
                
                if live_duration > duration:
                    duration = live_duration

            print(f"DURATION UPDATE: {duration:.2f}s (Damage: {damage_dealt})")

    app = MockApp()
    
    # Simulate first hit
    hit_time = datetime.now()
    print("--- FIRST HIT ---")
    app.process_external_event({"timestamp": hit_time, "damage": 100, "type": "dealt", "source": "You", "target": "Mob"})
    
    # Wait 0.5s
    time.sleep(0.5)
    print("--- TICK AFTER 0.5s (Simulating next update or manual refresh) ---")
    app.update_live_stats([e for e in app.all_events if e['timestamp'] >= app.app_start_time])

if __name__ == "__main__":
    test_duration_start()
