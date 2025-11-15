import os
import subprocess
from datetime import datetime

def system_process():
    if os.name == "nt":
        command = ["tasklist"]
    else:
        command = ["ps", "-aux"]

    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def save_output(result: str):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = "Newprojects/AutomationScripting/process_log"
    if not os.path.exists(file_path):
        os.mkdirs(file_path, exist_ok=True)
    file_name = f"process_log_{timestamp}.txt"
    new_path = os.path.join(file_path, file_name)

    with open(new_path, "w") as file:
        file.write(result)


if __name__ == "__main__":

    result = system_process()
    save_output(result)