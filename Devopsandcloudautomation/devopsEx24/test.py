import psutil


cpu = psutil.cpu_percent()
ram = psutil.virtual_memory()
disk = psutil.disk_usage("D:\\")
disk_part = psutil.disk_partitions()

print(disk)