
import tkinter as tk
from windows.calculator import CalculatorWindow
import math

class MockConfig:
    def get(self, *args, **kwargs): return None
    def getint(self, *args, **kwargs): return kwargs.get('fallback', 0)

class MockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config = MockConfig()
        self.always_on_top = True
        self.current_alpha = 1.0
        self.calc_win = None

def test_calculator():
    app = MockApp()
    calc = CalculatorWindow(app)
    calc.show()
    
    print("Testing basic operations...")
    # Test 7 + 3 = 10
    calc.on_button_click('7')
    calc.on_button_click('+')
    calc.on_button_click('3')
    calc.calculate()
    res = calc.display_var.get()
    print(f"7 + 3 = {res}")
    assert res == "10"
    
    # Test Clear
    calc.on_button_click('C')
    assert calc.display_var.get() == "0"
    
    # Test sin(90) = 1
    calc.on_button_click('sin')
    calc.on_button_click('9')
    calc.on_button_click('0')
    calc.on_button_click(')')
    calc.calculate()
    res = calc.display_var.get()
    print(f"sin(90) = {res}")
    assert res == "1"
    
    # Test log(100) = 2
    calc.on_button_click('C')
    calc.on_button_click('log')
    calc.on_button_click('1')
    calc.on_button_click('0')
    calc.on_button_click('0')
    calc.on_button_click(')')
    calc.calculate()
    res = calc.display_var.get()
    print(f"log(100) = {res}")
    assert res == "2"
    
    # Test sqrt(16) = 4
    calc.on_button_click('C')
    calc.on_button_click('sqrt')
    calc.on_button_click('1')
    calc.on_button_click('6')
    calc.on_button_click(')')
    calc.calculate()
    res = calc.display_var.get()
    print(f"sqrt(16) = {res}")
    assert res == "4"

    print("Calculator tests passed!")
    app.root.destroy()

if __name__ == "__main__":
    test_calculator()
