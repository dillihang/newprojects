import csv
from datetime import datetime
import os
import operator

def read_csv(file_path: str):
    """
    Read and parse a CSV file containing student data.

    The CSV file must contain the following columns:
        - name
        - score
        - grade_level   (formatted as: "<grade> <number>", e.g., "Year 10")

    This function:
        - Validates file existence.
        - Reads rows using csv.DictReader.
        - Cleans and converts:
            * name → stripped string
            * score → int
            * grade_level → ("Year", 10) tuple
        - Skips invalid rows and prints an error message.

    Parameters
    ----------
    file_path : str
        Path to the CSV file.

    Returns
    -------
    list[dict]
        A list of student dictionaries with keys:
            - "name": str
            - "score": int
            - "grade_level": tuple(str, int)
    """
    students = []

    if not os.path.exists(file_path):
        print("File does not exist!")
        return students

    with open(file_path, "r") as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            try:
                name_row = row["name"].strip()
                score_row=int(row["score"])
                grade_parts = row["grade_level"].split()
                grade_row = (grade_parts[0], int(grade_parts[1]))

                students.append({
                    "name":name_row, 
                    "score":score_row, 
                    "grade_level":grade_row
                    })

            except (ValueError, KeyError, IndexError) as e:
                print(f"Please check {row} - {e}")
    
    return students

def filter_and_save(data: list, condition: str, dest_folder: str):
    """
    Filter a list of student dictionaries based on a simple conditional expression,
    then save the matching students into a timestamped CSV file.

    Supported conditions:
        "score >= 50"
        "score < 40"
        "score != 75"
        etc.

    Supported operators:
        <   <=   >   >=   ==   !=

    This function:
        - Parses the condition string.
        - Applies the comparison to each student.
        - Converts grade_level tuples back to strings.
        - Saves results as: grades_filtered_<timestamp>.csv

    Parameters
    ----------
    data : list
        List of student dictionaries returned by read_csv().
    condition : str
        Condition string in the form "<field> <op> <number>".
    dest_folder : str
        Folder where the filtered CSV output will be saved.

    Returns
    -------
    None
    """
    operators = {
        '<': operator.lt,      
        '<=': operator.le,   
        '>': operator.gt,    
        '>=': operator.ge,   
        '==': operator.eq,  
        '!=': operator.ne    
    }

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder, exist_ok=True)

    timestamp = datetime.today().strftime("%d-%m-%Y_%H-%M-%S")
    file_name = f"grades_filtered_{timestamp}.csv"
    final_dest = os.path.join(dest_folder, file_name)

    try:
        part = [p.strip() for p in condition.split() if p.strip()]
        filter_by = part[0]
        ops = operators[part[1]] 
        numb = int(part[2])
        
        filtered_list = [students for students in data if ops(students[filter_by], numb)]
        
        for student in filtered_list:
            if isinstance(student["grade_level"], tuple):
                student["grade_level"] = " ".join(str(x) for x in student["grade_level"])
        
        if not filtered_list:
            print("No rows match the filter. No file created.")
            return

        with open(final_dest, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=filtered_list[0].keys())
            writer.writeheader()
            writer.writerows(filtered_list)
            print("CSV written successfully!")
    except Exception as e:
        print(e)
    


if __name__ == "__main__":

    data = read_csv("Newprojects/AutomationScripting/testforcsvfiltering.csv")
    filter_and_save(data, "score <= 45", "Newprojects/AutomationScripting/process_log")