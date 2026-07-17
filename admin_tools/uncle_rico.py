import os
import re
import sqlite3
import json
import zstandard as zstd
import io
import time
import threading
from pathlib import Path

class UncleReCoNScanner:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.loot_path = self.base_path / "loot/groups"
        self.mobile_path = self.base_path / "mobile"
        self.screenplay_path = self.base_path / "screenplays"
        self.schematic_path = self.base_path / "object/draft_schematic"
        
        self.db_path = "uncle_rico.db"
        self.compressed_db_path = "uncle_rico.v12"
        
        # Regex patterns for Lua parsing
        self.loot_group_pattern = re.compile(r'lootGroups = \{(.*?)\}', re.DOTALL)
        self.mobile_template_pattern = re.compile(r'template = "(.*?)"')
        self.coord_pattern = re.compile(r'spawnMobile\("(.*?)", "(.*?)", ([\-\d\.]+), ([\-\d\.]+), ([\-\d\.]+), ([\-\d\.]+), "(.*?)"\)')
        self.ingredient_pattern = re.compile(r'\{"?ingredientType"?\s*=\s*(\d+),\s*"?ingredientName"?\s*=\s*"(.*?)",\s*"?quantity"?\s*=\s*(\d+)')

    def normalize_name(self, name):
        """Removes prefixes like advanced_, superior_, etc. for better correlation."""
        if not name: return ""
        # Remove common SWG item prefixes
        prefixes = ["advanced_", "superior_", "modified_", "exceptional_", "legendary_", "refined_", "heavy_", "light_"]
        norm = name.lower().strip()
        for p in prefixes:
            if norm.startswith(p):
                norm = norm[len(p):]
        return norm

    def init_db(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Static Game Data
        c.execute('''CREATE TABLE loot_groups (id INTEGER PRIMARY KEY, group_name TEXT UNIQUE)''')
        c.execute('''CREATE TABLE loot_items (id INTEGER PRIMARY KEY, group_id INTEGER, item_template TEXT)''')
        c.execute('''CREATE TABLE mobiles (
            id INTEGER PRIMARY KEY, 
            mobile_template TEXT UNIQUE, 
            custom_name TEXT,
            health_min INTEGER DEFAULT 0,
            health_max INTEGER DEFAULT 0,
            armor_rating INTEGER DEFAULT 0,
            kinetic INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 0,
            blast INTEGER DEFAULT 0,
            stun INTEGER DEFAULT 0,
            lightsaber INTEGER DEFAULT 0,
            heat INTEGER DEFAULT 0,
            cold INTEGER DEFAULT 0,
            acid INTEGER DEFAULT 0,
            electricity INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE mobile_loot (mobile_id INTEGER, group_id INTEGER)''')
        c.execute('''CREATE TABLE spawns (
            id INTEGER PRIMARY KEY, 
            mobile_template TEXT, 
            planet TEXT, 
            x REAL, 
            y REAL, 
            z REAL,
            respawn_timer INTEGER DEFAULT 0,
            poi_name TEXT
        )''')
        c.execute('''CREATE TABLE schematics (id INTEGER PRIMARY KEY, name TEXT, template TEXT)''')
        c.execute('''CREATE TABLE ingredients (id INTEGER PRIMARY KEY, schematic_id INTEGER, component_name TEXT, normalized_name TEXT, quantity INTEGER)''')
        
        c.execute('''CREATE TABLE item_stats (
            template TEXT PRIMARY KEY,
            name TEXT,
            item_type TEXT,
            weapon_type TEXT,
            damage_min REAL,
            damage_max REAL,
            speed REAL,
            wound_chance REAL,
            armor_piercing TEXT,
            damage_type TEXT,
            accuracy_zero REAL,
            accuracy_mid REAL,
            accuracy_max REAL,
            range_zero REAL,
            range_mid REAL,
            range_max REAL,
            health_cost REAL,
            action_cost REAL,
            mind_cost REAL,
            armor_rating TEXT,
            effectiveness REAL,
            kinetic REAL,
            energy REAL,
            blast REAL,
            stun REAL,
            heat REAL,
            cold REAL,
            acid REAL,
            electricity REAL
        )''')
        
        # Metallica Dataset
        c.execute('''CREATE TABLE metallica_songs (id INTEGER PRIMARY KEY, song_title TEXT, album TEXT, trivia TEXT, tab TEXT)''')

        # Literary Archives
        c.execute('''CREATE TABLE literary_archives (id INTEGER PRIMARY KEY, title TEXT, author TEXT, content_sample TEXT, file_path TEXT)''')
        
        conn.commit()
        return conn

    def scan_all(self):
        print("[Uncle ReCoN] Starting Imperial Indexing...")
        start = time.time()
        conn = self.init_db()
        
        self._parse_loot(conn)
        self._parse_mobiles(conn)
        self._parse_screenplays(conn)
        self._parse_schematics(conn)
        self._parse_items(conn)
        self._parse_metallica(conn)
        self._parse_literary_archives(conn)
        
        conn.commit()
        conn.close()
        
        self._compress_db()
        print(f"[Uncle ReCoN] Indexing complete in {time.time()-start:.2f}s")

    def _parse_metallica(self, conn):
        print("[Uncle ReCoN] Learning Metallica Discography...")
        c = conn.cursor()
        try:
            from metallica import metallica_dataset, metallica_dataset_part2, megadeth_dataset, ozzy_sabbath_dataset, ozzy_solo_dataset
            all_sets = [metallica_dataset, metallica_dataset_part2, megadeth_dataset, ozzy_sabbath_dataset, ozzy_solo_dataset]
            
            for s_set in all_sets:
                for song in s_set:
                    title = song.get("song_title", "Unknown")
                    album = song.get("album", "Unknown")
                    trivia = song.get("trivia", "")
                    tab = song.get("main_riff_tab", {}).get("notation", "")
                    c.execute("INSERT INTO metallica_songs (song_title, album, trivia, tab) VALUES (?, ?, ?, ?)",
                             (title, album, trivia, tab))
        except ImportError:
            print("[Uncle ReCoN] metallica.py not found, skipping music dataset.")
        except Exception as e:
            print(f"[Uncle ReCoN] Error parsing Metallica data: {e}")

    def _parse_literary_archives(self, conn):
        print("[Uncle ReCoN] Indexing Literary Archives (3000 Books)...")
        c = conn.cursor()
        books_path = Path("3000")
        if not books_path.exists():
            print("[Uncle ReCoN] '3000' folder not found. Skipping literary archives.")
            return

        count = 0
        for file in books_path.rglob("*"):
            if file.is_file() and file.suffix.lower() in [".txt", ".htm", ".html"]:
                if "index.html" in file.name.lower(): continue
                
                try:
                    # Infer author and title from path
                    # Structure: 3000/3000/A/Author/BookTitle/File
                    parts = file.parts
                    author = "Unknown"
                    title = "Unknown"
                    
                    if len(parts) >= 5:
                        author = parts[3]
                        title = parts[4]
                    
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000) # Read first 10k chars for sample/learning
                        
                    c.execute("INSERT INTO literary_archives (title, author, content_sample, file_path) VALUES (?, ?, ?, ?)",
                             (title, author, content, str(file)))
                    count += 1
                    if count % 500 == 0:
                        print(f"[Uncle ReCoN] Indexed {count} book files...")
                except Exception as e:
                    continue
        
        print(f"[Uncle ReCoN] Successfully indexed {count} literary entries.")

    def _parse_loot(self, conn):
        print("[Uncle ReCoN] Indexing Loot Groups and Items...")
        c = conn.cursor()
        for file in self.loot_path.rglob("*.lua"):
            try:
                with open(file, 'r', errors='ignore') as f:
                    content = f.read()
                    group_name = file.stem
                    c.execute("INSERT OR IGNORE INTO loot_groups (group_name) VALUES (?)", (group_name,))
                    group_id = c.execute("SELECT id FROM loot_groups WHERE group_name = ?", (group_name,)).fetchone()[0]
                    
                    # 1. Capture direct items: {itemTemplate = "object/...", ...}
                    items = re.findall(r'itemTemplate\s*=\s*"(.*?)"', content)
                    for t in items:
                        c.execute("INSERT INTO loot_items (group_id, item_template) VALUES (?, ?)", (group_id, t))
                        # Also insert a more searchable version (no path, no iff)
                        short = t.split("/")[-1].replace(".iff", "").replace("shared_", "")
                        if short != t:
                            c.execute("INSERT INTO loot_items (group_id, item_template) VALUES (?, ?)", (group_id, short))
                        
                        # Special check for Janta Blood variant
                        if "janta_blood" in t.lower():
                             c.execute("INSERT OR IGNORE INTO loot_items (group_id, item_template) VALUES (?, ?)", (group_id, "janta blood"))
                    
                    # 2. Capture nested groups: {groupTemplate = "janta_common", ...}
                    # We'll store these as special entries in loot_items starting with "group:"
                    # so the RAG query can recursively follow them if needed, or we just flatten them.
                    nested_groups = re.findall(r'groupTemplate\s*=\s*"(.*?)"', content)
                    for ng in nested_groups:
                        c.execute("INSERT INTO loot_items (group_id, item_template) VALUES (?, ?)", (group_id, f"group:{ng}"))
            except Exception as e:
                print(f"[Uncle ReCoN] Error parsing loot file {file.name}: {e}")

    def _parse_mobiles(self, conn):
        print("[Uncle ReCoN] Indexing Mobiles and NPC Loot Tables...")
        c = conn.cursor()
        for file in self.mobile_path.rglob("*.lua"):
            try:
                with open(file, 'r', errors='ignore') as f:
                    content = f.read()
                    # 1. Capture the template name from the last line typically
                    # CreatureTemplates:addCreatureTemplate(janta_shaman, "janta_shaman")
                    template_match = re.search(r'addCreatureTemplate\(.*?, "(.*?)"\)', content)
                    if not template_match:
                        # Fallback to the object name if it's a direct assignment
                        template_match = re.search(r'(\w+)\s*=\s*Creature:new', content)
                    
                    if template_match:
                        template = template_match.group(1)
                        custom_name = None
                        # Try to find objectName or customName
                        name_match = re.search(r'objectName\s*=\s*"(.*?)"', content)
                        if name_match: 
                            custom_name = name_match.group(1).split(":")[-1].replace("_", " ").title()
                        
                        # Extract Health
                        h_min, h_max = 0, 0
                        h_match = re.search(r'health\s*=\s*\{(\d+),\s*(\d+)\}', content)
                        if h_match:
                            h_min, h_max = int(h_match.group(1)), int(h_match.group(2))
                        
                        # Extract Armor Rating
                        ar = 0
                        ar_match = re.search(r'armor\s*=\s*(\d+)', content)
                        if ar_match: ar = int(ar_match.group(1))
                        
                        # Extract Resistances
                        resists = {
                            "kinetic": 0, "energy": 0, "blast": 0, "stun": 0,
                            "lightsaber": 0, "heat": 0, "cold": 0, "acid": 0, "electricity": 0
                        }
                        for r_name in resists.keys():
                            r_match = re.search(rf'{r_name}\s*=\s*([\-\d]+)', content)
                            if r_match: resists[r_name] = int(r_match.group(1))

                        c.execute("""
                            INSERT OR IGNORE INTO mobiles (
                                mobile_template, custom_name, health_min, health_max, armor_rating,
                                kinetic, energy, blast, stun, lightsaber, heat, cold, acid, electricity
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            template, custom_name, h_min, h_max, ar,
                            resists["kinetic"], resists["energy"], resists["blast"], resists["stun"],
                            resists["lightsaber"], resists["heat"], resists["cold"], resists["acid"], resists["electricity"]
                        ))
                        mobile_id = c.execute("SELECT id FROM mobiles WHERE mobile_template = ?", (template,)).fetchone()[0]
                        
                        # 2. Capture Loot Groups - handle nested structures
                        # Look for blocks of groups = { ... }
                        groups = re.findall(r'group\s*=\s*"(.*?)",', content)
                        for g in groups:
                            c.execute("INSERT OR IGNORE INTO loot_groups (group_name) VALUES (?)", (g,))
                            gid = c.execute("SELECT id FROM loot_groups WHERE group_name = ?", (g,)).fetchone()[0]
                            c.execute("INSERT OR IGNORE INTO mobile_loot (mobile_id, group_id) VALUES (?, ?)", (mobile_id, gid))
            except Exception as e:
                print(f"[Uncle ReCoN] Error parsing mobile file {file.name}: {e}")

    def _parse_screenplays(self, conn):
        print("[Uncle ReCoN] Indexing Spawns, POIs and Dungeons...")
        c = conn.cursor()
        # Screenplays often define spawns via spawnMobile or similar
        for file in self.screenplay_path.rglob("*.lua"):
            try:
                # Get POI/Dungeon name from parent folder or file name
                poi_name = file.stem.replace("_", " ").title()
                if "Screenplay" in poi_name: poi_name = file.parent.name.replace("_", " ").title()

                with open(file, 'r', errors='ignore') as f:
                    content = f.read()
                    # 1. spawnMobile("planet", "template", x, z, y, respawn)
                    spawns = re.findall(r'spawnMobile\s*\(\s*"(.*?)"\s*,\s*"(.*?)"\s*,\s*([\-\d\.]+)\s*,\s*([\-\d\.]+)\s*,\s*([\-\d\.]+)\s*,\s*([\-\d\.]+)', content)
                    for s in spawns:
                        planet, template, x, z, y, respawn = s
                        c.execute("INSERT OR IGNORE INTO spawns (mobile_template, planet, x, y, z, respawn_timer, poi_name) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (template, planet, float(x), float(y), float(z), int(respawn) if respawn.isdigit() else 0, poi_name))
                    
                    # 2. spawnMobileByList patterns
                    # spawnMobileByList("tatooine", "tusken_raider_list", 100, 200, 300)
                    list_spawns = re.findall(r'spawnMobileByList\s*\(\s*"(.*?)"\s*,\s*"(.*?)"', content)
                    for ls in list_spawns:
                        planet, list_name = ls
                        c.execute("INSERT OR IGNORE INTO spawns (mobile_template, planet, x, y, z, poi_name) VALUES (?, ?, ?, ?, ?, ?)", 
                                 (list_name, planet, 0.0, 0.0, 0.0, poi_name))

                    # 3. Capture POI names/Dungeons explicitly
                    if "poi" in file.stem.lower() or "dungeon" in file.stem.lower() or "stronghold" in file.stem.lower():
                        c.execute("INSERT OR IGNORE INTO mobiles (mobile_template, custom_name) VALUES (?, ?)", 
                                 (f"poi_{file.stem}", poi_name))
            except Exception: pass

    def _parse_schematics(self, conn):
        print("[Uncle ReCoN] Indexing Crafting Schematics and Ingredients...")
        c = conn.cursor()
        for file in self.schematic_path.rglob("*.lua"):
            try:
                with open(file, 'r', errors='ignore') as f:
                    content = f.read()
                    # Capture name and target template
                    name_match = re.search(r'customObjectName\s*=\s*"(.*?)"', content)
                    schem_name = name_match.group(1) if name_match else file.stem.replace("_", " ").title()
                    
                    target_match = re.search(r'targetTemplate\s*=\s*"(.*?)"', content)
                    target = target_match.group(1) if target_match else ""
                    
                    c.execute("INSERT INTO schematics (name, template) VALUES (?, ?)", (schem_name, target))
                    sid = c.lastrowid
                    
                    # Ingredients parsing
                    # Titles: ingredientTitleNames = {"frame_assembly", ...}
                    # Resources: resourceTypes = {"aluminum_titanium", ...}
                    # Quantities: resourceQuantities = {65, ...}
                    
                    titles = re.search(r'ingredientTitleNames\s*=\s*\{(.*?)\}', content, re.DOTALL)
                    resources = re.search(r'resourceTypes\s*=\s*\{(.*?)\}', content, re.DOTALL)
                    quantities = re.search(r'resourceQuantities\s*=\s*\{(.*?)\}', content, re.DOTALL)
                    
                    if titles and resources and quantities:
                        t_list = [t.strip().strip('"') for t in titles.group(1).split(",")]
                        r_list = [r.strip().strip('"') for r in resources.group(1).split(",")]
                        q_list = [q.strip() for q in quantities.group(1).split(",")]
                        
                        for i in range(min(len(t_list), len(r_list), len(q_list))):
                            iname = t_list[i]
                            res = r_list[i]
                            qty = q_list[i]
                            if not qty.isdigit(): continue
                            
                            norm = self.normalize_name(res.split("/")[-1].replace(".iff", ""))
                            c.execute("INSERT INTO ingredients (schematic_id, component_name, normalized_name, quantity) VALUES (?, ?, ?, ?)",
                                     (sid, f"{iname} ({res.split('/')[-1]})", norm, int(qty)))
            except Exception: pass

    def _parse_items(self, conn):
        print("[Uncle ReCoN] Indexing Detailed Item Stats (Weapons/Armor)...")
        c = conn.cursor()
        # Item templates are often in object/tangible
        item_path = self.base_path / "object/tangible"
        if not item_path.exists(): return

        for file in item_path.rglob("*.lua"):
            try:
                with open(file, 'r', errors='ignore') as f:
                    content = f.read()
                    
                    # We need the template path relative to 'bin/scripts/'
                    try:
                        rel_path = file.relative_to(self.base_path).as_posix()
                        template = rel_path.replace(".lua", ".iff")
                    except:
                        template = file.name.replace(".lua", ".iff")

                    # Extract basic name
                    name_match = re.search(r'objectName\s*=\s*"(.*?)"', content)
                    name = name_match.group(1).split(":")[-1].replace("_", " ").title() if name_match else file.stem.replace("_", " ").title()

                    # Extract Stats
                    stats = {
                        "damage_min": 0, "damage_max": 0, "speed": 0, "wound_chance": 0,
                        "armor_piercing": "None", "damage_type": "Kinetic",
                        "accuracy_zero": 0, "accuracy_mid": 0, "accuracy_max": 0,
                        "range_zero": 0, "range_mid": 0, "range_max": 0,
                        "health_cost": 0, "action_cost": 0, "mind_cost": 0,
                        "armor_rating": "None", "effectiveness": 0,
                        "kinetic": 0, "energy": 0, "blast": 0, "stun": 0,
                        "heat": 0, "cold": 0, "acid": 0, "electricity": 0
                    }

                    # Weapon specific
                    m = re.search(r'minDamage\s*=\s*([\d\.]+)', content)
                    if m: stats["damage_min"] = float(m.group(1))
                    m = re.search(r'maxDamage\s*=\s*([\d\.]+)', content)
                    if m: stats["damage_max"] = float(m.group(1))
                    m = re.search(r'attackSpeed\s*=\s*([\d\.]+)', content)
                    if m: stats["speed"] = float(m.group(1))
                    m = re.search(r'woundChance\s*=\s*([\d\.]+)', content)
                    if m: stats["wound_chance"] = float(m.group(1))
                    m = re.search(r'armorPiercing\s*=\s*(\w+)', content)
                    if m: stats["armor_piercing"] = m.group(1)
                    m = re.search(r'damageType\s*=\s*(\d+)', content) # Often numerical in Lua
                    if m: stats["damage_type"] = m.group(1)
                    
                    # Ranges
                    m = re.search(r'pointBlankRange\s*=\s*([\d\.]+)', content)
                    if m: stats["range_zero"] = float(m.group(1))
                    m = re.search(r'idealRange\s*=\s*([\d\.]+)', content)
                    if m: stats["range_mid"] = float(m.group(1))
                    m = re.search(r'maxRange\s*=\s*([\d\.]+)', content)
                    if m: stats["range_max"] = float(m.group(1))
                    
                    # Accuracy
                    m = re.search(r'pointBlankAccuracy\s*=\s*([\d\.]+)', content)
                    if m: stats["accuracy_zero"] = float(m.group(1))
                    m = re.search(r'idealAccuracy\s*=\s*([\d\.]+)', content)
                    if m: stats["accuracy_mid"] = float(m.group(1))
                    m = re.search(r'maxAccuracy\s*=\s*([\d\.]+)', content)
                    if m: stats["accuracy_max"] = float(m.group(1))

                    # Armor specific
                    m = re.search(r'rating\s*=\s*(\w+)', content)
                    if m: stats["armor_rating"] = m.group(1)
                    m = re.search(r'effectiveness\s*=\s*([\d\.]+)', content)
                    if m: stats["effectiveness"] = float(m.group(1))
                    
                    # Resistances
                    for res in ["kinetic", "energy", "blast", "stun", "heat", "cold", "acid", "electricity"]:
                        m = re.search(rf'{res}\s*=\s*([\d\.]+)', content)
                        if m: stats[res] = float(m.group(1))

                    c.execute("""
                        INSERT OR REPLACE INTO item_stats (
                            template, name, damage_min, damage_max, speed, wound_chance,
                            armor_piercing, damage_type, accuracy_zero, accuracy_mid, accuracy_max,
                            range_zero, range_mid, range_max, health_cost, action_cost, mind_cost,
                            armor_rating, effectiveness, kinetic, energy, blast, stun, heat, cold, acid, electricity
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        template, name, stats["damage_min"], stats["damage_max"], stats["speed"], stats["wound_chance"],
                        stats["armor_piercing"], stats["damage_type"], stats["accuracy_zero"], stats["accuracy_mid"], stats["accuracy_max"],
                        stats["range_zero"], stats["range_mid"], stats["range_max"], stats["health_cost"], stats["action_cost"], stats["mind_cost"],
                        stats["armor_rating"], stats["effectiveness"], stats["kinetic"], stats["energy"], stats["blast"], stats["stun"],
                        stats["heat"], stats["cold"], stats["acid"], stats["electricity"]
                    ))
            except Exception: pass

    def _compress_db(self):
        if not os.path.exists(self.db_path):
            print(f"[Uncle ReCoN] Error: {self.db_path} not found. Cannot compress.")
            return
        try:
            import zstandard as zstd
            with open(self.db_path, "rb") as f:
                data = f.read()
            
            cctx = zstd.ZstdCompressor(level=11)
            compressed = cctx.compress(data)
            
            with open(self.compressed_db_path, "wb") as f:
                f.write(compressed)
            
            size_orig = os.path.getsize(self.db_path) / (1024*1024)
            size_comp = os.path.getsize(self.compressed_db_path) / (1024*1024)
            print(f"[Uncle ReCoN] Compression Ratio: {size_orig:.1f}MB -> {size_comp:.1f}MB")
        except ImportError:
            print("[Uncle ReCoN] zstandard not found, skipping compression. Using raw DB.")
            import shutil
            shutil.copy(self.db_path, self.compressed_db_path)

