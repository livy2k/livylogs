# LivyLogs - Full Setup Guide (Current Flow)

This guide is the **current, real startup flow** for LivyLogs.

## What this app does

LivyLogs is a live SWG combat log app with multiple windows for combat tracking, group analysis, alerts, loot/intel, and Discord reporting.

## Important startup clarification (read this first)

- The current Python app entrypoint is `livylogs.py`.
- It starts the UI by creating `CombatLogApp` and running the Tk main loop.
- The parser engine is still part of the system, but it is **not** the top-level app launch command in this guide.

If you follow this README, launch with:

```powershell
python .\livylogs.py
```

---

## Part 1: Install and launch LivyLogs

### Step 1) Open PowerShell in this folder

```powershell
cd C:\Users\LivyC\PycharmProjects\livylogs
```

### Step 2) Make sure Python is available

```powershell
python --version
```

Success looks like: you see a Python version (example `Python 3.12.x`).

### Step 3) Launch LivyLogs

```powershell
python .\livylogs.py
```

Success looks like:
- The LivyLogs UI appears.
- You can open app windows from the UI.

---

## Part 2: First-run checklist (do this in order)

1. Open the app `Options` window.
2. Click/select your SWG combat log file.
3. Confirm events start appearing while you play.
4. Adjust opacity/snap behavior if you want overlay style.
5. Use reset only when you want a new clean session.

Success looks like:
- Damage/healing/session values start moving.
- Windows update without manual refresh.

---

## Part 3: App window tour (what each window is for)

These windows are registered by the app:

- `skimmers`
  - Fast high-level skim of combat/session information.
- `damage_meter`
  - Live damage totals/rate view.
- `leaderboard`
  - Combined player ranking (damage + healing context).
- `details`
  - Deep per-player/per-event breakdown.
- `options`
  - Main settings and behavior controls.
- `alexa`
  - AI/helper style interaction window.
- `equalizer`
  - Audio/effect-related controls.
- `livius`
  - Main tactical/roster combat visibility view.
- `gharv`
  - Additional specialized analysis/utility panel.
- `fax`
  - Additional utility/status panel.
- `discord_viewer`
  - Discord relay link state and verify-link workflow.

Tip for new users:
1. Start with `livius`, `leaderboard`, and `details`.
2. Use `options` to set file and preferences.
3. Use `discord_viewer` only when linking Discord.

---

## Part 4: Uncle ReCoN (plain-language explanation)

Uncle ReCoN is an intelligence data component loaded by the app during startup.

- It is initialized automatically when the app starts.
- You do **not** need to manually start it in normal usage.
- It supports intel/report-related experiences used by the wider LivyLogs ecosystem.

What you need to configure:
- For basic app usage: usually nothing extra.
- For advanced Discord/report pipelines: follow the advanced bot sections below.

---

## Part 5: Standalone Discord relay bot (one-code link)

Use this when you want combat relay messages in Discord.

If you are the **bot owner** (you host one public bot for everyone), do these steps.
If you are an **end user**, skip to **Step 5** and just do `/verify` + `VERIFY & LINK`.

### Step 1) Install relay dependencies

```powershell
pip install discord.py aiohttp
```

### Step 2) Set token (same PowerShell window)

```powershell
$env:DISCORD_BOT_TOKEN="PASTE_YOUR_TOKEN_HERE"
```

### Step 3) (Optional) set relay port

```powershell
$env:RELAY_PORT="8080"
```

### Step 4) Run the relay bot

```powershell
python .\central_discord_bot.py
```

Success looks like console lines similar to:
- `Relay API started on port 8080`
- `Logged in as ...`

### Step 5) Invite the bot and link app

1. Invite bot with scopes: `bot`, `applications.commands`.
2. In your target Discord channel, run `/verify`.
3. Copy the 6-character code.
4. In LivyLogs `Discord Relay` window, paste code.
5. Click `VERIFY & LINK`.

Success looks like:
- LivyLogs shows relay linked/active.
- Messages appear in the channel used for `/verify`.

### Public standalone bot (host once, then everyone can use it)

Bot owner quick flow:
1. Keep `central_discord_bot.py` running 24/7 on one host.
2. Put HTTPS in front of it (example: `https://relay.yourdomain.com`).
3. Tell users to set:

```powershell
$env:CENTRAL_BOT_API_URL="https://relay.yourdomain.com"
```

4. Users invite bot, run `/verify` in their channel, paste code in LivyLogs, click `VERIFY & LINK`.

Success looks like:
- Users do not run Python bot code locally.
- Each user/server links their own channel safely with `/verify`.

### Specific channel behavior (important)

- `/verify` binds to the exact `guild_id` + `channel_id` where you run it.
- That means relays post to that exact linked destination, not random channels.

If you want one exact channel ID in advanced flow:

```powershell
$env:DISCORD_CHANNEL_ID="PASTE_CHANNEL_ID_HERE"
```

Then restart the bot process.

If app should use a hosted relay API instead of local:

```powershell
$env:CENTRAL_BOT_API_URL="https://your-relay-hostname"
```

---

## Part 6: Advanced Discord bot + website/report publishing (optional)

Use this only if you want full report automation and publish flow.

### Step 1) Create `.env` from template

1. Copy `.env.example` to `.env`.
2. Fill at least:
   - `DISCORD_BOT_TOKEN`
3. For website publishing, also fill:
   - `DISCORD_CHANNEL_ID`
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - `GITHUB_DOMAIN` (optional)

### Step 2) Install advanced dependencies

```powershell
pip install discord.py aiohttp python-dotenv cryptography pillow
```

### Step 3) Run advanced bot script

```powershell
python .\admin_tools\discord_bot_advanced.py
```

Success looks like:
- Bot logs in.
- Relay/report processing begins.
- If GitHub vars are valid, publish actions run to your pages repo.

### Step 4) Verify website/report flow

Check these:
- Bot is online.
- Relay events hit your configured channel.
- Encounter report artifacts are generated.
- GitHub Pages content updates.
- Report URL opens.

### GitHub Pages (like I am 5 version)

1. Make a GitHub repo for report pages.
2. In repo settings, turn on **GitHub Pages**.
3. Put these in `.env`:
   - `GITHUB_TOKEN` (a token that can write to the repo)
   - `GITHUB_REPO` (example: `yourname/your-gh-pages-repo`)
   - `GITHUB_DOMAIN` (only if you use your own custom domain)
4. Run advanced bot again:

```powershell
python .\admin_tools\discord_bot_advanced.py
```

Success looks like:
- Discord gets the tactical report.
- GitHub repo `gh-pages` content updates.
- Your Pages URL opens the report.

---

## Part 7: Troubleshooting (quick fixes)

- `DISCORD_BOT_TOKEN not set`
  - Set token in the same PowerShell window before running script.
- `DISCORD_CHANNEL_ID environment variable not set`
  - Add `DISCORD_CHANNEL_ID` in `.env` for advanced mode.
- `Invalid or expired code`
  - Run `/verify` again and use fresh code quickly.
- `Channel not found`
  - Confirm bot invite + permissions in that server/channel.
- No messages in Discord
  - Confirm bot process is still running and app is linked.

---

## Part 8: Packaging to `.exe` (optional)

```powershell
pyinstaller .\LivyLogs.spec
```

---

## Related docs

- `ADVANCED_DISCORD_BOT_SETUP_GUIDE.md` (expanded advanced setup)
- `.env.example` (all expected environment variables)
- `DEVELOPMENT_LOG.md` (internal architecture notes)
- `BUILD_ENGINE.md` (engine/build notes)

## License

GNU GPL v3.0 — see `LICENSE`.
