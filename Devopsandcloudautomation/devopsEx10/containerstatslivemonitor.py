import docker

class Containers:
    """
    A simple wrapper class around a Docker container object.
    
    This class stores the container's ID, name, and status.
    It also provides helper methods to refresh the container status
    and to fetch container statistics in streaming or snapshot mode.
    """
    def __init__(self, docker_container: object):
        """
        Initialise the Containers object.

        Args:
            docker_container: A Docker SDK container object.
        """
        self.__container = docker_container
        self.__id = docker_container.id
        self.__name = docker_container.name
        self.__status = docker_container.status

    @property     
    def id(self):
        """Return container ID."""
        return self.__id

    @property
    def name(self):
        """Return container name."""
        return self.__name

    @property
    def status(self):
        """
        Return the current container status.
        Status is refreshed before returning.
        """
        self.__container.reload()
        self.__status = self.__container.status
        return self.__status
    
    def refresh_status(self):
        """Reload the container's internal state from Docker."""
        self.__container.reload()

    def get_stats_stream(self):
        """
        Return a live streaming generator of stats.
        
        Returns:
            A generator that yields live container stats.
        """
        return self.__container.stats(stream=True, decode=True)
    
    def get_stats_snap(self):
        """
        Return a single snapshot of container stats.

        Returns:
            A dictionary of stats for the container.
        """
        stats = self.__container.stats(stream=False, decode=False)
        return stats
    
    def __str__(self):
        """Return a readable summary of the container."""
        return f"{self.__name} ({self.__id[:12]}) - {self.__status}"
    

class Monitoring_Container_app:
    """
    Main application class that handles listing containers,
    selecting containers, and monitoring their resource usage
    either live or as a one-time snapshot.
    """
    def __init__(self):
        """
        Initialise the monitoring application.

        Attempts to connect to Docker and load all containers.
        """
        try:
            self.__client = docker.from_env()
            self.__container_dict = {}
            self.__load_containers()
        except docker.errors.DockerException as e:
            print(f"Failed to connect to Docker: {e}")
            exit(1)
           
    def __load_containers(self):
        """
        Load all Docker containers into an internal dictionary.

        Each container is wrapped in a Containers object.
        """
        containers = self.__client.containers.list(all=True)
        if not containers:
            print("[ERROR] - no containers to load, please do the necessary checks")
        else:
            for c in containers:
                c_object = Containers(c)
                c_object.refresh_status()
                if c_object.id not in self.__container_dict:
                    self.__container_dict[c_object.id]=c_object
            print(f"Successfully loaded {len(self.__container_dict)} containers")

    def get_container_list(self):
        """
        Return a list of tuples containing container info.

        Returns:
            List of (name, status, id)
        """
        return [(c.name, c.status, c.id) for c in self.__container_dict.values()]
            
    def get_container_by_name(self, name: str):
        """
        Get a container object by its name.

        Args:
            name: The name of the container.

        Returns:
            A Containers object or None.
        """
        for c in self.__container_dict.values():
            if c.name == name:
                return c
            
    def display_containers(self):
        """
        Print all containers with their ID, name, and status.

        Returns:
            True if containers exist, False otherwise.
        """
        c_list = self.get_container_list()
        if not c_list:
            return False
        else:
            for name, status, id in c_list:
                print(f"ID: {id}, Name: {name}, Status: {status}")
            return True

    
    def get_selected_containers(self, names: str):
        """
        Convert a comma-separated string of names into container objects.

        Args:
            names: A string like "c1, c2"

        Returns:
            A list of Containers objects (or None for invalid names).
        """
        container_names = [n.strip() for n in names.split(",")]
        c_objs = []
        for name in container_names:
            container = self.get_container_by_name(name)
            if container:
                c_objs.append(container)
            else:
                 c_objs.append(None)

        return c_objs       

    def live_stream(self):
        """
        Display container resource stats live (streaming mode).

        Allows selecting one or multiple containers.
        Use Ctrl+C to stop monitoring a container.
        """
        if not self.display_containers():
            print("no containers available")
        
        names = input("Please enter the name or names (separated by ,) of the containers, ctrl+c to skip to next container: ").strip()
        if not names:
            print("Please enter a valid name")
        else:
            c_objs=self.get_selected_containers(names)
            for c_obj in c_objs:
                if not c_obj:
                    print("Name not found or invalid name")
                else:
                    try:
                        for stat in c_obj.get_stats_stream():
                            try:
                                cpu = stat.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage')
                                mem = stat.get('memory_stats', {}).get('usage')
                                networks = stat.get("networks", {})
                                net_rx = sum(n.get("rx_bytes", 0) for n in networks.values())
                                net_tx = sum(n.get("tx_bytes", 0) for n in networks.values())
                                print(f"Container: {c_obj.name} CPU: {cpu} | Mem: {mem:,} | Net: ↓{net_rx:,} ↑{net_tx:,}")
                            except Exception as e:
                                print(f"[ERROR] - {e}")

                    except (KeyboardInterrupt, EOFError):
                        print(f"\nStopped monitoring container {c_obj.name}")
                        continue
    
    def snap_shot(self):
        """
        Display a single stats snapshot for selected containers.

        Similar to calling `docker stats` once.
        """
        if not self.display_containers():
            print("no containers available")

        names = input("Please enter the name or names (separated by ,) of the containers: ").strip()
        if not names:
            print("Please enter a valid name")
        else:
            c_objs=self.get_selected_containers(names)
            for c_obj in c_objs:
                if not c_obj:
                    print("Name not found or invalid name")
                else:
                    stat = c_obj.get_stats_snap()  
                    try:
                        cpu = stat.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage')
                        mem = stat.get('memory_stats', {}).get('usage')
                        networks = stat.get("networks", {})
                        net_rx = sum(n.get("rx_bytes", 0) for n in networks.values())
                        net_tx = sum(n.get("tx_bytes", 0) for n in networks.values())
                        print(f"Container: {c_obj.name} CPU: {cpu} | Mem: {mem:,} | Net: ↓{net_rx:,} ↑{net_tx:,}")
                    except Exception as e:
                        print(f"[ERROR] - {e}")
    
    def execute(self):
        """
        Main application loop.

        Lets the user choose between:
        - live stream mode
        - snapshot mode
        - exit
        """
        print("1 - live stream")
        print("2 - snapshot")

        while True:
            try:
                command = input("please pick one fo the options, 1 or 2 or type exit to quit: ").strip()

                if command == "exit":
                    break
                elif command == "1":
                    self.live_stream()
                elif command == "2":
                    self.snap_shot()
                else:
                    continue
            except(KeyboardInterrupt, EOFError):
                print()
                continue

if __name__=="__main__":

    app = Monitoring_Container_app()
    app.execute()