"""
devopsEx25: Remote Server Automation (SSH) — System Summary & Command Executor

This script connects to a remote server via SSH using Paramiko, executes predefined
system-check commands (like uptime, disk usage, memory usage, login history, and recent
system errors/warnings), and optionally runs additional arbitrary commands.

It prints the outputs of each command and handles errors gracefully, ensuring
the SSH connection is properly closed even if an error occurs.

Environment Variables (loaded via .env):
- SSH_HOST       : IP or hostname of the remote server
- SSH_USER       : SSH username
- SSH_KEY_PATH   : Path to private key (.pem) for authentication

Functions:
- get_client(): Establishes SSH connection and returns an active client or None.
- get_commands(): Returns a dictionary of predefined system-check commands.
- print_summary(basic_checks=True, command_list=None): Executes basic checks and
  optional additional commands, printing output and errors.

Usage:
    python print_summary.py

Example:
    command_list = [
        "pwd",
        "ls -la",
        "echo 'Hello from EC2'",
        "cd /nonexistent", 
        "cat /file_does_not_exist.txt"
    ]
    print_summary(basic_checks=True, command_list=command_list)

This script is useful for routine server monitoring and ad-hoc command execution
on remote Linux servers via SSH.

Date: 2025-12-20
"""
import connectviaparamiko

def get_client():
    
    client = connectviaparamiko.connect_to_server()
    
    if not client:
        return None
    
    return client

def get_commands():

    commands = {
        "uptime": "uptime",
        "disk_usage": "df -h",
        "memory_usage": "free -h",
        "login_history": "last",
        "system_errors": "sudo journalctl -p err --since today -n 10",
        "system_warnings": "sudo journalctl -p warning --since today -n 10"
    }

    return commands

def print_summary(basic_checks=True, command_list:list=None):

    client = get_client()

    if not client:
        print("[ERROR] Connection could not be established")
        return
    try:
        if basic_checks:
            commands = get_commands()

            print(f"\n{'='*40}")
            print("BASIC SYSTEM SUMMARY")
            print(f"{'='*40}")
            
            for key, dict_cmd in commands.items():
                out, err, code = connectviaparamiko.run_remote_command(client, dict_cmd)
                if code != 0:
                    print(f"[ERROR] executing {dict_cmd} failed - {err}\n skipping...")
                else:
                    print(f"{key}:\n{out}")
        
        if command_list:
            print(f"\n{'='*40}")
            print("ADDITIONAL COMMANDS")
            print(f"{'='*40}")
            for list_cmd in command_list:
                out, err, code = connectviaparamiko.run_remote_command(client, list_cmd)
                if code !=0:
                    print(f"[ERROR] executing {list_cmd}\n failed due to: {err}\n skipping...\n")
                else:
                    print(f"{out}\n")
    finally:
        client.close()


if __name__=="__main__":

    command_list = [
    # These should work:
    "pwd",                    # Shows current directory
    "ls -la",                 # Lists files with details
    "echo 'Hello from EC2'",  # Simple echo
    
    # These should fail:
    "cd /nonexistent",        # Non-existent directory
    "cat /file_does_not_exist.txt",  # Non-existent file
]

    print_summary(basic_checks=True, command_list=command_list)

            

    