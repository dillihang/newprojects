import shutil
import os
from datetime import datetime

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

    Notes:
        - copytree will fail if the destination already exists.
        - The function does not return anything; it logs progress via print().
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


if __name__ == "__main__":

    backup("Newprojects/AutomationScripting", "Newprojects/Backup")
