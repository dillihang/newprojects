import boto3
from datetime import datetime, timedelta, UTC
import os
from dotenv import load_dotenv
import listresourcesviacloudapi
import json


load_dotenv()

s3 = boto3.client(
       "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def get_response():
    """
    Attempt to connect to the S3 endpoint and retrieve the list of buckets.

    Returns:
        dict | None: The full boto3 response if the HTTP status is 200,
        otherwise None. Prints diagnostic messages for success, warnings,
        or errors.
    """
    try:
        response = s3.list_buckets()
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status == 200:
            print(f"Successful connection to s3 endpoint.")
            return response
        else:
            print(f"[WARNING] Unexpected status: {status}")
            return None
    except Exception as e:
        print(f"[ERROR] could not retrieve buckets - {e}")
        return None

def get_buckets():
    """
    Retrieve and print all available S3 buckets.

    Returns:
        list[dict]: A list of bucket dictionaries from AWS S3.
        Each item contains at minimum:
            - Name (str)
            - CreationDate (datetime)

    Notes:
        - Prints "No buckets found" if S3 returns an empty list.
        - Prints warnings if the response is malformed or missing keys.
        - Responsible only for fetching and displaying buckets.
    """
    bucket_list = []
    response = get_response()

    if response:
        if "Buckets" in response:
            buckets = response["Buckets"]

            if buckets:
                print(f"Found {len(buckets)} buckets:")
                for bucket in buckets:
                    print(f"Bucket Name: {bucket["Name"]} (Created: {(bucket["CreationDate"]).strftime("%Y-%m-%d %H:%M:%S")})")
                    bucket_list.append(bucket)
            else:
                print("No buckets found.")
        else:
            print("No 'Buckets' key in response")
    
    return bucket_list

def json_log(output_dict: dict, output_folder: str = "json_log"):
    """
    Save cleanup results to a timestamped JSON log file.

    Args:
        output_dict (dict): The structured data to write to the log.
        output_folder (str): Directory where logs will be stored.
                             Defaults to 'json_log'.

    Returns:
        str | None: The full path to the saved JSON file on success,
        otherwise None.

    Notes:
        - Creates the folder automatically if it does not exist.
        - Uses indent=2 for readability.
        - UTF-8 encoded output.
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"log_{timestamp}.json"
        final_path = os.path.join(output_folder, file_name)
        
    
        json_str = json.dumps(output_dict, indent=2, ensure_ascii=False)
        
     
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        
        print(f"✓ JSON log saved: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"[ERROR] Could not create log: {e}")
        return None
    

def cleanup_objects(older_than_days: int=30):
    """
    Delete S3 objects older than a given number of days across all buckets.

    Workflow:
        1. Retrieve all buckets.
        2. For each bucket:
            - List all objects.
            - Compare object LastModified with the time threshold.
            - Delete objects older than the threshold.
            - Log successful deletions and errors.
        3. Print a summary and write logs to a JSON file (if any objects were deleted).

    Args:
        older_than_days (int): Age threshold for deleting objects (default 30 days than older).
                               Objects older than this number of days are removed.

    Notes:
        - Buckets with no objects are skipped.
        - All deletion attempts (success or failure) are logged.
        - If no objects are deleted, no JSON log file is created.
    """
    deleted_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    cleanup_log = {
        "Timestamp": deleted_time,
        "Threshold_days": older_than_days, 
        "Deleted_objects": [],
        "Error_deleting": [],
        "Buckets_processed": []  
    }
    
    bucket_list = get_buckets()
    deleted_count=0
    error_deleting=0

    if not bucket_list:
        return

    if bucket_list:
        for bucket in bucket_list:
            bucket_name=bucket["Name"]
            cleanup_log["Buckets_processed"].append(bucket_name)
            print(f"\n=== Processing bucket: {bucket_name} ===")

            try:
                object_response = s3.list_objects_v2(Bucket=bucket_name)

                if not "Contents" in object_response:
                    print(f"No objects available for {bucket_name}")
                    continue
                
                date_threshold = datetime.now(UTC) - timedelta(days=older_than_days)

                for obj in object_response["Contents"]:
                    obj_key = obj.get("Key", "Unknown")
                    obj_lastmodified = obj.get("LastModified", None)

                    if obj_lastmodified is None:
                        print(f"[Warning] Skipping {obj_key} - no LastModified date")
                        continue

                    if obj_lastmodified < date_threshold:
                        try:
                            s3.delete_object(Bucket=bucket_name, Key=obj_key)
                            print(f"Deleted Object: {obj_key} last modified was {obj_lastmodified} from Bucket: {bucket_name} and is older than {date_threshold}")
                            deleted_count+=1
                            cleanup_log["Deleted_objects"].append({
                                        "bucket": bucket_name,
                                        "key": obj_key,
                                        "last_modified": obj_lastmodified.isoformat() if obj_lastmodified else None,
                                        "deleted_at": datetime.now(UTC).isoformat()
                                    })
                        except Exception as delete_error:
                            print(f"[ERROR] failed to delete {obj_key}: {delete_error}")
                            error_deleting+=1
                            cleanup_log["Error_deleting"].append({
                                        "bucket": bucket_name,
                                        "key": obj_key,
                                        "error_time": datetime.now(UTC).isoformat(),
                                        "error_message": str(delete_error),
                                        "error_type": type(delete_error).__name__, 
                                        "last_modified": obj_lastmodified.isoformat() if obj_lastmodified else None,
                                    })
              
            except Exception as e:
                print(f"[ERROR] Could not process bucket '{bucket_name}': {e}")
    
    print(f"\n{'='*50}")
    print(f"CLEANUP SUMMARY")
    print(f"{'='*50}")
    print(f"Total deleted: {deleted_count}")
    if error_deleting > 0:
        print(f"Errors encountered: {error_deleting}")
    
    if deleted_count == 0:
        print("No objects were deleted.")
    print(f"\n{'='*50}")
    print("Buckets summary after cleanup")
    print(f"{'='*50}")
    listresourcesviacloudapi.list_buckets_data()

    if deleted_count>0:
        print(f"\n{'='*50}")
        json_log(output_dict=cleanup_log)
        print(f"{'='*50}")
    else:
        print(f"\n{'='*50}")
        print("No log file generated")
        print(f"{'='*50}")


if __name__=="__main__":

    cleanup_objects(0)