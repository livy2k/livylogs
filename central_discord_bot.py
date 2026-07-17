import discord
from discord import app_commands
import asyncio
import os
import json
import uuid
import time
import hashlib
from aiohttp import web

# Configuration
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
PORT = int(os.environ.get('RELAY_PORT', 8080))

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN not set.")

class CentralRelayBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.verifications = {} # {code: {"user_id": int, "guild_id": int, "channel_id": int, "expires": float}}
        self.verified_links = {} # {app_id: {"user_id": int, "channel_id": int}}
        self.load_links()

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        # Start web server for app-to-bot communication
        app = web.Application()
        app.add_routes([
            web.post('/verify', self.handle_app_verify),
            web.post('/relay', self.handle_app_relay)
        ])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        asyncio.create_task(site.start())
        print(f"Relay API started on port {PORT}")

    def save_links(self):
        with open("verified_links.json", "w") as f:
            json.dump(self.verified_links, f)

    def load_links(self):
        if os.path.exists("verified_links.json"):
            try:
                with open("verified_links.json", "r") as f:
                    self.verified_links = json.load(f)
            except:
                self.verified_links = {}

    async def handle_app_verify(self, request):
        try:
            data = await request.json()
            code = data.get("code")
            app_id = data.get("app_id")
            
            if code in self.verifications:
                v = self.verifications[code]
                if time.time() < v["expires"]:
                    self.verified_links[app_id] = {
                        "user_id": v["user_id"],
                        "channel_id": v["channel_id"],
                        "guild_id": v["guild_id"]
                    }
                    self.save_links()
                    del self.verifications[code]
                    return web.json_response({"status": "success", "message": "Verified!"})
            
            return web.json_response({"status": "error", "message": "Invalid or expired code"}, status=400)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_relay(self, request):
        try:
            data = await request.json()
            app_id = data.get("app_id")
            message = data.get("message")
            
            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                channel = self.get_channel(link["channel_id"])
                if channel:
                    await channel.send(message)
                    return web.json_response({"status": "success"})
                return web.json_response({"status": "error", "message": "Channel not found"}, status=404)
            
            return web.json_response({"status": "error", "message": "Not verified"}, status=403)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

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
        f"Expires in 10 minutes.", ephemeral=True
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
