import json
import os

def open_json(json_path: str):
    """
    Safely open and load a JSON file.

    Parameters
    ----------
    json_path : str
        Path to the JSON file to load.

    Returns
    -------
    list | dict | None
        Parsed JSON data if successful.
        Returns None if the file does not exist, contains invalid JSON,
        or cannot be loaded.

    Notes
    -----
    - Handles missing files
    - Handles invalid JSON
    - Ensures graceful program exit instead of raising exceptions
    """
    if not os.path.exists(json_path):
        print(f"[ERROR]: Invalid path or file does not exist - {json_path}")
        return
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    except json.JSONDecodeError as e:
        print(f"[ERROR]: JSON decode error - {e}")
        return
    
    if not data:
        print("no data to process")
        return
    
    return data

def validate_transform_entries(data: list):
    """
    Validate and transform a list of JSON-like dictionary entries.

    Validation rules
    ----------------
    - All fields (user, title, content) must be non-None.
    - `title` and `content` are stripped of whitespace.
    - `title` is converted to uppercase.
    - Empty strings after stripping are skipped.
    - Title length must not exceed 100 characters.
    - `user` must be a non-negative integer.

    Transformations
    ---------------
    - Adds a `content_length` field to each valid entry.

    Parameters
    ----------
    data : list
        A list of dictionaries containing entry data to validate.

    Returns
    -------
    tuple[list, list]
        (validated_entries, skipped_entries)
        validated_entries : list of cleaned and accepted entries
        skipped_entries : list of rejected entries with a reason
    """
    validated_entry_list = []
    skipped_entry_list = []

    for item in data:
        user = item.get("user", None)
        title = item.get("title", None)
        content = item.get("content", None)

        if user is not None and title is not None and content is not None:
            title = title.strip().upper()
            content = content.strip()

            if title == "" or content == "":
                skipped_entry_list.append({
                    "user": user,
                    "title": title,
                    "content": content,
                    "reason for skipping": "Field with just whitespaces"  
                }) 
            
            else:
                if len(title)>100:
                    skipped_entry_list.append({
                    "user": user,
                    "title": title,
                    "content": content,
                    "reason for skipping": "Title length too long"  
                }) 
                
                elif not isinstance(user, int): 
                    skipped_entry_list.append({
                    "user": user,
                    "title": title,
                    "content": content,
                    "reason for skipping": "user field is not an integer"  
                }) 
                
                elif user < 0:
                    skipped_entry_list.append({
                    "user": user,
                    "title": title,
                    "content": content,
                    "reason for skipping": "user field is negative"  
                })
                else:
                    validated_entry_list.append({
                        "user": user,
                        "title": title,
                        "content": content,
                        "content_length": len(content)
                    }) 
        else:
            skipped_entry_list.append({
                "user": user,
                "title": title,
                "content": content,
                "reason for skipping": "Fields had None value"
            })

    return validated_entry_list, skipped_entry_list

def save_valid_data(valid: list, output_path):
    if not valid:
        print("No data to write")
        return

    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        print(f"[ERROR] Could not create directory {output_path}: {e}")
        return

    file_name="valid_posts.json"
    final_output = os.path.join(output_path, file_name)
    
    try:
        with open(final_output, "w", encoding="utf-8") as json_file:
            json.dump(valid, json_file, indent=4, ensure_ascii=False)

        print(f"Sucessfully wrote to {final_output}")

    except (IOError, PermissionError) as e:
        print(f"File error: {e}")
        return
    except TypeError as e:
        print(f"JSON serialization error: {e}")
        return



def print_summary(valid: list, skipped: list):
    """
    Print a summary report of validated and skipped entries.

    Parameters
    ----------
    valid : list
        List of successfully validated entries.
    skipped : list
        List of skipped entries containing a 'reason for skipping' field.

    Output
    ------
    Prints:
        - Total entries
        - Count of valid vs skipped
        - Breakdown of skip reasons and their frequency
    """
    print("\n===== SUMMARY REPORT =====")
    print(f"Total entries: {len(valid) + len(skipped)}")
    print(f"Valid entries: {len(valid)}")
    print(f"Skipped entries: {len(skipped)}")

    reason_counts = {}
    for entry in skipped:
        reason = entry.get("reason for skipping", "Unknown reason")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    if reason_counts:
        print("\nBreakdown of skipped reasons:")
        for reason, count in reason_counts.items():
            print(f" - {reason}: {count}")
    print("===========================\n")

if __name__=="__main__":

    data_to_validate= open_json("Newprojects/Datahandling/json_data/bad_posts.json")
    if data_to_validate:
        valid, skipped = validate_transform_entries(data_to_validate)
        print_summary(valid, skipped)
        save_valid_data(valid, "Newprojects/Datahandling/json_data/")