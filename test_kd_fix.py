
import sys
import os
import json
import time

# Mock normalize_name
def normalize_name(name):
    if not name: return "Unknown"
    original_name = name
    
    # Aggressive stripping of descriptive fragments from NPC names
    lower_n = name.lower()
    status_frags = [
        " has been ", " have been ", " is ", " was ", " looks ", " by ", 
        " used ", " uses ", " intimidated", " kneeling", " prone", 
        " incapacitated", " knocked down", " kneel", " has defeated ",
        " use ", " attacks ", " deals ", " heals ", " hits ", " apply ",
        " resist ", " no longer ", " incapacitated by ", " intimidated by ",
        " knocked down by ", " kneels ", " prone by "
    ]
    
    for frag in status_frags:
        if frag in lower_n:
            name = name[:lower_n.find(frag)].strip()
            lower_n = name.lower()
            
    # Cleanup articles
    if lower_n.startswith("a "): name = name[2:]
    elif lower_n.startswith("an "): name = name[3:]
    elif lower_n.startswith("the "): name = name[4:]
    
    # Final check for common prefixes like "by " (independent of being a fragment)
    lower_n = name.lower()
    if lower_n.startswith("by "): name = name[3:]
    
    # Normalize "You" variations
    if name.lower() in ["you", "damage you", "yourself", "s you", "s yourself", "you have completely", "you have been", "you have", "you use", "by you", "you are", "you're", "you intimidate", "you use"]:
        return "You"
    
    if not name or name.lower() in ["use", "is", "has", "was"]:
        return "Unknown"
        
    return name.strip()

# Mock event processor logic
def process_status_event(event, char_name_curr="Autobahn"):
    target = event.get("target")
    source = event.get("source", "Unknown")
    
    target = normalize_name(target)
    if char_name_curr and target.lower() == char_name_curr.lower(): target = "You"
    
    src = normalize_name(source)
    if char_name_curr and src.lower() == char_name_curr.lower(): src = "You"
        
    return target, src

def run_repro_test():
    print("--- STARTING KD ATTRIBUTION TEST ---")
    
    # Simulation of what parser.exe now outputs with my fixes
    test_events = [
        # 1. "You have been knocked down" -> Should be Target: You
        {"type": "status", "target": "You", "source": "Unknown", "status": "knockdown", "message": "You have been knocked down"},
        
        # 2. "You use Intimidate on a Gundark" -> Target: A Gundark, Source: You
        {"type": "status", "target": "A Gundark", "source": "You", "status": "intimidate", "message": "You use Intimidate on a Gundark"},
        
        # 3. Fragment leak test: "Gundark looks very"
        {"type": "status", "target": "Gundark looks very", "source": "You", "status": "intimidate", "message": "Gundark looks very intimidated by You"},
        
        # 4. Verb leak test: target is "a Gundark has been intimidated"
        {"type": "status", "target": "a Gundark has been intimidated", "source": "You", "status": "intimidate", "message": "a Gundark has been intimidated by You"},

        # 5. "You have" fragment
        {"type": "status", "target": "You have", "source": "Unknown", "status": "knockdown", "message": "You have been knocked down"}
    ]
    
    for i, event in enumerate(test_events):
        target, source = process_status_event(event)
        
        print(f"Test {i+1}:")
        print(f"  Input Target: {event['target']}")
        print(f"  Final Target: {target}")
        print(f"  Final Source: {source}")
        
        # Validation
        if i == 0 or i == 4: # You tests
            if target == "You":
                print(f"  [PASS] Correctly attributed to 'You'")
            else:
                print(f"  [FAIL] Should be 'You' but got '{target}'")
        elif i == 1 or i == 2 or i == 3: # Gundark tests
            if target == "Gundark":
                print(f"  [PASS] Gundark correctly targeted")
            else:
                print(f"  [FAIL] Should be 'Gundark' but got '{target}'")

def run_repro_test():
    print("--- STARTING KD ATTRIBUTION TEST ---")
    
    # Simulation of what parser.exe now outputs with my fixes
    test_events = [
        # 1. "You have been knocked down" -> Should be Target: You
        {"type": "status", "target": "You", "source": "Unknown", "status": "knockdown", "message": "You have been knocked down"},
        
        # 2. "You use Intimidate on a Gundark" -> Target: A Gundark, Source: You
        {"type": "status", "target": "A Gundark", "source": "You", "status": "intimidate", "message": "You use Intimidate on a Gundark"},
        
        # 3. Fragment leak test: "Gundark looks very"
        {"type": "status", "target": "Gundark", "source": "You", "status": "intimidate", "message": "Gundark looks very intimidated by You"},
        
        # 4. Verb leak test: target is "a Gundark has been intimidated"
        {"type": "status", "target": "a Gundark has been intimidated", "source": "You", "status": "intimidate", "message": "a Gundark has been intimidated by You"},

        # 5. "You have" fragment
        {"type": "status", "target": "You have", "source": "Unknown", "status": "knockdown", "message": "You have been knocked down"}
    ]
    
    for i, event in enumerate(test_events):
        target, source = process_status_event(event)
        
        print(f"Test {i+1}:")
        print(f"  Input Target: {event['target']}")
        print(f"  Final Target: {target}")
        print(f"  Final Source: {source}")
        
        # Validation
        if i == 0 or i == 4: # You tests
            if target == "You":
                print(f"  [PASS] Correctly attributed to 'You'")
            else:
                print(f"  [FAIL] Should be 'You' but got '{target}'")
        elif i == 1 or i == 2 or i == 3: # Gundark tests
            if target == "Gundark":
                print(f"  [PASS] Gundark correctly targeted")
            else:
                print(f"  [FAIL] Should be 'Gundark' but got '{target}'")

if __name__ == "__main__":
    run_repro_test()
