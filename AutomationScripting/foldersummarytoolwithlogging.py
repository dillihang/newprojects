import argparse
import os
import glob
from collections import Counter
from contextlib import redirect_stdout
import json
from datetime import datetime
import logging
import tempfile
from logging.handlers import RotatingFileHandler

log_default = os.path.join(tempfile.gettempdir(), "folder_summary.log")

def validate_path(path: str):
    """
    Validate that the given path exists and is a non-empty directory.

    Parameters:
        path (str): The folder path to validate.

    Returns:
        bool: True if the path exists, is a directory, and contains files/folders; False otherwise.
    """
    try:
        if os.path.isfile(path):
            logging.error("Path is not a folder: %s", path)
            print(f"[ERROR] {path} is a file not a folder")
            return False

        if not os.path.exists(path):
            logging.error("Path does not exist: %s", path)
            print(f"[ERROR] {path} does not exist")
            return False
        
        if not os.path.isdir(path):
            logging.error("Path is not a directory: %s", path)
            print(f"[ERROR] {path} is not a directory")
            return False
        
        dir_list= os.listdir(path)
        if len(dir_list) == 0:
            logging.error("Path is empty: %s", path)
            print(f"[ERROR] {path} is empty - no files or folders to analyze")
            return False

        return True
    
    except PermissionError as e:
        logging.error("Permission denied accessing path: %s - %s", path, e)
        print(f"[ERROR] Permission denied: {path}")
        return False

def resolve_validate_output_path(output: str):
    """
    Validate and resolve the output file path.

    Checks if the directory exists and if the file already exists (prints info if overwriting).

    Parameters:
        output (str): Path to the output file.

    Returns:
        str or None: Returns the validated output path if valid; None if validation fails.
    """
    try:
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            logging.error("Output directory does not exist: %s", output_dir)
            print(f"[ERROR] Output directory does not exist: {output_dir}")
            return None  # ← Consistent: always return None on error
        if output_dir and not os.path.isdir(output_dir):
            logging.error("Output path is not a directory: %s", output_dir)
            print(f"[ERROR] Output path is not a directory: {output_dir}")
            return None
        
        if os.path.exists(output):
            logging.warning("Output file already exists - overwriting: %s", output)
            print(f"[INFO] Output file {output} already exists - overwriting")
        
        return output
    except PermissionError as e:
        logging.error("Permission denied accessing path: %s - %s", output, e)
        print(f"[ERROR] Permission denied: {output}")
        return None

def files_lookup(path: str, extension: str, subfolders: bool = False):
    """
    Collect files, folders, and root directories from a folder, optionally including subfolders.

    Parameters:
        path (str): The root folder to search in.
        extension (str): File extension filter (e.g., ".txt") or "*" for all files.
        subfolders (bool): If True, scan subdirectories recursively.

    Returns:
        dict or None: Dictionary containing:
            "Roots" : list of root folders scanned
            "Folders" : list of subfolders found
            "Files" : list of file paths matching the extension
        Returns None if permission errors occur.
    """
    folder_dict = {"Roots" : [], "Folders": [], "Files": []}
    try:
        if subfolders:
            for root, dirs, files in os.walk(path):
                folder_dict["Roots"].append(root)
                for dir_name in dirs:
                    folder_dict["Folders"].append(os.path.join(root, dir_name))
                for file_name in files:
                    file_ext = os.path.splitext(file_name)[1]
                    if extension == "*" or file_ext == extension:
                        folder_dict["Files"].append(os.path.join(root, file_name))
            logging.info("Found %d roots, %d folders, %d files", 
             len(folder_dict["Roots"]), 
             len(folder_dict["Folders"]), 
             len(folder_dict["Files"]))        
            return folder_dict
        
        else:
            if extension == "*":
                ext_str = "*"
            else:
                ext_str = extension
            file_list = glob.glob(os.path.join(path, ext_str))
            folder_dict["Files"].extend(file_list)
            logging.info("Found %d roots, %d folders, %d files", 
             len(folder_dict["Roots"]), 
             len(folder_dict["Folders"]), 
             len(folder_dict["Files"])) 
            return folder_dict
    except PermissionError as e:
        logging.error("Permission denied %s: %s", path, e)
        print(f"[ERROR] You do not have the right permission {e}")
        
    return None
         
