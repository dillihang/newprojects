import os
import subprocess
from pathlib import Path
from datetime import datetime
import psutil
import time
from contextlib import redirect_stdout


def windows_memory_info(output_folder: str):
    """
    Takes a single snapshot of system memory usage and high-memory processes
    and appends the results to a log file.

    The function does NOT loop by itself — it is intended to be called
    repeatedly by an external scheduler or timer.
    """
    system_dict = {}
    top_list = []

    # ---- Get running tasks ----
    result = subprocess.run(["tasklist"], capture_output=True, text=True)

    for line in result.stdout.splitlines()[4:]:
        parts = line.split()
        if len(parts) >= 5:
            try:
                memory = int(parts[4].replace(",", ""))
                if memory >= 100000:
                    top_list.append(f"{parts[0]} {parts[2]} {memory/1024:.2f} MB")
            except ValueError:
                continue

    # ---- Get memory info ----
    memory = psutil.virtual_memory()
    total = (f"Total: {memory.total / (1024 ** 3):.2f} GB")
    available = (f"Available: {memory.available / (1024 ** 3):.2f} GB")
    used = (f"Used: {memory.used / (1024 ** 3):.2f} GB")

    system_dict["memory_INFO"] = f"{total}, {available}, {used}"
    system_dict["services"] = sorted(
        top_list,
        key=lambda x: float(x.split()[2]),
        reverse=True
    )

    # ---- Write to log ----
    os.makedirs(output_folder, exist_ok=True)
    file_name = "periodic_memory_log.txt"
    output_path = os.path.join(output_folder, file_name)

    with redirect_stdout(open(output_path, "a")):
        print("===== MEMORY SNAPSHOT =====")
        print()

        print("memory_INFO")
        print(system_dict["memory_INFO"])
        print()

        print("High memory using services:")
        for line in system_dict["services"]:
            print(line)

        print()
        print(f"Recorded at: {datetime.today().strftime("%d-%m-%Y_%H-%M-%S")}")
        print("\n")


if __name__ == "__main__":

    destination = "Newprojects/AutomationScripting/process_log"

    # ---- Loop outside the function ----
    for i in range(5):
        windows_memory_info(destination)
        time.sleep(5)
