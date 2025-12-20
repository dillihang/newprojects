"""
Automated Docker Container Deployment via SSH

This script connects to a remote server using SSH (via Paramiko) and performs 
a complete Docker deployment workflow for a specified container. It handles 
pulling the latest image, checking if the container already exists, stopping 
and removing the old container if present, starting a new container, and 
verifying its logs.

Environment Variables:
- DOCKER_IMAGE: Full name of the Docker image to deploy.
- CONTAINER_NAME: Name of the container to create or update.
- SSH_HOST, SSH_USER, SSH_KEY_PATH: Used by `connectviaparamiko` for SSH connection.

Usage:
    python deploy_docker.py
"""
from dotenv import load_dotenv
import os
import connectviaparamiko

load_dotenv()

def get_dockerinfo_from_env():
    """
    Retrieves Docker deployment information from environment variables.

    Returns:
        tuple: (docker_image: str, container_name: str)
               Returns None if any variable is missing.
    """
    docker_image = os.getenv("DOCKER_IMAGE")
    container_name = os.getenv("CONTAINER_NAME")

    if not all([docker_image, container_name]):
        print("[ERROR] - Could not retrieve docker info from env")
        return
    
    return docker_image, container_name


def run_container(client, cmd: str, container_name: str):
    """
    Executes a command to start a Docker container on the remote server.

    Args:
        client (paramiko.SSHClient): Active SSH client connection.
        cmd (str): Docker run command to execute.
        container_name (str): Name of the container for logging.

    Returns:
        bool: True if the container started successfully, False otherwise.
    """
    out, err, code = connectviaparamiko.run_remote_command(client, cmd)
    print(f"[STEP] Starting new container...")
    if code == 0:
        print(f"OUTPUT:\n", out)
        print(f"[SUCCESS] Container {container_name} started\n")
        return True
    else:
        print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
        return False

def check_logs(client, cmd: str, container_name: str):
    """
    Retrieves and prints logs from a Docker container on the remote server.

    Args:
        client (paramiko.SSHClient): Active SSH client connection.
        cmd (str): Docker logs command to execute.
        container_name (str): Name of the container for logging.

    Returns:
        bool: True if logs were successfully retrieved, False otherwise.
    """
    out, err, code = connectviaparamiko.run_remote_command(client, cmd)
    print(f"[STEP] Verifying, getting log data for container {container_name}...")
    if code == 0:
        print(f"OUTPUT:\n", out)
        return True
    else:
        print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
        return False

def run_deploy():
    """
    Orchestrates the full Docker deployment workflow on the remote server.
    
    Steps:
        1. Connect to the server via SSH.
        2. Pull the latest Docker image.
        3. Check if the container exists.
            a. If it exists, stop and remove the old container.
        4. Start the new container.
        5. Retrieve and display container logs.
    """
    client = connectviaparamiko.connect_to_server()
    if not client:
        print("Connection failed")
        return
    
    docker_image, container_name = get_dockerinfo_from_env()

    commands = {
            "pull_image": f"docker pull {docker_image}", 
            "find_container": f"docker inspect {container_name}", 
            "stop_container": f"docker stop {container_name}", 
            "remove_container": f"docker rm {container_name}",
            "run_container": f"docker run --name {container_name} -d {docker_image}",
            "verify": f"docker logs {container_name}"
                }   
    
    # Pull Docker image
    out, err, code = connectviaparamiko.run_remote_command(client, commands["pull_image"])
    print("[STEP] Pulling docker image...")
    if code == 0:
        print(f"OUTPUT:\n", out)
        print("[SUCCESS] Image pulled\n")
    else:
        print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
        return
    
    # Check if container exists
    out, err, code = connectviaparamiko.run_remote_command(client, commands["find_container"])
    print(f"[STEP] finding existing container {container_name}...")
    if code == 0:
        print("container exists, starting stop and delete process\n")
        print(f"[STEP] Stopping old container")

        # Stop old container
        out, err, code = connectviaparamiko.run_remote_command(client, commands["stop_container"])
        if code == 0:
            print(f"OUTPUT:\n", out)
            print("[SUCCESS] old container stopped\n")
        else:
            print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
            return
        
        # Remove old container
        print(f"[STEP] Removing old container...")
        out, err, code = connectviaparamiko.run_remote_command(client, commands["remove_container"])
        if code == 0:
            print(f"OUTPUT:\n", out)
            print("[SUCCESS] old container removed\n")
        else:
            print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
            return
        
        if not run_container(client=client, cmd=commands["run_container"], container_name=container_name):
            return
        
        if not check_logs(client=client, cmd=commands["verify"], container_name=container_name):
            return

    elif code == 1:
        print(f"{container_name} does not exist...\n")

        if not run_container(client=client, cmd=commands["run_container"], container_name=container_name):
            return
        
        if not check_logs(client=client, cmd=commands["verify"], container_name=container_name):
            return

    else:
        print(f"[ERRORS]:\n, {err}\n[EXITCODE]: {code}\n")
        return
    

if __name__=="__main__":

    run_deploy()