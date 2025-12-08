import requests
import random
import string

def api_get(url: str, timeout: int = 5):
    """
    Fetch data from a REST API endpoint with comprehensive error handling.
    
    Args:
        url (str): The complete URL to fetch data from
        timeout (int): Request timeout in seconds (default: 5)
        
    Returns:
        tuple: (data, response) where:
            data (dict/list): Parsed JSON data if successful, None otherwise
            response (requests.Response): Raw HTTP response object for debugging
            
    Raises:
        Prints error messages but doesn't raise exceptions to allow graceful failure
        
    Example:
        >>> data, response = api_get("https://api.example.com/data")
        >>> if data:
        >>>     print(f"Got {len(data)} items")
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

def user_id_to_location(user_id):
    """
    Convert a numeric user ID to a warehouse location code.
    
    Generates a random letter (A-Z) combined with the user_id number.
    Note: This creates non-deterministic locations for the same user_id.
    
    Args:
        user_id (int): Numeric user identifier
        
    Returns:
        str: Location code in format "L#" where L is random letter, # is user_id
        
    Example:
        >>> user_id_to_location(5)  # Could return "A5", "B5", "Z5", etc.
        "C5"
    """
    location_letters = string.ascii_uppercase
    location_id = user_id
    return f"{random.choice(location_letters)}{location_id}"

def get_data(url: str):
    """
    Extract and transform data from an API endpoint.
    
    Fetches data from the URL, validates required fields, and prepares it
    for loading into the inventory system. Invalid items are logged separately.
    
    Args:
        url (str): API endpoint to fetch data from
        
    Returns:
        tuple: (data_list, skipped_list) where:
            data_list (list): List of tuples (location, name, quantity) for valid items
            skipped_list (list): List of dictionaries with invalid items and reasons
            
    Validation Rules:
        - userId, title, and body fields must not be None
        - Title must be 100 characters or less
        - Quantity is calculated as length of body content
        
    Example:
        >>> data, skipped = get_data("https://jsonplaceholder.typicode.com/posts")
        >>> print(f"Valid: {len(data)}, Skipped: {len(skipped)}")
    """
    data_list = []
    skipped_list = []

    data, _ = api_get(url)

    if not data:
        print("There is no data to process")
        return

    if data:
        for items in data:
            location_id = items.get("userId", None)
            name = items.get("title", None)
            description = items.get("body", None)
            
            if location_id is None or name is None or description is None:
                skipped_list.append({
                "location_id": location_id,  
                "name": name,   
                "body": description,
                "skipped due to": "data cannot be None"  
                })
                continue  
            
            if len(name)>100:
                skipped_list.append({
                    "location_id": location_id,
                    "name": name,
                    "body": description,
                    "skipped due to": "Name length is more than 100 characters"
                })
                continue

            location_str = user_id_to_location(location_id)
            quantity = len(description)

            data_list.append((location_str, name, quantity))
    
    return data_list, skipped_list
        
def post_data_to_API(from_url: str, send_url: str):
    """
    ETL pipeline: Extract from source API, Transform, Load to target API.
    
    Orchestrates the complete data pipeline:
    1. Extract data from source API
    2. Transform and validate data
    3. Load valid data to target inventory API
    
    Args:
        from_url (str): Source API URL to extract data from
        send_url (str): Target API URL to post data to
        
    Returns:
        None: Prints summary statistics to console
        
    Output:
        - Success/Failure counts for posted items
        - List of skipped items with reasons
        - Detailed error messages for failed posts
        
    Example:
        >>> post_data_to_API(
        >>>     "https://jsonplaceholder.typicode.com/posts",
        >>>     "http://localhost:5000/inventory"
        >>> )
        ✅ Posted apple to A1
        ❌ Failed: 400 - Invalid location format
        📊 Summary: 90 posted, 10 failed, 0 skipped
    """
    data_to_post, skipped_list = get_data(from_url)

    success_count = 0
    fail_count = 0   

    if data_to_post is None:
        print("[ERROR] no data to post")
        return 
            
    for location, name, quantity in data_to_post:
        response = requests.post(send_url, json={
            "location": location,
            "name": name,
            "quantity": quantity
        })

        if response.status_code == 201:
            print(f" Posted {name} to {location}")
            success_count +=1
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Unknown error")
            except:
                error_msg = response.text[:100]

            print(f" Failed: {response.status_code} - {error_msg}")
            fail_count +=1
    
    if skipped_list: 
        print(f"\n Total {len(skipped_list)} items skipped:")
        for item in skipped_list:
            print(f"  - {item}")
    
    print(f"\n Summary: {success_count} posted, {fail_count} failed, {len(skipped_list)} skipped")


if __name__ == "__main__":

    post_data_to_API("https://jsonplaceholder.typicode.com/posts", "http://127.0.0.1:5000/inventory")