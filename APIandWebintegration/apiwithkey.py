import requests
import os
from dotenv import load_dotenv

load_dotenv()

def print_data():
    """
    Main function to fetch and display top news headlines for a given country.
    
    Handles the complete workflow:
    - Loads API key from environment variables
    - Prompts user for country code
    - Fetches news data from NewsAPI
    - Displays top 5 headlines or error messages
    
    Exits gracefully on any errors during the process.
    """
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

    if status == "ok":
        print(f"Top 5 headlines from {country_abbr}\n")
        for items in articles[:5]:
            title = items.get("title", "Unknown")
            description = items.get("description", "Empty")
            source = items.get("source", {}).get("name", "Unknown")
            author = items.get("author", "Unknown")
            print(f"{title} - author {author}\n {description}\n")
    else:
        error_code = data_value.get("code", "Unknown")
        error_message = data_value.get("message", "Unknown error")
        print(f"NewsAPI error: {error_code} - {error_message}")


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

    print_data()
    