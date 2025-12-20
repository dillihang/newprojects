"""
devopsEx23: SSH Remote Command Executor using Paramiko

This script connects to a remote server (EC2 or any SSH-accessible host) using Paramiko,
executes commands remotely, and returns the output, errors, and exit code.

Environment Variables (loaded via .env):
- SSH_HOST       : IP or hostname of the server
- SSH_USER       : SSH username
- SSH_KEY_PATH   : Path to private key (.pem) for authentication

Example usage:
    python connectviaparamiko.py


Date: 2025-12-19
"""
import paramiko
from dotenv import load_dotenv
import os

load_dotenv()

def get_ssh_from_env():
    """
    Retrieves SSH connection details from environment variables.

    Returns:
        tuple: (ssh_host, ssh_user, ssh_key_path)

    Raises:
        ValueError: If any of the required environment variables are missing.
    """
    ssh_host = os.getenv("SSH_HOST")
    ssh_user = os.getenv("SSH_USER")
    ssh_key_path = os.getenv("SSH_KEY_PATH")

    if not all([ssh_host, ssh_user, ssh_key_path]):
        raise ValueError("missing SSH environment variables")
    
    return ssh_host, ssh_user, ssh_key_path

def connect_to_server():
    """
    Establishes an SSH connection to the remote server using Paramiko.

    Returns:
        paramiko.SSHClient: An active SSH client connected to the server.

    Prints:
        Error message and returns None if connection fails.
    """
    ssh_host, ssh_user, ssh_key_path = get_ssh_from_env()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=ssh_host,
            username=ssh_user,
            key_filename=ssh_key_path
        )
        return client
    except Exception as e:
        client.close()
        print(f"[ERROR]- {e}")
        return None
    
def run_remote_command(client, command: str):
    """
    Executes a command on the remote server via an active SSH client.

    Args:
        client (paramiko.SSHClient): Active SSH connection.
        command (str): The shell command to execute remotely.

    Returns:
        tuple: (stdout: str, stderr: str, exit_status: int)
            - stdout: Standard output from the command.
            - stderr: Standard error from the command.
            - exit_status: Exit code of the command (0 = success).
    """
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    return stdout.read().decode(), stderr.read().decode(), exit_status

def main():
    """
    Main function: connects to the server, runs a test command, prints output and errors,
    and closes the SSH connection safely.
    """
    client = connect_to_server()
    if not client:
        print("Connection failed")
        return

    try:
        commands = ["docker ps -a", "docker --version", "docker run =90949534"]
        for cmd in commands:
            out, err, code = run_remote_command(client,cmd)
            print("OUTPUT:\n", out)
            if code != 0:
                print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
