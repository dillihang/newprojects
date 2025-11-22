import requests

def get_age():
    name  = input("Please enter your name: ").strip()
    data_value = guess_age(name)

    if data_value and data_value["age"] is not None:
        print(f"Name: {name}")
        print(f"Predicted Age: {data_value["age"]}")
        print(f"Sample size: {data_value["count"]}")
    
    else:
        print("Could not predict your age")

def guess_age(name: str):
    the_url = f"https://api.agify.io/?name={name}"

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

    get_age()
    