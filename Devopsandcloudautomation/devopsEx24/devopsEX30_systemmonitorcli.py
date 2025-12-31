"""
Exercise 30 — Simple Monitoring Dashboard (CLI)

This project intentionally focuses on understanding system responsibilities
rather than building a production-ready monitoring solution.

The goal was to explore how metrics collection, remote execution (SSH),
health evaluation, and user interaction fit together in a real-world style
workflow. Some responsibilities (such as alert thresholds and health logic)
are intentionally kept simple and colocated to avoid premature abstraction.

This design reflects a learning-first approach, prioritizing clarity,
completeness, and end-to-end functionality over perfect separation of concerns.
"""
import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

class SSHSystemMonitor():
    def __init__(self, ssh_client, log_path=None):
        self.__log_path = None
        self.__ssh_client = ssh_client
        self.__machine_name = self.__fetch_hostname()

    def __fetch_hostname(self):
        cmd = f"hostname -f"

        out, err, code = self.__ssh_client.execute_command(command=cmd)
        if code !=0:
            return None
        
        if not out:
            return None
        
        return out
    
    def get_host_name(self):
        return self.__machine_name

    def get_cpu_usage(self):
        cmd = f"cat /proc/stat | head -1 | awk '{{idle=$5; total=$2+$3+$4+$5+$6+$7+$8; print 100 - (idle*100/total)}}'"

        out, err, code = self.__ssh_client.execute_command(command=cmd)
        if code !=0:
            return None
        
        parsed_data = self.cpu_normaliser(out)

        return parsed_data
    
    def get_ram_usage(self):
        cmd = f"cat /proc/meminfo | head -3 | awk 'NR==1{{total=$2}} NR==3{{avail=$2}} END{{used=total-avail; print (used*100/total) \",\" total \",\" used}}'"

        out, err, code = self.__ssh_client.execute_command(command=cmd)
        if code !=0:
            return None
        
        parsed_data = self.disk_ram_normaliser(out)

        return parsed_data

    def get_disk_usage(self):
        cmd = f"df | awk '$6==\"/\"{{print $5+0 \",\" $2+0 \",\" $3+0}}'"

        out, err, code = self.__ssh_client.execute_command(command=cmd)
        if code !=0:
            return None

        parsed_data = self.disk_ram_normaliser(out)

        return parsed_data
    
    def kb_to_gb(self, kb_value: int):

        return round(kb_value/(1024*1024), 2)
    
    def cpu_normaliser(self, raw_data:str):
        
        if not raw_data:
            return None
        
        try:
            int_data = int(float(raw_data))
            return int_data
        except Exception as e:
            print(f"Could not parse due to - {e}")
            return None
    
    def disk_ram_normaliser(self, raw_data:str):

        if not raw_data:
            return None
        
        part = raw_data.strip().split(",")
        try:
            percentage = int(float(part[0]))
            total = int(float(part[1]))
            used = int(float(part[2]))
            return percentage, self.kb_to_gb(total), self.kb_to_gb(used)
        except Exception as e:
            print(f"Could not parse due to - {e}")
            return None

class SSHClientManager():
    def __init__(self, host:str=None, username:str=None, key_path=None):
        self.__client = None
        self.__host = host
        self.__username = username
        self.__key_path = key_path
        self.__connected = False
        
    
    def connect(self):
        if self.__connected:
            return True
        
        try:
            self.__client = paramiko.SSHClient()
            self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

            self.__client.connect(hostname=self.__host, username=self.__username, key_filename=self.__key_path)

            self.__connected = True
            print(f"Connection Established")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
        
    def execute_command(self, command):

        if not self.__connected:
            self.connect()

        
        stdin, stdout, stderr = self.__client.exec_command(command=command)
        exit_status = stdout.channel.recv_exit_status()

        return stdout.read().decode(), stderr.read().decode(), exit_status
    
    def disconnect(self):

        if self.__client:
            self.__client.close()
            self.__client = None
            self.__connected = False

class MonitorCLI():
    def __init__(self, system: "SSHSystemMonitor"):
        self.__system = system

    def options(self):
        print("1) CPU usage")
        print("2) RAM usage")
        print("3) Disk usage")
        print("4) Show all")
        print("5) Exit")
    
    def get_cpu(self):
        print("Fetching CPU usage...")
        cpu_usage = self.__system.get_cpu_usage()
        if not cpu_usage:
            print(f"Could not retrieve CPU data")
        
        print(f"CPU Usage: {cpu_usage}{" % ⚠️" if cpu_usage >= 90 else " %"}")

    def get_ram(self):
        print("Fetching RAM usage...")
        result = self.__system.get_ram_usage()
        if not result:
            print(f"Could not retrieve RAM data")

        percentage, total, used = result

        print(f"RAM Usage: {percentage}{" % ⚠️" if percentage >=10 else " %"}")
        print(f"({used} GB used of {total} GB)")

    def get_disk(self):
        print("Fetching Disk usage...")
        result = self.__system.get_disk_usage()
        if not result:
            print(f"Could not retrieve Disk data")
        
        percentage, total, used = result

        print(f"Disk Usage (/): {percentage}{" % ⚠️" if percentage >=90 else " %"}")
        print(f"({used} GB used of {total} GB)")
    
    def show_all(self):
        cpu_result = self.__system.get_cpu_usage()
        ram_result = self.__system.get_ram_usage()
        disk_result = self.__system.get_disk_usage()

    
        if not cpu_result:
            cpu_str = "CPU: Could not retrieve data"
        else:
            cpu_str = f"CPU Usage: {cpu_result}{' % ⚠️' if cpu_result >= 90 else ' %'}"

       
        if not ram_result:
            ram_str = "RAM: Could not retrieve data"
        else:
            ram_percentage, _, _ = ram_result
            ram_str = f"RAM Usage: {ram_percentage}{' % ⚠️' if ram_percentage >= 90 else ' %'}"

        
        if not disk_result:
            disk_str = "Disk: Could not retrieve data"
        else:
            disk_percentage, _, _ = disk_result
            disk_str = f"Disk Usage: {disk_percentage}{' % ⚠️' if disk_percentage >= 90 else ' %'}"

        
        print("Fetching system metrics...")
        print("-" * 40)
        print(cpu_str)
        print(ram_str)
        print(disk_str)
        print("-" * 40)
        print()
        
        all_metrics = {}
        if cpu_result:
            all_metrics["CPU"] = cpu_result
        if ram_result:
            all_metrics["RAM"] = ram_percentage  
        if disk_result:
            all_metrics["DISK"] = disk_percentage

        if all_metrics and all(m <= 90 for m in all_metrics.values()):
            print("System looks healthy ✅")
        else:
            for metric_name, value in all_metrics.items():
                if value > 90:
                    print(f"⚠️  Attention required: {metric_name} {value}% High")
        
    def execute(self):
        
        self.options()
        while True:
            try: 
                option = int(input("Enter choice: "))
                
                if option == 5:
                    break
                elif option == 1:
                    self.get_cpu()
                elif option == 2:
                    self.get_ram()
                elif option == 3:
                    self.get_disk()
                elif option == 4:
                    self.show_all()
                else:
                    self.options()             
            except (Exception, KeyboardInterrupt):
                print("\n")
                self.options()
                continue
                

if __name__=="__main__":

    ssh_client = SSHClientManager(
        host=os.getenv("SSH_HOST"),
        username=os.getenv("SSH_USER"),
        key_path=os.getenv("SSH_KEY_PATH")
    )

    system=SSHSystemMonitor(ssh_client=ssh_client)
    app = MonitorCLI(system=system)
    app.execute()

