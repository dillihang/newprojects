import connectviaparamiko
import devopsEx26_servermaintenaceautoscript
from datetime import datetime, timedelta
import copy

def find_files(client, folder_path: str, ext: str):
    """
    Find files on a remote system matching a given extension and return
    their paths with last-modified dates.

    Uses SSH to execute a remote `find` command and extracts:
    - full file path
    - last modification date (YYYY-MM-DD)

    Args:
        client: Active SSH client connection.
        folder_path (str): Directory to scan.
        ext (str): File extension to match (e.g. '.log' or 'log').

    Returns:
        list[str]: Raw file metadata lines in the format:
                   "<path><>YYYY-MM-DD"
                   or an empty list if no files are found or on error.
    """
    if ext.startswith('.'):
        pattern = ext
    else:
        pattern = '.' + ext

    cmd = f"find {folder_path} -name '*{pattern}' -exec stat -c '%n %y' {{}} \\; | awk '{{print $1 \"<>\" $2}}'"
    
    result, err, code = connectviaparamiko.run_remote_command(client=client, command=cmd)
    if not result or result.isspace():
        print("[INFO] no files found")
        return []
    elif code != 0:
        print(f"[ERROR] {err}")
        return []
    else:
        raw_data = result.strip().split("\n")
        return raw_data

def data_parser(raw_data: list):
    """
    Parse raw file metadata lines into structured data.

    Converts raw strings into a dictionary mapping file paths
    to their last-modified date.

    Args:
        raw_data (list[str]): Raw metadata lines from `find_files`.

    Returns:
        tuple:
            - dict[str, date]: Parsed file paths and modification dates.
            - list[str]: Lines that failed to parse.
    """
    parsed_dict={}
    skipped_files=[]

    for line in raw_data:
            try:
                file_path, date_str=line.split("<>")
                timestamp=datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
                parsed_dict[file_path]=timestamp
            except ValueError as e:
                print(f"[ERROR] parsing line {line} : {e}")
                skipped_files.append(line)
                continue
            except Exception as e:
                print(f"[ERROR] Unexpected error with line '{line}': {e}")
                skipped_files.append(line)
                continue
    
    return parsed_dict, skipped_files
    
def file_filter(parsed_dict: dict, retention:int=7):
    """
    Filter files based on retention policy.

    Selects files older than the specified number of days.

    Args:
        parsed_dict (dict): Mapping of file paths to modification dates.
        retention (int): Retention period in days.

    Returns:
        dict[str, date]: Files exceeding retention threshold.
    """
    filtered_dict = {}
    threshold_date = datetime.now().date() - timedelta(days=retention)

    if not parsed_dict:
        print("[INFO] no files to process")
        return {}

    for file_path, modified_date in parsed_dict.items():
        if threshold_date>modified_date:
            filtered_dict[file_path] = modified_date
          
    return filtered_dict

def create_action_plan(filtered_dict: dict, retention:int=7):
    """
    Create an action plan describing what should happen to each file.

    The action plan is data-driven and does NOT perform any actions.
    It only describes intent (compress, delete, labels, previews).

    Args:
        filtered_dict (dict): Files selected for action.
        retention (int): Retention period used for labeling.

    Returns:
        dict: Action plan keyed by file path with action metadata.
    """
    if not filtered_dict:
        print("[INFO] No data to create action plan")
        return {}

    action_plan={}

    for file_path, modified_date in filtered_dict.items():
            action_plan[file_path]={
                "last_modified": modified_date,
                "compress":True,
                "delete": True,
                "preview_compress":f"{file_path} compressed",
                "preview_delete": f"{file_path} deleted",
                "label": f"file older than {retention} days"
            }

    return action_plan

