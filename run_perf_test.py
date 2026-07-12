import tkinter as tk
import time
import os
import sys
import psutil
import json
import threading

# Add current dir to path to import app
sys.path.append(os.getcwd())

from livylogs_main import CombatLogApp

class PerfTestRunner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide root during setup
        self.app = CombatLogApp(self.root)
        self.results = {}

    def run_test(self, duration=15):
        print(f"Running performance test for {duration}s...")
        
        process = psutil.Process(os.getpid())
        cpu_usages = []
        mem_usages = []
        ui_refresh_times = []
        
        # Monkey patch refresh_ui_only to measure execution time
        original_refresh = self.app.refresh_ui_only
        def timed_refresh(*args, **kwargs):
            start = time.perf_counter()
            res = original_refresh(*args, **kwargs)
            end = time.perf_counter()
            ui_refresh_times.append((end - start) * 1000) # ms
            return res
        self.app.refresh_ui_only = timed_refresh

        stop_event = threading.Event()
        
        def monitor():
            while not stop_event.is_set():
                cpu_usages.append(process.cpu_percent(interval=0.2))
                mem_usages.append(process.memory_info().rss / (1024 * 1024))

        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()

        # Force high-frequency updates and stress the dot matrix
        if hasattr(self.app, 'radio_mgr'):
            self.app.radio_mgr.is_playing = True
            # Static name to test content-check optimization
            self.app.radio_mgr.current_song_name = "STRESS TEST" 
            self.app.radio_mgr.current_station = "STATION"

        # Static artwork
        def art_stresser():
            from PIL import Image
            import io
            dummy_img = Image.new('RGB', (50, 50), color = 'red')
            buf = io.BytesIO()
            dummy_img.save(buf, format='PNG')
            art_data = buf.getvalue()
            
            while not stop_event.is_set():
                if hasattr(self.app, 'radio_mgr'):
                    # Only set once or infrequently to test caching
                    if not getattr(self.app.radio_mgr, 'current_art_data', None):
                        self.app.radio_mgr.current_art_data = art_data
                        self.app.radio_mgr.art_changed = True
                time.sleep(2)

        stress_thread = threading.Thread(target=art_stresser)
        stress_thread.start()

        # Static Volume
        def vol_stresser():
            while not stop_event.is_set():
                # No changes to volume to test idle state
                time.sleep(1)

        vol_thread = threading.Thread(target=vol_stresser)
        vol_thread.start()

        start_time = time.time()
        # Run the main loop for the specified duration
        while time.time() - start_time < duration:
            # We want to measure the ticker loop too
            self.app.refresh_ui_only() # Explicitly call it to stress test
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.033) # ~30 FPS cap (more realistic for this app)

        stop_event.set()
        stress_thread.join()
        vol_thread.join()
        monitor_thread.join()

        avg_cpu = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
        max_cpu = max(cpu_usages) if cpu_usages else 0
        avg_mem = sum(mem_usages) / len(mem_usages) if mem_usages else 0
        avg_ui_ms = sum(ui_refresh_times) / len(ui_refresh_times) if ui_refresh_times else 0
        max_ui_ms = max(ui_refresh_times) if ui_refresh_times else 0

        self.results = {
            "avg_cpu_percent": round(avg_cpu, 2),
            "max_cpu_percent": round(max_cpu, 2),
            "avg_mem_mb": round(avg_mem, 2),
            "avg_ui_refresh_ms": round(avg_ui_ms, 3),
            "max_ui_refresh_ms": round(max_ui_ms, 3),
            "refreshes_captured": len(ui_refresh_times)
        }
        
        print("Test complete.")
        print(json.dumps(self.results, indent=4))
        
        with open("perf_test_results.json", "w") as f:
            json.dump(self.results, f, indent=4)

        self.root.destroy()

if __name__ == "__main__":
    # Ensure we don't crash due to missing assets if running in restricted env
    try:
        runner = PerfTestRunner()
        runner.run_test(duration=10)
    except Exception as e:
        print(f"Error during perf test: {e}")
        import traceback
        traceback.print_exc()
