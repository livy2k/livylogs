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
import traceback
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
        print("[Bot] Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"[Bot] Successfully synced {len(synced)} commands.")
        except Exception as e:
            print(f"[Bot] Failed to sync commands: {e}")
            traceback.print_exc()
        
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
                    raw_links = json.load(f)
                    # Convert IDs back to int because JSON makes them strings
                    self.verified_links = {}
                    for app_id, data in raw_links.items():
                        self.verified_links[app_id] = {
                            "user_id": int(data["user_id"]),
                            "channel_id": int(data["channel_id"]),
                            "guild_id": int(data["guild_id"]) if data.get("guild_id") else None,
                            "relay_token": data["relay_token"],
                            "linked_at": data.get("linked_at", 0)
                        }
            except Exception as e:
                print(f"Error loading links: {e}")
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
            traceback.print_exc()
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
                
                channel_id = int(link["channel_id"])
                channel = self.get_channel(channel_id)
                if channel is None:
                    try:
                        channel = await self.fetch_channel(channel_id)
                    except Exception as ce:
                        print(f"Failed to fetch channel {channel_id}: {ce}")
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
            traceback.print_exc()
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_report(self, request):
        try:
            if request.content_type == 'application/json':
                data = await request.json()
            else:
                # Handle multipart/form-data fallback
                data = await request.post()
                # If content is a FileField, read it
                if "content" in data and not isinstance(data["content"], str):
                    data = dict(data) # copy
                    data["content"] = data["content"].file.read().decode('utf-8')

            app_id = data.get("app_id")
            relay_token = data.get("relay_token")
            content = data.get("content") # HTML content
            filename = data.get("filename", "combat_report.html")
            author_name = data.get("author_name", "LivyLogs User")

            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                if relay_token != link.get("relay_token"):
                    return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
                
                channel_id = int(link["channel_id"])
                channel = self.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.fetch_channel(channel_id)
                    except Exception as ce:
                        print(f"Failed to fetch channel {channel_id}: {ce}")
                        return web.json_response({"status": "error", "message": f"Channel {channel_id} not accessible"}, status=404)
                
                if channel:
                    # Optional stats from payload
                    try:
                        total_dmg = data.get("total_dmg")
                        total_heal = data.get("total_heal")
                        total_kd = data.get("total_kd")
                    except Exception as stats_e:
                        print(f"Error parsing stats: {stats_e}")
                        total_dmg = total_heal = total_kd = None

                    # Upload to GitHub if configured
                    report_url = None
                    try:
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
                                # Clean domain: remove http/https, leading/trailing slashes, and spaces
                                clean_domain = self.tracker.publisher.domain.replace("https://", "").replace("http://", "").strip().strip("/")
                                if clean_domain:
                                    report_url = f"https://{clean_domain}/{github_path}"
                            elif self.tracker.publisher.repo and "/" in self.tracker.publisher.repo:
                                user_repo = self.tracker.publisher.repo.strip().strip("/")
                                parts = user_repo.split('/')
                                if len(parts) >= 2:
                                    report_url = f"https://{parts[0]}.github.io/{parts[1]}/{github_path}"
                            
                            if report_url:
                                # Final safety check: ensure protocol and no spaces
                                if not report_url.startswith("http"):
                                    report_url = f"https://{report_url}"
                                report_url = report_url.replace(" ", "%20")
                                
                                # Validate URL format - basic check for Discord
                                if "://" not in report_url or "." not in report_url:
                                    print(f"[Report] Invalid URL skipped: {report_url}")
                                    report_url = None
                                else:
                                    print(f"[Report] Generated URL: {report_url}")
                    except Exception as github_e:
                        print(f"GitHub Upload Error: {github_e}")
                        traceback.print_exc()

                    # Send to Discord
                    try:
                        # Ensure filename is safe for Discord
                        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                        
                        embed = discord.Embed(
                            title=f"📊 Combat Performance Report: {author_name}",
                            description="A new tactical breakdown has been generated for this encounter.",
                            color=discord.Color.gold(),
                            timestamp=datetime.datetime.now()
                        )

                        if total_dmg is not None:
                            try:
                                embed.add_field(name="⚔️ Total Damage", value=f"{int(total_dmg):,}", inline=True)
                            except: embed.add_field(name="⚔️ Total Damage", value=str(total_dmg), inline=True)
                        if total_heal is not None:
                            try:
                                embed.add_field(name="💉 Total Healing", value=f"{int(total_heal):,}", inline=True)
                            except: embed.add_field(name="💉 Total Healing", value=str(total_heal), inline=True)
                        if total_kd is not None:
                            embed.add_field(name="💀 KDs", value=str(total_kd), inline=True)
                        
                        # Strict URL validation for Discord
                        is_valid_url = False
                        if report_url and isinstance(report_url, str):
                            report_url = report_url.strip()
                            if report_url.startswith(("http://", "https://")) and "." in report_url and len(report_url) > 12:
                                # Further validation: check for common illegal characters or incomplete domains
                                domain_part = report_url.split("//")[-1].split("/")[0]
                                if "." in domain_part and len(domain_part) > 3:
                                    is_valid_url = True

                        if is_valid_url:
                            print(f"[Report] Assigning valid URL to embed: {report_url}")
                            embed.url = report_url
                            embed.add_field(name="🌐 Interactive Web View", value=f"**[Click Here to Open Report]({report_url})**", inline=False)
                            
                            hosting_provider = "GitHub"
                            if self.tracker.publisher.domain:
                                if "wasmer" in self.tracker.publisher.domain:
                                    hosting_provider = "Wasmer Edge"
                                elif "pages.dev" in self.tracker.publisher.domain:
                                    hosting_provider = "Cloudflare Pages"
                                else:
                                    hosting_provider = self.tracker.publisher.domain
                            
                            embed.set_footer(text=f"LivyLogs • Hosted on {hosting_provider}")
                            await channel.send(embed=embed)
                        else:
                            print(f"[Report] No valid URL found or validation failed (URL: {report_url}). Sending as attachment.")
                            # If no URL or invalid URL, send as file attachment
                            file_data = content.encode() if isinstance(content, str) else content
                            file = discord.File(io.BytesIO(file_data), filename=safe_filename)
                            embed.add_field(name="📎 Attached Report", value=f"Open the attached file `{safe_filename}` in any web browser to view the full interactive report.", inline=False)
                            embed.set_footer(text="LivyLogs • Direct File Delivery")
                            await channel.send(embed=embed, file=file)

                        if self.tracker and self.tracker.publisher:
                            if not self.tracker.publisher.token or not self.tracker.publisher.repo:
                                 await channel.send("⚠️ **Note**: Website publishing is not fully configured (missing Token or Repo). Sent as attachment instead.")
                    except Exception as discord_e:
                        print(f"Discord Send Error: {discord_e}")
                        traceback.print_exc()
                        # Last ditch effort: send raw content if embed fails
                        error_detail = f" (Error: {str(discord_e)[:200]})"
                        debug_info = ""
                        if is_valid_url:
                            debug_info = f"\nDebug: Attempted URL: `{report_url}`"
                        await channel.send(f"📊 **Combat Report for {author_name}** generated but failed to format correctly.{error_detail}{debug_info}")

                    return web.json_response({"status": "success", "url": report_url})
                return web.json_response({"status": "error", "message": "Channel not found"}, status=404)
            return web.json_response({"status": "error", "message": "Not verified"}, status=403)
        except Exception as e:
            traceback.print_exc()
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_app_messages(self, request):
        try:
            app_id = request.query.get("app_id")
            relay_token = request.query.get("relay_token")
            
            # Debug log to see what's coming in
            print(f"[API] Messages request from {app_id}. Token provided: {'Yes' if relay_token else 'No'}")
            
            if app_id in self.verified_links:
                link = self.verified_links[app_id]
                expected_token = link.get("relay_token")
                
                if not relay_token or relay_token != expected_token:
                    print(f"[API] 401 Unauthorized for {app_id}")
                    return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

                channel_id = int(link["channel_id"])
                channel = self.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.fetch_channel(channel_id)
                    except Exception as ce:
                        print(f"Failed to fetch channel {channel_id}: {ce}")
                        return web.json_response({"status": "error", "message": f"Channel {channel_id} not accessible"}, status=404)
                
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
            traceback.print_exc()
            return web.json_response({"status": "error", "message": str(e)}, status=500)


# --- GITHUB PAGES PUBLISHER ---
class GitHubPublisher:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.domain = os.getenv("GITHUB_DOMAIN")
        self.branch = os.getenv("GITHUB_BRANCH", "gh-pages")
        self._repo_exists = None  # Cache for repository existence check

    async def _check_repo_exists(self):
        """Check if the configured repository exists on GitHub."""
        if self._repo_exists is not None:
            return self._repo_exists
        
        if not self.token:
            print("[GitHub] Cannot check repository: GITHUB_TOKEN is not set.")
            self._repo_exists = False
            return False
        if not self.repo:
            print("[GitHub] Cannot check repository: GITHUB_REPO is not set.")
            self._repo_exists = False
            return False
        
        url = f"https://api.github.com/repos/{self.repo}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        print(f"[GitHub] Checking repository existence at {url}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    response_text = await resp.text()
                    print(f"[GitHub] Repository check response status: {resp.status}")
                    if resp.status == 200:
                        print(f"[GitHub] Repository {self.repo} exists and is accessible.")
                        self._repo_exists = True
                        return True
                    elif resp.status == 404:
                        print(f"[GitHub] Repository {self.repo} does not exist. Attempting to create it...")
                        created = await self._create_repo()
                        if created:
                            print(f"[GitHub] Repository {self.repo} created successfully.")
                            self._repo_exists = True
                            return True
                        else:
                            print(f"[GitHub] Failed to create repository {self.repo}.")
                            self._repo_exists = False
                            return False
                    elif resp.status == 401:
                        print(f"[GitHub] ERROR: Unauthorized. Check your GITHUB_TOKEN.")
                        print(f"[GitHub] Response: {response_text[:200]}")
                        self._repo_exists = False
                        return False
                    elif resp.status == 403:
                        print(f"[GitHub] ERROR: Forbidden. Token may lack repo scope.")
                        print(f"[GitHub] Response: {response_text[:200]}")
                        self._repo_exists = False
                        return False
                    else:
                        print(f"[GitHub] Error checking repository ({resp.status}): {response_text[:200]}")
                        self._repo_exists = False
                        return False
        except Exception as e:
            print(f"[GitHub] Exception checking repository: {e}")
            traceback.print_exc()
            self._repo_exists = False
            return False

    async def _create_repo(self):
        """Create the repository on GitHub if it doesn't exist."""
        if not self.token:
            print("[GitHub] Cannot create repository: GITHUB_TOKEN is not set.")
            return False
        if not self.repo:
            print("[GitHub] Cannot create repository: GITHUB_REPO is not set.")
            return False
        
        # Parse username/repo from self.repo
        parts = self.repo.strip().strip("/").split("/")
        if len(parts) < 2:
            print(f"[GitHub] Invalid repo format: {self.repo}. Expected username/repo")
            return False
        
        username = parts[0]
        repo_name = parts[1]
        
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "name": repo_name,
            "description": "LivyLogs Combat Reports",
            "private": False,
            "auto_init": True,
            "gitignore_template": "Python"
        }
        
        print(f"[GitHub] Creating repository {self.repo}...")
        print(f"[GitHub] Token length: {len(self.token)} chars")
        print(f"[GitHub] Token starts with: {self.token[:10]}...")
        print(f"[GitHub] Request URL: {url}")
        print(f"[GitHub] Payload: {json.dumps(payload)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    response_text = await resp.text()
                    print(f"[GitHub] Create repo response status: {resp.status}")
                    print(f"[GitHub] Create repo response body: {response_text[:500]}")
                    if resp.status in (200, 201):
                        print(f"[GitHub] Repository {self.repo} created successfully.")
                        # Also create gh-pages branch
                        await self._create_gh_pages_branch()
                        return True
                    elif resp.status == 401:
                        print(f"[GitHub] ERROR: Unauthorized. Check your GITHUB_TOKEN.")
                        print(f"[GitHub] Token may be invalid or expired.")
                        return False
                    elif resp.status == 403:
                        print(f"[GitHub] ERROR: Forbidden. Token may lack repo scope.")
                        print(f"[GitHub] Ensure your token has 'repo' or 'public_repo' scope.")
                        return False
                    elif resp.status == 422:
                        print(f"[GitHub] ERROR: Repository already exists or name is invalid.")
                        print(f"[GitHub] Response: {response_text[:500]}")
                        return False
                    else:
                        print(f"[GitHub] Failed to create repository: {response_text[:500]}")
                        return False
        except Exception as e:
            print(f"[GitHub] Exception creating repository: {e}")
            traceback.print_exc()
            return False

    async def _create_gh_pages_branch(self):
        """Create the gh-pages branch for GitHub Pages."""
        if not self.token:
            print("[GitHub] Cannot create gh-pages branch: GITHUB_TOKEN is not set.")
            return
        if not self.repo:
            print("[GitHub] Cannot create gh-pages branch: GITHUB_REPO is not set.")
            return
        
        print(f"[GitHub] Creating gh-pages branch for {self.repo}...")
        
        # Get the default branch SHA
        url = f"https://api.github.com/repos/{self.repo}/git/refs/heads/main"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"[GitHub] Checking for main branch at {url}...")
                async with session.get(url, headers=headers) as resp:
                    response_text = await resp.text()
                    print(f"[GitHub] Main branch check status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        sha = data["object"]["sha"]
                        print(f"[GitHub] Main branch SHA: {sha}")
                        
                        # Create gh-pages branch from main
                        create_url = f"https://api.github.com/repos/{self.repo}/git/refs"
                        payload = {
                            "ref": "refs/heads/gh-pages",
                            "sha": sha
                        }
                        print(f"[GitHub] Creating gh-pages branch...")
                        async with session.post(create_url, headers=headers, json=payload) as create_resp:
                            create_response_text = await create_resp.text()
                            print(f"[GitHub] Create gh-pages response status: {create_resp.status}")
                            if create_resp.status in (200, 201):
                                print("[GitHub] gh-pages branch created successfully.")
                            else:
                                print(f"[GitHub] Failed to create gh-pages branch: {create_response_text[:300]}")
                    else:
                        print(f"[GitHub] Main branch not found (status {resp.status}). Trying master branch...")
                        # Try master branch
                        url_master = f"https://api.github.com/repos/{self.repo}/git/refs/heads/master"
                        async with session.get(url_master, headers=headers) as resp_m:
                            response_text_m = await resp_m.text()
                            print(f"[GitHub] Master branch check status: {resp_m.status}")
                            if resp_m.status == 200:
                                data = await resp_m.json()
                                sha = data["object"]["sha"]
                                print(f"[GitHub] Master branch SHA: {sha}")
                                
                                create_url = f"https://api.github.com/repos/{self.repo}/git/refs"
                                payload = {
                                    "ref": "refs/heads/gh-pages",
                                    "sha": sha
                                }
                                print(f"[GitHub] Creating gh-pages branch from master...")
                                async with session.post(create_url, headers=headers, json=payload) as create_resp:
                                    create_response_text = await create_resp.text()
                                    print(f"[GitHub] Create gh-pages response status: {create_resp.status}")
                                    if create_resp.status in (200, 201):
                                        print("[GitHub] gh-pages branch created from master.")
                                    else:
                                        print(f"[GitHub] Failed to create gh-pages branch: {create_response_text[:300]}")
                            else:
                                print(f"[GitHub] Neither main nor master branch found. Repository may not have been initialized.")
        except Exception as e:
            print(f"[GitHub] Exception creating gh-pages branch: {e}")
            traceback.print_exc()

    async def _upload_to_github(self, path, content, message):
        print(f"[GitHub] Starting upload attempt for {path}...")
        if not self.token:
            print("[GitHub] ERROR: GITHUB_TOKEN is not set.")
            return
        if not self.repo:
            print("[GitHub] ERROR: GITHUB_REPO is not set.")
            return
        
        # Check if repository exists before attempting upload
        repo_ok = await self._check_repo_exists()
        if not repo_ok:
            print("[GitHub] Skipping upload because repository does not exist or is not accessible.")
            return
        
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        headers = {
            "Authorization": f"token {self.token}", 
            "Accept": "application/vnd.github.v3+json"
        }
        
        print(f"[GitHub] Upload URL: {url}")
        print(f"[GitHub] Branch: {self.branch}")
        print(f"[GitHub] Token length: {len(self.token)} chars")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Get current SHA if file exists
                sha = None
                print(f"[GitHub] Checking if file exists at {url}...")
                async with session.get(url, headers=headers) as resp:
                    response_text = await resp.text()
                    print(f"[GitHub] File check response status: {resp.status}")
                    if resp.status == 200:
                        sha = (await resp.json()).get("sha")
                        print(f"[GitHub] File exists. SHA: {sha}")
                    elif resp.status == 404:
                        print("[GitHub] File does not exist (this is normal for new reports).")
                    else:
                        print(f"[GitHub] Error checking file existence ({resp.status}): {response_text[:200]}")
                
                # 2. Upload/Update
                payload = {
                    "message": message, 
                    "content": base64.b64encode(content.encode() if isinstance(content, str) else content).decode(), 
                    "branch": self.branch
                }
                if sha: 
                    payload["sha"] = sha
                
                print(f"[GitHub] Uploading to branch: {self.branch}...")
                async with session.put(url, headers=headers, json=payload) as resp:
                    response_text = await resp.text()
                    print(f"[GitHub] Upload response status: {resp.status}")
                    if resp.status in (200, 201):
                        print(f"[GitHub] SUCCESS: Uploaded {path} to branch {self.branch}")
                    else:
                        print(f"[GitHub] ERROR: Upload failed ({resp.status}): {response_text[:500]}")
        except Exception as e:
            print(f"[GitHub] CRITICAL EXCEPTION during upload: {e}")
            traceback.print_exc()

# --- COMBAT TRACKER ---
class CombatTracker:
    def __init__(self):
        # Sessions are grouped by channel_id
        # {channel_id: {"is_active": bool, "start_time": float, "last_pulse_time": float, "history": {...}}}
        self.sessions = {} 
        self.lock = asyncio.Lock()
        self.publisher = GitHubPublisher()
        self.pulse_pattern = re.compile(r"\[LIVYLOGS RELAY\] (.+?) \| DMG: (\d+) \| HEAL: (\d+) \| INC: (\d+) \| KD: (\d+) \| TGT: (.+?)(?: \| EVTS: (.+))?$")

    def _get_session(self, channel_id):
        if channel_id not in self.sessions:
            self.sessions[channel_id] = {
                "is_active": False,
                "start_time": 0,
                "last_pulse_time": 0,
                "history": {}
            }
        return self.sessions[channel_id]

    async def add_pulse_from_msg(self, content, channel=None):
        if not channel: return
        match = self.pulse_pattern.match(content)
        if not match: return
        name, dmg, heal, inc, kd, target, evts = match.groups()
        dmg, heal, inc, kd = int(dmg), int(heal), int(inc), int(kd)
        
        async with self.lock:
            now = time.time()
            session = self._get_session(channel.id)
            
            if not session["is_active"]:
                session["is_active"] = True
                session["start_time"] = now
                session["history"] = {}
                await channel.send(f"⚔️ **PvP Combat Session started in this channel!** (Tracking: {name})")
            
            history = session["history"]
            if name not in history: 
                history[name] = {"totals": [], "events": [], "pulses": []}
            
            rel_t = now - session["start_time"]
            
            # Store totals
            history[name]["totals"].append((rel_t, dmg, heal))
            # Store pulse
            history[name]["pulses"].append((rel_t, dmg, heal, target))
            
            # Parse individual events
            if evts:
                for ev_str in evts.split(','):
                    parts = ev_str.split(':', 4)
                    if len(parts) >= 4:
                        try:
                            # Note: relative time in event string is relative to APP start,
                            # but we normalize it to SESSION start if possible.
                            # For simplicity, we'll store it as is and use it for relative offsets.
                            t = float(parts[0]) 
                            etype = parts[1]
                            src = parts[2]
                            tgt = parts[3]
                            label = parts[4] if len(parts) > 4 else ""
                            
                            # Deduplication: Don't add the same event twice
                            # (e.g. if two players see the same KD)
                            is_dup = False
                            for existing in history[name]["events"]:
                                if abs(existing[0] - t) < 0.5 and existing[1] == etype and existing[3] == tgt:
                                    is_dup = True
                                    break
                            
                            if not is_dup:
                                history[name]["events"].append((t, etype, src, tgt, label))
                        except ValueError:
                            continue
            
            session["last_pulse_time"] = now

    async def finalize_combat(self, channel, author_name_override=None, is_test=False, interaction=None):
        """Generate, upload, and share the combat report."""
        print(f"[Report] finalize_combat called (test={is_test})")
        
        try:
            # 1. Start-up checks
            try:
                # Use wait_for instead of asyncio.timeout for Python < 3.11 compatibility
                result = await asyncio.wait_for(
                    self._acquire_lock_and_process(channel, author_name_override, is_test, interaction),
                    timeout=5.0
                )
                author_name = result["author_name"]
                total_dmg = result["total_dmg"]
                total_heal = result["total_heal"]
                total_kd = result["total_kd"]
                html_content = result["html_content"]
            except asyncio.TimeoutError:
                print("[Report] ERROR: Could not acquire lock.")
                if interaction:
                    await interaction.followup.send("❌ Error: Combat data is currently busy.", ephemeral=True)
                return "Lock timeout"
            except Exception as e:
                print(f"[Report] ERROR in lock acquisition: {e}")
                traceback.print_exc()
                if interaction:
                    await interaction.followup.send(f"❌ Error acquiring combat data: {e}", ephemeral=True)
                return f"Lock error: {e}"

            # 3. GitHub Upload with timeout
            report_url = None
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', author_name)
            github_path = f"reports/{'test_' if is_test else ''}{safe_name}_{ts}.html"
            
            print(f"[Report] Uploading to GitHub: {github_path}")
            try:
                await asyncio.wait_for(
                    self.publisher._upload_to_github(
                        github_path, 
                        html_content, 
                        f"{'Test ' if is_test else ''}Combat Report for {author_name}"
                    ),
                    timeout=10.0
                )
                
                # Form URL
                if self.publisher.domain:
                    clean_domain = self.publisher.domain.replace("https://", "").replace("http://", "").strip().strip("/")
                    report_url = f"https://{clean_domain}/{github_path}"
                elif self.publisher.repo and "/" in self.publisher.repo:
                    parts = self.publisher.repo.strip().strip("/").split('/')
                    if len(parts) >= 2:
                        report_url = f"https://{parts[0]}.github.io/{parts[1]}/{github_path}"
                
                if report_url:
                    report_url = report_url.replace(" ", "%20")
                    if not report_url.startswith("http"): report_url = f"https://{report_url}"
                    print(f"[Report] Final URL: {report_url}")
            except asyncio.TimeoutError:
                print("[Report] GitHub upload timed out. Proceeding with attachment.")
            except Exception as e:
                print(f"[Report] GitHub upload error: {e}")
                traceback.print_exc()

            # 4. Final Delivery
            print("[Report] Delivering to Discord...")
            embed = discord.Embed(
                title=f"{'🧪 Test' if is_test else '🏆'} Combat Report: {author_name}",
                description="A tactical breakdown has been generated for the encounter.",
                color=discord.Color.blue() if is_test else discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="⚔️ Damage", value=f"{total_dmg:,}", inline=True)
            embed.add_field(name="💉 Healing", value=f"{total_heal:,}", inline=True)
            embed.add_field(name="💀 KDs", value=str(total_kd), inline=True)

            try:
                # Validate URL before using it in embed
                is_valid_url = False
                if report_url and isinstance(report_url, str):
                    report_url = report_url.strip()
                    # Must start with http:// or https://, contain a dot, and be longer than 12 chars
                    if report_url.startswith(("http://", "https://")) and "." in report_url and len(report_url) > 12:
                        # Further validation: check domain part has a dot and is not empty
                        domain_part = report_url.split("//")[-1].split("/")[0]
                        if "." in domain_part and len(domain_part) > 3:
                            is_valid_url = True
                
                if is_valid_url:
                    embed.url = report_url
                    embed.add_field(name="🌐 Interactive Web View", value=f"**[Open Full Report]({report_url})**", inline=False)
                    if interaction:
                        try:
                            await interaction.followup.send(embed=embed)
                        except discord.NotFound:
                            await channel.send(content=f"{interaction.user.mention} here is your report:", embed=embed)
                    else:
                        await channel.send(embed=embed)
                else:
                    # Check file size before sending as attachment (Discord limit is 25MB)
                    html_bytes = html_content.encode()
                    file_size_mb = len(html_bytes) / (1024 * 1024)
                    if file_size_mb > 24:  # Leave some margin
                        print(f"[Report] HTML file too large ({file_size_mb:.1f}MB). Sending as text message instead.")
                        embed.add_field(name="📎 Report Too Large", value=f"The report is {file_size_mb:.1f}MB which exceeds Discord's attachment limit. Please check the console logs for the report content.", inline=False)
                        if interaction:
                            try:
                                await interaction.followup.send(embed=embed)
                            except discord.NotFound:
                                await channel.send(embed=embed)
                        else:
                            await channel.send(embed=embed)
                    else:
                        file = discord.File(io.BytesIO(html_bytes), filename=f"report_{ts}.html")
                        embed.add_field(name="📎 Attached Report", value="Interactive report is attached (upload skipped/failed).", inline=False)
                        if interaction:
                            try:
                                await interaction.followup.send(embed=embed, file=file)
                            except discord.NotFound:
                                await channel.send(content=f"{interaction.user.mention} here is your report:", embed=embed, file=file)
                        else:
                            await channel.send(embed=embed, file=file)
                print("[Report] Delivery complete.")
            except Exception as send_e:
                print(f"[Report] Final delivery failed: {send_e}")
                if interaction:
                    try:
                        await interaction.followup.send(f"❌ Delivery error: {send_e}")
                    except:
                        pass
            
            return True
        except Exception as e:
            print(f"[Report] CRITICAL ERROR in finalize_combat: {e}")
            traceback.print_exc()
            if interaction:
                try:
                    await interaction.followup.send(f"❌ Critical error generating report: {e}", ephemeral=True)
                except:
                    pass
            return f"Critical error: {e}"

    async def _acquire_lock_and_process(self, channel, author_name_override, is_test, interaction):
        """Helper method to acquire lock and process combat data.
        Returns a dict with author_name, total_dmg, total_heal, total_kd, html_content.
        """
        async with self.lock:
            session = self._get_session(channel.id)
            if not session["is_active"] and not is_test: 
                msg = "No active combat data in this channel. Try `/gd001` for a test report."
                if interaction: await interaction.followup.send(msg, ephemeral=True)
                return {"author_name": None, "total_dmg": 0, "total_heal": 0, "total_kd": 0, "html_content": ""}

            if is_test:
                session["history"] = self._generate_test_history()
                session["start_time"] = time.time()
                session["is_active"] = True
            
            history = session["history"]
            author_name = author_name_override or (list(history.keys())[0] if history else "Unknown Pilot")
            
            # Calculate stats
            total_dmg = 0
            total_heal = 0
            total_kd = 0
            for name, data in history.items():
                if data["pulses"]:
                    total_dmg += sum(p[1] for p in data["pulses"])
                    total_heal += sum(p[2] for p in data["pulses"])
                total_kd += len([e for e in data["events"] if e[1] == "KD"])

            print("[Report] Building HTML...")
            try:
                html_content = await asyncio.wait_for(
                    asyncio.to_thread(self.generate_html_report, session),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print("[Report] HTML generation timed out")
                html_content = "<html><body><h1>Report generation timed out</h1></body></html>"
            except Exception as e:
                print(f"[Report] HTML generation error: {e}")
                html_content = "<html><body><h1>Error generating report</h1></body></html>"
            
            if not is_test:
                session["is_active"] = False
                session["history"] = {}
            print("[Report] Data ready.")
            return {
                "author_name": author_name,
                "total_dmg": total_dmg,
                "total_heal": total_heal,
                "total_kd": total_kd,
                "html_content": html_content
            }

    def _generate_test_history(self):
        """Generate randomized combat data for /gd001."""
        test_history = {}
        players = ["Test_Pilot", "Enemy_Ace", "Support_Droid"]
        for p in players:
            pulses = []
            events = []
            totals = []
            for t in range(0, 60, 5):
                d = random.randint(500, 5000)
                h = random.randint(0, 1000)
                pulses.append((t, d, h, "Target"))
                totals.append((t, d, h))
            
            # Add one KD event
            events.append((30, "KD", p, "Someone", "Heavy Strike"))
            test_history[p] = {"totals": totals, "events": events, "pulses": pulses}
        return test_history

    def generate_html_report(self, session):
        """Generate the interactive HTML report from tracked history."""
        print("[Report] Starting HTML generation...")
        history = session["history"]
        players = list(history.keys())
        max_time = 0
        all_pulses = [] # Collect all pulses for lookup
        for name, data in history.items():
            for t, d, h in data.get("totals", []): max_time = max(max_time, t)
            for t, etype, src, tgt, label in data["events"]: max_time = max(max_time, t)
            for p in data.get("pulses", []):
                all_pulses.append((p[0], name, p[1], p[2], p[3])) # t, name, dmg, heal, tgt
        
        if max_time == 0: max_time = 1
        print(f"[Report] max_time: {max_time}, pulses: {len(all_pulses)}")
        all_pulses.sort(key=lambda x: x[0])
        print("[Report] Pulses sorted.")

        event_classes = {
            "KD": "badge-error", "PD": "badge-warning", "INT": "badge-info",
            "INC": "badge-secondary", "LOOT": "badge-success", "DEATH": "badge-ghost",
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
                :root {{ --starwars-blue: #00ecff; --starwars-red: #ff003c; --starwars-yellow: #ffe81f; --hud-bg: rgba(10, 15, 20, 0.9); }}
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

                <div class="hud-border bg-black/40 rounded-lg p-2 overflow-x-auto overflow-y-visible relative">
                    <div class="swimlane-container" style="height: {len(players) * 180 + 140}px;">
                        <div class="scanline"></div>
                        {"".join([f'<div class="time-line" style="left: {(s/max_time)*100}%; border-left-color: {"rgba(0, 236, 255, 0.15)" if s%10==0 else "rgba(0, 236, 255, 0.05)"};"></div><div class="absolute text-[8px] font-black tracking-tighter text-primary/40" style="left: {(s/max_time)*100}%; top: 20px; transform: translateX(-50%);">{s:03d}</div>' for s in range(0, int(max_time) + 1, 5)])}
        """

        for i, name in enumerate(players):
            print(f"[Report] Processing player {i+1}/{len(players)}: {name}")
            top = 90 + (i * 180)
            data = history[name]
            pulses = data.get("pulses", [])
            max_val = max([p[1] for p in pulses] + [p[2] for p in pulses] + [1])
            
            dmg_pts = " ".join([f"{(p[0]/max_time)*100},{100-(p[1]/max_val*80)}" for p in pulses])
            heal_pts = " ".join([f"{(p[0]/max_time)*100},{100-(p[2]/max_val*80)}" for p in pulses])
            
            hover_rows = {}
            for pt, pd, ph, ptgt in pulses:
                row = hover_rows.setdefault(pt, {"t": pt, "d": 0, "h": 0, "d_sources": {}, "h_sources": {}})
                row["d"] += pd; row["h"] += ph
                if pd > 0: row["d_sources"][ptgt] = row["d_sources"].get(ptgt, 0) + pd
                if ph > 0: row["h_sources"][ptgt] = row["h_sources"].get(ptgt, 0) + ph
            
            hover_payload = []
            for pt in sorted(hover_rows.keys()):
                r = hover_rows[pt]
                hover_payload.append({"t": r["t"], "d": r["d"], "h": r["h"], 
                                      "d_sources": sorted(r["d_sources"].items(), key=lambda x: x[1], reverse=True),
                                      "h_sources": sorted(r["h_sources"].items(), key=lambda x: x[1], reverse=True)})
            
            import html as html_lib
            hover_json = html_lib.escape(json.dumps(hover_payload), quote=True)

            html += f"""
                        <div class="absolute left-0 right-0 h-40 rounded border bg-black/20 flex items-center px-6 backdrop-blur-sm player-row" style="top: {top}px;">
                            <div class="w-60 flex-shrink-0 border-r border-white/10 mr-8 py-2 relative z-20">
                                <span class="text-[8px] font-black opacity-30 uppercase tracking-[0.3em] mb-1 block">Entity Signature</span>
                                <span class="text-lg font-orbitron font-black text-slate-200 truncate block tracking-widest">{name.upper()}</span>
                            </div>
                            <div class="relative flex-grow h-full overflow-visible pr-4">
                                <div class="h-full relative rounded border border-white/10 bg-black/20 overflow-visible">
                                    <svg class="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
                                        <polyline fill="rgba(255, 0, 60, 0.1)" stroke="rgba(255, 0, 60, 0.5)" stroke-width="1" points="0,100 {dmg_pts} 100,100" />
                                        <polyline fill="none" stroke="rgba(0, 255, 150, 0.8)" stroke-width="1" points="0,100 {heal_pts} 100,100" />
                                    </svg>
                                    <div class="graph-hover-layer" data-player="{name}" data-max-time="{max_time}" data-points="{hover_json}">
                                        <div class="graph-crosshair hidden"></div>
                                        <div class="graph-tooltip hidden bg-[#0a0f14] border border-primary/40 px-3 py-2 rounded text-[9px] font-mono shadow-[0_0_30px_rgba(0,236,255,0.2)] min-w-[280px]"></div>
                                    </div>
                                </div>
            """
            
            for t, etype, src, tgt, label in data["events"]:
                badge = event_classes.get(etype, "badge-ghost")
                left = (t / max_time) * 100
                
                # Mini-log for event detail
                # Optimization: use binary search to find the window in all_pulses (which is sorted)
                # Since all_pulses items are (time, name, dmg, heal, tgt), we search for (time,)
                start_time_val = t - 2
                end_time_val = t + 1
                
                # find start index where p[0] >= start_time_val
                low = 0
                high = len(all_pulses)
                while low < high:
                    mid = (low + high) // 2
                    if all_pulses[mid][0] < start_time_val: low = mid + 1
                    else: high = mid
                start_idx = low
                
                # find end index where p[0] > end_time_val
                low = 0
                high = len(all_pulses)
                while low < high:
                    mid = (low + high) // 2
                    if all_pulses[mid][0] <= end_time_val: low = mid + 1
                    else: high = mid
                end_idx = low
                
                window_pulses = all_pulses[start_idx:end_idx]
                
                mini_log = ""
                for pt, pname, pdmg, pheal, ptgt in window_pulses:
                    if pdmg == 0 and pheal == 0: continue
                    mini_log += f'<div class="flex justify-between py-1 border-b border-white/5 text-[9px] {"text-primary" if pname==name else ""}">'
                    mini_log += f'<span class="opacity-40">{pt-t:+.1f}s</span><span class="font-bold">{pname[:10]}</span>'
                    mini_log += f'<span>{"<span class=text-error>-"+str(pdmg)+"</span>" if pdmg>0 else ""} {"<span class=text-success>+"+str(pheal)+"</span>" if pheal>0 else ""}</span></div>'

                ev_json = html_lib.escape(json.dumps({"type": etype, "time": t, "source": src, "target": tgt, "label": label, "mini_log_html": mini_log, "player": name}), quote=True)
                html += f'<div class="event-marker event-clickable" data-event="{ev_json}" style="left: {left}%; top: 50%; margin-top: -14px;"><div class="badge {badge} badge-sm font-black cursor-pointer">{etype}</div></div>'
            
            html += "</div></div>"

        html += f"""
                    </div>
                </div>
                <div class="mt-12 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-[8px] opacity-20">
                    <div>LIVIUS ANALYSIS ENGINE V3.0 // TACTICAL OVERLAY</div>
                    <div>CYCLE TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
            <div class="event-detail-overlay" id="eventDetailOverlay"></div>
            <div class="event-detail-panel hud-border bg-[#0a0f14] rounded-lg p-4" id="eventDetailPanel">
                <div class="flex justify-between items-center mb-3 border-b border-primary/20 pb-2">
                    <div id="eventDetailType" class="text-[9px] font-black text-primary tracking-widest uppercase">Event</div>
                    <button class="btn btn-xs btn-ghost" id="eventDetailClose">Close</button>
                </div>
                <div class="grid grid-cols-2 gap-3 mb-3 text-[10px]">
                    <div class="bg-black/40 p-2 rounded"><div class="opacity-40 mb-1">Source</div><div id="eventDetailSource" class="font-bold"></div></div>
                    <div class="bg-black/40 p-2 rounded"><div class="opacity-40 mb-1">Target</div><div id="eventDetailTarget" class="font-bold"></div></div>
                </div>
                <div id="eventDetailLabel" class="bg-primary/5 p-2 rounded mb-3 text-[10px] italic"></div>
                <div id="eventDetailLog" class="mini-log bg-black/60 rounded p-2"></div>
            </div>
            <script>
                // ... Ported JS from generate_example_report.py (simplified) ...
                const layers = document.querySelectorAll('.graph-hover-layer');
                layers.forEach(l => {{
                    const pts = JSON.parse(l.dataset.points);
                    const maxT = Number(l.dataset.maxTime);
                    const tt = l.querySelector('.graph-tooltip');
                    l.addEventListener('mousemove', e => {{
                        const x = e.clientX - l.getBoundingClientRect().left;
                        const t = (x / l.offsetWidth) * maxT;
                        const s = pts.reduce((prev, curr) => Math.abs(curr.t - t) < Math.abs(prev.t - t) ? curr : prev, pts[0]);
                        tt.classList.remove('hidden'); tt.style.left = x+'px';
                        tt.innerHTML = `<b>T+${{t.toFixed(1)}}s</b><br>DMG: ${{s.d}}<br>HEAL: ${{s.h}}`;
                    }});
                    l.addEventListener('mouseleave', () => tt.classList.add('hidden'));
                }});
                const markers = document.querySelectorAll('.event-clickable');
                markers.forEach(m => m.addEventListener('click', e => {{
                    const p = JSON.parse(m.dataset.event);
                    document.getElementById('eventDetailType').innerText = p.type + ' @ T+' + p.time.toFixed(1) + 's';
                    document.getElementById('eventDetailSource').innerText = p.source;
                    document.getElementById('eventDetailTarget').innerText = p.target;
                    document.getElementById('eventDetailLabel').innerText = p.label;
                    document.getElementById('eventDetailLog').innerHTML = p.mini_log_html;
                    document.getElementById('eventDetailOverlay').classList.add('open');
                    document.getElementById('eventDetailPanel').classList.add('open');
                    document.getElementById('eventDetailPanel').style.left = e.clientX+'px';
                    document.getElementById('eventDetailPanel').style.top = e.clientY+'px';
                }}));
                document.getElementById('eventDetailOverlay').addEventListener('click', () => {{
                    document.getElementById('eventDetailOverlay').classList.remove('open');
                    document.getElementById('eventDetailPanel').classList.remove('open');
                }});
            </script>
        </body></html>
        """
        print("[Report] HTML generation complete.")
        return html

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

@bot.tree.command(name="ping", description="Test if the bot is responsive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 **Pong!** The bot is alive and listening.", ephemeral=True)

@bot.tree.command(name="sync", description="Force sync the bot commands with Discord")
async def sync_cmds(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ Successfully synced {len(synced)} commands with Discord.")
    except Exception as e:
        await interaction.followup.send(f"❌ Sync failed: {e}")

@bot.tree.command(name="testreport", description="Generate a test combat report")
async def test_report_new(interaction: discord.Interaction):
    print(f"[Command] /testreport used by {interaction.user}")
    await interaction.response.defer(ephemeral=True)
    try:
        await bot.tracker.finalize_combat(
            channel=interaction.channel,
            author_name_override="Test_Pilot",
            is_test=True,
            interaction=interaction
        )
    except Exception as e:
        print(f"[Command] /testreport error: {e}")
        await interaction.followup.send(f"❌ Error generating test report: {e}", ephemeral=True)

@bot.tree.command(name="combatreport", description="Generate a manual combat report")
async def manual_report_new(interaction: discord.Interaction):
    print(f"[Command] /combatreport used by {interaction.user}")
    await interaction.response.send_message("📊 **Check your LivyLogs App!** Type `d999` in your game chat to generate a report from your current data.", ephemeral=True)

@bot.tree.command(name="report", description="Generate a combat report from recent data")
async def manual_report(interaction: discord.Interaction):
    # Keep old command but point it to new logic
    await manual_report_new(interaction)

@bot.tree.command(name="gd001", description="Generate a test combat report with randomized data")
async def test_report(interaction: discord.Interaction):
    print(f"[Command] /gd001 used by {interaction.user}")
    await interaction.response.defer(ephemeral=True)
    try:
        await bot.tracker.finalize_combat(
            channel=interaction.channel,
            author_name_override="Test_Pilot",
            is_test=True,
            interaction=interaction
        )
    except Exception as e:
        print(f"[Command] /gd001 error: {e}")
        await interaction.followup.send(f"❌ Error generating test report: {e}", ephemeral=True)

@bot.tree.command(name="reset", description="Clear combat data for this channel")
async def reset_combat(interaction: discord.Interaction):
    async with bot.tracker.lock:
        session = bot.tracker._get_session(interaction.channel_id)
        session["is_active"] = False
        session["history"] = {}
        session["start_time"] = 0
    await interaction.response.send_message("🧹 Combat data cleared for this channel.", ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore our own messages
    if message.author == bot.user:
        return

    # LEGACY COMMANDS (Use these if slash commands are stuck "thinking")
    content = message.content.lower().strip()
    
    if content == "!gd001":
        print(f"[Legacy] !gd001 used by {message.author}")
        await message.channel.send("🧪 **Type `dg001` in your game chat** to generate a test report from the app.")
        return

    if content == "!report":
        print(f"[Legacy] !report used by {message.author}")
        await message.channel.send("📊 **Type `d999` in your game chat** to generate a combat report from the app.")
        return

    if content == "!reset":
        print(f"[Legacy] !reset used by {message.author}")
        async with bot.tracker.lock:
            session = bot.tracker._get_session(message.channel.id)
            session["is_active"] = False
            session["history"] = {}
            session["start_time"] = 0
        await message.channel.send("🧹 Combat data cleared (Legacy Reset).")
        return

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Please set DISCORD_BOT_TOKEN environment variable.")
