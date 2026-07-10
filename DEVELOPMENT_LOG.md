# Development Log - LivyLogs

## Major Change: Application Flow Inversion (2026-07-09)
Previously, the Python script (`livylogs.py`) was the entry point and launched `parser.exe`. We have inverted this flow.

### New Architecture
- **Entry Point**: `parser.exe` (compiled from `parser.c`).
- **Control**: `parser.exe` now launches `python livylogs.py`.
- **Window Management**: `parser.exe` handles showing/hiding all Python UI windows based on whether the game window ("SwgClient") is in focus or minimized.
- **Python Role**: `livylogs_main.py` has its internal `check_target_window` loop disabled to avoid conflicting with the C engine's window management.

### C-Powered Combat Engine & Obfuscation (2026-07-09)
- **State Offloading**: Significant portions of combat state management (DPS, HPS, AOE detection, loot counts) have been moved to the C engine (`parser.exe`).
- **Performance**: Python now receives pre-aggregated state snapshots via IPC, drastically reducing CPU usage for `process_events_for_ui`.
- **Window Management**: Window visibility, focus tracking, and "Always on Top" enforcement are now handled entirely by the C controller.
- **Enhanced Security**:
    - All sensitive strings (window names, combat triggers, JSON keys) are XOR-encrypted in the binary.
    - All internal functions and non-public variables use obfuscated, short identifiers (e.g., `u_v`, `s_e`, `a_o_t`).
    - Strings are decrypted only in local memory buffers during use.

### Build Instructions (CLion / MinGW)
To compile the `parser.exe` using the tools provided by CLion:
1. Open a terminal (PowerShell or Command Prompt).
2. Set the PATH to include the CLion MinGW bin directory:
   ```cmd
   set PATH=C:\Program Files\JetBrains\CLion 2026.1.4\bin\mingw\bin;%PATH%
   ```
3. Run the GCC compilation command:
   ```cmd
   gcc -O2 -o parser.exe parser.c -lkernel32 -luser32
   ```

### Files Involved
- `parser.c`: The C source code for the engine.
- `parser.exe`: The compiled binary.
- `livylogs_main.py`: The main Python logic (window management modified).
- `livylogs.py`: The Python entry script (launched by C).

## Summary of C Engine Logic
- XOR-obfuscated strings to hide logic from static analysis.
- Multi-threaded: One thread handles the combat log pipe, the main thread handles window visibility.
- Automatically detects "SwgClient" or "Star Wars Galaxies" windows.
- Automatically controls visibility of popout windows: "Damage Meter", "Leaderboard", "Skimmers", etc.
