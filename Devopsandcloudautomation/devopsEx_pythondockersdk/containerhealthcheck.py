"""
Docker Container Health Checker with Color Output

This script inspects and displays the status and health of Docker containers 
on the host machine using the Docker SDK for Python. 

Features:
- Lists all containers with their status and health.
- Health statuses are color-coded:
    - Green: healthy
    - Red: unhealthy
    - Yellow: starting
    - Cyan: no health check configured
- Interactive mode allows the user to select a container to check its health.
- Handles Ctrl+C gracefully to exit the interactive mode.
"""
from colorama import init, Fore, Style
import docker

client = docker.from_env()

containers = client.containers.list(all=True)


def get_colored_health_status(container):
    """
    Get the health status of a container and return it as a color-coded string.

    Args:
        container (docker.models.containers.Container): A Docker container object.

    Returns:
        str: Color-coded health status:
            - Green "healthy"
            - Red "unhealthy"
            - Yellow "starting"
            - Cyan for containers with no health check
    """
    health_info = container.attrs.get("State", {}).get("Health", {})
    health_status = health_info.get("Status", "No health check configured")
    
    if health_status == 'healthy':
        return f"{Fore.GREEN}✓ {health_status}{Style.RESET_ALL}"
    elif health_status == 'unhealthy':
        return f"{Fore.RED}✗ {health_status}{Style.RESET_ALL}"
    elif health_status == 'starting':
        return f"{Fore.YELLOW} {health_status}{Style.RESET_ALL}"
    else:  
        return f"{Fore.CYAN}{health_status}{Style.RESET_ALL}"


def everything_check():
    """
    Display all containers with their current status and health.

    Iterates through all Docker containers on the host and prints:
    - Container name
    - Status (running, exited, paused, etc.)
    - Color-coded health status
    """
    for c in containers:
        colored_status = get_colored_health_status(c)
        print(f"Container : {c.name}")
        print(f"status: {c.status}")
        print(f"Health: {colored_status}")
        print("-" * 40)


def interactive_checker():
    """
    Interactive container health checker.

    Allows the user to:
    - View the list of available containers.
    - Enter a container name to display its status and health.
    - Continues prompting until Ctrl+C is pressed to exit.
    - Handles invalid container names gracefully.
    """
    print("list of containers: ")
    for c in containers:
        print(f" - {c.name}")
    
    containers_dict = {c.name: c for c in containers}

    if containers_dict:
        while True:
            try:
                command = input("Please enter the container name or ctrl+c to exit: ")

                if command not in containers_dict:
                    print("no such container")
                    print("available containers: ")
                    for c in containers_dict:
                        print(f" - {containers_dict[c].name}")
                
                else:
                    container_object = containers_dict[command]

                    colored_status = get_colored_health_status(container_object)
                    print(f"Container : {container_object.name}")
                    print(f"status: {container_object.status}")
                    print(f"Health: {colored_status}")
                    print("-" * 40)

            except KeyboardInterrupt:
                print("\nExitting...")
                break
    else:
        print("no containers available")



if __name__=="__main__":

    everything_check()
    interactive_checker()