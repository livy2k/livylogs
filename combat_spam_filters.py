"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.

Utility to parse SWG Lua command files and extract combatSpam values.
"""

import os
import re
import json

COMBAT_SPAM_FILTERS_FILE = "combat_spam_filters.json"
LUA_COMMANDS_DIR = r"C:\Users\LivyC\PycharmProjects\SWG\MMOCoreORB\bin\scripts\commands"

def _parse_lua_file(filepath):
    """Parse a single Lua file and return the combatSpam value if found."""
    combat_spam = None
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Look for combatSpam = "something"
        # Pattern: combatSpam\s*=\s*"([^"]+)"
        match = re.search(r'combatSpam\s*=\s*"([^"]+)"', content)
        if match:
            combat_spam = match.group(1).strip().lower()
    except Exception as e:
        print(f"[DEBUG] Error parsing {filepath}: {e}")
    return combat_spam

def scan_combat_spam_filters():
    """Scan the Lua commands directory and return a set of combatSpam values."""
    filters = set()
    if not os.path.exists(LUA_COMMANDS_DIR):
        print(f"[DEBUG] Lua commands directory not found: {LUA_COMMANDS_DIR}")
        return filters
    
    for filename in os.listdir(LUA_COMMANDS_DIR):
        if filename.endswith(".lua"):
            filepath = os.path.join(LUA_COMMANDS_DIR, filename)
            combat_spam = _parse_lua_file(filepath)
            if combat_spam:
                filters.add(combat_spam)
    
    print(f"[DEBUG] Found {len(filters)} combat spam filters from Lua files")
    return filters

def save_combat_spam_filters(filters):
    """Save the filters to a JSON file."""
    try:
        with open(COMBAT_SPAM_FILTERS_FILE, "w") as f:
            json.dump(sorted(list(filters)), f, indent=2)
        print(f"[DEBUG] Saved {len(filters)} combat spam filters to {COMBAT_SPAM_FILTERS_FILE}")
    except Exception as e:
        print(f"[DEBUG] Error saving combat spam filters: {e}")

def load_combat_spam_filters():
    """Load the filters from JSON file, or scan Lua files if not found."""
    if os.path.exists(COMBAT_SPAM_FILTERS_FILE):
        try:
            with open(COMBAT_SPAM_FILTERS_FILE, "r") as f:
                filters = set(json.load(f))
            print(f"[DEBUG] Loaded {len(filters)} combat spam filters from {COMBAT_SPAM_FILTERS_FILE}")
            return filters
        except Exception as e:
            print(f"[DEBUG] Error loading combat spam filters: {e}")
    
    # Scan Lua files
    filters = scan_combat_spam_filters()
    if filters:
        save_combat_spam_filters(filters)
    return filters
