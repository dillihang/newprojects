"""
Expense Tracker

This program allows the user to track personal expenses over time. It supports
adding new expenses, viewing all recorded expenses, displaying a summary of total
spending, and saving data to a CSV file for persistence. Existing data is loaded
from the CSV file on startup, so previous entries are preserved and included in
views and summaries.

Features:
- Add expenses with name, category, and amount
- View all expenses sorted by amount (descending) and name
- Display total spending
- Save new entries to a CSV file
- Load existing data on startup to maintain continuity

Data Structures:
- new_list: Stores newly added expenses in the current session
- temp_list: Combined list of old and new expenses for display and summary
- old_list: Stores previously saved expenses loaded from the CSV file

Functions:
- read_file(): Loads existing expenses from the CSV file into old_list and temp_list
- save_file(): Appends new expenses to the CSV file
- options(): Displays the available actions to the user
- add_item(): Adds a new expense to the lists after validating input
- view_expense(): Displays all expenses in a readable format
- summary(): Shows all expenses and the total amount spent

Usage:
Run the program and choose options from the menu to manage expenses. Data is
persisted in 'expense_tracker.csv'.
"""
new_list = []
temp_list = []
old_list = []

def read_file():
    with open("Newprojects/expense_tracker.csv") as file:
        for line in file:
            line = line.strip()
            if line:
                line = line.replace(",", "")
                part = line.split()
                old_list.append({"Name": part[0], "Category": part[1], "Amount": float(part[2])})

    if len(old_list)>0:
        temp_list.extend(old_list)

def save_file():
    with open("Newprojects/expense_tracker.csv", "a") as file:
        for items in sorted(new_list, key =lambda x:(-x["Amount"],x["Name"])):
            file.write(f"{items["Name"]}, {items["Category"]}, {items["Amount"]}\n") 

def options():
    print("1. Add expense")
    print("2. View expense")
    print("3. Summary")
    print("4. Save & Exit")

def add_item():
    name = input("Name: ")
    if not name:
        print("Name cannot be empty!")
        return
    
    category = input("Category: ")
    if not category:
        print("category cannot be empty!")
        return
    
    try:
        amount = float(input("Amount: "))
        if amount <=0:
            print("Amount must be positive!")
            return
        
        new_list.append({"Name": name, "Category": category, "Amount": amount})
        temp_list.append({"Name": name, "Category": category, "Amount": amount})
        print(f"Item added")
    except (ValueError):
        print("please type in a float number or an int for amount")

def view_expense():
    print(f"Name        Category        Amount" )
    for item in sorted(temp_list, key=lambda x: (-x["Amount"],x["Name"])):
        print(f"{item["Name"]:11} {item["Category"]:15} £{item["Amount"]}")
        
def summary():
    total = sum([item["Amount"] for item in temp_list])
    view_expense()
    print(f"Total spent £{total}")

options()
read_file()
while True:
    try:
        user_input = int(input("Please type in the option: "))

        if user_input == 1:
            add_item()
        elif user_input == 2:
            view_expense()
        elif user_input == 3:
            summary()
        elif user_input == 4:
            save_file()
            break
    except (ValueError):
        options()

    


