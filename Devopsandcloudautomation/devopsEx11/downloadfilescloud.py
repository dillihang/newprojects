import boto3
import os
import authrequestcloudapi
import listresourcesviacloudapi
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# def verify_files(object_dict, download_path: str):
#     """
#     Compare downloaded local files with the metadata of objects retrieved from S3.

#     This function scans all files under the specified download directory and checks:
#       - That the count of downloaded files matches the number of S3 objects.
#       - That each file's size matches the size reported by S3.

#     Parameters
#     ----------
#     object_dict : dict
#         A dictionary mapping object keys (str) to file sizes (int) as reported by S3.
#         Example:
#             {
#                 "folder/file.txt": 1234,
#                 "image.png": 4567
#             }

#     download_path : str
#         The root directory where S3 objects were downloaded.

#     Returns
#     -------
#     bool
#         True if all files exist and their sizes match.
#         False if any file is missing or mismatched.
#     """
#     print("Verifying files....")
#     downloaded_dict={}
#     downloaded_files = glob.glob(f"{download_path}/**", recursive=True)

#     for item in downloaded_files:
#         if not os.path.isfile(item):
#             continue
#         rel_path = os.path.relpath(item, download_path)

#         if rel_path in object_dict:
#             item_size = os.path.getsize(item)
#             downloaded_dict[rel_path]=item_size
    
#     if len(object_dict) != len(downloaded_dict):
#         print(f"File count mismatch: {len(object_dict)} vs {len(downloaded_dict)}")
#         return False
    
#     all_match = True

#     for name, downloaded_size in downloaded_dict.items():
#         s3_file_size = object_dict.get(name)

#         if downloaded_size != s3_file_size:
#             print(f"File size mismatch for '{name}': {downloaded_size} vs {s3_file_size} bytes")
#             all_match=False
#         else:
#             print(f"downloaded file {name}: {downloaded_size} matches s3 file {name}: {s3_file_size}")
    
#     return all_match

def verify_files(object_dict, download_path: str):
    """
    Verify that all downloaded files exist locally and match the expected sizes
    reported by S3.

    Unlike directory-scanning methods, this function directly checks only the
    files that *should* exist (based on the metadata dictionary produced during
    downloading). This makes the verification process efficient even when the
    download directory contains many unrelated files.

    Each downloaded file path is constructed using the S3 object key combined
    with the timestamp applied during the download step.

    Notes
    -----
    Part of your custom module workflow using:
        - `authrequestcloudapi`
        - `listresourcesviacloudapi`

    Parameters
    ----------
    object_dict : dict
        Mapping of expected downloaded filenames (including timestamp suffixes)
        to their S3 sizes.
        Example:
            {
                "file_20241210_235959.txt": 1024,
                "data/report_20241210_235959.json": 54321
            }

    download_path : str
        Root directory where files were downloaded.

    Returns
    -------
    bool
        True if all files exist and sizes match.
        False if any file is missing or mismatched.
    """
    print("verifying files....")
    all_good=True

    for object_key, object_size in object_dict.items():
        local_path = os.path.join(download_path, object_key)
        
        if not os.path.exists(local_path):
            print(f"{object_key}: file missing")
            all_good=False
            continue

        try:
            local_file_size = os.path.getsize(local_path)
        except OSError:
            print(f"{object_key}: Cannot read file")
            all_good = False
            continue

        if local_file_size == object_size:
            print(f"s3 file {object_key}: {object_size} bytes matches with downloaded {local_path}: {local_file_size} bytes")
        else:
            print(f"[WARNING] - s3 file {object_key}: {object_size} bytes missmatch with downloaded {local_path}: {local_file_size} bytes")
            all_good=False
    
    if all_good:
        print(f"\n All {len(object_dict)} files verified successfully!")
    else:
        print(f"\n Verification failed for some files")
    
    return all_good


def download_allobjects(bucket_name: str, download_path: str):
    """
    Download every object from an S3 bucket into a local directory, rename them
    with a timestamp for versioned downloads, and verify their integrity.

    Workflow
    --------
    This function automates a full S3 → local transfer pipeline with versioning:

      1. Ensure the download root directory exists.
      2. Validate that the bucket exists using your custom module
         `authrequestcloudapi`.
      3. Retrieve all S3 objects using `list_objects_v2`.
      4. Recreate any necessary folder structure locally based on the object key.
      5. Append a timestamp (YYYYMMDD_HHMMSS) to each downloaded file to avoid
         overwriting previous downloads.
         Example:
             "data/report.json" → "data/report_20241210_235959.json"
      6. Download each object individually.
      7. Build a verification dictionary:
            {
                "report_20241210_235959.json": <size_from_s3>,
                ...
            }
      8. Pass this mapping to `verify_files()` to confirm file existence and size.

    Notes
    -----
    This function is part of your custom project structure and depends on:
        - `authrequestcloudapi`
            (your own module for bucket creation, checking, uploads)
        - `listresourcesviacloudapi`
            (your own module for printing S3 bucket contents)

    The timestamp renaming ensures that multiple runs of this script never
    overwrite previously downloaded files, enabling a versioned archival system.

    Parameters
    ----------
    bucket_name : str
        Name of the S3 bucket from which to download objects.

    download_path : str
        Local directory where objects should be downloaded.
        Subdirectories matching the S3 key structure will be created
        automatically.

    Returns
    -------
    None
        Output is printed directly. Errors for individual objects are caught
        and logged so the download process can continue.
    """
    object_dict={}

    try:
        os.makedirs(download_path, exist_ok=True)
    except OSError as e:
        print(f"[ERROR] - {e}")
        return
    
    torf, _ = authrequestcloudapi.check_bucket_exists(bucket_name=bucket_name)

    if not torf:
        print(f"{bucket_name} does not exist")
        return
    
    object_response = s3.list_objects_v2(Bucket=bucket_name)

    if "Contents" not in object_response:
        print(f"{bucket_name} has no objects to download")

    for obj in object_response["Contents"]:
        try:
            check_dir = os.path.dirname(obj["Key"])
            full_path = os.path.join(download_path, obj["Key"])
                                     
            if check_dir:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            base, ext = os.path.splitext(full_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path =f"{base}_{timestamp}{ext}"

            s3.download_file(bucket_name, obj["Key"], new_path)
            print(f"Downloaded: {obj["Key"]} → {new_path}")

            obj_name = obj.get("Key", None)
            base1, ext1 = os.path.splitext(obj_name)
            new_obj_ver = f"{base1}_{timestamp}{ext1}"
            obj_size = obj.get("Size", 0)
            object_dict[new_obj_ver]=obj_size
        except Exception as e:
            print(f"[ERROR] Download failed {obj["Key"]} - {e}")
            continue
    print()

    verify_files(object_dict, download_path)
    

if __name__=="__main__":

    new_bucket="ex13-bucket"
    file_to_upload = [("Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/new_file.txt", "new_file.txt"),
                      ("Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/roadmap.txt", "roadmap.txt"),
                      ("Newprojects/Devopsandcloudautomation/devopsEx11/randomobjects/News_Json.json", "new_json.json")
                      ]

    authrequestcloudapi.create_buckets(new_bucket)
    print()
    authrequestcloudapi.print_bucket_list()
    print()
    for path, key_name in file_to_upload:
        authrequestcloudapi.upload_objects(object_path=path,bucket_name=new_bucket,key_name=key_name)
    print()
    listresourcesviacloudapi.list_bucket_by_name(new_bucket)
    print()

    download_path = "Newprojects/Devopsandcloudautomation/devopsEx11/downloadedobjects"
    download_allobjects(new_bucket,download_path)