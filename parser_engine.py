import re
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import ctypes
from ctypes import wintypes
from constants import kernel32

def parse_combat_log(file_path, start_offset=0):
    """Parse a combat log and return damage events."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file does not exist: {file_path}")
    if not path.is_file():
        raise ValueError(f"Selected path is not a file: {file_path}")

    file_size = path.stat().st_size
    if file_size == 0:
        return [], 0
    
    read_offset = start_offset
    if read_offset == -1:
        read_offset = max(0, file_size - 256 * 1024)

    events = []
    timestamp_pattern = re.compile(r"\[?(\d{4}-\d{2}-\d{2} )?(\d{2}:\d{2}:\d{2})\]?")
    
    # Improved SWG pattern
    # Handles: Source [action] [ability] on Target for Amount [unit]
    swg_pattern = re.compile(
        r"^(?P<source>you|.+?)\s+(?P<action>uses|use|attacks|attack|deals|deal|heals|heal|hits|hit)\b\s+(?:(?P<ability>.+?)\s+(?:on|to|for)\s+)?(?P<target>.+?)\s+for\s+(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>damage|dmg|points|health)?",
        re.IGNORECASE
    )
    
    # Mitigation pattern
    mitigation_suffix = re.compile(r",?\s+but\s+(?:he|she|it|you)\s+(?P<mitigation>evades|evaded|dodges|parries|blocks it|counterattacks)(?:\s+it)?", re.IGNORECASE)
    
    swg_keywords = ["uses", "use", "attacks", "attack", "deals", "deal", "heals", "heal", "hits", "hit"]
    mitigation_keywords = ["counterattacks", "blocks it", "misses", "evades", "evaded", "dodges", "parries", "counterattack"]
    pvp_kws = ["has bested"]
    msg_kws = ["says", "shouts", "whispers", "tells", "emotes", "performs", "is", "has", "does", "goes", "starts", "stops", "completes"]
    act_kws = ["is", "has", "does", "goes", "starts", "stops", "completes", "stands", "kneels", "performs", "sits", "says", "shouts", "whispers", "tells", "emotes", "tosses", "nods", "waves", "smiles", "laughs", "cheers", "misses", "evade", "dodge", "parr", "block", "counterattack", "attack", "use", "hit"]
    death_kws = ["has died"]
    loot_kws = ["looted", "you cannot loot that item"]
    cmd_kws = ["log"]

    prevented_pattern = re.compile(r"armor prevented (?P<amount>\d+(?:\.\d+)?)\s*(?:damage|dmg|points)", re.IGNORECASE)

    activity_patterns = [
        (re.compile(r'(?:\[PvPBroadcasts\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?\[PvPBroadcasts\]\s+:\s+(?P<winner>.+?)\s+has bested\s+(?P<loser>.+?)\s+in GCW combat\.', re.IGNORECASE), pvp_kws),
        (re.compile(r'(?:\[Spatial\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>.+?)\s+says,\s+"(?P<command>log\d+)"', re.IGNORECASE), cmd_kws),
        (re.compile(r'".+",\s+(?P<name>.+?)\s+(?P<action>says|shouts|whispers|tells|emotes|performs|is|has|does|goes|starts|stops|completes)\b', re.IGNORECASE), msg_kws),
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>you|.+?)\s+(?P<action>is|has|does|goes|starts|stops|completes|stands|kneels|performs|sits|says|shouts|whispers|tells|emotes|tosses|nods|waves|smiles|laughs|cheers|misses|evades|evaded|dodges|parries|blocks|counterattacks|attacks|uses|hit|hits)\b', re.IGNORECASE), act_kws),
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?:\[GROUP\]\s+)?(?P<name>.+?) has died\.', re.IGNORECASE), death_kws),
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?:\[GROUP\]\s+)?(?P<name>.+?) looted (?P<item>.+?) from (?P<target>.+?)\.', re.IGNORECASE), loot_kws),
        (re.compile(r'(?:(?:\[\w+\]|\[None\])\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?You cannot loot that item because your inventory is full\.', re.IGNORECASE), loot_kws)
    ]

    with path.open("r", encoding="utf-8", errors="replace") as log_file:
        if read_offset > 0:
            log_file.seek(read_offset)
            log_file.readline()
        
        current_offset = log_file.tell()
        line_number = 0
        last_taken_event = None
        while True:
            line = log_file.readline()
            if not line: break
            
            line_number += 1
            original_line = line.strip()
            if not original_line:
                current_offset = log_file.tell()
                continue
            
            if "[GroupChat]" in original_line or "[Instant Messages]" in original_line:
                current_offset = log_file.tell()
                continue

            ts_match = timestamp_pattern.search(original_line)
            timestamp = None
            if ts_match:
                ts_str = ts_match.group(2)
                try:
                    timestamp = datetime.strptime(ts_str, "%H:%M:%S")
                    now = datetime.now()
                    timestamp = timestamp.replace(year=now.year, month=now.month, day=now.day)
                    if timestamp > now + timedelta(minutes=5):
                        timestamp -= timedelta(days=1)
                except: timestamp = None

            lower_line = original_line.lower()
            
            # Armor Prevented logic
            if "armor prevented" in lower_line:
                prev_match = prevented_pattern.search(original_line)
                if prev_match:
                    reduction = float(prev_match.group("amount"))
                    if last_taken_event and last_taken_event["type"] == "taken":
                        last_taken_event["damage"] = max(0, last_taken_event["damage"] - reduction)
                        current_offset = log_file.tell()
                        continue
                    else:
                        events.append({
                            "line_number": line_number, "damage": 0, "healing": 0, "type": "taken",
                            "source": "Unknown", "target": "You", "timestamp": timestamp, "raw": original_line,
                        })
                        current_offset = log_file.tell()
                        continue

            damage, healing, event_type = 0, 0, None
            source_name, target_name = "Unknown", "Unknown"
            is_mitigated = False
            item = ""

            # 1. Clean line (remove timestamp/channel)
            clean_line = re.sub(r"^(?:\[\w+\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?", "", original_line).strip()
            
            # 2. Check for SWG combat keywords
            if any(kw in lower_line for kw in swg_keywords):
                # Check for mitigation
                mit_match = mitigation_suffix.search(clean_line)
                line_to_parse = clean_line
                if mit_match:
                    is_mitigated = True
                    line_to_parse = clean_line[:mit_match.start()].strip().rstrip(",")
                
                # Parse core action
                swg_match = swg_pattern.search(line_to_parse)
                if swg_match:
                    source_name = swg_match.group("source").strip()
                    action = swg_match.group("action").lower()
                    ability = swg_match.group("ability").strip() if swg_match.group("ability") else ""
                    target_name = swg_match.group("target").strip().rstrip("!")
                    amount = float(swg_match.group("amount"))
                    
                    # Strip 'corpse of '
                    if source_name.lower().startswith("corpse of "): source_name = source_name[10:]
                    if target_name.lower().startswith("corpse of "): target_name = target_name[10:]
                    
                    # Filter system names
                    sys_names = ["target", "your target"]
                    if any(sn == source_name.lower() or source_name.lower().startswith("your target") for sn in sys_names): source_name = "Unknown"
                    if any(sn == target_name.lower() or target_name.lower().startswith("your target") for sn in sys_names): target_name = "Unknown"
                    
                    if source_name != "Unknown" and target_name != "Unknown":
                        source_name = "You" if source_name.lower() == "you" else source_name
                        target_name = "You" if target_name.lower() == "you" else target_name
                        
                        if "heal" in action:
                            healing = amount
                            event_type = "healing"
                        else:
                            damage = amount
                            if is_mitigated: damage = 0
                            if source_name == "You": event_type = "dealt"
                            elif target_name == "You": event_type = "taken"
                            else: event_type = "other_dealt"
            
            # 3. If not parsed, try mitigation-only line
            if not event_type and any(kw in lower_line for kw in mitigation_keywords):
                is_mitigated = True
                content = clean_line
                miss_match = re.search(r"(?P<source>.+?)(?:'s\s+(?P<ability>.+?))?\s+(?P<action>misses|evades|evaded|dodges|parries|counterattacks|blocks it)\b(?:\s+(?P<target>.+))?", content, re.IGNORECASE)
                if miss_match:
                    source_name = miss_match.group("source").strip()
                    ability = miss_match.group("ability").strip() if miss_match.group("ability") else ""
                    target_name = miss_match.group("target").strip().rstrip(".!") if miss_match.group("target") else "Unknown"
                    
                    if source_name.lower().startswith("corpse of "): source_name = source_name[10:]
                    if target_name.lower().startswith("corpse of "): target_name = target_name[10:]
                    
                    source_name = "You" if source_name.lower() == "you" else source_name
                    target_name = "You" if target_name.lower() == "you" else target_name
                    
                    event_type = "dealt" if source_name == "You" else "taken" if target_name == "You" else "dealt"

            # 4. Activity Patterns (Loot, death, etc)
            if not event_type:
                for pattern, keywords in activity_patterns:
                    if any(kw in lower_line for kw in keywords):
                        act_match = pattern.search(original_line)
                        if act_match:
                            gd = act_match.groupdict()
                            name = gd.get("name") or gd.get("winner") or gd.get("loser")
                            item = gd.get("item", "")
                            target = gd.get("target", "Unknown")
                            if name:
                                event_type = "activity"
                                source_name = "You" if name.lower() == "you" else name
                                if item:
                                    event_type = "loot"
                                    target_name = target
                                if "command" in gd:
                                    event_type = "command"
                                    item = gd["command"]
                                break

            if event_type:
                event = {
                    "line_number": line_number, "damage": damage, "healing": healing,
                    "type": event_type, "source": source_name, "target": target_name,
                    "timestamp": timestamp, "raw": original_line, "is_mitigated": is_mitigated,
                    "item": item, "ability": ability if 'ability' in locals() else ""
                }
                events.append(event)
                if event_type == "taken" and damage > 0: last_taken_event = event
            
            current_offset = log_file.tell()

    return events, current_offset

def calculate_dps(events):
    """Calculate statistics from a list of events."""
    if not events: return 0, 0, 0, 0, 0, 0, 0, 0
    damage_dealt = sum(e["damage"] for e in events if e["type"] == "dealt")
    damage_taken = sum(e["damage"] for e in events if e["type"] == "taken")
    timestamps = [e["timestamp"] for e in events if e["timestamp"] and (e["damage"] > 0 or e["type"] == "dealt")]
    duration = 0
    if timestamps:
        duration = (max(timestamps) - min(timestamps)).total_seconds()
    dps = damage_dealt / max(1, duration) if duration > 0 else 0
    miss_count = sum(1 for e in events if e["type"] == "dealt" and e.get("is_mitigated"))
    hit_count = sum(1 for e in events if e["type"] == "dealt" and e["damage"] > 0)
    avoided_count = sum(1 for e in events if e["type"] == "taken" and e.get("is_mitigated"))
    taken_count = sum(1 for e in events if e["type"] == "taken" and e["damage"] > 0)
    return damage_dealt, damage_taken, dps, duration, miss_count, hit_count, avoided_count, taken_count
