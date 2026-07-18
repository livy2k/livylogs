import json
import datetime
import os
import sys
from fpdf import FPDF

def create_bot_instructions_pdf(output_path):
    pdf = FPDF()
    pdf.add_page()

    def title(text):
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 8, text)
        pdf.ln(1)

    def body(text):
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, text)
        pdf.ln(1)

    # --- TITLE ---
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(211, 26, 23)
    pdf.cell(0, 14, "LivyLogs Full Setup Guide (Current Flow)", ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Very simple steps: do this, then this.", ln=True, align='C')
    pdf.ln(4)

    title("Read this first: real app entrypoint")
    body(
        "Start LivyLogs with python livylogs.py.\n"
        "Parser/engine pieces still exist, but this guide uses the current top-level app startup flow."
    )

    title("Part 1: Start LivyLogs app")
    body(
        "In PowerShell, run:\n"
        "cd C:\\Users\\LivyC\\PycharmProjects\\livylogs\n"
        "python --version\n"
        "python .\\livylogs.py\n"
        "\n"
        "Success looks like: the LivyLogs UI opens."
    )

    title("Part 2: First-run app checklist")
    body(
        "1) Open Options window.\n"
        "2) Select your SWG log file.\n"
        "3) Confirm combat events begin updating.\n"
        "4) Adjust overlay/opacity if wanted.\n"
        "\n"
        "Success looks like: damage/healing/session values move live."
    )

    title("Part 3: App window map (what each one does)")
    body(
        "- skimmers: quick high-level skim view\n"
        "- damage_meter: live damage totals/rate\n"
        "- leaderboard: ranking view\n"
        "- details: deep per-player/event breakdown\n"
        "- options: settings\n"
        "- alexa: helper/AI window\n"
        "- equalizer: audio/effect controls\n"
        "- livius: tactical roster view\n"
        "- gharv: utility analysis panel\n"
        "- fax: utility/status panel\n"
        "- discord_viewer: Discord link + relay state"
    )

    title("Part 4: Uncle ReCoN (simple explanation)")
    body(
        "Uncle ReCoN is loaded automatically during app startup.\n"
        "You normally do not start it manually.\n"
        "It supports intel/report-related workflows in the app ecosystem."
    )

    title("Part 5: Make Discord bot in Discord (one time)")
    body(
        "1) Go to Discord Developer Portal and create a New Application.\n"
        "2) Open the Bot tab and click Add Bot.\n"
        "3) Turn ON Message Content Intent.\n"
        "4) Copy the Bot Token (keep it secret).\n"
        "5) In OAuth2 -> URL Generator: check 'bot' and 'applications.commands'.\n"
        "6) Give it Send Messages + View Channel (+ Attach Files + Embed Links for advanced mode).\n"
        "7) Open the invite URL and add the bot to your server."
    )

    title("Part 6: Run relay bot (basic Discord posting)")
    body(
        "In PowerShell, run:\n"
        "\n"
        "pip install discord.py aiohttp\n"
        "$env:DISCORD_BOT_TOKEN=\"PASTE_YOUR_TOKEN_HERE\"\n"
        "$env:RELAY_PORT=\"8080\"   (optional)\n"
        "python .\\central_discord_bot.py\n"
        "\n"
        "Success looks like: 'Relay API started on port 8080' and 'Logged in as ...'."
    )

    title("Part 6B: Public standalone bot (host once for everyone)")
    body(
        "Like-I-am-5 version:\n"
        "- You (bot owner) keep one bot running all the time on one host.\n"
        "- Other people only invite your bot and link with one code.\n"
        "- They do NOT run bot code on their own PC.\n"
        "\n"
        "Owner setup:\n"
        "1) Keep central_discord_bot.py online 24/7.\n"
        "2) Put HTTPS in front (example: https://relay.yourdomain.com).\n"
        "3) Tell users to set in PowerShell:\n"
        "$env:CENTRAL_BOT_API_URL=\"https://relay.yourdomain.com\"\n"
        "\n"
        "Success looks like: users only do /verify + VERIFY & LINK."
    )

    title("Part 7: Link LivyLogs with one code")
    body(
        "1) In Discord, open the exact channel where you want messages.\n"
        "2) Run /verify.\n"
        "3) Discord shows a 6-character code (expires in 10 minutes).\n"
        "4) In LivyLogs: open Discord Relay window.\n"
        "5) Paste the code and click VERIFY & LINK.\n"
        "6) You should see RELAY ACTIVE."
    )

    title("Part 8: Specific channel ID (optional but recommended)")
    body(
        "If you want one exact channel:\n"
        "1) Turn on Discord Developer Mode.\n"
        "2) Right-click channel -> Copy Channel ID.\n"
        "3) Run /verify in that exact channel.\n"
        "\n"
        "Important: /verify binds to that exact guild_id + channel_id."
    )

    title("Part 9: Test relay mode")
    body(
        "Do a short combat test in-game.\n"
        "Success looks like: combat relay messages appear in the linked Discord channel."
    )

    title("Part 10: Advanced report + website mode (optional)")
    body(
        "Create .env from .env.example, then fill:\n"
        "- DISCORD_BOT_TOKEN\n"
        "- DISCORD_CHANNEL_ID\n"
        "- GITHUB_TOKEN\n"
        "- GITHUB_REPO\n"
        "- GITHUB_DOMAIN (optional)\n"
        "\n"
        "Run:\n"
        "\n"
        "pip install discord.py aiohttp python-dotenv cryptography pillow\n"
        "python .\\admin_tools\\discord_bot_advanced.py\n"
        "\n"
        "Success looks like: advanced bot logs in, tracks encounters, and can publish reports when GitHub values are valid."
    )

    title("Part 11: GitHub Pages setup (super simple)")
    body(
        "Goal: put your HTML reports on a website with almost no stress.\n"
        "\n"
        "1) Make a GitHub repo for reports.\n"
        "2) In GitHub repo Settings -> Pages, turn on GitHub Pages.\n"
        "3) In .env, fill:\n"
        "   - GITHUB_TOKEN (can write to repo)\n"
        "   - GITHUB_REPO (example: yourname/your-gh-pages-repo)\n"
        "   - GITHUB_DOMAIN (only if using custom domain)\n"
        "4) Run advanced bot again:\n"
        "python .\\admin_tools\\discord_bot_advanced.py\n"
        "\n"
        "Success looks like:\n"
        "- Discord gets tactical report messages.\n"
        "- GitHub gh-pages content updates.\n"
        "- Website report URL opens."
    )

    title("Common oops fixes")
    body(
        "- 'DISCORD_BOT_TOKEN not set': set the env var, then rerun the bot.\n"
        "- 'DISCORD_CHANNEL_ID environment variable not set': add it to .env for advanced mode.\n"
        "- 'Invalid or expired code': run /verify again and use the new code fast.\n"
        "- 'Connection Error' in app: make sure central_discord_bot.py is running and reachable.\n"
        "- No messages in channel: check bot permissions (Send Messages / View Channel).\n"
        "- GitHub upload skipped: check GITHUB_TOKEN and GITHUB_REPO in .env."
    )

    title("Ready status checklist")
    body(
        "[ ] LivyLogs opens with python .\\livylogs.py\n"
        "[ ] Options window set to your real SWG log file\n"
        "[ ] Bot invited to server\n"
        "[ ] central_discord_bot.py running\n"
        "[ ] (Public bot) Hosted URL is set with CENTRAL_BOT_API_URL\n"
        "[ ] /verify gives a code\n"
        "[ ] LivyLogs shows RELAY ACTIVE\n"
        "[ ] Combat pulse appears in Discord\n"
        "[ ] (Optional) HTML report published to GitHub Pages website"
    )

    # --- FOOTER ---
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d')} | LivyLogs Discord Relay Guide", align='C')

    pdf.output(output_path)
    print(f"PDF Instructions created at: {output_path}")

if __name__ == "__main__":
    output_name = "advanced_bot_instructions.pdf"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        output_name = sys.argv[1].strip()
    create_bot_instructions_pdf(output_name)
