import docker

client = docker.from_env()

containers = client.containers.list(all=True)

for c in containers:
    print(c.id, c.name, c.status)