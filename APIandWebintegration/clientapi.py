import requests

url = "http://127.0.0.1:5000/items"

def access_flaskapi():
    try:
        response = requests.get(url, timeout=5)
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
    
def post_data():
    response = requests.post(url, json={"id":5,"name":"tangerine"})

def delete_item():

    response = requests.delete(url, json={"id":5})

if __name__=="__main__":
    
    post_data()
    get_data()
    # delete_item()
    # get_data()