"""
AWS Identity Verification Module

Provides a simple function to verify AWS credentials are valid
and can authenticate with the specified AWS region.

This is typically used as a safety check before executing
any AWS operations that require valid credentials.

Key Features:
- Validates AWS credentials via STS GetCallerIdentity
- Provides clear error messaging for authentication failures
- Regional validation (credentials must work in specified region)

Usage:
    Import and call verify_identity() before any AWS operations
    to ensure credentials are valid and avoid runtime errors.

Dependencies:
- boto3: AWS SDK for Python
"""
import boto3
import sys

DRY_RUN = True

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


if __name__=="__main__":
    REGION = "eu-north-1"
    verify_identity(region=REGION)