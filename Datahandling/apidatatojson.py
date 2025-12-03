import json
from datetime import datetime
import requests
import os

def get_api(url: str):
    """
    Fetch JSON data from a REST API endpoint.
    
    Args:
        url (str): The complete URL to fetch data from
        
    Returns:
        dict/list: Parsed JSON data if successful, None otherwise
        
    Raises:
        Prints error messages for: Timeout, ConnectionError, HTTPError, 
        JSON parsing errors, and other exceptions
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            print(f"[WARNING] Could not parse JSON: {e}")
            return None

        return data

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection failed")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return None

def process_data(url: str):
    """
    Extract, validate, and transform data from an API endpoint.
    
    Fetches data from the given URL, validates required fields (userId, title, body),
    and separates valid data from invalid/skipped items.
    
    Args:
        url (str): API endpoint URL to fetch data from
        
    Returns:
        tuple: (parsed_data, skipped_data) where:
            parsed_data (list): List of dictionaries with valid items
            skipped_data (list): List of dictionaries with invalid items and reasons
            
    Example:
        >>> parsed, skipped = process_data("https://api.example.com/posts")
        >>> len(parsed)  # Number of valid items
        95
        >>> len(skipped) # Number of invalid items  
        5
    """
    parsed_data = []
    skipped_data = []
    data_to_process = get_api(url)
    
    if data_to_process is None:
        print("[ERROR]: No data to process")
        return

    for items in data_to_process:
        user = items.get("userId", None)
        title = items.get("title", None)
        content = items.get("body", None)

        if not all([user, title, content]):
            skipped_data.append({
                "user": user,
                "title": title,
                "content": content,
                "reason": "Missing fields"
            })
        
        else:
            parsed_data.append({
                "user": user,
                "title": title,
                "content": content
            })


    return parsed_data, skipped_data

def write_to_json(parsed_data: list, skipped_data: list, output_path: str):
    """
    Save processed data to a timestamped JSON file.
    
    Creates a JSON file with timestamp metadata, parsed data, and skipped items.
    File is saved with format: posts_DD_MM_YYYY_HH_MM_SS.json
    
    Args:
        parsed_data (list): Valid data items to save
        skipped_data (list): Skipped/invalid items with reasons
        output_path (str): Directory path where JSON file will be saved
        
    Returns:
        None: Prints success/error messages to console
        
    Raises:
        OSError: If directory creation fails
        IOError: If file writing fails  
        PermissionError: If file permissions insufficient
        TypeError: If data cannot be serialized to JSON
        
    Example:
        >>> write_to_json(parsed, skipped, "output/data")
        ✅ Successfully wrote to output/data/posts_03_12_2025_14_30_45.json
        📊 95 items written, 5 items skipped
    """
    if not parsed_data:
        print("No data to write")
        return
    
    dict_timestamp = datetime.now().isoformat()

    new_dict = {
        "timestamp": dict_timestamp,
        "data": parsed_data,
        "skipped_data": skipped_data if skipped_data else None
    }

    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        print(f"[ERROR] Could not create directory {output_path}: {e}")
        return

    timestamp = datetime.today().strftime("%d_%m_%Y_%H_%M_%S")
    file_name=f"posts{timestamp}.json"
    final_output = os.path.join(output_path, file_name)
    
    try:
        with open(final_output, "w", encoding="utf-8") as json_file:
            json.dump(new_dict, json_file, indent=4, ensure_ascii=False)

        print(f"Sucessfully wrote to {final_output}")
        print(f"{len(parsed_data)} data written and {len(skipped_data)} data skipped")

    except (IOError, PermissionError) as e:
        print(f"File error: {e}")
        return
    except TypeError as e:
        print(f"JSON serialization error: {e}")
        return


if __name__=="__main__":

    parsed_data, skipped_data = process_data("https://jsonplaceholder.typicode.com/posts")
    write_to_json(parsed_data, skipped_data, output_path="Newprojects/Datahandling/json_data")