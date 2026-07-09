# Transitioning LivyLogs to Overwolf

This guide outlines the architecture and steps required to migrate the Python-based LivyLogs application to the Overwolf platform as a native overlay plugin.

## 1. Architecture Overview

An Overwolf app consists of two main parts:
1.  **UI Layer (Web-based):** Built using HTML, CSS, and TypeScript (React is recommended). This replaces the current Tkinter UI.
2.  **Logic Layer (Plugin-based):** Since Overwolf runs in a Chromium environment, heavy file I/O or system-level tasks require a **.NET 4.5+ Plugin** or a **Process Manager** to run external executables.

### Integration Strategy for LivyLogs:
*   **The UI:** Use TypeScript/React for the overlays (Damage Meter, Leaderboard, etc.).
*   **The Engine:** Continue using `log_engine.exe` as the primary log harvester. Overwolf's **Process Manager Plugin** will launch and manage this process.
*   **The Parser:** Port the `parser_engine.py` logic to TypeScript (preferred for responsiveness) or a C#/.NET plugin (if complex math/regex performance is critical).

---

## 2. Component Migration

### UI Windows to Overwolf Windows
Overwolf handles window management via `manifest.json`. You will map your current windows to declared Overwolf windows:

| Python Window | Overwolf Window Type | Purpose |
| :--- | :--- | :--- |
| `MainWindow` | `background` / `desktop` | App controller and settings. |
| `DamageMeter` | `overlay` | Personal stats (Locked to game). |
| `Leaderboard` | `overlay` | Group rankings and targets. |
| `Skimmers` | `overlay` | Loot and system logs. |

### Log Harvesting (The C Engine)
Overwolf apps cannot directly "listen" to pipes as easily as Python can. You have two options:
1.  **Process Manager:** Launch `log_engine.exe` and have it write to a temporary JSON file or a local WebSocket. Overwolf can then read this file using the `overwolf.io` API.
2.  **Native Plugin:** Re-write the C logic into a .NET DLL that uses `NamedPipeClientStream` to talk to the engine, exposing events directly to JavaScript.

---

## 3. Recommended Tech Stack

*   **Frontend:** React + TypeScript (for strong typing of combat events).
*   **Styling:** Tailwind CSS (matches the "Dark/Cyber" theme easily).
*   **Build Tools:** Webpack or Vite (to bundle the app for Overwolf).
*   **API:** Overwolf SDK (to handle window positioning and game focus).

---

## 4. Step-by-Step Migration Path

### Step 1: Initialize the Project
Download the [Overwolf Sample App](https://github.com/overwolf/sample-app-ts) and configure the `manifest.json`. Set the `game_ids` to Star Wars Galaxies.

### Step 2: Implement File I/O
Use the [Simple I/O Plugin](https://github.com/overwolf/overwolf-simple-io-plugin) to detect and read the SWG combat log files. This replaces the `os.path` and `polling` logic in Python.

### Step 3: Launch the C Engine
Use the [Process Manager Plugin](https://github.com/overwolf/process-manager-plugin) to start `log_engine.exe`.
```javascript
overwolf.extensions.current.getExtraObject("process-manager", (result) => {
    if (result.status === "success") {
        const processManager = result.object;
        processManager.launchProcess("log_engine.exe", "path_to_log.txt", (res) => {
            console.log("C Engine Started");
        });
    }
});
```

### Step 4: Port the Parser
The regex logic in `parser_engine.py` can be moved to a TypeScript service. This allows for instant UI updates without crossing the Python/JS bridge.

---

## 5. Why Move to Overwolf?

*   **Official Overlay Support:** No more fighting with `topmost` and "Windowed Mode" issues. Overwolf handles the DirectX/Vulkan injection perfectly.
*   **Auto-Updates:** Overwolf manages the distribution and updates of your app.
*   **Hardware Acceleration:** Chromium's rendering is significantly smoother than Tkinter for high-frequency data updates.
*   **Game Events:** Overwolf can detect when the game starts/stops and handle window visibility automatically.

---

*Note: This transition requires moving from Python to TypeScript/C#. The core C engine (`log_engine.exe`) remains your "secret sauce" and can be reused directly.*
