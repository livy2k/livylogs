import tkinter as tk
import sys
import os
import time
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

def test_log_format():
    print("[TEST] Starting log format verification...")
    root = tk.Tk()
    root.withdraw()
    app = CombatLogApp(root)
    
    # Add various events
    # stats to create player
    app.process_external_event({"type": "stats", "name": "Livy", "damage": 5000, "healing": 200})
    app.process_external_event({"type": "stats", "name": "Boss_C", "damage": 1000, "healing": 0})
    
    # dealt event
    app.process_external_event({
        "type": "dealt", 
        "source": "Livy", 
        "target": "NPC_A", 
        "damage": 1234, 
        "ability": "Blaster Shot"
    })
    
    # healing event
    app.process_external_event({
        "type": "healing", 
        "source": "Livy", 
        "target": "Ally_B", 
        "healing": 567, 
        "ability": "Medpac"
    })
    
    # Boss_C deals damage to Livy -> TAKEN event for Livy
    app.process_external_event({
        "type": "dealt", 
        "source": "a Stormtrooper", 
        "target": "Livy", 
        "damage": 888, 
        "ability": "Blaster Shot"
    })

    # xp event
    app.process_external_event({
        "type": "xp",
        "source": "Livy",
        "amount": 100,
        "xp_type": "Combat"
    })

    # kill event
    app.process_external_event({
        "type": "mobs",
        "source": "Livy",
        "target": "NPC_A"
    })

    print("[TEST] Opening Details Window...")
    details = app.details_win
    details.show()
    details.drill_down("Livy")
    root.update()
    
    # Verify the text content in 'DEALT' tab (default)
    print("\n[TEST] Verifying DEALT tab content:")
    details.refresh(force=True)
    root.update()
    txt_content = details.txt.get("1.0", tk.END).strip()
    print(f"--- DEALT LOGS ---\n{txt_content}\n-----------------")
    
    # Check if format is "amount detail time"
    lines = txt_content.split('\n')
    for line in lines:
        if not line: continue
        parts = line.split('\t')
        print(f"Line parts: {parts}")
        if len(parts) >= 2:
             # Check if first part is a number (possibly with commas)
             amount = parts[0].strip().replace(',', '')
             if amount.isdigit():
                 print(f"SUCCESS: Found amount {parts[0].strip()}")
             else:
                 print(f"WARNING: First part '{parts[0]}' is not a digit.")
        else:
             print(f"FAILURE: Line '{line}' does not have enough tab-separated columns.")

    # Switch to TAKEN tab
    print("\n[TEST] Verifying TAKEN tab content:")
    app.details_tab = 'taken'
    details.refresh(force=True)
    root.update()
    txt_content = details.txt.get("1.0", tk.END).strip()
    print(f"--- TAKEN LOGS ---\n{txt_content}\n-----------------")
    
    lines = txt_content.split('\n')
    for line in lines:
        if not line: continue
        parts = line.split('\t')
        print(f"Line parts: {parts}")
        if len(parts) >= 2:
             amount = parts[0].strip().replace(',', '')
             if amount.isdigit():
                 print(f"SUCCESS: Found amount {parts[0].strip()}")
             else:
                 print(f"WARNING: First part '{parts[0]}' is not a digit.")

    print("\n[TEST] Test completed.")
    app.on_exit()
    root.destroy()

if __name__ == "__main__":
    test_log_format()
