import datetime
import html as html_utils
import json
import random
import os

class MockTracker:
    def __init__(self):
        random.seed(42)

        friendly_names = [
            "Medico", "Vex", "Ryn", "Daro", "Kira", "Nox", "Tallis", "Brigg", "Echo", "Aeris"
        ]
        enemy_names = [
            "IiIiIiIi", "Stormtrooper", "Bounty Hunter", "Rancor", "Nightblade", "Skorn", "Rivet", "Krell", "Mako", "Zyra"
        ]

        self.history = {}
        self.player_alignment = {}

        for name in friendly_names:
            self.player_alignment[name] = "friendly"
        for name in enemy_names:
            self.player_alignment[name] = "enemy"

        all_names = friendly_names + enemy_names
        ability_map = {
            "KD": ["Killing Blow", "Heavy Slam", "Smash"],
            "PD": ["Point Blank Shot", "Quick Burst", "Impact Round"],
            "INT": ["Intimidate", "Disrupt", "Pressure"],
            "INC": ["Incapacitate", "Crippling Hit", "Shock Down"],
            "LOOT": ["Credits", "Composite Segment", "Weapon Parts"],
            "KILL": ["Final Strike", "Execution", "Finisher"],
            "DEATH": ["Defeated", "Collapsed", "Eliminated"],
        }

        encounter_time = 165
        event_types = ["KD", "PD", "INT", "INC", "LOOT", "KILL", "DEATH"]

        for idx, name in enumerate(all_names):
            pulses = []
            events = []
            cumulative_damage = 0
            cumulative_heal = 0

            lane_targets = enemy_names if self.player_alignment[name] == "friendly" else friendly_names

            for _ in range(18):
                t = random.randint(4, encounter_time)
                target = random.choice(lane_targets)

                if self.player_alignment[name] == "friendly":
                    dmg = random.randint(900, 6800)
                    heal = random.randint(0, 2600) if idx % 3 == 0 else random.randint(0, 600)
                else:
                    dmg = random.randint(700, 5400)
                    heal = random.randint(0, 1000) if idx % 4 == 0 else random.randint(0, 300)

                pulses.append((t, dmg, heal, target))
                cumulative_damage += dmg
                cumulative_heal += heal

            pulses.sort(key=lambda x: x[0])

            totals = []
            if pulses:
                step = max(1, len(pulses) // 3)
                running_dmg = 0
                running_heal = 0
                for j, (t, dmg, heal, _) in enumerate(pulses):
                    running_dmg += dmg
                    running_heal += heal
                    if (j + 1) % step == 0 or j == len(pulses) - 1:
                        totals.append((t, running_dmg, running_heal))

            for _ in range(6):
                t = random.randint(6, encounter_time)
                etype = random.choice(event_types)
                target = random.choice(lane_targets)
                label = random.choice(ability_map[etype])
                src = name
                tgt = target

                if etype == "DEATH":
                    src, tgt = target, name

                events.append((t, etype, src, tgt, label))

            events.sort(key=lambda x: x[0])
            self.history[name] = {"pulses": pulses, "totals": totals, "events": events}

    def generate_html_report(self):
        # Generate an interactive HTML report using Tailwind CSS and DaisyUI
        players = list(self.history.keys())
        max_time = 0
        all_pulses = [] # Collect all pulses for lookup
        for name, data in self.history.items():
            for t, d, h in data.get("totals", []): max_time = max(max_time, t)
            for t, etype, src, tgt, label in data["events"]: max_time = max(max_time, t)
            for p in data.get("pulses", []):
                all_pulses.append((p[0], name, p[1], p[2], p[3])) # t, name, dmg, heal, tgt
        if max_time == 0: max_time = 1
        
        all_pulses.sort(key=lambda x: x[0]) # Sort by time

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
                .swimlane-container {{ position: relative; min-width: 2100px; padding-top: 80px; }}
                .event-marker {{ position: absolute; transform: translateX(-50%); transition: all 0.2s; z-index: 90; }}
                .event-marker:hover {{ transform: translateX(-50%) scale(1.2); z-index: 150; }}
                .time-line {{ position: absolute; top: 0; bottom: 0; border-left: 1px solid rgba(0, 236, 255, 0.1); pointer-events: none; }}
                .mini-log {{ max-height: 160px; overflow-y: auto; scrollbar-width: thin; }}
                .mini-log::-webkit-scrollbar {{ width: 4px; }}
                .mini-log::-webkit-scrollbar-thumb {{ background: var(--starwars-blue); border-radius: 2px; }}
                .hud-border {{ border: 1px solid rgba(0, 236, 255, 0.2); box-shadow: 0 0 15px rgba(0, 236, 255, 0.1); }}
                .scanline {{ width: 100%; height: 100px; z-index: 5; background: linear-gradient(0deg, rgba(0, 236, 255, 0) 0%, rgba(0, 236, 255, 0.02) 50%, rgba(0, 236, 255, 0) 100%); position: absolute; animation: scan 8s linear infinite; pointer-events: none; }}
                @keyframes scan {{ from {{ top: -100px; }} to {{ top: 100%; }} }}
                .glow-text-blue {{ text-shadow: 0 0 10px rgba(0, 236, 255, 0.5); }}
                .glow-text-red {{ text-shadow: 0 0 10px rgba(255, 0, 60, 0.5); }}
                .player-row {{ transition: background 0.3s; z-index: 10; }}
                .player-row:hover {{ background: rgba(0, 236, 255, 0.05); z-index: 120; }}
                .sparkline {{ pointer-events: none; width: 100%; height: 100%; display: block; z-index: 10; opacity: 0.6; }}
                .graph-hover-layer {{ position: absolute; inset: 0; z-index: 40; cursor: default; }}
                .graph-crosshair {{ position: absolute; top: 0; bottom: 0; width: 1px; background: rgba(255, 255, 255, 0.35); pointer-events: none; }}
                .graph-tooltip {{ position: absolute; top: calc(100% + 8px); transform: translateX(-50%); pointer-events: none; z-index: 500; }}
                .event-detail-overlay {{ position: fixed; inset: 0; background: rgba(1, 6, 12, 0.52); z-index: 900; display: none; }}
                .event-detail-overlay.open {{ display: block; }}
                .event-detail-panel {{ position: fixed; left: 20px; top: 20px; width: min(460px, calc(100vw - 40px)); max-height: min(76vh, 700px); overflow: auto; z-index: 901; display: none; }}
                .event-detail-panel.open {{ display: block; }}
            </style>
        </head>
        <body class="min-h-screen p-4 md:p-8 text-slate-300">
            <div class="max-w-[2350px] mx-auto relative">
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
                    <div class="flex items-center gap-6 relative z-10">
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

                <!-- Main Analysis Area -->
                <div class="hud-border bg-black/40 rounded-lg p-2 overflow-x-auto overflow-y-visible relative">
                    <div class="swimlane-container" style="height: {len(players) * 180 + 140}px;">
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

        # Draw Player Lanes
        for i, name in enumerate(players):
            top = 90 + (i * 180)
            alignment = self.player_alignment.get(name, "friendly")
            if alignment == "friendly":
                row_bg = "bg-emerald-500/10 border-emerald-300/30"
                lane_label_class = "badge-success"
                lane_label = "FRIENDLY"
            else:
                row_bg = "bg-red-500/10 border-red-300/30"
                lane_label_class = "badge-error"
                lane_label = "ENEMY"
            
            # Generate Sparkline Data
            pulses = self.history[name].get("pulses", [])
            dmg_points = []
            heal_points = []
            
            max_val = 1
            for t, d, h, _ in pulses: max_val = max(max_val, d, h)
            
            # Construct SVG paths for DMG and HEAL
            dmg_path = ""
            heal_path = ""
            hover_points = ""
            if pulses:
                sorted_pulses = sorted(pulses, key=lambda x: x[0])
                hover_rows = {}
                for pt, pd, ph, ptgt in sorted_pulses:
                    row = hover_rows.setdefault(pt, {"t": pt, "d": 0, "h": 0, "d_sources": {}, "h_sources": {}})
                    row["d"] += pd
                    row["h"] += ph
                    if pd > 0:
                        row["d_sources"][ptgt] = row["d_sources"].get(ptgt, 0) + pd
                    if ph > 0:
                        row["h_sources"][ptgt] = row["h_sources"].get(ptgt, 0) + ph

                hover_payload = []
                for pt in sorted(hover_rows.keys()):
                    row = hover_rows[pt]
                    hover_payload.append({
                        "t": row["t"],
                        "d": row["d"],
                        "h": row["h"],
                        "d_sources": sorted(row["d_sources"].items(), key=lambda x: x[1], reverse=True),
                        "h_sources": sorted(row["h_sources"].items(), key=lambda x: x[1], reverse=True),
                    })
                hover_points = html_utils.escape(json.dumps(hover_payload, separators=(",", ":")), quote=True)
                
                def get_svg_points(data_type_idx):
                    pts = []
                    # Start at 0
                    pts.append(f"0,100")
                    for pt, pd, ph, ptgt in sorted_pulses:
                        val = pd if data_type_idx == 1 else ph
                        x = (pt / max_time) * 100
                        y = 100 - (val / max_val * 80) # 80% height usage
                        pts.append(f"{x},{y}")
                    pts.append(f"100,100")
                    return " ".join(pts)

                dmg_path = get_svg_points(1)
                heal_path = get_svg_points(2)
            html += f"""
                        <div class="absolute left-0 right-0 h-40 rounded border {row_bg} flex items-center px-6 backdrop-blur-sm player-row" style="top: {top}px;">
                            <div class="w-60 flex-shrink-0 border-r border-white/10 mr-8 py-2 relative z-20">
                                <span class="text-[8px] font-black opacity-30 uppercase tracking-[0.3em] mb-1 block">Entity Signature</span>
                                <span class="text-lg font-orbitron font-black text-slate-200 truncate block tracking-widest">
                                    {name.upper()}
                                </span>
                                <div class="mt-2">
                                    <span class="badge {lane_label_class} badge-xs font-black tracking-widest">{lane_label}</span>
                                </div>
                                <div class="flex gap-2 mt-2">
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-error" style="width: {min(100, sum(p[1] for p in pulses)/1000)}%"></div>
                                    </div>
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-success" style="width: {min(100, sum(p[2] for p in pulses)/1000)}%"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="relative flex-grow h-full overflow-visible pr-4">
                                <div class="h-full relative rounded border border-white/10 bg-black/20 overflow-visible">
                                    <div class="absolute left-2 top-1 text-[8px] font-black tracking-widest text-error/70">DMG</div>
                                    <div class="absolute left-12 top-1 text-[8px] font-black tracking-widest text-success/70">HEAL</div>
                                    <svg class="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
                                        <polyline fill="rgba(255, 0, 60, 0.10)" stroke="rgba(255, 0, 60, 0.55)" stroke-width="1.1" points="{dmg_path}" />
                                        <polyline fill="none" stroke="rgba(0, 255, 150, 0.80)" stroke-width="1.1" points="{heal_path}" />
                                    </svg>
                                    <div class="graph-hover-layer" data-player="{name}" data-max-time="{max_time}" data-points="{hover_points}">
                                        <div class="graph-crosshair hidden"></div>
                                        <div class="graph-tooltip hidden bg-[#0a0f14] border border-primary/40 px-3 py-2 rounded text-[9px] font-mono shadow-[0_0_30px_rgba(0,236,255,0.2)] min-w-[280px]"></div>
                                    </div>
                                </div>
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

                event_payload = html_utils.escape(json.dumps({
                    "type": etype,
                    "time": round(float(t), 1),
                    "source": src,
                    "target": tgt,
                    "label": label,
                    "mini_log_html": mini_log_html,
                    "player": name,
                }, separators=(",", ":")), quote=True)
                
                html += f"""
                                <div class="event-marker event-clickable" data-event="{event_payload}" style="left: {left}%; top: 50%; margin-top: -14px;" role="button" tabindex="0" aria-label="Open event details">
                                    <div class="badge {badge_class} badge-sm font-black shadow-[0_0_10px_rgba(0,0,0,0.5)] border-white/20 cursor-pointer hover:scale-110 transition-transform font-orbitron">
                                        {etype}
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

                <div class="mt-12 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div class="flex items-center gap-3">
                        <div class="text-[8px] font-black tracking-[0.4em] uppercase text-primary/30">Livius Analysis Engine v3.0 // Tactical Overlay</div>
                        <div class="w-1.5 h-1.5 rounded-full bg-primary/20 animate-pulse"></div>
                    </div>
                    <div class="text-[8px] font-mono font-bold tracking-widest uppercase opacity-20">Cycle Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
            <div class="event-detail-overlay" id="eventDetailOverlay"></div>
            <div class="event-detail-panel hud-border bg-[#0a0f14] rounded-lg p-4 shadow-[0_0_45px_rgba(0,236,255,0.22)]" id="eventDetailPanel">
                <div class="flex justify-between items-center mb-3 border-b border-primary/20 pb-2">
                    <div>
                        <div class="text-[9px] font-black text-primary tracking-[0.22em] uppercase" id="eventDetailType">Event</div>
                        <div class="text-[8px] opacity-60" id="eventDetailMeta">Tactical Breakdown</div>
                    </div>
                    <button class="btn btn-xs btn-ghost" id="eventDetailClose" type="button">Close</button>
                </div>
                <div class="grid grid-cols-2 gap-3 mb-3 text-[10px]">
                    <div class="bg-black/40 p-2 rounded border border-white/5">
                        <div class="text-[8px] opacity-35 uppercase tracking-widest mb-1">Source</div>
                        <div class="font-bold text-primary break-all" id="eventDetailSource">-</div>
                    </div>
                    <div class="bg-black/40 p-2 rounded border border-white/5">
                        <div class="text-[8px] opacity-35 uppercase tracking-widest mb-1">Target</div>
                        <div class="font-bold text-secondary break-all" id="eventDetailTarget">-</div>
                    </div>
                </div>
                <div class="bg-primary/5 p-3 rounded mb-3 text-[10px] border-l-2 border-primary/40 tracking-tight italic opacity-85" id="eventDetailLabel">-</div>
                <div>
                    <div class="flex justify-between items-center mb-2 px-1">
                        <span class="text-[8px] font-black text-primary/60 uppercase tracking-[0.2em]">High-Res Telemetry</span>
                        <span class="text-[8px] opacity-35">-2.0s / +1.0s</span>
                    </div>
                    <div class="mini-log bg-black/60 rounded p-2 border border-white/5" id="eventDetailLog"></div>
                </div>
            </div>
            <script>
                (() => {{
                    const layers = document.querySelectorAll('.graph-hover-layer');
                    const eventMarkers = document.querySelectorAll('.event-clickable');
                    const eventDetailOverlay = document.getElementById('eventDetailOverlay');
                    const eventDetailPanel = document.getElementById('eventDetailPanel');
                    const eventDetailType = document.getElementById('eventDetailType');
                    const eventDetailMeta = document.getElementById('eventDetailMeta');
                    const eventDetailSource = document.getElementById('eventDetailSource');
                    const eventDetailTarget = document.getElementById('eventDetailTarget');
                    const eventDetailLabel = document.getElementById('eventDetailLabel');
                    const eventDetailLog = document.getElementById('eventDetailLog');
                    const eventDetailClose = document.getElementById('eventDetailClose');

                    const parsePoints = (raw) => {{
                        if (!raw) return [];
                        try {{
                            const parsed = JSON.parse(raw);
                            return Array.isArray(parsed)
                                ? parsed.filter((p) => Number.isFinite(p.t)).sort((a, b) => a.t - b.t)
                                : [];
                        }} catch (_) {{
                            return [];
                        }}
                    }};

                    layers.forEach((layer) => {{
                        const points = parsePoints(layer.dataset.points || '');
                        const maxTime = Number(layer.dataset.maxTime || '1');
                        const crosshair = layer.querySelector('.graph-crosshair');
                        const tooltip = layer.querySelector('.graph-tooltip');
                        const player = layer.dataset.player || 'Unknown';

                        const findNearest = (timeAtCursor) => {{
                            if (!points.length) return {{ t: timeAtCursor, d: 0, h: 0, d_sources: [], h_sources: [] }};
                            let nearest = points[0];
                            let bestDelta = Math.abs(points[0].t - timeAtCursor);
                            for (let i = 1; i < points.length; i += 1) {{
                                const delta = Math.abs(points[i].t - timeAtCursor);
                                if (delta < bestDelta) {{
                                    bestDelta = delta;
                                    nearest = points[i];
                                }}
                            }}
                            return nearest;
                        }};

                        const renderSources = (sources, cssClass, label) => {{
                            if (!Array.isArray(sources) || !sources.length) {{
                                return `<div class="${{cssClass}}/80">${{label}} Sources: none</div>`;
                            }}
                            const top = sources.slice(0, 3)
                                .map(([who, amount]) => `<span class="font-bold">${{who}}</span> ${{Number(amount || 0).toLocaleString()}}`)
                                .join(' • ');
                            return `<div class="${{cssClass}}">${{label}} Sources: ${{top}}</div>`;
                        }};

                        layer.addEventListener('mousemove', (event) => {{
                            const rect = layer.getBoundingClientRect();
                            const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
                            const ratio = rect.width > 0 ? x / rect.width : 0;
                            const timeAtCursor = ratio * maxTime;
                            const sample = findNearest(timeAtCursor);

                            crosshair.classList.remove('hidden');
                            tooltip.classList.remove('hidden');
                            crosshair.style.left = `${{x}}px`;

                            tooltip.style.left = `${{x}}px`;
                            const boxWidth = tooltip.offsetWidth || 220;
                            if (x < 100) {{
                                tooltip.style.transform = 'translateX(0)';
                            }} else if (x > rect.width - 100) {{
                                tooltip.style.transform = `translateX(-${{boxWidth}}px)`;
                            }} else {{
                                tooltip.style.transform = 'translateX(-50%)';
                            }}

                            const dmgSources = renderSources(sample.d_sources, 'text-error', 'DMG');
                            const healSources = renderSources(sample.h_sources, 'text-success', 'HEAL');
                            tooltip.innerHTML =
                                `<div class="text-primary font-bold mb-1">${{player}} @ T+${{timeAtCursor.toFixed(1)}}s</div>` +
                                `<div class="mb-1"><span class="text-error">DMG: ${{Number(sample.d || 0).toLocaleString()}}</span> • <span class="text-success">HEAL: ${{Number(sample.h || 0).toLocaleString()}}</span></div>` +
                                `<div class="text-[8px] space-y-0.5">${{dmgSources}}${{healSources}}</div>`;
                        }});

                        layer.addEventListener('mouseleave', () => {{
                            crosshair.classList.add('hidden');
                            tooltip.classList.add('hidden');
                        }});
                    }});

                    const closeEventDetail = () => {{
                        eventDetailOverlay?.classList.remove('open');
                        eventDetailPanel?.classList.remove('open');
                    }};

                    const placeEventPanelNearCursor = (x, y) => {{
                        if (!eventDetailPanel) return;
                        const offsetX = 10;
                        const safePadding = 12;
                        const panelRect = eventDetailPanel.getBoundingClientRect();
                        const maxLeft = Math.max(safePadding, window.innerWidth - panelRect.width - safePadding);
                        const maxTop = Math.max(safePadding, window.innerHeight - panelRect.height - safePadding);
                        const nextLeft = Math.min(Math.max(safePadding, x + offsetX), maxLeft);
                        const nextTop = Math.min(Math.max(safePadding, y), maxTop);
                        eventDetailPanel.style.left = `${{nextLeft}}px`;
                        eventDetailPanel.style.top = `${{nextTop}}px`;
                        eventDetailPanel.style.right = 'auto';
                        eventDetailPanel.style.bottom = 'auto';
                    }};

                    const openEventDetail = (payload, clickX, clickY) => {{
                        if (!payload || !eventDetailPanel || !eventDetailOverlay) return;
                        eventDetailType.textContent = `${{payload.type || 'EVENT'}} @ T+${{Number(payload.time || 0).toFixed(1)}}S`;
                        eventDetailMeta.textContent = `Lane: ${{(payload.player || 'Unknown').toUpperCase()}}`;
                        eventDetailSource.textContent = payload.source || 'Unknown';
                        eventDetailTarget.textContent = payload.target || 'Unknown';
                        eventDetailLabel.textContent = payload.label || 'No summary available';
                        eventDetailLog.innerHTML = payload.mini_log_html || "<div class='text-[8px] opacity-20 italic text-center py-4 tracking-widest'>NO TELEMETRY IN WINDOW</div>";
                        eventDetailOverlay.classList.add('open');
                        eventDetailPanel.classList.add('open');
                        const fallbackX = window.innerWidth * 0.5;
                        const fallbackY = window.innerHeight * 0.5;
                        placeEventPanelNearCursor(
                            Number.isFinite(clickX) ? clickX : fallbackX,
                            Number.isFinite(clickY) ? clickY : fallbackY,
                        );
                    }};

                    eventMarkers.forEach((marker) => {{
                        const openFromElement = (event) => {{
                            const raw = marker.dataset.event || '';
                            if (!raw) return;
                            try {{
                                const rect = marker.getBoundingClientRect();
                                const clickX = event?.clientX ?? (rect.left + (rect.width / 2));
                                const clickY = event?.clientY ?? (rect.top + (rect.height / 2));
                                openEventDetail(JSON.parse(raw), clickX, clickY);
                            }} catch (_) {{
                                // Ignore bad payloads in sample data
                            }}
                        }};
                        marker.addEventListener('click', openFromElement);
                        marker.addEventListener('keydown', (event) => {{
                            if (event.key === 'Enter' || event.key === ' ') {{
                                event.preventDefault();
                                openFromElement();
                            }}
                        }});
                    }});

                    eventDetailOverlay?.addEventListener('click', closeEventDetail);
                    eventDetailClose?.addEventListener('click', closeEventDetail);
                    document.addEventListener('keydown', (event) => {{
                        if (event.key === 'Escape') closeEventDetail();
                    }});
                }})();
            </script>
        </body>
        </html>
        """
        return html

if __name__ == "__main__":
    tracker = MockTracker()
    report_html = tracker.generate_html_report()
    with open("example_combat_report.html", "w") as f:
        f.write(report_html)
    print("Example report generated: example_combat_report.html")
