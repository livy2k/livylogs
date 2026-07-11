
import psutil
import time
import subprocess
import os
import json
import threading
import ctypes
import sys
from datetime import datetime

# Performance monitoring settings
TEST_DURATION = 300 # 5 minutes
SAMPLE_INTERVAL = 5 # seconds
LOG_PIPE = r"\\.\pipe\LivyLogsPipe"

def get_process_by_name(name):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'].lower() == name.lower():
            return proc
    return None

def send_event(h, event):
    j = json.dumps(event) + "\n"
    data = j.encode('utf-8')
    bytes_written = ctypes.c_ulong(0)
    ctypes.windll.kernel32.WriteFile(h, data, len(data), ctypes.byref(bytes_written), None)

def simulate_load(stop_event):
    """Simulates high event traffic to stress the app."""
    # Wait for pipe to be available
    h = -1
    while not stop_event.is_set() and h == -1:
        if ctypes.windll.kernel32.WaitNamedPipeW(LOG_PIPE, 1000):
            h = ctypes.windll.kernel32.CreateFileW(LOG_PIPE, 0x40000000, 0, None, 3, 0, None)
        if h == -1:
            time.sleep(1)
            
    if h == -1: return

    players = ["You", "Eliemau", "Fikiosa", "Ma-o", "Leloglo", "Turd", "Rehote", "Rancor"]
    npcs = ["Stormtrooper", "Rebel Col", "Krayt Drag", "Imperial S", "Rebel Major General"]
    abilities = ["Melee", "Power Shot", "Force Crush", "Laser Blast", "Quick Shot"]
    
    count = 0
    try:
        while not stop_event.is_set():
            # Send periodic bursts
            for _ in range(5):
                p = players[count % len(players)]
                t = npcs[count % len(npcs)]
                dmg = 100 + (count % 900)
                
                # Dealt
                send_event(h, {"type": "dealt", "source": p, "target": t, "damage": dmg, "ability": abilities[count % len(abilities)]})
                # Taken
                send_event(h, {"type": "taken", "source": t, "target": p, "damage": dmg // 2, "ability": "Attack"})
                # Stats (periodic)
                if count % 10 == 0:
                    send_event(h, {"type": "stats", "name": p, "damage": dmg * 100, "healing": 0, "taken": dmg * 10})
                
                count += 1
            time.sleep(0.5) # Moderate frequency
    finally:
        ctypes.windll.kernel32.CloseHandle(h)

def main():
    print(f"Starting performance test for {TEST_DURATION} seconds...")
    
    # 1. Start the app
    app_proc = subprocess.Popen([sys.executable, "livylogs.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(5) # Give it time to start
    
    # Identify processes
    python_proc = psutil.Process(app_proc.pid)
    # The engine parser.exe should be started by the app
    engine_proc = None
    for _ in range(10):
        engine_proc = get_process_by_name("parser.exe")
        if engine_proc: break
        time.sleep(1)
    
    if not engine_proc:
        print("Warning: parser.exe not found.")

    # 2. Start simulation thread
    stop_sim = threading.Event()
    sim_thread = threading.Thread(target=simulate_load, args=(stop_sim,))
    sim_thread.start()
    
    # 3. Monitor
    data = []
    start_time = time.time()
    try:
        while time.time() - start_time < TEST_DURATION:
            sample = {
                "timestamp": time.time() - start_time,
                "py_cpu": python_proc.cpu_percent(interval=None),
                "py_ram": python_proc.memory_info().rss / (1024 * 1024),
                "en_cpu": engine_proc.cpu_percent(interval=None) if engine_proc and engine_proc.is_running() else 0,
                "en_ram": engine_proc.memory_info().rss / (1024 * 1024) if engine_proc and engine_proc.is_running() else 0
            }
            data.append(sample)
            print(f"[{int(sample['timestamp'])}s] CPU: {sample['py_cpu'] + sample['en_cpu']:.1f}% | RAM: {sample['py_ram'] + sample['en_ram']:.1f}MB")
            time.sleep(SAMPLE_INTERVAL)
    finally:
        stop_sim.set()
        sim_thread.join()
        
        # Kill the app
        app_proc.terminate()
        if engine_proc:
            try: engine_proc.terminate()
            except: pass
            
    # Save raw data
    with open("perf_results.json", "w") as f:
        json.dump(data, f)
    
    print("Performance data collection complete.")

if __name__ == "__main__":
    main()
