import requests
import time
import re

def github_get(url: str, timeout: int = 5):
    """
    Send a GET request to a GitHub API URL with consistent error handling.

    Args:
        url (str): The API endpoint to request.
        timeout (int): Timeout for the request in seconds. Defaults to 5.

    Returns:
        tuple:
            - dict | None: Parsed JSON response if available, otherwise None.
            - requests.Response | None: The raw response object if successful, otherwise None.

    Notes:
        - Automatically raises and prints HTTP-related errors.
        - Safely attempts JSON parsing and warns if it fails.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            print(f"[WARNING] Could not parse JSON: {e}")
            return None, response

        return data, response

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection failed")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return None, None

def initial_data_check(user_name: str):
    """
    Perform the first API request to check user validity, pagination,
    and rate-limit information.

    Args:
        user_name (str): GitHub username.

    Returns:
        tuple:
            - int | None: Number of pages available.
            - int | None: Remaining rate limit.

    Notes:
        - Handles JSON parsing and empty response cases.
        - Delegates header parsing to `check_api_info()`.
    """
    the_url = f"https://api.github.com/users/{user_name}/repos?page=1&per_page=30"

    data, response = github_get(the_url)

    if data is None or response is None:
        return None, None

    if not data:
        print("[ERROR] Empty data returned.")
        return None, None

    return check_api_info(response, data)


def get_data(user_name: str, page_no: int):
    """
    Fetch one or all pages of a user's public repositories.

    Args:
        user_name (str): GitHub username.
        page_no (int): Page number to fetch. If falsy, fetches all pages.

    Returns:
        list: A list of pages, where each page is a list of repo dictionaries.

    Notes:
        - Applies a 2-second delay between full-page fetches to respect rate limits.
        - Uses `github_get()` for uniform request handling.
    """
    data_list = []

    if not page_no:
        # Fetch ALL pages
        page = 1
        while True:
            url_again = (
                f"https://api.github.com/users/{user_name}/repos?page={page}&per_page=30"
            )
            data, response = github_get(url_again)

            if data is None or not data:
                break

            data_list.append(data)
            page += 1
            time.sleep(2)

    else:
        # Fetch ONE page
        url_again = (
            f"https://api.github.com/users/{user_name}/repos?page={page_no}&per_page=30"
        )
        data, response = github_get(url_again)
        if data:
            data_list.append(data)

    return data_list


def check_api_info(response, response_body):
    """
    Extract pagination and rate-limit data from a GitHub API response.

    Args:
        response (requests.Response): The HTTP response object.
        response_body (dict): Parsed JSON body.

    Returns:
        tuple:
            - int | None: Detected number of pages.
            - int | None: Remaining rate limit.

    Notes:
        - Searches multiple possible header formats.
        - Includes fallbacks for APIs that return rate limits inside JSON.
    """
    rate_limit_remaining = None
    pages_no = None
    headers = response.headers

    # Try Link header first
    if headers.get("Link"):
        link_header = headers["Link"]
        pages_no = extract_page_num(link_header)

    # Try standard pagination headers
    if headers.get("X-Total-Pages"):
        pages_no = int(headers["X-Total-Pages"])
    if headers.get("Total-Pages"):
        pages_no = int(headers["Total-Pages"])

    # Try "Last" header if exists
    if headers.get("Last"):
        link_header = headers["Last"]
        pages_no = extract_page_num(link_header)

    # Rate-limit headers
    try:
        rate_limit_remaining = int(
            headers.get("X-RateLimit-Remaining")
            or headers.get("RateLimit-Remaining")
        )
    except:
        rate_limit_remaining = None

    # Fallback rate limit from body (rare)
    if not rate_limit_remaining:
        try:
            rate_limit_remaining = int(
                response_body.get("rate_limit", {}).get("remaining")
                or response_body.get("quota", {}).get("remaining")
                or response_body.get("limits", {}).get("remaining")
                or response_body.get("meta", {}).get("rate_limit", {}).get("remaining")
                or response_body.get("remaining")
            )
        except Exception:
            rate_limit_remaining = None

    return pages_no, rate_limit_remaining


def extract_page_num(link_header: str):
    """
    Extract the final page number from a GitHub Link header.

    Args:
        link_header (str): The raw "Link" header.

    Returns:
        int | None: The last page number if found, otherwise None.

    Notes:
        - Checks common parameter patterns: `page`, `p`, `page_num`.
        - Returns the last page number extracted.
    """
    try:
        # GitHub-style pattern
        page_numbers = re.findall(r"[?&]page=(\d+)", link_header)
        if page_numbers:
            return int(page_numbers[-1])

        # Fallback patterns
        for param in ["p=", "page_num="]:
            page_numbers = re.findall(r"[?&]" + param + r"(\d+)", link_header)
            if page_numbers:
                return int(page_numbers[-1])

        return None

    except (ValueError, AttributeError, TypeError):
        return None


def print_data(user_name: str, data_list: list):
    """
    Print summary data for fetched repositories, including top 5 repos.

    Args:
        user_name (str): GitHub username.
        data_list (list): List of pages (each page is a list of repo dicts).

    Notes:
        - Flattens all pages.
        - Sorts repos by stargazer count descending.
    """
    all_repos = []

    total_repo_extracted = sum(len(repo) for repo in data_list)
    for page in data_list:
        all_repos.extend(page)

    all_repos = sorted(all_repos, key=lambda x: x["stargazers_count"], reverse=True)

    print(f"Retrieved {total_repo_extracted} repos for user {user_name}")
    print("Top 5:")

    for repo in all_repos[:5]:
        # careful with quotes here
        print(f"{repo['name']} (⭐ {repo['stargazers_count']}, {repo['language']})")


def user_UX():
    """
    Handle user interaction and orchestrate the full GitHub fetch workflow.

    Steps:
        - Ask for GitHub username
        - Perform initial API validation
        - Check pagination and rate limit
        - Ask user whether to fetch all pages or one page
        - Fetch data accordingly
        - Print final results

    Notes:
        - Includes user-friendly warnings and input validation.
    """
    user_name = input("Please enter the GitHub username: ").strip()
    if not user_name:
        print("[ERROR] Username cannot be empty")
        return

    page_no, rate_remaining = initial_data_check(user_name)

    if not page_no or not rate_remaining:
        print(f"Total pages: {page_no} and rate remaining: {rate_remaining}")
        print("[WARNING] Could not detect page count or rate limit reliably.")
        yes_no = input("Continue anyway? yes/no: ").strip().lower()
        if yes_no == "no":
            return
        elif yes_no == "yes":
            data_list = get_data(user_name, None)
        else:
            print("[ERROR] Invalid input.")
            return
    else:
        # Safe conditions
        if rate_remaining >= page_no:
            print(f"Total pages: {page_no}, Rate remaining: {rate_remaining}")
            yes_no = input("Enter 'all' for everything or a page number: ").strip().lower()
            if yes_no == "all":
                data_list = get_data(user_name, None)
            else:
                try:
                    page_input = int(yes_no)
                    data_list = get_data(user_name, page_input)
                except ValueError:
                    print("[ERROR] Invalid page number.")
                    return
        else:
            print(f"Total pages: {page_no}, Rate remaining: {rate_remaining}")
            print("Cannot fetch all pages due to rate limit.")
            try:
                page_input = int(input(f"Enter a page number 1–{page_no} or 0 to cancel: "))
                if page_input <= 0:
                    return
                if page_input > page_no:
                    print("[ERROR] Page too high.")
                    return
                data_list = get_data(user_name, page_input)
            except ValueError:
                print("[ERROR] Invalid input.")
                return

    print_data(user_name, data_list)


if __name__ == "__main__":
    user_UX()
