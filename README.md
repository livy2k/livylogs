# LivyLogs - Combat Log Parser

A lightweight, real-time combat log parser for Star Wars Galaxies (SWG). This application provides a themed overlay with damage meters, loot tracking, and detailed player analysis.

## ✨ Features

- **Real-time Damage Meter:** Track your DPS and total damage output.
- **Leaderboards:** See how players rank during your session.
- **Loot Tracker:** Keep a history of items looted in the last 30 minutes.
- **Detailed Analytics:** View specific logs for individual players, including damage taken and healing.
- **Customizable UI:** 
    - Adjust opacity/transparency for the perfect overlay.
    - Snap windows together for a clean layout.
    - Independent options window.
- **Audio Notifications:** Plays a sound when important notices appear.

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- `tkinter` (usually included with Python)

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/livylogs.git
   ```
2. Navigate to the directory:
   ```bash
   cd livylogs
   ```
3. Run the application:
   ```bash
   python combat_log_parser_app.py
   ```

## 🛠 Usage

1. **Select Log File:** Click the "SELECT LOG FILE" button in the settings and point it to your SWG combat log (usually found in your game directory's `logs` folder).
2. **Auto-Tracking:** The app will automatically detect when the game window is active and start parsing new entries.
3. **Overlay Mode:** Use the opacity slider to make the window semi-transparent so it can sit over your game client.
4. **Resetting:** Use the "RESET DATA" button to clear current session stats.

## 📦 Distribution
To package this as a standalone `.exe` for Windows, use PyInstaller:
```bash
pyinstaller Livylogs.spec
```

## 📄 License
This project is for personal use and educational purposes.
