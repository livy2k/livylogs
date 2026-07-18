
import sys
import os
import re

# Simulate the normalization and logic on the player name specifically
def simulate_fix(raw_name, char_name):
    from utils import normalize_name
    
    print(f"Testing input: '{raw_name}' with character name: '{char_name}'")
    
    # 1. Normalize
    norm = normalize_name(raw_name)
    print(f"  Step 1 (normalize_name): '{norm}'")
    
    # 2. Character Name Check (Python side logic)
    if char_name and norm.lower() == char_name.lower():
        norm = "You"
    elif "you" in norm.lower():
        norm = "You"
        
    print(f"  Step 2 (Identity Mapping): '{norm}'")
    return norm

if __name__ == "__main__":
    # Test cases based on the image and user reports
    char_name = "IiIiIiIi"
    test_cases = [
        "IiIiIiIi stands up.",
        "IiIiIiIi stands up",
        "IiIiIiIi falls down when he tries to change posture!",
        "IiIiIiIi kneels.",
        "IiIiIiIi",
        "IiIiIiIi looks very intimidated by you!",
        "A Gundark has been intimidated",
        "You have been knocked down"
    ]
    
    print(f"{'INPUT':<60} | {'FINAL RESULT'}")
    print("-" * 80)
    for tc in test_cases:
        res = simulate_fix(tc, char_name)
        print(f"FINAL: {res}")
        print()
