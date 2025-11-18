import os
import getpass
import shutil
import platform
from datetime import datetime
import string
import psutil


def get_all_drives():
    """
    Detect all available drive letters on a Windows system.

    Returns:
        list[str]: A list of drive paths such as ['C:', 'D:', ...].

    Notes:
        - On non-Windows systems, this will return an empty list.
        - Uses A–Z and checks which ones actually exist on the system.
    """
    drive_list = []

    for letter in string.ascii_uppercase:
        drive_name = f"{letter}:"
        if os.path.exists(drive_name):
            drive_list.append(drive_name)
    
    return drive_list

def get_system_info():
    """
    Collect a structured dictionary of system information.

    Returns:
        dict: A dictionary containing:
            - Operating system name, release, version
            - CPU architecture and core count
            - Current username
            - Disk usage for each detected drive
            - RAM statistics (total, used, available, %)
            - Python version
            - Timestamp of the report

    Behavior:
        - Uses platform, psutil, os, and shutil to gather system data.
        - Formats sizes in gigabytes to 2 decimal places.
        - Adds drive info only if drives are detected.
    """
    info = {}
    drives_dict = {}

    info["os"] = platform.system()
    info["os_release"] = platform.release()
    info["os_version"] = platform.version()
    info["cpu_arch"] = platform.processor()
    info["username"] = getpass.getuser()
    info["CPU"] = os.cpu_count()
    
    all_drives = get_all_drives()
    if all_drives:
        for drives in all_drives:
            drives_dict[drives] = shutil.disk_usage(drives)
    
    for drive_name, details in drives_dict.items():
        drive_key = f"{drive_name} drive details"
        disk_total = f"{details.total/(1024 ** 3):.2f} GB Total" 
        disk_used = f"{details.used/(1024 ** 3):.2f} GB Used"
        disk_free = f"{details.free/(1024 ** 3):.2f} GB Free"
        info[drive_key] = [disk_total, disk_used, disk_free]
    
    memory = psutil.virtual_memory()
    total_ram = f"{memory.total/(1024 ** 3):.2f} GB Total"
    available_ram = f"{memory.available/(1024 ** 3):.2f} GB Available"
    percent_ram = f"{memory.percent}%"
    used_ram = f"{memory.used/(1024 ** 3):.2f} GB Used"
    free_ram = f"{memory.free/(1024 ** 3):.2f} GB Free"

    info["RAM"] = [total_ram, available_ram, percent_ram, used_ram, free_ram]
    info["Python Ver"] = platform.python_version()

    info["timestamp"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    
    return info

def save_log(info: dict, dest_folder: str):
    """
    Save system information to a timestamped text file.

    Parameters:
        info (dict): Dictionary returned from get_system_info().
        dest_folder (str): Folder where log files will be saved.

    Behavior:
        - Creates the destination folder if needed.
        - Generates a filename with the current timestamp.
        - Writes each key/value pair in the dictionary to the log file.
        - Prints the path of the saved report.
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"system_report_{timestamp}.txt"
    new_path = os.path.join(dest_folder, file_name)

    with open(new_path, "w") as file:
        for keys, items in info.items():
            file.write(f"{keys}: {items}\n")
    
    print(f"System report saved: {new_path}")


if __name__=="__main__":

    dict_info = get_system_info()
    save_log(dict_info, "Newprojects/AutomationScripting/process_log")
