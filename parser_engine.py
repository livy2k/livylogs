import re
import json
import time
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
    swg_pattern = re.compile(
        r"(?:\[\w+\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?(?P<name>you|.+?)\s+(?P<action>uses|use|attacks|attack|deals|deal|heals|heal|hits|hit)\b\s+(?:(?P<ability>.+?)\s+(?:on|to|for)\s+)?(?P<target>.+?)\s+for\s+(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>damage|dmg|points|health)?",
        re.IGNORECASE
    )
    
    swg_keywords = ["uses", "use", "attacks", "attack", "deals", "deal", "heals", "heal", "hits", "hit"]
    pvp_kws = ["has bested"]
    msg_kws = ["says", "shouts", "whispers", "tells", "emotes", "performs", "is", "has", "does", "goes", "starts", "stops", "completes"]
    act_kws = ["is", "has", "does", "goes", "starts", "stops", "completes", "stands", "kneels", "performs", "sits", "says", "shouts", "whispers", "tells", "emotes", "tosses", "nods", "waves", "smiles", "laughs", "cheers", "misses", "evade", "dodge", "parr", "block", "counterattack", "attack", "use", "hit"]
    death_kws = ["has died"]
    loot_kws = ["looted", "you cannot loot that item"]

    prevented_pattern = re.compile(r"armor prevented (?P<amount>\d+(?:\.\d+)?)\s*(?:damage|dmg|points)", re.IGNORECASE)

    activity_patterns = [
        (re.compile(r'(?:\[PvPBroadcasts\]\s+)?(?:\d{2}:\d{2}:\d{2}\s+)?\[PvPBroadcasts\]\s+:\s+(?P<winner>.+?)\s+has bested\s+(?P<loser>.+?)\s+in GCW combat\.', re.IGNORECASE), pvp_kws),
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
                            "source": "Unknown", "target": "you", "timestamp": timestamp, "raw": original_line,
                        })
                        current_offset = log_file.tell()
                        continue

            is_mitigated = False
            mitigation_keywords = ["counterattacks", "blocks it", "misses", "evades", "evaded", "dodges", "parries"]
            if any(kw in lower_line for kw in mitigation_keywords):
                is_mitigated = True
                source_candidate = "Unknown"
                target_candidate = "Unknown"
                content = re.sub(r"^(\[\w+\]\s+)?(\d{2}:\d{2}:\d{2}\s+)?", "", original_line)
                miss_match = re.search(r"(?P<source>.+?)(?:'s\s+(?P<ability>.+?))?\s+(?P<action>misses|evades|evaded|dodges|parries|counterattacks|blocks it)\b(?:\s+(?P<target>.+))?", content, re.IGNORECASE)
                if miss_match:
                    source_candidate = miss_match.group("source").strip()
                    target_candidate = miss_match.group("target").strip() if miss_match.group("target") else "Unknown"
                else:
                    swg_miss_match = re.search(r"(?P<source>you|.+?)\s+(?P<action>uses|use|attacks|attack|deals|deal|heals|heal|hits|hit)\b\s+(?:(?P<ability>.+?)\s+(?:on|to|for)\s+)?(?P<target>.+?)\s+for\s+(?P<amount>\d+(?:\.\d+)?)\s*.+?,\s*but\s+(?:he|she|it|you)\s+(?P<mitigation>evades|evaded|dodges|parries|blocks it|counterattacks)", content, re.IGNORECASE)
                    if swg_miss_match:
                        source_candidate = swg_miss_match.group("source").strip()
                        target_candidate = swg_miss_match.group("target").strip()
                
                if source_candidate.lower().startswith("corpse of "): source_candidate = source_candidate[len("corpse of "):]
                if target_candidate.lower().startswith("corpse of "): target_candidate = target_candidate[len("corpse of "):]
                
                if source_candidate:
                    source_name = "You" if source_candidate.lower() == "you" else source_candidate
                    target_name = "You" if target_candidate.lower() == "you" else target_candidate
                    etype = "dealt" if source_name == "You" else "taken" if target_name == "You" else "dealt"
                    event = {
                        "line_number": line_number, "damage": 0, "healing": 0, "type": etype,
                        "source": source_name, "target": target_name, "timestamp": timestamp, "raw": original_line, "is_mitigated": True
                    }
                    events.append(event)
                    if etype == "taken": last_taken_event = event
                    current_offset = log_file.tell()
                    continue

            swg_match = None
            if any(kw in lower_line for kw in swg_keywords):
                swg_match = swg_pattern.search(original_line)
            
            damage, healing, event_type = 0, 0, None
            source_name, target_name = "Unknown", "Unknown"
            
            if swg_match:
                source_name = swg_match.group("name").strip()
                action = swg_match.group("action").lower()
                amount = float(swg_match.group("amount"))
                target_name = swg_match.group("target").strip()
                if source_name.lower().startswith("corpse of "): source_name = source_name[len("corpse of "):]
                if target_name.lower().startswith("corpse of "): target_name = target_name[len("corpse of "):]
                if not source_name: source_name = "Unknown"
                if not target_name: target_name = "Unknown"

                if "heal" in action:
                    healing = amount
                    event_type = "healing"
                else:
                    damage = amount
                    if source_name.lower() == "you": event_type = "dealt"
                    elif target_name.lower() == "you": event_type = "taken"
                    else: event_type = "other_dealt"
                
                if "evades" in lower_line or "counterattacks" in lower_line:
                    damage, is_mitigated = 0, True
            
            if not event_type:
                if any(kw in lower_line for kw in mitigation_keywords):
                    is_mitigated = True
                    parts = original_line.split(" ")
                    clean_parts = [p for p in parts if ":" not in p and "[" not in p and "]" not in p]
                    if len(clean_parts) >= 3:
                        source_candidate = clean_parts[0]
                        target_candidate = clean_parts[-1].rstrip(".!")
                        if source_candidate.lower() == "you":
                            source_name, target_name, event_type = "you", target_candidate, "dealt"
                        elif target_candidate.lower() == "you":
                            source_name, target_name, event_type = source_candidate, "you", "taken"
                        elif source_candidate:
                            source_name, event_type = source_candidate, "other_dealt"
                        if event_type: damage = 0

            if not event_type:
                for pattern, keywords in activity_patterns:
                    if any(kw in lower_line for kw in keywords):
                        act_match = pattern.search(original_line)
                        if act_match:
                            gd = act_match.groupdict()
                            name = gd.get("name") or gd.get("winner") or gd.get("loser")
                            item = gd.get("item")
                            target = gd.get("target")
                            if name:
                                event_type = "activity"
                                source_name = "You" if name.lower() == "you" else name
                                if item:
                                    event_type = "loot"
                                    target_name = target if target else "Unknown"
                                break
            
            if event_type:
                event = {
                    "line_number": line_number, "damage": damage, "healing": healing,
                    "type": event_type, "source": source_name, "target": target_name,
                    "timestamp": timestamp, "raw": original_line, "is_mitigated": is_mitigated,
                    "item": item if event_type == "loot" else ""
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
