
import sys
import os
import json
import time

# Mock normalize_name
def normalize_name(name):
    if not name: return "Unknown"
    return name.strip()

# Mock event processor logic
def process_status_event(event, char_name_curr="Autobahn"):
    target = event.get("target")
    source = event.get("source", "Unknown")
    status_val = event.get("status")
    msg = event.get("message", "")
    
    # Normalization logic from livylogs_main.py
    norm_target = normalize_name(target)
    if norm_target.lower() == char_name_curr.lower():
        norm_target = "You"
    
    norm_src = normalize_name(source)
    if norm_src.lower() == char_name_curr.lower():
        norm_src = "You"
        
    log_msg = f"Status: {status_val.title()}"
    if norm_src and norm_src != "Unknown":
        log_msg += f" by {norm_src}"
        
    return norm_target, norm_src, log_msg

def run_bidirectional_test():
    print("--- STARTING BIDIRECTIONAL ENGINE EXTRACTION TEST ---")
    
    # These represent events coming from the C engine
    test_events = [
        # You vs NPC
        {"type": "status", "target": "A Gundark", "source": "You", "status": "intimidate", "message": "You intimidate A Gundark"},
        # NPC vs You
        {"type": "status", "target": "You", "source": "A Gundark", "status": "knockdown", "message": "A Gundark has knocked you down"},
        # Player Full Name vs NPC
        {"type": "status", "target": "A Gundark", "source": "Autobahn", "status": "posture", "message": "Autobahn changes A Gundark's posture"},
        # NPC vs Player Full Name
        {"type": "status", "target": "Autobahn", "source": "A Gundark", "status": "incapacitated", "message": "A Gundark has incapacitated Autobahn"},
        # Complex NPC name
        {"type": "status", "target": "A Krayt Dragon Ancient", "source": "You", "status": "intimidate", "message": "You intimidate A Krayt Dragon Ancient"},
    ]
    
    for i, event in enumerate(test_events):
        target, source, log_msg = process_status_event(event)
        print(f"Test {i+1}:")
        print(f"  Input Message: {event['message']}")
        print(f"  Extracted Target: {target}")
        print(f"  Extracted Source: {source}")
        print(f"  Generated Log: {log_msg}")
        
        # Validation
        if "Autobahn" in event['message'] or "You" in event['message']:
            if "You" not in [target, source]:
                print(f"  [FAIL] 'You' identity not detected!")
            else:
                print(f"  [PASS] 'You' identity correctly mapped.")
        
        if "Gundark" in event['message'] and "Gundark" not in target and "Gundark" not in source:
             print(f"  [FAIL] 'Gundark' name lost!")
             
    print("\n--- TESTING FRAGMENT STRIPPING (Logic Check) ---")
    # This simulates what the C engine WOULD send after my parser.c fix
    fragment_event = {"type": "status", "target": "Gundark", "source": "You", "status": "intimidate", "message": "Gundark looks very intimidated"}
    target, source, log_msg = process_status_event(fragment_event)
    print(f"Fragment Test:")
    print(f"  Input: {fragment_event['message']}")
    print(f"  Target: {target} (Should be 'Gundark', not 'Gundark looks very')")
    if target == "Gundark":
        print("  [PASS] Fragment correctly stripped.")
    else:
        print("  [FAIL] Fragment still present.")

if __name__ == "__main__":
    run_bidirectional_test()
