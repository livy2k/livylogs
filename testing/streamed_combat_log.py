import time
import os

def create_streamed_log(filename):
    lines = [
        "[Spatial] [12:00:01] Livy: 123",
        "[Spatial] [12:00:02] Turd: 123",
        "[Spatial] [12:00:05] Slinky: 123",
        "[Combat] [12:00:10] Enemy1 attacks You for 100 points of damage.",
        "[Combat] [12:00:12] You hit Enemy1 with Fire Knockdown for 50 points of damage.",
        "[Combat] [12:00:15] Enemy1 has been incapacitated by You.",
        "[Combat] [12:00:20] You apply poison to Enemy1.",
        "[Combat] [12:00:25] Enemy2 uses Intimidate on Turd for 0.",
        "[Combat] [12:00:30] Turd no longer intimidated.",
        "[Combat] [12:00:35] Enemy1 has died.",
        "[Combat] [12:00:40] Enemy2 has been incapacitated by Slinky.",
        "[Combat] [12:00:45] Enemy2 has been incapacitated by Slinky.",
        "[Combat] [12:00:50] Slinky has died.",
        "[Combat] [12:01:00] You have been incapacitated by Enemy2.",
    ]
    
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
            f.flush()
            print(f"Logged: {line}")
            time.sleep(0.5) # Simulate streaming

if __name__ == "__main__":
    log_file = "testing/streamed_combat_log.txt"
    if os.path.exists(log_file):
        os.remove(log_file)
    create_streamed_log(log_file)
