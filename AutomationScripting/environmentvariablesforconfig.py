import os
from pathlib import Path
from datetime import datetime
import glob
from contextlib import redirect_stdout
from dotenv import load_dotenv

load_dotenv()

source_folder = os.getenv("SOURCE_FOLDER")
dest_folder = os.getenv("DEST_FOLDER")
api_key = os.getenv("API_KEY")

print(f"[INFO] Using API key: {api_key}")

def collect_txt_files(folder_path: str):
    """
    Collect all .txt files in the given folder.

    Parameters:
        folder_path (str): Path to the folder containing .txt files.

    Returns:
        list[str]: Sorted list of .txt file paths.
                   Returns empty list if folder doesn't exist or no files found.
    """
    if not os.path.exists(folder_path):
        print("[ERROR]: Folder path does not exist")
        return None

    all_txt_files = glob.glob(os.path.join(folder_path,"*.txt"))

    return sorted(all_txt_files)

def generate_report(files: list, output_folder: str):
    
    if not files:
        print("[INFO] No text files found to process")
        return

    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.today().strftime("%d-%m-%Y_%H-%M-%S")
    file_name = f"amalgated_txt_files_{timestamp}.txt"
    output_path = os.path.join(output_folder, file_name)

    with redirect_stdout(open(output_path, "w")):
        for txt_file in files:
            file_name = Path(txt_file).stem
            header_str = f"===== {file_name} ====="
            print(header_str)
            print()
            with open(txt_file, "r") as file_txt:
                content = file_txt.read().strip()
                if not content:
                    print("[INFO] Empty file")
                else:
                    for line in content.splitlines():
                        if line.strip():
                            print(line)
                print()

    print(f"[INFO] Combined report saved at {output_path}")

if __name__ == "__main__":
    """
    Generates a combined text report from multiple .txt files.
    Adds headers for each file and skips empty lines.

    Parameters:
        files (list[str]): List of .txt file paths to include.
        output_folder (str): Folder where the combined report will be saved.

    Returns:
        None
    """

    file_list = collect_txt_files(source_folder)
    generate_report(file_list, dest_folder)