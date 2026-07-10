
import sys
import os
sys.path.append(os.getcwd())
import tkinter as tk
from windows.skimmers import SkimmersWindow
from constants import *
import time

class MockConfig:
    def get(self, section, key, fallback=None):
        return fallback
    def getint(self, section, key, fallback=0):
        return fallback

class MockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config = MockConfig()
        self.current_alpha = 1.0
        self.always_on_top = False
        self.inventory_full = False
        self.is_interacting = False
        self.player_classes = {}
        def refresh_ui_only(force=False): pass
        self.refresh_ui_only = refresh_ui_only
        self.player_data = {
            "Player1": {"lb_mobs": 5},
            "Player2": {"lb_mobs": 0},
            "You": {"lb_mobs": 10}
        }
        self.loot_data = {
            "Player1": [{"item": "Sword", "credits": False}],
            "Player2": [{"item": "100 Credits", "credits": True}],
            "You": [{"item": "Shield", "credits": False}]
        }
        self.char_name = tk.StringVar(value="Livy")
        self.skimmer_tab = "loot"
        self.skimmer_search_mode = False
        self.skimmer_search_query = tk.StringVar(value="")
        self.enable_sync = tk.BooleanVar(value=False)
        self.sync_data = None
        
        # Colors from constants if not available, but I'll define basics
        global PANEL_DARK, WINDOW_BG, ACCENT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT
        PANEL_DARK = "#1e1e1e"
        WINDOW_BG = "#121212"
        ACCENT_BLUE = "#007acc"
        TEXT_PRIMARY = "#ffffff"
        TEXT_SECONDARY = "#aaaaaa"
        TEXT_ACCENT = "#00ff00"

def test_skimmer_filtering():
    app = MockApp()
    win = SkimmersWindow(app)
    win.show(force_open=True)
    
    # Test Loot Tab filtering
    win.refresh(force=True)
    app.root.update() # Ensure UI builds
    print("Testing Loot Tab filtering...")
    # Give it a tiny bit of time for widgets to manifest
    app.root.after(100, lambda: None)
    app.root.update()
    players_shown = list(win._row_frames.keys()) if hasattr(win, '_row_frames') else []
    print(f"Players shown in Loot: {players_shown}")
    assert "Player1" in players_shown
    assert "You" in players_shown
    assert "Player2" not in players_shown, "Player2 should be filtered out as they only have credits"
    
    # Test Drilldown Nav Row
    print("Testing Drilldown Nav Row...")
    win.drill_down("Player1")
    win.refresh(force=True)
    app.root.update()
    if hasattr(win, 'nav_row') and win.nav_row.winfo_ismapped():
        print("Nav row is visible in drilldown")
    else:
        print("ERROR: Nav row is NOT visible in drilldown")
        # Let's check why
        print(f"is_drilldown: {win.is_drilldown}")
        print(f"item_detail_mode: {getattr(win, 'item_detail_mode', False)}")
        print(f"npc_detail_mode: {getattr(win, 'npc_detail_mode', False)}")

    # Test Mobs Tab filtering
    print("Testing Mobs Tab filtering...")
    app.skimmer_tab = "mobs"
    win.refresh(force=True)
    app.root.update()
    players_shown = list(win._row_frames.keys()) if hasattr(win, '_row_frames') else []
    print(f"Players shown in Mobs: {players_shown}")
    assert "Player1" in players_shown
    assert "You" in players_shown
    assert "Player2" not in players_shown, "Player2 should be filtered out as they have 0 mob kills"

    print("All tests passed!")
    app.root.destroy()

if __name__ == "__main__":
    try:
        test_skimmer_filtering()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
