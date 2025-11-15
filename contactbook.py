"""
Contact Book Application (JSON-Enabled)

This module implements a contact management system that supports storing
names, phone numbers, and addresses. Contacts are represented using the
Person class, while the ContactBook class manages all Person instances
and provides lookup, add, save, and load operations.

Key Features:
- Store multiple phone numbers per person
- Store one address per person
- Add or update contact information dynamically
- Search by name or search by phone number
- Save all data to a JSON file
- Load existing contact data from a JSON file
- Prevent overwriting loaded data unless confirmed
- Robust error handling for file operations

Classes:
    Person:
        Represents a single contact with a name, number list,
        and optional address.

    ContactBook:
        Stores Person objects and provides:
        - add_number()
        - add_address()
        - search_by_name()
        - search_by_number()
        - save_to_file()
        - load_from_file()
        Includes optional improvements such as number-uniqueness,
        merging contacts, and simplified internal logic.

    ContactBookApplication:
        Command-line interface for user interaction:
        add number, add address, search, save, load, exit.

This module is designed for simple contact management and can be extended
in the future with validation, duplicate detection, reverse lookup tables,
or more detailed address structures.
"""
import json
import os

class Person:
    def __init__(self, name: str):
        self.__name = name
        self.__numbers_list = []
        self.__address = None

    @property
    def name(self):
        return self.__name
    
    @property
    def numbers(self):
        return self.__numbers_list
    
    @property
    def address(self):
        return self.__address
    
    def set_address(self, address_input: str):
        self.__address = address_input
    
    def add_number(self, number):
        if number not in self.__numbers_list:
            self.__numbers_list.append(number)

    def __str__(self):

        return f"{self.__name} {self.__address}"

class ContactBook:
    def __init__(self):
        self.__phone_dict = {}
        self.__loaded_file = None
    
    @property
    def loaded_file(self):
        return self.__loaded_file

    def add_number(self, name: str, number: str = None):
        if name not in self.__phone_dict:
            self.__phone_dict[name] = Person(name)

        if number is not None:
            self.__phone_dict[name].add_number(number)
        

    def add_address(self, name: str, address: str = None):
        if name in self.__phone_dict:
            if self.__phone_dict[name].address is None: 
                self.__phone_dict[name].set_address(address)
            else:
                self.__phone_dict[name].set_address(address)
    
    def search_by_name(self, name: str):
        if name in self.__phone_dict:
            return self.__phone_dict[name]
    
    def search_by_number(self, number: str):
        for name, person_object in self.__phone_dict.items():
            if number in person_object.numbers:
                return person_object
        
    def load_from_file(self, filename: str):

        if self.__loaded_file is None:
            try:
                with open(filename, "r") as file:
                    data = json.load(file)

                    for name, contact_info in data.items():
                        if name not in self.__phone_dict:
                            self.add_number(name)
                        for numberoraddress, listorstring in contact_info.items():
                            if numberoraddress == "numbers":
                                if isinstance(listorstring, list):
                                    for numbers in listorstring:
                                        self.add_number(name, numbers)
                            elif numberoraddress == "address" and listorstring is not None:
                                self.add_address(name, listorstring)

                self.__loaded_file = filename

            except FileNotFoundError:
                print(f"Error: File '{filename}' not found")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in '{filename}': {e}")
            except PermissionError:
                print(f"Error: No permission to read '{filename}'")
            except IsADirectoryError:
                print(f"Error: '{filename}' is a directory")
            except Exception as e:
                print(f"Unexpected error: {e}")
        

    def save_to_file(self, filename: str):
        if os.path.isfile(filename):
            answer = input("The file already exists, to Overwrite type Y, or else type N to return and provide new directory/filename: ").strip()
            if answer.upper() == "Y":
                log_entry = {}
                for name, person_object in self.__phone_dict.items():
                    log_entry[name] = {
                                        "numbers": person_object.numbers,
                                        "address": person_object.address
                                        } 
                with open(filename, "w") as json_file:
                    json.dump(log_entry, json_file, indent=4)

            elif answer.upper() == "N":
                return
        
        else:
            log_entry = {}
            for name, person_object in self.__phone_dict.items():
                log_entry[name]= {
                                "numbers": person_object.numbers,
                                "address": person_object.address
                                } 
                
            with open(filename, "w") as json_file:
                json.dump(log_entry, json_file, indent=4)
 
