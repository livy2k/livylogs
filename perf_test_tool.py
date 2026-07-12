import time
import psutil
import os
import threading
import json

def measure_performance(duration=10):
    process = psutil.Process(os.getpid())
    cpu_usages = []
    mem_usages = []
    
    start_time = time.time()
    while time.time() - start_time < duration:
        cpu_usages.append(process.cpu_percent(interval=0.5))
        mem_usages.append(process.memory_info().rss / (1024 * 1024)) # MB
        
    avg_cpu = sum(cpu_usages) / len(cpu_usages)
    max_cpu = max(cpu_usages)
    avg_mem = sum(mem_usages) / len(mem_usages)
    max_mem = max(mem_usages)
    
    return {
        "avg_cpu": avg_cpu,
        "max_cpu": max_cpu,
        "avg_mem": avg_mem,
        "max_mem": max_mem,
        "duration": duration
    }

if __name__ == "__main__":
    print("Starting performance measurement...")
    # This script is intended to be imported or run alongside the main app.
    # For standalone test, we just measure itself.
    results = measure_performance(duration=5)
    print(json.dumps(results, indent=4))
