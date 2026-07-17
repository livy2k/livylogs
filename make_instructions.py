import json
import datetime
import os
from fpdf import FPDF

def create_bot_instructions_pdf(output_path):
    pdf = FPDF()
    pdf.add_page()
    
    # --- TITLE ---
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(211, 26, 23) # Red #d31a17
    pdf.cell(0, 20, "LIVIUS ADVANCED BOT: TACTICAL GUIDE", ln=True, align='C')
    pdf.ln(5)
    
    # --- INTRODUCTION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Overview", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, "The Advanced Bot is a high-performance Discord automation tool designed to link your game client with the Livius Tactical Overlay. It provides real-time combat tracking, database queries via Uncle ReCoN, and automatic report publishing to GitHub Pages.")
    pdf.ln(10)
    
    # --- SETUP SECTION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. One-Code Setup (/123)", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, "Linking your desktop application to the Discord Bot is now automated:")
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 6, "1. In your Discord server, type '/123' in the channel where you want reports posted.\n2. The bot will DM you a 6-digit secure code.\n3. Open the LivyLogs app -> Options -> Advanced Bot Setup.\n4. Enter the code and click 'LINK BOT'.\n5. The app will automatically configure your Token and Channel ID using encrypted transport.")
    pdf.ln(8)
    
    # --- COMMANDS SECTION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Tactical Commands", ln=True)
    pdf.set_font("Arial", size=11)
    
    commands = [
        ["/rico <query>", "Search Uncle ReCoN archives for Mobs, Items, or Stats."],
        ["/curate", "List pending combat reports waiting for approval."],
        ["/curate approve <ID>", "Validate a report and move it to official archives."],
        ["/123", "Generate a setup code for the desktop application."]
    ]
    
    for cmd, desc in commands:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(50, 8, cmd, border=0)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, desc, ln=True)
    
    pdf.ln(10)
    
    # --- WEB INTERFACE SECTION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Tactical Overlay & Web Reports", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, "The bot automatically generates interactive HTML reports after combat encounters. These reports feature:\n- Dynamic DPS/HPS Charts (Tailwind & DaisyUI)\n- Loot Acquisition Tracking\n- MVP Performance Metrics\n- Uncle ReCoN Stat Injections")
    pdf.ln(10)
    
    # --- TECHNICAL SPECS ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "4. Technical Specifications", ln=True)
    pdf.set_font("Arial", size=10)
    specs = (
        "- Runtime: Python 3.12+ / Discord.py\n"
        "- Database: Uncle ReCoN v12 (RAM-cached SQLite)\n"
        "- Encryption: Fernet (AES-128) for token transport\n"
        "- Web API: Port 8081 (Local Verification Relay)\n"
        "- Integration: GitHub API v3 for Web Hosting"
    )
    pdf.multi_cell(0, 5, specs)
    
    # --- FOOTER ---
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d')} | Livius Tactical Systems v4.0", align='C')
    
    pdf.output(output_path)
    print(f"PDF Instructions created at: {output_path}")

if __name__ == "__main__":
    create_bot_instructions_pdf("advanced_bot_instructions.pdf")
