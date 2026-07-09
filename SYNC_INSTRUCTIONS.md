# LivyLogs Web Sync Instructions

This document provides a comprehensive guide to setting up and using the automated web synchronization system for LivyLogs.

## 1. Overview
The Web Sync system allows multiple LivyLogs users to share combat, healing, and loot data in real-time. The application sends local stats to a central hub (the Sync Server), which aggregates the data and broadcasts it back to all connected apps.

## 2. Server Setup (VPS)
To host the sync hub, you need a server running Python.

### Requirements
- Python 3.x
- Flask (`pip install flask`)
- Gunicorn (Recommended for production: `pip install gunicorn`)

### Deployment
1. Upload `sync_server.py` to your server.
2. Run the server using Gunicorn for stability:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 sync_server:app
   ```
3. (Optional but Recommended) Set up Nginx and Let's Encrypt (Certbot) to enable HTTPS encryption.

## 3. Security & Encryption
- **Automatic Authentication**: The app and server use a built-in internal key (`LivyLogs_Auto_Sync_v1`) to verify data integrity automatically.
- **Transport Security**: If you use an `https://` URL, all data is encrypted during transit using TLS 1.2/1.3.
- **Secret Keys**: You can optionally set a custom "SECRET KEY" in the app settings. If set, the server must also be updated with the same key in its `SECRET_KEY` variable.

## 4. App Configuration
In the LivyLogs **SETTINGS** menu:
1. **API URL**: Enter your server address (e.g., `https://your-server.com/sync`).
2. **CHARACTER NAME**: Should be auto-detected, but ensures "You" is correctly identified to others.
3. **ENABLE SYNC**: Toggle to **ON**.
4. **SECRET KEY**: Leave blank for automatic security, or enter a custom group key.

## 5. Seamless Functionality
- **Sync Cadence**: Updates occur every 15 seconds in the background.
- **Automatic Merging**: Data is merged on the server. The Leaderboard and Skimmers (Loot) windows will automatically display combined group data.
- **Persistence**: Your settings are saved to `settings.ini` and will be restored automatically every time you start the app.

## 6. VPS vs Cloud Hosting
Choosing between a VPS and Cloud Hosting (Serverless) depends on your budget and technical expertise.

### VPS (e.g., DigitalOcean, Linode)
- **Pros**: Predictable monthly cost, full control over the environment, easy to debug.
- **Cons**: You must manage security updates, SSL certificates, and scaling manually.
- **Verdict**: Best for small-to-medium groups where you want a simple "set and forget" server.

### Cloud Hosting (e.g., AWS Lambda, Google Cloud Run)
- **Pros**: Extremely robust, scales automatically to thousands of users, high security, pay-only-for-what-you-use (often free for low traffic).
- **Cons**: More complex to set up initially, costs can spike if traffic is massive.
- **Verdict**: Best for large-scale deployments or if you want "enterprise-grade" reliability.

## 7. VPS Resource Estimates (for 500 users)
- **RAM**: 2 GB (Recommended for 500+ users).
- **CPU**: 1-2 vCPUs.
- **Bandwidth**: ~100 GB/month.
- **Storage**: Negligible (data is stored in memory).

## 8. Proximity Filtering
To keep the experience clean and fair, the app uses **Proximity Filtering**:
- **Loot**: Shared globally across everyone using the same API.
- **Damage/Healing**: Only displayed for other players if your app has seen them "locally" in combat recently. This ensures you only see stats for people you are actually playing with.
