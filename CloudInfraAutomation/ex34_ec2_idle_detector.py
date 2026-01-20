"""
EC2 Idle Instance Detector and Terminator

This module identifies idle EC2 instances based on age and state,
categorizes them, and optionally terminates stopped instances that
exceed a specified idle threshold.

Key Features:
- Detects stopped instances older than specified days
- Categorizes instances by state and idle status
- Supports dry-run mode for safe testing
- Provides detailed inventory reports

Usage:
    Set DRY_RUN = False to perform actual terminations
    Configure idle_days to control termination threshold
"""
import ex32_aws_saftey_check
import ex33_aws_executor
from datetime import datetime, timedelta, timezone

DRY_RUN = True

def fetch_aws_data(service:str, action:str, region:str)->dict:
    """
    Orchestrates AWS data retrieval and initial processing.
    
    Args:
        service (str): AWS service name (e.g., 'ec2')
        action (str): AWS API action (e.g., 'describe_instances')
        region (str): AWS region code (e.g., 'eu-north-1')
    
    Returns:
        dict: raw response data or None if retrieval fails
    
    Raises:
        None: Returns None on any failure
    """
    if not ex32_aws_saftey_check.verify_identity(region=region):
        return None
    
    response = ex33_aws_executor.aws_executor(
                                             service=service, 
                                             action=action, 
                                             region=region
                                             )

    if not response:
        print(f"[INFO] could not retrieve any data")
        return None
    
    return response

def parse_to_ec2_data(raw_data:dict)->list:
    
    parsed_data = ex33_aws_executor.parse_ec2_data(response=raw_data)

    return parsed_data

def categorize_data(parsed_data:list, idle_days:int)->list:
    """
    Categorizes EC2 instances based on state and idle status.
    
    Args:
        parsed_data (list): List of EC2 instance dictionaries
        idle_days (int): Number of days to consider an instance idle
    
    Returns:
        dict: Categorized instances with keys:
            - 'stopped': All stopped instances
            - 'active': Running instances launched within idle_days
            - 'possible_idle': Running instances older than idle_days
    
    Note:
        Uses UTC timezone for consistent date comparisons
    """
    categorized_data = {"stopped":[], "active":[], "possible_idle":[]}

    threshold_date = datetime.now(timezone.utc) - timedelta(days=idle_days) 

    for instance in parsed_data:
        if instance["State"] == "stopped":
            categorized_data["stopped"].append(instance)
        elif instance["State"] == "running":
            if instance["LaunchTime"] < threshold_date:
                categorized_data["possible_idle"].append(instance)
            else:
                categorized_data["active"].append(instance)

    return categorized_data


def action_planner(categorized_data, idle_days:int)->dict:
    """
    Creates action plan based on categorized instances.
    
    Args:
        categorized_data (dict): Output from categorize_data()
        idle_days (int): Age threshold for termination (days)
    
    Returns:
        dict: Action plan with keys:
            - 'terminate_list': Instance IDs to terminate
            - 'start_list': Instance IDs to start (not implemented)
            - 'stop_list': Instance IDs to stop (not implemented)
    
    Note:
        Currently only plans termination of stopped instances
        older than idle_days. Start and stop actions are placeholders.
    """
    action_plan = {
        "terminate_list": [],
        "start_list": [],
        "stop_list": [],
    }

    threshold_date = datetime.now(timezone.utc) - timedelta(days=idle_days)

    for state, instance_list in categorized_data.items():
        if state == "stopped":
            for instance in instance_list:
                if instance["LaunchTime"]<threshold_date:
                    action_plan["terminate_list"].append(instance["InstanceID"])
    
    return action_plan

