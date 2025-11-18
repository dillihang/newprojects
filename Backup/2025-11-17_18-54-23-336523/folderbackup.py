import shutil
import os
from datetime import datetime

print("SCRIPT STARTED")

def backup(folder_path: str, dest_path: str):
    """
    Create a timestamped backup copy of a folder.

    Parameters:
        folder_path (str): Path to the folder you want to back up.
        dest_path (str): Path to the directory where backups will be stored.

    Behavior:
        - Creates the destination folder if it does not exist.
        - Appends a timestamp (YYYY-MM-DD_HH-MM-SS-microseconds) to each backup folder.
        - Uses shutil.copytree to copy the entire directory recursively.
        - Prints a success message including the backup path.
        - Prints an error message if copying fails.
    """
    if os.path.exists(folder_path):
        os.makedirs(dest_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        destination = os.path.join(dest_path, timestamp)
        try:
            shutil.copytree(folder_path, destination)
            print(f"Backup completed: {destination}")
        except Exception as e:
            print(f"Backup failed {e}")
    else:
        print(f"[ERROR] Source folder does not exist: {folder_path}")


if __name__ == "__main__":
    # Get folder of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Source: AutomationScripting folder (the script folder itself)
    source = script_dir

    # Destination: Backup folder alongside AutomationScripting
    dest = os.path.join(os.path.dirname(script_dir), "Backup")

    print(f"script_dir: {script_dir}")
    print(f"source path: {source}")
    print(f"destination path: {dest}")
    print(f"Exists? {os.path.exists(source)}")

    backup(source, dest)

    print("SCRIPT FINISHED")
