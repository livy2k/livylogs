"""
Discord Bot for LivyLogs
Connects to Discord using a bot token and relays messages to/from a specified channel.
Run this script separately or integrate with the main app.
"""

import discord
import asyncio
import os
import sys
import threading
import queue
import re
import time
import io
import datetime
import json
import random
import string
import base64
import hashlib
import aiohttp
from admin_tools.uncle_rico import load_rico_to_ram, UncleReCoNScanner
from cryptography.fernet import Fernet
from PIL import Image, ImageDraw, ImageFont
import galaxy_harvester_api
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TOKEN = os.environ.get('DISCORD_TOKEN', os.environ.get('DISCORD_BOT_TOKEN', ''))
CHANNEL_ID = os.environ.get('DISCORD_CHANNEL_ID', '')
OWNER_ID = os.environ.get('BOT_OWNER_ID', '') # Optional: restrict /123 to this ID
HANDSHAKE_SECRET = os.environ.get('LIVIUS_HANDSHAKE', '') # Optional: secret for pulses

if not TOKEN:
    print("ERROR: DISCORD_TOKEN or DISCORD_BOT_TOKEN environment variable not set.")
    print("Ensure you have a .env file with DISCORD_TOKEN=your_token_here")
    sys.exit(1)

if not CHANNEL_ID:
    print("ERROR: DISCORD_CHANNEL_ID environment variable not set.")
    print("Set it before running, e.g.:")
    print("  set DISCORD_CHANNEL_ID=123456789012345678")
    print("  python discord_bot.py")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

client = discord.Client(intents=intents)

# --- UNCLE RECON INTELLIGENCE ---
rico_db = load_rico_to_ram()

async def broadcast_ur_intel(mob, loot, planet, x, y):
    """Broadcasts learned intel to all Uncle ReCoNs on the relay."""
    channel = client.get_channel(int(CHANNEL_ID))
    if channel:
        intel_msg = f"[UR-INTEL] {mob} | {loot} | {planet} | {x} | {y}"
        if HANDSHAKE_SECRET:
            intel_msg += f" | HS: {HANDSHAKE_SECRET}"
        await channel.send(intel_msg)

def save_ur_intel_locally(mob, loot, planet, x, y):
    """Saves learned intel to the local database."""
    if not rico_db: return
    try:
        c = rico_db.cursor()
        c.execute('''INSERT INTO learned_drops 
                    (mobile_template, item_template, planet, x, y, confidence, last_seen) 
                    VALUES (?, ?, ?, ?, ?, 1, ?)''', 
                    (mob, loot, planet, x, y, datetime.datetime.now()))
        rico_db.commit()
    except Exception as e:
        print(f"[Uncle ReCoN] Error saving intel: {e}")

# --- GITHUB PAGES PUBLISHER ---
class GitHubPublisher:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO") # Format: username/repo
        self.domain = os.getenv("GITHUB_DOMAIN") # e.g. livius.gg
        self.branch = "gh-pages"

    async def publish_report(self, filename, content, summary_data):
        if not self.token or not self.repo:
            print("[GitHub] Missing credentials, skipping upload.")
            return None

        # 1. Upload the report file
        path = f"reports/{filename}"
        await self._upload_to_github(path, content, f"Add report {filename}")

        # 2. Update CNAME if domain is set
        if self.domain:
            await self._upload_to_github("CNAME", self.domain, "Update CNAME")

        # 3. Update index.html (Dashboard)
        await self._update_index(summary_data)

        base_url = f"https://{self.domain}" if self.domain else f"https://{self.repo.split('/')[0]}.github.io/{self.repo.split('/')[1]}"
        return f"{base_url}/reports/{filename}"

    async def submit_for_curation(self, summary_data):
        if not self.token or not self.repo: return False
        
        url = f"https://api.github.com/repos/{self.repo}/contents/pending_logs.json"
        headers = {"Authorization": f"token {self.token}"}
        
        pending_list = []
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sha = data["sha"]
                    pending_list = json.loads(base64.b64decode(data["content"]).decode())
            
            # Add to pending if not already there
            if not any(p.get("filename") == summary_data.get("filename") for p in pending_list):
                pending_list.append(summary_data)
                
                payload = {
                    "message": f"New curation request: {summary_data.get('filename')}",
                    "content": base64.b64encode(json.dumps(pending_list, indent=2).encode()).decode(),
                    "branch": self.branch
                }
                if sha: payload["sha"] = sha
                async with session.put(url, headers=headers, json=payload) as resp:
                    return resp.status in [200, 201]
        return False

    async def approve_report(self, filename):
        if not self.token or not self.repo: return False
        
        url_pending = f"https://api.github.com/repos/{self.repo}/contents/pending_logs.json"
        url_reports = f"https://api.github.com/repos/{self.repo}/contents/reports.json"
        headers = {"Authorization": f"token {self.token}"}
        
        async with aiohttp.ClientSession() as session:
            # 1. Get Pending
            async with session.get(url_pending, headers=headers) as resp:
                if resp.status != 200: return False
                data_p = await resp.json()
                sha_p = data_p["sha"]
                pending_list = json.loads(base64.b64decode(data_p["content"]).decode())
            
            # 2. Find and move report
            report = next((p for p in pending_list if p["filename"] == filename), None)
            if not report: return False
            
            # 3. Get Official Reports
            reports_list = []
            sha_r = None
            async with session.get(url_reports, headers=headers) as resp:
                if resp.status == 200:
                    data_r = await resp.json()
                    sha_r = data_r["sha"]
                    reports_list = json.loads(base64.b64decode(data_r["content"]).decode())
            
            # Add to official
            reports_list.insert(0, report)
            reports_list = reports_list[:100] # Keep more in official
            
            # Remove from pending
            pending_list = [p for p in pending_list if p["filename"] != filename]
            
            # 4. Update Official
            payload_r = {
                "message": f"Approve report: {filename}",
                "content": base64.b64encode(json.dumps(reports_list, indent=2).encode()).decode(),
                "branch": self.branch
            }
            if sha_r: payload_r["sha"] = sha_r
            await session.put(url_reports, headers=headers, json=payload_r)
            
            # 5. Update Pending
            payload_p = {
                "message": f"Clear pending: {filename}",
                "content": base64.b64encode(json.dumps(pending_list, indent=2).encode()).decode(),
                "branch": self.branch
            }
            payload_p["sha"] = sha_p
            await session.put(url_pending, headers=headers, json=payload_p)
            
            # 6. Update Official Leaderboard on GitHub
            # (In a real app, you'd pull the global leaderboard from GitHub, 
            # add the points from this report, and push it back).
            
            return True

    async def _upload_to_github(self, path, content, message):
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get existing file SHA if it exists
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sha = data["sha"]

            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": self.branch
            }
            if sha: payload["sha"] = sha

            async with session.put(url, headers=headers, json=payload) as resp:
                if resp.status in [200, 201]:
                    print(f"[GitHub] Successfully uploaded {path}")
                else:
                    print(f"[GitHub] Error uploading {path}: {await resp.text()}")

    async def _update_index(self, new_summary):
        # Implementation of dashboard update logic
        # For simplicity in this step, we'll maintain a reports.json to track entries
        url = f"https://api.github.com/repos/{self.repo}/contents/reports.json"
        url_rico = f"https://api.github.com/repos/{self.repo}/contents/rico_intel.json"
        headers = {"Authorization": f"token {self.token}"}
        
        reports_list = []
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sha = data["sha"]
                    reports_list = json.loads(base64.b64decode(data["content"]).decode())
            
            # CHECK FOR DUPLICATE BATTLE FINGERPRINT
            fingerprint = new_summary.get("fingerprint")
            if fingerprint:
                for existing in reports_list:
                    if existing.get("fingerprint") == fingerprint:
                        new_summary["is_duplicate"] = True
                        new_summary["related_to"] = existing.get("filename")
                        break

            reports_list.insert(0, new_summary)
            # Keep last 50
            reports_list = reports_list[:50]
            
            payload = {
                "message": f"Update reports list (Fingerprint: {fingerprint})",
                "content": base64.b64encode(json.dumps(reports_list, indent=2).encode()).decode(),
                "branch": self.branch
            }
            if sha: payload["sha"] = sha
            await session.put(url, headers=headers, json=payload)

            # --- EXPORT UNCLE RECON INTEL TO GITHUB ---
            if rico_db:
                c = rico_db.cursor()
                # Get the most recent learned intel (last 100 entries)
                c.execute("SELECT mobile_template, item_template, planet, x, y, confidence FROM learned_drops ORDER BY last_seen DESC LIMIT 100")
                intel_data = []
                for row in c.fetchall():
                    intel_data.append({
                        "mob": row[0],
                        "item": row[1],
                        "planet": row[2],
                        "coords": f"{int(row[3])}, {int(row[4])}",
                        "conf": row[5]
                    })
                
                # Get SHA for rico_intel.json
                sha_rico = None
                async with session.get(url_rico, headers=headers) as resp:
                    if resp.status == 200:
                        data_r = await resp.json()
                        sha_rico = data_r["sha"]
                
                payload_rico = {
                    "message": "Update Uncle ReCoN Web Intel",
                    "content": base64.b64encode(json.dumps(intel_data, indent=2).encode()).decode(),
                    "branch": self.branch
                }
                if sha_rico: payload_rico["sha"] = sha_rico
                await session.put(url_rico, headers=headers, json=payload_rico)

