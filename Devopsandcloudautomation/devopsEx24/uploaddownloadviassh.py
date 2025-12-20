import paramiko
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_ssh_from_env():
    """
    Read SSH connection details from environment variables.

    Expects the following environment variables to be set:
    - SSH_HOST: public IP or hostname of the server
    - SSH_USER: SSH username
    - SSH_KEY_PATH: path to the private SSH key file

    Returns:
        tuple[str, str, str]:
            A tuple containing (ssh_host, ssh_user, ssh_key_path)

    Raises:
        ValueError:
            If any required environment variable is missing.
    """
    ssh_host = os.getenv("SSH_HOST")
    ssh_user = os.getenv("SSH_USER")
    ssh_key_path = os.getenv("SSH_KEY_PATH")


    if not all([ssh_host, ssh_user, ssh_key_path]):
        raise ValueError("[ERROR] - Missing Enviornment variable/variables")

    return ssh_host, ssh_user, ssh_key_path

def ssh_to_server():
    """
    Establish an SSH connection to the remote server using Paramiko.

    The connection details are loaded from environment variables
    using `get_ssh_from_env()`.

    Returns:
        paramiko.SSHClient | None:
            An active SSHClient object if the connection succeeds,
            or None if the connection fails.
    """
    host, user, key_path = get_ssh_from_env()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            username=user,
            key_filename=key_path
        )
    except Exception as e:
        client.close()
        print(f"[ERROR] - Could not connect - {e}")
        return None

    return client


def upload_file(local_path: str, remote_path: str):
    """
    Upload a file from the local machine to the remote server via SFTP.

    This function:
    - Opens an SSH connection
    - Creates an SFTP session
    - Uploads the file to the given remote path
    - Closes the SFTP and SSH connections

    Existing files at the remote path will be overwritten.

    Args:
        local_path (str):
            Path to the local file to upload.
        remote_path (str):
            Destination path on the remote server.
    """
    client = ssh_to_server()

    if not client:
        print("[ERROR] - Connection Failed")
        return
    
    sftp = None
    try:
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        print(f"Uploaded {local_path} -> {remote_path}")
    except Exception as e:
        print(f"[ERROR] - {e}")
    finally:
        if sftp:
            sftp.close()
        client.close()


def download_file(remote_path: str, local_path: str):
    """
    Download a file from the remote server to the local machine via SFTP.

    If the local file already exists, a timestamp is appended to the
    filename to prevent overwriting.

    This function:
    - Ensures the local directory exists
    - Opens an SSH connection
    - Downloads the file using SFTP
    - Closes the SFTP and SSH connections

    Args:
        remote_path (str):
            Path to the file on the remote server.
        local_path (str):
            Destination path on the local machine.
    """
    dir_name = os.path.dirname(local_path)
    file_name = os.path.basename(local_path)

    if os.path.exists(local_path):
        print("File already exists, adding timestamp")

        name, ext = os.path.splitext(file_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{name}_{timestamp}{ext}"
        
        new_local_path = os.path.join(dir_name, new_filename)
    else:
        os.makedirs(dir_name, exist_ok=True)
        new_local_path = local_path

    client = ssh_to_server()

    if not client:
        print("[ERROR] - Connection Failed")
        return
    
    sftp = None
    try:
        sftp = client.open_sftp()
        sftp.get(remote_path, new_local_path)
        print(f"Downloaded {remote_path} → {new_local_path}")
    except Exception as e:
        print(f"[ERROR] - {e}")
    finally:
        if sftp:
            sftp.close()
        client.close()


if __name__=="__main__":

    upload_local_path = r"C:\Users\44746\Documents\Python\Newprojects\Devopsandcloudautomation\devopsEx24\file_send_ssh.txt"
    upload_remote_path = "/home/ec2-user/test_folder/file_send_ssh.txt"

    download_local_path = r"C:\Users\44746\Documents\Python\Newprojects\Devopsandcloudautomation\devopsEx24\ec2_download_file.txt"
    download_remote_path = "/home/ec2-user/test_folder/file_download.txt"



    # upload_file(local_path=upload_local_path, remote_path=upload_remote_path)
    download_file(remote_path=download_remote_path, local_path=download_local_path)