def get_file_size(filepath_dict: dict):
    """
    Get the size of each file in the list of file paths.

    Parameters:
        filepath_dict (dict): Dictionary containing a "Files" key with full file paths.

    Returns:
        dict: Dictionary mapping full file path -> size in MB (formatted as string "xx.xx MB").
              Skips files that cannot be accessed due to permissions or OS errors.
    """
    file_size_dict={}

    for file_name in filepath_dict["Files"]:
        try:
            file_size = os.path.getsize(file_name)/(1024 * 1024)
            file_size_dict[file_name]=f"{file_size:.2f} MB"
        except (PermissionError, OSError) as e:
            logging.error("File access error for %s: %s", file_name, e)
            print(f"[WARNING] Cannot access {file_name}: {e}")
            continue
    
    return file_size_dict

def calculate_file_stats(size_dict: dict, filepath_dict: dict, top_N: int = None):
    """
    Compute summary statistics about the files in a folder.

    Parameters:
        size_dict (dict): Dictionary of file sizes (full path -> size in MB string).
        filepath_dict (dict): Dictionary from files_lookup() containing folder/file info.
        top_N (int, optional): Return top N largest files if specified.

    Returns:
        dict: Dictionary containing summary stats:
            - timestamp
            - total_files
            - total_folders
            - total_size_mb
            - largest_file (name, size)
            - smallest_file (name, size)
            - file_types (Counter of extensions)
            - most_common_type (ext, count)
            - top_N_files (optional)
    """
    stats_dict = {}
    
    timestamp = f"report generated on {datetime.today().strftime("%d/%m/%Y, %H:%M:%S")}."

    stats_dict["timestamp"] = timestamp
    
    stats_dict["total_files"] = len(size_dict)
    stats_dict["total_folders"] = len(filepath_dict["Folders"])
    stats_dict["total_size_mb"] = sum(float(size_str.split()[0]) for file_name, size_str in size_dict.items())
    
    stats_dict["largest_file"] = max(((file_name, float(size_str.split()[0])) for file_name, size_str in size_dict.items()), key=lambda x:x[1])
    stats_dict["smallest_file"] = min(((file_name, float(size_str.split()[0])) for file_name, size_str in size_dict.items()), key=lambda x:x[1])
    logging.info("File size range: %.2f MB to %.2f MB", 
             stats_dict["smallest_file"][1], 
             stats_dict["largest_file"][1])

    file_ext_list = [os.path.splitext(file_names)[1] for file_names in size_dict.keys()]
    file_ext_list = [ext if ext else"(no extension)" for ext in file_ext_list]
    ext_counter = Counter(file_ext_list)
    
    stats_dict["file_types"] = ext_counter
    stats_dict["most_common_type"] = ext_counter.most_common(1)[0] if ext_counter else (None, 0)

    if top_N:
        new_list = sorted([(file_name, float(size_str.split()[0])) for file_name, size_str in size_dict.items()], key=lambda x:x[1], reverse=True)
        stats_dict["top_N_files"] = new_list[:top_N]
    
    return stats_dict 

def print_stats(path: str, stats: dict):
    """
    Print a human-readable summary of folder statistics to the console.

    Parameters:
        path (str): Folder path being summarized.
        stats (dict): Dictionary from calculate_file_stats() containing computed stats.
    """
    print(f"Folder summary {stats["timestamp"]} for: {path}")
    print(f"Total Files: {stats['total_files']}")
    print(f"Total Folders: {stats['total_folders']}")
    print(f"Total Size: {stats['total_size_mb']:.2f} MB")
    print()
    largest_file, largest_size = stats["largest_file"]
    smallest_file, smallest_size = stats["smallest_file"]
    print(f"Largest File: {os.path.basename(largest_file)} ({largest_size:.2f} MB)")
    print(f"Smallest File: {os.path.basename(smallest_file)} ({smallest_size:.2f} MB)")
    print()
    print("Files by Type:")
    for ext, count in stats["file_types"].most_common():
        print(f"  {ext}: {count} files")
    print()    
    most_common_ext, most_common_count = stats["most_common_type"]
    print(f"Most Common File Type: {most_common_ext} ({most_common_count} files)") 
    print()
    if "top_N_files" in stats:
        print(f"Top {len(stats['top_N_files'])} Largest Files:")
        for file_name, size in stats["top_N_files"]:
            print(f"  {os.path.basename(file_name)} ({size:.2f} MB)")

