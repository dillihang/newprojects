"""
To-Do List Manager
------------------

A command-line based task management application that allows users to add, view, complete, 
and remove tasks. Tasks are stored persistently in a JSON file, enabling data to be saved 
and loaded across sessions.

Features:
- Add new tasks with a title, description, and optional due date.
- View all tasks, sorted by due date, status, and title.
- Mark tasks as completed (records the completion date).
- Remove tasks by their ID.
- Persistent storage in JSON format.

Classes:
--------
Task:
    Represents a single task in the To-Do list.
    
    Attributes:
        - title (str): Task title.
        - description (str): Task description.
        - due_date (date): Task due date (default 7 days from creation).
        - completed_date (date | None): Date when task was completed.
        - date_created (date): Date the task was created.
        - id (int): Unique task identifier.
        - status (bool): Completion status (True if completed).

    Methods:
        - mark_completed(): Marks the task as completed and records the completion date.
        - __str__(): Returns a formatted string representation of the task.

ToDoList:
    Manages a collection of Task objects and handles persistence.

    Attributes:
        - __todo_dict (dict): Dictionary mapping task titles to Task objects.

    Methods:
        - add_task_objects(title, description, due_date): Adds a new Task object.
        - list_tasks(): Returns all Task objects.
        - mark_complete(task_id): Marks a task as complete by ID.
        - remove_task_object(task_id): Removes a task by ID.
        - saving_file(): Saves all tasks to a JSON file.
        - load_Json_file(): Loads tasks from the JSON file; creates file if missing.

ToDoApp:
    Handles user interaction via the command line.

    Methods:
        - add_tasks(): Prompts user to add a new task.
        - view_tasks_by_filter(): Displays tasks sorted by due date, status, and title.
        - mark_task_completed(): Marks a task as completed via user input.
        - remove_task(): Removes a task via user input.
        - options(): Prints menu options.
        - execute(): Main loop for running the app.
"""

from datetime import datetime, timedelta, date
import json
import os

class Task:
    id_counter = 1
    def __init__(self, title: str, description: str, due_date: date = None, completed_date: date = None, date_created: date = None, task_id: int = None, status: bool = False):
        self.__title = title
        self.__description = description
        if due_date == None:
            due_date = datetime.now().date() + timedelta(days=7)
        self.__due_date = due_date
        self.__status = status
        self.__id = task_id if task_id is not None else Task.id_counter
        if task_id==None:
            Task.id_counter += 1
        if date_created== None:
            self.__date_created = datetime.now().date()
        else:
            self.__date_created = date_created
        self.__completed_date = completed_date
    
    @property
    def title(self):
        return self.__title
    
    @property
    def description(self):
        return self.__description
    
    @property
    def due_date(self):
        return self.__due_date
    
    @property
    def status(self):
        return self.__status
    
    @property
    def id(self):
        return self.__id
    
    @property
    def date_created(self):
        return self.__date_created
    
    @property
    def completed_date(self):
        return self.__completed_date
    
    def mark_completed(self):
        self.__status = True
        self.__completed_date = datetime.now().date()
    
    def __str__(self):
        created_str = self.date_created.strftime("%d/%m/%Y")
        due_str = self.__due_date.strftime("%d/%m/%Y")
        
        if not self.__status:
            return f"{self.id}. Created on {created_str} Task: {self.__title}, Description: {self.__description} - Due: {due_str}, Status: In progress"
        else:
            completed_str = self.__completed_date.strftime("%d/%m/%Y") if self.__completed_date else "N/A"
            return f"{self.id}. Created on {created_str} Task: {self.__title}, Description: {self.__description} - Due: {due_str}, Status: Completed({completed_str})"
        
