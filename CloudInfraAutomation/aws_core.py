import boto3
import sys

def verify_identity(region: str) -> dict:
    """
    Verifies AWS credentials by attempting to get caller identity.
    
    Uses AWS Security Token Service (STS) GetCallerIdentity API
    to validate that the current AWS credentials are valid and
    can authenticate with the specified region.
    
    Args:
        region (str): AWS region code to validate credentials against
                     (e.g., 'eu-north-1', 'us-east-1')
    
    Returns:
        bool: True if credentials are valid and authentication succeeds
              False if GetCallerIdentity returns empty response
    
    Raises:
        SystemExit: If authentication fails completely (invalid credentials,
                   network issues, permission denied, etc.)
    
    Example:
        >>> if verify_identity("us-east-1"):
        ...     print("Credentials valid, proceeding...")
        ... else:
        ...     print("Credentials invalid or empty response")
    
    Note:
        - Exits the program with code 1 on authentication failure
        - Returns False only if STS returns empty identity (rare case)
        - Must have AWS credentials configured (~/.aws/credentials,
          environment variables, or IAM role)
    """
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        if identity:
            return True
        else:
            return False
    except Exception as e:
        print("[ERROR] AWS Authentication failed")
        print(e)
        sys.exit(1)
        return False

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
        Exits program on credential failure or API error
    """
    if not verify_identity(region=region):
        print(f"[ERROR] AWS credentials not valid")
        sys.exit(1)
    
    try:
        client = boto3.client(service, region_name=region)
        method = getattr(client, action)
        return method(**kwargs)

    except Exception as e:
        print(f"[ERROR] {service}.{action} failed - {e}")
        sys.exit(1)

def parse_ec2_data(response:dict)->list:
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
    results = []

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

def parse_iam_data(raw_response: dict) -> list:
    """
    Flatten IAM list_users response into structured dicts.

    Args:
        raw_response (dict): Response from iam.list_users()

    Returns:
        list: List of dicts with keys:
            - user_name
            - user_id
            - created_date
            - password_last_used
            - access_keys: empty list for now
            - console_access: None (to be populated later)
    """
    parsed = []

    for user in raw_response.get("Users", []):
        parsed.append({
            "user_name": user.get("UserName"),
            "user_id": user.get("UserId"),
            "created_date": user.get("CreateDate"),
            "password_last_used": user.get("PasswordLastUsed", None),
            "console_access": None,  # populate later
            "access_keys": []        # populate later
        })
    
    return parsed
        

