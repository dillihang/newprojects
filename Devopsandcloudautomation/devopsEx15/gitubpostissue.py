import requests
import os
from dotenv import load_dotenv
import githubapitolistrepos

load_dotenv()

def get_header():
    """
    Retrieve the authorization headers required for GitHub API requests.

    This function delegates token retrieval to the shared authentication
    utility defined in `githubapitolistrepos`.

    Returns
    -------
    dict | None
        A dictionary containing HTTP headers for authentication, or None
        if the token could not be retrieved.
    """

    return githubapitolistrepos.get_token()

def create_issue(owner: str, repo: str, title: str, body: str):
    """
    Create a new GitHub issue in the specified repository.

    This function sends an authenticated POST request to the GitHub
    Issues API endpoint and creates an issue with the given title and body.

    On success, the function prints:
        - The issue number assigned by GitHub
        - The public URL of the created issue

    Parameters
    ----------
    owner : str
        GitHub username or organization that owns the repository.
    repo : str
        Name of the repository where the issue will be created.
    title : str
        Title of the issue.
    body : str
        Body/description of the issue.

    Returns
    -------
    None
        Output is printed directly. Errors are handled and reported.
    """
    header = get_header()

    if not header:
        print("Header could not be established")
        return
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    pay_load = {"title": title,
                "body": body,
                }
    try:
        response = requests.post(url, headers=header, json=pay_load)
        response.raise_for_status()

        data=response.json()
        print(f"issue #{data["number"]}")
        print(f"{data["html_url"]}")

    except requests.exceptions.HTTPError as e:   
        if response.status_code == 401:
            print("[ERROR] 401 - Token invalid/expired")
            return None
        elif response.status_code == 403:
            print("[ERROR] 403 - Rate limited or insufficient permissions")
            return None
        elif response.status_code == 404:
            print("[ERROR] 404 - Resource not found")
            return 
        
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection failed")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return

if __name__=="__main__":

    title = "Test issue from API"
    body = "This issue was created via a Python script."

    create_issue(owner="dillihang", repo="mero-services", title=title, body=body)