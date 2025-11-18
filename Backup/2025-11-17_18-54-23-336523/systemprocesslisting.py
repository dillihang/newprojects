import os
import subprocess
from datetime import datetime
"""
System Process Logger

This module retrieves a list of running system processes (Windows or Linux/macOS)
and saves the output to a timestamped log file.
"""
def system_process():
    """
    Retrieve a list of running system processes using the appropriate
    platform command.

    Returns:
        str: The raw output of the process list command.

    Notes:
        - Windows uses 'tasklist'
        - Linux/macOS use 'ps -aux'
        - The function returns the full text output for further processing.
    """
    if os.name == "nt":
        command = ["tasklist"]
    else:
        command = ["ps", "-aux"]

    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def save_output(result: str):
    """
    Save the system process output to a timestamped text log file.

    Parameters:
        result (str): The text output from the system_process() function.

    Notes:
        - Creates the destination folder if it does not exist.
        - File will be named using:
            process_log_YYYY-MM-DD_HH-MM-SS.txt
    """
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