def save_txt_report(path: str, output: str, stats: dict):
    """
    Save the folder summary to a text file.

    Parameters:
        path (str): Folder path being summarized.
        output (str): Output file path.
        stats (dict): Dictionary from calculate_file_stats() containing computed stats.
    """
    with open(output, "w") as file_txt:
        with redirect_stdout(file_txt):
            print_stats(path, stats)

    logging.info("txt file saved at: %s", output)
    print(f"{output} file saved")

def save_json_report(output:str, stats: dict):
    """
    Save the folder summary to a JSON file.

    Parameters:
        output (str): Output file path.
        stats (dict): Dictionary from calculate_file_stats() containing computed stats.
    """
    with open(output, "w") as file_json:
        json.dump(stats, file_json, indent=4)

    logging.info("json file saved at: %s", output)
    print(f"{output} file saved")

def generate_summary(args):
    """
    Generate a summary of the folder contents based on command-line arguments.

    Parameters:
        args: Parsed argparse.Namespace object with attributes:
            - path: folder to summarize
            - top_N: optional, number of largest files to show
            - ext: file extension filter
            - subfolders: whether to include subfolders
            - output: optional output file path
            - format: output format ("txt" or "json")
    """
    print(f"Generating summary on files on {args.path}")

    if not validate_path(args.path):
        return
    
    output_path = None

    if args.output:
        output_path = resolve_validate_output_path(args.output)
        if output_path is None:
            return
    
    filepath_dict = files_lookup(args.path, args.ext, args.subfolders)
    if filepath_dict is None:
        return
    size_dict = get_file_size(filepath_dict)
    stats_dict = calculate_file_stats(size_dict, filepath_dict, args.top_N)

    if output_path is None:
        print_stats(args.path, stats_dict)
    else:
        if args.format == "json":
            save_json_report(output_path, stats_dict)
        else:
            save_txt_report(args.path, output_path, stats_dict)

def main():
    """
    Parse command-line arguments and run the folder summary generation.

    CLI arguments:
        path (str): Folder to summarize.
        --top-N (int): Show N largest files in descending size order.
        --ext (str): File extension filter (default: "*").
        --subfolders (flag): Include subfolders if set.
        --output (str): Save results to file.
        --format (str): Output format ("txt" or "json", default "txt").
    """
     
    main_parser = argparse.ArgumentParser(description="Folder Summary CLI tool - produces a summary report about its files")

    main_parser.add_argument("path", help="Folder to summarize")
    main_parser.add_argument("--top-N", type=int, help="Show N Largest files in descending size order")
    main_parser.add_argument("--ext", default="*", help="File extension filter (default: everything)")
    main_parser.add_argument("--subfolders", action="store_true", help="look for files in subfolders (default: only the path)")
    main_parser.add_argument("--output", help="Save results to file (specify filename)")
    main_parser.add_argument("--format", choices=["json", "txt"], default="txt", help="Output format (default: txt)")
    main_parser.add_argument("--log-file", default=log_default, help=f"Path to log file (default: {log_default})")

    
    args = main_parser.parse_args()
    
    handler = RotatingFileHandler(
        args.log_file,
        maxBytes=1024*1024,
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
        ))

    logging.basicConfig(
        handlers=[handler],
        level=logging.INFO
    )
    
    print(f"[INFO] Logs are being written to: {args.log_file}")
    
    generate_summary(args)
    
if __name__=="__main__":
    main()