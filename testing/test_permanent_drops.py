import json
import os
import time
from datetime import datetime
from livylogs_main import CombatLogApp
import tkinter as tk

def test_permanent_drops():
    root = tk.Tk()
    root.withdraw()
    app = CombatLogApp(root)
    
    # Mock some loot events
    loot_event_1 = {
        "type": "loot",
        "source": "Livy",
        "item": "Krayt Tissue",
        "target": "a Krayt Dragon",
        "timestamp": datetime.now()
    }
    
    loot_event_2 = {
        "type": "loot",
        "source": "Livy",
        "item": "Krayt Tissue",
        "target": "Ancient Krayt Dragon",
        "timestamp": datetime.now()
    }
    
    loot_event_3 = {
        "type": "loot",
        "source": "Livy",
        "item": "Power Crystal",
        "target": "Imperial Trooper",
        "timestamp": datetime.now()
    }
    
    print("Processing loot events...")
    app.process_external_event(loot_event_1)
    app.process_external_event(loot_event_2)
    app.process_external_event(loot_event_3)
    
    print("Drops in memory:", app.permanent_drops)
    
    # Check if mappings are correct
    assert "Krayt Tissue" in app.permanent_drops
    assert "Krayt Dragon" in app.permanent_drops["Krayt Tissue"]
    assert "Ancient Krayt Dragon" in app.permanent_drops["Krayt Tissue"]
    assert "Power Crystal" in app.permanent_drops
    assert "Imperial Trooper" in app.permanent_drops["Power Crystal"]
    
    print("Saving drops...")
    app.save_permanent_drops()
    
    # Check if file exists
    assert os.path.exists("drops.json")
    
    with open("drops.json", "r") as f:
        saved_data = json.load(f)
    print("Saved data:", saved_data)
    
    # Test loading
    app_new = CombatLogApp(tk.Tk())
    app_new.root.withdraw()
    print("Drops after reload:", app_new.permanent_drops)
    assert app_new.permanent_drops == saved_data
    
    print("Test passed!")
    
    # Cleanup
    if os.path.exists("drops.json"):
        os.remove("drops.json")
    root.destroy()

if __name__ == "__main__":
    test_permanent_drops()
