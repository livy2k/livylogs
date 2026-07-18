import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from utils import normalize_name

def test_normalization():
    test_cases = [
        ("Queue Fives [Combat]", "Queue Fives"),
        ("A Gundark [Spatial]", "Gundark"),
        ("[Spatial] Queue Fives", "Queue Fives"),
        ("Queue Fives looks very intimidated by you!", "Queue Fives"),
        ("by you!", "You"),
        ("intimidated by you", "You"),
        ("IiIiIiIi stands up", "IiIiIiIi"),
        ("a Krayt Dragon [Group]", "Krayt Dragon"),
        ("SomeName [Tell]", "SomeName"),
        ("ou", "You"),
        ("ou!", "You"),
        ("by ou", "You"),
        ("you       enter of being     in", "Unknown"),
    ]
    
    passed = 0
    for input_name, expected in test_cases:
        result = normalize_name(input_name)
        if result == expected:
            print(f"PASS: '{input_name}' -> '{result}'")
            passed += 1
        else:
            print(f"FAIL: '{input_name}' -> '{result}' (expected '{expected}')")
            
    print(f"\nPassed {passed}/{len(test_cases)} tests.")
    return passed == len(test_cases)

if __name__ == "__main__":
    test_normalization()
