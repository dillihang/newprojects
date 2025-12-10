"""
Exercise 9b — Docker Networking (Python SDK)

This script demonstrates basic Docker networking using the Python Docker SDK.
It performs the following steps:

1. Assumes a Docker network named 'exercise_network' exists (or can be created separately).
2. Starts two containers: 
   - 'app' (Alpine Linux, acts as client)
   - 'db' (e.g., Nginx, acts as server)
3. Ensures containers are running.
4. Shows all containers attached to the network.
5. Tests connectivity by pinging the server from the client container.
6. Demonstrates container lifecycle management:
   - Stop container
   - Remove container
   - Recreate container and re-test connectivity
7. Reloads the network object to reflect changes in attached containers.

Requirements:
- Docker installed and running.
- Python Docker SDK (`pip install docker`).
- Existing images: 'alpine' and 'nginx' (or pull automatically).

Notes:
- This is beginner-friendly, interactive-style code focusing on networking concepts.
- The script highlights:
  - Network inspection
  - Exec command execution in a container
  - Ping connectivity
  - Container creation, removal, and reattachment to a network
"""
import docker
import time

client = docker.from_env()


def create_network():
    network = client.networks.create("exercise_network", driver="bridge")
    print(f"{network} created")

def create_containers():
    app = client.containers.run("alpine", name="app", detach=True, network="exercise_network", command="tail -f /dev/null")
    print(f"{app} created and added to the network excersie_network")
    # db_container = client.containers.run("nginx", name="db", detach=True, network="exercise_network")
    # print(f"{db_container} created and added to the network excersie_network")


def test_network():

    network = client.networks.get("exercise_network")

    app_container = client.containers.get("app")
    db_container = client.containers.get("db")

    if app_container.status != "running":
        app_container.start()
    
    if db_container.status != "running":
        db_container.start()
    
    for c in network.containers:
        print(c.name)

    result = app_container.exec_run("ping -c 5 db")
    print("Ping result:", result.output.decode())

    app_container.stop()

    network.reload()

    for c in network.containers:
        print(c.name)

    time.sleep(4)
    app_container.remove()

    time.sleep(4)

    network.reload()

    for c in network.containers:
        print(c.name)

    app_new = client.containers.run("alpine", name="app_new", detach=True, network="exercise_network", command="tail -f /dev/null")
    print(f"{app_new} created and added to the network excersie_network")

    time.sleep(4)
    network.reload()

    for c in network.containers:
        print(c.name)

    result = app_new.exec_run("ping -c 5 db")
    print("Ping result:", result.output.decode())

if __name__=="__main__":

    test_network()
