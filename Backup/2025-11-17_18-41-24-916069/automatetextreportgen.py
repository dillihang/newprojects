import os
from pathlib import Path
from datetime import datetime
import glob
import pandas as pd
from contextlib import redirect_stdout
from io import StringIO

def collect_txt_files(folder_path: str):

    if not os.path.exists(folder_path):
        print("[ERROR]: Folder path does not exist")
        return None

    all_txt_files = glob.glob(os.path.join(folder_path,"*.txt"))

    return all_txt_files

def generate_report(files: list, output_folder: str):
    
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.today().strftime("%d-%m-%Y_%H-%M-%S")
    file_name = f"amalgated_txt_files_{timestamp}.txt"
    output_path = os.path.join(output_folder, file_name)

    with redirect_stdout(open(output_path, "w")):
        for file in files:
            file_name = Path(file).stem
            header_str = f"===== {file_name} ====="
            print(header_str)
            print()
            with open(file, "r") as file_txt:
                content = file_txt.read().strip()
                if not content:
                    print("Empty file")
                else:
                    for line in content.splitlines():
                        if line:
                            print(line)
                    
                print()

if __name__ == "__main__":

    source = "Newprojects/AutomationScripting"
    destination = "Newprojects/AutomationScripting"
    file_list = collect_txt_files(source)
    generate_report(file_list, destination)