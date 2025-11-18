import argparse
import os
import glob

def path_validation(path: str):
    """
    Validate that the given path exists and is a directory.

    Parameters:
        path (str): The filesystem path to validate.

    Returns:
        bool: True if the path exists and is a directory, False otherwise.

    Notes:
        - Prints descriptive error messages for missing or invalid paths.
    """
    if not os.path.exists(path):
        print(f"[ERROR] Path {path} does not exist")
        return False
        
    if not os.path.isdir(path):
        print(f"[ERROR] {path} is not a directory")
        return False
    
    return True

def get_search_path(path: str, extension: str):
    """
    Build a file search pattern from a directory path and file extension.

    Parameters:
        path (str): Directory to search in.
        extension (str): File extension filter (e.g., ".txt").

    Returns:
        str: A glob-compatible pattern string pointing to the target files.

    Example:
        get_search_path("logs", ".txt") -> "logs/*.txt"
    """
    if extension:
        pattern = f"*{extension}"                 
    else:
        pattern = "*"     
    return os.path.join(path, pattern)

def get_files_list(path: str):
    """
    Retrieve a sorted list of file paths matching a glob pattern.

    Parameters:
        path (str): Full glob-style pattern (e.g., 'folder/*.txt').

    Returns:
        list[str]: Alphabetically sorted list of matching file paths.
    """
    return sorted([f for f in glob.glob(path)])

def handle_count(args):
    """
    Execute the COUNT command: list and count files in a directory.

    Parameters:
        args (Namespace): Parsed arguments containing:
            - path (str): Directory to inspect.
            - ext (str): File extension filter (e.g., ".txt").

    Behaviour:
        - Validates the directory.
        - Counts all matching files.
        - Prints a sorted list of filenames.
        - Prints total count.

    Notes:
        - If no files are found, a clear message is printed.
    """
    print(f"Counting files in: {args.path}")

    if not path_validation(args.path):
        return
    
    search_path = get_search_path(args.path, args.ext)

    files = get_files_list(search_path)
    total_files = len(files)

    if files:
        print(f"total {args.ext} files found {total_files} in {args.path}")
        for f in files:
            print(f"{os.path.basename(f)}")
    
    else:
        print(f"No {args.ext} files found in {args.path}")

def handle_search(args):
    """
    Execute the SEARCH command: find files containing a keyword.

    Parameters:
        args (Namespace): Parsed arguments containing:
            - path (str): Directory to search in.
            - keyword (str): Search term to look for.
            - ext (str): File extension filter.
            - case_sensitive (bool): Controls case handling.

    Behaviour:
        - Validates the directory.
        - Rejects keywords with leading/trailing spaces.
        - Opens each readable file and checks for keyword presence.
        - Case-insensitive search if requested.
        - Reports matching files by name.

    Notes:
        - Files that cannot be decoded as UTF-8 are skipped with warnings.
        - Each file appears at most once in the result.
    """
    print(f"Searching for keyword files in: {args.path}")

    if not path_validation(args.path):
        return

    search_path = get_search_path(args.path, args.ext)
        
    files = get_files_list(search_path)

    if not files:
        print(f"No {args.ext} files found in {args.path}")
        return

    if args.keyword.startswith(" ") or args.keyword.endswith(" "):
        print("[ERROR]Search keyword cannot have spaces or just spaces")
        return 

    search_term = args.keyword

    if not args.case_sensitive:
        search_term = search_term.lower()

    file_list = []   
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as file_obj:
                content = file_obj.read().splitlines()
                for line in content:
                    sensitive_line = line if args.case_sensitive else line.lower()
                    if search_term in sensitive_line:
                        file_list.append(file_path)
                        break
        except UnicodeDecodeError:
            print(f"[WARNING] Skipping {os.path.basename(file_path)} - not a readable file")
    
    unique_files_list= set(file_list)
    unique_files_list=sorted(unique_files_list)

    if unique_files_list:
        print(f"{search_term} found in following {len(unique_files_list)} file/files:")
        for path_file in unique_files_list:
            print(f"{os.path.basename(path_file)}")
    else:
        print(f"{search_term} could not be found in any files")

