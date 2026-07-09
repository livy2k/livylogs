import os
import time
from datetime import datetime, timedelta

def create_mock_log(path, combat_lines):
    with open(path, "w") as f:
        for line in combat_lines:
            f.write(line + "\n")

def get_timestamp_str(delta_seconds=0):
    dt = datetime.now() + timedelta(seconds=delta_seconds)
    return dt.strftime("[%m/%d %H:%M:%S]")

log_path = "reproduce_issue.txt"

# 1. Create a log with old combat data (e.g., from 5 seconds ago)
old_ts = get_timestamp_str(-5)
combat_lines = [
    f"{old_ts} You hit a womp rat for 100 points of damage.",
    f"{old_ts} You hit a womp rat for 150 points of damage.",
]

print("--- Testing Initial Load with 'Recent' Old Data ---")
create_mock_log(log_path, combat_lines)

# We want to see if the app picks this up as a current session on start.
# Since it's < 10s old, the current logic says 'is_recent' is True, so it starts a session.
# The user says "started with old data", which confirms this happens.

# 2. Test manual reset
print("\n--- Testing Manual Reset ---")
# If we call reset, it should clear everything.
# But if analyze_log runs again and sees the same log file, does it re-add those events?
# If manual=True is passed to analyze_log, it clears all_events and sets last_read_offset to -1.
# -1 means seek to end. So it SHOULDN'T see old events.

# Let's check the code for analyze_log when manual=True:
# 1775: self.all_events = []
# 1776: self.last_read_offset = -1
# ...
# 1820: self.last_read_offset = -1
# 1821: is_initial_history_load = True
# ...
# 1840: new_events, new_offset = parse_combat_log(actual_file_path, self.last_read_offset)
# If last_read_offset is -1, parse_combat_log (which I should check) probably seeks to end.

# Wait, if parse_combat_log seeks to end, then new_events will be empty.
# If new_events is empty, app_start_time remains None.
# If app_start_time is None, the UI should be zeroed.

# Why did the user say "reset button didnt work"?
# Maybe because the UI refresh didn't happen correctly or some other state persisted.

print("Check complete. I will now examine parse_combat_log and the reset logic more closely.")
