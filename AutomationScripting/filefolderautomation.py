import os
import glob
from datetime import datetime, date, time
import shutil

def rename_files(folder_path: str):
 
    if os.path.exists(folder_path):
        contents = os.listdir(folder_path)
        for items in contents:
            if items.endswith(".txt"):
                old_folderpath = os.path.join(folder_path, items)
                new_name  = f"{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{items}"
                new_folderpath  = os.path.join(folder_path, new_name)
                os.rename(old_folderpath, new_folderpath)

def move_files(folder_path: str, new_path: str):
    
    if not os.path.exists(new_path):
        os.mkdir(new_path)

    if os.path.exists(folder_path):
        contents = os.listdir(folder_path)
        for items in contents:
            if items.endswith(".jpg"):
                old_folderpath = os.path.join(folder_path, items)
                new_folderpath = os.path.join(new_path, items)
                shutil.move(old_folderpath, new_folderpath)

def delete_empty_folders(folder_path: str):
    
    if os.path.exists(folder_path):
        for root, dirs, files in os.walk(folder_path, topdown=False):
            contents = os.listdir(root)
            if len(contents) == 0:
                os.rmdir(root)


if __name__ == "__main__":

    delete_empty_folders("Newprojects/AutomationScripting/images")