def compress_file_keep_original(client, file_path: str):
    """
    Compress a file using gzip while keeping the original file.

    Args:
        client: Active SSH client connection.
        file_path (str): Path to the file to compress.

    Returns:
        tuple:
            - bool: True if compression succeeded, False otherwise.
            - str | None: Error message if failed.
    """
    out, err, code = connectviaparamiko.run_remote_command(
                    client=client, 
                    command=f"sudo gzip -k {file_path}"
                    )
    if code !=0:
        print(f"[ERROR] Compression process failed for {file_path}: {err}")
        return False, err
    return True, None

def delete_file(client, file_path: str):
    """
    Delete a file from the remote system.

    Args:
        client: Active SSH client connection.
        file_path (str): Path to the file to delete.

    Returns:
        tuple:
            - bool: True if deletion succeeded, False otherwise.
            - str | None: Error message if failed.
    """
    out, err, code = connectviaparamiko.run_remote_command(
                    client=client,
                    command=f"sudo rm {file_path}"
                    )
    if code !=0:
        print(f"[ERROR] Deletion process failed for {file_path}: {err}")
        return False, err
    return True, None

def apply_action(client, action_plan: dict):
    """
    Apply actions described in an action plan.

    Executes compression and/or deletion based on flags in the plan.
    Produces a detailed execution log without mutating the original plan.

    Args:
        client: Active SSH client connection.
        action_plan (dict): Data-driven action plan.

    Returns:
        dict: Execution log with statuses, results, and errors.
    """
    apply_action_log=copy.deepcopy(action_plan)

    for file_path, metadata in action_plan.items():
     
        apply_action_log[file_path]["status"] = "pending"
        apply_action_log[file_path]["error"] = None
        apply_action_log[file_path]["error_type"] = None
        
        if not metadata["compress"] and metadata["delete"]:
            
            delete_result, delete_err = delete_file(client, file_path)
            if delete_result:
                apply_action_log[file_path]["status"] = "success"
                apply_action_log[file_path]["action"] = "deleted_only"
            else:
                apply_action_log[file_path]["status"] = "failed"
                apply_action_log[file_path]["error_type"] = "deletion_failed"
                apply_action_log[file_path]["error"] = delete_err
        
        elif metadata["compress"] and not metadata["delete"]:
            
            compress_result, compress_err = compress_file_keep_original(client, file_path)
            if compress_result:
                apply_action_log[file_path]["status"] = "success"
                apply_action_log[file_path]["action"] = "compressed_only"
                apply_action_log[file_path]["compressed_file"] = f"{file_path}.gz"
            else:
                apply_action_log[file_path]["status"] = "failed"
                apply_action_log[file_path]["error_type"] = "compression_failed"
                apply_action_log[file_path]["error"] = compress_err
        
        else:  
          
            compress_result, compress_err = compress_file_keep_original(client, file_path)
            if compress_result:
               
                delete_result, delete_err = delete_file(client, file_path)
                if delete_result:
                    apply_action_log[file_path]["status"] = "success"
                    apply_action_log[file_path]["action"] = "compressed_and_deleted"
                    apply_action_log[file_path]["compressed_file"] = f"{file_path}.gz"
                else:
                    apply_action_log[file_path]["status"] = "partial_success"
                    apply_action_log[file_path]["action"] = "compressed_but_not_deleted"
                    apply_action_log[file_path]["compressed_file"] = f"{file_path}.gz"
                    apply_action_log[file_path]["error_type"] = "deletion_failed"
                    apply_action_log[file_path]["error"] = delete_err
            else:
                apply_action_log[file_path]["status"] = "failed"
                apply_action_log[file_path]["error_type"] = "compression_failed"
                apply_action_log[file_path]["error"] = compress_err
    
    return apply_action_log


