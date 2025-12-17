import requests
import os
import base64
import githubapitolistrepos


def get_file_content(local_path: str):
    """
    Read a local file and return its Base64-encoded content.

    Args:
        local_path (str): Path to the local file to be uploaded.

    Returns:
        str | None:
            - Base64-encoded file content if successful
            - None if the file does not exist or cannot be read

    Notes:
        - GitHub API requires file content to be Base64-encoded.
        - This function assumes a text file.
    """
    if not os.path.exists(local_path):
        print(f"{local_path} does not exist")
        return None

    with open(local_path, "r") as file:
        content = file.read()
        encoded = base64.b64encode(content.encode()).decode()
        return encoded
            

def check_response(url:str, headers: str):
    """
    Send a GET request to a GitHub API endpoint and validate the response.

    Args:
        url (str): GitHub API URL to query.
        headers (dict): Authorization headers for the request.

    Returns:
        requests.Response | None:
            - Response object if the request is successful
            - None if an error occurs or the request is invalid

    Notes:
        - Handles common GitHub API errors (401, 403, 404).
        - Can be used as both a boolean check and a data provider.
    """
    if not headers:
        print("[ERROR] invalid header, please check")
        return None, None
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 401:
            print("[ERROR] 401 - Token invalid/expired")
            return None
        elif response.status_code == 403:
            print("[ERROR] 403 - Rate limited or insufficient permissions")
            return None
        elif response.status_code == 404:
            print("[ERROR] 404 - Resource not found")
            return None
        
        response.raise_for_status()

        return response
    
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection failed")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return None

def get_file_sha(api_url: str, header: str):
    """
    Retrieve the SHA of a file in a GitHub repository if it exists.

    Args:
        api_url (str): GitHub API URL for the file content endpoint.
        header (dict): Authorization headers.

    Returns:
        str | None:
            - SHA string if the file exists
            - None if the file does not exist or cannot be retrieved

    Notes:
        - SHA is required when updating an existing file via the GitHub API.
        - If no SHA is returned, the file will be created instead.
    """
    response=check_response(url=api_url, headers=header)
    if response:
        data = response.json()
        return data.get("sha")
    return None
        
def push_file(owner: str, repo_name: str, local_path: str, remote_path: str):
    """
    Create or update a file in a GitHub repository using the GitHub API.

    Args:
        owner (str): GitHub username or organization name.
        repo_name (str): Name of the repository.
        local_path (str): Path to the local file to upload.
        remote_path (str): Destination path inside the repository.

    Behavior:
        - Creates the file if it does not exist.
        - Updates the file if it already exists (using its SHA).
        - Prints the commit URL on success.

    Notes:
        - Uses Base64 encoding as required by GitHub.
        - Performs repository existence checks before uploading.
        - Designed for automation scripts, not interactive usage.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{remote_path}"
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"

    header = githubapitolistrepos.get_token()

    if not header:
        print("[ERROR] Header could not be established")
        return
    
    if not check_response(repo_url,headers=header):
        print("[ERROR] repo does not exist")
        return
    
    encoded_content = get_file_content(local_path=local_path)
    if not encoded_content:
        return
    
    payload = {
        "message": f"Add {remote_path} via API",
        "content": encoded_content
    }
    
    sha_data = get_file_sha(api_url=api_url, header=header)
    try:
        if sha_data:
            payload["sha"] = sha_data  
        
        response = requests.put(url=api_url, headers=header, json=payload)
        response.raise_for_status()
        
        commit_url = response.json().get("commit", {}).get("html_url")
        action = "Updated" if sha_data else "Created"
        print(f"{action}! Commit: {commit_url}")
        
    except Exception as e:
        print(f"[ERROR] failed: {e}")

if __name__=="__main__":

    header = githubapitolistrepos.get_token()
    repo = "mero-services"
    local_path = "Newprojects/Devopsandcloudautomation/devopsEx15/test_file.txt"
    owner="dillihang"
    remote_path="file.txt"

    push_file(owner=owner, repo_name=repo, local_path=local_path, remote_path=remote_path)

