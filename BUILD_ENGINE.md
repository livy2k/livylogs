### Building the Obfuscated Log Engine

To protect the `log_engine.exe` from being easily decompiled or tampered with, I have created an obfuscated source file: `log_engine.c`. This file hides all sensitive strings (like the pipe name and combat keywords) using XOR encryption.

#### 1. How to Compile
You will need a C compiler installed on your machine (like MSVC, GCC, or via CLion).

**Using Microsoft Visual C++ (Developer Command Prompt):**
```cmd
cl /O2 /Fe:log_engine.exe log_engine.c kernel32.lib user32.lib
```

**Using GCC (MinGW/Cygwin):**
```bash
gcc -O2 -o log_engine.exe log_engine.c -lkernel32 -luser32
```

#### 2. Additional Obfuscation (Optional but Recommended)
For even better protection, you can "pack" the resulting `.exe` using **UPX**. This compresses the file and makes it much harder to read without a debugger.

1.  Download UPX from [upx.github.io](https://upx.github.io/).
2.  Run the following command:
    ```bash
    upx --best log_engine.exe
    ```

#### 3. Deployment
Once you have built the new `log_engine.exe`, simply replace the existing one in your project folder. The Python app will automatically detect it and use the new obfuscated version.

### What was changed in the source?
- **String Encryption**: All internal strings (Pipe Name, "points of damage", "looted") are now stored as encrypted byte arrays and only decrypted in memory during execution.
- **Symbol Obfuscation**: Variable names and functions have been simplified to make the logic less obvious to reverse engineers.
- **No Static Keywords**: No readable text is left in the binary for tools like `strings.exe` to find.
