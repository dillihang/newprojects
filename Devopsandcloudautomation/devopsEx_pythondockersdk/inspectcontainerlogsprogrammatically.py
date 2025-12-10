"""
Docker Container Log Inspector

This script allows the user to inspect and stream logs from Docker containers
using the Docker SDK for Python.

Features:
- Lists all Docker containers on the host.
- Shows the last 5 lines of logs for each container.
- Allows the user to select a container and stream its logs in real-time.
- Supports two exit mechanisms:
    1. Ctrl+C: Stops the current log streaming and returns to the container selection menu.
    2. Typing 'exit': Quits the program entirely.
- Handles KeyboardInterrupt and EOFError gracefully to prevent crashes.
- Includes a small sleep in the streaming loop to allow responsive Ctrl+C handling.

Usage:
1. Run the script.
2. Observe the list of available containers and their recent logs.
3. Enter the container name to stream logs.
4. Press Ctrl+C to stop streaming and select another container, or type 'exit' to quit.
"""
import docker
import time

client = docker.from_env()
containers = client.containers.list(all=True)

if not containers:
    print("no containers!!!!!!!!!!!")

for c in containers:
    try:
        print(f"Container: {c.name}")
        logs_tail = c.logs(tail = 5)
        print(f"last 5 lines of the log:\n{logs_tail.decode("utf-8")}")
        print("-" * 40)
    except Exception as e:
            print(f"[ERROR] - {e}")


print(f"Available containers:")
for c in containers:
    print(c.name)

containers_dict = {c.name: c for c in containers}

while True:
        try:
           
            command = input("Please enter the the container name to stream the logs, or exit to quit: ")
        
            if command == "exit":
                break

            if command not in containers_dict:
                print(f"{command} does not exist")
                continue

            container_object = containers_dict[command]
            log_stream = container_object.logs(stream=True, follow=True)
            print(f"Streaming logs from {container_object.name}... Press Ctrl+C to stop.")
            try: 
                for line in log_stream:
                    print(line.decode("utf-8", errors="ignore").rstrip())
                    time.sleep(0.01)
            except KeyboardInterrupt:
                print("\nStreaming stopped by user.")
                
        except (KeyboardInterrupt, EOFError):
            print("\n")
            continue
            

    


# logs = container.logs()
# print(logs.decode("utf-8"))


# logs_tail = container.logs(tail=5)
# print(logs_tail.decode("utf-8"))


# for line in container.logs(stream=True):
#     print(line.decode("utf-8").strip())