import aws_core
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

IDLE_DAYS = 90  # Customize inactivity threshold


def enrich_iam_users(region: str, users: list):
    """
    Enrich IAM user data with console access info and access key last used.
    
    Args:
        region (str): AWS region
        users (list): List of user dicts from parse_iam_users
    
    Returns:
        list: Each dict now contains:
            - console_access (bool)
            - access_keys (list of dicts with AccessKeyId & LastUsed date)
    """
    enriched = []

    for user in users:
        user_name = user.get("user_name")
        user_copy = user.copy()

        # Check console access
        try:
            aws_core.aws_executor(
                service="iam",
                action="get_login_profile",
                region=region,
                UserName=user_name
            )
            user_copy["console_access"] = True
        except ClientError as e:
            # If login profile doesn't exist, assume no console access
            user_copy["console_access"] = False

        # Check access keys
        keys_info = []
        try:
            keys = aws_core.aws_executor(
                service="iam",
                action="list_access_keys",
                region=region,
                UserName=user_name
            )
            for key in keys.get("AccessKeyMetadata", []):
                key_id = key.get("AccessKeyId")
                # Get last used
                last_used = aws_core.aws_executor(
                    service="iam",
                    action="get_access_key_last_used",
                    region=region,
                    AccessKeyId=key_id
                )
                keys_info.append({
                    "AccessKeyId": key_id,
                    "LastUsedDate": last_used.get("AccessKeyLastUsed", {}).get("LastUsedDate")
                })
        except ClientError as e:
            keys_info = []

        user_copy["access_keys"] = keys_info
        enriched.append(user_copy)

    return enriched


def detect_idle_users(users: list, idle_days: int = IDLE_DAYS):
    """
    Categorize IAM users based on activity.
    
    Args:
        users (list): Enriched user dicts
        idle_days (int): Threshold to consider a user idle
    
    Returns:
        dict: Grouped by status
    """
    now = datetime.now(timezone.utc)
    idle_threshold = now - timedelta(days=idle_days)

    categorized = {
        "idle_users": [],
        "active_users": [],
    }

    for user in users:
        # Consider idle if no console access and all keys unused
        last_key_used_dates = [
            k.get("LastUsedDate") for k in user.get("access_keys", [])
            if k.get("LastUsedDate")
        ]

        most_recent_key_use = max(last_key_used_dates) if last_key_used_dates else None
        password_used = user.get("password_last_used")

        if (not user.get("console_access")) and \
           (not most_recent_key_use or most_recent_key_use < idle_threshold) and \
           (not password_used or password_used < idle_threshold):
            categorized["idle_users"].append(user)
        else:
            categorized["active_users"].append(user)

    return categorized


def main():
    region = "eu-north-1"

    # Step 1: Get raw IAM users
    raw_users = aws_core.aws_executor(service="iam", action="list_users", region=region)
    
    # Step 2: Parse users
    parsed_users = aws_core.parse_iam_data(raw_users)

    # Step 3: Enrich with console access and access key info
    enriched_users = enrich_iam_users(region=region, users=parsed_users)

    # Step 4: Categorize based on activity
    categorized = detect_idle_users(enriched_users)

    # Step 5: Print summary
    print("="*50)
    print(f"IAM User Hygiene Report - Region: {region}")
    print("="*50)

    for status, user_list in categorized.items():
        print(f"\n{status.upper()} ({len(user_list)})")
        for u in user_list:
            console = "Yes" if u.get("console_access") else "No"
            keys = u.get("access_keys", [])
            last_used_list = [
                k.get("LastUsedDate").strftime("%Y-%m-%d") if k.get("LastUsedDate") else "Never"
                for k in keys
            ]
            last_used_str = ", ".join(last_used_list) if last_used_list else "N/A"
            print(f"  - {u['user_name']:20} | Console: {console} | Keys Last Used: {last_used_str}")

    print("="*50)


if __name__ == "__main__":
    main()
