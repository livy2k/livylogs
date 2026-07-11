# LivyLogs - Combat Log Parser

A lightweight, real-time combat log parser for Star Wars Galaxies (SWG). This application provides a themed overlay with damage meters, loot tracking, and detailed player analysis.

## ✨ Features

- **Real-time Damage Meter:** Track your DPS and total damage output.
- **Unified Leaderboard:** A single, top-level display showing player rankings with Name, Damage, and Healing columns.
- **Seamless Drill-down:** Click any player in the leaderboard to view their detailed combat logs (Damage Dealt, Taken, Healing, XP, Kills) directly in the same window.
- **Loot Tracker:** Keep a history of items looted for the entire session.
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
   parser.exe
   ```
   *Note: Previously, you would run `python livylogs.py`, but now the C engine (`parser.exe`) is the main entry point and manages the UI windows.*

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

## 📄 Development & Architecture
For details on the latest architectural changes (Flow Inversion), build instructions using CLion/MinGW, and internal logic, see:
- [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
- [BUILD_ENGINE.md](BUILD_ENGINE.md)

## 📄 License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for the full text.
