import connectviaparamiko
from dotenv import load_dotenv
import os

load_dotenv()

def super_user():
    super_user_key = os.getenv("OWNER_KEY")
    if not super_user_key:
        print("[ERROR] could not retrieve super user")
        return False
    
    user_key = input("please enter your key: ")

    if user_key == super_user_key:
        return True
    
    return False


def check_disk_space(client):

    return connectviaparamiko.run_remote_command(client, "df -h test_log_folder | awk 'NR==2 {print $5}'")

def delete_files_datebased(client, delete=False):

    if not delete:
        return connectviaparamiko.run_remote_command(client, "cd test_log_folder && find . -mtime +30 -type f")
    else:
        return connectviaparamiko.run_remote_command(client, "cd test_log_folder && find . -mtime +30 -type f -delete")

def backup_logs(client, back_up=False):
    if not back_up:
        return connectviaparamiko.run_remote_command(client, "ls -la /var/log/cloud-init.log")
    else:
        return connectviaparamiko.run_remote_command(client, "sudo tar -czf /home/ec2-user/logs_backup.tgz -C /var/log cloud-init-output.log")


def automated_maintenance(dry_run=True):

    client = connectviaparamiko.connect_to_server()

    if not client:
        print("[ERROR] Could not connect to server")
        return
    
    try:
        out, err, code = check_disk_space(client=client)
        if code !=0:
            print(f"[ERROR] failed {err}")
            return
        
        use_number = int(out.strip().strip('%'))
        if use_number < 30:
            print(f"disk is still under the threshold, exiting...")
            return
        else:
            print(f"[WARNING] Disk usage at {use_number}%")
            print(f"Proceeding with automated cleanup process...\n")

            if dry_run:
                out, err, code = delete_files_datebased(client=client, delete=False)
                if code != 0:
                    print(f"[ERROR] failed {err}")
                else:
                    print("[DRY-RUN] Deleting files...")
                    print(out)
                
                out, err, code = backup_logs(client=client, back_up=False)
                if code !=0:
                    print(f"[ERROR] failed {err}")
                else:
                    print("[Dry-RUN] Backing up files...")
                    print(out)
            else:
                result = super_user()
                if not result:
                    print(f"[ERROR] Super user access key could not be valid, permission denied")
                    return
                else:
                    print(f"Super user validated, proceeding...")

                    delete_out, _, _ = delete_files_datebased(client=client, delete=False)
                    out, err, code = delete_files_datebased(client=client, delete=True)
                    if code != 0:
                        print(f"[ERROR] failed {err}")
                    else:
                        print("Deleting files...")
                        print(delete_out)
                        print("Files deleted\n")
                    
                    out, err, code = backup_logs(client=client, back_up=True)
                    backup_out, _, _ = backup_logs(client=client, back_up=False)
                    if code !=0:
                        print(f"[ERROR] failed {err}")
                    else:
                        print("Backing up files...")
                        print(backup_out)
                        print("Files backed up /home/ec2-user/")
    finally:
        client.close()


if __name__=="__main__":
    
    # automated_maintenance(dry_run=True)
    automated_maintenance(dry_run=False)


# bit more advanced version
# import connectviaparamiko
# from dotenv import load_dotenv
# import os

# load_dotenv()


# def super_user():
#     """
#     Very simple authentication check to allow destructive actions.
#     """
#     super_user_key = os.getenv("OWNER_KEY")
#     if not super_user_key:
#         print("[ERROR] could not retrieve super user key")
#         return False

#     user_key = input("please enter your key: ")
#     return user_key == super_user_key


# def check_disk_space(client):
#     """
#     Returns disk usage percentage for test_log_folder.
#     """
#     return connectviaparamiko.run_remote_command(
#         client,
#         "df -h test_log_folder | awk 'NR==2 {print $5}'"
#     )


# def run_action(client, preview_cmd, exec_cmd=None, dry_run=True, label=""):
#     """
#     Runs a preview command and optionally executes the real command.

#     Args:
#         client: Active SSH client
#         preview_cmd (str): Command to show what will happen
#         exec_cmd (str): Command that performs the real action
#         dry_run (bool): If True, do not execute destructive actions
#         label (str): Friendly description of the action

#     Returns:
#         bool: True if successful, False otherwise
#     """
#     out, err, code = connectviaparamiko.run_remote_command(client, preview_cmd)
#     if code != 0:
#         print(f"[ERROR] {label} preview failed:\n{err}")
#         return False

#     print(out)

#     if dry_run:
#         print(f"[DRY-RUN] {label} skipped\n")
#         return True

#     if exec_cmd:
#         _, err, code = connectviaparamiko.run_remote_command(client, exec_cmd)
#         if code != 0:
#             print(f"[ERROR] {label} execution failed:\n{err}")
#             return False

#         print(f"[SUCCESS] {label} completed\n")

#     return True


# def automated_maintenance(dry_run=True):
#     """
#     Automated server maintenance script.

#     - Checks disk usage
#     - Deletes old log files if threshold exceeded
#     - Backs up important logs
#     - Supports dry-run mode
#     """
#     client = connectviaparamiko.connect_to_server()
#     if not client:
#         print("[ERROR] Could not connect to server")
#         return

#     try:
#         out, err, code = check_disk_space(client)
#         if code != 0:
#             print(f"[ERROR] Disk check failed:\n{err}")
#             return

#         usage = int(out.strip().strip('%'))

#         if usage < 30:
#             print("Disk usage below threshold, exiting.")
#             return

#         print(f"[WARNING] Disk usage at {usage}%")
#         print("Proceeding with automated maintenance...\n")

#         if not dry_run:
#             if not super_user():
#                 print("[ERROR] Permission denied")
#                 return
#             print("Super user validated, proceeding...\n")

#         # Delete old log files
#         run_action(
#             client=client,
#             preview_cmd="cd test_log_folder && find . -mtime +30 -type f",
#             exec_cmd="cd test_log_folder && find . -mtime +30 -type f -delete",
#             dry_run=dry_run,
#             label="Deleting old log files"
#         )

#         # Backup important logs
#         run_action(
#             client=client,
#             preview_cmd="ls -la /var/log/cloud-init.log",
#             exec_cmd="sudo tar -czf /home/ec2-user/logs_backup.tgz -C /var/log cloud-init-output.log",
#             dry_run=dry_run,
#             label="Backing up system logs"
#         )

#     finally:
#         client.close()


# if __name__ == "__main__":
#     # automated_maintenance(dry_run=True)
#     automated_maintenance(dry_run=False)
  
    