class ToDoList:
    def __init__(self):
        self.__todo_dict = {}

    def add_task_objects(self, title: str, description: str, due_date: str):
        if title not in self.__todo_dict:
            self.__todo_dict[title] = Task(title, description, due_date)
            print(f"✅ Task '{title}' added successfully!")
        else:
            print(f"❌ Task '{title}' already exists!")

    def list_tasks(self):
        return self.__todo_dict
    
    def mark_complete(self, task_id: int):
        task_object = [task for task in self.__todo_dict.values() if task.id == task_id]
        if task_object:
            task = task_object[0]
            if task.status == True:
                print(f"{task_id} is already marked as complete")
            else:
                task.mark_completed()
                print(f"{task_id} marked as completed")
        else:
            print(f"{task_id} does not exist")

    def remove_task_object(self, task_id: int):
        task_name = [task.title for task in self.__todo_dict.values() if task.id == task_id]
        if task_name:
            task_name = task_name[0]
            if task_name in self.__todo_dict:
                del self.__todo_dict[task_name]
                print(f"{task_id} removed")
        
        else:
            print(f"{task_id} does not exist")

    def saving_file(self):
        data_to_save = {}

        for key, task_objects in self.__todo_dict.items():
            data_to_save[key] = {
                "ID": task_objects.id,
                "Created_date": task_objects.date_created.isoformat(),
                "Title": task_objects.title,
                "Description": task_objects.description,
                "Due_date": task_objects.due_date.isoformat(),
                "Completed_date": task_objects.completed_date.isoformat() if task_objects.completed_date else None,
                "Status": task_objects.status          
            }
        
        with open("Newprojects/Todo.json", "w") as json_file:
            json.dump(data_to_save, json_file, indent=4)

    def load_Json_file(self):
        file_path = "Newprojects/Todo.json"

        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({}, f, indent=4)

        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            
            if data:
                max_id = max(value["ID"] for value in data.values())
                Task.id_counter = max_id + 1

            for key, value in data.items():
                self.__todo_dict[key] = Task(
                                            title=value["Title"], 
                                            description=value["Description"],
                                            due_date=date.fromisoformat(value["Due_date"]),
                                            completed_date = date.fromisoformat(value["Completed_date"]) if "Completed_date" in value else None,
                                            date_created=date.fromisoformat(value["Created_date"]),
                                            task_id=value["ID"],
                                            status=value["Status"]
                                        )
            

class ToDoApp():
    def __init__(self):
        self.__todoapp = ToDoList()
        self.__todoapp.load_Json_file()

    def add_tasks(self):
        title = input("Title: ")
        description = input("Description: ")
        
        try:
            date_input = input("Enter date: ")  
            if date_input == "":  
                due_date = None
            else:
                due_date = datetime.strptime(date_input.strip(), "%d/%m/%Y").date()
                if due_date < datetime.now().date():
                    print("Cannot enter past dates")
                    return              
        except ValueError:
            print("Invalid date format! Please use DD/MM/YYYY")
            return  

        self.__todoapp.add_task_objects(title, description, due_date)
        self.__todoapp.saving_file()

    def view_tasks_by_filter(self):

        tasks = [task for task in self.__todoapp.list_tasks().values()]

        if len(tasks)>0:
            for task_objects in sorted(self.__todoapp.list_tasks().values(), key=lambda x:(x.due_date, x.status, x.title)):
                    print(task_objects)
        else:
            print("No tasks")
            
    def mark_task_completed(self):
        try:
            task_id = int(input("Enter the task id: "))
        except ValueError:
            print("Please enter ID number")
            return
        self.__todoapp.mark_complete(task_id)
        self.__todoapp.saving_file()
                
    def remove_task(self):
        try:
            task_id = int(input("Enter the ID of the task you want removed: "))
        except ValueError:
            print("Please enter ID number")
        self.__todoapp.remove_task_object(task_id)
        self.__todoapp.saving_file()

    def options(self):
        print("1. Add Task")
        print("2. View Tasks")
        print("3. Complete Task")
        print("4. Remove Task")
        print("5. Exit")

    def execute(self):
        print("Welcome to To-Do List Manager")
        self.options()
        while True:
            try:
                option = int(input("Choose an option: "))
                
                if option == 1:
                    self.add_tasks()
                elif option == 2:
                    self.view_tasks_by_filter()
                elif option == 3:
                    self.mark_task_completed()
                elif option == 4:
                    self.remove_task()
                elif option == 5:
                    break
                    
            except (ValueError):
                self.options()

if __name__ == "__main__":

    app = ToDoApp()
    app.execute()