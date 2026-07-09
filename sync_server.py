from flask import Flask, request, jsonify
import time
import threading

app = Flask(__name__)

# Storage for combat data
# Format: { character_name: { "timestamp": float, "data": { ... } } }
combat_store = {}

# Time in seconds before data is considered stale and removed
STALE_TIMEOUT = 60 

# Secret key required for authentication
# Set this to match your app's internal key for automatic connection
SECRET_KEY = "LivyLogs_Auto_Sync_v1"

@app.route('/sync', methods=['POST'])
def sync_data():
    try:
        payload = request.json
        if not payload or 'character' not in payload or 'data' not in payload:
            return jsonify({"error": "Invalid payload"}), 400

        # Verify key
        if payload.get('key') != SECRET_KEY:
            return jsonify({"error": "Unauthorized"}), 401

        char_name = payload['character']
        
        # Update store with latest data from this character
        combat_store[char_name] = {
            "timestamp": time.time(),
            "data": payload['data']
        }

        # Cleanup stale data
        now = time.time()
        stale_chars = [c for c, data in combat_store.items() if now - data['timestamp'] > STALE_TIMEOUT]
        for c in stale_chars:
            del combat_store[c]

        # Prepare aggregated response
        # We need to merge stats for damage, healing, and loot
        merged = {
            "damage": {},
            "healing": {},
            "loot": {}
        }

        for c, entry in combat_store.items():
            char_data = entry['data']
            
            # Merge Damage
            for p, val in char_data.get('damage', {}).items():
                merged['damage'][p] = max(merged['damage'].get(p, 0), val)
            
            # Merge Healing
            for p, val in char_data.get('healing', {}).items():
                merged['healing'][p] = max(merged['healing'].get(p, 0), val)
            
            # Merge Loot
            for p, items in char_data.get('loot', {}).items():
                if p not in merged['loot']:
                    merged['loot'][p] = []
                # Simple merge of loot lists, avoiding exact duplicates if they have the same timestamp
                existing_timestamps = { (i.get('item'), i.get('timestamp')) for i in merged['loot'][p] }
                for item in items:
                    if (item.get('item'), item.get('timestamp')) not in existing_timestamps:
                        merged['loot'][p].append(item)
                # Keep only last 50 loot items per player to avoid massive payloads
                merged['loot'][p] = sorted(merged['loot'][p], key=lambda x: x.get('timestamp', 0), reverse=True)[:50]

        return jsonify({
            "status": "success",
            "count": len(combat_store),
            "data": merged
        })

    except Exception as e:
        print(f"Error in sync: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
