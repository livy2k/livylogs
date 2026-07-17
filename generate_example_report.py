import datetime
import random
import os

class MockTracker:
    def __init__(self):
        # Sample data to make the report look realistic
        self.history = {
            "YOU": {
                "pulses": [
                    (4, 50, 0, "Stormtrooper"),
                    (5, 100, 0, "Stormtrooper"),
                    (6, 20, 0, "Stormtrooper"),
                    (11, 200, 0, "Stormtrooper"),
                    (12, 500, 0, "Stormtrooper"),
                    (24, 0, 0, "YOU"),
                    (25, 0, 0, "YOU"),
                    (45, 0, 0, "Stormtrooper"),
                    (54, 300, 0, "Bounty Hunter"),
                    (55, 600, 0, "Bounty Hunter"),
                ],
                "totals": [(5, 150, 0), (12, 850, 0), (55, 1750, 0)],
                "events": [
                    (5, "PD", "YOU", "Stormtrooper", "Point Blank Shot"),
                    (12, "KD", "YOU", "Stormtrooper", "Killing Blow"),
                    (25, "INC", "Bounty Hunter", "YOU", "Tracking Shot"),
                    (45, "LOOT", "YOU", "Stormtrooper", "Credits, Blaster Carbine"),
                    (55, "KILL", "YOU", "Bounty Hunter", "Final Strike"),
                ]
            },
            "Vader": {
                "pulses": [
                    (9, 100, 0, "Rebel Scum"),
                    (10, 200, 0, "Rebel Scum"),
                    (29, 300, 0, "Luke"),
                    (30, 400, 0, "Luke"),
                    (59, 1000, 0, "Luke"),
                    (60, 0, 0, "Luke"),
                ],
                "totals": [(10, 300, 0), (30, 700, 0), (60, 1700, 0)],
                "events": [
                    (10, "INT", "Vader", "Rebel Scum", "Force Choke"),
                    (30, "PD", "Vader", "Luke", "Lightsaber Strike"),
                    (60, "DEATH", "Luke", "Vader", "Defeated"),
                ]
            },
            "Boba Fett": {
                "pulses": [
                    (14, 50, 0, "Han Solo"),
                    (15, 80, 0, "Han Solo"),
                    (39, 0, 0, "Boba Fett"),
                    (40, 0, 0, "Boba Fett"),
                ],
                "totals": [(15, 130, 0), (40, 130, 0)],
                "events": [
                    (15, "PD", "Boba Fett", "Han Solo", "E-3 Carbine Fire"),
                    (40, "INC", "Han Solo", "Boba Fett", "Lucky Shot"),
                ]
            }
        }

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
                .player-row {{ transition: background 0.3s; }}
                .player-row:hover {{ background: rgba(0, 236, 255, 0.05); }}
                .sparkline {{ pointer-events: none; position: absolute; inset: 0; z-index: 10; opacity: 0.6; }}
            </style>
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
                <div class="hud-border bg-black/40 rounded-lg p-1 overflow-x-auto relative">
                    <div class="swimlane-container" style="height: {len(players) * 140 + 100}px;">
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
            top = 80 + (i * 140)
            is_you = name.upper() == "YOU"
            row_bg = "bg-primary/5 border-primary/30" if is_you else "bg-white/[0.02] border-white/5"
            
            # Generate Sparkline Data
            pulses = self.history[name].get("pulses", [])
            dmg_points = []
            heal_points = []
            
            max_val = 1
            for t, d, h, _ in pulses: max_val = max(max_val, d, h)
            
            # Construct SVG paths for DMG and HEAL
            dmg_path = ""
            heal_path = ""
            if pulses:
                # Add padding points at start/end
                sorted_pulses = sorted(pulses, key=lambda x: x[0])
                
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
                        <div class="absolute left-0 right-0 h-28 rounded border {row_bg} flex items-center px-6 backdrop-blur-sm player-row" style="top: {top}px;">
                            <div class="w-48 flex-shrink-0 border-r border-white/10 mr-8 py-2 relative z-20">
                                <span class="text-[8px] font-black opacity-30 uppercase tracking-[0.3em] mb-1 block">Entity Signature</span>
                                <span class="text-lg font-orbitron font-black {'text-primary glow-text-blue' if is_you else 'text-slate-200'} truncate block tracking-widest">
                                    {name.upper()}
                                </span>
                                <div class="flex gap-2 mt-2">
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-error" style="width: {min(100, sum(p[1] for p in pulses)/1000)}%"></div>
                                    </div>
                                    <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div class="h-full bg-success" style="width: {min(100, sum(p[2] for p in pulses)/1000)}%"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="relative flex-grow h-full overflow-hidden">
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

                <div class="mt-12 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div class="flex items-center gap-3">
                        <div class="text-[8px] font-black tracking-[0.4em] uppercase text-primary/30">Livius Analysis Engine v3.0 // Tactical Overlay</div>
                        <div class="w-1.5 h-1.5 rounded-full bg-primary/20 animate-pulse"></div>
                    </div>
                    <div class="text-[8px] font-mono font-bold tracking-widest uppercase opacity-20">Cycle Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
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