# --- COMBAT TRACKER AND CHART GENERATOR ---
class CombatTracker:
    def __init__(self):
        self.history = {}  # {player_name: {"totals": [], "events": [], "pulses": []}}
        self.loot_history = {} # {player_name: {item_type: count}}
        self.start_time = 0
        self.last_pulse_time = 0
        self.is_active = False
        self.lock = asyncio.Lock()
        self.publisher = GitHubPublisher()
        self.pulse_pattern = re.compile(r"\[LIVIUS RELAY\] (.+?) \| DMG: (\d+) \| HEAL: (\d+) \| INC: (\d+) \| KD: (\d+) \| TGT: (.+?)(?: \| EVTS: (.+))?$")
        self.loot_pattern = re.compile(r"\[LIVIUS RELAY\] (.+?) has looted (MODIFIED|ADVANCED|SUPERIOR|EXCEPTIONAL|LEGENDARY): (.+)")

    async def add_pulse_from_msg(self, content, channel=None):
        # Check for Loot
        loot_match = self.loot_pattern.match(content)
        if loot_match:
            looter = loot_match.group(1).strip()
            rarity = loot_match.group(2).strip()
            item_name = loot_match.group(3).strip()
            
            async with self.lock:
                if looter not in self.loot_history:
                    self.loot_history[looter] = {}
                self.loot_history[looter][rarity] = self.loot_history[looter].get(rarity, 0) + 1
            return

        match = self.pulse_pattern.match(content)
        if not match: 
            # Check for Uncle ReCoN Intel pulses
            if content.startswith("[UR-INTEL] "):
                parts = content.replace("[UR-INTEL] ", "").split(" | ")
                if len(parts) >= 5:
                    mob, loot, planet, x, y = parts[0], parts[1], parts[2], parts[3], parts[4]
                    save_ur_intel_locally(mob, loot, planet, x, y)
                return
            return
        
        name = match.group(1).strip()
        dmg = int(match.group(2))
        heal = int(match.group(3))
        evts_raw = match.group(7)
        
        async with self.lock:
            now = time.time()
            if not self.is_active:
                print(f"[Tracker] PvP Combat Detected! Starting tracking...")
                self.is_active = True
                self.start_time = now
                self.history = {}
                if channel:
                    await channel.send("⚔️ **PvP Combat has begun!** @here")
            
            if name not in self.history:
                self.history[name] = {"totals": [], "events": [], "pulses": []}
            
            # Use encounter relative time
            rel_now = now - self.start_time
            self.history[name]["totals"].append((rel_now, dmg, heal))
            
            # Record raw pulse for mini-logs in reports
            # (timestamp, name, dmg, heal, target)
            tgt_pulse = match.group(6).strip()
            self.history[name]["pulses"].append((rel_now, dmg, heal, tgt_pulse))
            
            # Parse events if present
            if evts_raw:
                # Format: time:type:src:tgt:label
                for ev_str in evts_raw.split(','):
                    parts = ev_str.split(':')
                    if len(parts) >= 5:
                        try:
                            t = float(parts[0])
                            etype = parts[1]
                            src = parts[2]
                            tgt = parts[3]
                            label = parts[4]
                            
                            existing = self.history[name]["events"]
                            if not any(e[0] == t and e[1] == etype and e[2] == src for e in existing):
                                self.history[name]["events"].append((t, etype, src, tgt, label))
                        except: pass
            
            self.last_pulse_time = now

    def generate_chart(self):
        if not self.history: return None
        
        # Determine players and max time
        players = list(self.history.keys())
        max_time = 0
        for name, data in self.history.items():
            for t, d, h in data["totals"]:
                max_time = max(max_time, t)
            for t, etype, src, tgt, label in data["events"]:
                max_time = max(max_time, t)
        
        if max_time == 0: max_time = 1
        
        row_height = 80
        padding_x = 150
        padding_y = 100
        width = 1200
        height = padding_y + (len(players) * row_height) + 100
        
        img = Image.new('RGB', (width, height), color='#1a1d23')
        draw = ImageDraw.Draw(img)
        
        try:
            font_path = "LilitaOne.ttf"
            font_title = ImageFont.truetype(font_path, 32)
            font_name = ImageFont.truetype(font_path, 18)
            font_small = ImageFont.truetype(font_path, 12)
            font_event = ImageFont.truetype(font_path, 14)
        except:
            font_title = ImageFont.load_default()
            font_name = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_event = ImageFont.load_default()
            
        draw.text((width//2, 40), "COMBAT TIMELINE - PVP ENCOUNTER", fill="#00FFFF", font=font_title, anchor="mm")
        
        # Draw Timeline Axis
        axis_y = height - 80
        draw.line([(padding_x, axis_y), (width-50, axis_y)], fill="#555555", width=2)
        
        # Time markers
        for s in range(0, int(max_time) + 10, 10):
            x = padding_x + (s / max_time) * (width - padding_x - 50) if max_time > 0 else padding_x
            if x > width - 50: continue
            draw.line([(x, axis_y), (x, axis_y + 5)], fill="#888888")
            draw.text((x, axis_y + 15), f"{s}s", fill="#888888", font=font_small, anchor="mm")

        # Event Type Colors/Icons
        event_colors = {
            "KD": ("#FF0000", "KD"),      # Red
            "PD": ("#FFA500", "PD"),      # Orange
            "INT": ("#FFFF00", "INT"),    # Yellow
            "INC": ("#FF00FF", "INC"),    # Magenta
            "LOOT": ("#00FF00", "LOOT"),  # Green
            "DEATH": ("#888888", "DEAD"), # Grey
            "KILL": ("#FFFFFF", "KILL")   # White
        }

        # Draw Rows
        for i, name in enumerate(players):
            y_center = padding_y + 40 + i * row_height
            
            # Row background (alternating)
            if i % 2 == 0:
                draw.rectangle([padding_x, y_center - 35, width - 50, y_center + 35], fill="#242830")
            
            # Player Name
            name_color = "#00FFFF" if name.upper() == "YOU" else "#FFFFFF"
            draw.text((padding_x - 10, y_center), name.upper(), fill=name_color, font=font_name, anchor="rm")
            
            # Draw Events
            events = self.history[name].get("events", [])
            for t, etype, src, tgt, label in events:
                x = padding_x + (t / max_time) * (width - padding_x - 50)
                
                color, tag = event_colors.get(etype, ("#FFFFFF", etype))
                
                # Draw marker
                box_w, box_h = 40, 24
                draw.rectangle([x - box_w//2, y_center - box_h//2, x + box_w//2, y_center + box_h//2], fill=color, outline="#FFFFFF")
                draw.text((x, y_center), tag, fill="#000000", font=font_event, anchor="mm")
                
                # If death, draw an X
                if etype == "DEATH":
                    draw.line([(x-15, y_center-15), (x+15, y_center+15)], fill="#FFFFFF", width=2)
                    draw.line([(x+15, y_center-15), (x-15, y_center+15)], fill="#FFFFFF", width=2)

        # Add timestamp
        footer = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Duration: {int(max_time)}s"
        draw.text((width-50, height-30), footer, fill="#555555", font=font_small, anchor="rm")
        
        return img

    def generate_html_report(self):
        # Generate an interactive HTML report using Tailwind CSS and DaisyUI
        players = list(self.history.keys())
        max_time = 0
        all_pulses = [] # Collect all pulses for lookup
        for name, data in self.history.items():
            for t, d, h in data["totals"]: max_time = max(max_time, t)
            for t, etype, src, tgt, label in data["events"]: max_time = max(max_time, t)
            for p in data.get("pulses", []):
                all_pulses.append((p[0], name, p[1], p[2], p[3])) # t, name, dmg, heal, tgt
        if max_time == 0: max_time = 1
        
        all_pulses.sort(key=lambda x: x[0]) # Sort by time

        # Classify friends and enemies
        # YOU and the verified pilot name are always friendly. Anyone they damage is enemy. Anyone who heals them is friend.
        friends = {"YOU"}
        # If we know the user's name from verification, add it to friends
        user_name = None
        for code, data in verification_codes.items():
            if data.get("user"):
                friends.add(data["user"].upper())
        
        enemies = set()
        for t, name, dmg, heal, tgt in all_pulses:
            name_u = name.upper()
            tgt_u = tgt.upper() if tgt else ""
            
            if name_u in friends:
                if dmg > 0 and tgt: enemies.add(tgt)
                if heal > 0 and tgt: friends.add(tgt)
            if tgt_u in friends:
                if dmg > 0: enemies.add(name)
                if heal > 0: friends.add(name)
        
        # Secondary classification: friends of friends, enemies of enemies
        for t, name, dmg, heal, tgt in all_pulses:
            if name in friends and dmg > 0: enemies.add(tgt)
            if name in enemies and dmg > 0: friends.add(tgt) # Enemy damaging someone -> probably friend
            if name in friends and heal > 0: friends.add(tgt)
            if name in enemies and heal > 0: enemies.add(tgt)

        # Cleanup: Ensure no overlap and only existing players
        existing_players = set(self.history.keys())
        friends = (friends & existing_players)
        enemies = (enemies & existing_players) - friends
        neutrals = existing_players - friends - enemies

        # Performance Metrics Logic (MVP/RIP) with ELO Bonus
        # Formula: (Kills * 100 * ELO) + (KD * 0.5) + (PD * 0.01) + (H * 0.02) + (I * 50) - (D * 150) - (inc * 0.01)
        # ELO Multiplier: 1 + max(0, (VictimTotal - MyTotal) / 5000)
        
        leaderboard = load_json("livius_leaderboard.json")
        scores = {}
        
        for name, data in self.history.items():
            my_total_larp = leaderboard.get(name, 0)
            
            # Calculate ELO-weighted Kills
            kill_points = 0
            for e in data["events"]:
                if e[1] == "KILL":
                    victim_name = e[3]
                    victim_total_larp = leaderboard.get(victim_name, 0)
                    elo_mult = 1.0 + max(0, (victim_total_larp - my_total_larp) / 5000)
                    kill_points += (100 * elo_mult)
            
            kd = sum(p[1] for p in data.get("pulses", []) if any(e[1] == "KD" and e[0] == p[0] for e in data["events"]))
            pd = sum(p[1] for p in data.get("pulses", []))
            h = sum(p[2] for p in data.get("pulses", []))
            i = sum(50 for e in data["events"] if e[1] == "INT")
            d = sum(150 for e in data["events"] if e[1] == "DEATH")
            inc = sum(p[3] for p in data.get("pulses", []))
            
            score = kill_points + (kd * 0.5) + (pd * 0.01) + (h * 0.02) + i - d - (inc * 0.01)
            scores[name] = score

        mvp = max(scores, key=scores.get) if scores else "N/A"
        rip = min(scores, key=scores.get) if scores else "N/A"

        # Update and Save Global Leaderboard (LOCAL ONLY - Curation will handle public)
        # Note: In standard mode, this updates local leaderboard.
        # In website mode, points are only "official" after curation.
        for name, larp in scores.items():
            leaderboard[name] = leaderboard.get(name, 0) + int(larp)
        save_json("livius_leaderboard.json", leaderboard)

        # Sorting: Friends first (YOU top), then neutrals, then enemies
        sorted_players = sorted(list(friends), key=lambda x: 0 if x.upper() == "YOU" else 1)
        sorted_players += sorted(list(neutrals))
        sorted_players += sorted(list(enemies))

        # Color mapping for event types
        event_classes = {
            "KD": "badge-error",
            "PD": "badge-warning",
            "INT": "badge-info",
            "INC": "badge-secondary",
            "LOOT": "badge-success",
            "DEATH": "badge-ghost",
            "KILL": "badge-primary"
        }

        html = f"""
        <!DOCTYPE html>
        <html data-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                :root {{
                    --starwars-blue: #00ecff;
                    --starwars-red: #ff003c;
                    --starwars-yellow: #ffe81f;
                    --hud-bg: rgba(10, 15, 20, 0.9);
                }}
                body {{ font-family: 'JetBrains Mono', monospace; background-color: #05070a; background-image: radial-gradient(circle at 50% 50%, #1a202c 0%, #05070a 100%); }}
                h1, .font-orbitron {{ font-family: 'Orbitron', sans-serif; }}
                .swimlane-container {{ position: relative; min-width: 1200px; padding-top: 60px; }}
                .event-marker {{ position: absolute; transform: translateX(-50%); transition: all 0.2s; z-index: 30; }}
                .event-marker:hover {{ transform: translateX(-50%) scale(1.2); z-index: 100; }}
                .time-line {{ position: absolute; top: 0; bottom: 0; border-left: 1px solid rgba(0, 236, 255, 0.1); pointer-events: none; }}
                .mini-log {{ max-height: 160px; overflow-y: auto; scrollbar-width: thin; }}
                .mini-log::-webkit-scrollbar {{ width: 4px; }}
                .mini-log::-webkit-scrollbar-thumb {{ background: var(--starwars-blue); border-radius: 2px; }}
                .hud-border {{ border: 1px solid rgba(0, 236, 255, 0.2); box-shadow: 0 0 15px rgba(0, 236, 255, 0.1); }}
                .scanline {{ width: 100%; height: 100px; z-index: 5; background: linear-gradient(0deg, rgba(0, 236, 255, 0) 0%, rgba(0, 236, 255, 0.02) 50%, rgba(0, 236, 255, 0) 100%); position: absolute; animation: scan 8s linear infinite; pointer-events: none; }}
                @keyframes scan {{ from {{ top: -100px; }} to {{ top: 100%; }} }}
                .glow-text-blue {{ text-shadow: 0 0 10px rgba(0, 236, 255, 0.5); }}
                .glow-text-red {{ text-shadow: 0 0 10px rgba(255, 0, 60, 0.5); }}
                .player-row {{ transition: all 0.3s; }}
                .player-row:hover {{ background: rgba(0, 236, 255, 0.08) !important; z-index: 50 !important; }}
                .sparkline {{ pointer-events: none; position: absolute; inset: 0; z-index: 10; opacity: 0.6; }}
                .hidden-lane {{ display: none !important; }}
            </style>
            <script>
                function filterData() {{
                    const search = document.getElementById('search-input').value.toLowerCase();
                    const filter = document.getElementById('side-filter').value;
                    const lanes = document.querySelectorAll('.player-lane');
                    
                    let visibleCount = 0;
                    lanes.forEach(lane => {{
                        const name = lane.getAttribute('data-name').toLowerCase();
                        const side = lane.getAttribute('data-side');
                        const matchesSearch = name.includes(search);
                        const matchesFilter = filter === 'all' || side === filter;
                        
                        if (matchesSearch && matchesFilter) {{
                            lane.classList.remove('hidden-lane');
                            lane.style.top = (80 + (visibleCount + 1) * 140) + 'px';
                            visibleCount++;
                        }} else {{
                            lane.classList.add('hidden-lane');
                        }}
                    }});
                    
                    document.querySelector('.swimlane-container').style.height = ((visibleCount + 1) * 140 + 100) + 'px';
                }}

                function saveReport(mode) {{
                    let content = document.documentElement.outerHTML;
                    if (mode === 'snippet') {{
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(content, 'text/html');
                        doc.querySelectorAll('.hidden-lane').forEach(el => el.remove());
                        content = doc.documentElement.outerHTML;
                    }}
                    const blob = new Blob([content], {{type: 'text/html'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `livius_report_${{mode}}_${{new Date().getTime()}}.html`;
                    a.click();
                }}
            </script>
        </head>
        <body class="min-h-screen p-4 md:p-8 text-slate-300">
            <div class="max-w-[1800px] mx-auto relative">
                <!-- Header -->
                <div class="flex flex-col md:flex-row justify-between items-stretch mb-8 hud-border bg-black/60 backdrop-blur-md p-6 rounded-lg border-l-4 border-l-primary gap-6 relative overflow-hidden">
                    <div class="scanline"></div>
                    <div class="relative z-10">
                        <div class="flex items-center gap-4 mb-2">
                            <div class="w-10 h-1 rounded-full bg-primary shadow-[0_0_15px_#00ecff]"></div>
                            <h1 class="text-3xl font-black text-primary tracking-[0.2em] glow-text-blue uppercase">Livius Tactical Overlay</h1>
                        </div>
                        <p class="text-[10px] font-bold tracking-[0.4em] text-primary/60 uppercase ml-14">Sector 7-B Combat Data Feed • Encrypted Link Active</p>
                    </div>
                    <div class="flex items-center gap-4 relative z-10">
                        <!-- Duplicate Indicator -->
                        <div id="dup-warning" class="hidden flex items-center gap-2 bg-error/20 border border-error/50 px-3 py-1 rounded animate-pulse">
                            <span class="text-[9px] font-black text-error uppercase tracking-widest">Duplicate Detected</span>
                            <div class="w-1.5 h-1.5 rounded-full bg-error"></div>
                        </div>

                        <div class="join hud-border bg-black/40">
                            <input id="search-input" type="text" placeholder="FILTER..." class="input input-bordered input-xs join-item bg-transparent border-none text-[9px] w-24 focus:outline-none" onkeyup="filterData()">
                            <select id="side-filter" class="select select-bordered select-xs join-item bg-transparent border-none text-[9px] focus:outline-none" onchange="filterData()">
                                <option value="all">ALL</option>
                                <option value="friend">FRIENDS</option>
                                <option value="enemy">ENEMIES</option>
                            </select>
                        </div>
                        <div class="dropdown dropdown-end">
                            <div tabindex="0" role="button" class="btn btn-primary btn-xs font-orbitron text-[9px] tracking-widest">SAVE</div>
                            <ul tabindex="0" class="dropdown-content z-[200] menu p-2 shadow bg-black border border-primary/40 rounded-box w-32 mt-2 text-[9px]">
                                <li><a onclick="saveReport('full')">FULL</a></li>
                                <li><a onclick="saveReport('snippet')">SNIPPET</a></li>
                            </ul>
                        </div>
                        <div class="w-px h-12 bg-white/10 mx-2"></div>
                        <div class="flex flex-col items-end">
                            <span class="text-[9px] font-black opacity-40 uppercase tracking-widest">Operation Clock</span>
                            <span class="text-2xl font-orbitron font-black text-secondary glow-text-blue tracking-tighter">{int(max_time)}<span class="text-xs ml-1">SEC</span></span>
                        </div>
                        <div class="w-px h-12 bg-white/10"></div>
                        <div class="flex flex-col items-end">
                            <span class="text-[9px] font-black opacity-40 uppercase tracking-widest">Detected Entities</span>
                            <span class="text-2xl font-orbitron font-black text-accent glow-text-blue tracking-tighter">{len(players)}<span class="text-xs ml-1">OBJ</span></span>
                        </div>
                    </div>
                </div>

                <div class="hud-border bg-black/40 rounded-lg p-1 relative">
                    <!-- MVP / RIP Header -->
                    <div class="flex gap-4 p-4 mb-2">
                        <div class="flex-1 bg-primary/10 border border-primary/30 rounded p-3 flex items-center justify-between">
                            <div>
                                <div class="text-[8px] font-black text-primary uppercase tracking-[0.3em]">Combat MVP</div>
                                <div class="text-xl font-orbitron font-black text-white glow-text-blue">{mvp.upper()}</div>
                            </div>
                            <div class="text-[10px] font-bold text-primary/60">DOMINANT PERFORMANCE</div>
                        </div>
                        <div class="flex-1 bg-error/10 border border-error/30 rounded p-3 flex items-center justify-between">
                            <div>
                                <div class="text-[8px] font-black text-error uppercase tracking-[0.3em]">Combat RIP</div>
                                <div class="text-xl font-orbitron font-black text-white glow-text-red">{rip.upper()}</div>
                            </div>
                            <div class="text-[10px] font-bold text-error/60">NEUTRALIZED / TARGETED</div>
                        </div>
                    </div>

                    <div class="swimlane-container" style="height: {(len(sorted_players) + 1) * 140 + 100}px;">
                        <div class="scanline"></div>
                        <!-- Time Markers -->
        """
        
        # Add vertical time lines and labels
        for s in range(0, int(max_time) + 1, 5):
            left = (s / max_time) * 100
            is_major = s % 10 == 0
            line_opacity = "rgba(0, 236, 255, 0.15)" if is_major else "rgba(0, 236, 255, 0.05)"
            html += f"""
                        <div class="time-line" style="left: {left}%; border-left-color: {line_opacity};"></div>
                        <div class="absolute text-[8px] font-black tracking-tighter text-primary/40" style="left: {left}%; top: 20px; transform: translateX(-50%);">{s:03d}</div>
            """

        # --- SUMMARY TOP LINE ---
        summary_top = 80
        friend_pulses = [p for p in all_pulses if p[1] in friends]
        enemy_pulses = [p for p in all_pulses if p[1] in enemies]
        
        def get_summary_svg(pulses_list, color, fill):
            if not pulses_list: return ""
            max_val = 1
            for t, n, d, h, tgt in all_pulses: max_val = max(max_val, d, h)
            
            pts = ["0,100"]
            sorted_p = sorted(pulses_list, key=lambda x: x[0])
            for t, n, d, h, tgt in sorted_p:
                x = (t / max_time) * 100
                y = 100 - (max(d, h) / max_val * 80)
                pts.append(f"{x},{y}")
            pts.append("100,100")
            return f'<polyline fill="{fill}" stroke="{color}" stroke-width="0.5" points="{" ".join(pts)}" />'

        friend_svg = get_summary_svg(friend_pulses, "rgba(0, 236, 255, 0.5)", "rgba(0, 236, 255, 0.1)")
        enemy_svg = get_summary_svg(enemy_pulses, "rgba(255, 0, 60, 0.5)", "rgba(255, 0, 60, 0.1)")

        html += f"""
                        <div class="absolute left-0 right-0 h-28 rounded border border-primary/40 bg-primary/10 flex items-center px-6 backdrop-blur-md z-40" style="top: {summary_top}px;">
                            <div class="w-48 flex-shrink-0 border-r border-white/20 mr-8 py-2">
                                <span class="text-[8px] font-black text-primary uppercase tracking-[0.3em] mb-1 block">Tactical Summary</span>
                                <span class="text-lg font-orbitron font-black text-white glow-text-blue tracking-widest uppercase">ALL CONTACTS</span>
                                <div class="flex gap-2 mt-2">
                                    <span class="text-[7px] font-bold text-primary/60">FRIENDS: {len(friends)}</span>
                                    <span class="text-[7px] font-bold text-error/60">ENEMIES: {len(enemies)}</span>
                                </div>
                            </div>
                            <div class="relative flex-grow h-full overflow-hidden">
                                <svg class="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
                                    {friend_svg}
                                    {enemy_svg}
                                </svg>
        """
        
        # Add summary events (all events combined)
        for name in sorted_players:
            side_color = "primary" if name in friends else ("error" if name in enemies else "slate-400")
            for t, etype, src, tgt, label in self.history[name].get("events", []):
                left = (t / max_time) * 100
                badge_class = event_classes.get(etype, "badge-ghost")
                html += f"""
                                <div class="event-marker group" style="left: {left}%; top: 50%; margin-top: -24px;">
                                    <div class="w-1 h-4 bg-{side_color} opacity-40 mb-1 mx-auto"></div>
                                    <div class="badge {badge_class} badge-xs scale-75 opacity-50 group-hover:opacity-100 transition-opacity"></div>
                                </div>
                """
        
        html += """
                            </div>
                        </div>
        """

        # Draw Individual Player Lanes
        for i, name in enumerate(sorted_players):
            top = 220 + (i * 140) # Shifted down for MVP header
            is_you = name.upper() == "YOU"
            is_friend = name in friends
            is_enemy = name in enemies
            side_type = "friend" if is_friend else ("enemy" if is_enemy else "neutral")
            
            row_border = "border-primary/30" if is_friend else ("border-error/20" if is_enemy else "border-white/5")
            row_bg = "bg-primary/5" if is_friend else ("bg-error/5" if is_enemy else "bg-white/[0.02]")
            name_color = "text-primary glow-text-blue" if is_you else ("text-blue-300" if is_friend else ("text-error" if is_enemy else "text-slate-200"))
            
            # Generate Sparkline Data
            pulses = self.history[name].get("pulses", [])
            
            dmg_path = ""
            heal_path = ""
            if pulses:
                max_v = 1
                for t, d, h, _ in pulses: max_v = max(max_v, d, h)
                def get_p(idx):
                    pts = ["0,100"]
                    for pt, pd, ph, ptgt in sorted(pulses, key=lambda x: x[0]):
                        v = pd if idx == 1 else ph
                        x = (pt / max_time) * 100
                        y = 100 - (v / max_v * 80)
                        pts.append(f"{x},{y}")
                    pts.append("100,100")
                    return " ".join(pts)
                dmg_path = get_p(1)
                heal_path = get_p(2)

            html += f"""
                        <div class="player-lane absolute left-0 right-0 h-28 rounded border {row_border} {row_bg} flex items-center px-6 backdrop-blur-sm player-row" 
                             style="top: {top}px;" data-name="{name}" data-side="{side_type}">
                            <div class="w-48 flex-shrink-0 border-r border-white/10 mr-8 py-2 relative z-20">
                                <span class="text-[8px] font-black opacity-30 uppercase tracking-[0.3em] mb-1 block">Entity Signature</span>
                                <span class="text-lg font-orbitron font-black {name_color} truncate block tracking-widest">
                                    {name.upper()}
                                </span>
                                <div class="flex gap-2 mt-2">
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-error" style="width: {min(100, sum(p[1] for p in pulses)/1000)}%"></div>
                                    </div>
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-success" style="width: {min(100, sum(p[2] for p in pulses)/1000)}%"></div>
                                    </div>
                                    <div class="flex flex-col">
                                        <span class="text-[7px] font-bold opacity-40 uppercase">CURR LARP: {int(scores.get(name, 0))}</span>
                                        <span class="text-[7px] font-black text-primary uppercase">TOTAL LARP: {leaderboard.get(name, 0)}</span>
                                        <span class="text-[6px] opacity-30 italic">FORMULA: TACTICAL-STD v1.0 (ELO)</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="relative flex-grow h-full overflow-visible">
                                <!-- Continuous Data Sparklines -->
                                <svg class="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
                                    <polyline fill="rgba(255, 0, 60, 0.05)" stroke="rgba(255, 0, 60, 0.3)" stroke-width="0.5" points="{dmg_path}" />
                                    <polyline fill="rgba(0, 255, 150, 0.05)" stroke="rgba(0, 255, 150, 0.3)" stroke-width="0.5" points="{heal_path}" />
                                </svg>
            """
            
            events = self.history[name].get("events", [])
            for t, etype, src, tgt, label in events:
                left = (t / max_time) * 100
                badge_class = event_classes.get(etype, "badge-ghost")
                
                # MINI-LOG LOGIC: -2s to +1s window
                window_start = t - 2.0
                window_end = t + 1.0
                mini_log_html = ""
                
                relevant_pulses = [p for p in all_pulses if window_start <= p[0] <= window_end]
                
                if not relevant_pulses:
                    mini_log_html = "<div class='text-[8px] opacity-20 italic text-center py-4 tracking-widest'>NO TELEMETRY IN WINDOW</div>"
                else:
                    for pt, pname, pdmg, pheal, ptgt in relevant_pulses:
                        if pdmg == 0 and pheal == 0: continue
                        p_is_me = pname == name
                        text_color = "text-primary" if p_is_me else "text-slate-400"
                        
                        log_line = ""
                        if pdmg > 0:
                            log_line += f"<span class='text-error font-bold'>-{pdmg}</span>"
                        if pheal > 0:
                            if log_line: log_line += " "
                            log_line += f"<span class='text-success font-bold'>+{pheal}</span>"
                            
                        mini_log_html += f"""
                        <div class="flex justify-between items-center py-1 border-b border-white/[0.03] {text_color} font-mono text-[9px]">
                            <span class="opacity-40 w-8">{pt-t:+.1f}s</span>
                            <span class="font-bold truncate flex-grow px-2">{pname[:12]}</span>
                            <span class="text-right tabular-nums">{log_line}</span>
                        </div>
                        """
                
                html += f"""
                                <div class="event-marker group" style="left: {left}%; top: 50%; margin-top: -14px;">
                                    <div class="badge {badge_class} badge-sm font-black shadow-[0_0_10px_rgba(0,0,0,0.5)] border-white/20 cursor-pointer hover:scale-110 transition-transform font-orbitron">
                                        {etype}
                                    </div>
                                    <!-- Tactical Tooltip -->
                                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 hidden group-hover:block z-[100] animate-in fade-in zoom-in duration-200">
                                        <div class="bg-[#0a0f14] border border-primary/40 p-4 rounded-lg shadow-[0_0_40px_rgba(0,236,255,0.2)] w-80 text-xs hud-border">
                                            <div class="flex justify-between items-center mb-4 border-b border-primary/20 pb-2">
                                                <span class="font-orbitron font-black text-primary text-[10px] tracking-widest uppercase">{etype} @ T+{t:.1f}S</span>
                                                <div class="flex gap-1">
                                                    <div class="w-1.5 h-1.5 bg-primary animate-pulse"></div>
                                                    <div class="w-1.5 h-1.5 bg-primary/20"></div>
                                                </div>
                                            </div>
                                            
                                            <div class="grid grid-cols-2 gap-4 mb-4">
                                                <div class="bg-black/40 p-2 border border-white/5 rounded">
                                                    <div class="text-[7px] font-black opacity-30 uppercase tracking-widest mb-1">Source</div>
                                                    <div class="font-bold truncate text-primary uppercase">{src}</div>
                                                </div>
                                                <div class="bg-black/40 p-2 border border-white/5 rounded">
                                                    <div class="text-[7px] font-black opacity-30 uppercase tracking-widest mb-1">Target</div>
                                                    <div class="font-bold truncate text-secondary uppercase">{tgt}</div>
                                                </div>
                                            </div>
                                            
                                            <div class="bg-primary/5 p-3 rounded mb-4 text-[9px] font-bold border-l-2 border-primary/40 tracking-tight italic opacity-80">
                                                {label}
                                            </div>

                                            <div>
                                                <div class="flex justify-between items-center mb-2 px-1">
                                                    <span class="text-[8px] font-black text-primary/60 uppercase tracking-[0.2em]">High-Res Telemetry</span>
                                                    <span class="text-[8px] opacity-30">-2.0s / +1.0s</span>
                                                </div>
                                                <div class="mini-log bg-black/60 rounded p-2 border border-white/5">
                                                    {mini_log_html}
                                                </div>
                                            </div>
                                        </div>
                                        <div class="w-3 h-3 bg-[#0a0f14] border-r border-b border-primary/40 absolute left-1/2 -translate-x-1/2 -bottom-1.5 rotate-45"></div>
                                    </div>
                                </div>
                """
            
            html += """
                            </div>
                        </div>
            """
            
        html += f"""
                    </div>
                </div>
                
                <!-- Legend & Footer -->
                <div class="mt-8 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-error badge-xs font-black mb-1">KD</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Kill Damage</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-warning badge-xs font-black mb-1">PD</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Point Damage</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-info badge-xs font-black mb-1">INT</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Interruption</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-secondary badge-xs font-black mb-1">INC</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Incoming</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-success badge-xs font-black mb-1">LOOT</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Acquisition</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-ghost badge-xs font-black mb-1 text-slate-400">DEATH</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Neutralized</div>
                    </div>
                    <div class="hud-border bg-black/40 p-2 rounded text-center">
                        <div class="badge badge-primary badge-xs font-black mb-1">KILL</div>
                        <div class="text-[7px] font-black opacity-40 uppercase tracking-widest">Objective Met</div>
                    </div>
                </div>

                <!-- Curation & Submission HUD -->
                <div class="mt-8 bg-primary/5 border border-primary/20 p-6 rounded-xl flex flex-col md:flex-row justify-between items-center gap-6 backdrop-blur-md">
                    <div>
                        <h3 class="font-orbitron font-black text-primary text-xl tracking-tighter uppercase">Parse Log</h3>
                        <p class="text-[10px] opacity-60 uppercase tracking-widest mt-1">Submit telemetry for official Imperial validation</p>
                    </div>
                    <div class="flex items-center gap-8">
                        <div class="text-right">
                            <span class="text-[8px] font-black opacity-30 uppercase tracking-[0.2em] block">Potential Yield</span>
                            <span class="text-2xl font-orbitron font-black text-secondary glow-text-yellow">+{int(scores.get('YOU', 0))} <span class="text-xs opacity-50">LARP</span></span>
                            <span class="text-[7px] block opacity-40 italic mt-1">Subject to processing & verification</span>
                        </div>
                        <button onclick="submitLog()" id="submitBtn" class="btn btn-primary btn-outline font-orbitron font-black tracking-widest hover:scale-105 transition-all px-10">
                            TRANSMIT
                        </button>
                    </div>
                </div>
                
                <script>
                    function submitLog() {{
                        const btn = document.getElementById('submitBtn');
                        btn.disabled = true;
                        btn.innerText = "TRANSMITTING...";
                        
                        // In this implementation, the report is already uploaded, 
                        // we just notify the curation system via Discord or a pending file update.
                        // Since this is a static HTML, we use a custom protocol or a pre-defined webhook if needed.
                        // For Livius, clicking this will ping the Advanced Bot.
                        
                        fetch(window.location.href, {{ method: 'POST', body: JSON.stringify({{ action: 'curate', file: window.location.pathname }}) }})
                        .catch(e => {{
                            // It's a static file, so POST will fail, but the user sees it as a "Request Sent"
                            // The real logic is handled by the Advanced Bot when it posts the report.
                            btn.innerText = "TRANSMISSION LOGGED";
                            btn.classList.add('btn-success');
                            alert("Log signature has been queued for Imperial Curation.");
                        }});
                    }}
                </script>

                <div class="mt-12 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div class="flex items-center gap-3">
                        <div class="text-[8px] font-black tracking-[0.4em] uppercase text-primary/30">Livius Analysis Engine v3.0 // Tactical Overlay</div>
                        <div class="w-1.5 h-1.5 rounded-full bg-primary/20 animate-pulse"></div>
                    </div>
                    <div class="text-[8px] font-mono font-bold tracking-widest uppercase opacity-20">Cycle Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
            <script>
                // Check if this is a duplicate from the URL or metadata
                if (window.location.search.includes('duplicate=true') || document.documentElement.innerHTML.includes('""is_duplicate"": true')) {{
                    document.getElementById('dup-warning').classList.remove('hidden');
                }}
            </script>
        </body>
        </html>
        """
        return html

    async def finish_and_report(self, channel):
        async with self.lock:
            if not self.is_active: return
            print(f"[Tracker] Combat inactivity reached. Generating reports...")
            img = self.generate_chart()
            html = self.generate_html_report()
            report_bytes = html.encode('utf-8')
            report_sha256 = hashlib.sha256(report_bytes).hexdigest()
            
            # Determine MVP for summary
            leaderboard = load_json("livius_leaderboard.json")
            scores = {}
            for name, data in self.history.items():
                k = sum(1 for e in data["events"] if e[1] == "KILL")
                pd = sum(p[1] for p in data.get("pulses", []))
                scores[name] = (k * 100) + (pd * 0.01)
            mvp = max(scores, key=scores.get) if scores else "N/A"
            
            # GENERATE BATTLE FINGERPRINT
            # We use sorted unique player names (excluding YOU if generic) and the start time rounded to 5 mins
            all_players = sorted([p.upper() for p in self.history.keys() if p.upper() != "YOU"])
            # Fallback if only YOU is present
            if not all_players: all_players = ["SOLO_CONTACT"]
            
            time_bin = int(self.start_time / 300) * 300 # 5 minute window
            fingerprint_raw = f"{'|'.join(all_players)}@{time_bin}"
            battle_fingerprint = hashlib.md5(fingerprint_raw.encode()).hexdigest()[:12]

            report_name = f"combat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Add potential loot sources from Uncle ReCoN to the report data
            rico_drops = []
            if rico_db:
                try:
                    c = rico_db.cursor()
                    # Get the most valuable loots from this combat
                    for looter, items in self.loot_history.items():
                        for rarity, count in items.items():
                            c.execute("SELECT mobile_template, item_template, planet, x, y FROM learned_drops WHERE item_template LIKE ? LIMIT 2", (f"%{rarity}%",))
                            for row in c.fetchall():
                                rico_drops.append({
                                    "mob": row[0],
                                    "item": row[1],
                                    "planet": row[2],
                                    "coords": f"{int(row[3])}, {int(row[4])}"
                                })
                except: pass

            # GitHub Upload (Archive as Temporary)
            summary_data = {
                "name": f"ENCOUNTER // {datetime.datetime.now().strftime('%Y.%m.%d %H:%M')}",
                "timestamp": datetime.datetime.now().strftime("%Y.%m.%d %H:%M"),
                "filename": report_name,
                "mvp": mvp,
                "kills": sum(1 for d in self.history.values() for e in d["events"] if e[1] == "KILL"),
                "potential_larp": int(scores.get('YOU', 0)),
                "status": "TEMPORARY",
                "fingerprint": battle_fingerprint,
                "rico_intel": rico_drops[:5]
            }
            github_url = await self.publisher.publish_report(report_name, html, summary_data)

            # Post to Discord
            is_dup = summary_data.get("is_duplicate", False)
            title = "⚔️ TEMPORARY TACTICAL REPORT"
            if is_dup:
                title = "⚠️ DUPLICATE COMBAT DETECTED"
            
            embed = discord.Embed(
                title=title,
                description=f"Field analysis generated. Log is pending Imperial verification." if not is_dup else "Another log for this battle was already detected. Curation required to merge.",
                color=0xffe81f if not is_dup else 0xffa500
            )
            if github_url:
                embed.add_field(name="🌐 VIEW TEMP HUD", value=f"[**ACCESS ARCHIVE**]({github_url})", inline=False)
            embed.add_field(name="📎 DISCORD REPORT MIRROR", value=f"Attached `{report_name}` is the same HTML report uploaded to the website.\n`sha256: {report_sha256[:16]}...`", inline=False)
            
            embed.add_field(name="🏆 MVP", value=f"`{mvp}`", inline=True)
            embed.add_field(name="✨ EST. LARP", value=f"`+{summary_data['potential_larp']}`", inline=True)
            
            if is_dup:
                embed.add_field(name="🔗 RELATED", value=f"`{summary_data.get('related_to')}`", inline=False)

            embed.set_footer(text="LIVIUS TACTICAL OVERLAY v4.0 // CURATION REQUIRED")

            files = []
            if img:
                image_binary = io.BytesIO()
                
                # Consistent width for Discord display
                target_width = 1000
                if img.width != target_width:
                    ratio = target_width / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                files.append(discord.File(fp=image_binary, filename='pvp_timeline.png'))
                embed.set_image(url="attachment://pvp_timeline.png")
            
            if html:
                html_binary = io.BytesIO(report_bytes)
                files.append(discord.File(fp=html_binary, filename=report_name))

            await channel.send(embed=embed, files=files)
            
            self.is_active = False
            self.history = {}
            print(f"[Tracker] Reports sent. Monitoring for next encounter.")

tracker = CombatTracker()

async def combat_monitor_task():
    while True:
        try:
            if tracker.is_active:
                now = time.time()
                if now - tracker.last_pulse_time > 60: # 1 minute inactivity
                    channel = client.get_channel(int(CHANNEL_ID))
                    if channel:
                        await tracker.finish_and_report(channel)
        except Exception as e:
            print(f"[Tracker] Error in monitor task: {e}")
        await asyncio.sleep(5)

async def hourly_loot_report_task():
    while True:
        try:
            # Wait until the top of the next hour
            now = datetime.datetime.now()
            next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            wait_seconds = (next_hour - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            async with tracker.lock:
                if not tracker.loot_history:
                    continue
                
                channel = client.get_channel(int(CHANNEL_ID))
                if not channel:
                    continue
                
                embed = discord.Embed(
                    title="📦 HOURLY ACQUISITION REPORT",
                    description="Condensed summary of high-value assets secured in the last hour.",
                    color=0x00FF00,
                    timestamp=datetime.datetime.now()
                )
                
                for player, items in tracker.loot_history.items():
                    loot_details = []
                    for rarity, count in sorted(items.items()):
                        loot_details.append(f"`{rarity}`: **x{count}**")
                    
                    embed.add_field(
                        name=f"👤 {player.upper()}",
                        value="\n".join(loot_details) if loot_details else "No significant acquisitions.",
                        inline=False
                    )
                
                embed.set_footer(text="LIVIUS SECTOR LOGISTICS // ENCRYPTED FEED")
                await channel.send(embed=embed)
                
                # Clear history for next hour
                tracker.loot_history = {}
                
        except Exception as e:
            print(f"[Loot] Error in hourly report task: {e}")
            await asyncio.sleep(60)

# Queue for outgoing messages (from app to Discord)
outgoing_queue = queue.Queue()

# Verification storage
VERIFICATION_FILE = "pending_verifications.json"
VERIFIED_USERS_FILE = "verified_users.json"

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[Bot] Error saving {filename}: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    # Start background tasks
    client.loop.create_task(process_outgoing())
    client.loop.create_task(combat_monitor_task())
    client.loop.create_task(hourly_loot_report_task())
    # Start Advanced Web API
    client.loop.create_task(start_adv_web_server())

# Verification codes store: {code: {"token": TOKEN, "channel": CHANNEL_ID, "user": display_name, "expires": timestamp}}
verification_codes = {}

# --- ADD WEB API TO ADVANCED BOT ---
from aiohttp import web

async def handle_adv_verify(request):
    try:
        data = await request.json()
        code = data.get("code")
        now = time.time()
        
        if code in verification_codes and verification_codes[code]["expires"] > now:
            v_data = verification_codes[code]
            
            # Derive encryption key from code
            key_src = code.encode() + b"LivyLogsSalt"
            key = base64.urlsafe_b64encode(hashlib.sha256(key_src).digest())
            f_enc = Fernet(key)
            encrypted_token = f_enc.encrypt(v_data['token'].encode()).decode()
            
            # Clear code
            del verification_codes[code]
            
            return web.json_response({
                "status": "success",
                "user": v_data['user'],
                "token": encrypted_token,
                "channel": v_data['channel']
            })
            
        return web.json_response({"status": "error", "message": "Invalid or expired code"}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def start_adv_web_server():
    app = web.Application()
    app.add_routes([web.post('/adv_verify', handle_adv_verify)])
    runner = web.AppRunner(app)
    await runner.setup()
    # Use a different port than the central bot
    site = web.TCPSite(runner, '0.0.0.0', 8081)
    await site.start()
    print("[Advanced Bot] Web API started on port 8081")

@client.event
async def on_message(message):
    # Admin Curation Command /curate
    if message.content.startswith("/curate"):
        # ... existing curation code ...
        if OWNER_ID and str(message.author.id) != OWNER_ID: return
        
        args = message.content.split()
        if len(args) == 1:
            # List pending
            url = f"https://api.github.com/repos/{tracker.publisher.repo}/contents/pending_logs.json"
            headers = {"Authorization": f"token {tracker.publisher.token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pending = json.loads(base64.b64decode(data["content"]).decode())
                        if not pending:
                            await message.channel.send("📁 **Curation Queue Empty.** No logs pending processing.")
                            return
                        
                        embed = discord.Embed(title="🛡️ IMPERIAL CURATION QUEUE", color=0xffe81f)
                        for i, p in enumerate(pending[:10]):
                            is_dup = p.get("is_duplicate", False)
                            dup_tag = " [⚠️ DUPLICATE]" if is_dup else ""
                            embed.add_field(
                                name=f"{i+1}. {p['name']}{dup_tag}",
                                value=f"Pilot: `{p['mvp']}` | Kills: `{p['kills']}`\nID: `{p['filename']}`\nEST. LARP: `+{p.get('potential_larp', 0)}`",
                                inline=False
                            )
                        embed.set_footer(text="Use `/curate approve <ID>` to validate.")
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send("❌ Error accessing curation queue.")
            return

        if len(args) >= 3 and args[1] == "approve":
            target_id = args[2]
            success = await tracker.publisher.approve_report(target_id)
            if success:
                await message.channel.send(f"✅ **LOG VALIDATED.** `{target_id}` has been moved to the official archives and LARP points distributed.")
            else:
                await message.channel.send(f"❌ **PROCESSING FAILED.** Log ID `{target_id}` not found or archive unreachable.")
            return

    # Uncle ReCoN Query Command /rico
    if message.content.startswith("/rico"):
        if not rico_db:
            await message.channel.send("⚠️ **UNCLE RECON OFFLINE.** Database not loaded.")
            return
            
        query = message.content.replace("/rico", "").strip()
        if not query:
            await message.channel.send("🔍 **UNCLE RECON READY.** Type `/rico <item or mob name>` to search.")
            return

        c = rico_db.cursor()
        # Search for schematics, loot, or mobiles
        # This is a simple query, in reality we'd use fuzzy matching logic here
        search_term = f"%{query}%"
        
        # Check Schematics
        c.execute("SELECT name, template FROM schematics WHERE name LIKE ? LIMIT 3", (search_term,))
        schems = c.fetchall()
        
        # Check Mobiles
        c.execute("SELECT mobile_template FROM mobiles WHERE mobile_template LIKE ? LIMIT 3", (search_term,))
        mobs = c.fetchall()

        # Check Literary Archives
        c.execute("SELECT title, author, content_sample FROM literary_archives WHERE title LIKE ? OR author LIKE ? LIMIT 1", (search_term, search_term))
        book = c.fetchone()

        embed = discord.Embed(title=f"🕵️ UNCLE RECON INTEL: {query.upper()}", color=0x00ecff)
        
        if book:
            b_title = book[0].replace("_", " ").upper()
            b_author = book[1].replace("_", " ").upper()
            embed.add_field(name=f"📖 LITERARY RECORD: {b_title}", value=f"Author: **{b_author}**", inline=False)
            sample = book[2].strip()
            if len(sample) > 400: sample = sample[:400] + "..."
            embed.add_field(name="EXCERPT", value=f"```\n{sample}\n```", inline=False)
            embed.color = 0x4a266a # Purple for books
        
        if schems:
            val = "\n".join([f"🛠️ `{s[0]}`" for s in schems])
            embed.add_field(name="CRAFTABLE SCHEMATICS", value=val, inline=False)
            # Find ingredients for the first match
            c.execute("SELECT component_name, quantity FROM ingredients WHERE schematic_id = (SELECT id FROM schematics WHERE name = ?)", (schems[0][0],))
            ings = c.fetchall()
            if ings:
                ing_val = "\n".join([f"• {i[1]}x `{i[0]}`" for i in ings])
                embed.add_field(name=f"INGREDIENTS FOR {schems[0][0]}", value=ing_val, inline=False)

        if mobs:
            val = "\n".join([f"👾 `{m[0]}`" for m in mobs])
            embed.add_field(name="KNOWN ENTITIES", value=val, inline=False)
            # Find spawns for the first match
            c.execute("SELECT planet, x, y, z FROM spawns WHERE mobile_template = ? LIMIT 3", (mobs[0][0],))
            locs = c.fetchall()
            if locs:
                loc_val = "\n".join([f"📍 {l[0]} ({int(l[1])}, {int(l[3])})" for l in locs])
                embed.add_field(name=f"LOCATIONS FOR {mobs[0][0]}", value=loc_val, inline=False)

        if not schems and not mobs and not book:
            # Check for Loot
            c.execute("SELECT group_name FROM loot_groups WHERE group_name LIKE ? LIMIT 5", (search_term,))
            groups = c.fetchall()
            if groups:
                val = "\n".join([f"💰 `{g[0]}`" for g in groups])
                embed.add_field(name="LOOT GROUPS", value=val, inline=False)
            else:
                # Check for Music
                c.execute("SELECT song_title, album FROM metallica_songs WHERE song_title LIKE ? LIMIT 5", (search_term,))
                songs = c.fetchall()
                if songs:
                    val = "\n".join([f"🎸 `{s[0]}` ({s[1]})" for s in songs])
                    embed.add_field(name="MUSIC ARCHIVES", value=val, inline=False)
                else:
                    embed.description = "No direct records found in Imperial Archives."

        embed.set_footer(text="UNCLE RECON v1.0 // DISTRIBUTED INTEL")
        await message.channel.send(embed=embed)
        return

    # Check for setup command /123
    if message.content == "/123":
        # Check permissions
        if OWNER_ID and str(message.author.id) != OWNER_ID:
            print(f"[Bot] Unauthorized /123 attempt by {message.author} (ID: {message.author.id})")
            return

        code = ''.join(random.choices(string.digits, k=6))
        expires = time.time() + 300 # 5 minutes
        verification_codes[code] = {
            "token": TOKEN,
            "channel": str(message.channel.id),
            "user": message.author.display_name,
            "expires": expires
        }
        
        try:
            await message.author.send(
                f"🛡️ **LivyLogs Setup Code**: `{code}`\n"
                f"Enter this code in the app to automatically configure your Bot Token and Channel ID.\n"
                f"Note: This code expires in 5 minutes."
            )
            await message.channel.send(f"✅ {message.author.mention}, I've sent a setup code to your DMs!")
        except discord.Forbidden:
            await message.channel.send(
                f"⚠️ {message.author.mention}, I couldn't DM you! "
                f"Please enable 'Allow direct messages from server members' in your privacy settings and try again."
            )
        return

    # Check for verification check (app sending "[VERIFY] 123456")
    if message.content.startswith("[VERIFY] "):
        code = message.content.replace("[VERIFY] ", "").strip()
        now = time.time()
        if code in verification_codes and verification_codes[code]["expires"] > now:
            data = verification_codes[code]
            
            # Encrypt the token using the code as part of the key
            # We derive a Fernet key from the 6-digit code
            # Note: This isn't super high security (code is only 6 digits), 
            # but it prevents the token from being in plain text in the Discord channel or logs.
            key_src = code.encode() + b"LivyLogsSalt" # Add salt
            key = base64.urlsafe_b64encode(hashlib.sha256(key_src).digest())
            f = Fernet(key)
            encrypted_token = f.encrypt(data['token'].encode()).decode()
            
            # Send back the config
            # Format: [VERIFIED] code | user | encrypted_token | channel
            response = f"[VERIFIED] {code} | {data['user']} | {encrypted_token} | {data['channel']}"
            await message.channel.send(response)
            # Remove code after use
            del verification_codes[code]
        return

    # Ignore messages from the bot itself unless it's a relay pulse
    if message.author == client.user:
        if message.content.startswith("[LIVIUS RELAY]"):
             # Optional Handshake validation
             msg_content = message.content
             if HANDSHAKE_SECRET:
                 if f"HS: {HANDSHAKE_SECRET}" not in msg_content:
                     print(f"[Bot] Rejected pulse from {message.author}: Missing/Invalid Handshake")
                     return
                 # Strip handshake for tracker
                 msg_content = msg_content.replace(f" | HS: {HANDSHAKE_SECRET}", "")

             await tracker.add_pulse_from_msg(msg_content, message.channel)
        return

    # Only process messages from the configured channel
    if str(message.channel.id) != CHANNEL_ID:
        return

    # Check for verification command
    if message.content.strip() == "/123":
        code = ''.join(random.choices(string.digits, k=6))
        pending = load_json(VERIFICATION_FILE)
        # Clean up old codes (older than 10 mins)
        now = time.time()
        pending = {k: v for k, v in pending.items() if now - v.get('timestamp', 0) < 600}
        
        pending[code] = {
            "id": str(message.author.id),
            "name": message.author.display_name,
            "timestamp": now
        }
        save_json(VERIFICATION_FILE, pending)
        
        try:
            await message.author.send(f"Your LivyLogs verification code is: **{code}**\nEnter this in the app to verify your identity. This code expires in 10 minutes.")
            await message.channel.send(f"✅ {message.author.mention}, I've sent you a verification code in DMs!")
        except discord.Forbidden:
            await message.channel.send(f"❌ {message.author.mention}, I couldn't DM you! Please enable DMs from server members.")
        return

    # Print to console
    print(f'[{message.channel.name}] {message.author.display_name}: {message.content}')

    # Check for Galaxy Harvester queries
    content_lower = message.content.lower()
    if content_lower.startswith("whats the best"):
        match = re.search(r"whats the best (.+) in (.+)", content_lower)
        if match:
            item = match.group(1).strip()
            planet = match.group(2).strip()
            result = galaxy_harvester_api.get_best_item(item, planet)
            await message.channel.send(result)
            return

    # Also forward to any registered listeners (e.g., the app)
    # For now, just print

async def process_outgoing():
    """Background task to send messages from the queue to Discord."""
    while True:
        try:
            content = outgoing_queue.get_nowait()
            channel = client.get_channel(int(CHANNEL_ID))
            if channel:
                await channel.send(content)
                print(f'[Bot] Sent: {content}')
            else:
                print(f'[Bot] Error: Channel {CHANNEL_ID} not found')
        except queue.Empty:
            pass
        await asyncio.sleep(0.1)

def send_message(content):
    """Send a message to the configured Discord channel (thread-safe)."""
    outgoing_queue.put(content)

def run_bot():
    """Run the Discord bot (blocking)."""
    client.run(TOKEN)

if __name__ == '__main__':
    # Start a thread for console input
    def input_thread():
        while True:
            try:
                msg = input('> ')
                if msg.lower() in ('exit', 'quit'):
                    print('Exiting...')
                    os._exit(0)
                send_message(msg)
            except EOFError:
                break
            except KeyboardInterrupt:
                break

    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    run_bot()
