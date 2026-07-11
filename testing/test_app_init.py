import tkinter as tk
from livylogs_main import CombatLogApp
import os

def test_app_init():
    root = tk.Tk()
    # Mock some basic things to avoid full start
    root.withdraw() 
    try:
        app = CombatLogApp(root)
        print("Success: App initialized without errors.")
        # Trigger a resize to check the gradient draw function
        app.main_title_bar.event_generate("<Configure>", width=400, height=35)
        root.update()
        print("Success: Gradient redraw triggered without errors.")
    except Exception as e:
        print(f"Failure: {e}")
        import traceback
        traceback.print_exc()
    finally:
        root.destroy()

if __name__ == "__main__":
    test_app_init()
