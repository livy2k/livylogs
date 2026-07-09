import os
import time
from datetime import datetime, timedelta

def parse_mock_log(file_path, start_offset=0):
    events = []
    with open(file_path, "r") as f:
        if start_offset > 0:
            f.seek(start_offset)
        lines = f.readlines()
        for line in lines:
            # Simple mock parser for [MM/DD HH:MM:SS] You hit ...
            try:
                ts_str = line[1:15]
                ts = datetime.strptime(ts_str, "%m/%d %H:%M:%S")
                # Adjust year to current year
                ts = ts.replace(year=datetime.now().year)
                
                damage = 0
                if "hit" in line:
                    parts = line.split("for ")
                    if len(parts) > 1:
                        damage = int(parts[1].split(" ")[0])
                
                events.append({
                    "timestamp": ts,
                    "damage": damage,
                    "type": "dealt" if damage > 0 else "info",
                    "source": "You",
                    "target": "Target",
                    "healing": 0,
                    "item": None
                })
            except:
                continue
    return events, os.path.getsize(file_path)

# Mocking the app state
class MockApp:
    def __init__(self):
        self.actual_app_start_time = datetime.now()
        self.app_start_time = None
        self.all_events = []
        self.last_read_offset = 0
        self.last_processed_file = None
        self.time_window_dm = 10
        self.last_combat_time = 0
        
    def test_logic(self, new_events, is_initial_history_load):
        now_dt = datetime.now()
        now_ts = time.time()
        
        if new_events:
            if self.app_start_time is None:
                # CURRENT LOGIC in livylogs.py
                damage_events = [
                    e for e in new_events 
                    if e["damage"] > 0 and e["timestamp"] and e["timestamp"] >= self.actual_app_start_time
                ]
                if damage_events:
                    latest_damage_ts = max(e["timestamp"] for e in damage_events)
                    is_recent = (datetime.now() - latest_damage_ts).total_seconds() < 10
                    
                    if not is_initial_history_load: # Simplified
                        self.app_start_time = min(e["timestamp"] for e in damage_events)
                        print(f"DEBUG: Initialized app_start_time to {self.app_start_time}")
                    else:
                        print("DEBUG: is_initial_history_load is True")
                else:
                    print("DEBUG: No damage events >= actual_app_start_time")

def run_repro():
    app = MockApp()
    log_path = "repro_log.txt"
    
    # 1. Create a log with an old entry from 1 hour ago
    one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("[%m/%d %H:%M:%S]")
    with open(log_path, "w") as f:
        f.write(f"{one_hour_ago} You hit a target for 100 points of damage.\n")
    
    print(f"Actual App Start: {app.actual_app_start_time}")
    
    # Simulate selecting this log as "new"
    # In change_log_path: self.app_start_time = None
    # then analyze_log(manual=True)
    # manual=True sets self.last_read_offset = -1
    
    # In analyze_log:
    app.app_start_time = None
    app.last_read_offset = -1
    
    # Simulate parse_combat_log(manual=True) -> it usually reads last 256KB
    # Here we just read the whole file for the mock
    new_events, _ = parse_mock_log(log_path)
    
    print(f"Parsed event TS: {new_events[0]['timestamp']}")
    
    app.test_logic(new_events, is_initial_history_load=True)
    
    if app.app_start_time:
        duration = (datetime.now() - app.app_start_time).total_seconds()
        print(f"Duration: {duration}")
    else:
        print("No session started.")

run_repro()
