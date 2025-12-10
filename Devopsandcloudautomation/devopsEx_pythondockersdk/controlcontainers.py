import docker

client = docker.from_env()


containers = client.containers.list(all=True)

for c in containers:
    try:
        c.reload()
        if c.status != "running":
            print(f"Starting container {c.name}...")
            c.start()
            print(f"Container {c.name} started succesfully")
        else:
            print(f"container {c.name} is already running")

    except Exception as e:
        print(f"[ERROR] - {e}")

print()

for c in containers:
    try:
        c.reload()
        if c.status == "running":
            print(f"Stopping container {c.name}...")
            c.stop()
            print(f"container {c.name} stopped succesfully")
        else:
            print(f"container {c.name} is already stopped")
    
    except Exception as e:
        print(f"[ERROR] - {e}")

print()

try:
    container = client.containers.get("gracious_galois")
    container.reload()
    print(f"container {container.name} found")

    if container.status =="running":
        print(f"container status is running")
        print(f"stopping the container..")
        container.stop()
        print(f"container stopped")
        container.remove()
        print(f"container {container.name} has been removed")
    else:
        container.remove()
        print(f"container {container.name} has been removed")

except Exception as e:
    print(f"[ERROR] - {e}")