import discord
from discord import app_commands
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
import secrets
from aiohttp import web

# Configuration
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
PORT = int(os.environ.get('RELAY_PORT', 8080))
DATABASE_URL = os.environ.get('DATABASE_URL', '') 

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN not set.")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set. Memory will not work!")    

class CentralRelayBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.verifications = {} # {code: {"user_id": int, "guild_id": int, "channel_id": int, "expires": float}}
        self.verified_links = {} # {app_id: {"user_id": int, "channel_id": int}}
        self.load_links()
        self.tracker = CombatTracker()

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        # Start web server for app-to-bot communication
        app = web.Application(client_max_size=1024**2 * 10) # 10MB limit
        app.add_routes([
            web.get('/', self.handle_root),
            web.post('/verify', self.handle_app_verify),
            web.post('/relay', self.handle_app_relay),
            web.post('/report', self.handle_app_report),
            web.get('/messages', self.handle_app_messages)
        ])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        asyncio.create_task(site.start())
        print(f"Relay API started on port {PORT}")

    def save_links(self):
        with open("verified_links.json", "w") as f:
            json.dump(self.verified_links, f)

    @staticmethod
    def _new_relay_token():
        return secrets.token_urlsafe(24)

    def load_links(self):
        if os.path.exists("verified_links.json"):
            try:
                with open("verified_links.json", "r") as f:
                    self.verified_links = json.load(f)
            except:
                self.verified_links = {}

    async def handle_root(self, request):
        return web.Response(text="LivyLogs Bot Relay is active and alive! 🚀", content_type='text/html')

    async def handle_app_verify(self, request):
        try:
            data = await request.json()
            code = data.get("code")
            app_id = data.get("app_id")
            
            if code in self.verifications:
                v = self.verifications[code]
                if time.time() < v["expires"]:
                    relay_token = self._new_relay_token()
                    self.verified_links[app_id] = {
                        "user_id": v["user_id"],
                        "channel_id": v["channel_id"],
                        "guild_id": v["guild_id"],
                        "relay_token": relay_token,
                        "linked_at": int(time.time())
                    }
                    self.save_links()
                    del self.verifications[code]
                    return web.json_response({
                        "status": "success",
                        "message": "Verified!",
                        "relay_token": relay_token
                    })
            
            return web.json_response({"status": "error", "message": "Invalid or expired code"}, status=400)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_relay(self, request):
        try:
            data = await request.json()
            app_id = data.get("app_id")
            message = data.get("message")
            image_data = data.get("image_data")
            relay_token = data.get("relay_token")
            author_name = data.get("author_name", "LivyLogs User")
            
            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                expected_token = link.get("relay_token")
                if expected_token and relay_token != expected_token:
                    return web.json_response({"status": "error", "message": "Unauthorized relay token"}, status=401)
                
                channel = self.get_channel(link["channel_id"])
                if channel is None:
                    try:
                        channel = await self.fetch_channel(link["channel_id"])
                    except Exception:
                        channel = None
                
                if channel:
                    # Pass pulse to tracker
                    if message and "[LIVYLOGS RELAY]" in message:
                        if self.tracker:
                            await self.tracker.add_pulse_from_msg(message, channel)

                    # Try to use Webhook for better attribution
                    webhook = None
                    try:
                        webhooks = await channel.webhooks()
                        webhook = discord.utils.get(webhooks, name="LivyLogs Relay")
                        if not webhook:
                            webhook = await channel.create_webhook(name="LivyLogs Relay")
                    except Exception:
                        webhook = None

                    if image_data:
                        image_bytes = base64.b64decode(image_data)
                        file = discord.File(io.BytesIO(image_bytes), filename="upload.png")
                        
                        if webhook:
                            await webhook.send(content=message or "", username=author_name, file=file)
                        else:
                            display_msg = f"**{author_name}**: {message}" if message else f"**{author_name}** shared an image:"
                            await channel.send(content=display_msg, file=file)
                    else:
                        safe_message = (message or "")[:1900]
                        if safe_message:
                            if webhook:
                                await webhook.send(content=safe_message, username=author_name)
                            else:
                                display_msg = f"**{author_name}**: {safe_message}"
                                await channel.send(display_msg)
                    return web.json_response({"status": "success"})
                return web.json_response({"status": "error", "message": "Channel not found"}, status=404)
            
            return web.json_response({"status": "error", "message": "Not verified"}, status=403)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_report(self, request):
        try:
            data = await request.json()
            app_id = data.get("app_id")
            relay_token = data.get("relay_token")
            content = data.get("content") # HTML content
            filename = data.get("filename", "combat_report.html")
            author_name = data.get("author_name", "LivyLogs User")

            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                if relay_token != link.get("relay_token"):
                    return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
                
                channel = self.get_channel(link["channel_id"])
                if not channel:
                    channel = await self.fetch_channel(link["channel_id"])
                
                if channel:
                    # Upload to GitHub if configured
                    report_url = None
                    if self.tracker and self.tracker.publisher:
                        # Create a unique path for the report
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', author_name)
                        github_path = f"reports/{safe_name}_{ts}.html"
                        
                        await self.tracker.publisher._upload_to_github(
                            github_path, 
                            content, 
                            f"Combat Report for {author_name}"
                        )
                        
                        if self.tracker.publisher.domain:
                            report_url = f"https://{self.tracker.publisher.domain}/{github_path}"
                        elif self.tracker.publisher.repo:
                            # Fallback to raw.githubusercontent or similar if domain not set
                            user_repo = self.tracker.publisher.repo
                            report_url = f"https://{user_repo.split('/')[0]}.github.io/{user_repo.split('/')[1]}/{github_path}"

                    # Send to Discord
                    embed = discord.Embed(
                        title="📊 Combat Performance Report",
                        description=f"New tactical breakdown generated for **{author_name}**.",
                        color=discord.Color.blue(),
                        timestamp=datetime.datetime.now()
                    )
                    
                    if report_url:
                        embed.add_field(name="🌐 Web View", value=f"[Click to View Interactive Report]({report_url})")
                        await channel.send(embed=embed)
                    else:
                        # If no GitHub, send as file attachment
                        file = discord.File(io.BytesIO(content.encode()), filename=filename)
                        await channel.send(embed=embed, file=file)

                    return web.json_response({"status": "success", "url": report_url})
                return web.json_response({"status": "error", "message": "Channel not found"}, status=404)
            return web.json_response({"status": "error", "message": "Not verified"}, status=403)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_messages(self, request):
        try:
            app_id = request.query.get("app_id")
            relay_token = request.query.get("relay_token")
            
            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                if relay_token != link.get("relay_token"):
                    return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

                channel = self.get_channel(link["channel_id"])
                if not channel:
                    channel = await self.fetch_channel(link["channel_id"])
                
                messages = []
                async for msg in channel.history(limit=20):
                    # Skip messages from the bot itself if they are pulses
                    if msg.author == self.user and "[LIVYLOGS RELAY]" in msg.content:
                        continue
                    messages.append({
                        "author": str(msg.author.display_name),
                        "content": msg.content,
                        "timestamp": msg.created_at.timestamp(),
                        "is_bot": msg.author.bot,
                        "attachments": [att.url for att in msg.attachments if att.content_type and att.content_type.startswith("image")]
                    })
                
                # Return in chronological order
                return web.json_response({"status": "success", "messages": messages[::-1]})
            
            return web.json_response({"status": "error", "message": "Not verified"}, status=403)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)