def ec2_terminate(region:str, instance_id_list:list, dryrun=DRY_RUN):
    """
    Terminates EC2 instances with safety controls.
    
    Args:
        region (str): AWS region code
        instance_id_list (list): List of EC2 instance IDs to terminate
        dryrun (bool): If True, only simulates termination (default: DRY_RUN)
    
    Returns:
        bool: True if successful (or simulated success in dry-run),
              False if actual termination fails
    
    Safety:
        - When dryrun=True: Only prints simulation, no AWS calls
        - When dryrun=False: Makes actual termination API calls
        - DRY_RUN global constant provides default safety
    """
    if dryrun:
        print(f"[DRY RUN] Would terminate {len(instance_id_list)} instances:")
        for inst_id in instance_id_list:
            print(f"  - {inst_id}")
        return True
  
    try:
        ex33_aws_executor.aws_executor(
            service="ec2",
            action="terminate_instances",
            region=region,
            InstanceIds=instance_id_list,
            DryRun=False
        )
        print(f"[SUCCESS] Terminated {len(instance_id_list)} instances")
        return True
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return False

def ec2_apply_action(region: str, action_plan: dict, dryrun=DRY_RUN):
    """
    Executes actions specified in the action plan.
    
    Args:
        region (str): AWS region code
        action_plan (dict): Action plan from action_planner()
        dryrun (bool): Passed to individual action functions
    
    Returns:
        dict: Results dictionary with action categories as keys
              and boolean success status as values
    
    Note:
        Currently only implements termination actions.
        Start and stop actions are stubbed for future implementation.
    """
    if not action_plan:
        print("[INFO] No data to apply action")
        return
    
    results = {}
    
    for category, id_list in action_plan.items():
        if not id_list:
            print(f"[INFO] No instances in {category}")
            continue
            
        if category == "terminate_list":
            results[category] = ec2_terminate(region, id_list, dryrun)
        elif category == "start_list":
            pass
        elif category == "stop_list":
            pass
    
    return results


def main():
    """
    Main execution function for EC2 idle instance management.
    
    Workflow:
        1. Retrieve EC2 instance data from AWS
        2. Categorize instances by state and idle status
        3. Create termination plan for old stopped instances
        4. Display inventory and planned actions
        5. Execute actions (simulated or real based on DRY_RUN)
        6. Display results
    
    Configuration:
        - Set DRY_RUN global variable for safety
        - Adjust idle_days to control termination threshold
        - Modify region for different AWS regions
    
    Example Output:
        Displays inventory, action plan, and execution results
        in a formatted console output
    """
    service = "ec2"
    action = "describe_instances"
    region = "eu-north-1"
    idle_days = 5000

    raw_data = fetch_aws_data(service=service, action=action, region=region)
    if not raw_data:
        return
    
    parsed_data = parse_to_ec2_data(raw_data=raw_data)
    
    cat_data = categorize_data(parsed_data=parsed_data, idle_days=idle_days)
    planned_data = action_planner(categorized_data=cat_data, idle_days=idle_days)

    # Print inventory
    print("="*50)
    print(f"EC2 Inventory - Region: {region}")
    print("="*50)
    
    for category, instance_list in cat_data.items():
        for instance in sorted(instance_list, key=lambda x:x["State"]):
            launch_time = instance["LaunchTime"]
            formatted_date = launch_time.strftime("%Y-%m-%d %H:%M:%S") if launch_time else "N/A"
            print(f"{category:15} - ID: {instance['InstanceID']:20} Name: {instance['name_tag']:15} State: {instance['State']:10} Launch: {formatted_date}")
    
    print("="*50)
    print("Action Plan:")
    for action_type, ids in planned_data.items():
        print(f"  {action_type}: {ids}")
    
    print("="*50)
    print("[INFO] Applying actions...")
    results = ec2_apply_action(region=region, action_plan=planned_data, dryrun=DRY_RUN)
    
    print("="*50)
    print("Results:")
    if results:
        for action_type, success in results.items():
            print(f"  {action_type}: {'Success' if success else 'Failed'}")
    else:
        print("  No actions performed")
    
    print("="*50)
            

if __name__=="__main__":

    main()
    
