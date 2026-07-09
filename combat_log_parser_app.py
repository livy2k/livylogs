import subprocess
import sys
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(current_dir, "livylogs.py")
    if os.path.exists(target_script):
        subprocess.run([sys.executable, target_script] + sys.argv[1:])
    else:
        print(f"Error: {target_script} not found.")
        sys.exit(1)
