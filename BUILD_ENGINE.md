### Building the Obfuscated Log Engine

To protect the `parser.exe` from being easily decompiled or tampered with, I have created an obfuscated source file: `parser.c`. This file hides all sensitive strings (like the pipe name and combat keywords) using XOR encryption.

#### 1. How to Compile
You must use **CLion**'s bundled toolchain for compilation to ensure consistency and availability of the required environment.

**Using CLion's bundled MinGW (via PowerShell):**
```powershell
# Add CLion MinGW to PATH for the session
$env:PATH = "C:\Program Files\JetBrains\CLion 2026.1.4\bin\mingw\bin;" + $env:PATH
# Compile (using -mwindows for background mode)
gcc -O2 -mwindows -o parser.exe parser.c -lkernel32 -luser32 -lgdi32 -lshell32
```

#### 2. Additional Obfuscation (Optional but Recommended)
For even better protection, you can "pack" the resulting `.exe` using **UPX**. This compresses the file and makes it much harder to read without a debugger.

1.  Download UPX from [upx.github.io](https://upx.github.io/).
2.  Run the following command:
    ```bash
    upx --best parser.exe
    ```

#### 3. Deployment
Once you have built the new `parser.exe`, simply replace the existing one in your project folder. The Python app will automatically detect it and use the new obfuscated version.

### What was changed in the source?
- **Enhanced String Encryption**: All internal strings (Pipe Name, window names, combat keywords, and JSON keys) are now stored as encrypted byte arrays and only decrypted in memory during execution.
- **Symbol Obfuscation**: Function names (`main` excepted) and internal variable names have been replaced with non-descriptive, short identifiers (e.g., `u_v` for `update_visibility`, `s_e` for `send_event`) to hinder reverse engineering.
- **Dynamic Decryption**: Strings are decrypted into local buffers and cleared after use, minimizing the window of exposure in memory.
- **No Static Keywords**: No readable text related to the application's logic or communication protocol remains in the binary.
