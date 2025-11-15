import shutil
import os
from datetime import datetime

def backup(folder_path: str, dest_path: str):

    if os.path.exists(folder_path):
        os.makedirs(dest_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        destination = os.path.join(dest_path, timestamp)

        shutil.copytree(folder_path, destination)
        print(f"Backup completed: {destination}")



if __name__ == "__main__":

    backup("Newprojects/AutomationScripting", "Newprojects/Backup")