def print_summary(action_plan: dict, summary_dict: dict, dry_run: bool = True):
    """
    Print a human-readable summary of planned or executed actions.

    Displays per-file results and overall statistics.
    Intended for terminal output (not structured logging).

    Args:
        action_plan (dict): Planned actions or execution results.
        summary_dict (dict): Aggregated statistics.
        dry_run (bool): Whether this is a dry-run preview.
    """
    mode = "DRY RUN - PLAN" if dry_run else "EXECUTION RESULTS"
    print(f"\n{'='*60}")
    print(f"{mode:^60}")
    print(f"{'='*60}")
    
    # File actions
    success_count = 0
    failed_count = 0
    partial_count = 0
    
    for file_path, metadata in action_plan.items():
        status = metadata.get('status', 'planned')
        
        if status == 'success':
            success_count += 1
            action = metadata.get('action', 'completed').replace('_', ' ').title()
            print(f"[SUCCESS] {file_path}")
            print(f"  Result: {action}")
            
        elif status == 'failed':
            failed_count += 1
            error_type = metadata.get('error_type', 'unknown').replace('_', ' ').title()
            print(f"[FAILED] {file_path}")
            print(f"  Reason: {error_type}: {metadata.get('error', 'No details')}")
            
        elif status == 'partial_success':
            partial_count += 1
            action = metadata.get('action', 'partial').replace('_', ' ').title()
            print(f"[PARTIAL] {file_path}")
            print(f"  Result: {action}: {metadata.get('error', '')}")
            
        else:  # planned/dry-run
            print(f"[PLANNED] {file_path}")
            print(f"  Compress: {metadata['preview_compress']}")
            print(f"  Delete: {metadata['preview_delete']}")
        print()  # Empty line between files
    
    # Summary
    print(f"{'='*60}")
    print("SUMMARY:")
    print(f"{'='*60}")
    
    if dry_run:
        print(f"Files to process: {len(action_plan)}")
    else:
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        if partial_count > 0:
            print(f"Partial: {partial_count}")
    
    # Stats
    for key, val in summary_dict.items():
        if val is not None:
            print(f"{key.replace('_', ' ').title()}: {val}")
    
def orchestrate_action(folder_path: str, ext:str = ".log", dry_run=True, retention:int = 7):
    """
    Orchestrate the full maintenance workflow.

    Pipeline:
        find → parse → filter → plan → apply → report

    Manages:
    - SSH lifecycle
    - permission checks
    - dry-run vs execution
    - error handling and cleanup

    Args:
        folder_path (str): Directory to scan.
        ext (str): File extension to target.
        dry_run (bool): Preview actions without executing.
        retention (int): Retention period in days.
    """
    client=None
    try:
        client = connectviaparamiko.connect_to_server()

        if not client:
            print("[ERROR] Could not establish connection")
            return 
        
        raw_data = find_files(client=client, folder_path=folder_path, ext=ext)

        if not raw_data:
            return
        
        parsed_data, skipped_data = data_parser(raw_data=raw_data)

        if not parsed_data:
            print("[INFO] No data")
            return
        
        filtered_data = file_filter(parsed_dict=parsed_data, retention=retention)

        if not filtered_data:
            print(f"[INFO] no files older than retention day. Total files scanned: {len(raw_data)}")
            return
        
        action_plan=create_action_plan(filtered_dict=filtered_data, retention=retention)
        
        if not action_plan:
            return
        
        summary_dict = {
            "totalfiles_scanned": len(raw_data),
            "skipped_data": len(skipped_data) if skipped_data else None,
            "totalfiles_to_compress": len(action_plan),
            "totalfiles_to_delete": len(action_plan)
        }
        
        if not dry_run:
            result=devopsEx26_servermaintenaceautoscript.super_user()
            if not result:
                print("[ERROR] Permission denied")
                return

            action_plan_log = apply_action(client=client, action_plan=action_plan)
            print_summary(action_plan=action_plan_log, summary_dict=summary_dict, dry_run=False)
        else:
            print_summary(action_plan=action_plan, summary_dict=summary_dict, dry_run=True)
    finally:
        if client:
            client.close()


if __name__=="__main__":

    folder_path = "/home/ec2-user/test_log_folder"
    orchestrate_action(folder_path=folder_path, dry_run=False, retention=400)
