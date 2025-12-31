"""
Exercise 27 — Remote System Monitoring Script

This script connects to a remote server via SSH and collects
basic system health metrics:

- CPU usage
- Memory usage
- Disk usage

Each metric is evaluated against a predefined threshold and
reported with optional warning labels.

The script is read-only and safe to run repeatedly.
It is designed as a foundation for future monitoring,
alerting, and automation workflows.
"""
import connectviaparamiko

def get_cpu_usage(client):
    """
    Retrieves the current CPU usage percentage from the remote server.

    The CPU usage is calculated by parsing the output of the `top` command
    and subtracting the idle percentage from 100.

    Args:
        client (paramiko.SSHClient): Active SSH client connection.

    Returns:
        int | None:
            - CPU usage percentage as an integer if successful
            - None if the command fails or parsing is unsuccessful
    """
    out, err, code=connectviaparamiko.run_remote_command(client=client, command="top -bn1 | grep 'Cpu(s)'")
    if code != 0:
        print(err)
        return None
    else:
        if not out:
            print("Could not retrieve data")
            return None
        try:
            part = out.split(",")
            return int(100-float(part[3].strip().strip("id")))
        except Exception as e:
            print(f"[ERROR] - {e}")
            return None
        

        # top -bn1 | grep "Cpu(s)" | awk '{idle=$8; print 100-idle}'
        
def get_memory_usage(client):
    """
    Retrieves the current memory usage percentage from the remote server.

    Memory usage is calculated using the `free` command and expressed
    as a percentage of total memory used.

    Args:
        client (paramiko.SSHClient): Active SSH client connection.

    Returns:
        int | None:
            - Memory usage percentage as an integer if successful
            - None if retrieval or parsing fails
    """
    out, err, code=connectviaparamiko.run_remote_command(client=client, command="free -m | grep 'Mem' | awk '{print ($3/$2)*100}'")
    if code != 0:
        print(err)
        return None
    else:
        if not out:
            print("[ERROR] Could not retrieve data")
            return None
        try:
            return (int(float(out.strip())))
        except ValueError:
            print(f"[ERROR] Failed to convert: {out}")
            return None

def get_disk_usage(client):
    """
    Retrieves the disk usage percentage for the root filesystem
    on the remote server.

    Uses the `df` command and extracts the usage percentage.

    Args:
        client (paramiko.SSHClient): Active SSH client connection.

    Returns:
        int | None:
            - Disk usage percentage as an integer if successful
            - None if retrieval or parsing fails
    """
    out, err, code=connectviaparamiko.run_remote_command(client=client, command="df -h / | awk 'NR==2 {print $5+0}'")
    if code != 0:
        print(err)
        return None
    else:
        if not out:
            print("[ERROR] Could not retrieve data")
            return None
        try:
            return (int(float(out.strip())))
        except ValueError:
            print(f"[ERROR] failed to conver: {out}")
            return None

def get_data():
    """
    Collects system health metrics from the remote server.

    Establishes an SSH connection, gathers CPU, memory, and disk usage,
    and safely closes the connection afterward.

    Returns:
        dict:
            A dictionary containing raw metric values:
            {
                "CPU Usage": int | None,
                "Memory Usage": int | None,
                "Disk Usage": int | None
            }

            Returns an empty dictionary if the connection fails.
    """
    client = connectviaparamiko.connect_to_server()

    if not client:
        return {}
    
    summary_dict={}
    try:
        summary_dict["CPU Usage"] = get_cpu_usage(client=client)
        summary_dict["Memory Usage"] = get_memory_usage(client=client)
        summary_dict["Disk Usage"] = get_disk_usage(client=client)
    finally:
        client.close()
    
    return summary_dict

def alert_check(data: dict):
    """
    Evaluates collected system metrics against predefined thresholds.

    Metrics that exceed their threshold are marked with a warning label.
    Missing or invalid metrics are reported accordingly.

    Args:
        data (dict): Dictionary of raw metric values.

    Returns:
        dict:
            A dictionary with formatted metric values suitable for display.
    """
    threshold_dict={
        "CPU Usage": 80,
        "Memory Usage": 10,
        "Disk Usage": 5
    }
    for key, value in data.items():
        try:
            if value is not None and value >= threshold_dict[key]:
                data[key]=f"{value}% [WARNING]"
            elif value is None:
                data[key]=f"None value - could not retrieve data"
            else:
                data[key]=f"{value}%"
        except Exception as e:
            print(f"[WARNING] could not process {key} - {e} skipping...")
            continue
            
    return data

def print_summary():
    """
    Generates and prints a formatted system health report.

    Retrieves system metrics, applies alert checks,
    and displays the final results in a readable summary format.
    """
    raw_data=get_data()

    if not raw_data:
        print("[ERROR] No data collected")
        return

    alerted_data = alert_check(raw_data)

    print(f"\n{'='*40}")
    print("SYSTEM HEALTH REPORT")
    print(f"{'='*40}")
    for key, value in alerted_data.items():
        print(f"{key}: {value}")

    
if __name__=="__main__":

    print_summary()

#     CHECKS = [
#     {
#         "label": "CPU Usage",
#         "command": "...",
#         "parser": cpu_parser,
#         "threshold": 80
#     },
#     ...
# ]
