import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(current_dir, "livylogs.py")
    
    if os.path.exists(target_script):
        # Execute livylogs.py with the same arguments
        cmd = [sys.executable, target_script] + sys.argv[1:]
        subprocess.run(cmd)
    else:
        print(f"Error: {target_script} not found.")
        sys.exit(1)
