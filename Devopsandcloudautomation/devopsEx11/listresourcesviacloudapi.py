import boto3
from datetime import datetime

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="eu-west-1"
)

def list_buckets_data():
    """
    List all S3 buckets and their objects along with metadata.
    
    Prints for each bucket:
        - Bucket name
        - Creation date
        - Objects inside with:
            - Object name (Key)
            - Size in KB
            - Last modified timestamp
    
    Notes:
        - Uses 'list_objects_v2' to fetch objects.
        - Handles empty buckets and missing metadata safely.
    """
    response = s3.list_buckets()

    if not response:
        print("No buckets inside the s3")
        return

    for bucket in response["Buckets"]:
        print(f"Bucket Name: {bucket["Name"]} (Created: {(bucket["CreationDate"]).strftime("%Y-%m-%d %H:%M:%S")})")
        
        object_response = s3.list_objects_v2(Bucket=bucket["Name"])
        if not "Contents" in object_response:
            print(f"No objects inside {bucket["Name"]}")
        else:
            print("Contents:")
            for obj in object_response["Contents"]:
                obj_name = obj.get("Key", None)
                obj_size = obj.get("Size", 0)/1024
                obj_lastmodified = obj.get("LastModified", None)
                if obj_lastmodified:
                    formatted_date = obj_lastmodified.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_date = obj_lastmodified
                print(f"Object name: {obj_name}, Size: {obj_size:.2f} kb, Last modified: {formatted_date}")
            print()

def list_bucket_by_name(bucket_name:str):
    response = s3.list_buckets()

    if not response:
        print("No buckets inside the s3")
        return

    found_bucket = None

    for bucket in response["Buckets"]:
        if bucket_name == bucket["Name"]:
            found_bucket = bucket
            break
    
    if not found_bucket:
        print(f"Bucket Name: {bucket_name} does not exist")
        return
    
    print(f"Bucket Name: {found_bucket["Name"]} (Created: {(found_bucket["CreationDate"]).strftime("%Y-%m-%d %H:%M:%S")})")

    object_response = s3.list_objects_v2(Bucket=found_bucket["Name"])

    if not "Contents" in object_response:
        print(f"No objects inside {found_bucket["Name"]}")
    else:
        print("Contents:")
        for obj in object_response["Contents"]:
            obj_name = obj.get("Key", None)
            obj_size = obj.get("Size", 0)/1024
            obj_lastmodified = obj.get("LastModified", None)
            if obj_lastmodified:
                formatted_date = obj_lastmodified.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_date = obj_lastmodified
            print(f"Object name: {obj_name}, Size: {obj_size:.2f} kb, Last modified: {formatted_date}")
        print()
    


if __name__=="__main__":

    list_buckets_data()
    