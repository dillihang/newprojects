import boto3
import os

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="eu-west-1"
)

def check_bucket_exists(bucket_name: str):
    """
    Check if a bucket exists in the S3 instance.
    
    Args:
        bucket_name (str): Name of the S3 bucket.
        
    Returns:
        tuple: (exists (bool), response (dict))
            - exists: True if bucket exists, False otherwise
            - response: raw response from s3.list_buckets()
    """
    response = s3.list_buckets()
    
    bucket_name_list=[bucket["Name"] for bucket in response["Buckets"]]
    if bucket_name in bucket_name_list:
        return True, response
    
    return False, response

def print_bucket_list():
    """
    Print the names of all buckets in the S3 instance.
    """
    response = s3.list_buckets()

    for buckets in response["Buckets"]:
        print(buckets["Name"])

def create_buckets(bucket_name: str):
    """
    Create a new bucket if it does not already exist.
    
    Args:
        bucket_name (str): Name of the S3 bucket to create.
        
    Notes:
        Uses 'eu-west-1' region as the LocationConstraint.
        Prints current bucket list after creation.
    """
    torf, response = check_bucket_exists(bucket_name)

    if not torf:
        try:
            s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
            print(f"{bucket_name} created succesfully")
        except Exception as e:
            print(f"[ERROR] - {e}")
            
    else:
        print(f"{bucket_name} already exists")

    print_bucket_list()


def upload_objects(object_path: str, bucket_name: str, key_name: str):
    """
    Upload a file to a specified S3 bucket under a given key name.
    
    Args:
        object_path (str): Local file path to upload.
        bucket_name (str): S3 bucket to upload to.
        key_name (str): Key name under which to store the object.
        
    Notes:
        - Checks if the file exists locally.
        - Checks if the bucket exists.
        - Skips upload if the key already exists in the bucket.
    """
    if not os.path.exists(object_path):
        print("[ERROR] Please check the path or file if it exists")
        return
    
    torf, _ = check_bucket_exists(bucket_name)

    if not torf:
        print(f"{bucket_name} does not exist")
        return
    
    objects = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in objects:
        for obj in objects['Contents']:
            if obj['Key'] == key_name:
                print(f"[WARNING] Key '{key_name}' already exists in bucket '{bucket_name}'. Skipping upload.")
                return
    
    try:
        s3.upload_file(object_path, bucket_name, key_name)
        print(f"Uploaded {object_path} to {bucket_name}/{key_name}")
    except Exception as e:
        print(f"[ERROR] upload failed due to - {e}")


if __name__=="__main__":

    b1 = "my-first-bucket"
    b2 = "my-first-persistent-bucket"

    create_buckets(b1)
    create_buckets(b2)
  
    file1="Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/test.txt"
    file2="Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/myfile.txt"
    file3="Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/roadmap.txt"
    file4="Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/News_json.json"


    upload_objects(file1, b1, "test.txt")
    upload_objects(file2, b1, "myfile.txt")
    upload_objects(file3, b2, "roadmap.txt")
    upload_objects(file4, b2, "News_json.json")
    