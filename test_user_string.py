
import sys
import os

# Updated normalize_name with new fixes
def normalize_name(name):
    if not name: return "Unknown"
    original_name = name
    
    # Aggressive stripping of descriptive fragments from NPC names
    lower_n = name.lower()
    status_frags = [
        " looks very intimidated by you", " looks very", " has been ", " have been ", 
        " is ", " was ", " looks ", " by ", 
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
    while True:
        original_loop_name = name
        lower_n = name.lower()
        if lower_n.startswith("a "): name = name[2:]
        elif lower_n.startswith("an "): name = name[3:]
        elif lower_n.startswith("the "): name = name[4:]
        
        if name == original_loop_name:
            break
            
    # Final check for common prefixes like "by "
    lower_n = name.lower()
    if lower_n.startswith("by "): name = name[3:]
    
    # Normalize "You" variations
    if name.lower() in ["you", "damage you", "yourself", "s you", "s yourself", "you have completely", "you have been", "you have", "you use", "by you", "you are", "you're", "you intimidate", "you use", "you!"]:
        return "You"
    
    if not name or name.lower() in ["use", "is", "has", "was"]:
        return "Unknown"
        
    return name.strip()

def test_user_string():
    print("--- TESTING USER STRING ---")
    user_input = "Queue Fives looks very intimidated by you!"
    # The parser might return this whole thing as a target if it fails to split.
    # Or it might return "Queue Fives looks very" as the target.
    
    cases = [
        "Queue Fives looks very intimidated by you!",
        "Queue Fives looks very",
        "Queue Fives"
    ]
    
    for case in cases:
        result = normalize_name(case)
        print(f"Input: '{case}' -> Normalized: '{result}'")
        if result == "Queue Fives":
            print("  [PASS] Correctly resolved to Queue Fives")
        else:
            print(f"  [FAIL] Got '{result}'")

if __name__ == "__main__":
    test_user_string()
