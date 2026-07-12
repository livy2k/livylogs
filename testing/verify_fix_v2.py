import tkinter as tk
import os
import sys

# Add current dir to path to import local modules
sys.path.append(os.getcwd())

from windows.livius import LiviusWindow
from constants import WINDOW_BG

class MockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.current_alpha = 1.0
        self.config = self._MockConfig()
        # Mock other expected app attributes
        self.friendly_players = set()
        self.enemy_players = set()
        self.player_arrival_order = []
        self.status_cooldowns = {}
        self.is_interacting = False
        self.last_interaction_time = 0
        self.target_alpha = 1.0
        
    class _MockConfig:
        def getint(self, section, option, fallback=None):
            return fallback
        def get(self, section, option, fallback=None):
            return fallback
    
    def save_config(self):
        pass
    def refresh_ui_only(self, force=True):
        pass
    def save_size(self, e):
        pass
    def _get_managed_windows(self):
        return []

def test_livius_init():
    print("Testing LiviusWindow initialization and title bar logic...")
    app = MockApp()
    try:
        # This will trigger __init__ -> BasePopoutWindow.__init__ -> show() -> _draw_title_gradient
        win = LiviusWindow(app)
        win.show()
        print("LiviusWindow created successfully.")
        
        # Manually trigger the gradient draw which caused the crash
        if hasattr(win, '_draw_title_gradient'):
            print("Manually triggering _draw_title_gradient...")
            win._draw_title_gradient()
            print("_draw_title_gradient executed without crash.")
        
        # Test a refresh cycle
        print("Testing refresh cycle...")
        win.refresh(force=True)
        print("Refresh executed without crash.")
        
        win.close()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        app.root.destroy()

if __name__ == "__main__":
    test_livius_init()
    print("Verification successful!")