class ContactBookApplication():
    def __init__(self):
        self.__app = ContactBook()

    def options(self):
        print("0    exit")
        print("1    add number")
        print("2    add address")
        print("3    search by name")
        print("4    search by number")
        print("5    save")
        print("6    load")

    def load_file(self):
        if self.__app.loaded_file == None: 
            file_path = input("Enter file path: ")
            self.__app.load_from_file(file_path)
            print("Json file loaded succesfully")
        else:
            print("file already loaded. please save and exit and load new file")
            return

    def add_number(self):
        name = input("Name: ").strip()
        if not name:
            print("Error: Name cannot be empty!")
            return
        number = input("Number: ").strip()
        if number:
            self.__app.add_number(name, number)
            print("Succesfully added")
        else:
            self.__app.add_number(name)
            print("Succesfully added")
        
    
    def add_address(self):
        name = input("Name: ").strip()
        if not name:
            print("Error: Name cannot be empty!")
            return
        checking_name = self.__app.search_by_name(name)
        if checking_name:
            address = input("Address: ").strip()
            if not address:
                print("Be advised you did not add anything to address")
            self.__app.add_address(name, address)
            print("Address saved")
        else:
            print("Person does not exist!")
    
    def search_by_name(self):
        name = input("Name: ")
        person_object = self.__app.search_by_name(name)
        if person_object:
            print(person_object.name)
            if person_object.numbers:
                for numbers in person_object.numbers:
                    print(numbers)
            else:
                print("Number Unknown")
            if person_object.address == None:
                print("Address Unknown")
            else:
                print(person_object.address)
        else:
            print("person does not exist")

    def search_by_number(self):
        number = input("Number: ").strip()
        if not number:
            print("Error: Number cannot be empty!")
            return
        person_object = self.__app.search_by_number(number)
        
        if person_object:
            print(person_object.name)
            if person_object.numbers:
                for numbers in person_object.numbers:
                    print(numbers)
            else:
                print("Number Unknown")
            if person_object.address:
                print(person_object.address)
            else:
                print("Unknown Address")
        else:
            print(f"No contact details found for {number}")
    
    def save_file(self):
        file_path = input("Please enter file path: ").strip()
        if not file_path:
            print("File path cannot be empty!")
            return
        
        self.__app.save_to_file(file_path)

    def execute(self):
        
        self.options()
        while True:
            try:
                option_input = int(input("Please pick an option from the list: "))
                if option_input == 0:
                    break
                elif option_input == 1:
                    self.add_number()
                elif option_input == 2:
                    self.add_address()
                elif option_input == 3:
                    self.search_by_name()
                elif option_input == 4:
                    self.search_by_number()
                elif option_input == 5:
                    self.save_file()
                elif option_input == 6:
                    self.load_file()
                else:
                    self.options()
            except ValueError:
                self.options()

if __name__ == "__main__":

    t = ContactBookApplication()
    t.execute()
    

"""
    ===============================
CONTACT BOOK – IMPROVEMENTS LIST
===============================

1. SIMPLIFY add_number() LOGIC
------------------------------
Current version contains multiple nested if/else branches.
Cleaner unified version:

    def add_number(self, name, number=None):
        if name not in self.__phone_dict:
            self.__phone_dict[name] = Person(name)
        if number is not None:
            self.__phone_dict[name].add_number(number)

This eliminates duplication and handles all cases:
- new contact + number
- existing contact + number
- new contact without number
- existing contact without number


2. SIMPLIFY add_address()
-------------------------
Your current implementation repeats logic.

Improved version:

    def add_address(self, name, address):
        if name not in self.__phone_dict:
            self.__phone_dict[name] = Person(name)
        self.__phone_dict[name].set_address(address)

Removes unnecessary branching.


3. HELPERS FOR JSON LOADING
----------------------------
Add a dedicated helper for creating/updating contacts:

    def _create_or_update_contact(self, name, data):
        if name not in self.__phone_dict:
            self.__phone_dict[name] = Person(name)
        person = self.__phone_dict[name]
        for num in data.get("numbers", []):
            person.add_number(num)
        if data.get("address"):
            person.set_address(data["address"])

Then replace loader loop with:

    for name, info in data.items():
        self._create_or_update_contact(name, info)


4. PREVENT DUPLICATE NUMBERS
-----------------------------
Inside Person.add_number():

    def add_number(self, number):
        if number not in self.__numbers_list:
            self.__numbers_list.append(number)

Guarantees uniqueness and safer data.


5. REVERSE LOOKUP TABLE FOR FAST NUMBER SEARCH
-----------------------------------------------
Optional but improves performance:

Inside ContactBook.__init__():

    self.__number_to_name = {}

Whenever adding a number:

    self.__number_to_name[number] = name

Searching becomes:

    name = self.__number_to_name.get(number)
    return self.__phone_dict.get(name)

No more looping through entire dict.


6. BETTER PRINT/OUTPUT FORMATTING
----------------------------------
Instead of stacking raw prints, produce:

    Name: John
    Numbers: 123, 456
    Address: London

Makes output cleaner and user-friendly.


7. OPTIONAL JSON CORRUPTION SAFETY
-----------------------------------
Inside load_from_file():

    numbers = info.get("numbers", [])
    if not isinstance(numbers, list):
        print(f"Warning: malformed number list for {name}")
        numbers = []

Adds safety for bad JSON.


8. MERGE CONTACTS FEATURE (OPTIONAL)
-------------------------------------
A method to combine two contact entries:

    def merge_contact(self, source, target):
        if source in self.__phone_dict and target in self.__phone_dict:
            src = self.__phone_dict[source]
            trg = self.__phone_dict[target]
            
            for num in src.numbers:
                trg.add_number(num)

            if src.address and not trg.address:
                trg.set_address(src.address)

            del self.__phone_dict[source]

Useful when loading mixed casing, duplicates, or user mistakes.


9. VALIDATION (OPTIONAL)
-------------------------
Add optional checks:
- require phone numbers to be digits
- require min length
- prevent empty names

These can be placed in ContactBookApplication before adding.


10. UI QUALITY IMPROVEMENTS
----------------------------
Format search results consistently
Show clear success/error messages
Avoid repeating text in multiple branches


==========================
END OF IMPROVEMENT NOTES
==========================

"""