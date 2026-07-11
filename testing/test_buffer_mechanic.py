
import tkinter as tk
from windows.hit_miss_calc import HitMissCalcWindow

import configparser

class MockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.current_alpha = 1.0
        self.config = configparser.ConfigParser()
        self.config.add_section("HitMissCalcWindow")
        self.config.set("HitMissCalcWindow", "x", "100")
        self.config.set("HitMissCalcWindow", "y", "100")
        self.config.set("HitMissCalcWindow", "width", "450")
        self.config.set("HitMissCalcWindow", "height", "850")
        self.always_on_top = False

def test_buffer_mechanic():
    app = MockApp()
    win = HitMissCalcWindow(app)
    win.show(force_open=True)
    
    # Test Case A: No Buffer Pete
    # skillBoxMod = 100, tapeBonus = 25. Total Raw = 125.
    # Intimidated (-20) -> 105. Capped at 125 -> 105. Final = 105.
    win.inputs["def_skill"].set("100")
    win.inputs["def_tapes"].set("25")
    win.inputs["def_intimidated"].set(True)
    win.calculate()
    
    summary = win.summary_var.get()
    print(f"Test A Summary:\n{summary}")
    # We expect Base Defense to be 105 (Raw 125 -> Capped 105)
    if "Net Defense: 105" in summary:
        print("Test A PASSED")
    else:
        print("Test A FAILED")

    # Test Case B: Stacked Steve
    # skillBoxMod = 140, tapeBonus = 25. Total Raw = 165.
    # Intimidated (-20) -> 145. Capped at 125 -> 125. Final = 125.
    win.inputs["def_skill"].set("140")
    win.inputs["def_tapes"].set("25")
    win.inputs["def_intimidated"].set(True)
    win.calculate()
    
    summary = win.summary_var.get()
    print(f"\nTest B Summary:\n{summary}")
    # We expect Base Defense to be 125 (Raw 165 -> Capped 125)
    if "Net Defense: 125" in summary:
        print("Test B PASSED")
    else:
        print("Test B FAILED")

    # Test Case C: Over-capped + Food (+20)
    # Final = 125 + 20 = 145.
    win.inputs["def_food"].set("20")
    win.calculate()
    
    summary = win.summary_var.get()
    print(f"\nTest C Summary:\n{summary}")
    if "Net Defense: 145" in summary:
        print("Test C PASSED")
    else:
        print("Test C FAILED")

    win.window.destroy()
    app.root.destroy()

if __name__ == "__main__":
    test_buffer_mechanic()
