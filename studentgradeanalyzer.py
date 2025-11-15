"""
Student Grade Analyzer

This module provides an object-oriented system to read, store, and analyze student grades 
from a CSV file. It allows you to compute averages, identify top-performing students, and 
summarize subject performance statistics.

Classes:

1. Student
   - Represents a student with an ID, full name, and list of subjects/grades.
   - Methods:
       - add_subject(subject: Subject)
       - subject_list (property)
       - __str__(): returns string representation including all subjects

2. Subject
   - Represents a single subject and its associated grade.
   - Properties: subject_name, grade
   - __str__(): returns "subject_name grade"

3. Data_Processor
   - Reads and stores student data from a CSV file.
   - Maintains a dictionary of Student objects keyed by student ID.
   - Methods:
       - read_and_load_student_data(file_path: str)
       - students_dict (property)

4. Analyser
   - Processes and analyzes data from Data_Processor.
   - Methods:
       - load_data(file_path: str): loads CSV data
       - average_per_student(): returns dict mapping student name → average grade
       - average_per_subject(): returns dict mapping subject name → average grade
       - top_student(): returns (student_name, average_grade) of highest scoring student
       - subject_perf_summary(): returns dict of subjects with min, max, and average
       - generate_report(): outputs textual report to a file

Features:
- Handles malformed CSV lines safely, printing warnings for unparseable lines.
- Computes per-student and per-subject statistics.
- Supports generating a human-readable report summarizing all student performance.
- Uses object encapsulation to maintain clean separation between Student, Subject, and Data handling.

Usage Example:
    analyzer = Analyser()
    analyzer.load_data("student_data.csv")
    print(analyzer.average_per_student())
    analyzer.generate_report()
"""
import statistics
from collections import defaultdict
from contextlib import redirect_stdout

class Student:
    def __init__(self, student_id: int, student_name: str):
        self.__student_id = student_id
        self.__student_name = student_name
        self.__subject_list = []
        
    @property
    def student_id(self):
        return self.__student_id
    
    @property
    def student_name(self):
        return self.__student_name
    
    def add_subject(self, subjects: "Subject"):
        self.__subject_list.append(subjects)

    @property
    def subject_list(self):
        return self.__subject_list

    def __str__(self):
        subjects_str = [str(subject) for subject in self.__subject_list] 
        return f"{self.__student_id} {self.__student_name} {subjects_str}"

class Subject:
    def __init__(self, subject_name, grade: int):
        self.__subject_name = subject_name
        self.__grade = grade

    @property
    def subject_name(self):
        return self.__subject_name
    
    @property
    def grade(self):
        return self.__grade
    
    def __str__(self):
        return f"{self.__subject_name} {self.__grade}"
    
class Data_Processor:
    def __init__(self):
        self.__students_dict = {}

    def read_and_load_student_data(self, file_path: str):
        try:
            with open(file_path, "r") as file:
                next(file)
                for line in file:
                    if line:
                        line = line.strip().replace(","," ")
                        part = line.split()
                        if len(part)>5:
                            print(f"Please check this line {line}")
                        try:
                            student_id = int(part[0])
                            full_name = f"{part[1]} {part[2]}"
                            sub = part[3]
                            grade = int(part[4])
                            
                            if student_id not in self.__students_dict:
                                student_object = Student(student_id, full_name)
                                student_object.add_subject(Subject(sub, grade))
                                self.__students_dict[student_id]=student_object
                            else:
                                self.__students_dict[student_id].add_subject(Subject(sub, grade))

                        except (ValueError, IndexError):
                            print(f"Could not parse, Please check this is line {line}")
                    else:
                        print("The file seems to be empty")
        except FileNotFoundError:
            print("please check that the file exists or is correct path")

    @property    
    def students_dict(self):
        return self.__students_dict
    
class Analyser:
    def __init__(self):
        self.__data = Data_Processor()
    
    def load_data(self, file_path : str):
        self.__data.read_and_load_student_data(file_path)
    
    def average_per_student(self):
        avg_dict = {}
        for keys, students in self.__data.students_dict.items():
            grades = [subjects.grade for subjects in students.subject_list]
            avg = statistics.mean(grades)
            avg_dict[students.student_name] = avg

        return avg_dict
    
    def average_per_subject(self):
        sub_avg_dict = defaultdict(list)
        for keys, students in self.__data.students_dict.items():
            for subject in students.subject_list:
                sub_avg_dict[subject.subject_name].append(subject.grade)
        
        return{subject: statistics.mean(grades) for subject, grades in sub_avg_dict.items()}

    def top_student(self):
        avg_grades = self.average_per_student()
        top_student = max(avg_grades, key=lambda name: avg_grades[name])
        return (top_student, avg_grades[top_student])
    
    def subject_perf_summary(self):
        
        avg_per_sub = self.average_per_subject()
        summary_dict = defaultdict(list)
        for keys, students in self.__data.students_dict.items():
            for subject in students.subject_list:
                summary_dict[subject.subject_name].append(subject.grade)

        final_dict = {}
        for subject, grades in summary_dict.items():
            minimum = min(grades)
            maximum = max(grades)
            avg = statistics.mean(grades)
            final_dict[subject] = f"min: {minimum}, max: {maximum}, Avg: {avg:.1f}"
        
        return final_dict

    def generate_report(self):

        file_path = "Newprojects/summary.txt"

        with open(file_path, "w") as file:
            with redirect_stdout(file):    
                print("Average per student:")
                for keys, values in self.average_per_student().items():
                    print(f"{keys}: {values:.1f}")
                print()
                print("Average per subject:")
                for keys, values in self.average_per_subject().items():
                    print(f"{keys}: {values:.1f}")
                print()
                top_student = self.top_student()
                print(f"Top student is {top_student[0]} with {top_student[1]} average")
                print()
                summary = self.subject_perf_summary()
                print("Subject performance summary:")
                for subject, grades in summary.items():
                    print(f"{subject} -> {grades}")


if __name__=="__main__":
    f_path = "Newprojects/student_data.csv"

    data = Analyser()
    data.load_data(f_path)
    data.generate_report()

    

        
    
