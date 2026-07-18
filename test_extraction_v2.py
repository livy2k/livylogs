
import sys
import os
import json
import time

# Mock normalize_name
def normalize_name(name):
    if not name: return "Unknown"
    # Basic normalization to simulate Python side
    name = name.strip()
    if name.lower().startswith("[group] "):
        name = name[8:].strip()
    return name

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

def run_extraction_test():
    print("--- STARTING UPDATED ENGINE EXTRACTION TEST ---")
    
    # Simulated output from new parser.exe (after my C changes)
    # The C code now handles the stripping, so 'target' and 'source' fields 
    # should be clean when they hit Python.
    
    test_cases = [
        # Case 1: Spatial/Timestamp prefix + Domination
        {
            "line": "[Spatial] 14:56:36 You use Domination on a Gundark for 2915 points of damage!",
            "expected_target": "a Gundark",
            "expected_source": "You",
            "expected_status": "domination"
        },
        # Case 2: Attacks pattern
        {
            "line": "[Spatial] 14:56:29 a Gundark attacks you for 252 points of damage!",
            "expected_target": "you",
            "expected_source": "a Gundark",
            "expected_status": "knockdown" # Assuming 'attacks' might imply knockdown in some contexts or just testing name extraction
        },
        # Case 3: Combat bracket + Has been pattern
        {
            "line": "[Combat] 12:00:00 A Gundark has been incapacitated by You.",
            "expected_target": "A Gundark",
            "expected_source": "You",
            "expected_status": "incapacitated"
        }
    ]

    # I'll manually run the C stripping logic in Python to verify my C logic works
    def c_strip(l):
        clean = l
        if clean.startswith('['):
            idx = clean.find(']')
            if idx != -1:
                clean = clean[idx+1:].strip()
                if clean.startswith('['):
                    idx2 = clean.find(']')
                    if idx2 != -1:
                        clean = clean[idx2+1:].strip()
        
        while clean.startswith(' '): clean = clean[1:]
        
        # Timestamp 00:00:00
        if len(clean) >= 8 and clean[0].isdigit() and clean[1].isdigit() and clean[2] == ':':
             clean = clean[8:].strip()
        
        while clean.startswith(' '): clean = clean[1:]
        
        if clean.startswith('['):
            idx = clean.find(']')
            if idx != -1:
                clean = clean[idx+1:].strip()
        
        return clean

    for i, case in enumerate(test_cases):
        print(f"\nTest {i+1}:")
        clean = c_strip(case["line"])
        print(f"  Stripped line: '{clean}'")
        
        # Simulating Case 3 (use/on) or Case 4 (attacks) extraction logic from C
        lower = clean.lower()
        target = "Unknown"
        source = "Unknown"
        
        if "use " in lower and " on " in lower:
            p_use = lower.find("use ")
            p_on = lower.find(" on ")
            source = clean[:p_use].strip()
            if not source: source = "You"
            target = clean[p_on+4:].strip()
            p_for = target.lower().find(" for ")
            if p_for != -1: target = target[:p_for]
            if target.endswith('!'): target = target[:-1]
            target = target.strip()
        elif " attacks " in lower:
            p_att = lower.find(" attacks ")
            source = clean[:p_att].strip()
            target = clean[p_att+9:].strip()
            p_for = target.lower().find(" for ")
            if p_for != -1: target = target[:p_for]
            target = target.strip()
        elif " has been " in lower:
            p_hb = lower.find(" has been ")
            target = clean[:p_hb].strip()
            p_by = lower.find(" by ")
            if p_by != -1:
                source = clean[p_by+4:].strip()
                if source.endswith('.'): source = source[:-1]
            target = target.strip()
            
        print(f"  Extracted Source: '{source}'")
        print(f"  Extracted Target: '{target}'")
        
        if source.lower() == case["expected_source"].lower() and target.lower() == case["expected_target"].lower():
            print("  [PASS] Extraction matches expectation.")
        else:
            print(f"  [FAIL] Expected {case['expected_source']} -> {case['expected_target']}")

if __name__ == "__main__":
    run_extraction_test()