# --- GITHUB PAGES PUBLISHER ---
class GitHubPublisher:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.domain = os.getenv("GITHUB_DOMAIN")
        self.branch = "gh-pages"

    async def _upload_to_github(self, path, content, message):
        if not self.token or not self.repo: return
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                sha = (await resp.json()).get("sha") if resp.status_code == 200 else None
            payload = {"message": message, "content": base64.b64encode(content.encode() if isinstance(content, str) else content).decode(), "branch": self.branch}
            if sha: payload["sha"] = sha
            await session.put(url, headers=headers, json=payload)

# --- COMBAT TRACKER ---
class CombatTracker:
    def __init__(self):
        self.history = {}
        self.start_time = 0
        self.last_pulse_time = 0
        self.is_active = False
        self.lock = asyncio.Lock()
        self.publisher = GitHubPublisher()
        self.pulse_pattern = re.compile(r"\[LIVYLOGS RELAY\] (.+?) \| DMG: (\d+) \| HEAL: (\d+) \| INC: (\d+) \| KD: (\d+) \| TGT: (.+?)(?: \| EVTS: (.+))?$")

    async def add_pulse_from_msg(self, content, channel=None):
        match = self.pulse_pattern.match(content)
        if not match: return
        name, dmg, heal = match.group(1).strip(), int(match.group(2)), int(match.group(3))
        async with self.lock:
            now = time.time()
            if not self.is_active:
                self.is_active, self.start_time, self.history = True, now, {}
                if channel: await channel.send("⚔️ **PvP Combat has begun!**")
            if name not in self.history: self.history[name] = {"totals": [], "events": []}
            self.history[name]["totals"].append((now - self.start_time, dmg, heal))
            self.last_pulse_time = now

bot = CentralRelayBot()

@bot.tree.command(name="verify", description="Get a verification code for the LivyLogs app")
async def verify(interaction: discord.Interaction):
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    bot.verifications[code] = {
        "user_id": interaction.user.id,
        "guild_id": interaction.guild_id,
        "channel_id": interaction.channel_id,
        "expires": time.time() + 600 # 10 mins
    }
    await interaction.response.send_message(
        f"🛡️ **LivyLogs Verification Code**: `{code}`\n"
        f"Enter this code in your LivyLogs app to link this channel.\n"
        f"Expires in 10 minutes.\n"
        f"Use `/unlink` in this channel any time to stop broadcasts.", ephemeral=True
    )

@bot.tree.command(name="unlink", description="Stop LivyLogs broadcasts to this channel")
async def unlink(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    user_id = interaction.user.id

    matching_app_ids = [
        app_id
        for app_id, link in bot.verified_links.items()
        if link.get("guild_id") == guild_id
        and link.get("channel_id") == channel_id
        and link.get("user_id") == user_id
    ]

    if not matching_app_ids:
        await interaction.response.send_message(
            "No active LivyLogs link from your account was found for this channel.",
            ephemeral=True
        )
        return

    for app_id in matching_app_ids:
        bot.verified_links.pop(app_id, None)

    bot.save_links()
    await interaction.response.send_message(
        f"✅ Unlinked `{len(matching_app_ids)}` LivyLogs app link(s) for this channel."
        " Broadcasts to this channel are now stopped for those links.",
        ephemeral=True
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Please set DISCORD_BOT_TOKEN environment variable.")
