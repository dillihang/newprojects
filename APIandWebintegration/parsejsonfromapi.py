import requests

def get_age():
    name  = input("Please enter your name: ").strip()
    if not name:
        print("cannot be empty")
        return

    data_value = guess_age(name)

    if data_value is None:
        print(f"Failed to retrieve data.")
        return

    count = data_value.get("count", 0)
    gender = data_value.get("gender", "unknown")
    probability = data_value.get("probability", 0.0)
    
    print(f"{name} is {gender}, with the probability of {probability *100:.1f}%, based on {count} people in database")

def guess_age(name: str):
    the_url = f"https://api.genderize.io/?name={name}"

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
    