def load_rico_to_ram():
    """Loads the compressed Uncle ReCoN database (v12 preferred, v11 fallback) into an in-memory SQLite connection."""
    from utils import join_files
    
    db_versions = ["uncle_rico.v12", "uncle_rico.v11", "uncle_rico.db"]
    selected_version = None
    
    for v in db_versions:
        # Check for split parts if the file itself is missing
        if not os.path.exists(v) and os.path.exists(f"{v}.part0"):
            join_files(v)
            
        if os.path.exists(v):
            selected_version = v
            break
            
    if not selected_version:
        return None
    
    try:
        import sqlite3
        
        if selected_version.endswith(".db"):
            # Raw DB
            mem_db = sqlite3.connect(":memory:", check_same_thread=False)
            disk_db = sqlite3.connect(selected_version)
            disk_db.backup(mem_db)
            disk_db.close()
            print(f"[Uncle ReCoN] Successfully loaded raw {selected_version} into RAM.")
            return mem_db

        import zstandard as zstd
        with open(selected_version, "rb") as f:
            compressed_data = f.read()
        
        dctx = zstd.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_data)
        
        # Create an in-memory database
        mem_db = sqlite3.connect(":memory:", check_same_thread=False)
        temp_db_path = f"temp_rico_load_{int(time.time())}_{selected_version.split('.')[-1]}.db"
        with open(temp_db_path, "wb") as f:
            f.write(decompressed_data)
        
        disk_db = sqlite3.connect(temp_db_path)
        disk_db.backup(mem_db)
        disk_db.close()
        try: os.remove(temp_db_path)
        except: pass
        
        print(f"[Uncle ReCoN] Successfully loaded compressed {selected_version} into RAM.")
        return mem_db
    except Exception as e:
        print(f"[Uncle ReCoN] Error loading {selected_version}: {e}")
        return None

if __name__ == "__main__":
    # Example usage for building
    # To build the database, you need the SWG Core3 scripts directory.
    # Replace the path below with your local MMOCoreORB/bin/scripts path.
    base = r"C:\Users\LivyC\PycharmProjects\SWG\MMOCoreORB\bin\scripts"
    
    if not os.path.exists(base):
        print(f"[Uncle ReCoN] Error: Source path not found: {base}")
        print("Please edit uncle_rico.py and set 'base' to your local SWG scripts directory.")
    else:
        rico = UncleReCoNScanner(base)
        rico.scan_all()
