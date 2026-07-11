import tkinter as tk
import configparser
from windows.resists_calc import ResistsCalcWindow

class MockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.current_alpha = 1.0
        self.config = configparser.ConfigParser()
        self.config.add_section("ResistsCalcWindow")
        self.config.set("ResistsCalcWindow", "x", "100")
        self.config.set("ResistsCalcWindow", "y", "100")
        self.config.set("ResistsCalcWindow", "width", "400")
        self.config.set("ResistsCalcWindow", "height", "500")
        self.always_on_top = False

def test_resists_logic():
    app = MockApp()
    win = ResistsCalcWindow(app)
    win.show(force_open=True)
    
    # Test Case 1: Equal values (Resist 50, Potency 50)
    # Expected: 50 - 50 = 0%
    win.inputs["poison_res"].set("50")
    win.inputs["poison_potency"].set("50")
    win.calculate()
    
    chance = win.chance_var.get()
    print(f"Test 1 (50 vs 50 Application): {chance}")
    if "0.0%" in chance: 
        print("Test 1 PASSED")
    else:
        print(f"Test 1 FAILED (Expected 0.0%)")

    # Test Case 2: Re-separated Mitigation Logic (Base 1000, Resist 0, Potency 50, Absorb 45%)
    # Expected:
    # 1. Application: 50 - 0 = 50.0%
    # 2. Skill Absorb = 45% -> 1000 * (1 - 0.45) = 550
    # 3. Doc Absorb = 45% -> 550 * (1 - 0.45) = 302.5 -> round(302.5) = 302
    win.inputs["base_tick"].set("1000")
    win.inputs["poison_res"].set("0") # Resistance
    win.inputs["poison_potency"].set("50")
    win.inputs["poison_absorb"].set("45") # Absorption
    win.jedi_enabled.set(False)
    win.calculate()
    
    tick = win.final_tick_var.get()
    chance = win.chance_var.get()
    print(f"Test 2 (1000, 45% Absorb, 0 Resist): {tick} | {chance}")
    if "302" in tick and "50.0%" in chance:
        print("Test 2 PASSED")
    else:
        print(f"Test 2 FAILED (Got {tick} | {chance})")

    # Test Case 3: Jedi Resist Cap (Base 1000, Absorb 0, Jedi Active)
    # Expected: Jedi is 50%. 1000 * (1 - 0.5) = 500
    win.inputs["poison_absorb"].set("0")
    win.jedi_enabled.set(True)
    win.calculate()
    
    tick = win.final_tick_var.get()
    print(f"Test 3 (1000, 0 Absorb + Jedi): {tick}")
    if "500" in tick:
        print("Test 3 PASSED")
    else:
        print(f"Test 3 FAILED (Got {tick})")

    # Test Case 3b: Jedi + Doc Cap (Base 1000, Absorb 50, Jedi Active)
    # Expected: 50% skill absorb -> 500. 
    # Buff portion (Doc + Jedi) capped at 50%. 
    # 500 * (1 - 0.5) = 250.
    win.inputs["poison_absorb"].set("50")
    win.jedi_enabled.set(True)
    win.calculate()
    tick = win.final_tick_var.get()
    mitigation = win.mitigation_var.get()
    print(f"Test 3b (1000, 50 Absorb + Jedi): {tick} | {mitigation}")
    if "250" in tick:
        print("Test 3b PASSED")
    else:
        print(f"Test 3b FAILED (Got {tick})")

    # Test Case 4: Absorption Skill Cap (Base 1000, Absorb 80)
    # Skill absorb capped at 50% -> 1000 * 0.5 = 500
    # Doc absorb = 80%. Buff portion capped at 50%. -> 500 * 0.5 = 250
    win.inputs["base_tick"].set("1000")
    win.inputs["poison_absorb"].set("80")
    win.jedi_enabled.set(False)
    win.calculate()
    
    tick = win.final_tick_var.get()
    print(f"Test 4 (1000, 80 Absorb): {tick}")
    if "250" in tick:
        print("Test 4 PASSED")
    else:
        print(f"Test 4 FAILED (Got {tick})")

    # Test Case 5: Resistance doesn't affect mitigation
    # poison_res = 100 (100% resist)
    # poison_absorb = 0 (0% mitigation)
    # Attacker Potency = 50.
    # Stick Chance = max(0, 50 - 100) = 0.0%
    win.inputs["poison_res"].set("100")
    win.inputs["poison_potency"].set("50")
    win.inputs["poison_absorb"].set("0")
    win.calculate()
    tick = win.final_tick_var.get()
    chance = win.chance_var.get()
    print(f"Test 5 (100 Resist, 50 Potency, 0 Absorb): {tick} | {chance}")
    if "1,000" in tick and "0.0%" in chance:
        print("Test 5 PASSED")
    else:
        print(f"Test 5 FAILED (Got {tick} | {chance})")

    win.window.destroy()
    app.root.destroy()

if __name__ == "__main__":
    test_resists_logic()
