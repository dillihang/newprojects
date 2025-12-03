import requests
import random
import string

def api_get(url: str, timeout: int = 5):
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
    location_letters = string.ascii_uppercase
    location_id = user_id
    return f"{random.choice(location_letters)}{location_id}"

def get_data(url: str):

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