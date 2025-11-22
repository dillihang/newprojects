import json
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def print_save_data():
    """
    Main function to fetch and display top news headlines for a given country.
    
    Handles the complete workflow:
    - Loads API key from environment variables
    - Prompts user for country code
    - Fetches news data from NewsAPI
    - Displays top 5 headlines or error messages
    
    Exits gracefully on any errors during the process.
    """
    news_dict = {}

    try:
        api_key = os.getenv("API_KEY")
    except OSError as e:
        print("[ERROR]", e)
        return
    
    if not api_key:
        print("Could not succeed in getting the API KEY, please check environment file")
        return

    country_abbr = input("Please enter the country e.g us for USA, gb for United Kingdom: ").strip().lower()
    
    if not country_abbr:
        print(f"Country cannot be empty")
        return
    
    data_value = get_data(country_abbr, api_key)

    if not data_value:
        print("Failed to retrieve data from the API.")
        return

    status = data_value.get("status", "unknown")
    total_results = data_value.get("totalResults", 0)
    articles = data_value.get("articles", [])
    time_stamp = f"Top 5 headlines recorded on {datetime.today().strftime("%d-%m-%Y, %H:%M:%S")}"

    if status == "ok":
        
        print(f"Top 5 headlines from {country_abbr}\n")
        news_dict["timestamp"]=time_stamp
        news_dict["country"]=country_abbr
        news_dict["articles"]=[]
        for items in articles[:5]:
            title = items.get("title", "Unknown")
            description = items.get("description", "Empty")
            source_name = items.get("source", {}).get("name", "Unknown")
            published_at = items.get("publishedAt", "Unknown")
            author = items.get("author", "Unknown")
            print(f"{title} - author {author}\n {description}\n published at {published_at}\n")
            news_dict["articles"].append({
                "title" : title,
                "author": author,
                "source": source_name,
                "description": description,
                "published_at": published_at
            })
        save_json(news_dict, "News_Json.json") 
        print("json file saved")   
    else:
        error_code = data_value.get("code", "Unknown")
        error_message = data_value.get("message", "Unknown error")
        print(f"NewsAPI error: {error_code} - {error_message}")
    
    

def save_json(news_dict: dict, file_name: str):

    path = os.getenv("PATH_JSON_FILES")
    
    if not path:
        print(f"[ERROR] path does not exist. Please check .env.")
        return
    
    os.makedirs(path, exist_ok=True)

    final_path = os.path.join(path, file_name)

    if not os.path.isfile(final_path):
        data = [news_dict]
    else:
        try:
            with open(final_path, "r") as json_f:
                data = json.load(json_f)
        except json.JSONDecodeError:
            print("[WARN] JSON file corrupted. Starting a new one.")
            data = []
        data.append(news_dict)
    
    with open(final_path, "w") as json_f:
        json.dump(data, json_f, indent=4)


def get_data(country:str, api_key: str):
    """
    Fetches top news headlines from NewsAPI for a specific country.
    
    Args:
        country (str): ISO country code (e.g., 'us', 'gb', 'in')
        api_key (str): NewsAPI authentication key
        
    Returns:
        dict or None: Parsed JSON response from API, or None if request fails
        
    Handles various network and API errors:
    - Timeouts after 5 seconds
    - Connection failures
    - HTTP errors (4xx, 5xx status codes)
    - Invalid JSON responses
    """
    the_url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={api_key}"

    
    try:
        response = requests.get(the_url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection failed")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    except ValueError:
        print("Response is not valid JSON")
        return None

    return data



if __name__=="__main__":

    print_save_data()
    