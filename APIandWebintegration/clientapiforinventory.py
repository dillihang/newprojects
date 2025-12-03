import requests

base_url = "http://127.0.0.1:5000/inventory"

def access_flaskapi():
    try:
        response = requests.get(base_url, timeout=5)
        response.raise_for_status()

        data = response.json()
        
        return data
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

def get_data():

    new_data = access_flaskapi()
    
    if not new_data:
        print("No data")
        return

    print(new_data)
    
def post_data(location: str, name: str, quantity: int):
    response = requests.post(base_url, json={
        "location": location,
        "name": name,
        "quantity": quantity
    })
    return response.json()

def delete_item(item_id: str):

    response = requests.delete(f"{base_url}/{item_id}")

def update_item(item_id: str):

    response = requests.patch(f"{base_url}/{item_id}", json={"quantity": 30})

def search_by_location(location):

    response = requests.get(f"{base_url}/search", params={"location": location})



if __name__=="__main__":

    print("🚀 Testing Complete Inventory API Workflow\n")
    
    # 1. CREATE multiple items and capture IDs
    print("1. Creating inventory items...")
    inventory_data = [
        ("A1", "apple", 10),
        ("A1", "banana", 5),
        ("B2", "orange", 8),
        ("B2", "mango", 12),
        ("C3", "grapes", 15),
        ("C3", "watermelon", 1),
        ("D4", "pineapple", 3),
        ("D4", "kiwi", 20),
        ("E5", "strawberry", 25),
        ("E5", "blueberry", 30)
    ]
    
    created_items = {}  # Store name -> id mapping
    
    for location, name, quantity in inventory_data:
        try:
            response = post_data(location, name, quantity)
            item_id = response["item_id"]
            created_items[name] = item_id
            print(f"   Created {name} at {location} (ID: {item_id})")
        except Exception as e:
            print(f"   ❌ Failed to create {name}: {e}")
            print(f"   Response: {response.json() if 'response' in locals() else 'No response'}")
    
    # 2. GET all items
    print("\n2. Current inventory:")
    get_data()
    
    # 3. UPDATE various items (only if they exist)
    print("\n3. Updating items...")
    for fruit in ["apple", "orange", "grapes"]:
        if fruit in created_items:
            update_item(created_items[fruit])
            print(f"   Updated {fruit}")
        else:
            print(f"   ❌ {fruit} not found to update")
    
    # 4. DELETE some items
    print("\n4. Deleting items...")
    for fruit in ["banana", "watermelon", "kiwi"]:
        if fruit in created_items:
            delete_item(created_items[fruit])
            print(f"   Deleted {fruit}")
        else:
            print(f"   ❌ {fruit} not found to delete")
    
    # 5. SEARCH by different locations
    print("\n5. Searching by location...")
    for location in ["A1", "B2", "C3", "D4", "E5"]:
        print(f"\n   Items in {location}:")
        search_by_location(location)
    
    # 6. Final state
    print("\n6. Final inventory state:")
    get_data()
    
    print("\n✅ All tests completed!")
   
  