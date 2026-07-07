import psutil
import time
import logging

def monitor_resources(interval=60):
    """
    Monitor system resources such as CPU, memory, and disk usage.
    Args:
        interval (int): Time in seconds between each resource check.
    """
    logging.basicConfig(filename="monitoring.log", level=logging.INFO, format="%(asctime)s - %(message)s")
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        logging.info(f"CPU Usage: {cpu_usage}% | Memory: {memory.percent}% | Disk Usage: {disk.percent}%")
        time.sleep(interval)

if __name__ == "__main__":
    monitor_resources()
