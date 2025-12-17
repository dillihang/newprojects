import requests
import os
from dotenv import load_dotenv
import paginatedapifetcher
import json

load_dotenv()

def get_token():
    """
    Retrieve GitHub API authentication headers from environment variables.

    Reads the GIT_TOKEN value from the environment and constructs
    the required headers for authenticated GitHub API requests.

    Returns:
        dict | None:
            - Dictionary containing Authorization and User-Agent headers
            - None if the token is missing

    Notes:
        - Expects GIT_TOKEN to be set in a .env file or environment
        - Prints a helpful error message if the token is not found
    """
    token = os.getenv("GIT_TOKEN")

    if token is None:
        print("[ERROR] GIT_TOKEN environment variable not found")
        print("Please create a .env file with: GIT_TOKEN=your_token_here")
        return None

    return {"Authorization": f"Bearer {token}",
            "User-Agent": "my-python-script"
            }
   
def check_response():
    """
    Perform a basic authenticated request to the GitHub repositories API.

    Validates the GitHub token by making a request to the
    /user/repos endpoint and handling common HTTP errors.

    Returns:
        requests.Response | None:
            - Response object if the request succeeds
            - None if authentication fails or an error occurs

    Handles:
        - 401: Invalid or expired token
        - 403: Rate limiting or insufficient permissions
        - 404: Resource not found
        - Network and timeout errors
    """
    headers = get_token()
    print(headers)

    if not headers:
        print(f"[ERROR] No header data")
        return None

    try:
        response = requests.get("https://api.github.com/user/repos", headers=headers, timeout=5)
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

def get_data():
    """
    Fetch repository data from GitHub after validating the API response.

    Calls check_response(), safely parses the JSON body,
    and returns both the parsed data and the raw response.

    Returns:
        tuple:
            - list | None: Parsed JSON repository data
            - requests.Response | None: Raw HTTP response

    Notes:
        - Handles invalid JSON responses gracefully
        - Returns (None, None) if the request fails
    """
    response = check_response()
    if not response:
        return None, None
    
    try:
        data = response.json()
        return data, response
    except ValueError as e:
        print(f"[ERROR] Invalid JSON response: {e}")
        print(f"Could not retreive any data")
        return None, response
    
def summary_data():
    """
    Display a formatted summary of the authenticated user's repositories.

    Retrieves repository data from GitHub and prints:
        - Repository name
        - Visibility (public/private)
        - Primary language
        - Last push timestamp

    Additional Info:
        - Extracts pagination and rate-limit metadata using
          the imported paginatedapifetcher utility
        - Repositories are sorted by most recently pushed

    Output:
        - Human-readable table printed to the console

    Notes:
        - Pagination is not performed in this exercise
        - The imported pagination helper is used only for metadata
    """
    data, response = get_data()

    if not (response and data):
        return
    
    # print(json.dumps(data, indent=2))

    pages, ratelimit = paginatedapifetcher.check_api_info(response=response, response_body=data)
    user_name = [repo.get("owner").get("login") for repo in data][0]

    print(f"\n{'='*100}")
    print(f"Repo summary for user: {user_name} \npages: {pages if pages else "No page data"}, current ratelimit: {ratelimit}")
    print(f"Total repositories: {len(data)}")
    print(f"{'='*100}")
    print(f"{"NAME":<30} {"VISIBILITY":<12} {"LANGUAGE":<12} {"LAST PUSH":<12}")
    print(f"{"-"*100}")
    for r in sorted(data, key=lambda x:x["pushed_at"], reverse=True):
        name = r["name"]
        visibility = "Private" if r["private"] == True else "Public"
        language = r.get("language") or "Unknown"
        last_pushed = r["pushed_at"]
        print(f"{name:<30} {visibility:<12} {language:<12} {last_pushed:<12}")

if __name__=="__main__":

    summary_data()

    