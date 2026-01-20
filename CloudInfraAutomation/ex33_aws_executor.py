import boto3
import sys
import ex32_aws_saftey_check
import json
from datetime import datetime

DRY_RUN = True

def aws_executor(service:str, action:str, region:str, **kwargs)-> dict:
    """
    Generic AWS service executor with credential validation.
    
    Executes any boto3 client method with safety checks and error handling.
    Validates AWS credentials before attempting any API calls.
    
    Args:
        service (str): AWS service name (e.g., 'ec2', 's3', 'rds')
        action (str): boto3 client method name (e.g., 'describe_instances')
        region (str): AWS region code (e.g., 'eu-north-1')
        **kwargs: Arbitrary keyword arguments passed to the AWS method
    
    Returns:
        dict: AWS API response as dictionary
    
    Raises:
        SystemExit: If credentials are invalid or API call fails
        Exception: Propagates boto3 exceptions with context
    
    Example:
        >>> response = aws_executor(
        ...     service="ec2",
        ...     action="describe_instances",
        ...     region="us-east-1",
        ...     InstanceIds=["i-12345678"]
        ... )
    
    Note:
        Always validates credentials via ex32_aws_saftey_check first
        Exits program on credential failure or API error
    """
    if not ex32_aws_saftey_check.verify_identity(region=region):
        print(f"[ERROR] AWS credentials not valid")
        sys.exit(1)
    
    try:
        client = boto3.client(service, region_name=region)
        method = getattr(client, action)
        return method(**kwargs)

    except Exception as e:
        print(f"[ERROR] {service}.{action} failed - {e}")
        sys.exit(1)
  

def parse_ec2_data(response:dict)->dict:
    """
    Parses AWS EC2 describe_instances response into structured data.
    
    Extracts key instance attributes from the nested AWS response structure
    into a flat list of dictionaries for easier processing.
    
    Args:
        response (dict): Raw response from ec2.describe_instances()
    
    Returns:
        list: List of dictionaries, each containing:
            - InstanceID (str): EC2 instance ID
            - InstanceType (str): Instance type (e.g., t2.micro)
            - LaunchTime (datetime): Instance launch timestamp
            - State (str): Current state (running, stopped, etc.)
            - name_tag (str/None): Value of 'Name' tag if exists
    
    Example Response:
        [
            {
                "InstanceID": "i-12345678",
                "InstanceType": "t2.micro",
                "LaunchTime": datetime(2024, 1, 1, 12, 0, 0),
                "State": "running",
                "name_tag": "web-server-01"
            }
        ]
    
    Note:
        Handles missing tags gracefully (returns None for name_tag)
        Preserves datetime objects for LaunchTime
    """
    results=[]

    for reservations in response["Reservations"]:
        for instance in reservations["Instances"]:
            parsed_dict={}
            parsed_dict["InstanceID"] = instance.get("InstanceId", None)
            parsed_dict["InstanceType"] = instance.get("InstanceType", None)
            parsed_dict["LaunchTime"] = instance.get("LaunchTime", None)
            parsed_dict["State"] = instance.get("State", {}).get("Name", None)
            tags = instance.get("Tags", [])
            name_tag = [tag["Value"] for tag in tags if tag.get("Value")]
            parsed_dict["name_tag"] = name_tag[0] if name_tag else None
            results.append(parsed_dict)

    return results

def main():
    """
    Demonstration function for AWS executor and EC2 parser.
    
    Shows example usage of aws_executor() and parse_ec2_data()
    by fetching all EC2 instances in a region and displaying
    them in a formatted table.
    
    Workflow:
        1. Fetch EC2 instances from AWS
        2. Parse response into structured data
        3. Display formatted inventory table
    
    Output:
        Prints a table with columns:
        ID, Name, State, Type, LaunchTime
    
    Note:
        This is a demonstration - customize for production use
        The DRY_RUN constant is declared but not used in this example
    """
    region = "eu-north-1"
    response = aws_executor(service="ec2", region=region, action="describe_instances")

    if not response:
        print(f"[ERROR] Could not get any response")
        return

    result = parse_ec2_data(response=response)

    print("="*50)
    print(f"EC2 Inventory - Region: {region}")
    print("="*50)

    print(f"{'ID':20} {'Name':20} {'State':10} {'Type':10} {'LaunchTime':20}")
    print("-"*85)

    sorted_by_state = sorted(result, key=lambda x:x["State"])

    for item in sorted_by_state:
        if item["LaunchTime"] is not None:
            actual_date = item["LaunchTime"]
            formated_date = actual_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formated_date = None
        print(f"{item["InstanceID"]:20} {item["name_tag"]:20} {item["State"]:10} {item["InstanceType"]:10} {formated_date}")

if __name__=="__main__":
    main()

    result =  aws_executor(
    service="ec2",
    action="describe_instances",
    region="eu-north-1",
    InstanceIds=["i-klfjlsdk"]
    )

