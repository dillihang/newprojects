"""
Docker Container Inspection & Interactive Command Runner

This script connects to the local Docker engine, finds all running containers,
and performs a set of predefined inspections on each one:

1. Lists the root directory inside the container using:     ls /
2. Gets the Python version (if installed) using:            python --version
3. Reads a file located at:                                /data/myfile.txt

After the automatic inspection, the script provides an
interactive shell-like interface that lets the user manually run
one of the following commands inside any running container:

    - "ls /"
    - "python --version"
    - "cat /data/myfile.txt"
    - "exit"

This demonstrates how to:
    • Connect to Docker from Python
    • Retrieve container objects
    • Execute commands inside containers using exec_run()
    • Decode command output
    • Handle errors safely
    • Build a simple interactive CLI to control containers

Requires:
    pip install docker

Author: (your name if you want)
"""
import docker

client = docker.from_env()

containers = client.containers.list(all=True)

# --- AUTOMATIC INSPECTION PHASE ---
for c in containers:
    if c.status == "running":

        try:
            filepath = c.exec_run("ls /")
            ver = c.exec_run("python --version")

            exit_code, output_bytes = c.exec_run("cat /data/myfile.txt")
            file_content = output_bytes.decode("utf-8")
            
            print(f"Container: {c.name}")
            print(f"directories in root: \n{filepath[1].decode("utf-8")}")
            print(f"python version - {ver[1].decode("utf-8").strip()}")
            print(f"Exit code: {exit_code}")
            print(f"File content:\n{file_content}")
            print("-" * 40)
        except Exception as e:
            print(f"[ERROR] - {e}")

# Build a quick lookup table for running containers
running_containers = {c.name: c for c in containers if c.status == "running"}

# --- INTERACTIVE COMMAND SHELL ---
if running_containers:
    print(f"{len(running_containers)} running containers found")
    for name, c in running_containers.items():
        print(name)
    while True:
                name = input("please enter the container name: ").strip()
                command = input("Enter a command to run inside container: ").strip().lower()

                if name in running_containers:
                    container_object = running_containers[name]

                    if command == "ls /":
                        _, output_bytes = container_object.exec_run("ls /")
                        file_content = output_bytes.decode("utf-8")

                        print(f"Container: {container_object.name}")
                        print(f"directories in root: \n{file_content}")
                    
                    elif command == "python --version":
                        _, output_bytes = container_object.exec_run("python --version")
                        ver = output_bytes.decode("utf-8")

                        print(f"Container: {container_object.name}")
                        print(f"Python version: {ver}")
                    
                    elif command == "cat /data/myfile.txt":
                        exitcode, output_bytes = container_object.exec_run("cat /data/myfile.txt")
                        file_content = output_bytes.decode("utf-8")

                        print(f"Continer: {container_object.name}")
                        print(f"Exit code: {exitcode}")
                        print(f"file content: {file_content}")

                    elif command == "exit":
                        break
                    
                    else:
                        print("Pick between ls /, python --version, cat /data/myfile.txt or exit")
                        continue

                else:
                    print(f"{name} does not exist")
                    print("Available containers: ")
                    for name in running_containers:
                        print(f" - {name}")
                    continue
  
else:
     print("no running containers found")