def handle_merge(args):
    """
    Execute the MERGE command: combine multiple text files into one.

    Parameters:
        args (Namespace): Parsed arguments containing:
            - path (str): Folder containing files to merge.
            - output (str): Output filename or absolute output path.
            - ext (str): Extension filter for files to merge.
            - skip_empty (bool): If True, empty files are not included.

    Behaviour:
        - Validates input directory and output file path.
        - Scans for matching files and merges them in alphabetical order.
        - Writes a header before each file's content:
              ===== filename.txt =====
        - Handles empty files based on skip_empty flag.

    Notes:
        - Unreadable files (wrong encoding) are skipped with warnings.
        - If output file exists, it is overwritten with a notice.
    """
    print(f"Merging files in {args.path}")

    if not path_validation(args.path):
        return
    
    if os.path.isabs(args.output):
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            print(f"[ERROR] Output directory does not exist: {output_dir}")
            return
        output_path = args.output
    else:
        output_path = os.path.join(args.path, args.output)

    if os.path.exists(output_path):
        print(f"[INFO] Output file {output_path} already exists - overwriting")

    search_path = get_search_path(args.path, args.ext)
        
    files = get_files_list(search_path)

    if not files:
        print(f"No {args.ext} files found in {args.path}")

    merge_count=0
    with open(output_path, "w", encoding="utf-8") as output_file:
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as file_obj:
                    content = file_obj.read().splitlines()

                    if not content:
                        if args.skip_empty:
                            continue
                        else:
                            output_file.write(f"===== {os.path.basename(file_path)} =====\n")
                            output_file.write("[EMPTY FILE]\n\n")
                            merge_count+=1
                            continue
                    
                    output_file.write(f"===== {os.path.basename(file_path)} =====\n")
                    for line in content:
                        output_file.write(line + "\n")
                        merge_count+=1
                    output_file.write("\n")
            except UnicodeDecodeError:
                print(f"[WARNING] Skipping {os.path.basename(file_path)} - not a readable file")

    print(f"Merged {merge_count} into {output_path}")


def main():
    """
    Entry point for the Text File Toolkit CLI.

    Behaviour:
        - Sets up argparse with three subcommands:
            count  → list and count files
            search → search for keyword in files
            merge  → merge multiple files into one output file
        - Dispatches the call to the appropriate handler.

    Usage:
        python tool.py count <path> [--ext .log]
        python tool.py search <path> <keyword> [--case-sensitive]
        python tool.py merge <path> output.txt [--skip-empty]

    Notes:
        - The `command` argument is required.
        - Prints the active command before execution.
    """
    parser = argparse.ArgumentParser(description="Text File Toolkit - Count, search, and merge text files")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    # COUNT command
    count_parser = subparsers.add_parser("count", help="Count files in a directory")
    count_parser.add_argument("path", help="folder to count files in")
    count_parser.add_argument("--ext", default=".txt", help="file extension filter (default: .txt)")

    # SEARCH command
    search_parser = subparsers.add_parser("search", help="Search for keywords in files")
    search_parser.add_argument("path", help="Folder to search in")
    search_parser.add_argument("keyword", help="text to search for")
    search_parser.add_argument("--ext", default=".txt", help="File extension filter (default: .txt)")
    search_parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")

    # MERGE command
    merge_parser = subparsers.add_parser("merge", help="Merge multiple files into one")
    merge_parser.add_argument("path", help="Folder containing files to merge")
    merge_parser.add_argument("output", help="Output file name for merged content")
    merge_parser.add_argument("--ext", default=".txt", help="File extension to merge (default: .txt)")
    merge_parser.add_argument("--skip-empty", action="store_true", help="Skip empty files during merge")

    args = parser.parse_args()

    print(f"Command: {args.command}")

    if args.command == "count":
        handle_count(args)
    elif args.command == "search":
        handle_search(args)
    elif args.command == "merge":
        handle_merge(args)


if __name__=="__main__":
    main()