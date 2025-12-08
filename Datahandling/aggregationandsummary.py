import json
import os
import statistics
from collections import Counter
from datetime import datetime
import apidatatojson

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

def compute_summary_metrics(json_path: str):
    """
    Analyze post data and generate user statistics summary.
    
    Processes JSON data containing user posts to calculate:
    - Total posts per user
    - Content length statistics
    - Most frequently used words per user
    
    Args:
        json_path: Path to JSON file with post data
        
    Returns:
        Dictionary with timestamp and sorted user summaries
        
    Note: Leverages existing `apidatatojson.write_to_json()` function
          for saving results, demonstrating code reuse.
    """
    data = open_json(json_path)

    new_dict= {}
    final_dict = {}

    if not data:
        print("No data to process")
    
    for item in data:
        if item["user"] not in new_dict:
            new_dict[item["user"]]=[]
        new_dict[item["user"]].append({
            "title" : item["title"],
            "content" : item["content"],
            "content_length": item["content_length"]
        })
    

    timestamp = datetime.now().isoformat()

    final_dict = {
    "timestamp": timestamp,
    "summary": []
    }

    for user, values in new_dict.items():
        total_items = len(values)
        content_lengths = [item["content_length"] for item in values]
        total_content_length = sum(content_lengths)
        avg_content_by_user = statistics.mean(content_lengths)
        content_strings = "".join([item["content"] for item in values]).replace(".", " ").split()
        counter_words = Counter(content_strings).most_common(1)
        final_dict["summary"].append({
            "user": user,
            "total_items": total_items,
            "total_content_length": total_content_length,
            "average_content_length": int(avg_content_by_user),
            "most_common_word": counter_words[0]
        })

    final_dict["summary"].sort(key=lambda x: x["average_content_length"], reverse=True)

    return final_dict

def print_summary(final_dict: dict):
    """
    Display analysis results in a clean, readable format.
    
    Args:
        final_dict: Dictionary containing summary data from compute_summary_metrics
        
    Prints formatted report with indented user statistics for better readability.
    """
    print("\n===== SUMMARY REPORT =====")
    print(f"report generated at {final_dict["timestamp"]}\n")
   
    for item in final_dict["summary"]:
        print(f"  User: {item["user"]} has total {item["total_items"]} items with total content length of {item["total_content_length"]}")
        print(f"  The average content length is {item["average_content_length"]} and the most common word in the content is - {item["most_common_word"][0]}, with {item["most_common_word"][1]} occurances.")


    print("===========================\n")


if __name__ == "__main__":
    """
    Main execution: Analyze post data and save results.
    
    Demonstrates workflow:
    1. Load and process JSON data
    2. Generate user statistics
    3. Display formatted report
    4. Save using existing utility function
    
    The reuse of `apidatatojson.write_to_json()` shows how previously
    built components can be integrated into new workflows.
    """
    json_path= "Newprojects/Datahandling/json_data/valid_posts.json"
    data = compute_summary_metrics(json_path)
    if data:
        print_summary(data)

    output_path = "Newprojects/Datahandling/json_data"
    apidatatojson.write_to_json(data, None, output_path=output_path)
