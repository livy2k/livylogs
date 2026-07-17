import requests
import threading
import json
import time
import os
import re
import random
from constants import AI_ENDPOINT, AI_API_KEY, AI_MODEL, LOCAL_MODEL_NAME, LOCAL_MODEL_PATH

class AIHandler:
    def __init__(self, app=None, system_prompt=""):
        self.app = app
        self.history = []
        self.is_loading_local = False # Keep for compatibility
        self.rico_quotes = [
            "How about that? I bet I could throw a football over those mountains.",
            "Back in '82, I could find any spawn in the galaxy... probably throw a football over those mountains too.",
            "If coach had just put me in, we would've been state champions. No doubt. No doubt in my mind.",
            "I'm just over here eating some steak and thinking about what could've been.",
            "You know, people still come up to me and ask about that season. It was legendary.",
            "Check out this van. It's got everything a man needs.",
            "I could've gone pro. I would've been soaking it up in a hot tub with a model right now.",
            "Things were just... better in '82.",
            "I bet I could still throw a pigskin a quarter mile. Easy.",
            "You ever feel like you're just stuck in the wrong decade? I do. Every day.",
            "If I could go back in time, I'd take state. No question.",
            "You know, Napoleon? You're just jealous because I've been chatting with models online all day.",
            "I'm training to be a cage fighter. Or a state champ. Whichever comes first.",
            "Grandma says I'm the best quarterback she's ever seen. And she saw the greats.",
            "Do you think anyone would want to buy a 24-piece set of Tupperware from a state champ?",
            "I'm thinking about getting into the bust enhancement business. High profit margins.",
            "Don't you ever wish you could go back? Just for a second? To the glory days?",
            "I've been working on a secret play. It involves a lot of vertical movement.",
            "You got any crystals? I'm looking to power up my time machine. Or just my van.",
            "I bet I could hurl a thermal detonator over those dunes. Probably take out a krayt dragon.",
            "Back in '82, I didn't need a map. I just followed the scent of victory.",
            "The Imperial Archives? Yeah, I read 'em. All 3,000 volumes. Between practice sessions.",
            "I'm like a fine wine. Or a vintage van. I just get better with age. And some new upholstery.",
            "Ever see a guy throw a touchdown while eating a steak? I have. It was me. In '82.",
            "The key to victory? It's all in the wrist. And the sheer, unadulterated will to win.",
            "I bet I could throw a droid clean into orbit if I really got some torque on it.",
            "They call it the 'Force'. I call it 'good old-fashioned hustle'. I had plenty in '82.",
            "You want a piece of the pie? You gotta bake the pie first. And I'm a master baker. Of victory.",
            "I once ran a marathon in full football gear just to prove a point. I didn't even break a sweat.",
            "If the scouts could see me now... they'd probably realize they made the biggest mistake in sports history.",
            "My van isn't just a vehicle. It's a mobile command center of pure, unbridled potential.",
            "I bet I could take on a whole squad of Stormtroopers with nothing but a pigskin and a dream.",
            "You ever see a sunset and think, 'Man, I bet I could throw a ball right over that sun'? I do.",
            "I'm not saying I'm a hero. I'm just saying the town's never been the same since I stopped playing."
        ]

    def ask(self, user_input, context_data=None, callback=None):
        """
        Processes the query using the Pseudo-AI logic (SQL + Regex + Personality).
        """
        # If no context data provided, attempt to fetch it here to keep it async
        if context_data is None:
             thread = threading.Thread(target=self._process_pseudo_ai_with_context, args=(user_input, callback))
        else:
             thread = threading.Thread(target=self._process_pseudo_ai, args=(user_input, context_data, callback))
        thread.daemon = True
        thread.start()

    def _process_pseudo_ai_with_context(self, user_input, callback):
        # Move RAG logic here to keep UI thread free
        context = ""
        if self.app and hasattr(self.app, "rico_db") and self.app.rico_db:
            try:
                import difflib
                c = self.app.rico_db.cursor()
                
                # Clean and Tokenize
                filler_words = ["where", "can", "i", "get", "how", "to", "find", "is", "loot", "drop", "from", "location", "what", "does", "the", "a", "an"]
                tokens = [w for w in user_input.lower().split() if w not in filler_words and len(w) > 2]
                if not tokens: tokens = [user_input.lower()]

                # 1. Anchor Matching & Fuzzy Correction
                corrected_tokens = []
                for t in tokens:
                    if hasattr(self.app, "learned_typos") and t in self.app.learned_typos:
                        corrected_tokens.append(self.app.learned_typos[t])
                        continue

                    # Try direct LIKE first
                    search_t = f"%{t}%"
                    c.execute("SELECT item_template FROM loot_items WHERE item_template LIKE ? LIMIT 1", (search_t,))
                    if c.fetchone():
                        corrected_tokens.append(t)
                        continue
                    c.execute("SELECT mobile_template FROM mobiles WHERE mobile_template LIKE ? LIMIT 1", (search_t,))
                    if c.fetchone():
                        corrected_tokens.append(t)
                        continue
                                
                    if len(t) >= 4:
                        c.execute("SELECT DISTINCT group_name FROM loot_groups WHERE group_name LIKE ? LIMIT 200", (f"{t[0]}%",))
                        candidates = [r[0] for r in c.fetchall()]
                        c.execute("SELECT DISTINCT item_template FROM loot_items WHERE item_template LIKE ? LIMIT 200", (f"{t[0]}%",))
                        candidates.extend([r[0].split("/")[-1].replace(".iff", "").replace("shared_", "") for r in c.fetchall()])
                                
                        if t == "genosian": candidates.append("geonosian")
                        if t == "cubes": candidates.append("cube")
                        if t == "tissues" or t == "tissue": candidates.append("krayt")
                                
                        matches = difflib.get_close_matches(t, candidates, n=1, cutoff=0.5)
                        if matches:
                            corrected_tokens.append(matches[0])
                            context += f"(Note: Searching for '{matches[0]}' instead of '{t}')\n"
                            if hasattr(self.app, "learned_typos"):
                                self.app.learned_typos[t] = matches[0]
                                self.app.save_learned_typos()
                        else: corrected_tokens.append(t)
                    else: corrected_tokens.append(t)
                
                if any(x in corrected_tokens for x in ["tissue", "tissues"]) and "krayt" not in corrected_tokens:
                    corrected_tokens.append("krayt")
                if any(x in corrected_tokens for x in ["blood"]) and "janta" not in corrected_tokens and "janta" in user_input.lower():
                    corrected_tokens.append("janta")

                # 1. Check Mobiles & Spawns
                mob_where = " AND ".join(["(m.mobile_template LIKE ? OR m.custom_name LIKE ? OR s.poi_name LIKE ?)" for _ in corrected_tokens])
                mob_params = []
                for ct in corrected_tokens: mob_params.extend([f"%{ct}%", f"%{ct}%", f"%{ct}%"])
                        
                c.execute(f"""
                    SELECT m.mobile_template, s.planet, s.x, s.y, m.custom_name, s.respawn_timer, s.poi_name,
                           m.health_min, m.health_max, m.armor_rating, m.kinetic, m.energy, m.blast, m.stun,
                           m.lightsaber, m.heat, m.cold, m.acid, m.electricity
                    FROM mobiles m 
                    LEFT JOIN spawns s ON (m.mobile_template = s.mobile_template OR s.mobile_template LIKE '%' || m.mobile_template || '%')
                    WHERE {mob_where} LIMIT 8
                """, tuple(mob_params))
                mobs = c.fetchall()
                if not mobs and len(corrected_tokens) > 1:
                    mob_where_or = " OR ".join(["(m.mobile_template LIKE ? OR m.custom_name LIKE ? OR s.poi_name LIKE ?)" for _ in corrected_tokens])
                    c.execute(f"""
                        SELECT m.mobile_template, s.planet, s.x, s.y, m.custom_name, s.respawn_timer, s.poi_name,
                               m.health_min, m.health_max, m.armor_rating, m.kinetic, m.energy, m.blast, m.stun,
                               m.lightsaber, m.heat, m.cold, m.acid, m.electricity
                        FROM mobiles m 
                        LEFT JOIN spawns s ON (m.mobile_template = s.mobile_template OR s.mobile_template LIKE '%' || m.mobile_template || '%')
                        WHERE {mob_where_or} ORDER BY (m.mobile_template LIKE ? OR m.custom_name LIKE ? OR s.poi_name LIKE ?) DESC LIMIT 5
                    """, tuple(mob_params + [f"%{corrected_tokens[0]}%", f"%{corrected_tokens[0]}%", f"%{corrected_tokens[0]}%"]))
                    mobs = c.fetchall()

                if mobs:
                    context += "IMPERIAL ARCHIVE - ENTITIES & LOCATIONS:\n"
                    for m in mobs:
                        m_name = m[4] if m[4] else m[0]
                        loc = f" on {m[1]}" if m[1] else " (Location unknown)"
                        if m[6]: loc = f" in {m[6]}" + loc 
                        if m[2] and m[3] and (m[2] != 0 or m[3] != 0): loc += f" (at {m[2]}, {m[3]})"
                        specs = f"HP: {m[7]}-{m[8]} | Armor: {m[9]}"
                        resists = []
                        res_names = ["Kinetic", "Energy", "Blast", "Stun", "LS", "Heat", "Cold", "Acid", "Elec"]
                        for i, r_val in enumerate(m[10:19]):
                            if r_val != 0: resists.append(f"{res_names[i]}: {r_val}%")
                        res_str = f" | Res: {', '.join(resists)}" if resists else ""
                        timer = f" [Respawn: {m[5]}s]" if m[5] else ""
                        context += f"- {m_name} ({m[0]}){loc}{timer}\n  (Tactical: {specs}{res_str})\n"
                        c.execute("""
                            SELECT DISTINCT li.item_template FROM mobile_loot ml
                            JOIN loot_items li ON ml.group_id = li.group_id
                            WHERE ml.mobile_id = (SELECT id FROM mobiles WHERE mobile_template = ?) LIMIT 5
                        """, (m[0],))
                        mob_drops = c.fetchall()
                        if mob_drops:
                            drop_list = ", ".join([d[0].split("/")[-1].replace(".iff", "").replace("shared_", "") for d in mob_drops])
                            context += f"  (Drops: {drop_list})\n"
                            
                        # NEW: Check for detailed stats if this mobile has item stats (for bosses/specific templates)
                        c.execute("SELECT template, name, damage_min, damage_max, speed, armor_piercing, damage_type, armor_rating, effectiveness, kinetic, energy, blast, stun, heat, cold, acid, electricity FROM item_stats WHERE template = ? OR template LIKE '%' || ? || '%' OR name = ? OR name LIKE '%' || ? || '%'", (m[0], m[0], m[0], m[0]))
                        istat = c.fetchone()
                        if istat:
                            # 0:template, 1:name, 2:damage_min, 3:damage_max, 4:speed, 5:armor_piercing, 6:damage_type, 
                            # 7:armor_rating, 8:effectiveness, 
                            # 9:kinetic, 10:energy, 11:blast, 12:stun, 13:heat, 14:cold, 15:acid, 16:electricity
                            stat_str = f"Name: {istat[1]} | Dmg: {istat[2]}-{istat[3]} | Speed: {istat[4]} | AP: {istat[5]} | DmgType: {istat[6]}"
                            if istat[7] and istat[7] != "None": # Armor
                                res_list = []
                                r_names = ["Kin", "Ene", "Bla", "Stu", "Hea", "Col", "Aci", "Ele"]
                                for i, r_val in enumerate(istat[9:17]):
                                    if r_val and r_val > 0: res_list.append(f"{r_names[i]}: {r_val}%")
                                stat_str += f" | Armor Rating: {istat[7]} | Eff: {istat[8]}% | {', '.join(res_list)}"
                            context += f"  (Archive Stat: {stat_str})\n"
                        
                # 2. Recursive Loot Sources
                loot_where = " AND ".join(["lt.item_template LIKE ?" for _ in corrected_tokens])
                base_where = " OR ".join(["item_template LIKE ?" for _ in corrected_tokens])
                base_params = [f"%{ct}%" for ct in corrected_tokens]
                loot_params = [f"%{ct}%" for ct in corrected_tokens]
                c.execute(f"""
                    WITH RECURSIVE
                    loot_tree(group_id, item_template) AS (
                        SELECT group_id, item_template FROM loot_items WHERE {base_where}
                        UNION
                        SELECT li.group_id, lt.item_template FROM loot_items li
                        JOIN loot_tree lt ON li.item_template = 'group:' || (SELECT group_name FROM loot_groups WHERE id = lt.group_id)
                    )
                    SELECT DISTINCT lt.item_template, m.mobile_template, s.planet, m.custom_name
                    FROM loot_tree lt
                    JOIN mobile_loot ml ON lt.group_id = ml.group_id
                    JOIN mobiles m ON ml.mobile_id = m.id
                    LEFT JOIN spawns s ON (m.mobile_template = s.mobile_template OR s.mobile_template LIKE '%' || m.mobile_template || '%')
                    WHERE {loot_where} LIMIT 15
                """, tuple(base_params + loot_params))
                loot_sources = c.fetchall()
                if not loot_sources and len(corrected_tokens) > 1:
                    c.execute(f"""
                        WITH RECURSIVE
                        loot_tree(group_id, item_template) AS (
                            SELECT group_id, item_template FROM loot_items WHERE {base_where}
                            UNION
                            SELECT li.group_id, lt.item_template FROM loot_items li
                            JOIN loot_tree lt ON li.item_template = 'group:' || (SELECT group_name FROM loot_groups WHERE id = lt.group_id)
                        )
                        SELECT DISTINCT lt.item_template, m.mobile_template, s.planet, m.custom_name
                        FROM loot_tree lt
                        JOIN mobile_loot ml ON lt.group_id = ml.group_id
                        JOIN mobiles m ON ml.mobile_id = m.id
                        LEFT JOIN spawns s ON (m.mobile_template = s.mobile_template OR s.mobile_template LIKE '%' || m.mobile_template || '%')
                        ORDER BY (lt.item_template LIKE ?) DESC LIMIT 10
                    """, tuple(base_params + [f"%{corrected_tokens[0]}%"]))
                    loot_sources = c.fetchall()

                if loot_sources:
                    context += "IMPERIAL ARCHIVE - LOOT SOURCES:\n"
                    for ls in loot_sources:
                        m_name = ls[3] if ls[3] else ls[1]
                        loc = f" on {ls[2]}" if ls[2] else ""
                        context += f"- {ls[0]} carried by {m_name}{loc}\n"
                        
                        # NEW: Enrichment with item_stats
                        c.execute("SELECT template, name, damage_min, damage_max, speed, armor_piercing, armor_rating, effectiveness FROM item_stats WHERE template = ? OR template LIKE '%' || ? || '%' OR name = ? OR name LIKE '%' || ? || '%'", (ls[0], ls[0], ls[0], ls[0]))
                        istat = c.fetchone()
                        if istat:
                            # 0:template, 1:name, 2:damage_min, 3:damage_max, 4:speed, 5:armor_piercing, 6:armor_rating, 7:effectiveness
                            stat_str = f"Dmg: {istat[2]}-{istat[3]} | Speed: {istat[4]} | AP: {istat[5]}"
                            if istat[6] and istat[6] != "None":
                                stat_str = f"Armor: {istat[6]} | Eff: {istat[7]}%"
                            context += f"  (Archive Stat: {stat_str})\n"
            except Exception as e:
                print(f"Async RAG context error: {e}")
        
        self._process_pseudo_ai(user_input, context, callback)

    def _process_pseudo_ai(self, user_input, context_data, callback):
        if callback:
            # Immersive filler: while "searching the archives", Rico shares some nostalgia
            if not any(word in user_input.lower() for word in ["metallica", "song", "music", "riff", "guitar", "tab", "play"]):
                filler = self._get_personality_filler()
                callback(f"Wait a sec... {filler}\n[STILL SEARCHING...]")
                time.sleep(0.5) # Artificial pause for "searching" effect

        answer = self._generate_response(user_input, context_data)
        
        if callback:
            callback(answer)

    def _get_personality_filler(self):
        # Choose between a book quote, a Metallica bit, or a Rico-ism
        choice = random.random()
        if choice < 0.35: # 35% chance of a book
            try:
                if self.app and hasattr(self.app, "rico_db") and self.app.rico_db:
                    c = self.app.rico_db.cursor()
                    c.execute("SELECT content_sample FROM literary_archives ORDER BY RANDOM() LIMIT 1")
                    res = c.fetchone()
                    if res:
                        # Use book content as a language enhancer/filler
                        quote = res[0][:200].strip()
                        return f"You know, I read this once in one of my 3,000 books: '{quote}...' It's heavy, right? Reminds me of the weight of expectations in '82."
            except: pass
        elif choice < 0.7: # 35% chance of Metallica
            try:
                from metallica import metallica_dataset
                song = random.choice(metallica_dataset)
                trivia = song['trivia']
                if len(trivia) > 200: trivia = trivia[:200] + "..."
                return f"I was just thinking about that Metallica song '{song['song_title']}'. {trivia} I bet Lars and James would've loved my arm back in '82."
            except: pass
        
        return random.choice(self.rico_quotes)

    def _generate_response(self, user_input, context_data):
        user_input_lower = user_input.lower().strip()
        
        # 0. Check for Combat Math queries (PvP Calculator)
        if any(word in user_input_lower for word in ["damage", "calculate", "how much", "against", "mit3", "armor", "psg"]):
            calc_response = self._handle_combat_math(user_input_lower)
            if calc_response: return calc_response

        # 1. Check for Metallica/Music queries
        if any(word in user_input_lower for word in ["metallica", "song", "music", "riff", "guitar", "tab", "play"]):
            return self._handle_music_query(user_input_lower)

        # 2. Check for Schematic/Crafting queries
        if any(word in user_input_lower for word in ["how many", "craft", "schematic", "take", "need", "ingredient", "for", "make", "recipe", "build"]):
            craft_response = self._handle_crafting_query(user_input_lower)
            if craft_response: return craft_response

        # 3. Check learned permanent drops
        learned_context = ""
        if self.app and hasattr(self.app, "permanent_drops"):
            matches = []
            for item, mobs in self.app.permanent_drops.items():
                # Fuzzy match for learned items
                item_clean = item.lower().replace("_", " ")
                if item_clean in user_input_lower or user_input_lower in item_clean:
                    matches.append(f"- {item} is known to be carried by {', '.join(mobs)}")
            if matches:
                learned_context = "IMPERIAL ARCHIVE - RECENTLY LEARNED INTEL:\n" + "\n".join(matches) + "\n"

        # 4. Use Context Data from Alexa (RAG) if available
        if (context_data and "IMPERIAL ARCHIVE" in context_data) or learned_context:
            combined_context = (context_data or "") + "\n" + learned_context
            # IMPROVED: If we have direct loot sources, prioritize them
            if "LOOT SOURCES" in combined_context:
                 return self._format_rico_response(user_input, combined_context, prioritize_loot=True)
            return self._format_rico_response(user_input, combined_context)

        # 5. Direct DB check for Mobiles if context_data was empty (Extra safety)
        if self.app and hasattr(self.app, "rico_db") and self.app.rico_db:
            try:
                c = self.app.rico_db.cursor()
                search = f"%{user_input_lower.replace(' ', '%')}%"
                c.execute("SELECT mobile_template, custom_name FROM mobiles WHERE mobile_template LIKE ? OR custom_name LIKE ? LIMIT 3", (search, search))
                mobs = c.fetchall()
                if mobs:
                    mob_list = ", ".join([m[1] if m[1] else m[0] for m in mobs])
                    return f"Listen, I found some chatter about {mob_list} in the archives. I bet I could take 'em down with one arm if Coach put me in. What specifically do you need to know about them?"
            except: pass

        # 6. Fallback to general Rico banter
        quote = random.choice(self.rico_quotes)
        return f"Listen, I'm thinking about '82 right now, but about your '{user_input}'... {quote} Maybe if you asked about something I can find in my archives, like a Janta or a DXR6, I could help you more."

    def _handle_combat_math(self, query):
        try:
            # Normalize '1k' to '1000'
            query = query.replace("1k", "1000").replace("2k", "2000").replace("3k", "3000")
            
            dmg_match = re.findall(r'(\d+)[\s\-]*min|(\d+)[\s\-]*max', query)
            min_dmg, max_dmg = 0, 0
            
            if not dmg_match:
                dmg_range = re.findall(r'(\d+)[\s]*[\-][\s]*(\d+)', query)
                if dmg_range:
                    min_dmg, max_dmg = int(dmg_range[0][0]), int(dmg_range[0][1])
                else:
                    nums = re.findall(r'\d+', query)
                    if len(nums) >= 2:
                        min_dmg, max_dmg = int(nums[0]), int(nums[1])
                    else:
                        return None
            else:
                min_dmg_list = [m[0] for m in dmg_match if m[0]]
                max_dmg_list = [m[1] for m in dmg_match if m[1]]
                min_dmg = int(min_dmg_list[0]) if min_dmg_list else 0
                max_dmg = int(max_dmg_list[0]) if max_dmg_list else 0

            # 2. Extract Defense stats
            armor = 0
            armor_match = re.search(r'(\d+)[\s]*armor', query)
            if armor_match: armor = int(armor_match.group(1))
            elif "90base" in query: armor = 90

            mit = 0
            if "mit3" in query: mit = 60
            elif "mit2" in query: mit = 40
            elif "mit1" in query: mit = 20
            else:
                mit_match = re.search(r'(\d+)[\s]*mit', query)
                if mit_match: mit = int(mit_match.group(1))

            psg = 0
            psg_match = re.search(r'(\d+)[\s]*psg', query)
            if psg_match: psg = int(psg_match.group(1))

            # 3. Weapons Database Cross-Ref for Damage Type
            dmg_type = "Energy" # Default
            if "dxr6" in query or "carbine" in query: dmg_type = "Energy"
            elif "scatter" in query or "pistol" in query: dmg_type = "Kinetic"
            elif "acid" in query: dmg_type = "Acid"
            elif "stun" in query: dmg_type = "Stun"
            elif "blast" in query: dmg_type = "Blast"
            elif "heat" in query: dmg_type = "Heat"
            elif "cold" in query: dmg_type = "Cold"
            elif "elec" in query: dmg_type = "Electricity"
            elif "ls" in query or "lightsaber" in query: dmg_type = "Lightsaber"

            psg_applies = dmg_type in ["Energy", "Kinetic", "Blast"]
            
            def swg_calc(base):
                # 1. Base Armor %
                res = base * (1.0 - (armor / 100.0))
                # 2. PSG % (if applicable)
                if psg_applies:
                    if psg > 0:
                        res = res * (1.0 - (psg / 100.0))
                    elif "psg" not in query:
                        return "PROMPT_PSG"
                # 3. Mitigation %
                res = res * (1.0 - (mit / 100.0))
                return int(res)

            res_min = swg_calc(min_dmg)
            if res_min == "PROMPT_PSG":
                return f"Listen, regarding that {dmg_type} damage from your DXR-6... Are they wearing a Personal Shield Generator (PSG)? I need the % protection and if it's active. Most PSGs back in '82 were top-tier. Give me the PSG % and I'll give you the real numbers."

            res_max = swg_calc(max_dmg)
            
            rico_intro = f"Alright, let's look at the tape. Your {dmg_type} weapon hitting for {min_dmg}-{max_dmg} against a target with {armor}% armor and Mit-{mit/20:.0f}..."
            breakdown = f"\n• Base Armor ({armor}%): Massive reduction"
            if psg > 0: breakdown += f"\n• PSG ({psg}%): Shielding applied"
            breakdown += f"\n• Mitigation ({mit}%): Final layer"
            
            result_text = f"Final Damage: {res_min} - {res_max}"
            rico_outro = f"\n\nBack in '82, I didn't need a PSG. I just outran the blaster bolts. If Coach had put me in, I'd be hitting for twice that. No doubt. No doubt in my mind."
            
            return f"{rico_intro}{breakdown}\n\n{result_text}{rico_outro}"

        except: return None

    def _handle_music_query(self, query):
        try:
            from metallica import metallica_dataset
            song = random.choice(metallica_dataset)
            
            rico_intro = f"Music? Man, I used to blast this in my van back in '82. "
            answer = f"{rico_intro}{song['trivia']}"
            
            # Sync metadata
            sync_data = {
                "title": song["song_title"],
                "trivia": song["trivia"],
                "tab": song["main_riff_tab"]["notation"]
            }
            return answer + f"\n---METALLICA_SYNC---\n{json.dumps(sync_data)}"
        except Exception as e:
            return f"[LOCAL] I tried to find my tapes, but they're lost in the van. {random.choice(self.rico_quotes)}"

    def _handle_crafting_query(self, query):
        if not self.app or not hasattr(self.app, "rico_db") or not self.app.rico_db:
            return None

        try:
            c = self.app.rico_db.cursor()
            c.execute("SELECT id, name FROM schematics")
            all_schems = c.fetchall()
            
            target_schem = None
            clean_query = re.sub(r'[^\w\s]', '', query)
            words_in_query = set(clean_query.split())

            # Specific shorthand overrides
            shorthand = {
                "t21": "t-21 rifle",
                "t-21": "t-21 rifle",
                "dxr6": "dxr6 carbine",
                "fwg5": "fwg5 pistol"
            }
            search_query = shorthand.get(clean_query, clean_query)

            for s_id, s_name in all_schems:
                s_name_lower = s_name.lower()
                # Exact match or space-replaced match
                if s_name_lower == search_query or s_name_lower.replace("_", " ") == search_query:
                    target_schem = (s_id, s_name)
                    break
                
            if not target_schem:
                for s_id, s_name in all_schems:
                    s_name_lower = s_name.lower()
                    if s_name_lower in search_query or (s_name_lower.replace("_", " ") in search_query):
                        target_schem = (s_id, s_name)
                        break
            
            if not target_schem:
                for s_id, s_name in all_schems:
                    s_name_lower = s_name.lower()
                    # Multi-word fuzzy match
                    s_words = set(s_name_lower.split("_"))
                    if s_words.intersection(words_in_query) and len(s_words.intersection(words_in_query)) >= min(2, len(s_words)):
                        target_schem = (s_id, s_name)
                        break
            
            if not target_schem:
                # Last ditch check for short names (e.g., 't21')
                for s_id, s_name in all_schems:
                    s_name_lower = s_name.lower()
                    if any(len(w) > 2 and w in query for w in s_name_lower.split("_")):
                        target_schem = (s_id, s_name)
                        break

            if target_schem:
                s_id, s_name = target_schem
                
                def get_ingredients_recursive(schem_id, depth=0):
                    if depth > 2: return [] # Prevent infinite loops
                    
                    try:
                        c2 = self.app.rico_db.cursor()
                        c2.execute("SELECT component_name, quantity FROM ingredients WHERE schematic_id = ?", (schem_id,))
                        ingreds = c2.fetchall()
                        
                        full_list = []
                        for row in ingreds:
                            name, qty = row[0], row[1]
                            clean_comp_name = name
                            if "(" in name:
                                template_path = name.split("(")[-1].strip(")")
                                clean_comp_name = template_path.split("/")[-1].replace(".iff", "").replace("shared_", "")
                            
                            c2.execute("SELECT id, name FROM schematics WHERE template LIKE ? OR name = ? OR name LIKE ?", 
                                     (f"%{clean_comp_name}%", clean_comp_name, f"%{clean_comp_name.replace('_', ' ')}%"))
                            res_sub = c2.fetchone()
                            
                            if res_sub:
                                sub_id, sub_display_name = res_sub[0], res_sub[1]
                                sub_ingreds = get_ingredients_recursive(sub_id, depth + 1)
                                if sub_ingreds:
                                    sub_str = ", ".join(sub_ingreds)
                                    full_list.append(f"{qty} {name} \n    - Requires: {sub_str}")
                                else:
                                    full_list.append(f"{qty} {name}")
                            else:
                                full_list.append(f"{qty} {name}")
                        return full_list
                    except Exception as e:
                        print(f"Recursion error: {e}")
                        return []

                detailed_ingreds = get_ingredients_recursive(s_id)
                
                if detailed_ingreds:
                    ingred_list = "\n- ".join(detailed_ingreds)
                    rico_comment = "Back in '82, I could've built this with one hand tied behind my back while eating a steak."
                    
                    filler = self._get_personality_filler()
                    return f"--- CRAFTING SPEC: {s_name.upper()} ---\n\nIt takes:\n- {ingred_list}\n\n{rico_comment}\n\n{filler}"
        except Exception as e:
            print(f"Crafting query error: {e}")
            pass
        return None

    def _format_rico_response(self, user_input, context, prioritize_loot=False):
        lines = context.split("\n")
        intel = []
        loot_sources = []
        schematics = []
        notes = []
        
        current_section = ""
        for line in lines:
            if "ENTITIES & LOCATIONS" in line: current_section = "entities"
            elif "LOOT SOURCES" in line: current_section = "loot"
            elif "SCHEMATICS" in line: current_section = "schems"
            
            if line.startswith("(Note:"):
                notes.append(line.strip())
            elif line.startswith("- "):
                item = line[2:]
                if " carried by " in item:
                    item = item.replace("object/mobile/shared_", "").replace(".iff", "").replace("_", " ")
                    loot_sources.append(item)
                elif "(takes: " in item:
                    schematics.append(item)
                else:
                    item = item.replace("group:", "")
                    intel.append(item)
            elif line.startswith("  (Drops: "):
                if intel:
                    intel[-1] += f" {line.strip()}"
            elif line.startswith("  (Tactical: "):
                if intel:
                    intel[-1] += f" {line.strip()}"
            elif line.startswith("  (Archive Stat: "):
                if intel:
                    intel[-1] += f" {line.strip()}"
                elif loot_sources:
                    loot_sources[-1] += f" {line.strip()}"
            elif "carried by" in line and "is known to be" not in line:
                 loot_sources.append(line.strip())
        
        if not intel and not loot_sources and not schematics:
            if notes:
                filler = self._get_personality_filler()
                return f"Listen, I tried searching for those {user_input}... I even checked for '{notes[0].split(chr(39))[1]}' instead, but it's like that time in '82 when the scout missed my 70-yard pass. Not found.\n\n{filler}"
            
            # Use a more natural filler here too
            filler = self._get_personality_filler()
            return f"I looked in the archives for '{user_input}', but it's like that time in '82 when the scout missed my 70-yard pass. Not found. \n\n{filler}"

        unique_intel = []
        for i in intel:
            if i not in unique_intel: unique_intel.append(i)
            
        unique_loot = []
        for l in loot_sources:
            if l not in unique_loot: unique_loot.append(l)

        combined_intel = []
        if notes:
            combined_intel.append(f"Archives Note: {notes[0]}")
            combined_intel.append("")
        
        if prioritize_loot and unique_loot:
            combined_intel.append("--- LOOT INTEL ---")
            combined_intel.extend([f"• {i}" for i in unique_loot[:10]])
            if unique_intel:
                combined_intel.append("")
                combined_intel.append("--- MOB LOCATIONS & SPECS ---")
                combined_intel.extend([f"• {i}" for i in unique_intel[:5]])
        else:
            if unique_intel:
                combined_intel.append("--- TACTICAL INTEL & SPECS ---")
                combined_intel.extend([f"• {i}" for i in unique_intel[:8]])
            if unique_loot:
                if combined_intel: combined_intel.append("")
                combined_intel.append("--- LOOT INTEL ---")
                combined_intel.extend([f"• {i}" for i in unique_loot[:8]])
        
        if schematics:
            if combined_intel: combined_intel.append("")
            combined_intel.append("--- CRAFTING SPECS ---")
            combined_intel.extend([f"• {s}" for s in schematics[:3]])

        main_intel = "\n".join(combined_intel)
        
        # Make the prefix more varied
        prefixes = [
            f"Listen, regarding {user_input}... I checked the Imperial Archives.",
            f"I did a quick scan of the archives for '{user_input}'.",
            f"Regarding your query about '{user_input}'... here's what the Archives have.",
            f"I pulled up the file on '{user_input}' from the Archives. Back in '82 I would've had this memorized.",
            f"Archival records for '{user_input}' are now clear. Check this out:"
        ]
        rico_prefix = random.choice(prefixes)
        
        # Use more natural personality filler for the suffix
        rico_suffix = f"\n\n{self._get_personality_filler()}"
        
        # Randomly inject a Metallica riff/trivia once in a while (15% chance)
        riff_injection = ""
        if random.random() < 0.15:
            try:
                from metallica import metallica_dataset
                song = random.choice(metallica_dataset)
                riff_injection = f"\n\nSpeaking of heavy hits, check out this riff from '{song['song_title']}':\n{song['main_riff_tab']['notation']}\n{song['trivia'][:120]}..."
            except: pass

        return f"{rico_prefix}\n\n{main_intel}\n{rico_suffix}{riff_injection}"
